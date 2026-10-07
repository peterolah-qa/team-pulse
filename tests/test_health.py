"""Testy kontroly zdravia."""

import json
from pathlib import Path

import pandas as pd

from team_pulse.health import check_injuries, check_scoreboard, check_state

FIX = Path(__file__).parent / "fixtures"
NOW = pd.Timestamp("2026-09-27T20:00:00Z")


def load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def test_fixture_injuries_are_healthy():
    assert check_injuries(load("espn_injuries"), NOW) == []


def test_unknown_injury_type_is_reported():
    data = load("espn_injuries")
    data["injuries"][0]["injuries"][0]["type"]["name"] = "INJURY_STATUS_NEW"
    problems = check_injuries(data, NOW)
    assert any("neznámy typ" in p for p in problems)


def test_unknown_team_is_reported():
    data = load("espn_injuries")
    data["injuries"][0]["injuries"][0]["athlete"]["team"]["abbreviation"] = "XYZ"
    assert any("XYZ" in p for p in check_injuries(data, NOW))


def test_stale_injuries_are_reported():
    assert any("staré" in p for p in check_injuries(load("espn_injuries"), NOW + pd.Timedelta(days=2)))


def test_scoreboard_fixture_is_healthy():
    assert check_scoreboard(load("espn_scoreboard")) == []


def test_broken_scoreboard_is_reported():
    assert check_scoreboard({"events": [{"id": "1"}]}) != []


def state(last_result, game_dates):
    return {
        "last_result": last_result,
        "schedule": [
            {"game_id": str(i), "date": d, "tipoff_utc": f"{d}T23:00:00Z", "season": 2027}
            for i, d in enumerate(game_dates)
        ],
    }


def test_state_fresh_when_results_up_to_date():
    s = state("2026-10-22", ["2026-10-20", "2026-10-22", "2026-10-25"])
    assert check_state(s, pd.Timestamp("2026-10-24")) == []


def test_state_stale_when_daily_update_missed():
    s = state("2026-10-20", ["2026-10-20", "2026-10-22", "2026-10-25"])
    problems = check_state(s, pd.Timestamp("2026-10-24"))
    assert problems and "neprebehla" in problems[0]


def test_state_before_season_is_not_stale():
    s = state("2026-06-13", ["2026-10-20", "2026-10-22"])
    assert check_state(s, pd.Timestamp("2026-09-27")) == []


def test_preseason_results_from_mac_keep_state_fresh():
    """Výsledky prípravy nie sú v histórii, Mac ich dáva do state["results"]."""
    s = state("2026-06-13", ["2026-10-08", "2026-10-20"])
    s["schedule"][0]["kind"] = "preseason"
    s["results"] = [{"date": "2026-10-08"}]
    assert check_state(s, pd.Timestamp("2026-10-12")) == []


def test_missed_mac_run_detected_in_preseason():
    s = state("2026-06-13", ["2026-10-05", "2026-10-06", "2026-10-20"])
    s["results"] = [{"date": "2026-10-04"}]
    problems = check_state(s, pd.Timestamp("2026-10-09"))
    assert problems and "neprebehla" in problems[0]
