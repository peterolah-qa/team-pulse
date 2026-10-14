"""Backtest NHL a brána G0-NHL (kritérium v docs/sporty.md, stanovené pred meraním).

Postup:
  1. Elo beží cez všetky zápasy (základná časť aj playoff), každá predpoveď len z minulosti.
  2. Parametre Ela (K, domáca výhoda, prenos do sezóny) sa ladia LEN na tréningových sezónach.
  3. Baseline sa tiež naučia len z tréningu (podiel výhier domácich, výhry teamu s lepšou bilanciou).
  4. Hodnotí sa základná časť testovacích sezón 2023/24 – 2025/26.

Spustenie:  uv run python -m team_pulse.nhl.backtest
Výstup:     reports/nhl_backtest.md
"""

from __future__ import annotations

import argparse
import itertools
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from team_pulse.backtest import calibration, metrics
from team_pulse.nhl.elo import START, HockeyEloParams, run
from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.fetch_games import season_label

REPORT = Path("reports/nhl_backtest.md")
BURN_IN = 3  # prvé sezóny sa nehodnotia, Elo sa rozbieha zo štartu 1505
TRAIN_LAST = 2023  # tréning do 2022/23
TEST = (2024, 2026)  # test 2023/24 – 2025/26
THRESHOLD = 0.0005  # o koľko musí byť log loss Ela nižší než lepšia z baseline

GRID = {
    "k": [4.0, 5.0, 6.0, 7.0, 8.0, 10.0],
    "hca": [20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
    "carryover": [0.5, 0.6, 0.7, 0.8, 0.9],
}


def split(games: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Masky: tréningové a testovacie zápasy základnej časti (bez rozbehu)."""
    first = int(games["season"].min())
    regular = games["game_type"] == "R"
    train = regular & games["season"].between(first + BURN_IN, TRAIN_LAST)
    test = regular & games["season"].between(*TEST)
    return train, test


def home_won(games: pd.DataFrame) -> pd.Series:
    return games["goals_home"] > games["goals_away"]


def record_category(games: pd.DataFrame) -> pd.Series:
    """Pred zápasom: má domáci lepšiu (1), rovnakú (0) alebo horšiu (−1) bilanciu v sezóne?

    Počíta sa len z už odohratých zápasov sezóny."""
    wins: dict[tuple[int, str], int] = {}
    played: dict[tuple[int, str], int] = {}
    cat = []
    for r in games.itertuples(index=False):
        kh, ka = (r.season, r.home), (r.season, r.away)
        wh = wins.get(kh, 0) / played[kh] if played.get(kh) else 0.5
        wa = wins.get(ka, 0) / played[ka] if played.get(ka) else 0.5
        cat.append(int(np.sign(wh - wa)))
        won = r.goals_home > r.goals_away
        wins[kh] = wins.get(kh, 0) + int(won)
        wins[ka] = wins.get(ka, 0) + int(not won)
        played[kh] = played.get(kh, 0) + 1
        played[ka] = played.get(ka, 0) + 1
    return pd.Series(cat, index=games.index)


def fit_baselines(games: pd.DataFrame, train: pd.Series) -> dict[str, object]:
    """Pravdepodobnosti baseline z tréningových sezón (najsilnejšia verzia, nie odhad od oka)."""
    won = home_won(games)
    cat = record_category(games)
    by_cat = won[train].groupby(cat[train]).mean()
    return {"home_rate": float(won[train].mean()), "record": {int(k): float(v) for k, v in by_cat.items()}}


def baseline_probs(games: pd.DataFrame, fit: dict[str, object]) -> dict[str, pd.Series]:
    cat = record_category(games)
    record = fit["record"]
    return {
        "Baseline: vždy domáci": pd.Series(fit["home_rate"], index=games.index),
        "Baseline: lepšia bilancia": cat.map(lambda c: record.get(c, fit["home_rate"])),
    }


def tune(games: pd.DataFrame, train: pd.Series, grid: dict[str, list[float]] = GRID) -> pd.DataFrame:
    """Log loss Ela na tréningových sezónach pre každú kombináciu parametrov (od najlepšej)."""
    won = home_won(games)
    rows = []
    for k, hca, carry in itertools.product(grid["k"], grid["hca"], grid["carryover"]):
        p = replace(START, k=k, hca=hca, carryover=carry)
        res = run(games, p)
        m = metrics(res.loc[train, "prob_home"], won[train])
        rows.append({"k": k, "hca": hca, "carryover": carry, **m})
    return pd.DataFrame(rows).sort_values("log_loss", kind="stable").reset_index(drop=True)


def backtest(games: pd.DataFrame, grid: dict[str, list[float]] = GRID) -> dict[str, object]:
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    games = games.sort_values(order, kind="stable").reset_index(drop=True)
    train, test = split(games)
    if not train.any() or not test.any():
        raise ValueError("chýbajú tréningové alebo testovacie sezóny")
    won = home_won(games)

    tuning = tune(games, train, grid)
    best = tuning.iloc[0]
    tuned = replace(START, k=float(best["k"]), hca=float(best["hca"]), carryover=float(best["carryover"]))
    elo = {"Elo ladené na tréningu": run(games, tuned), "Elo štart (FiveThirtyEight)": run(games, START)}

    fit = fit_baselines(games, train)
    probs = {name: res["prob_home"] for name, res in elo.items()} | baseline_probs(games, fit)
    summary = pd.DataFrame([{"model": name, **metrics(p[test], won[test])} for name, p in probs.items()])

    main = elo["Elo ladené na tréningu"]
    best_base = summary.loc[summary["model"].str.startswith("Baseline"), "log_loss"].min()
    elo_ll = float(summary.loc[summary["model"] == "Elo ladené na tréningu", "log_loss"].iloc[0])
    per_season = (
        main[test]
        .assign(won=won[test])
        .groupby("season")
        .apply(lambda d: pd.Series(metrics(d["prob_home"], d["won"])), include_groups=False)
    )
    lp = games.loc[test, "last_period"] if "last_period" in games else pd.Series(dtype=object)
    return {
        "summary": summary,
        "tuned": tuned,
        "tuning": tuning,
        "baselines": fit,
        "calibration": calibration(main.loc[test, "prob_home"], won[test]),
        "per_season": per_season,
        "gate": {"elo": elo_ll, "baseline": float(best_base), "passed": elo_ll <= best_base - THRESHOLD},
        "seasons": (int(games["season"].min()), int(games["season"].max())),
        "counts": {"train": int(train.sum()), "test": int(test.sum())},
        "home_rate_test": float(won[test].mean()),
        "extra_time_test": float(lp.isin(["OT", "SO"]).mean()) if lp.notna().any() else None,
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _dec(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    s0, s1 = r["seasons"]
    t: HockeyEloParams = r["tuned"]
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
    ps.index = [season_label(int(s)) for s in ps.index]
    ps["n"] = ps["n"].astype(int)
    ps["accuracy"] = ps["accuracy"].map(_pct)
    ps["log_loss"] = ps["log_loss"].map(_num)
    ps["brier"] = ps["brier"].map(_num)
    ps.columns = ["zápasy", "presnosť", "log loss", "Brier"]
    top = r["tuning"].head(5).copy()
    top["log_loss"] = top["log_loss"].map(_num)
    top["carryover"] = top["carryover"].map(_dec)
    top = top[["k", "hca", "carryover", "log_loss"]]
    top.columns = ["K", "domáca výhoda", "prenos do sezóny", "log loss (tréning)"]
    g = r["gate"]
    b = r["baselines"]

    def rec(c: int) -> str:
        return _pct(b["record"][c]) if c in b["record"] else "–"

    verdict = "✅ splnené" if g["passed"] else "❌ nesplnené"
    extra = r["extra_time_test"]
    return (
        "# Backtest NHL – vrstva A (hokejové Elo)\n\n"
        f"Dáta: {season_label(s0)} – {season_label(s1)}. Prvé {BURN_IN} sezóny sú rozbeh Ela. "
        f"Tréning do {season_label(TRAIN_LAST)} ({r['counts']['train']} zápasov), "
        f"test {season_label(TEST[0])} – {season_label(TEST[1])} ({r['counts']['test']} zápasov "
        "základnej časti, model ich pri ladení nevidel). Každá predpoveď používa len dáta pred zápasom.\n\n"
        f"## Brána G0-NHL: {verdict}\n\n"
        f"Kritérium (docs/sporty.md): log loss Ela na teste o ≥ {_num(THRESHOLD)} nižší "
        "než lepšia z baseline.\n\n"
        f"Elo {_num(g['elo'])} · lepšia baseline {_num(g['baseline'])} · "
        f"rozdiel {_num(g['baseline'] - g['elo'])}\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{summ.to_markdown(index=False)}\n\n"
        "Log loss a Brier: nižšie = lepšie. Trestajú aj prehnanú istotu, nielen zlý tip.\n\n"
        f"Domáci vyhrali {_pct(r['home_rate_test'])} testovacích zápasov"
        + (f", {_pct(extra)} zápasov rozhodlo predĺženie alebo nájazdy" if extra is not None else "")
        + ".\n\n"
        "## Parametre Ela (ladené len na tréningu)\n\n"
        f"Zvolené: K {t.k:g}, domáca výhoda {t.hca:g} Elo, prenos do sezóny {_dec(t.carryover)}. "
        f"Štart FiveThirtyEight: K {START.k:g}, domáca výhoda {START.hca:g}, "
        f"prenos {_dec(START.carryover)}.\n\n"
        f"{top.to_markdown(index=False)}\n\n"
        "## Baseline (naučené na tréningu)\n\n"
        f"- Vždy domáci: {_pct(b['home_rate'])}\n"
        f"- Lepšia bilancia: domáci s lepšou bilanciou {rec(1)}, s rovnakou {rec(0)}, s horšou {rec(-1)}\n\n"
        "## Kalibrácia (test)\n\n"
        f"Keď model dá favoritovi X %, vyhrá favorit naozaj cca X %?\n\n{cal.to_markdown(index=False)}\n\n"
        f"## Po sezónach (test)\n\n{ps.to_markdown()}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> dict[str, object]:
    r = backtest(pd.read_parquet(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<30} presnosť {row.accuracy:6.1%}   log loss {row.log_loss:.4f}   "
            f"Brier {row.brier:.4f}"
        )
    g = r["gate"]
    print(f"\nParametre: {asdict(r['tuned'])}")
    verdict = "SPLNENÁ" if g["passed"] else "NESPLNENÁ"
    print(f"Brána G0-NHL: {verdict} (Elo {g['elo']:.4f}, baseline {g['baseline']:.4f})")
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
