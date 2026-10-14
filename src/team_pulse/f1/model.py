"""F1 model: šanca na víťazstvo pre každého jazdca na štarte (tip po kvalifikácii).

Vrstvy:
  kvalifikácia  ln(šanca na víťazstvo z daného miesta v kvalifikácii), tabuľka z tréningových sezón
  Elo jazdca    z poradia v cieli, každý s každým (rating pred pretekmi = len skoršie preteky)
  Elo tímu      to isté pre tím (oba vozy), tímy spojené cez premenovania (LINEAGE)
Šance: podmienený logit (softmax cez jazdcov na štarte), váhy z tréningových sezón.
Pódium: Plackett-Luce z tých istých skóre (presne, cez prvé tri miesta).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MEAN = 1500.0
# Tím pokračuje pod dnešným menom (rovnaká továreň a ľudia, iný názov).
LINEAGE = {
    "lotus_f1": "alpine", "renault": "alpine",
    "toro_rosso": "rb", "alphatauri": "rb",
    "force_india": "aston_martin", "racing_point": "aston_martin",
    "sauber": "audi", "alfa": "audi",
    "manor": "marussia",
}  # fmt: skip
FEATURES = ["quali", "elo_driver", "elo_team"]


@dataclass(frozen=True)
class EloParams:
    k_driver: float = 24.0
    k_team: float = 24.0
    carry: float = 0.7  # na začiatku sezóny sa rating vráti k priemeru: MEAN + carry · (rating − MEAN)


def team_of(constructor: str) -> str:
    return LINEAGE.get(constructor, constructor)


def races(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Preteky v poradí (sezóna, kolo), každé ako tabuľka jazdcov zoradená podľa poradia v cieli."""
    df = df.sort_values(["season", "round", "position"], kind="stable")
    return [g for _, g in df.groupby(["season", "round"], sort=False)]


def _pairwise(r: np.ndarray, pos: np.ndarray, same: np.ndarray | None = None) -> np.ndarray:
    """Zmena ratingu za jedny preteky (bez K): skutočné výhry v dueloch − očakávané, / (N − 1)."""
    n = len(r)
    exp = 1.0 / (1.0 + 10 ** ((r[None, :] - r[:, None]) / 400.0))  # exp[i, j] = šanca, že i porazí j
    won = (pos[:, None] < pos[None, :]).astype(float)
    mask = ~np.eye(n, dtype=bool) if same is None else ~(np.eye(n, dtype=bool) | same)
    return ((won - exp) * mask).sum(axis=1) / max(n - 1, 1)


def elo_ratings(df: pd.DataFrame, p: EloParams) -> pd.DataFrame:
    """Ku každému riadku rating jazdca a tímu PRED týmito pretekmi (vidí len skoršie preteky)."""
    drv: dict[str, float] = {}
    team: dict[str, float] = {}
    season = None
    out = []
    for g in races(df):
        s = int(g["season"].iloc[0])
        if season is not None and s != season:
            drv = {k: MEAN + p.carry * (v - MEAN) for k, v in drv.items()}
            team = {k: MEAN + p.carry * (v - MEAN) for k, v in team.items()}
        season = s
        teams = g["constructor"].map(team_of).to_numpy()
        rd = np.array([drv.get(d, MEAN) for d in g["driver"]])
        rt = np.array([team.get(t, MEAN) for t in teams])
        out.append(g.assign(elo_driver=rd, elo_team=rt))
        pos = g["position"].to_numpy()
        rd_new = rd + p.k_driver * _pairwise(rd, pos)
        same = teams[:, None] == teams[None, :]  # tímoví kolegovia sa pri tíme neporovnávajú
        dt = p.k_team * _pairwise(rt, pos, same)
        for d, v in zip(g["driver"], rd_new, strict=True):
            drv[d] = v
        for t in np.unique(teams):  # oba vozy tímu: priemer zmien
            team[t] = rt[teams == t][0] + dt[teams == t].mean()
    return pd.concat(out, ignore_index=True)


def quali_slot(df: pd.DataFrame) -> pd.Series:
    """Miesto v kvalifikácii; bez času v kvalifikácii = za posledným v tých pretekoch."""
    last = (
        df.groupby(["season", "round"])["quali"]
        .transform("max")
        .fillna(df.groupby(["season", "round"])["driver"].transform("size"))
    )
    return df["quali"].fillna(last + 1).astype(int)


def win_table(slot: pd.Series, won: pd.Series, max_slot: int = 26) -> np.ndarray:
    """Podiel víťazstiev z miesta 1 … max_slot, vyhladený (+0,5 víťazstva / +1 štart) – nikdy nie nula."""
    wins = np.zeros(max_slot + 1)
    starts = np.zeros(max_slot + 1)
    for s, w in zip(slot.clip(upper=max_slot), won, strict=True):
        starts[s] += 1
        wins[s] += w
    return (wins + 0.5) / (starts + 1.0)


def features(df: pd.DataFrame, table: np.ndarray) -> pd.DataFrame:
    """Vstupy logitu: ln šance z kvalifikácie, Elo jazdca a tímu oproti priemeru poľa (v stovkách)."""
    slot = quali_slot(df).clip(upper=len(table) - 1)
    key = [df["season"], df["round"]]
    return pd.DataFrame({
        "quali": np.log(table[slot.to_numpy()]),
        "elo_driver": (df["elo_driver"] - df.groupby(key)["elo_driver"].transform("mean")) / 100.0,
        "elo_team": (df["elo_team"] - df.groupby(key)["elo_team"].transform("mean")) / 100.0,
    }, index=df.index)  # fmt: skip


def softmax_by_race(score: np.ndarray, race_id: np.ndarray) -> np.ndarray:
    out = np.empty_like(score, dtype=float)
    for r in np.unique(race_id):
        m = race_id == r
        e = np.exp(score[m] - score[m].max())
        out[m] = e / e.sum()
    return out


def fit_logit(x: np.ndarray, won: np.ndarray, race_id: np.ndarray, iters: int = 50) -> np.ndarray:
    """Váhy podmieneného logitu (Newton). Max. vierohodnosť víťaza každých pretekov."""
    w = np.zeros(x.shape[1])
    for _ in range(iters):
        p = softmax_by_race(x @ w, race_id)
        grad = np.zeros_like(w)
        hess = np.zeros((len(w), len(w)))
        for r in np.unique(race_id):
            m = race_id == r
            xm, pm = x[m], p[m]
            mu = pm @ xm
            grad += x[m][won[m] == 1].sum(axis=0) - mu
            hess -= (xm * pm[:, None]).T @ xm - np.outer(mu, mu)
        step = np.linalg.solve(hess - 1e-6 * np.eye(len(w)), grad)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def podium(p: np.ndarray) -> np.ndarray:
    """Šanca každého jazdca byť do 3. miesta (Plackett-Luce zo šancí na víťazstvo)."""
    n = len(p)
    out = p.copy()
    for i in range(n):
        for j in range(n):
            if j == i:
                continue
            pj = p[j]
            rest_j = 1 - pj
            out[i] += pj * p[i] / rest_j  # j prvý, i druhý
            for k in range(n):
                if k in (i, j):
                    continue
                pk2 = pj * p[k] / rest_j
                out[i] += pk2 * p[i] / (rest_j - p[k])  # j prvý, k druhý, i tretí
    return out
