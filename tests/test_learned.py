"""Testy naučených váh."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from team_pulse.learned import (
    BASE_COLS,
    FATIGUE_COLS,
    TEST,
    TRAIN,
    build_dataset,
    elo_equivalents,
    split,
)

TEAMS = ["BOS", "NYK", "LAL", "DEN", "MIA", "UTA"]


def random_games(n=400, seed=0):
    rng = np.random.default_rng(seed)
    home = rng.choice(TEAMS, n)
    away = [rng.choice([t for t in TEAMS if t != h]) for h in home]
    pts_home = rng.integers(85, 130, n)
    pts_away = pts_home + rng.choice([-1, 1], n) * rng.integers(1, 20, n)
    return pd.DataFrame(
        {
            "date": pd.Timestamp("2024-10-22") + pd.to_timedelta(np.sort(rng.integers(0, 170, n)), unit="D"),
            "season": 2025,
            "home": home,
            "away": away,
            "pts_home": pts_home,
            "pts_away": pts_away,
        }
    )


def test_train_and_test_seasons_do_not_overlap():
    assert TRAIN[1] < TEST[0]


def test_split_respects_seasons():
    ds = pd.DataFrame({"season": range(2001, 2027)})
    train, test = split(ds)
    assert train["season"].max() < test["season"].min()


def test_model_inputs_never_contain_results():
    for col in BASE_COLS + FATIGUE_COLS:
        assert "pts" not in col and "won" not in col and "post" not in col


def test_altitude_only_for_visitors():
    assert "away_altitude" in FATIGUE_COLS
    assert "home_altitude" not in FATIGUE_COLS


def test_dataset_has_one_row_per_game_and_all_inputs():
    g = random_games()
    ds = build_dataset(g)
    assert len(ds) == len(g)
    assert set(BASE_COLS + FATIGUE_COLS + ["home_won"]) <= set(ds.columns)
    assert ds[BASE_COLS + FATIGUE_COLS].notna().all().all()


def test_elo_equivalents_conversion():
    cols = ["elo_diff", "home", "away_b2b"]
    m = LogisticRegression()
    m.coef_ = np.array([[0.5, 0.35, 0.1]])  # 0,5 na 100 Elo → 0,005 na 1 Elo
    m.intercept_ = np.array([0.0])
    m.classes_ = np.array([0, 1])
    eq = elo_equivalents(m, cols)
    assert eq["home"] == pytest.approx(70)
    assert eq["away_b2b"] == pytest.approx(20)


def test_dataset_with_players_adds_layer_b():
    from team_pulse.learned import PLAYER_COLS

    g = random_games(n=120).reset_index(drop=True)
    g["game_id"] = [f"G{i:04d}" for i in range(len(g))]
    rows = []
    for r in g.itertuples():
        for team in (r.home, r.away):
            base = TEAMS.index(team) * 10
            for k in range(3):
                if k == 0 and r.Index % 7 == 0:
                    continue  # hviezda občas chýba
                rows.append(
                    {
                        "game_id": r.game_id,
                        "date": r.date,
                        "season": r.season,
                        "team": team,
                        "player_id": base + k,
                        "min": 30.0,
                        "pts": 20 - 5 * k,
                        "fgm": 7,
                        "fga": 14,
                        "ftm": 3,
                        "fta": 4,
                        "oreb": 1,
                        "dreb": 5,
                        "ast": 4,
                        "stl": 1,
                        "blk": 1,
                        "tov": 2,
                        "pf": 2,
                    }
                )
    ds = build_dataset(g, pd.DataFrame(rows))
    from team_pulse.learned import ROSTER_COLS

    assert set(PLAYER_COLS + ROSTER_COLS) <= set(ds.columns)
    assert ds["has_players"].all()
    assert (ds[PLAYER_COLS] >= 0).all().all()
    assert (ds[PLAYER_COLS] > 0).any().any()
