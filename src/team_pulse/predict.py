"""Predikcia pre nadchádzajúce zápasy: pravdepodobnosť, rozdiel skóre a Pulse oboch teamov.

Spája všetky vrstvy:
  A  Elo z výsledkov (s letným návratom k priemeru v novej sezóne)
  B  chýbajúci hráči a sila súpisky zo súpisiek + Injury Reportu ESPN
  C  únava z rozpisu (vrátane zápasov v Mexiku a Európe)
a finálny model models/v1.json.

Spustenie (z Macu):  uv run python -m team_pulse.predict [--date 2026-10-20]
Výstup:              data/live/predictions_<dátum>.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from team_pulse.elo import ELO_PER_POINT, EloParams, current_ratings, rating_for_season
from team_pulse.live.availability import p_out_for_game, player_snapshot, season_rotation, team_availability
from team_pulse.model_store import StoredModel, load
from team_pulse.pulse import confidence, team_state
from team_pulse.schedule import FEATURES, add_features

MODEL = Path("models/v1.json")
OUT_DIR = Path("data/live")
SCHEDULE_COLS = ["game_id", "date", "season", "home", "away", "neutral"]

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


def upcoming_fatigue(
    history: pd.DataFrame, schedule: pd.DataFrame, target_date: pd.Timestamp
) -> pd.DataFrame:
    """Únava pre zápasy v target_date: história + naplánované zápasy od poslednej odohranej po target."""
    last = history["date"].max()
    ahead = schedule[(schedule["date"] > last) & (schedule["date"] <= target_date)].copy()
    ahead["pts_home"], ahead["pts_away"] = 0, 0
    cols = SCHEDULE_COLS + ["pts_home", "pts_away"]
    hist = history.assign(neutral=history.get("neutral", False))[cols]
    combo = pd.concat([hist, ahead[cols + ["arena_city"]]], ignore_index=True)
    feats = add_features(combo)
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
    target_date = pd.Timestamp(target_date).normalize()
    games = schedule[schedule["date"] == target_date]
    if games.empty:
        return []
    season = int(games["season"].iat[0])
    w = model.elo_weights
    p = EloParams(**model.elo_params)

    # A: Elo
    teams = set(history["home"]) | set(history["away"])
    state = current_ratings(history, p, initial={t: p.mean for t in teams})
    elo = {t: rating_for_season(state.get(t, (p.mean, season)), season, p) for t in set(roster["team"])}

    # B: dostupnosť hráčov
    snap = player_snapshot(players)
    rotation = season_rotation(players, season)
    p_out = p_out_for_game(injuries, target_date)
    rosters = {t: set(g["player_id"].astype(int)) for t, g in roster.groupby("team")}

    def avail(team: str, override: dict[int, float] | None = None) -> dict:
        po = {**p_out, **(override or {})}
        return team_availability(team, rosters.get(team, set()), po, snap, rotation)

    league = {t: avail(t) for t in rosters}
    avg_strength = sum(a["strength"] for a in league.values()) / max(len(league), 1)

    # C: únava
    fat = upcoming_fatigue(history, schedule, target_date).set_index("game_id")

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


def main(date: str | None) -> None:
    from team_pulse.learned import GAMES, PLAYERS
    from team_pulse.live.injuries import fetch_injuries, parse_injuries
    from team_pulse.live.roster import ROSTER, match_injuries
    from team_pulse.live.schedule import fetch_schedule, parse_schedule

    history = pd.read_parquet(GAMES)
    players = pd.read_parquet(PLAYERS)
    roster = pd.read_parquet(ROSTER)
    schedule = parse_schedule(fetch_schedule())
    raw_inj = fetch_injuries()
    injuries = match_injuries(parse_injuries(raw_inj), roster)
    age = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(raw_inj["timestamp"])).total_seconds() / 3600
    model = load(MODEL)

    today = pd.Timestamp.now().normalize()
    target = pd.Timestamp(date) if date else schedule.loc[schedule["date"] >= today, "date"].min()
    preds = predict_games(target, history, players, schedule, roster, injuries, model, age)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"predictions_{target.date()}.json"
    out.write_text(json.dumps(preds, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{target.date()} · {len(preds)} zápasov · model {model.version} · zranenia pred {age:.1f} h\n")
    for r in preds:
        h, a = r["home"], r["away"]
        head = f"{a['team']} @ {h['team']}   výhra {h['team']} {r['p_home']:.0%}"
        print(f"{head}   rozdiel {r['margin_home']:+.1f}")
        for s in (h, a):
            drop = f" (normálne {s['normal_tier']})" if s["dropped"] else ""
            print(f"  {s['team']}  Pulse {s['pulse']:5.1f}  {s['tier']:<9}{drop}  istota {s['confidence']}")
            for text, elo in s["reasons"]:
                print(f"        {elo:+4d}  {text}")
        print()
    print(f"Uložené: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD, predvolene najbližší hrací deň")
    main(ap.parse_args().date)
