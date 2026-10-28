"""Zápasy NFL z nflverse games.csv (Lee Sharpe, github.com/nflverse/nfldata).

Zdroj: „nflverse / Lee Sharpe“. Súbor obsahuje aj stávkové stĺpce (moneyline, spread, total); tie sa
**nenačítajú vôbec** – čítajú sa len stĺpce zo zoznamu ALLOWED (zoznam povolených, nie zakázaných).
Surový súbor sa ukladá do data/raw/nfl/ a necommituje sa.

Brána G0-NFL používa pripnutý commit G0_COMMIT (docs/gate-nfl-G0.md), ostrá prevádzka najnovší súbor.

Spustenie (stiahne súbor a overí počty):  uv run python -m team_pulse.nfl.games [--commit SHA]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

G0_COMMIT = "a6b91bf54e55b0ac8970dfaef3b3dfb9ce438210"
URL = "https://raw.githubusercontent.com/nflverse/nfldata/{commit}/data/games.csv"
RAW = Path("data/raw/nfl")
SOURCE = "nflverse / Lee Sharpe (github.com/nflverse/nfldata)"

# Jediné stĺpce, ktoré sa z games.csv čítajú. Stávkové (away_moneyline, home_moneyline, spread_line,
# away_spread_odds, home_spread_odds, total_line, under_odds, over_odds) tu zámerne nie sú.
ALLOWED = (
    "game_id",
    "season",
    "game_type",
    "week",
    "gameday",
    "gametime",
    "away_team",
    "away_score",
    "home_team",
    "home_score",
    "location",
    "overtime",
    "espn",
    "away_rest",
    "home_rest",
    "div_game",
    "roof",
    "surface",
    "away_qb_id",
    "home_qb_id",
    "away_qb_name",
    "home_qb_name",
    "stadium_id",
    "stadium",
)
BETTING = (
    "away_moneyline",
    "home_moneyline",
    "spread_line",
    "away_spread_odds",
    "home_spread_odds",
    "total_line",
    "under_odds",
    "over_odds",
)
GAME_TYPES = ("REG", "WC", "DIV", "CON", "SB")

# Presťahované kluby = jedna franšíza (Elo pokračuje): Oakland → Las Vegas, San Diego → LA Chargers,
# St. Louis → LA Rams. Skratky podľa dnešného games.csv.
FRANCHISE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

# Očakávaný počet zápasov (základná časť, play-off) podľa NFL; brána G0-NFL kritérium 1.
EXPECTED = (
    {s: (248, 11) for s in range(1999, 2002)}
    | {s: (256, 11) for s in range(2002, 2020)}
    | {2020: (256, 13), 2021: (272, 13), 2022: (271, 13)}  # 2022: zrušený BUF – CIN
    | {s: (272, 13) for s in range(2023, 2026)}
)


def franchise(team: str) -> str:
    return FRANCHISE.get(team, team)


def path_for(commit: str) -> Path:
    return RAW / f"games_{commit[:7]}.csv"


def download(commit: str = G0_COMMIT, session: requests.Session | None = None) -> Path:
    """Stiahne games.csv z daného commitu (ak už nie je stiahnutý)."""
    out = path_for(commit)
    if out.exists():
        return out
    r = (session or requests.Session()).get(URL.format(commit=commit), timeout=60)
    r.raise_for_status()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    return out


def load(path: Path) -> pd.DataFrame:
    """games.csv → jeden riadok na zápas, len povolené stĺpce, jednotné názvy pre Elo.

    Stĺpce výstupu: game_id, season, game_type, week, date, home, away, score_home, score_away,
    neutral, played (výsledok známy), tie, espn_id, home_rest, away_rest, home_qb, away_qb, ...
    """
    raw = pd.read_csv(path, usecols=lambda c: c in ALLOWED, dtype={"espn": "string"})
    missing = set(ALLOWED) - set(raw.columns)
    if missing:
        raise ValueError(f"games.csv: chýbajú stĺpce {sorted(missing)}")
    bad = raw.loc[~raw["game_type"].isin(GAME_TYPES), "game_type"].unique()
    if len(bad):
        raise ValueError(f"games.csv: neznámy typ zápasu {list(bad)}")
    if raw["game_id"].duplicated().any():
        raise ValueError("games.csv: zápas dvakrát")
    g = pd.DataFrame(
        {
            "game_id": raw["game_id"],
            "season": raw["season"].astype(int),
            "game_type": raw["game_type"],
            "playoff": raw["game_type"] != "REG",
            "week": raw["week"].astype(int),
            "date": pd.to_datetime(raw["gameday"]),
            "gametime": raw["gametime"],
            "home": raw["home_team"].map(franchise),
            "away": raw["away_team"].map(franchise),
            "score_home": raw["home_score"],
            "score_away": raw["away_score"],
            "neutral": raw["location"].eq("Neutral"),
            "espn_id": raw["espn"],
            "home_rest": raw["home_rest"],
            "away_rest": raw["away_rest"],
            "div_game": raw["div_game"].astype(bool),
            "home_qb": raw["home_qb_name"],
            "away_qb": raw["away_qb_name"],
            "home_qb_id": raw["home_qb_id"],
            "away_qb_id": raw["away_qb_id"],
        }
    )
    g["played"] = g["score_home"].notna() & g["score_away"].notna()
    g["tie"] = g["played"] & (g["score_home"] == g["score_away"])
    return g.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


def check_counts(games: pd.DataFrame, seasons: range | None = None) -> list[str]:
    """Rozdiely oproti EXPECTED (prázdny zoznam = všetko sedí). Rátajú sa len odohrané zápasy."""
    problems = []
    played = games[games["played"]]
    for s in seasons or sorted(EXPECTED):
        d = played[played["season"] == s]
        got = (int((~d["playoff"]).sum()), int(d["playoff"].sum()))
        if got != EXPECTED[s]:
            problems.append(f"{s}: základná časť + play-off {got}, má byť {EXPECTED[s]}")
    return problems


def main(commit: str = G0_COMMIT) -> int:
    path = download(commit)
    g = load(path)
    print(f"{path}: {len(g)} zápasov, sezóny {g['season'].min()} – {g['season'].max()}")
    problems = check_counts(g)
    print("\n".join(problems) or "Počty po sezónach 1999 – 2025 sedia.")
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default=G0_COMMIT)
    raise SystemExit(main(ap.parse_args().commit))
