"""Contract testy živých zdrojov na uložených ukážkach (tests/fixtures).

Keď ESPN alebo NBA zmení formát, tieto testy zlyhajú skôr, než sa pokazí appka.
Ukážky obnovíš:  uv run python scripts/probe_sources.py
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from team_pulse.live.injuries import STATUS, espn_player_id, parse_injuries
from team_pulse.live.schedule import parse_schedule, season_end_year
from team_pulse.live.scoreboard import parse_scoreboard
from team_pulse.live.teams import ESPN_ALIASES, from_espn, our_teams

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


# --- teamy ---------------------------------------------------------------


def test_espn_aliases_map_to_our_teams():
    assert set(ESPN_ALIASES.values()) <= our_teams()


@pytest.mark.parametrize("espn, ours", [("NY", "NYK"), ("SA", "SAS"), ("BOS", "BOS"), ("UTAH", "UTA")])
def test_from_espn(espn, ours):
    assert from_espn(espn) == ours


def test_unknown_team_fails_loudly():
    with pytest.raises(KeyError):
        from_espn("XYZ")


# --- zranenia ESPN ---------------------------------------------------------


def test_injuries_fixture_has_expected_shape():
    data = load("espn_injuries")
    assert data["status"] == "success"
    inj = data["injuries"][0]["injuries"][0]
    for key in ("status", "date", "athlete", "type"):
        assert key in inj
    assert "abbreviation" in inj["athlete"]["team"]
    assert inj["type"]["name"].startswith("INJURY_STATUS_")


def test_parse_injuries():
    df = parse_injuries(load("espn_injuries"))
    assert len(df) > 0
    assert set(df["team"]) <= our_teams()
    assert df["status"].isin(["OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE"]).all()
    assert df["p_out"].between(0, 1).all()
    assert df["espn_id"].notna().all()
    veesaar = df[df["player"] == "Henri Veesaar"].iloc[0]
    assert (veesaar["team"], veesaar["status"], veesaar["p_out"]) == ("ATL", "OUT", 1.0)
    assert veesaar["espn_id"] == 5105571


def test_all_fixture_statuses_are_known():
    data = load("espn_injuries")
    types = {i["type"]["name"] for t in data["injuries"] for i in t["injuries"]}
    assert types <= set(STATUS), f"nový typ zranenia od ESPN: {types - set(STATUS)}"


def test_espn_player_id_from_links():
    assert espn_player_id({"links": [{"href": "https://www.espn.com/nba/player/_/id/123/x"}]}) == 123
    assert espn_player_id({"links": []}) is None


# --- scoreboard ESPN ---------------------------------------------------------


def test_parse_scoreboard():
    df = parse_scoreboard(load("espn_scoreboard"))
    assert len(df) == 3
    first = df.iloc[0]
    assert (first["home"], first["away"]) == ("DET", "BOS")
    assert df.loc[1, "home"] == "NYK"  # ESPN „NY“
    assert df.loc[2, "home"] == "SAS"  # ESPN „SA“
    assert (df["state"] == "pre").all() and not df["completed"].any()


def test_scoreboard_ignores_betting_odds():
    df = parse_scoreboard(load("espn_scoreboard"))
    assert not any("odds" in c or "spread" in c for c in df.columns)


# --- rozpis NBA ---------------------------------------------------------------


def test_season_end_year():
    assert season_end_year("2026-27") == 2027


def test_schedule_fixture_has_expected_shape():
    ls = load("nba_schedule")["leagueSchedule"]
    g = ls["gameDates"][0]["games"][0]
    for key in ("gameId", "gameDateEst", "gameDateTimeUTC", "homeTeam", "awayTeam", "isNeutral"):
        assert key in g
    assert "teamTricode" in g["homeTeam"]


def test_preseason_is_skipped_by_default():
    data = load("nba_schedule")  # ukážka obsahuje len prípravné zápasy
    assert parse_schedule(data).empty
    pre = parse_schedule(data, include_preseason=True)
    assert len(pre) == 6
    assert (pre["kind"] == "preseason").all()
    assert set(pre["home"]) | set(pre["away"]) <= our_teams()
    assert pre["season"].eq(2027).all()


def test_schedule_regular_season_game_is_parsed():
    data = load("nba_schedule")
    g = json.loads(json.dumps(data["leagueSchedule"]["gameDates"][0]["games"][0]))
    g["gameId"] = "0022600001"
    data["leagueSchedule"]["gameDates"] = [{"gameDate": "x", "games": [g]}]
    df = parse_schedule(data)
    assert len(df) == 1
    row = df.iloc[0]
    assert (row["kind"], row["home"], row["away"]) == ("regular", "TOR", "MIA")
    assert row["date"] == pd.Timestamp("2026-10-03")
