"""Test úniku dát z budúcnosti.

Predpoveď zápasu smie vychádzať len z toho, čo bolo známe PRED zápasom.
Ak zmeníme výsledok zápasu k (a všetkých neskorších), predpovede zápasov 0..k
sa nesmú zmeniť ani o chlp.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.elo import run

TEAMS = ["AAA", "BBB", "CCC", "DDD"]


def make_games(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    home = rng.choice(TEAMS, n)
    away = [rng.choice([t for t in TEAMS if t != h]) for h in home]
    pts_home = rng.integers(85, 130, n)
    pts_away = pts_home + rng.choice([-1, 1], n) * rng.integers(1, 25, n)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-10-22", periods=n, freq="D"),
            "season": 2025,
            "home": home,
            "away": away,
            "pts_home": pts_home,
            "pts_away": pts_away,
        }
    )


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=0, max_value=39), st.integers(min_value=0, max_value=10_000))
def test_changing_result_does_not_change_earlier_predictions(k, seed):
    games = make_games(40, seed)
    base = run(games)

    changed = games.copy()
    # otočíme výsledok zápasu k a všetkých neskorších
    ph = changed["pts_home"].to_numpy().copy()
    pa = changed["pts_away"].to_numpy().copy()
    ph[k:], pa[k:] = pa[k:].copy(), ph[k:].copy()
    changed["pts_home"], changed["pts_away"] = ph, pa
    alt = run(changed)

    cols = ["elo_home_pre", "elo_away_pre", "prob_home"]
    pd.testing.assert_frame_equal(base.loc[:k, cols], alt.loc[:k, cols])


def test_unsorted_input_is_processed_chronologically():
    games = make_games(10, seed=1)
    shuffled = games.sample(frac=1, random_state=7)
    pd.testing.assert_series_equal(run(games)["prob_home"], run(shuffled)["prob_home"])


def test_first_game_prediction_ignores_its_own_result():
    games = make_games(1, seed=2)
    flipped = games.assign(pts_home=games["pts_away"], pts_away=games["pts_home"])
    assert run(games)["prob_home"].iat[0] == pytest.approx(run(flipped)["prob_home"].iat[0])
