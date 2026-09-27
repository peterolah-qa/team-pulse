"""Replikačný test: naše Elo vs. archív FiveThirtyEight (pokračovanie Neila Painea).

Stiahni archív:
    curl -L -o data/ref/nba_elo.csv \
      https://raw.githubusercontent.com/Neil-Paine-1/NBA-elo/main/nba_elo.csv

Spusti:  uv run python -m team_pulse.replicate_538 [--from 2000]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from team_pulse.elo import EloParams, run

REF = Path("data/ref/nba_elo.csv")

# presťahované / premenované franšízy → jeden kód, aby sa rating prenášal
FRANCHISE = {"VAN": "MEM", "CHH": "NOP", "NOH": "NOP", "NOK": "NOP", "SEA": "OKC", "NJN": "BRK"}


def load_reference(path: Path = REF, from_season: int = 2000) -> pd.DataFrame:
    d = pd.read_csv(path)
    d = d[d["season"] >= from_season].copy()
    # archív má každý zápas 2× (z pohľadu oboch teamov) → jeden riadok na zápas
    home_rows = d[(d["is_home"] == 1) | ((d["neutral"] == 1) & (d["team1"] < d["team2"]))]
    g = home_rows.rename(
        columns={"team1": "home", "team2": "away", "score1": "pts_home", "score2": "pts_away"}
    )
    g["home"] = g["home"].replace(FRANCHISE)
    g["away"] = g["away"].replace(FRANCHISE)
    g["date"] = pd.to_datetime(g["date"])
    return g.sort_values("date", kind="stable").reset_index(drop=True)


def initial_ratings(ref: pd.DataFrame) -> dict[str, float]:
    """Rating každého teamu pred jeho prvým zápasom v prvej sezóne výrezu."""
    first_season = ref["season"].min()
    s = ref[ref["season"] == first_season]
    init: dict[str, float] = {}
    for row in s.itertuples(index=False):
        init.setdefault(row.home, row.elo1_pre)
        init.setdefault(row.away, row.elo2_pre)
    return init


def compare(from_season: int = 2000, path: Path = REF) -> dict[str, float]:
    ref = load_reference(path, from_season)
    ours = run(
        ref[["date", "season", "home", "away", "pts_home", "pts_away", "neutral"]],
        EloParams(),
        initial=initial_ratings(ref),
    )
    diff_elo = (ours["elo_home_pre"] - ref["elo1_pre"]).abs()
    diff_p = (ours["prob_home"] - ref["elo_prob1"]).abs()
    return {
        "games": float(len(ref)),
        "elo_mae": float(diff_elo.mean()),
        "elo_max": float(diff_elo.max()),
        "prob_mae": float(diff_p.mean()),
        "prob_max": float(diff_p.max()),
        "share_within_1": float((diff_elo < 1.0).mean()),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_season", type=int, default=2000)
    a = ap.parse_args()
    r = compare(a.from_season)
    print(f"Zápasy: {int(r['games'])}")
    print(f"Elo  – priemerná odchýlka {r['elo_mae']:.4f}, max {r['elo_max']:.4f}")
    print(f"Prob – priemerná odchýlka {r['prob_mae']:.6f}, max {r['prob_max']:.6f}")
    print(f"Zápasy s odchýlkou pod 1 Elo: {r['share_within_1']:.2%}")
