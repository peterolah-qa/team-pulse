"""Backtest NFL a brána G0-NFL (kritériá v docs/gate-nfl-G0.md, stanovené 28. 10. 2026 pred meraním).

Postup:
  1. Elo beží cez všetky zápasy 1999 – 2025 (základná časť aj play-off), každá predpoveď len z minulosti.
  2. Zahrievanie 1999 – 2009 sa nemeria. Parametre Ela (K, výhoda domáceho, prenos) a baseline sa ladia
     LEN na tréningu 2010 – 2022.
  3. Test 2023 – 2025: základná časť aj play-off, remízy sa nevyhodnocujú.

Spustenie:  uv run python -m team_pulse.nfl.backtest
Výstup:     reports/nfl_backtest.md
"""

from __future__ import annotations

import argparse
import itertools
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from team_pulse.backtest import calibration, metrics
from team_pulse.nfl import games as G
from team_pulse.nfl.elo import START, NflEloParams, run

REPORT = Path("reports/nfl_backtest.md")
WARMUP = (1999, 2009)
TRAIN = (2010, 2022)
TEST = (2023, 2025)
THRESHOLD = 0.0005
GRID = {
    "k": [15.0, 20.0, 25.0, 30.0],
    "hfa": [30.0, 40.0, 48.0, 55.0, 65.0],
    "carryover": [0.6, 2.0 / 3.0, 0.75, 0.8],
}


def masks(g: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Tréning a test: odohrané zápasy bez remíz v daných sezónach."""
    ok = g["played"] & ~g["tie"]
    return ok & g["season"].between(*TRAIN), ok & g["season"].between(*TEST)


def home_won(g: pd.DataFrame) -> pd.Series:
    return g["score_home"] > g["score_away"]


def record_diff(g: pd.DataFrame) -> pd.Series:
    """Bilancia domácich − bilancia hostí z doterajších zápasov sezóny (remíza 0,5; bez zápasu 0,5)."""
    pts: dict[tuple[int, str], float] = {}
    n: dict[tuple[int, str], int] = {}
    out = []
    for r in g.itertuples(index=False):
        kh, ka = (r.season, r.home), (r.season, r.away)
        wh = pts[kh] / n[kh] if n.get(kh) else 0.5
        wa = pts[ka] / n[ka] if n.get(ka) else 0.5
        out.append(wh - wa)
        if r.played:
            s = 0.5 if r.score_home == r.score_away else float(r.score_home > r.score_away)
            pts[kh] = pts.get(kh, 0.0) + s
            pts[ka] = pts.get(ka, 0.0) + 1.0 - s
            n[kh] = n.get(kh, 0) + 1
            n[ka] = n.get(ka, 0) + 1
    return pd.Series(out, index=g.index)


def fit_baselines(g: pd.DataFrame, train: pd.Series) -> dict[str, float]:
    """Vždy domáci (podiel výhier domácich mimo neutrálnych ihrísk) a lepšia bilancia σ(a·dom + b·rozdiel)."""
    won = home_won(g)
    home = ~g["neutral"]
    rate = float(won[train & home].mean())
    x = np.column_stack([home[train].astype(float), record_diff(g)[train]])
    lr = LogisticRegression(fit_intercept=False, C=1e6, max_iter=1000).fit(x, won[train].astype(int))
    a, b = (float(v) for v in lr.coef_[0])
    return {"home_rate": rate, "a": a, "b": b}


def baseline_probs(g: pd.DataFrame, fit: dict[str, float]) -> dict[str, pd.Series]:
    home = (~g["neutral"]).astype(float)
    z = fit["a"] * home + fit["b"] * record_diff(g)
    return {
        "Baseline: vždy domáci": pd.Series(np.where(g["neutral"], 0.5, fit["home_rate"]), index=g.index),
        "Baseline: lepšia bilancia": 1.0 / (1.0 + np.exp(-z)),
    }


def tune(g: pd.DataFrame, train: pd.Series, grid: dict[str, list[float]] = GRID) -> pd.DataFrame:
    won = home_won(g)
    rows = []
    for k, hfa, carry in itertools.product(grid["k"], grid["hfa"], grid["carryover"]):
        p = replace(START, k=k, hfa=hfa, carryover=carry)
        res = run(g, p)
        rows.append(
            {"k": k, "hfa": hfa, "carryover": carry, **metrics(res.loc[train, "prob_home"], won[train])}
        )
    return pd.DataFrame(rows).sort_values("log_loss", kind="stable").reset_index(drop=True)


def backtest(games: pd.DataFrame, grid: dict[str, list[float]] = GRID) -> dict[str, object]:
    g = (
        games[games["season"] <= TEST[1]]
        .sort_values(["date", "game_id"], kind="stable")
        .reset_index(drop=True)
    )
    train, test = masks(g)
    if not train.any() or not test.any():
        raise ValueError("chýbajú tréningové alebo testovacie sezóny")
    won = home_won(g)
    tuning = tune(g, train, grid)
    best = tuning.iloc[0]
    tuned = replace(START, k=float(best["k"]), hfa=float(best["hfa"]), carryover=float(best["carryover"]))
    elo = {"Elo ladené na tréningu": run(g, tuned), "Elo štart (FiveThirtyEight)": run(g, START)}
    fit = fit_baselines(g, train)
    probs = {name: res["prob_home"] for name, res in elo.items()} | baseline_probs(g, fit)
    summary = pd.DataFrame([{"model": n, **metrics(p[test], won[test])} for n, p in probs.items()])
    main = elo["Elo ladené na tréningu"]
    elo_ll = float(summary.loc[summary["model"] == "Elo ladené na tréningu", "log_loss"].iloc[0])
    best_base = float(summary.loc[summary["model"].str.startswith("Baseline"), "log_loss"].min())
    per_season = (
        main[test]
        .assign(won=won[test])
        .groupby("season")
        .apply(lambda d: pd.Series(metrics(d["prob_home"], d["won"])), include_groups=False)
    )
    counts = G.check_counts(g, range(TRAIN[0], TEST[1] + 1))
    return {
        "summary": summary,
        "tuned": tuned,
        "tuning": tuning,
        "baselines": fit,
        "calibration": calibration(main.loc[test, "prob_home"], won[test]),
        "per_season": per_season,
        "gate": {"elo": elo_ll, "baseline": best_base, "passed": elo_ll <= best_base - THRESHOLD},
        "counts": {"train": int(train.sum()), "test": int(test.sum()), "problems": counts},
        "ties_test": int((g["tie"] & g["season"].between(*TEST)).sum()),
        "home_rate_test": float(won[test & ~g["neutral"]].mean()),
        "playoff_test": int((test & g["playoff"]).sum()),
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def _dec(x: float) -> str:
    return f"{x:.3g}".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    t: NflEloParams = r["tuned"]
    summ = r["summary"].copy()
    summ["n"] = summ["n"].astype(int)
    summ["accuracy"] = summ["accuracy"].map(_pct)
    summ["log_loss"] = summ["log_loss"].map(_num)
    summ["brier"] = summ["brier"].map(_num)
    summ.columns = ["model", "zápasy", "presnosť", "log loss", "Brier"]
    cal = r["calibration"].copy()
    cal["band"] = cal["band"].astype(str)
    cal["predpoved"] = cal["predpoved"].map(_pct)
    cal["skutocnost"] = cal["skutocnost"].map(_pct)
    cal.columns = ["pásmo", "zápasy", "predpoveď", "skutočnosť"]
    ps = r["per_season"].copy()
    ps["n"] = ps["n"].astype(int)
    for c, f in (("accuracy", _pct), ("log_loss", _num), ("brier", _num)):
        ps[c] = ps[c].map(f)
    ps.columns = ["zápasy", "presnosť", "log loss", "Brier"]
    top = r["tuning"].head(5).copy()
    top["log_loss"] = top["log_loss"].map(_num)
    top["carryover"] = top["carryover"].map(_dec)
    top = top[["k", "hfa", "carryover", "log_loss"]]
    top.columns = ["K", "výhoda domáceho", "prenos do sezóny", "log loss (tréning)"]
    g, b, c = r["gate"], r["baselines"], r["counts"]
    verdict = "✅ splnené" if g["passed"] else "❌ nesplnené"
    complete = "všetky počty sedia" if not c["problems"] else "; ".join(c["problems"])
    return (
        "# Backtest NFL – vrstva A (Elo tímov)\n\n"
        f"Dáta: nflverse games.csv (commit `{G.G0_COMMIT[:7]}`), zdroj {G.SOURCE}. Stávkové stĺpce sa "
        "nenačítali. Zahrievanie 1999 – 2009 (nemeria sa), "
        f"tréning {TRAIN[0]} – {TRAIN[1]} ({c['train']} zápasov), test {TEST[0]} – {TEST[1]} "
        f"({c['test']} zápasov, z toho {r['playoff_test']} play-off; "
        f"{r['ties_test']} remíza sa nevyhodnocuje). "
        "Každá predpoveď používa len zápasy pred ňou.\n\n"
        f"## Brána G0-NFL: {verdict}\n\n"
        "Kritériá: docs/gate-nfl-G0.md (stanovené 28. 10. 2026 pred meraním).\n\n"
        f"| # | Kritérium | Výsledok |\n|---|---|---|\n"
        f"| 1 | Úplnosť dát {TRAIN[0]} – {TEST[1]} | {complete} |\n"
        f"| 2 | Log loss Ela vs. lepšia baseline (≥ {_num(THRESHOLD)}) | Elo {_num(g['elo'])}, "
        f"baseline {_num(g['baseline'])}, rozdiel {_num(g['baseline'] - g['elo'])} |\n"
        "| 3 | Test úniku dát | tests/test_nfl.py |\n"
        "| 4 | Stávkové stĺpce sa nenačítajú | tests/test_nfl.py |\n"
        "| 5 | Contract test ESPN NFL | tests/test_nfl.py |\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{summ.to_markdown(index=False)}\n\n"
        "Log loss a Brier: nižšie = lepšie.\n\n"
        f"Domáci (mimo neutrálnych ihrísk) vyhrali {_pct(r['home_rate_test'])} testovacích zápasov.\n\n"
        "## Parametre Ela (ladené len na tréningu)\n\n"
        f"Zvolené: K {t.k:g}, výhoda domáceho {t.hfa:g} Elo, prenos do sezóny {_dec(t.carryover)}; "
        f"play-off × {_dec(t.playoff_mult)} a nový klub {t.new_team:g} pevne podľa FiveThirtyEight. "
        f"Štart FiveThirtyEight: K {START.k:g}, výhoda domáceho {START.hfa:g}, "
        f"prenos {_dec(START.carryover)}.\n\n"
        f"{top.to_markdown(index=False)}\n\n"
        "## Baseline (naučené na tréningu)\n\n"
        f"- Vždy domáci: {_pct(b['home_rate'])} (na neutrálnom ihrisku 50 %)\n"
        f"- Lepšia bilancia: σ({_dec(b['a'])} · domáci + {_dec(b['b'])} · rozdiel bilancií)\n\n"
        "## Kalibrácia (test)\n\n"
        f"Keď model dá favoritovi X %, vyhrá favorit naozaj cca X %?\n\n{cal.to_markdown(index=False)}\n\n"
        f"## Po sezónach (test)\n\n{ps.to_markdown()}\n"
    )


def main(commit: str = G.G0_COMMIT, out: Path = REPORT) -> dict[str, object]:
    r = backtest(G.load(G.download(commit)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<30} presnosť {row.accuracy:6.1%}   "
            f"log loss {row.log_loss:.4f}   Brier {row.brier:.4f}"
        )
    g = r["gate"]
    print(f"\nParametre: {r['tuned']}")
    print(f"Úplnosť: {r['counts']['problems'] or 'sedí'}")
    print(
        f"Brána G0-NFL (kritérium 2): {'SPLNENÉ' if g['passed'] else 'NESPLNENÉ'} "
        f"(Elo {g['elo']:.4f}, baseline {g['baseline']:.4f})"
    )
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default=G.G0_COMMIT)
    main(ap.parse_args().commit)
