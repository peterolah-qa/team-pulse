"""Backtest: ako dobre model predpovedal zápasy, ktoré ešte nevidel.

Spustenie:  uv run python -m team_pulse.backtest
Výstup:     reports/backtest.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from team_pulse.elo import EloParams, run

GAMES = Path("data/raw/games.parquet")
REPORT = Path("reports/backtest.md")
BURN_IN = 3  # prvé sezóny, kým sa Elo „rozbehne“ zo štartu 1505, sa nehodnotia


def metrics(prob: pd.Series, home_won: pd.Series) -> dict[str, float]:
    """Presnosť, log loss a Brier score (nižšie = lepšie pre log loss a Brier)."""
    p = prob.clip(1e-6, 1 - 1e-6).to_numpy()
    y = home_won.astype(float).to_numpy()
    return {
        "n": float(len(y)),
        "accuracy": float(((p > 0.5) == (y == 1)).mean()),
        "log_loss": float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()),
        "brier": float(((p - y) ** 2).mean()),
    }


def calibration(prob: pd.Series, home_won: pd.Series, bins: int = 10) -> pd.DataFrame:
    """Pre každé pásmo predpovede: priemerná predpoveď vs. skutočnosť."""
    fav_p = np.maximum(prob, 1 - prob)  # pravdepodobnosť favorita, 50–100 %
    fav_won = np.where(prob >= 0.5, home_won, ~home_won.astype(bool))
    edges = np.linspace(0.5, 1.0, bins // 2 + 1)
    band = pd.cut(fav_p, edges, include_lowest=True)
    df = pd.DataFrame({"band": band, "p": fav_p, "won": fav_won.astype(float)})
    out = df.groupby("band", observed=True).agg(
        zapasy=("p", "size"), predpoved=("p", "mean"), skutocnost=("won", "mean")
    )
    return out.reset_index()


def record_baseline(games: pd.DataFrame) -> pd.Series:
    """Naivný model: vyhrá team s lepšou bilanciou v sezóne doteraz (pri zhode domáci)."""
    wins: dict[tuple[int, str], int] = {}
    played: dict[tuple[int, str], int] = {}
    probs = []
    for r in games.itertuples(index=False):
        kh, ka = (r.season, r.home), (r.season, r.away)
        wh = wins.get(kh, 0) / max(played.get(kh, 0), 1)
        wa = wins.get(ka, 0) / max(played.get(ka, 0), 1)
        probs.append(0.6 if wh >= wa else 0.4)
        home_won = r.pts_home > r.pts_away
        wins[kh] = wins.get(kh, 0) + int(home_won)
        wins[ka] = wins.get(ka, 0) + int(not home_won)
        played[kh] = played.get(kh, 0) + 1
        played[ka] = played.get(ka, 0) + 1
    return pd.Series(probs, index=games.index)


def backtest(games: pd.DataFrame, burn_in: int = BURN_IN) -> dict[str, object]:
    games = games.sort_values(["date"], kind="stable").reset_index(drop=True)
    teams = set(games["home"]) | set(games["away"])
    first = int(games["season"].min())
    evaluated = games["season"] >= first + burn_in
    home_won = games["pts_home"] > games["pts_away"]

    variants = {
        "Elo FiveThirtyEight (HCA 100)": EloParams(hca=100),
        "Elo náš variant (HCA 70)": EloParams(hca=70),
    }
    rows, results = [], {}
    for name, p in variants.items():
        res = run(games, p, initial={t: p.mean for t in teams})
        results[name] = res
        rows.append({"model": name, **metrics(res.loc[evaluated, "prob_home"], home_won[evaluated])})

    base = record_baseline(games)
    rows.append({"model": "Baseline: lepšia bilancia", **metrics(base[evaluated], home_won[evaluated])})
    always_home = pd.Series(0.6, index=games.index)
    rows.append({"model": "Baseline: vždy domáci", **metrics(always_home[evaluated], home_won[evaluated])})

    main = results["Elo FiveThirtyEight (HCA 100)"]
    per_season = (
        main[evaluated]
        .assign(won=home_won[evaluated])
        .groupby("season")
        .apply(lambda d: pd.Series(metrics(d["prob_home"], d["won"])), include_groups=False)
    )
    return {
        "summary": pd.DataFrame(rows),
        "calibration": calibration(main.loc[evaluated, "prob_home"], home_won[evaluated]),
        "per_season": per_season,
        "seasons": (first + burn_in, int(games["season"].max())),
    }


def to_markdown(r: dict[str, object]) -> str:
    s0, s1 = r["seasons"]
    summ = r["summary"].copy()
    summ["n"] = summ["n"].astype(int)
    summ["accuracy"] = (summ["accuracy"] * 100).map("{:.1f} %".format)
    summ["log_loss"] = summ["log_loss"].map("{:.4f}".format)
    summ["brier"] = summ["brier"].map("{:.4f}".format)
    cal = r["calibration"].copy()
    cal["band"] = cal["band"].astype(str)
    cal["predpoved"] = (cal["predpoved"] * 100).map("{:.1f} %".format)
    cal["skutocnost"] = (cal["skutocnost"] * 100).map("{:.1f} %".format)
    ps = r["per_season"].copy()
    ps["n"] = ps["n"].astype(int)
    ps["accuracy"] = (ps["accuracy"] * 100).map("{:.1f} %".format)
    ps["log_loss"] = ps["log_loss"].map("{:.4f}".format)
    ps["brier"] = ps["brier"].map("{:.4f}".format)
    return (
        f"# Backtest – vrstva A (Elo)\n\n"
        f"Hodnotené sezóny: {s0 - 1}/{str(s0)[-2:]} – {s1 - 1}/{str(s1)[-2:]} "
        f"(prvé {BURN_IN} sezóny sú rozbeh modelu). Každá predpoveď používa len dáta pred zápasom.\n\n"
        f"## Porovnanie modelov\n\n{summ.to_markdown(index=False)}\n\n"
        f"Log loss a Brier: nižšie = lepšie. Trestajú aj prehnanú istotu, nielen zlý tip.\n\n"
        f"## Kalibrácia (Elo HCA 100)\n\n"
        f"Keď model dá favoritovi X %, vyhrá favorit naozaj cca X %?\n\n{cal.to_markdown(index=False)}\n\n"
        f"## Po sezónach (Elo HCA 100)\n\n{ps.to_markdown()}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> None:
    r = backtest(pd.read_parquet(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    summ = r["summary"]
    for row in summ.itertuples(index=False):
        print(
            f"{row.model:<32} presnosť {row.accuracy:6.1%}   log loss {row.log_loss:.4f}   "
            f"Brier {row.brier:.4f}"
        )
    print(f"\nReport: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
