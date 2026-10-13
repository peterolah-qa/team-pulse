"""Živé NHL tipy: aktuálna sezóna z API NHL, model Elo + únava (models/nhl_v1.json).

Postup:
  1. história do minulej sezóny (data/raw/nhl_games.parquet) + dohraté zápasy tejto sezóny z API,
  2. Elo cez všetky dohraté zápasy (rating pred zápasom, po lete návrat k priemeru),
  3. únava z rozpisu (dohraté aj nadchádzajúce zápasy, výsledky netreba),
  4. šanca domácich z uloženého modelu, tip = favorit (domáci pri šanci nad 50 %, ako v NBA).

Spustenie (z Macu):  uv run python -m team_pulse.nhl.predict [--days 3]
Výstup:             app/public/data/nhl/predictions.json + tipy v termináli
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from team_pulse.model_store import StoredModel, load
from team_pulse.nhl.elo import HockeyEloParams, run, season_reset
from team_pulse.nhl.fetch_games import FINISHED, fetch_season, finished_games, franchise, season_label
from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.model import MODEL
from team_pulse.nhl.schedule import add_features

OUT = Path("app/public/data/nhl/predictions.json")
ET = ZoneInfo("America/New_York")
LOCAL = ZoneInfo("Europe/Bratislava")
KINDS = {"R": "regular", "P": "playoff"}
MIN_REASON = 10  # Elo – menší vplyv sa v dôvodoch neukazuje


def today_et(now: datetime | None = None) -> date:
    """Dnešný deň v USA (ET): dátumy zápasov NHL sú podľa ET."""
    return (now or datetime.now(UTC)).astimezone(ET).date()


def season_of(day: date) -> int:
    """Sezóna = rok, v ktorom končí. Nová sezóna NHL začína v septembri/októbri."""
    return day.year + 1 if day.month >= 8 else day.year


def upcoming_games(current: pd.DataFrame, first: date, days: int) -> pd.DataFrame:
    """Nedohraté zápasy s dátumom (ET) od `first` na `days` dní, s klubmi pod dnešnou skratkou."""
    last = first + timedelta(days=days - 1)
    day = pd.to_datetime(current["date"]).dt.date
    up = current[~current["state"].isin(FINISHED) & (day >= first) & (day <= last)].copy()
    up["home"] = up["home_abbr"].map(franchise)
    up["away"] = up["away_abbr"].map(franchise)
    up["date"] = pd.to_datetime(up["date"])
    return up.reset_index(drop=True)


def ratings(done: pd.DataFrame, p: HockeyEloParams) -> dict[str, tuple[float, int]]:
    """Klub → (Elo po poslednom dohratom zápase, sezóna toho zápasu)."""
    res = run(done, p)
    out: dict[str, tuple[float, int]] = {}
    for r in res.itertuples(index=False):
        out[r.home] = (r.elo_home_post, int(r.season))
        out[r.away] = (r.elo_away_post, int(r.season))
    return out


def rating_now(state: tuple[float, int] | None, season: int, p: HockeyEloParams) -> float:
    if state is None:
        return p.new_team
    elo, last = state
    return season_reset(elo, p) if season > last else elo


def reasons(row: pd.Series, side: str, weights: dict[str, float]) -> dict[str, float]:
    """Vplyv únavy v Elo bodoch z pohľadu klubu (kladné = pomáha mu). Len výrazné položky."""
    sign = 1.0 if side == "home" else -1.0  # váhy sú z pohľadu domácich
    items = {
        "back-to-back": weights.get(f"{side}_b2b", 0.0) * row[f"{side}_b2b"],
        "3. zápas za 4 dni": weights.get(f"{side}_three_in4", 0.0) * row[f"{side}_three_in4"],
        f"posun o {int(row[f'{side}_tz_east'])} h na východ": weights.get(f"{side}_tz_east", 0.0)
        * row[f"{side}_tz_east"],
    }
    if side == "away" and row["away_road"] >= 2:
        items[f"{int(row['away_road'])}. zápas výjazdu"] = weights.get("away_road", 0.0) * row["away_road"]
    return {k: round(sign * v, 1) for k, v in items.items() if abs(v) >= MIN_REASON}


def predict(
    history: pd.DataFrame, current: pd.DataFrame, model: StoredModel, first: date, days: int = 3
) -> list[dict]:
    """Tipy na nedohraté zápasy aktuálnej sezóny v najbližších `days` dňoch (ET)."""
    p = HockeyEloParams(**model.elo_params)
    done_now = finished_games(current)
    done = pd.concat([history[~history["game_id"].isin(done_now["game_id"])], done_now], ignore_index=True)
    up = upcoming_games(current, first, days)
    if up.empty:
        return []
    season = int(up["season"].max())
    state = ratings(done, p)
    cols = ["game_id", "season", "date", "start_utc", "home", "away", "home_abbr", "away_abbr", "neutral"]
    sched = pd.concat([done[done["season"] == season][cols], up[cols]], ignore_index=True)
    feats = add_features(sched).set_index("game_id").loc[up["game_id"]]
    feats["elo_home"] = [rating_now(state.get(t), season, p) for t in feats["home"]]
    feats["elo_away"] = [rating_now(state.get(t), season, p) for t in feats["away"]]
    feats["elo_diff"] = (feats["elo_home"] - feats["elo_away"]) / 100
    feats["home"] = (~feats["neutral"].astype(bool)).astype(int)
    probs = model.predict_proba(feats)
    out = []
    for (gid, row), prob, g in zip(feats.iterrows(), probs, up.itertuples(index=False), strict=True):
        tip = g.home if prob > 0.5 else g.away
        out.append({
            "game_id": str(gid),
            "date": g.date.date().isoformat(),
            "tipoff_utc": g.start_utc,
            "kind": KINDS.get(g.game_type, "regular"),
            "neutral": bool(g.neutral),
            "p_home": round(float(prob), 3),
            "tip": tip,
            "home": {"team": g.home, "elo": round(float(row["elo_home"]), 1),
                     "reasons": reasons(row, "home", model.elo_weights)},
            "away": {"team": g.away, "elo": round(float(row["elo_away"]), 1),
                     "reasons": reasons(row, "away", model.elo_weights)},
        })  # fmt: skip
    return sorted(out, key=lambda x: (x["tipoff_utc"], x["game_id"]))


def to_json(games: list[dict], model: StoredModel, now: datetime) -> dict:
    days: dict[str, list[dict]] = {}
    for g in games:
        days.setdefault(g["date"], []).append(g)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "sport": "nhl",
        "model": model.version,
        "days": days,
    }


def line(g: dict) -> str:
    """„st 14. 10. 01:00  NJD @ DET  tip DET 56 %  (DET: back-to-back −42)“ v našom čase."""
    start = datetime.fromisoformat(g["tipoff_utc"].replace("Z", "+00:00")).astimezone(LOCAL)
    p = g["p_home"] if g["tip"] == g["home"]["team"] else 1 - g["p_home"]
    notes = [
        f"{side['team']}: {k} {v:+.0f}" for side in (g["home"], g["away"]) for k, v in side["reasons"].items()
    ]
    pct = round(p * 100)
    return f"{start:%d. %m. %H:%M}  {g['away']['team']} @ {g['home']['team']}  tip {g['tip']} {pct} %" + (
        f"  ({'; '.join(notes)})" if notes else ""
    )


def main(days: int = 3, out: Path = OUT, games_path: Path = GAMES, model_path: Path = MODEL) -> dict:
    now = datetime.now(UTC)
    first = today_et(now)
    model = load(model_path)
    history = pd.read_parquet(games_path)
    current = fetch_season(requests.Session(), season_of(first))
    games = predict(history, current, model, first, days)
    data = to_json(games, model, now)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    done = int(current["state"].isin(FINISHED).sum())
    print(f"Sezóna {season_label(season_of(first))}: dohratých {done} zápasov, tipy na {days} dni")
    for g in games:
        print(line(g))
    print(f"\nUložené: {out}")
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    a = ap.parse_args()
    main(a.days)
