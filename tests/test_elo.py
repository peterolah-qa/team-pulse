"""Unit testy vrstvy A – ručne spočítané príklady a skutočné čísla z archívu FiveThirtyEight."""

import pandas as pd
import pytest

from team_pulse.elo import (
    EloParams,
    expected_home,
    k_factor,
    run,
    season_reset,
    spread,
    update,
)


def test_expected_home_equal_teams_with_home_court():
    # 1500 vs 1500, domáci +100 → 1 / (1 + 10^-0.25)
    assert expected_home(1500, 1500, hca=100) == pytest.approx(0.640065, abs=1e-6)


def test_expected_home_neutral_court_is_coin_flip():
    assert expected_home(1500, 1500, hca=100, neutral=True) == pytest.approx(0.5)


def test_k_factor_hand_computed():
    # 20 * (10 + 3)^0.8 / 7.5
    assert k_factor(10, 0.0) == pytest.approx(20 * 13**0.8 / 7.5)


def test_k_factor_smaller_when_favourite_wins():
    assert k_factor(10, elo_diff_winner=200) < k_factor(10, elo_diff_winner=-200)


def test_update_matches_first_game_in_538_archive():
    # 1. 11. 1946: Toronto Huskies (doma) 66 – 68 New York Knicks, obaja 1300
    home, away = update(1300, 1300, 66, 68)
    assert home == pytest.approx(1293.2767, abs=1e-4)
    assert away == pytest.approx(1306.7233, abs=1e-4)


def test_update_rejects_tie():
    with pytest.raises(ValueError):
        update(1500, 1500, 100, 100)


def test_season_reset_regresses_to_mean():
    # 0.75 * 1600 + 0.25 * 1505
    assert season_reset(1600) == pytest.approx(1576.25)


def test_spread_in_points():
    # (1600 - 1500 + 100) / 28
    assert spread(1600, 1500, hca=100) == pytest.approx(200 / 28)


def test_run_requires_columns():
    with pytest.raises(ValueError, match="chýbajú stĺpce"):
        run(pd.DataFrame({"date": [], "home": []}))


def test_run_resets_ratings_between_seasons():
    games = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-04-01", "2024-10-25"]),
            "season": [2024, 2025],
            "home": ["AAA", "AAA"],
            "away": ["BBB", "BBB"],
            "pts_home": [110, 100],
            "pts_away": [100, 110],
        }
    )
    p = EloParams()
    res = run(games, p, initial={"AAA": 1505, "BBB": 1505})
    post_first = res.loc[0, "elo_home_post"]
    assert res.loc[1, "elo_home_pre"] == pytest.approx(season_reset(post_first, p))


def test_early_multiplier_default_is_off():
    from team_pulse.elo import early_multiplier

    assert early_multiplier(0, EloParams()) == 1.0


def test_early_multiplier_decays_to_one():
    from team_pulse.elo import early_multiplier

    p = EloParams(early_boost=1.0, early_games=20)
    assert early_multiplier(0, p) == pytest.approx(2.0)
    assert early_multiplier(10, p) == pytest.approx(1.5)
    assert early_multiplier(20, p) == pytest.approx(1.0)
    assert early_multiplier(50, p) == pytest.approx(1.0)


def test_dynamic_k_moves_ratings_more_at_season_start():
    games = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-10-22"]),
            "season": [2025],
            "home": ["AAA"],
            "away": ["BBB"],
            "pts_home": [120],
            "pts_away": [100],
        }
    )
    init = {"AAA": 1505, "BBB": 1505}
    plain = run(games, EloParams(), initial=init).loc[0, "elo_home_post"]
    boosted = run(games, EloParams(early_boost=1.0), initial=init).loc[0, "elo_home_post"]
    assert boosted - 1505 == pytest.approx(2 * (plain - 1505))
