"""Finálny model: natrénovanie na všetkých sezónach, uloženie do JSON a načítanie.

Uložený model je malý JSON (váhy + zoznam vstupov + parametre Ela + metriky), takže:
  * je čitateľný v pull requeste – zmena modelu je vidieť ako zmena čísel,
  * predikcia nepotrebuje scikit-learn (stačí numpy) → rýchla aj v cloude.

Spustenie (z Macu):  uv run python -m team_pulse.model_store
Výstup:              models/v1.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from team_pulse.learned import (
    BASE_COLS,
    ELO_PARAMS,
    FATIGUE_COLS,
    GAMES,
    PLAYER_COLS,
    PLAYERS,
    ROSTER_COLS,
    TRAIN,
    build_dataset,
    elo_equivalents,
    evaluate,
    fit,
)

MODELS = Path("models")
FEATURES_V1 = BASE_COLS + PLAYER_COLS + ROSTER_COLS + FATIGUE_COLS


@dataclass
class StoredModel:
    version: str
    features: list[str]
    coef: list[float]
    intercept: float
    elo_params: dict
    train_seasons: list[int]
    n_games: int
    created: str
    test_metrics: dict
    elo_weights: dict
    calibration: list = field(default_factory=list)  # kalibrácia na testovacích sezónach
    versions: list = field(default_factory=list)  # porovnanie vrstiev na testovacích sezónach

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Pravdepodobnosť výhry domácich (rovnaký výpočet ako scikit-learn)."""
        missing = set(self.features) - set(df.columns)
        if missing:
            raise ValueError(f"chýbajú vstupy modelu: {sorted(missing)}")
        z = df[self.features].to_numpy(dtype=float) @ np.array(self.coef) + self.intercept
        return 1.0 / (1.0 + np.exp(-z))

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path


def load(path: Path) -> StoredModel:
    return StoredModel(**json.loads(path.read_text(encoding="utf-8")))


def train_final(
    games: pd.DataFrame,
    players: pd.DataFrame,
    version: str = "v1",
    test_metrics: dict | None = None,
    calibration: list | None = None,
    versions: list | None = None,
) -> StoredModel:
    """Tréning na všetkých sezónach od konca rozbehu Ela po poslednú odohranú."""
    ds = build_dataset(games, players)
    seasons = [TRAIN[0], int(ds["season"].max())]
    train = ds[ds["season"].between(*seasons)]
    model = fit(train, FEATURES_V1)
    return StoredModel(
        version=version,
        features=FEATURES_V1,
        coef=[float(c) for c in model.coef_[0]],
        intercept=float(model.intercept_[0]),
        elo_params=asdict(ELO_PARAMS),
        train_seasons=seasons,
        n_games=len(train),
        created=str(date.today()),
        test_metrics=test_metrics or {},
        elo_weights={k: round(float(v), 1) for k, v in elo_equivalents(model, FEATURES_V1).items()},
        calibration=calibration or [],
        versions=versions or [],
    )


def main(version: str) -> None:
    games = pd.read_parquet(GAMES)
    players = pd.read_parquet(PLAYERS)
    # metriky z testovacích sezón (model trénovaný bez nich) – zapíšeme ich k finálnemu modelu
    r = evaluate(games, players)
    best = r["summary"].iloc[-1]
    metrics = {k: round(float(best[k]), 4) for k in ("accuracy", "log_loss", "brier")}
    metrics["test_seasons"] = "2023/24 – 2025/26"
    calibration = [
        {
            "band": str(c.band),
            "n": int(c.zapasy),
            "pred": round(float(c.predpoved), 4),
            "actual": round(float(c.skutocnost), 4),
        }
        for c in r["cal_after"].itertuples()
    ]
    versions = [
        {
            "model": row.model,
            "accuracy": round(float(row.accuracy), 4),
            "log_loss": round(float(row.log_loss), 4),
            "brier": round(float(row.brier), 4),
        }
        for row in r["summary"].itertuples()
    ]
    m = train_final(games, players, version, metrics, calibration, versions)
    path = m.save(MODELS / f"{version}.json")
    print(f"Model {version}: {m.n_games} zápasov, sezóny {m.train_seasons[0]}–{m.train_seasons[1]}")
    print(f"Testovacie metriky: {metrics}")
    print("Váhy v Elo:", m.elo_weights)
    print(f"Uložené: {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    main(ap.parse_args().version)
