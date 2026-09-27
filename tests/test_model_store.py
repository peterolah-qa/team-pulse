"""Testy uloženia a načítania modelu."""

import numpy as np
import pandas as pd
import pytest

from team_pulse.model_store import FEATURES_V1, StoredModel, load


def fake_model():
    rng = np.random.default_rng(0)
    return StoredModel(
        version="test",
        features=FEATURES_V1,
        coef=list(rng.normal(0, 0.1, len(FEATURES_V1))),
        intercept=0.2,
        elo_params={"hca": 70},
        train_seasons=[2004, 2026],
        n_games=100,
        created="2026-09-27",
        test_metrics={"log_loss": 0.6},
        elo_weights={},
    )


def inputs(n=5):
    rng = np.random.default_rng(1)
    return pd.DataFrame(rng.normal(0, 1, (n, len(FEATURES_V1))), columns=FEATURES_V1)


def test_features_v1_contains_all_layers():
    for col in ("elo_diff", "home", "home_missing", "strength_diff", "away_b2b", "away_altitude"):
        assert col in FEATURES_V1
    assert "strength_diff_early" not in FEATURES_V1  # vyradené pri bráne G1


def test_save_and_load_roundtrip(tmp_path):
    m = fake_model()
    loaded = load(m.save(tmp_path / "m.json"))
    assert loaded == m
    np.testing.assert_allclose(loaded.predict_proba(inputs()), m.predict_proba(inputs()))


def test_predict_matches_scikit_learn():
    from sklearn.linear_model import LogisticRegression

    X = inputs(200)
    y = (X["elo_diff"] + np.random.default_rng(2).normal(0, 1, 200) > 0).astype(int)
    sk = LogisticRegression(C=1e6, max_iter=5000).fit(X, y)
    m = fake_model()
    m.coef, m.intercept = list(sk.coef_[0]), float(sk.intercept_[0])
    np.testing.assert_allclose(m.predict_proba(X), sk.predict_proba(X)[:, 1], rtol=1e-9)


def test_predict_uses_feature_names_not_column_order():
    m = fake_model()
    X = inputs()
    np.testing.assert_allclose(m.predict_proba(X), m.predict_proba(X[X.columns[::-1]]))


def test_missing_feature_fails_loudly():
    with pytest.raises(ValueError, match="chýbajú vstupy"):
        fake_model().predict_proba(inputs().drop(columns="home"))
