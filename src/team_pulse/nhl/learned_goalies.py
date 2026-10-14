"""Návrh vrstvy G pre NHL: kvalita brankára nad schváleným modelom A + C (Elo + únava).

Dva varianty, každý musí zlepšiť log loss na teste aspoň o 0,0005 oproti A + C:
  * očakávaný brankár – mix brankárov klubu podľa podielu štartov v posledných 10 zápasoch,
    dá sa spočítať vždy pred zápasom
  * skutočný brankár – ten, kto naozaj začal; naživo použiteľný len vtedy, keď štartujúceho
    brankára vieme pred zápasom (sonda scripts/probe_nhl_goalies.py)
O zaradení rozhoduje Peter.

Spustenie (po fetch_goalies):  uv run python -m team_pulse.nhl.learned_goalies
Výstup:                       reports/nhl_goalies.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from team_pulse.backtest import metrics
from team_pulse.nhl import learned
from team_pulse.nhl.backtest import TEST, THRESHOLD, TRAIN_LAST, split
from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.fetch_games import season_label
from team_pulse.nhl.fetch_goalies import OUT as GOALIES
from team_pulse.nhl.goalies import LAST, PRIOR, add_features

REPORT = Path("reports/nhl_goalies.md")
BASE = "A + C (schválené)"
EXPECTED = "A + C + G očakávaný brankár"
KNOWN = "A + C + G skutočný brankár"
VARIANTS = {
    BASE: learned.BASE_COLS + learned.FATIGUE_COLS,
    EXPECTED: learned.BASE_COLS + learned.FATIGUE_COLS + ["goalie_expected_diff"],
    KNOWN: learned.BASE_COLS + learned.FATIGUE_COLS + ["goalie_known_diff"],
}
GOALIE_COLS = ["goalie_expected_diff", "goalie_known_diff", "goalie_known_ok"]


def build_dataset(games: pd.DataFrame, goalies: pd.DataFrame) -> pd.DataFrame:
    ds = learned.build_dataset(games)
    feats = add_features(games, goalies).set_index("game_id")[GOALIE_COLS]
    return ds.join(feats, on="game_id")


def evaluate(games: pd.DataFrame, goalies: pd.DataFrame) -> dict[str, object]:
    ds = build_dataset(games, goalies)
    train_mask, test_mask = split(ds)
    train, test = ds[train_mask], ds[test_mask]
    y = test["home_won"]
    rows, weights = [], {}
    for name, cols in VARIANTS.items():
        model = learned.fit(train, cols)
        rows.append({"model": name, **metrics(learned.predict(model, test, cols), y)})
        if name != BASE:
            weights[name] = float(learned.elo_equivalents(model, cols)[cols[-1]])
    summary = pd.DataFrame(rows)
    ll = summary.set_index("model")["log_loss"]
    decisions = {
        name: {"log_loss": float(ll[name]), "gain": float(ll[BASE] - ll[name]),
               "accepted": bool(ll[name] <= ll[BASE] - THRESHOLD)}
        for name in (EXPECTED, KNOWN)
    }  # fmt: skip
    return {
        "summary": summary,
        "decisions": decisions,
        "weights": weights,
        "coverage": float(test["goalie_known_ok"].mean()),
        "spread": float(test["goalie_expected_diff"].abs().mean()),
        "n_train": len(train),
        "n_test": len(test),
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    s = r["summary"].copy()
    s["n"] = s["n"].astype(int)
    s["accuracy"] = s["accuracy"].map(_pct)
    s["log_loss"] = s["log_loss"].map(_num)
    s["brier"] = s["brier"].map(_num)
    s.columns = ["model", "zápasy", "presnosť", "log loss", "Brier"]
    lines = []
    for name, d in r["decisions"].items():
        mark = "✅ zlepšuje" if d["accepted"] else "❌ nezlepšuje dosť"
        lines.append(
            f"- **{name}:** {mark} (zlepšenie {_num(d['gain'])}, hranica {_num(THRESHOLD)}); "
            f"1 gól chytený navyše za zápas = {_num(r['weights'][name], 1)} Elo"
        )
    return (
        "# NHL – návrh vrstvy G (brankár)\n\n"
        f"Nad schváleným modelom A + C. Tréning do {season_label(TRAIN_LAST)} ({r['n_train']} zápasov), "
        f"test {season_label(TEST[0])} – {season_label(TEST[1])} ({r['n_test']} zápasov základnej časti).\n\n"
        f"Kvalita brankára = góly na zápas nad ligový priemer z jeho predchádzajúcich zápasov "
        f"(stiahnuté k priemeru o {PRIOR:g} striel). Očakávaný brankár = mix podľa štartov "
        f"v posledných {LAST} zápasoch klubu.\n\n"
        "## Rozhodnutie\n\n" + "\n".join(lines) + "\n\n"
        "Skutočný brankár je naživo použiteľný len vtedy, keď štartujúceho brankára poznáme pred zápasom.\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{s.to_markdown(index=False)}\n\n"
        f"Štartujúci brankár oboch klubov je v dátach pri {_pct(r['coverage'])} testovacích zápasov. "
        f"Priemerný rozdiel očakávaných brankárov: {_num(r['spread'], 2)} gólu na zápas.\n"
    )


def main(games_path: Path = GAMES, goalies_path: Path = GOALIES, out: Path = REPORT) -> dict[str, object]:
    r = evaluate(pd.read_parquet(games_path), pd.read_parquet(goalies_path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<30} presnosť {row.accuracy:6.1%}   log loss {row.log_loss:.4f}   "
            f"Brier {row.brier:.4f}"
        )
    for name, d in r["decisions"].items():
        print(f"{name}: {'ZLEPŠUJE' if d['accepted'] else 'NEZLEPŠUJE'} (o {d['gain']:.4f})")
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    ap.add_argument("--goalies", type=Path, default=GOALIES)
    a = ap.parse_args()
    main(a.games, a.goalies)
