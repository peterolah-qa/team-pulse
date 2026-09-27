"""Vrstva A – Elo podľa FiveThirtyEight.

Vzorce:
    E      = 1 / (1 + 10^(-(R_home + HCA - R_away) / 400))
    K      = 20 * (MOV + 3)^0.8 / (7.5 + 0.006 * D_winner)
    R_new  = R + K * (S - E)
    sezóna = 0.75 * R + 0.25 * 1505

Dôležité: pre každý zápas sa ukladá rating PRED zápasom (elo_home_pre),
takže predpoveď nikdy nevidí výsledok zápasu, ktorý predpovedá.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

ELO_PER_POINT = 28.0


@dataclass(frozen=True)
class EloParams:
    k: float = 20.0
    hca: float = 100.0  # FiveThirtyEight: +100, náš variant štart +70 (určí backtest)
    new_team: float = 1300.0  # nový team (expanzia)
    mean: float = 1505.0  # priemer ligy, k nemu sa ratingy vracajú medzi sezónami
    carryover: float = 0.75  # podiel ratingu, ktorý prejde do novej sezóny
    early_boost: float = 0.0  # dynamický K: o koľko vyšší K na začiatku sezóny (0 = FiveThirtyEight)
    early_games: int = 20  # počet zápasov, počas ktorých zvýšenie K klesne na nulu


DEFAULT_PARAMS = EloParams()


def expected_home(elo_home: float, elo_away: float, hca: float, neutral: bool = False) -> float:
    """Pravdepodobnosť výhry domácich."""
    diff = elo_home - elo_away + (0.0 if neutral else hca)
    return 1.0 / (1.0 + 10.0 ** (-diff / 400.0))


def k_factor(mov: int, elo_diff_winner: float, k: float = 20.0) -> float:
    """K s úpravou o rozdiel skóre; výhra favorita sa počíta menej než prekvapenie."""
    return k * (abs(mov) + 3) ** 0.8 / (7.5 + 0.006 * elo_diff_winner)


def update(
    elo_home: float,
    elo_away: float,
    pts_home: int,
    pts_away: int,
    p: EloParams = DEFAULT_PARAMS,
    neutral: bool = False,
) -> tuple[float, float]:
    """Vráti (nové Elo domácich, nové Elo hostí) po jednom zápase."""
    if pts_home == pts_away:
        raise ValueError("NBA zápas nemôže skončiť remízou")
    hca = 0.0 if neutral else p.hca
    e_home = expected_home(elo_home, elo_away, p.hca, neutral)
    home_won = pts_home > pts_away
    diff_winner = (elo_home + hca - elo_away) if home_won else (elo_away - elo_home - hca)
    k = k_factor(pts_home - pts_away, diff_winner, p.k)
    delta = k * ((1.0 if home_won else 0.0) - e_home)
    return elo_home + delta, elo_away - delta


def season_reset(elo: float, p: EloParams = DEFAULT_PARAMS) -> float:
    return p.carryover * elo + (1.0 - p.carryover) * p.mean


def spread(elo_home: float, elo_away: float, hca: float, neutral: bool = False) -> float:
    """Očakávaný rozdiel skóre v bodoch v prospech domácich."""
    return (elo_home - elo_away + (0.0 if neutral else hca)) / ELO_PER_POINT


def early_multiplier(games_played: float, p: EloParams) -> float:
    """Násobok K: na začiatku sezóny 1 + early_boost, po early_games zápasoch 1."""
    if p.early_boost == 0:
        return 1.0
    return 1.0 + p.early_boost * max(0.0, 1.0 - games_played / p.early_games)


def run(
    games: pd.DataFrame, p: EloParams = DEFAULT_PARAMS, initial: dict[str, float] | None = None
) -> pd.DataFrame:
    """Prejde zápasy chronologicky a doplní Elo pred/po zápase a pravdepodobnosť.

    Očakávané stĺpce: date, season, home, away, pts_home, pts_away, [neutral]
    """
    req = {"date", "season", "home", "away", "pts_home", "pts_away"}
    missing = req - set(games.columns)
    if missing:
        raise ValueError(f"chýbajú stĺpce: {sorted(missing)}")

    g = games.sort_values(["date"], kind="stable").reset_index(drop=True).copy()
    neutral = g["neutral"].astype(bool) if "neutral" in g else pd.Series(False, index=g.index)
    ratings: dict[str, float] = dict(initial or {})
    last_season: dict[str, int] = {}
    played: dict[str, int] = {}
    pre_h, pre_a, prob, post_h, post_a = [], [], [], [], []

    for i, row in enumerate(g.itertuples(index=False)):
        for team in (row.home, row.away):
            if team not in ratings:
                ratings[team] = p.new_team
            elif last_season.get(team) is not None and last_season[team] != row.season:
                ratings[team] = season_reset(ratings[team], p)
            if last_season.get(team) != row.season:
                played[team] = 0
            last_season[team] = row.season

        rh, ra = ratings[row.home], ratings[row.away]
        nt = bool(neutral.iat[i])
        pre_h.append(rh)
        pre_a.append(ra)
        prob.append(expected_home(rh, ra, p.hca, nt))
        mult = early_multiplier((played[row.home] + played[row.away]) / 2, p)
        pk = p if mult == 1.0 else replace(p, k=p.k * mult)
        nh, na = update(rh, ra, int(row.pts_home), int(row.pts_away), pk, nt)
        played[row.home] += 1
        played[row.away] += 1
        ratings[row.home], ratings[row.away] = nh, na
        post_h.append(nh)
        post_a.append(na)

    g["elo_home_pre"], g["elo_away_pre"] = pre_h, pre_a
    g["prob_home"] = prob
    g["elo_home_post"], g["elo_away_post"] = post_h, post_a
    return g
