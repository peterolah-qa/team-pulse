"""Testy súpisiek a párovania mien ESPN ↔ nba_api."""

import pandas as pd
import pytest

from team_pulse.live.roster import match_injuries, normalize_name, parse_roster


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Nikola Jokić", "nikola jokic"),
        ("Luka Dončić", "luka doncic"),
        ("Jaren Jackson Jr.", "jaren jackson"),
        ("P.J. Washington", "pj washington"),
        ("De'Aaron Fox", "deaaron fox"),
        ("Gary Trent Jr", "gary trent"),
        ("Robert Williams III", "robert williams"),
        ("Karl-Anthony Towns", "karl anthony towns"),
        ("  Bojan   Bogdanović ", "bojan bogdanovic"),
    ],
)
def test_normalize_name(raw, expected):
    assert normalize_name(raw) == expected


def roster():
    raw = pd.DataFrame(
        {
            "PERSON_ID": [1, 2, 3, 4, 5, 6],
            "DISPLAY_FIRST_LAST": [
                "Nikola Jokić",
                "Jaren Jackson Jr.",
                "Herbert Jones",
                "Jalen Williams",
                "Jaylin Williams",
                "Free Agent",
            ],
            "TEAM_ID": [10, 20, 30, 40, 40, 0],
            "TEAM_ABBREVIATION": ["DEN", "MEM", "NOP", "OKC", "OKC", ""],
        }
    )
    return parse_roster(raw, {})


def test_parse_roster_skips_free_agents():
    r = roster()
    assert len(r) == 5
    assert "Free Agent" not in set(r["player"])


def injuries(rows):
    return pd.DataFrame(rows, columns=["team", "player", "status"])


def test_match_by_team_and_name_with_accents_and_suffix():
    m = match_injuries(injuries([("DEN", "Nikola Jokic", "OUT"), ("MEM", "Jaren Jackson", "OUT")]), roster())
    assert m["player_id"].tolist() == [1, 2]
    assert m["match"].tolist() == ["team", "team"]


def test_match_by_name_when_espn_team_is_stale():
    m = match_injuries(injuries([("MIA", "Nikola Jokić", "OUT")]), roster())
    assert (m.loc[0, "player_id"], m.loc[0, "match"]) == (1, "name")


def test_match_by_initial_for_nicknames():
    m = match_injuries(injuries([("NOP", "Herb Jones", "QUESTIONABLE")]), roster())
    assert (m.loc[0, "player_id"], m.loc[0, "match"]) == (3, "initial")


def test_ambiguous_initial_is_not_guessed():
    # J. Williams sú v OKC dvaja → radšej nespárovať než spárovať zle
    m = match_injuries(injuries([("OKC", "J. Williams", "OUT")]), roster())
    assert pd.isna(m.loc[0, "player_id"])


def test_unknown_player_stays_unmatched():
    m = match_injuries(injuries([("DEN", "Rookie Nobody", "OUT")]), roster())
    assert pd.isna(m.loc[0, "player_id"]) and m.loc[0, "match"] is None
