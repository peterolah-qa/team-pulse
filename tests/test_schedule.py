"""Testy vrstvy C – príznaky únavy."""

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.schedule import FEATURES, add_features


def games(rows, season=2025):
    """rows: (dátum, domáci, hostia[, neutral])"""
    data = [(pd.Timestamp(r[0]), season, r[1], r[2], 100, 90, len(r) > 3 and r[3]) for r in rows]
    df = pd.DataFrame(data, columns=["date", "season", "home", "away", "pts_home", "pts_away", "neutral"])
    return add_features(df)


def test_first_game_of_season_is_fully_rested():
    g = games([("2024-10-22", "BOS", "NYK")])
    assert g.loc[0, "home_rest"] == 7 and g.loc[0, "away_rest"] == 7
    assert g.loc[0, "away_km"] == 0


def test_back_to_back():
    g = games([("2024-11-01", "BOS", "NYK"), ("2024-11-02", "PHI", "NYK")])
    assert g.loc[1, "away_rest"] == 1
    assert g.loc[1, "away_b2b"] == 1
    assert g.loc[1, "home_b2b"] == 0


def test_three_games_in_four_days():
    g = games(
        [
            ("2024-11-01", "BOS", "NYK"),
            ("2024-11-03", "NYK", "MIA"),
            ("2024-11-04", "NYK", "CHI"),
        ]
    )
    assert g.loc[2, "home_three_in4"] == 1
    assert g.loc[1, "home_three_in4"] == 0


def test_travel_and_time_zone_west_to_east():
    # NYK hrá v LA, potom v New Yorku → cca 3 940 km, 3 hodiny na východ
    g = games([("2024-11-01", "LAL", "NYK"), ("2024-11-03", "NYK", "BOS")])
    assert g.loc[1, "home_km"] == pytest.approx(3940, abs=40)
    assert g.loc[1, "home_tz_east"] == 3


def test_travel_east_to_west_is_not_counted_as_tz_east():
    g = games([("2024-11-01", "NYK", "LAL"), ("2024-11-03", "LAL", "BOS")])
    assert g.loc[1, "home_tz_east"] == 0


def test_road_trip_counter_and_reset_at_home():
    g = games(
        [
            ("2024-11-01", "BOS", "LAL"),
            ("2024-11-03", "NYK", "LAL"),
            ("2024-11-05", "PHI", "LAL"),
            ("2024-11-08", "LAL", "MIA"),
            ("2024-11-10", "DEN", "LAL"),
        ]
    )
    assert g["away_road"].tolist()[:3] == [1, 2, 3]
    assert g.loc[3, "home_road"] == 0
    assert g.loc[4, "away_road"] == 1


def test_altitude_only_for_lowland_visitors():
    g = games([("2024-11-01", "DEN", "MIA"), ("2024-11-03", "DEN", "UTA")])
    assert g.loc[0, "away_altitude"] == 1
    assert g.loc[1, "away_altitude"] == 0  # Utah je sám vo výške
    assert g.loc[0, "home_altitude"] == 0


def test_bubble_game_is_played_in_orlando_without_road_trip():
    g = games([("2020-07-31", "LAL", "LAC", True)], season=2020)
    assert g.loc[0, "away_road"] == 0


def test_new_season_resets_rest_and_travel():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-04-14", "2024-10-22"]),
            "season": [2024, 2025],
            "home": ["LAL", "BOS"],
            "away": ["BOS", "NYK"],
            "pts_home": [100, 100],
            "pts_away": [90, 90],
        }
    )
    g = add_features(df)
    assert g.loc[1, "home_rest"] == 7
    assert g.loc[1, "home_km"] == 0


TEAMS = ["BOS", "NYK", "LAL", "DEN", "MIA", "UTA"]


def random_schedule(n, seed):
    import numpy as np

    rng = np.random.default_rng(seed)
    home = rng.choice(TEAMS, n)
    away = [rng.choice([t for t in TEAMS if t != h]) for h in home]
    dates = pd.Timestamp("2024-10-22") + pd.to_timedelta(np.sort(rng.integers(0, 60, n)), unit="D")
    return pd.DataFrame(
        {
            "date": dates,
            "season": 2025,
            "home": home,
            "away": away,
            "pts_home": rng.integers(80, 130, n),
            "pts_away": rng.integers(80, 130, n),
        }
    )


@settings(max_examples=30, deadline=None)
@given(st.integers(min_value=1, max_value=29), st.integers(min_value=0, max_value=10_000))
def test_features_do_not_depend_on_future_games(k, seed):
    games_ = random_schedule(30, seed)
    full = add_features(games_)
    cut = add_features(full.loc[: k - 1, games_.columns])
    cols = [f"{s}_{f}" for s in ("home", "away") for f in FEATURES]
    pd.testing.assert_frame_equal(full.loc[: k - 1, cols], cut[cols])


@settings(max_examples=20, deadline=None)
@given(st.integers(min_value=0, max_value=10_000))
def test_features_do_not_depend_on_results(seed):
    games_ = random_schedule(30, seed)
    flipped = games_.assign(pts_home=games_["pts_away"], pts_away=games_["pts_home"])
    cols = [f"{s}_{f}" for s in ("home", "away") for f in FEATURES]
    pd.testing.assert_frame_equal(add_features(games_)[cols], add_features(flipped)[cols])
