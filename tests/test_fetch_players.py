"""Testy normalizácie box score hráčov (bez siete)."""

import pandas as pd
import pytest

from team_pulse.data.fetch_players import STATS, normalize, parse_minutes

ABBR = {1610612766: "CHA", 1610612738: "BOS"}


def raw_row(team_id, abbr, minutes, pts=10):
    row = {
        "GAME_ID": "0020100001",
        "GAME_DATE": "2002-01-10",
        "PLAYER_ID": 1,
        "PLAYER_NAME": "Test Hráč",
        "TEAM_ID": team_id,
        "TEAM_ABBREVIATION": abbr,
    }
    row.update({c: 1 for c in STATS})
    row["MIN"], row["PTS"] = minutes, pts
    return row


@pytest.mark.parametrize(
    "value, expected",
    [(34, 34.0), (34.5, 34.5), ("34:30", 34.5), ("12", 12.0), (None, 0.0), ("", 0.0), (float("nan"), 0.0)],
)
def test_parse_minutes(value, expected):
    assert parse_minutes(value) == pytest.approx(expected)


def test_normalize_columns_and_types():
    df = normalize(pd.DataFrame([raw_row(1610612738, "BOS", "30:00", 25)]), 2002, False, ABBR)
    assert df.loc[0, "team"] == "BOS"
    assert df.loc[0, "min"] == 30.0
    assert df.loc[0, "pts"] == 25
    assert {"fgm", "fga", "dreb", "tov", "plus_minus"} <= set(df.columns)


def test_old_charlotte_player_belongs_to_new_orleans_franchise():
    df = normalize(pd.DataFrame([raw_row(1610612766, "CHH", 20)]), 2002, False, ABBR)
    assert df.loc[0, "team"] == "NOP"
