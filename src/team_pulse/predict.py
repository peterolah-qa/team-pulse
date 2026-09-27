"""Predikcia pre nadchádzajúce zápasy: pravdepodobnosť, rozdiel skóre a Pulse oboch teamov.

Spája všetky vrstvy:
  A  Elo z výsledkov (s letným návratom k priemeru v novej sezóne)
  B  chýbajúci hráči a sila súpisky zo súpisiek + Injury Reportu ESPN
  C  únava z rozpisu (vrátane zápasov v Mexiku a Európe)
a finálny model models/v1.json.

Predikcia pracuje zo stavu (state/state.json, pripraví ho Mac), takže beží aj v cloude.

Spustenie:  uv run python -m team_pulse.predict [--date 2026-10-20] [--days 3]
Výstup:     site/data/predictions.json
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from team_pulse.elo import ELO_PER_POINT
from team_pulse.live.availability import p_out_for_game, team_availability
from team_pulse.model_store import StoredModel, load
from team_pulse.pulse import confidence, team_state
from team_pulse.schedule import FEATURES, add_features
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
SITE_DATA = Path("site/data/predictions.json")
FATIGUE_COLS = ["game_id", "date", "season", "home", "away", "neutral", "arena_city"]

REASON_TEXT = {
    "b2b": "2. zápas za 2 dni",
    "three_in4": "3. zápas za 4 dni",
    "tz_east": "Posun na východ o {v:.0f} h",
    "altitude": "Hrá vo výške",
    "road": "{v:.0f}. zápas výjazdu",
    "rest": "{v:.0f} dni voľna",
    "km": "Cestovanie {km:.0f} km",
}


def _fatigue_text(feature: str, value: float) -> str:
    return REASON_TEXT[feature].format(v=value, km=value * 1000)


def season_fatigue(schedule: pd.DataFrame, target_date: pd.Timestamp) -> pd.DataFrame:
    """Únava pre zápasy v target_date z rozpisu sezóny (odohrané aj naplánované zápasy).

    Pri učení sa únava na začiatku sezóny tiež nulovala, takže stačí rozpis aktuálnej sezóny.
    """
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
    w = model.elo_weights
    elo = state["elo"]

    # B: dostupnosť hráčov
    snap = snapshot_from_state(state)
    rotation = rotation_from_state(state)
    rosters = rosters_from_state(state)
    p_out = p_out_for_game(injuries, target_date)

    def avail(team: str, override: dict[int, float] | None = None) -> dict:
        po = {**p_out, **(override or {})}
        return team_availability(team, rosters.get(team, set()), po, snap, rotation)

    league = {t: avail(t) for t in rosters}
    avg_strength = sum(a["strength"] for a in league.values()) / max(len(league), 1)

    # C: únava
    fat = season_fatigue(schedule, target_date).set_index("game_id")

    per_elo = model.coef[model.features.index("elo_diff")] / 100
    results = []
    for g in games.itertuples():
        f = fat.loc[g.game_id]
        ah, aa = league[g.home], league[g.away]
        row = {
            "elo_diff": (elo[g.home] - elo[g.away]) / 100,
            "home": 0 if g.neutral else 1,
            "home_missing": ah["missing"] * 100,
            "away_missing": aa["missing"] * 100,
            "strength_diff": (ah["strength"] - aa["strength"]) * 100,
        }
        for c in model.features:
            if c not in row:
                row[c] = float(f[c]) / 1000 if c.endswith("_km") else float(f[c])
        prob = float(model.predict_proba(pd.DataFrame([row]))[0])
        margin = math.log(prob / (1 - prob)) / per_elo / ELO_PER_POINT

        teams_out = {}
        for side, team, a, sign in (("home", g.home, ah, 1.0), ("away", g.away, aa, -1.0)):
            # plná súpiska (nikto nechýba) vs. dnešná: rozdiel pripíšeme chýbajúcim hráčom
            team_ids = rosters.get(team, set())
            full = avail(team, {pid: 0.0 for pid in team_ids})
            injury_elo = sign * w[f"{side}_missing"] * a["missing"] * 100
            injury_elo += w["strength_diff"] * (a["strength"] - full["strength"]) * 100
            contrib = {"Sila súpisky": w["strength_diff"] * (full["strength"] - avg_strength) * 100}
            if a["absent"] and abs(injury_elo) > 0.5:
                contrib[_absent_text(a["absent"])] = injury_elo
            contrib.update(_side_contrib(side, f, w, sign))
            st = team_state(elo[team], contrib)

            # istota: otázni hráči všetci nastúpia vs. nikto nenastúpi
            questionable = {
                pid for pid, po in p_out.items() if 0 < po < 1 and pid in rosters.get(team, set())
            }
            if questionable:
                best = avail(team, dict.fromkeys(questionable, 0.0))
                worst = avail(team, dict.fromkeys(questionable, 1.0))

                def elo_of(x: dict, side: str = side, sign: float = sign) -> float:
                    return (
                        sign * w[f"{side}_missing"] * x["missing"] * 100
                        + w["strength_diff"] * (x["strength"] - avg_strength) * 100
                    )

                swing = abs(elo_of(best) - elo_of(worst))
                base = sum(v for k, v in contrib.items() if not k.startswith("Bez") and k != "Sila súpisky")
                t_best = team_state(elo[team], {"x": elo_of(best) + base})["tier"]
                t_worst = team_state(elo[team], {"x": elo_of(worst) + base})["tier"]
            else:
                swing, t_best, t_worst = 0.0, st["tier"], st["tier"]
            st["confidence"] = confidence(t_best, t_worst, swing, data_age_hours)
            st["team"] = team
            teams_out[side] = st

        results.append(
            {
                "game_id": g.game_id,
                "date": str(target_date.date()),
                "tipoff_utc": str(getattr(g, "tipoff_utc", "")),
                "neutral": bool(g.neutral),
                "p_home": round(prob, 3),
                "margin_home": round(margin, 1),
                "home": teams_out["home"],
                "away": teams_out["away"],
            }
        )
    return results


def upcoming_dates(state: dict, today: pd.Timestamp, days: int) -> list[pd.Timestamp]:
    sched = schedule_frame(state)
    if sched.empty:
        return []
    dates = sorted(d for d in sched["date"].unique() if d >= today.normalize())
    return [pd.Timestamp(d) for d in dates[:days]]


def main(date: str | None, days: int) -> None:
    from team_pulse.live.injuries import fetch_injuries, parse_injuries
    from team_pulse.live.roster import match_injuries

    state = load_state()
    model = load(MODEL)
    raw_inj = fetch_injuries()
    injuries = match_injuries(parse_injuries(raw_inj), roster_frame(state))
    age = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(raw_inj["timestamp"])).total_seconds() / 3600

    targets = [pd.Timestamp(date)] if date else upcoming_dates(state, pd.Timestamp.now(), days)
    by_date = {str(t.date()): predict_from_state(state, injuries, model, t, age) for t in targets}

    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model.version,
        "state_generated_at": state["generated_at"],
        "last_result": state["last_result"],
        "injuries_timestamp": raw_inj.get("timestamp"),
        "injuries_matched": f"{int(injuries['player_id'].notna().sum())}/{len(injuries)}",
        "days": by_date,
    }
    SITE_DATA.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"Model {model.version} · stav z {state['generated_at']} · zranenia pred {age:.1f} h\n")
    for day, preds in by_date.items():
        print(f"=== {day} · {len(preds)} zápasov ===")
        for r in preds:
            h, a = r["home"], r["away"]
            head = f"{a['team']} @ {h['team']}   výhra {h['team']} {r['p_home']:.0%}"
            print(f"{head}   rozdiel {r['margin_home']:+.1f}")
            for s in (h, a):
                drop = f" (normálne {s['normal_tier']})" if s["dropped"] else ""
                print(
                    f"  {s['team']}  Pulse {s['pulse']:5.1f}  {s['tier']:<9}{drop}  istota {s['confidence']}"
                )
                for text, elo_pts in s["reasons"]:
                    print(f"        {elo_pts:+4d}  {text}")
        print()
    print(f"Uložené: {SITE_DATA}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD; predvolene najbližšie hracie dni")
    ap.add_argument("--days", type=int, default=3, help="koľko najbližších hracích dní")
    a = ap.parse_args()
    main(a.date, a.days)
