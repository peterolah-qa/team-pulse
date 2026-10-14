"""Stiahne štatistiky brankárov NHL po zápasoch (kto začal, strely, zákroky) – podklad pre vrstvu brankára.

Zdroj: api.nhle.com/stats, goalie/summary po zápasoch (isGame=true). Jedna sezóna je ~28 strán
po 100 riadkov namiesto 1 300 box score. Riadok = brankár × zápas (aj striedajúci brankár).

Kontrola: každý dohratý zápas z data/raw/nhl_games.parquet musí mať pre oba kluby práve
jedného brankára, ktorý začal. Nájdené odchýlky sa vypíšu a uložia, aby sa dali skontrolovať.

Spustenie (z Macu, po fetch_games):  uv run python -m team_pulse.nhl.fetch_goalies --from 2006 --to 2026
Výstup:                            data/raw/nhl_goalies.parquet (necommituje sa)
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests

from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.fetch_games import franchise, season_id, season_label

OUT = Path("data/raw/nhl_goalies.parquet")
URL = "https://api.nhle.com/stats/rest/en/goalie/summary"
PAGE = 100
GAME_TYPES = {2: "R", 3: "P"}
SORT = json.dumps([{"property": "gameId", "direction": "ASC"}, {"property": "playerId", "direction": "ASC"}])
COLUMNS = [
    "game_id", "season", "game_type", "date", "team_abbr", "team", "home", "player_id", "name",
    "started", "shots_against", "saves", "goals_against", "toi",
]  # fmt: skip


def parse_row(r: dict, end_year: int, game_type: str) -> dict:
    return {
        "game_id": int(r["gameId"]),
        "season": end_year,
        "game_type": game_type,
        "date": r["gameDate"],
        "team_abbr": r["teamAbbrev"],
        "team": franchise(r["teamAbbrev"]),
        "home": r["homeRoad"] == "H",
        "player_id": int(r["playerId"]),
        "name": r["goalieFullName"],
        "started": int(r.get("gamesStarted") or 0) == 1,
        "shots_against": int(r.get("shotsAgainst") or 0),
        "saves": int(r.get("saves") or 0),
        "goals_against": int(r.get("goalsAgainst") or 0),
        "toi": int(r.get("timeOnIce") or 0),
    }


def fetch_page(session: requests.Session, end_year: int, type_id: int, start: int, retries: int = 4) -> dict:
    params = {
        "isAggregate": "false",
        "isGame": "true",
        "start": start,
        "limit": PAGE,
        "sort": SORT,
        "cayenneExp": f"seasonId={season_id(end_year)} and gameTypeId={type_id}",
    }
    for attempt in range(1, retries + 1):
        try:
            r = session.get(URL, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            if attempt == retries:
                raise RuntimeError(f"{season_label(end_year)} typ {type_id} od {start}: {e}") from e
            time.sleep(3 * attempt)
    return {}


def fetch_season(session: requests.Session, end_year: int, pause: float = 0.25) -> pd.DataFrame:
    rows = []
    for type_id, game_type in GAME_TYPES.items():
        start, total = 0, None
        while total is None or start < total:
            page = fetch_page(session, end_year, type_id, start)
            total = int(page.get("total") or 0)
            data = page.get("data") or []
            rows += [parse_row(r, end_year, game_type) for r in data]
            if not data:
                break
            start += PAGE
            time.sleep(pause)
        got = sum(1 for r in rows if r["game_type"] == game_type)
        if got != total:
            raise ValueError(f"{season_label(end_year)} {game_type}: API hlási {total} riadkov, prišlo {got}")
    df = pd.DataFrame(rows, columns=COLUMNS).drop_duplicates(["game_id", "player_id"])
    return df.sort_values(["game_id", "home", "started"], ascending=[True, False, False]).reset_index(
        drop=True
    )


def check_starters(goalies: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Zápasy, kde klub nemá práve jedného brankára, ktorý začal (alebo kde brankár nesedí na klub)."""
    starters = goalies[goalies["started"]].groupby(["game_id", "team"]).size()
    expected = pd.concat(
        [
            games[["game_id", "home"]].rename(columns={"home": "team"}),
            games[["game_id", "away"]].rename(columns={"away": "team"}),
        ]
    )
    expected["starters"] = [
        starters.get((g, t), 0) for g, t in zip(expected["game_id"], expected["team"], strict=True)
    ]
    return expected[expected["starters"] != 1].sort_values("game_id").reset_index(drop=True)


def main(first: int, last: int, out: Path = OUT, games_path: Path = GAMES) -> pd.DataFrame:
    games = pd.read_parquet(games_path)
    session = requests.Session()
    parts, problems = [], []
    for year in range(first, last + 1):
        df = fetch_season(session, year)
        bad = check_starters(df, games[games["season"] == year])
        parts.append(df)
        problems.append(bad.assign(season=year))
        print(
            f"{season_label(year)}  riadkov {len(df):>5}  začali {int(df['started'].sum()):>5}  "
            f"odchýlky {len(bad)}"
        )
    goalies = pd.concat(parts, ignore_index=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    goalies.to_parquet(out, index=False)
    bad = pd.concat(problems, ignore_index=True)
    print(f"\nUložené: {out}  ({len(goalies)} riadkov, {goalies['player_id'].nunique()} brankárov)")
    if len(bad):
        bad.to_csv(out.with_name("nhl_goalies_problems.csv"), index=False)
        print(f"POZOR: {len(bad)} odchýlok, zoznam v {out.with_name('nhl_goalies_problems.csv')}")
    return goalies


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2006)
    ap.add_argument("--to", dest="last", type=int, default=2026)
    a = ap.parse_args()
    main(a.first, a.last)
