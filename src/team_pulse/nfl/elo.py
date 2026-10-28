"""Elo tímov NFL podľa FiveThirtyEight (vrstva A pre NFL).

    rozdiel = R_dom − R_hos + HFA (na neutrálnom ihrisku bez HFA); v play-off × 1,2
    E       = 1 / (1 + 10^(−rozdiel / 400))
    násobok = ln(|rozdiel skóre| + 1) · 2,2 / (0,001 · rozdiel_víťaza + 2,2)
    R_nové  = R + K · násobok · (S − E)
    sezóna  = prenos · R + (1 − prenos) · 1505

Remíza: S = 0,5 a násobok 1 (docs/gate-nfl-G0.md: „v Ele sa počíta ako polovica výhry“;
ln(1) by ju vynulovalo).
Nový klub (Houston 2002) začína na 1300 ako pri FiveThirtyEight; kluby v prvej sezóne dát (1999) na 1505.
Pre každý zápas sa ukladá rating PRED zápasom, takže predpoveď nevidí vlastný výsledok.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class NflEloParams:
    k: float = 20.0
    hfa: float = 48.0
    carryover: float = 2.0 / 3.0
    playoff_mult: float = 1.2
    mean: float = 1505.0
    new_team: float = 1300.0


START = NflEloParams()


def diff(elo_home: float, elo_away: float, p: NflEloParams, neutral: bool, playoff: bool) -> float:
    d = elo_home - elo_away + (0.0 if neutral else p.hfa)
    return d * p.playoff_mult if playoff else d


def expected(d: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-d / 400.0))


def mov_multiplier(point_diff: float, elo_diff_winner: float) -> float:
    return math.log(abs(point_diff) + 1.0) * 2.2 / (elo_diff_winner * 0.001 + 2.2)


def update(
    elo_home: float,
    elo_away: float,
    score_home: float,
    score_away: float,
    p: NflEloParams = START,
    neutral: bool = False,
    playoff: bool = False,
) -> tuple[float, float]:
    """Vráti (nové Elo domácich, nové Elo hostí) po jednom zápase."""
    d = diff(elo_home, elo_away, p, neutral, playoff)
    e = expected(d)
    if score_home == score_away:
        s, mult = 0.5, 1.0
    else:
        home_won = score_home > score_away
        s = 1.0 if home_won else 0.0
        mult = mov_multiplier(score_home - score_away, d if home_won else -d)
    delta = p.k * mult * (s - e)
    return elo_home + delta, elo_away - delta


def run(games: pd.DataFrame, p: NflEloParams = START) -> pd.DataFrame:
    """Prejde odohrané zápasy chronologicky; doplní Elo pred / po zápase a šancu domácich (prob_home).

    Očakávané stĺpce (team_pulse.nfl.games.load): game_id, season, date, home, away, score_home,
    score_away, neutral, playoff. Neodohrané zápasy (bez skóre) dostanú šancu z aktuálnych ratingov,
    ratingy nemenia.
    """
    g = games.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True).copy()
    first_season = int(g["season"].min())
    ratings: dict[str, float] = {}
    last_season: dict[str, int] = {}
    pre_h, pre_a, prob, post_h, post_a = [], [], [], [], []
    for row in g.itertuples(index=False):
        for team in (row.home, row.away):
            if team not in ratings:
                ratings[team] = p.mean if row.season == first_season else p.new_team
            elif last_season[team] != row.season:
                ratings[team] = p.carryover * ratings[team] + (1.0 - p.carryover) * p.mean
            last_season[team] = row.season
        rh, ra = ratings[row.home], ratings[row.away]
        pre_h.append(rh)
        pre_a.append(ra)
        prob.append(expected(diff(rh, ra, p, bool(row.neutral), bool(row.playoff))))
        if pd.notna(row.score_home) and pd.notna(row.score_away):
            rh, ra = update(rh, ra, row.score_home, row.score_away, p, bool(row.neutral), bool(row.playoff))
            ratings[row.home], ratings[row.away] = rh, ra
        post_h.append(rh)
        post_a.append(ra)
    g["elo_home_pre"], g["elo_away_pre"], g["prob_home"] = pre_h, pre_a, prob
    g["elo_home_post"], g["elo_away_post"] = post_h, post_a
    return g
