"""Ladenie dynamického K – LEN na tréningových sezónach (testovacie sa nesmú použiť).

Spustenie:  uv run python -m team_pulse.tune
"""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd

from team_pulse.backtest import metrics
from team_pulse.elo import EloParams, run
from team_pulse.learned import GAMES, TRAIN

BOOSTS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
WINDOWS = [10, 20, 30]


def grid(games: pd.DataFrame, hca: float = 70) -> pd.DataFrame:
    teams = set(games["home"]) | set(games["away"])
    train = games["season"].between(*TRAIN).to_numpy()
    home_won = (games["pts_home"] > games["pts_away"]).to_numpy()
    rows = []
    for boost, window in product(BOOSTS, WINDOWS):
        if boost == 0 and window != WINDOWS[0]:
            continue  # bez zvýšenia na okne nezáleží
        p = EloParams(hca=hca, early_boost=boost, early_games=window)
        res = run(games, p, initial={t: p.mean for t in teams})
        m = metrics(res["prob_home"][train], pd.Series(home_won[train]))
        rows.append({"early_boost": boost, "early_games": window, **m})
    return pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    games = pd.read_parquet(a.games).sort_values("date", kind="stable").reset_index(drop=True)
    g = grid(games)
    print(f"Tréningové sezóny {TRAIN[0]}–{TRAIN[1]}, zoradené podľa log loss (nižší = lepší):\n")
    print(g[["early_boost", "early_games", "accuracy", "log_loss", "brier"]].round(4).to_string(index=False))
