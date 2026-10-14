"""Test Glicko-2 pre NHL: pomôže namiesto Ela alebo vedľa neho?

Postup ako pri ostatných vrstvách:
  1. parametre Glicko-2 sa ladia LEN na tréningových sezónach (log loss samotného ratingu),
  2. na teste 2023/24 – 2025/26 sa porovná so schváleným modelom A + C (Elo + únava):
       * Glicko-2 namiesto Ela (+ únava),
       * Glicko-2 navyše k Elu (+ únava).
Prijme sa len variant, ktorý zlepší log loss aspoň o 0,0005. O zmene modelu rozhoduje Peter.

Spustenie:  uv run python -m team_pulse.nhl.learned_glicko
Výstup:     reports/nhl_glicko.md
"""

from __future__ import annotations

import argparse
import itertools
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd

from team_pulse.backtest import metrics
from team_pulse.nhl import learned
from team_pulse.nhl.backtest import TEST, THRESHOLD, TRAIN_LAST, split
from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.fetch_games import season_label
from team_pulse.nhl.glicko import START, GlickoParams, run

REPORT = Path("reports/nhl_glicko.md")
GRID = {
    "tau": [0.2, 0.5],
    "hca": [20.0, 30.0, 40.0],
    "rd_season": [25.0, 50.0, 100.0],
    "carryover": [0.8, 0.9],
    "sigma": [0.06, 0.1, 0.15],  # vyššia volatilita = rating reaguje rýchlejšie aj po rokoch dát
}
APPROVED = "A + C (schválené: Elo + únava)"
REPLACE = "Glicko-2 namiesto Ela + únava"
ADD = "Elo + Glicko-2 + únava"
FATIGUE = learned.FATIGUE_COLS
VARIANTS = {
    APPROVED: ["elo_diff", "home", *FATIGUE],
    REPLACE: ["glicko_logit", "home", *FATIGUE],
    ADD: ["elo_diff", "glicko_logit", "home", *FATIGUE],
}


def tune(games: pd.DataFrame, grid: dict[str, list[float]] = GRID) -> pd.DataFrame:
    """Log loss samotného Glicko-2 na tréningových sezónach pre každú kombináciu (od najlepšej)."""
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    g = games.sort_values(order, kind="stable").reset_index(drop=True)
    train, _ = split(g)
    won = g["goals_home"] > g["goals_away"]
    rows = []
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values, strict=True))
        res = run(g, replace(START, **params))
        rows.append({**params, **metrics(res.loc[train, "glicko_prob"], won[train])})
    return pd.DataFrame(rows).sort_values("log_loss", kind="stable").reset_index(drop=True)


def evaluate(games: pd.DataFrame, grid: dict[str, list[float]] = GRID) -> dict[str, object]:
    tuning = tune(games, grid)
    best = tuning.iloc[0]
    params = replace(START, **{k: float(best[k]) for k in grid})
    gl = run(games, params).set_index("game_id")[
        ["glicko_prob", "glicko_logit", "rd_home_pre", "rd_away_pre"]
    ]
    ds = learned.build_dataset(games).join(gl, on="game_id")
    train_mask, test_mask = split(ds)
    train, test = ds[train_mask], ds[test_mask]
    y = test["home_won"]
    rows = [
        {"model": "A: Elo (samotné)", **metrics(test["elo_prob"], y)},
        {"model": "A: Glicko-2 (samotné)", **metrics(test["glicko_prob"], y)},
    ]
    for name, cols in VARIANTS.items():
        rows.append({"model": name, **metrics(learned.predict(learned.fit(train, cols), test, cols), y)})
    summary = pd.DataFrame(rows)
    ll = summary.set_index("model")["log_loss"]
    decisions = {
        name: {"log_loss": float(ll[name]), "gain": float(ll[APPROVED] - ll[name]),
               "accepted": bool(ll[name] <= ll[APPROVED] - THRESHOLD)}
        for name in (REPLACE, ADD)
    }  # fmt: skip
    return {
        "summary": summary,
        "decisions": decisions,
        "params": params,
        "tuning": tuning,
        "rd_test": float(test[["rd_home_pre", "rd_away_pre"]].to_numpy().mean()),
        "n_train": len(train),
        "n_test": len(test),
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def _dec(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    s = r["summary"].copy()
    s["n"] = s["n"].astype(int)
    s["accuracy"] = s["accuracy"].map(_pct)
    s["log_loss"] = s["log_loss"].map(_num)
    s["brier"] = s["brier"].map(_num)
    s.columns = ["model", "zápasy", "presnosť", "log loss", "Brier"]
    top = r["tuning"].head(5).copy()
    top["log_loss"] = top["log_loss"].map(_num)
    for c in ("tau", "carryover", "sigma"):
        top[c] = top[c].map(_dec)
    top = top[["tau", "sigma", "hca", "rd_season", "carryover", "log_loss"]]
    top.columns = ["tau", "volatilita", "domáca výhoda", "neistota po lete", "prenos", "log loss (tréning)"]
    p: GlickoParams = r["params"]
    lines = [
        f"- **{name}:** {'✅ zlepšuje' if d['accepted'] else '❌ nezlepšuje dosť'} "
        f"(zlepšenie {_num(d['gain'])}, hranica {_num(THRESHOLD)})"
        for name, d in r["decisions"].items()
    ]
    return (
        "# NHL – test Glicko-2\n\n"
        f"Tréning do {season_label(TRAIN_LAST)} ({r['n_train']} zápasov), test {season_label(TEST[0])} – "
        f"{season_label(TEST[1])} ({r['n_test']} zápasov základnej časti). Parametre Glicko-2 ladené len "
        "na tréningu. Glicko-2 berie len výhru/prehru, Elo aj rozdiel gólov.\n\n"
        "## Rozhodnutie\n\n" + "\n".join(lines) + "\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{s.to_markdown(index=False)}\n\n"
        "## Parametre Glicko-2 (ladené na tréningu)\n\n"
        f"Zvolené: tau {_dec(p.tau)}, volatilita {_dec(p.sigma)}, domáca výhoda {p.hca:g}, "
        f"neistota po lete +{p.rd_season:g}, "
        f"prenos do sezóny {_dec(p.carryover)}. "
        f"Priemerná neistota klubu v teste {r['rd_test']:.0f} bodov.\n\n"
        f"{top.to_markdown(index=False)}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> dict[str, object]:
    r = evaluate(pd.read_parquet(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<32} presnosť {row.accuracy:6.1%}   log loss {row.log_loss:.4f}   "
            f"Brier {row.brier:.4f}"
        )
    print(f"\nParametre: {asdict(r['params'])}")
    for name, d in r["decisions"].items():
        print(f"{name}: {'ZLEPŠUJE' if d['accepted'] else 'NEZLEPŠUJE'} (o {d['gain']:.4f})")
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
