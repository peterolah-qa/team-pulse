"""Glicko-2 pre NHL – kandidát namiesto Ela (alebo vedľa neho).

Oproti Elu má každý klub okrem sily aj neistotu (RD) a volatilitu:
  * po lete sa neistota zvýši (rd_season) → prvé zápasy sezóny posúvajú rating viac,
  * predpoveď s veľkou neistotou je opatrnejšia (bližšie k 50 %).
Výsledok zápasu je len výhra/prehra (Glicko nepozná rozdiel skóre, Elo áno).

Vzorce: Glickman, „Example of the Glicko-2 system“ (2012). Každý zápas = vlastné obdobie,
domáca výhoda sa pripočíta k sile domácich ako pri Elu.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

SCALE = 173.7178  # Glicko-2 ↔ bežná stupnica (400 / ln 10)
MAX_RD = 350.0


@dataclass(frozen=True)
class GlickoParams:
    tau: float = 0.5  # ako rýchlo sa môže meniť volatilita
    hca: float = 30.0  # domáca výhoda v bodoch (rovnaká stupnica ako Elo)
    rd_season: float = 100.0  # o koľko narastie neistota cez leto
    carryover: float = 1.0  # podiel sily, ktorý prejde do novej sezóny (1 = bez návratu k priemeru)
    rd_start: float = 200.0  # neistota klubu v prvom zápase dát / nového klubu
    sigma: float = 0.06  # počiatočná volatilita
    mean: float = 1505.0


START = GlickoParams()


def g(phi: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / math.pi**2)


def win_prob(mu: float, mu_opp: float, phi: float) -> float:
    """Pravdepodobnosť výhry (vnútorná stupnica Glicko-2), phi = neistota súpera alebo spoločná."""
    return 1.0 / (1.0 + math.exp(-g(phi) * (mu - mu_opp)))


def _volatility(phi: float, sigma: float, v: float, delta: float, tau: float) -> float:
    """Nová volatilita (Illinoisova metóda z článku Glickmana)."""
    a = math.log(sigma * sigma)

    def f(x: float) -> float:
        ex = math.exp(x)
        return ex * (delta**2 - phi**2 - v - ex) / (2 * (phi**2 + v + ex) ** 2) - (x - a) / tau**2

    lo = a
    if delta**2 > phi**2 + v:
        hi = math.log(delta**2 - phi**2 - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        hi = a - k * tau
    f_lo, f_hi = f(lo), f(hi)
    while abs(hi - lo) > 1e-6:
        c = lo + (lo - hi) * f_lo / (f_hi - f_lo)
        f_c = f(c)
        if f_c * f_hi <= 0:
            lo, f_lo = hi, f_hi
        else:
            f_lo /= 2
        hi, f_hi = c, f_c
    return math.exp(lo / 2)


def update_one(
    mu: float, phi: float, sigma: float, mu_opp: float, phi_opp: float, score: float, tau: float
) -> tuple[float, float, float]:
    """Jeden klub po jednom zápase (vnútorná stupnica). score 1 = výhra, 0 = prehra."""
    gj = g(phi_opp)
    e = win_prob(mu, mu_opp, phi_opp)
    v = 1.0 / (gj * gj * e * (1 - e))
    delta = v * gj * (score - e)
    new_sigma = _volatility(phi, sigma, v, delta, tau)
    phi_star = math.sqrt(phi * phi + new_sigma * new_sigma)
    new_phi = 1.0 / math.sqrt(1.0 / phi_star**2 + 1.0 / v)
    return mu + new_phi**2 * gj * (score - e), new_phi, new_sigma


def season_reset(mu: float, phi: float, p: GlickoParams) -> tuple[float, float]:
    """Leto: sila sa (voliteľne) vráti k priemeru, neistota narastie."""
    phi = min(math.sqrt(phi**2 + (p.rd_season / SCALE) ** 2), MAX_RD / SCALE)
    return p.carryover * mu, phi


def run(games: pd.DataFrame, p: GlickoParams = START) -> pd.DataFrame:
    """Chronologicky doplní rating a neistotu pred zápasom a pravdepodobnosť výhry domácich.

    Výstupné stĺpce: glicko_home_pre, glicko_away_pre (bežná stupnica), rd_home_pre, rd_away_pre,
    glicko_prob (s domácou výhodou), glicko_logit (bez domácej výhody, pre logistickú regresiu).
    """
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    df = games.sort_values(order, kind="stable").reset_index(drop=True).copy()
    neutral = df["neutral"].astype(bool).to_numpy() if "neutral" in df else [False] * len(df)
    state: dict[str, list[float]] = {}  # klub → [mu, phi, sigma]
    season: dict[str, int] = {}
    hca = p.hca / SCALE
    out = {k: [] for k in ("glicko_home_pre", "glicko_away_pre", "rd_home_pre", "rd_away_pre", "glicko_prob",
                           "glicko_logit")}  # fmt: skip

    for i, r in enumerate(df.itertuples(index=False)):
        for team in (r.home, r.away):
            if team not in state:
                state[team] = [0.0, p.rd_start / SCALE, p.sigma]
            elif season[team] != r.season:
                state[team][0], state[team][1] = season_reset(state[team][0], state[team][1], p)
            season[team] = r.season
        (mh, ph, sh), (ma, pa, sa) = state[r.home], state[r.away]
        edge = 0.0 if neutral[i] else hca
        both = math.sqrt(ph * ph + pa * pa)
        out["glicko_home_pre"].append(p.mean + mh * SCALE)
        out["glicko_away_pre"].append(p.mean + ma * SCALE)
        out["rd_home_pre"].append(ph * SCALE)
        out["rd_away_pre"].append(pa * SCALE)
        out["glicko_prob"].append(win_prob(mh + edge, ma, both))
        out["glicko_logit"].append(g(both) * (mh - ma))
        won = 1.0 if r.goals_home > r.goals_away else 0.0
        state[r.home] = list(update_one(mh + edge, ph, sh, ma, pa, won, p.tau))
        state[r.home][0] -= edge
        state[r.away] = list(update_one(ma, pa, sa, mh + edge, ph, 1.0 - won, p.tau))

    for k, v in out.items():
        df[k] = v
    return df
