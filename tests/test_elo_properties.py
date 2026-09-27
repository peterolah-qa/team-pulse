"""Property-based testy – vlastnosti, ktoré musia platiť pre ľubovoľné vstupy."""

from hypothesis import given
from hypothesis import strategies as st

from team_pulse.elo import expected_home, update

elo = st.floats(min_value=1000, max_value=2000, allow_nan=False)
pts = st.integers(min_value=60, max_value=160)


@given(elo, elo)
def test_probability_is_between_0_and_1(a, b):
    assert 0.0 < expected_home(a, b, hca=100) < 1.0


@given(elo, elo)
def test_probabilities_of_both_teams_sum_to_1(a, b):
    assert abs(expected_home(a, b, 0, neutral=True) + expected_home(b, a, 0, neutral=True) - 1.0) < 1e-12


@given(elo, elo, pts, pts)
def test_elo_is_zero_sum(a, b, ph, pa):
    if ph == pa:
        return
    na, nb = update(a, b, ph, pa)
    assert abs((na + nb) - (a + b)) < 1e-9


@given(elo, elo, pts, pts)
def test_winner_gains_and_loser_loses(a, b, ph, pa):
    if ph == pa:
        return
    na, nb = update(a, b, ph, pa)
    if ph > pa:
        assert na > a and nb < b
    else:
        assert na < a and nb > b


@given(elo, elo, st.floats(min_value=1, max_value=300))
def test_stronger_home_team_has_higher_probability(a, b, bonus):
    assert expected_home(a + bonus, b, 100) > expected_home(a, b, 100)
