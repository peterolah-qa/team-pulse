"""Hokejové Elo (vrstva A pre NHL).

Rovnaký princíp ako pri NBA, iné čísla: v hokeji padne málo gólov, takže rozdiel skóre
sa počíta logaritmicky. Štartové hodnoty podľa FiveThirtyEight, ladí sa len na tréningu.

    E      = 1 / (1 + 10^(-(R_home + HCA - R_away) / 400))
    násobok = (0,6686 · ln(rozdiel gólov) + 0,8048) · 2,05 / (0,001 · D_víťaz + 2,05)
    R_new  = R + K · násobok · (S − E)
    sezóna = carryover · R + (1 − carryover) · 1505

Výhra po predĺžení alebo nájazdoch je výhra (S = 1), rozdiel gólov je vtedy 1.
Pre každý zápas sa ukladá rating PRED zápasom, takže predpoveď nevidí vlastný výsledok.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from team_pulse.elo import expected_home


@dataclass(frozen=True)
class HockeyEloParams:
    k: float = 6.0
    hca: float = 50.0
    carryover: float = 0.7
    mean: float = 1505.0
    new_team: float = 1505.0  # nový klub (Vegas 2017, Seattle 2021) začína na priemere ligy


START = HockeyEloParams()


def mov_multiplier(goal_diff: int, elo_diff_winner: float) -> float:
    """Väčšia výhra posunie rating viac; výhra favorita sa počíta menej než prekvapenie."""
    return (0.6686 * math.log(abs(goal_diff)) + 0.8048) * 2.05 / (elo_diff_winner * 0.001 + 2.05)


def update(
    elo_home: float,
    elo_away: float,
    goals_home: int,
    goals_away: int,
    p: HockeyEloParams = START,
    neutral: bool = False,
) -> tuple[float, float]:
    """Vráti (nové Elo domácich, nové Elo hostí) po jednom zápase."""
    if goals_home == goals_away:
        raise ValueError("zápas NHL nemôže skončiť remízou (od 2005/06 rozhodnú nájazdy)")
    hca = 0.0 if neutral else p.hca
    e_home = expected_home(elo_home, elo_away, p.hca, neutral)
    home_won = goals_home > goals_away
    diff_winner = (elo_home + hca - elo_away) if home_won else (elo_away - elo_home - hca)
    delta = p.k * mov_multiplier(goals_home - goals_away, diff_winner) * ((1.0 if home_won else 0.0) - e_home)
    return elo_home + delta, elo_away - delta


def season_reset(elo: float, p: HockeyEloParams = START) -> float:
    return p.carryover * elo + (1.0 - p.carryover) * p.mean


def run(games: pd.DataFrame, p: HockeyEloParams = START) -> pd.DataFrame:
    """Prejde zápasy chronologicky a doplní Elo pred/po zápase a pravdepodobnosť výhry domácich.

    Očakávané stĺpce: game_id, season, home, away, goals_home, goals_away, [start_utc | date], [neutral]
    """
    req = {"game_id", "season", "home", "away", "goals_home", "goals_away"}
    missing = req - set(games.columns)
    if missing:
        raise ValueError(f"chýbajú stĺpce: {sorted(missing)}")
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    g = games.sort_values(order, kind="stable").reset_index(drop=True).copy()
    neutral = g["neutral"].astype(bool).to_numpy() if "neutral" in g else [False] * len(g)

    ratings: dict[str, float] = {}
    last_season: dict[str, int] = {}
    pre_h, pre_a, prob, post_h, post_a = [], [], [], [], []
    for i, row in enumerate(g.itertuples(index=False)):
        for team in (row.home, row.away):
            if team not in ratings:
                ratings[team] = p.new_team
            elif last_season[team] != row.season:
                ratings[team] = season_reset(ratings[team], p)
            last_season[team] = row.season
        rh, ra = ratings[row.home], ratings[row.away]
        nt = bool(neutral[i])
        pre_h.append(rh)
        pre_a.append(ra)
        prob.append(expected_home(rh, ra, p.hca, nt))
        nh, na = update(rh, ra, int(row.goals_home), int(row.goals_away), p, nt)
        ratings[row.home], ratings[row.away] = nh, na
        post_h.append(nh)
        post_a.append(na)

    g["elo_home_pre"], g["elo_away_pre"] = pre_h, pre_a
    g["prob_home"] = prob
    g["elo_home_post"], g["elo_away_post"] = post_h, post_a
    return g
