"""Stiahne box score hráčov (každý hráč × každý zápas) z nba_api.

Jedna požiadavka = celá sezóna (cca 26 000 riadkov), takže 26 sezón × 2 časti = 52 požiadaviek.

Spustenie:  uv run python -m team_pulse.data.fetch_players --from 2001 --to 2026
Výstup:     data/raw/players.parquet
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from team_pulse.data.fetch_games import SEASON_TYPES, current_abbr, fix_franchise, season_label

OUT = Path("data/raw/players.parquet")
STATS = ["MIN", "PTS", "FGM", "FGA", "FTM", "FTA", "OREB", "DREB"]
STATS += ["AST", "STL", "BLK", "TOV", "PF", "PLUS_MINUS"]


def parse_minutes(value: object) -> float:
    """Minúty prichádzajú ako číslo (34 / 34.5) alebo text ('34:30')."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, str):
        if ":" in value:
            m, s = value.split(":", 1)
            return int(m) + int(s) / 60
        return float(value) if value.strip() else 0.0
    return float(value)


def normalize(raw: pd.DataFrame, end_year: int, playoff: bool, abbr: dict[int, str]) -> pd.DataFrame:
    df = raw.copy()
    out = pd.DataFrame(
        {
            "game_id": df["GAME_ID"].astype(str),
            "date": pd.to_datetime(df["GAME_DATE"]),
            "season": end_year,
            "playoff": playoff,
            "player_id": df["PLAYER_ID"].astype(int),
            "player": df["PLAYER_NAME"],
            "team": [
                fix_franchise(abbr.get(tid, ab), end_year)
                for tid, ab in zip(df["TEAM_ID"], df["TEAM_ABBREVIATION"], strict=True)
            ],
        }
    )
    out["min"] = df["MIN"].map(parse_minutes)
    for c in STATS[1:]:
        out[c.lower()] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return out


def fetch_season(end_year: int, season_type: str, retries: int = 3) -> pd.DataFrame:
    from nba_api.stats.endpoints import leaguegamelog

    for attempt in range(1, retries + 1):
        try:
            r = leaguegamelog.LeagueGameLog(
                season=season_label(end_year),
                season_type_all_star=season_type,
                player_or_team_abbreviation="P",
                league_id="00",
                timeout=60,
            )
            return r.get_data_frames()[0]
        except Exception as e:
            if attempt == retries:
                raise
            wait = 5 * attempt
            print(f"  chyba ({e.__class__.__name__}), skúšam znova o {wait} s")
            time.sleep(wait)
    raise RuntimeError("nedosiahnuteľné")


def main(first: int, last: int, out: Path = OUT) -> pd.DataFrame:
    abbr = current_abbr()
    parts = []
    for year in range(first, last + 1):
        for stype, playoff in SEASON_TYPES.items():
            raw = fetch_season(year, stype)
            if raw.empty:
                continue
            rows = normalize(raw, year, playoff, abbr)
            parts.append(rows)
            n_players = rows["player_id"].nunique()
            print(f"{season_label(year)} {stype:<14} {len(rows):>6} riadkov, {n_players:>4} hráčov")
            time.sleep(1.0)
    players = pd.concat(parts, ignore_index=True)
    players = players.sort_values(["date", "game_id", "team"]).reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    players.to_parquet(out, index=False)
    print(f"\nUložené: {out}  ({len(players)} riadkov, {players['player_id'].nunique()} hráčov)")
    return players


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2001)
    ap.add_argument("--to", dest="last", type=int, default=2026)
    a = ap.parse_args()
    main(a.first, a.last)
