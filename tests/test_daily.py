"""Testy dennej aktualizácie."""

import subprocess

import pandas as pd

from team_pulse.daily import GAME_KEYS, PLAYER_KEYS, git_commit_if_changed, merge_new


def games(rows):
    return pd.DataFrame(rows, columns=["game_id", "date", "home", "away", "pts_home", "pts_away"])


def test_merge_adds_only_new_games():
    old = games([("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 100, 90)])
    new = games(
        [
            ("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 100, 90),
            ("G2", pd.Timestamp("2026-10-21"), "NYK", "PHI", 110, 101),
        ]
    )
    merged, added = merge_new(old, new, GAME_KEYS)
    assert added == 1 and len(merged) == 2


def test_merge_is_idempotent():
    old = games([("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 100, 90)])
    merged, _ = merge_new(old, old, GAME_KEYS)
    again, added = merge_new(merged, old, GAME_KEYS)
    assert added == 0 and len(again) == 1


def test_merge_newer_row_wins():
    old = games([("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 0, 0)])  # ešte nedohraný
    new = games([("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 100, 90)])
    merged, added = merge_new(old, new, GAME_KEYS)
    assert added == 0 and merged.loc[0, "pts_home"] == 100


def test_merge_players_by_game_and_player():
    cols = ["game_id", "player_id", "date", "min"]
    old = pd.DataFrame([("G1", 1, pd.Timestamp("2026-10-20"), 30)], columns=cols)
    new = pd.DataFrame(
        [("G1", 1, pd.Timestamp("2026-10-20"), 30), ("G1", 2, pd.Timestamp("2026-10-20"), 20)], columns=cols
    )
    _, added = merge_new(old, new, PLAYER_KEYS)
    assert added == 1


def test_merge_empty_new_keeps_old():
    old = games([("G1", pd.Timestamp("2026-10-20"), "DET", "BOS", 100, 90)])
    merged, added = merge_new(old, games([]), GAME_KEYS)
    assert added == 0 and merged is old


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def test_commit_only_when_state_changes(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    state = tmp_path / "state.json"
    state.write_text('{"a": 1}\n')
    assert git_commit_if_changed(state.name, "prvý", push=False, cwd=tmp_path)
    assert not git_commit_if_changed(state.name, "rovnaký", push=False, cwd=tmp_path)
    state.write_text('{"a": 2}\n')
    assert git_commit_if_changed(state.name, "zmena", push=False, cwd=tmp_path)
    assert git(tmp_path, "log", "--oneline").count("\n") == 2


def test_same_state_ignores_generated_at(tmp_path):
    import json

    from team_pulse.daily import same_state

    path = tmp_path / "state.json"
    assert not same_state(path, {"a": 1})  # súbor ešte neexistuje
    path.write_text(json.dumps({"generated_at": "2026-09-27T10:00:00", "a": 1}))
    assert same_state(path, {"generated_at": "2026-09-28T10:00:00", "a": 1})
    assert not same_state(path, {"generated_at": "2026-09-28T10:00:00", "a": 2})
