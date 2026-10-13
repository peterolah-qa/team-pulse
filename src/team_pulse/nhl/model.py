"""Finálny NHL model (Elo + únava): tréning na všetkých sezónach a uloženie do JSON.

Rovnaký formát ako NBA (team_pulse.model_store.StoredModel), predikcia nepotrebuje scikit-learn.
Metriky v súbore sú z testu 2023/24 – 2025/26 (reports/nhl_learned.md), model sa potom
natrénuje na všetkých sezónach od konca rozbehu Ela po poslednú odohranú.

Spustenie (z Macu):  uv run python -m team_pulse.nhl.model
Výstup:              models/nhl_v1.json
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd

from team_pulse.model_store import StoredModel, load
from team_pulse.nhl import learned
from team_pulse.nhl.backtest import BURN_IN
from team_pulse.nhl.fetch_games import OUT as GAMES

MODEL = Path("models/nhl_v1.json")
FEATURES = learned.BASE_COLS + learned.FATIGUE_COLS


def train_final(games: pd.DataFrame, test: dict[str, object] | None = None) -> StoredModel:
    """Váhy z celej histórie (len základná časť), metriky z testovacích sezón."""
    ds = learned.build_dataset(games)
    first, last = int(ds["season"].min()) + BURN_IN, int(ds["season"].max())
    train = ds[ds["season"].between(first, last) & (ds["game_type"] == "R")]
    model = learned.fit(train, FEATURES)
    test = test or learned.evaluate(games)
    summary = test["summary"].set_index("model")
    row = summary.loc["A + C (+ únava)"]
    return StoredModel(
        version="nhl-v1",
        features=FEATURES,
        coef=[float(c) for c in model.coef_[0]],
        intercept=float(model.intercept_[0]),
        elo_params=asdict(learned.ELO),
        train_seasons=[first, last],
        n_games=len(train),
        created=date.today().isoformat(),
        test_metrics={k: float(row[k]) for k in ("accuracy", "log_loss", "brier")} | {"n": int(row["n"])},
        elo_weights={k: round(float(v), 1) for k, v in learned.elo_equivalents(model, FEATURES).items()},
        versions=[
            {"model": m, "accuracy": float(r["accuracy"]), "log_loss": float(r["log_loss"])}
            for m, r in summary.iterrows()
        ],
    )


def main(path: Path = GAMES, out: Path = MODEL) -> StoredModel:
    m = train_final(pd.read_parquet(path))
    m.save(out)
    t = m.test_metrics
    print(f"NHL model {m.version}: sezóny {m.train_seasons[0]}–{m.train_seasons[1]}, {m.n_games} zápasov")
    print(f"Test: presnosť {t['accuracy']:.1%}, log loss {t['log_loss']:.4f}")
    print(f"Váhy (Elo): {m.elo_weights}")
    print(f"Uložené: {out}")
    return m


__all__ = ["MODEL", "FEATURES", "load", "main", "train_final"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
