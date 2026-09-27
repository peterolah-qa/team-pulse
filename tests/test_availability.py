"""Testy vrstvy B naživo."""

import pandas as pd
import pytest

from team_pulse.live.availability import (
    Snapshot,
    p_out_for_game,
    player_snapshot,
    season_rotation,
    team_availability,
)

STAT_COLS = ["pts", "fgm", "fga", "ftm", "fta", "oreb", "dreb", "ast", "stl", "blk", "tov", "pf"]


def box(game, date, team, pid, minutes, pts=10, season=2026, name=None):
    row = dict.fromkeys(STAT_COLS, 0)
    row.update(pts=pts, fgm=pts // 2, fga=pts // 2 + 3, dreb=3, ast=2)
    return {
        "game_id": game,
        "date": pd.Timestamp(date),
        "season": season,
        "team": team,
        "player_id": pid,
        "player": name or f"P{pid}",
        "min": minutes,
        **row,
    }


def history():
    rows = []
    for i in range(12):
        gid, d = f"G{i:02d}", pd.Timestamp("2026-01-01") + pd.Timedelta(days=2 * i)
        rows += [box(gid, d, "AAA", 1, 36, 30, name="Hviezda"), box(gid, d, "AAA", 2, 20, 8)]
        if i >= 8:  # posila od 9. zápasu
            rows.append(box(gid, d, "AAA", 3, 30, 12, name="Posila"))
        rows += [box(gid, d, "BBB", 11, 30, 10), box(gid, d, "BBB", 12, 30, 10)]
    return pd.DataFrame(rows)


def test_snapshot_values_and_minutes():
    snap = player_snapshot(history())
    assert snap.value[1] > snap.value[2]  # hviezda je hodnotnejšia
    assert snap.typical_min[1] == pytest.approx(36)
    assert snap.current_team[3] == "AAA"
    assert snap.name[1] == "Hviezda"


def test_rotation_new_player_is_not_diluted_by_games_before_arrival():
    rot = season_rotation(history(), 2026)["AAA"]
    assert rot[1] == pytest.approx(36)
    assert rot[3] == pytest.approx(30)  # 4 zápasy po 30 min, nie 120 / 10


def test_rotation_empty_for_new_season():
    assert season_rotation(history(), 2027) == {}


def test_star_out_raises_missing_and_lowers_strength():
    h = history()
    snap, rot = player_snapshot(h), season_rotation(h, 2026)
    full = team_availability("AAA", {1, 2, 3}, {}, snap, rot)
    no_star = team_availability("AAA", {1, 2, 3}, {1: 1.0}, snap, rot)
    assert full["missing"] == 0
    assert no_star["missing"] > 0
    assert no_star["strength"] < full["strength"]
    assert no_star["absent"][0]["player"] == "Hviezda"


def test_questionable_counts_half():
    h = history()
    snap, rot = player_snapshot(h), season_rotation(h, 2026)
    out = team_availability("AAA", {1, 2, 3}, {1: 1.0}, snap, rot)["missing"]
    half = team_availability("AAA", {1, 2, 3}, {1: 0.5}, snap, rot)["missing"]
    assert half == pytest.approx(out / 2)


def test_player_who_left_roster_counts_as_missing():
    h = history()
    snap, rot = player_snapshot(h), season_rotation(h, 2026)
    assert team_availability("AAA", {2, 3}, {}, snap, rot)["missing"] > 0


def test_strength_uses_only_top_n_players():
    ids = range(20)
    snap = Snapshot(value=dict.fromkeys(ids, 0.05), typical_min=dict.fromkeys(ids, 20.0), current_team={})
    s5 = team_availability("AAA", set(range(20)), {}, snap, {}, top_n=5)["strength"]
    s10 = team_availability("AAA", set(range(20)), {}, snap, {}, top_n=10)["strength"]
    assert s10 == pytest.approx(2 * s5)


def test_p_out_uses_return_date():
    inj = pd.DataFrame(
        {
            "player_id": pd.array([1, 2, None], dtype="Int64"),
            "p_out": [0.5, 0.5, 1.0],
            "return_date": pd.to_datetime(["2026-10-25", "2026-10-15", None]),
        }
    )
    p = p_out_for_game(inj, pd.Timestamp("2026-10-20"))
    assert p == {1: 1.0, 2: 0.5}  # návrat po zápase → OUT; nespárovaný sa ignoruje
