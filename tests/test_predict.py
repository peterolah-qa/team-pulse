"""Integračný test predikcie na malých syntetických dátach."""

import numpy as np
import pandas as pd
import pytest

from team_pulse.model_store import FEATURES_V1, StoredModel
from team_pulse.predict import _fatigue_text, days_word, predict_games, today_et

TEAMS = ["BOS", "NYK", "LAL", "DEN"]
STAT_COLS = ["pts", "fgm", "fga", "ftm", "fta", "oreb", "dreb", "ast", "stl", "blk", "tov", "pf"]
WEIGHTS = {  # približne ako skutočný model v1 (Elo body)
    "home": 44, "home_missing": -24, "away_missing": 21, "strength_diff": 11, "home_rest": 1,
    "home_b2b": -43, "home_three_in4": -6, "home_km": 2, "home_tz_east": -15, "home_road": 0,
    "away_rest": 0, "away_b2b": 49, "away_three_in4": 8, "away_km": 1, "away_tz_east": -4,
    "away_road": -5, "away_altitude": 40,
}  # fmt: skip


def model():
    per_elo = 0.0055 * 100 / 100  # logit na 1 Elo × 100 (vstup elo_diff je v stovkách)
    coef = [per_elo * 100 if f == "elo_diff" else per_elo * WEIGHTS[f] for f in FEATURES_V1]
    return StoredModel("test", FEATURES_V1, coef, 0.0, {"hca": 70}, [2004, 2026], 1, "", {}, WEIGHTS)


def history_and_players():
    rng = np.random.default_rng(0)
    games, box = [], []
    for i in range(60):
        d = pd.Timestamp("2026-01-01") + pd.Timedelta(days=i)
        h, a = rng.choice(TEAMS, 2, replace=False)
        gid = f"H{i:03d}"
        strong = {"BOS": 12, "DEN": 6, "NYK": 0, "LAL": -6}
        margin = strong[h] - strong[a] + 3 + rng.normal(0, 8)
        games.append((gid, d, 2026, h, a, 110 + round(margin / 2), 110 - round(margin / 2) - (margin == 0)))
        for team in (h, a):
            base = TEAMS.index(team) * 10
            for k, mins in enumerate([36, 32, 28, 24, 20, 16, 12, 10]):
                row = dict.fromkeys(STAT_COLS, 0)
                pts = 30 - 3 * k if k else 32
                row.update(pts=pts, fgm=pts // 2, fga=pts // 2 + 4, dreb=4, ast=3)
                box.append({"game_id": gid, "date": d, "season": 2026, "team": team, "player_id": base + k,
                            "player": f"{team}-{k}", "min": float(mins), **row})  # fmt: skip
    hist = pd.DataFrame(games, columns=["game_id", "date", "season", "home", "away", "pts_home", "pts_away"])
    hist = hist[hist["pts_home"] != hist["pts_away"]]
    return hist, pd.DataFrame(box)


def schedule():
    return pd.DataFrame(
        {
            "game_id": ["N1", "N2"],
            "date": pd.to_datetime(["2026-10-20", "2026-10-20"]),
            "tipoff_utc": pd.to_datetime(["2026-10-20T23:00Z", "2026-10-21T02:00Z"]),
            "season": [2027, 2027],
            "kind": ["regular", "regular"],
            "home": ["BOS", "DEN"],
            "away": ["NYK", "LAL"],
            "neutral": [False, False],
            "arena_city": ["Boston", "Denver"],
        }
    )


def roster():
    return pd.DataFrame(
        [
            {"player_id": TEAMS.index(t) * 10 + k, "player": f"{t}-{k}", "team": t}
            for t in TEAMS
            for k in range(8)
        ]
    )


def no_injuries():
    return pd.DataFrame(columns=["team", "player", "player_id", "p_out", "return_date", "status"])


def run(injuries=None):
    hist, players = history_and_players()
    inj = no_injuries() if injuries is None else injuries
    return predict_games(pd.Timestamp("2026-10-20"), hist, players, schedule(), roster(), inj, model(), 0.5)


def test_predictions_have_expected_shape():
    preds = run()
    assert len(preds) == 2
    for r in preds:
        assert 0 < r["p_home"] < 1
        for side in ("home", "away"):
            s = r[side]
            assert 0 <= s["pulse"] <= 100
            assert s["tier"] in {"Silný", "Stabilný", "Oslabený", "Kritický"}
            assert s["confidence"] in {"vysoká", "stredná", "nízka"}
            assert len(s["reasons"]) <= 3


def test_stronger_team_is_favourite():
    bos = run()[0]
    assert bos["home"]["team"] == "BOS"
    assert bos["p_home"] > 0.5 and bos["margin_home"] > 0
    assert bos["home"]["elo"] > bos["away"]["elo"]


def test_star_out_lowers_pulse_and_win_probability():
    inj = pd.DataFrame(
        {
            "team": ["BOS"],
            "player": ["BOS-0"],
            "player_id": pd.array([0], dtype="Int64"),
            "p_out": [1.0],
            "return_date": [pd.NaT],
            "status": ["OUT"],
        }
    )
    base, out = run()[0], run(inj)[0]
    assert out["p_home"] < base["p_home"]
    assert out["home"]["pulse"] < base["home"]["pulse"]
    assert out["home"]["reasons"][0][0].startswith("Bez BOS-0")


def test_questionable_star_lowers_confidence():
    inj = pd.DataFrame(
        {
            "team": ["BOS"],
            "player": ["BOS-0"],
            "player_id": pd.array([0], dtype="Int64"),
            "p_out": [0.5],
            "return_date": [pd.NaT],
            "status": ["QUESTIONABLE"],
        }
    )
    assert run(inj)[0]["home"]["confidence"] in {"stredná", "nízka"}
    assert run()[0]["home"]["confidence"] == "vysoká"


def test_no_games_that_day():
    hist, players = history_and_players()
    assert (
        predict_games(pd.Timestamp("2026-10-19"), hist, players, schedule(), roster(), no_injuries(), model())
        == []
    )


@pytest.mark.parametrize("p", [0.25, 0.5, 0.75])
def test_margin_sign_matches_probability(p):
    import math

    margin = math.log(p / (1 - p)) / 0.0055 / 28
    assert (margin > 0) == (p > 0.5) or p == 0.5


def questionable_star():
    return pd.DataFrame(
        {
            "team": ["BOS"],
            "player": ["BOS-0"],
            "player_id": pd.array([0], dtype="Int64"),
            "p_out": [0.5],
            "return_date": [pd.NaT],
            "status": ["QUESTIONABLE"],
        }
    )


def test_layers_and_contributions_for_game_screen():
    g = run()[0]
    assert g["home_adv"] > 0
    for side in ("home", "away"):
        assert set(g[side]["layers"]) == {"strength", "roster", "players", "fatigue"}
        assert "Sila súpisky" in g[side]["contributions"]


def test_what_if_for_questionable_player():
    g = run(questionable_star())[0]
    wi = g["what_if"]
    assert len(wi) == 1 and wi[0]["player"] == "BOS-0" and wi[0]["side"] == "home"
    assert wi[0]["plays"]["p_home"] > wi[0]["out"]["p_home"]
    assert wi[0]["plays"]["pulse"] > wi[0]["out"]["pulse"]
    assert run()[0]["what_if"] == []


def test_what_if_hides_scenario_without_effect():
    # BOS-2 má malú hodnotu: šanca sa zmení o menej ako 1 p. b. a úroveň ostane → scenár sa neukáže
    injuries = questionable_star().assign(player=["BOS-2"], player_id=pd.array([2], dtype="Int64"))
    assert run(injuries)[0]["what_if"] == []


def test_build_teams_for_team_screen():
    from team_pulse.predict import build_teams
    from team_pulse.state import build_state

    hist, players = history_and_players()
    state = build_state(hist, players, roster(), schedule(), model().elo_params)
    teams = build_teams(state, questionable_star(), model(), pd.Timestamp("2026-10-01"))
    assert set(teams) == set(TEAMS)
    bos = teams["BOS"]
    assert bos["rank"] == 1  # najsilnejší team v syntetických dátach
    assert 0 < len(bos["trend"]) <= 10 and "pulse" in bos["trend"][0]
    assert bos["roster"][0]["player"] == "BOS-0"
    assert bos["roster"][0]["status"] == "QUESTIONABLE"
    assert bos["upcoming"][0]["opp"] == "NYK" and bos["upcoming"][0]["home"]


def test_model_info_for_model_screen():
    from team_pulse.predict import model_info

    info = model_info(model())
    assert {"version", "test_metrics", "calibration", "versions", "elo_weights"} <= set(info)


@pytest.mark.parametrize("n,word", [(0, "dní"), (1, "deň"), (2, "dni"), (4, "dni"), (5, "dní"), (6, "dní")])
def test_days_word(n, word):
    assert days_word(n) == word


def test_rest_reason_text():
    assert _fatigue_text("rest", 3) == "3 dni voľna"
    assert _fatigue_text("rest", 5) == "5 dní voľna"
    assert _fatigue_text("rest", 7) == "Bez zápasu 7+ dní"  # 1. zápas sezóny alebo dlhá prestávka


def test_today_is_us_date():
    """O 01:00 UTC je v USA ešte predchádzajúci večer a jeho zápasy musia ostať v predpovediach."""
    assert today_et(pd.Timestamp("2026-10-21 01:00", tz="UTC")) == pd.Timestamp("2026-10-20")
    assert today_et(pd.Timestamp("2026-10-21 05:00", tz="UTC")) == pd.Timestamp("2026-10-21")
    assert today_et(pd.Timestamp("2026-12-02 04:30", tz="UTC")) == pd.Timestamp("2026-12-01")  # zimný čas
