"""Predikcia pre nadchádzajúce zápasy a dáta pre appku.

Spája všetky vrstvy:
  A  Elo z výsledkov (s letným návratom k priemeru v novej sezóne)
  B  chýbajúci hráči a sila súpisky zo súpisiek + Injury Reportu ESPN
  C  únava z rozpisu (vrátane zápasov v Mexiku a Európe)
a finálny model models/v1.json.

Pracuje zo stavu (state/state.json, pripraví ho Mac), takže beží aj v cloude.
Zapíše tri súbory pre appku:
  predictions.json  zápasy najbližších dní: šanca, rozdiel, Pulse, vrstvy, dôvody, „čo keby“
  teams.json        30 teamov: Pulse dnes, trend, súpiska so stavom hráčov, najbližšie zápasy
  model.json        presnosť, kalibrácia, porovnanie verzií, naučené váhy

Spustenie:  uv run python -m team_pulse.predict [--date 2026-10-20] [--days 3] [--out app/public/data]
                                                 [--archive]
  --archive  zápasy, ktoré začínajú do 2 h, uloží do archive/predictions (len v cloude, predict.yml)
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from team_pulse.archive import PRED_DIR, lock_games
from team_pulse.elo import ELO_PER_POINT
from team_pulse.live.availability import (
    MAX_MIN,
    REPLACEMENT,
    ROOKIE_MIN,
    Snapshot,
    p_out_for_game,
    team_availability,
)
from team_pulse.model_store import StoredModel, load
from team_pulse.pulse import LEAGUE_MEAN, confidence, pulse_from_elo, team_state
from team_pulse.schedule import FEATURES, MAX_REST, add_features
from team_pulse.state import (
    build_state,
    load_state,
    roster_frame,
    rosters_from_state,
    rotation_from_state,
    schedule_frame,
    snapshot_from_state,
)

MODEL = Path("models/v1.json")
OUT = Path("app/public/data")
FATIGUE_COLS = ["game_id", "date", "season", "home", "away", "neutral", "arena_city"]
ROSTER_KEY = "Sila súpisky"
MAX_WHAT_IF = 4
MIN_WHAT_IF_SWING = 0.01  # scenár bez zmeny šance aspoň o 1 p. b. (a bez zmeny úrovne) sa neukáže
PRESEASON = "preseason"

REASON_TEXT = {
    "b2b": "2. zápas za 2 dni",
    "three_in4": "3. zápas za 4 dni",
    "tz_east": "Posun na východ o {v:.0f} h",
    "altitude": "Hrá vo výške",
    "road": "{v:.0f}. zápas výjazdu",
    "rest": "{v:.0f} {days} voľna",
    "km": "Cestovanie {km:.0f} km",
}


def days_word(n: int) -> str:
    """1 deň, 2 – 4 dni, 0 a 5+ dní."""
    return "deň" if n == 1 else "dni" if 2 <= n <= 4 else "dní"


def _fatigue_text(feature: str, value: float) -> str:
    if feature == "rest" and value >= MAX_REST:
        return f"Bez zápasu {MAX_REST}+ dní"  # 1. zápas sezóny alebo dlhá prestávka (strop únavy)
    return REASON_TEXT[feature].format(v=value, km=value * 1000, days=days_word(round(value)))


def is_preseason(schedule: pd.DataFrame) -> pd.Series:
    if "kind" not in schedule:
        return pd.Series(False, index=schedule.index)
    return schedule["kind"].eq(PRESEASON)


def season_fatigue(schedule: pd.DataFrame, target_date: pd.Timestamp) -> pd.DataFrame:
    """Únava pre zápasy v target_date z rozpisu sezóny (odohrané aj naplánované zápasy).

    Pri učení sa únava na začiatku sezóny tiež nulovala, takže stačí rozpis aktuálnej sezóny.
    Príprava a základná časť sa počítajú oddelene: pri učení príprava v dátach nebola, takže
    na prvý zápas sezóny má team plné voľno, aj keď pár dní predtým hral prípravu.
    """
    pre = is_preseason(schedule)
    if pre.any() and (~pre).any():
        parts = [season_fatigue(schedule[mask], target_date) for mask in (pre, ~pre)]
        return pd.concat(parts, ignore_index=True)
    upto = schedule[schedule["date"] <= target_date][FATIGUE_COLS].copy()
    upto["pts_home"], upto["pts_away"] = 0, 0  # výsledky únava nepoužíva
    feats = add_features(upto)
    return feats[feats["date"] == target_date].reset_index(drop=True)


def _side_contrib(side: str, feats: pd.Series, w: dict, own_sign: float) -> dict[str, float]:
    """Príspevky únavy jedného teamu v Elo (z pohľadu tohto teamu)."""
    out = {}
    for f in FEATURES:
        key = f"{side}_{f}"
        if key not in w:
            continue
        value = float(feats[key]) / 1000 if f == "km" else float(feats[key])
        elo = own_sign * w[key] * value
        if value and abs(elo) > 0.5:
            out[_fatigue_text(f, value)] = elo
    return out


def _absent_text(absent: list[dict]) -> str:
    names = [a["player"] + ("" if a["p_out"] >= 1 else " (?)") for a in absent[:2]]
    return "Bez " + ", ".join(names) if names else "Chýbajúci hráči"


def _above(pid: int, snap: Snapshot) -> float:
    return max(snap.value.get(pid, REPLACEMENT) - REPLACEMENT, 0.0)


@dataclass
class Context:
    """Všetko, čo sa počíta raz na deň; jednotlivé zápasy a scenáre „čo keby“ z neho čerpajú."""

    state: dict
    model: StoredModel
    target_date: pd.Timestamp
    p_out: dict[int, float]
    data_age_hours: float
    snap: Snapshot = field(init=False)
    rotation: dict = field(init=False)
    rosters: dict = field(init=False)
    avg_strength: float = field(init=False)

    def __post_init__(self) -> None:
        self.snap = snapshot_from_state(self.state)
        self.rotation = rotation_from_state(self.state)
        self.rosters = rosters_from_state(self.state)
        league = [self.avail(t) for t in self.rosters]
        self.avg_strength = sum(a["strength"] for a in league) / max(len(league), 1)

    @property
    def w(self) -> dict:
        return self.model.elo_weights

    def avail(self, team: str, override: dict[int, float] | None = None) -> dict:
        po = {**self.p_out, **(override or {})}
        return team_availability(team, self.rosters.get(team, set()), po, self.snap, self.rotation)

    def roster_elo(self, a: dict) -> float:
        return self.w["strength_diff"] * (a["strength"] - self.avg_strength) * 100

    def team_contrib(self, team: str, side: str | None, override: dict[int, float] | None = None) -> dict:
        """Príspevky súpisky a chýbajúcich hráčov v Elo. side=None: priemer domáci/hostia (stránka teamu)."""
        a = self.avail(team, override)
        full = self.avail(team, dict.fromkeys(self.rosters.get(team, set()), 0.0))
        if side is None:
            w_missing = (self.w["home_missing"] - self.w["away_missing"]) / 2
        else:
            w_missing = self.w[f"{side}_missing"] * (1.0 if side == "home" else -1.0)
        injury = (
            w_missing * a["missing"] * 100
            + self.w["strength_diff"] * (a["strength"] - full["strength"]) * 100
        )
        contrib = {ROSTER_KEY: self.roster_elo(full)}
        if a["absent"] and abs(injury) > 0.5:
            contrib[_absent_text(a["absent"])] = injury
        return {"contrib": contrib, "avail": a, "injury": injury, "roster": contrib[ROSTER_KEY]}


def _game(ctx: Context, g, fat: pd.Series, override: dict[int, float] | None = None) -> dict:
    w, elo, model = ctx.w, ctx.state["elo"], ctx.model
    parts = {
        "home": ctx.team_contrib(g.home, "home", override),
        "away": ctx.team_contrib(g.away, "away", override),
    }
    ah, aa = parts["home"]["avail"], parts["away"]["avail"]
    row = {
        "elo_diff": (elo[g.home] - elo[g.away]) / 100,
        "home": 0 if g.neutral else 1,
        "home_missing": ah["missing"] * 100,
        "away_missing": aa["missing"] * 100,
        "strength_diff": (ah["strength"] - aa["strength"]) * 100,
    }
    for c in model.features:
        if c not in row:
            row[c] = float(fat[c]) / 1000 if c.endswith("_km") else float(fat[c])
    prob = float(model.predict_proba(pd.DataFrame([row]))[0])
    per_elo = model.coef[model.features.index("elo_diff")] / 100
    margin = math.log(prob / (1 - prob)) / per_elo / ELO_PER_POINT

    po = {**ctx.p_out, **(override or {})}
    teams_out = {}
    for side, team, sign in (("home", g.home, 1.0), ("away", g.away, -1.0)):
        fatigue = _side_contrib(side, fat, w, sign)
        contrib = {**parts[side]["contrib"], **fatigue}
        st = team_state(elo[team], contrib)

        # istota: otázni hráči všetci nastúpia vs. nikto nenastúpi
        questionable = {pid for pid, p in po.items() if 0 < p < 1 and pid in ctx.rosters.get(team, set())}
        if questionable:
            best = ctx.team_contrib(team, side, {**(override or {}), **dict.fromkeys(questionable, 0.0)})
            worst = ctx.team_contrib(team, side, {**(override or {}), **dict.fromkeys(questionable, 1.0)})
            fat_sum = sum(fatigue.values())
            elo_best = best["injury"] + best["roster"] + fat_sum
            elo_worst = worst["injury"] + worst["roster"] + fat_sum
            swing = abs(elo_best - elo_worst)
            t_best = team_state(elo[team], {"x": elo_best})["tier"]
            t_worst = team_state(elo[team], {"x": elo_worst})["tier"]
        else:
            swing, t_best, t_worst = 0.0, st["tier"], st["tier"]
        st["confidence"] = confidence(t_best, t_worst, swing, ctx.data_age_hours)
        st["team"] = team
        st["layers"] = {
            "strength": round(elo[team] - LEAGUE_MEAN, 1),
            "roster": round(parts[side]["roster"], 1),
            "players": round(parts[side]["injury"], 1),
            "fatigue": round(sum(fatigue.values()), 1),
        }
        st["contributions"] = {k: round(v, 1) for k, v in contrib.items()}
        teams_out[side] = st

    return {
        "game_id": g.game_id,
        "date": str(ctx.target_date.date()),
        "tipoff_utc": str(getattr(g, "tipoff_utc", "")),
        "kind": str(getattr(g, "kind", "regular")),
        "neutral": bool(g.neutral),
        "home_adv": 0.0 if g.neutral else round(w["home"], 1),
        "p_home": round(prob, 3),
        "margin_home": round(margin, 1),
        "home": teams_out["home"],
        "away": teams_out["away"],
    }


def _scenario(pred: dict, side: str) -> dict:
    return {"p_home": pred["p_home"], "pulse": pred[side]["pulse"], "tier": pred[side]["tier"]}


def _what_if(ctx: Context, g, fat: pd.Series) -> list[dict]:
    """Scenáre pre otáznych hráčov: čo ak nastúpi / nenastúpi."""
    out = []
    for side, team in (("home", g.home), ("away", g.away)):
        for pid in ctx.rosters.get(team, set()):
            p = ctx.p_out.get(pid, 0.0)
            if not 0 < p < 1 or _above(pid, ctx.snap) <= 0:
                continue
            plays, sits = _game(ctx, g, fat, {pid: 0.0}), _game(ctx, g, fat, {pid: 1.0})
            swing = abs(plays["p_home"] - sits["p_home"])
            if swing < MIN_WHAT_IF_SWING and plays[side]["tier"] == sits[side]["tier"]:
                continue
            impact = abs(plays[side]["elo_today"] - sits[side]["elo_today"])
            out.append(
                {
                    "player_id": pid,
                    "player": ctx.snap.name.get(pid, str(pid)),
                    "team": team,
                    "side": side,
                    "p_out": p,
                    "impact_elo": round(impact),
                    "plays": _scenario(plays, side),
                    "out": _scenario(sits, side),
                }
            )
    out.sort(key=lambda x: -x["impact_elo"])
    return out[:MAX_WHAT_IF]


def predict_from_state(
    state: dict,
    injuries: pd.DataFrame,
    model: StoredModel,
    target_date: pd.Timestamp,
    data_age_hours: float = 0.0,
) -> list[dict]:
    target_date = pd.Timestamp(target_date).normalize()
    schedule = schedule_frame(state)
    games = schedule[schedule["date"] == target_date] if not schedule.empty else schedule
    if games.empty:
        return []
    ctx = Context(state, model, target_date, p_out_for_game(injuries, target_date), data_age_hours)
    fat = season_fatigue(schedule, target_date).set_index("game_id")
    results = []
    for g in games.itertuples():
        res = _game(ctx, g, fat.loc[g.game_id])
        res["what_if"] = _what_if(ctx, g, fat.loc[g.game_id])
        results.append(res)
    return results


def predict_games(
    target_date: pd.Timestamp,
    history: pd.DataFrame,
    players: pd.DataFrame,
    schedule: pd.DataFrame,
    roster: pd.DataFrame,
    injuries: pd.DataFrame,
    model: StoredModel,
    data_age_hours: float = 0.0,
) -> list[dict]:
    """Predikcia priamo z histórie (Mac, testy): najprv zostaví stav, potom predpovedá."""
    state = build_state(history, players, roster, schedule, model.elo_params)
    return predict_from_state(state, injuries, model, target_date, data_age_hours)


# --- stránka teamu a stránka modelu ------------------------------------------------


def build_teams(
    state: dict, injuries: pd.DataFrame, model: StoredModel, today: pd.Timestamp, data_age_hours: float = 0.0
) -> dict:
    """Stav každého teamu dnes (bez únavy konkrétneho zápasu), trend, súpiska, najbližšie zápasy."""
    today = pd.Timestamp(today).normalize()
    ctx = Context(state, model, today, p_out_for_game(injuries, today), data_age_hours)
    status_by_pid = {int(r.player_id): r.status for r in injuries.dropna(subset=["player_id"]).itertuples()}
    sched = schedule_frame(state)
    ranking = sorted(state["elo"], key=lambda t: -state["elo"][t])
    teams = {}
    for team in state["rosters"]:
        tc = ctx.team_contrib(team, None)
        st = team_state(state["elo"][team], tc["contrib"])
        roster = []
        for pid in state["rosters"][team]:
            typical = min(ctx.snap.typical_min.get(pid, ROOKIE_MIN), MAX_MIN)
            impact = model.elo_weights["strength_diff"] * typical / 48 * _above(pid, ctx.snap) * 100
            p = ctx.p_out.get(pid, 0.0)
            roster.append(
                {
                    "player_id": pid,
                    "player": ctx.snap.name.get(pid, str(pid)),
                    "status": status_by_pid.get(pid, "HRÁ") if p > 0 else "HRÁ",
                    "p_out": p,
                    "typical_min": round(typical, 1),
                    "impact_elo": round(impact),
                }
            )
        roster.sort(key=lambda r: -r["impact_elo"])
        upcoming = []
        if not sched.empty:
            mine = sched[((sched["home"] == team) | (sched["away"] == team)) & (sched["date"] >= today)]
            for g in mine.head(3).itertuples():
                home = g.home == team
                upcoming.append(
                    {
                        "game_id": g.game_id,
                        "date": str(g.date.date()),
                        "opp": g.away if home else g.home,
                        "home": home,
                        "kind": str(getattr(g, "kind", "regular")),
                    }
                )
        trend = [
            {**h, "pulse": round(pulse_from_elo(h["elo"]), 1)}
            for h in state.get("elo_history", {}).get(team, [])
        ]
        teams[team] = {
            **st,
            "team": team,
            "rank": ranking.index(team) + 1,
            "trend": trend,
            "roster": roster[:13],
            "upcoming": upcoming,
        }
    return teams


def model_info(model: StoredModel) -> dict:
    return {
        "version": model.version,
        "created": model.created,
        "train_seasons": model.train_seasons,
        "n_games": model.n_games,
        "test_metrics": model.test_metrics,
        "calibration": model.calibration,
        "versions": model.versions,
        "elo_weights": model.elo_weights,
    }


def upcoming_dates(state: dict, today: pd.Timestamp, days: int) -> list[pd.Timestamp]:
    sched = schedule_frame(state)
    if sched.empty:
        return []
    dates = sorted(d for d in sched["date"].unique() if d >= today.normalize())
    return [pd.Timestamp(d) for d in dates[:days]]


def results_for_app(state: dict, pred_dir: Path = PRED_DIR) -> list[dict]:
    """Výsledky posledných dní (zo stavu) doplnené o našu poslednú predpoveď pred zápasom z archívu."""
    out, cache = [], {}
    for r in state.get("results", []):
        if r["date"] not in cache:
            path = pred_dir / f"{r['date']}.json"
            cache[r["date"]] = json.loads(path.read_text(encoding="utf-8"))["games"] if path.exists() else {}
        rec = cache[r["date"]].get(r["game_id"])
        out.append({**r, "p_home": rec["p_home"] if rec else None})
    return out


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def today_et(now: pd.Timestamp | None = None) -> pd.Timestamp:
    """Dnešný dátum v USA (ET). Dátumy zápasov sú v ET; zápas o 22:00 ET je v UTC už ďalší deň."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    return now.tz_convert("America/New_York").tz_localize(None).normalize()


def main(date: str | None, days: int, out: Path, archive: bool = False) -> None:
    from team_pulse.live.injuries import fetch_injuries, parse_injuries
    from team_pulse.live.roster import match_injuries

    state = load_state()
    model = load(MODEL)
    raw_inj = fetch_injuries()
    injuries = match_injuries(parse_injuries(raw_inj), roster_frame(state))
    age = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(raw_inj["timestamp"])).total_seconds() / 3600
    today = today_et()

    targets = [pd.Timestamp(date)] if date else upcoming_dates(state, today, days)
    by_date = {str(t.date()): predict_from_state(state, injuries, model, t, age) for t in targets}
    meta = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model.version,
        "state_generated_at": state["generated_at"],
        "last_result": state["last_result"],
        "injuries_timestamp": raw_inj.get("timestamp"),
        "injuries_matched": f"{int(injuries['player_id'].notna().sum())}/{len(injuries)}",
    }
    write_json(out / "predictions.json", {**meta, "days": by_date, "results": results_for_app(state)})
    write_json(out / "teams.json", {**meta, "teams": build_teams(state, injuries, model, today, age)})
    write_json(out / "model.json", model_info(model))

    print(f"Model {model.version} · stav z {state['generated_at']} · zranenia pred {age:.1f} h\n")
    for day, preds in by_date.items():
        print(f"=== {day} · {len(preds)} zápasov ===")
        for r in preds:
            h, a = r["home"], r["away"]
            head = f"{a['team']} @ {h['team']}   výhra {h['team']} {r['p_home']:.0%}"
            print(f"{head}   rozdiel {r['margin_home']:+.1f}")
            for s in (h, a):
                drop = f" (normálne {s['normal_tier']})" if s["dropped"] else ""
                line = f"  {s['team']}  Pulse {s['pulse']:5.1f}  {s['tier']:<9}{drop}"
                print(f"{line}  istota {s['confidence']}")
                for text, elo_pts in s["reasons"]:
                    print(f"        {elo_pts:+4d}  {text}")
            for wi in r["what_if"]:
                plays, sits = wi["plays"]["p_home"], wi["out"]["p_home"]
                print(f"    čo keby {wi['player']}: hrá {plays:.0%} / nehrá {sits:.0%}")
        print()
    print(f"Uložené: {out}/predictions.json, teams.json, model.json")

    if archive:
        changed = lock_games(by_date, meta, pd.Timestamp.now(tz="UTC"))
        print(
            f"Archív: {len(changed)} zápasov uložených alebo zmenených"
            + (f" ({', '.join(changed)})" if changed else "")
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD; predvolene najbližšie hracie dni")
    ap.add_argument("--days", type=int, default=3, help="koľko najbližších hracích dní")
    ap.add_argument("--out", type=Path, default=OUT, help="priečinok pre JSON súbory appky")
    ap.add_argument(
        "--archive", action="store_true", help="uložiť predpovede pred začiatkom zápasov do archívu"
    )
    a = ap.parse_args()
    main(a.date, a.days, a.out, a.archive)
