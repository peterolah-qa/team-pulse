"""Testy stavu modelu (Mac → cloud)."""

import json

import pandas as pd
import pytest

from team_pulse.predict import predict_from_state, predict_games, upcoming_dates
from team_pulse.state import build_state, load_state, roster_frame, save_state


@pytest.fixture
def parts():
    import test_predict as tp

    hist, players = tp.history_and_players()
    return hist, players, tp.roster(), tp.schedule(), tp.model(), tp.no_injuries()


def test_state_is_json_and_small(parts, tmp_path):
    hist, players, roster, sched, model, _ = parts
    state = build_state(hist, players, roster, sched, model.elo_params)
    path = save_state(state, tmp_path / "state.json")
    assert json.loads(path.read_text())["season"] == 2027
    assert set(state["elo"]) == {"BOS", "NYK", "LAL", "DEN"}
    assert len(state["schedule"]) == 2
    assert path.stat().st_size < 50_000


def test_state_roundtrip_gives_same_predictions(parts, tmp_path):
    hist, players, roster, sched, model, inj = parts
    day = pd.Timestamp("2026-10-20")
    direct = predict_games(day, hist, players, sched, roster, inj, model, 0.5)
    state = load_state(
        save_state(build_state(hist, players, roster, sched, model.elo_params), tmp_path / "s.json")
    )
    assert predict_from_state(state, inj, model, day, 0.5) == direct


def test_unknown_state_version_fails(parts, tmp_path):
    hist, players, roster, sched, model, _ = parts
    state = build_state(hist, players, roster, sched, model.elo_params)
    state["version"] = 999
    with pytest.raises(ValueError, match="verzia"):
        load_state(save_state(state, tmp_path / "s.json"))


def test_roster_frame_supports_name_matching(parts):
    hist, players, roster, sched, model, _ = parts
    rf = roster_frame(build_state(hist, players, roster, sched, model.elo_params))
    assert {"player_id", "player", "team", "norm"} <= set(rf.columns)
    assert len(rf) == len(roster)


def test_upcoming_dates(parts):
    hist, players, roster, sched, model, _ = parts
    state = build_state(hist, players, roster, sched, model.elo_params)
    assert upcoming_dates(state, pd.Timestamp("2026-10-01"), 3) == [pd.Timestamp("2026-10-20")]
    assert upcoming_dates(state, pd.Timestamp("2026-10-21"), 3) == []
