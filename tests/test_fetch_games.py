"""Testy normalizácie zápasov z nba_api (bez siete – na vzorových dátach)."""

import pandas as pd

from team_pulse.data.fetch_games import fix_franchise, normalize, season_label

ABBR = {1610612760: "OKC", 1610612738: "BOS", 1610612766: "CHA", 1610612748: "MIA"}
COLS = ["GAME_ID", "GAME_DATE", "MATCHUP", "TEAM_ID", "TEAM_ABBREVIATION", "PTS"]


def raw(rows):
    return pd.DataFrame(rows, columns=COLS)


def test_two_rows_become_one_game_with_home_and_away():
    r = raw(
        [
            ["1", "2024-11-01", "BOS vs. MIA", 1610612738, "BOS", 110],
            ["1", "2024-11-01", "MIA @ BOS", 1610612748, "MIA", 101],
        ]
    )
    g = normalize(r, 2025, False, ABBR)
    assert len(g) == 1
    assert (g.loc[0, "home"], g.loc[0, "away"]) == ("BOS", "MIA")
    assert (g.loc[0, "pts_home"], g.loc[0, "pts_away"]) == (110, 101)


def test_relocated_team_gets_current_abbreviation():
    r = raw(
        [
            ["2", "2008-01-05", "SEA vs. BOS", 1610612760, "SEA", 95],
            ["2", "2008-01-05", "BOS @ SEA", 1610612738, "BOS", 104],
        ]
    )
    assert normalize(r, 2008, False, ABBR).loc[0, "home"] == "OKC"


def test_charlotte_2001_2002_is_new_orleans_franchise():
    r = raw(
        [
            ["3", "2002-02-01", "CHH vs. MIA", 1610612766, "CHH", 99],
            ["3", "2002-02-01", "MIA @ CHH", 1610612748, "MIA", 90],
        ]
    )
    assert normalize(r, 2002, False, ABBR).loc[0, "home"] == "NOP"


def test_fix_franchise_keeps_modern_charlotte():
    assert fix_franchise("CHA", 2005) == "CHA"
    assert fix_franchise("CHA", 2002) == "NOP"
    assert fix_franchise("BOS", 2002) == "BOS"


def test_game_with_only_one_side_is_dropped():
    r = raw([["4", "2024-11-01", "BOS vs. MIA", 1610612738, "BOS", 110]])
    assert normalize(r, 2025, False, ABBR).empty


def test_season_label():
    assert season_label(2026) == "2025-26"
    assert season_label(2001) == "2000-01"


def test_bubble_games_are_neutral():
    from team_pulse.data.fetch_games import mark_neutral

    g = pd.DataFrame({"date": pd.to_datetime(["2020-03-10", "2020-07-30", "2020-10-11", "2020-12-22"])})
    assert mark_neutral(g)["neutral"].tolist() == [False, True, True, False]
