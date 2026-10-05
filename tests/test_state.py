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


def test_recent_results_with_box_score():
    from team_pulse.state import recent_results

    hist = pd.DataFrame(
        {
            "game_id": ["0022600001", "0022600002", "0022500999"],
            "date": pd.to_datetime(["2026-10-20", "2026-10-21", "2026-06-13"]),
            "season": [2027, 2027, 2026],
            "home": ["DET", "NYK", "OKC"],
            "away": ["BOS", "PHI", "IND"],
            "pts_home": [110, 99, 103],
            "pts_away": [104, 101, 91],
        }
    )
    stat = {"oreb": 1, "dreb": 5, "ast": 4, "blk": 1, "stl": 2}
    players = pd.DataFrame(
        [
            {"game_id": "0022600001", "team": "DET", "player": "A", "min": 35.6, "pts": 30, **stat},
            {"game_id": "0022600001", "team": "DET", "player": "B", "min": 12.0, "pts": 4, **stat},
            {"game_id": "0022600001", "team": "BOS", "player": "C", "min": 38.2, "pts": 22, **stat},
        ]
    )
    sched = pd.DataFrame(
        {
            "game_id": ["0012600050", "0022600001", "0022600002"],
            "date": pd.to_datetime(["2026-10-16", "2026-10-20", "2026-10-21"]),
            "season": [2027, 2027, 2027],
            "kind": ["preseason", "regular", "regular"],
            "home": ["DET", "DET", "NYK"],
            "away": ["CHI", "BOS", "PHI"],
            "status": [3, 3, 3],
            "pts_home": [95, 110, 99],
            "pts_away": [97, 104, 101],
        }
    )
    res = recent_results(hist, players, sched, days=3)
    assert [r["game_id"] for r in res] == ["0012600050", "0022600001", "0022600002"]  # bez minulej sezóny
    pre, first, second = res
    assert pre["kind"] == "preseason" and pre["box"] == {}  # z prípravy len skóre
    assert first["box"]["DET"][0] == {
        "player": "A",
        "min": 36,
        "pts": 30,
        "reb": 6,
        "ast": 4,
        "blk": 1,
        "stl": 2,
    }
    assert [p["player"] for p in first["box"]["DET"]] == ["A", "B"]  # podľa minút
    assert second["box"] == {}  # box score ešte nie je stiahnuté
    assert [r["game_id"] for r in recent_results(hist, players, sched, days=1)] == ["0022600002"]
