"""Hokejové Elo: vzorce, sezóny a test úniku dát z budúcnosti."""

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.nhl.elo import START, HockeyEloParams, mov_multiplier, run, season_reset, update


def test_mov_multiplier():
    assert mov_multiplier(1, 0) == pytest.approx(0.8048)
    assert mov_multiplier(3, 0) == pytest.approx(0.6686 * math.log(3) + 0.8048)
    assert mov_multiplier(1, 0) < mov_multiplier(2, 0) < mov_multiplier(5, 0)
    assert mov_multiplier(-3, 0) == mov_multiplier(3, 0)
    # výhra favorita sa počíta menej, prekvapenie viac
    assert mov_multiplier(2, 200) < mov_multiplier(2, 0) < mov_multiplier(2, -200)


def test_update_zero_sum_and_direction():
    h, a = update(1505, 1505, 3, 2)
    assert h > 1505 > a and h - 1505 == pytest.approx(1505 - a)
    h2, _ = update(1505, 1505, 6, 2)
    assert h2 > h  # väčšia výhra posunie viac


def test_upset_moves_more_than_expected_win():
    fav_win = update(1600, 1450, 3, 2)[0] - 1600
    upset = update(1450, 1600, 3, 2)[0] - 1450
    assert upset > fav_win > 0


def test_tie_is_an_error():
    with pytest.raises(ValueError, match="remízou"):
        update(1505, 1505, 2, 2)


def test_neutral_site_has_no_home_advantage():
    g = frame([("A", "B", 3, 2)])
    home_edge = 1 / (1 + 10 ** (-START.hca / 400))
    assert run(g.assign(neutral=False))["prob_home"].iloc[0] == pytest.approx(home_edge)
    neutral = run(g.assign(neutral=True))
    assert neutral["prob_home"].iloc[0] == pytest.approx(0.5)
    # na neutrálnom ľade sa po výhre zmení rating ako bez domácej výhody
    assert neutral["elo_home_post"].iloc[0] == pytest.approx(update(1505, 1505, 3, 2, START, neutral=True)[0])
    assert neutral["elo_home_post"].iloc[0] > run(g)["elo_home_post"].iloc[0]


def frame(rows, season=2025, start="2024-10-10"):
    d = pd.DataFrame(rows, columns=["home", "away", "goals_home", "goals_away"])
    d.insert(0, "game_id", range(1, len(d) + 1))
    d.insert(1, "season", season)
    d["start_utc"] = pd.date_range(start, periods=len(d), freq="D").strftime("%Y-%m-%dT23:00:00Z")
    return d


def test_run_starts_at_mean_and_carries_over_between_seasons():
    p = HockeyEloParams(carryover=0.7)
    first, second = frame([("A", "B", 5, 1)], 2025), frame([("A", "B", 2, 3)], 2026, "2025-10-10")
    g = pd.concat([first, second], ignore_index=True)
    res = run(g, p)
    assert res.loc[0, ["elo_home_pre", "elo_away_pre"]].tolist() == [1505, 1505]
    a_end = res.loc[0, "elo_home_post"]
    assert res.loc[1, "elo_home_pre"] == pytest.approx(season_reset(a_end, p))
    assert res.loc[1, "elo_home_pre"] == pytest.approx(0.7 * a_end + 0.3 * 1505)


def test_run_orders_by_start_time_not_by_row_order():
    g = frame([("A", "B", 5, 1), ("C", "A", 4, 2)])
    shuffled = g.iloc[::-1].reset_index(drop=True)
    pd.testing.assert_frame_equal(run(g), run(shuffled))


def test_run_requires_columns():
    with pytest.raises(ValueError, match="goals_home"):
        run(pd.DataFrame({"game_id": [1], "season": [2025], "home": ["A"], "away": ["B"], "goals_away": [1]}))


TEAMS = ["AAA", "BBB", "CCC", "DDD"]


def make_games(n, seed):
    rng = np.random.default_rng(seed)
    home = rng.choice(TEAMS, n)
    away = [rng.choice([t for t in TEAMS if t != h]) for h in home]
    gh = rng.integers(0, 7, n)
    ga = gh + rng.choice([-1, 1], n) * rng.integers(1, 4, n)
    ga = np.where(ga < 0, gh + 1, ga)
    d = frame(list(zip(home, away, gh, ga, strict=True)))
    d["season"] = np.where(np.arange(n) < n // 2, 2025, 2026)
    return d


@settings(max_examples=40, deadline=None)
@given(st.integers(min_value=0, max_value=29), st.integers(min_value=0, max_value=10_000))
def test_changing_result_does_not_change_earlier_predictions(k, seed):
    games = make_games(30, seed)
    base = run(games)
    gh, ga = games["goals_home"].to_numpy().copy(), games["goals_away"].to_numpy().copy()
    gh[k:], ga[k:] = ga[k:].copy(), gh[k:].copy()  # otočíme výsledok zápasu k a všetkých neskorších
    after = run(games.assign(goals_home=gh, goals_away=ga))
    cols = ["elo_home_pre", "elo_away_pre", "prob_home"]
    pd.testing.assert_frame_equal(base.loc[:k, cols], after.loc[:k, cols])
