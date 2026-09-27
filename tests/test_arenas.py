"""Testy tabuľky arén."""

from pathlib import Path

import pandas as pd
import pytest

from team_pulse.arenas import distance_km, location, table

CURRENT_TEAMS = {
    "ATL",
    "BOS",
    "BKN",
    "CHA",
    "CHI",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GSW",
    "HOU",
    "IND",
    "LAC",
    "LAL",
    "MEM",
    "MIA",
    "MIL",
    "MIN",
    "NOP",
    "NYK",
    "OKC",
    "ORL",
    "PHI",
    "PHX",
    "POR",
    "SAC",
    "SAS",
    "TOR",
    "UTA",
    "WAS",
}
GAMES = Path("data/raw/games.parquet")


def test_table_has_exactly_30_teams():
    assert set(table()["team"]) == CURRENT_TEAMS


@pytest.mark.parametrize("season", range(2005, 2027))
def test_every_team_has_exactly_one_arena_each_season(season):
    for team in CURRENT_TEAMS:
        location(team, season)  # vyhodí KeyError, ak chýba alebo sa prekrýva


def test_coordinates_are_in_north_america():
    t = table()
    assert t["lat"].between(24, 50).all()
    assert t["lon"].between(-125, -70).all()


def test_relocated_franchises():
    assert location("OKC", 2008).city == "Seattle"
    assert location("OKC", 2009).city == "Oklahoma City"
    assert location("BKN", 2012).city == "New Jersey"
    assert location("MEM", 2001).city == "Vancouver"
    assert location("NOP", 2006).city == "Oklahoma City"


def test_charlotte_did_not_exist_2003_2004():
    with pytest.raises(KeyError):
        location("CHA", 2004)


def test_distance_new_york_los_angeles():
    # skutočná vzdušná vzdialenosť cca 3 940 km
    assert distance_km(location("NYK", 2025), location("LAL", 2025)) == pytest.approx(3940, abs=40)


def test_distance_to_itself_is_zero():
    a = location("DEN", 2025)
    assert distance_km(a, a) == 0


def test_denver_and_utah_are_high_altitude():
    assert location("DEN", 2025).altitude_m > 1500
    assert location("UTA", 2025).altitude_m > 1200


@pytest.mark.skipif(not GAMES.exists(), reason="chýbajú stiahnuté zápasy")
def test_every_team_season_in_data_has_arena():
    games = pd.read_parquet(GAMES)
    pairs = set(zip(games["home"], games["season"], strict=True))
    missing = []
    for team, season in pairs:
        try:
            location(team, int(season))
        except KeyError:
            missing.append((team, int(season)))
    assert not missing, f"chýbajú arény: {sorted(missing)[:10]}"
