"""Ukážka: ako nba_api vracia zápasy NBA na neutrálnej pôde (Mexiko, Paríž, Berlín, Londýn, NBA Cup).

normalize() v team_pulse.data.fetch_games páruje dva riadky zápasu podľa „vs.“ (domáci) a „@“ (hostia).
Pri zápasoch na neutrálnej pôde to v sezónach 2024/25 a 2025/26 nesedí a zápas z histórie vypadne
(5 zápasov v každej sezóne). Skript vypíše tieto zápasy z LeagueGameFinder, k nim domácich, hostí
a príznak isNeutral z rozpisu ScheduleLeagueV2 a uloží ukážku pre test opravy.

Spustenie (z Macu):  uv run python scripts/probe_nba_neutral.py
Výstup:             tests/fixtures/nba_neutral_games.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, scheduleleaguev2

OUT = Path("tests/fixtures/nba_neutral_games.json")
SEASONS = ["2023-24", "2024-25", "2025-26"]  # 2023/24 je kompletná (kontrola, že tam nič nevypadne)
GAME_COLS = ["SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "PTS"]
SCHEDULE_COLS = [
    "gameId", "gameDateEst", "arenaCity", "isNeutral", "gameLabel", "gameSubLabel",
    "homeTeam_teamId", "homeTeam_teamTricode", "homeTeam_score",
    "awayTeam_teamId", "awayTeam_teamTricode", "awayTeam_score",
]  # fmt: skip


def unpaired(raw: pd.DataFrame) -> pd.DataFrame:
    """Riadky zápasov, ktoré nemajú presne jeden riadok domácich („vs.“) a jeden riadok hostí."""
    home = raw["MATCHUP"].str.contains(" vs. ", regex=False)
    n_home = home.groupby(raw["GAME_ID"]).sum()
    n_rows = raw.groupby("GAME_ID").size()
    bad = n_home.index[(n_home != 1) | (n_rows != 2)]
    return raw[raw["GAME_ID"].isin(bad)].sort_values(["GAME_DATE", "GAME_ID", "TEAM_ABBREVIATION"])


def schedule(season: str) -> pd.DataFrame:
    df = scheduleleaguev2.ScheduleLeagueV2(season=season, league_id="00", timeout=60).get_data_frames()[0]
    missing = [c for c in SCHEDULE_COLS if c not in df.columns]
    if missing:
        print(f"  Rozpis nemá stĺpce {missing}. Má: {list(df.columns)}")
    return df[[c for c in SCHEDULE_COLS if c in df.columns]]


def main() -> None:
    fixture: dict[str, dict] = {}
    for season in SEASONS:
        raw = leaguegamefinder.LeagueGameFinder(
            season_nullable=season, league_id_nullable="00", season_type_nullable="Regular Season", timeout=60
        ).get_data_frames()[0]
        bad = unpaired(raw)
        print(f"\n{season}: {raw['GAME_ID'].nunique()} zápasov, nespárovaných {bad['GAME_ID'].nunique()}")
        if not bad.empty:
            print(bad[GAME_COLS[2:]].to_string(index=False))
        time.sleep(1.0)
        sched = schedule(season)
        neutral = sched.iloc[0:0]
        if "isNeutral" in sched:  # môže prísť ako bool aj ako text „true“/„false“
            neutral = sched[sched["isNeutral"].astype(str).str.lower().isin(["true", "1"])]
        print(f"Rozpis: {len(sched)} zápasov, na neutrálnej pôde {len(neutral)}")
        if not neutral.empty:
            print(neutral.to_string(index=False))
        ids = set(bad["GAME_ID"]) | set(neutral["gameId"].astype(str))
        fixture[season] = {
            "games": json.loads(raw[raw["GAME_ID"].isin(ids)][GAME_COLS].to_json(orient="records")),
            "schedule": json.loads(sched[sched["gameId"].astype(str).isin(ids)].to_json(orient="records")),
        }
        time.sleep(1.0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nUložené: {OUT}")


if __name__ == "__main__":
    main()
