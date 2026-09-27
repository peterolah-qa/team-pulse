"""Testy Pulse, úrovní, pravidla poklesu, dôvodov a istoty."""

import pytest

from team_pulse.pulse import confidence, pulse_from_elo, team_state, tier_index


@pytest.mark.parametrize("elo, pulse", [(1505, 50), (1625, 70), (1385, 30), (1805, 100), (1205, 0)])
def test_pulse_from_elo(elo, pulse):
    assert pulse_from_elo(elo) == pytest.approx(pulse)


BOUNDARIES = [(100, 0), (70, 0), (69.9, 1), (50, 1), (49.9, 2), (30, 2), (29.9, 3), (0, 3)]


@pytest.mark.parametrize("pulse, idx", BOUNDARIES)
def test_tier_boundaries(pulse, idx):
    assert tier_index(pulse) == idx


def test_no_contributions_keeps_normal_tier():
    s = team_state(1700, {})
    assert s["tier"] == s["normal_tier"] == "Silný"
    assert s["reasons"] == [] and not s["dropped"]


def test_drop_rule_lowers_tier_even_above_threshold():
    # 1750 → 1680: Pulse 79 by stále bol „Silný“, ale pokles 70 Elo ho posunie o úroveň nižšie
    s = team_state(1750, {"Bez hviezdy": -70})
    assert s["pulse"] > 70
    assert s["dropped"] and s["tier"] == "Stabilný"
    assert s["normal_tier"] == "Silný"


def test_small_drop_does_not_trigger_rule():
    s = team_state(1700, {"2. zápas za 2 dni": -40})
    assert not s["dropped"] and s["tier"] == "Silný"


def test_reasons_top3_by_absolute_impact_and_threshold():
    s = team_state(1505, {"a": -5, "b": 30, "c": -60, "d": 12, "e": -11})
    assert [k for k, _ in s["reasons"]] == ["c", "b", "d"]


def test_pulse_never_leaves_0_100():
    assert team_state(2500, {})["pulse"] == 100
    assert team_state(900, {"x": -300})["pulse"] == 0


@pytest.mark.parametrize(
    "a, b, swing, age, expected",
    [
        ("Silný", "Silný", 5, 0.5, "vysoká"),
        ("Silný", "Silný", 20, 0.5, "stredná"),
        ("Silný", "Silný", 5, 3, "stredná"),
        ("Silný", "Stabilný", 5, 0.5, "nízka"),
        ("Silný", "Silný", 50, 0.5, "nízka"),
        ("Silný", "Silný", 5, 8, "nízka"),
    ],
)
def test_confidence(a, b, swing, age, expected):
    assert confidence(a, b, swing, age) == expected
