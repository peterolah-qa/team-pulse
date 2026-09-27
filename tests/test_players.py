"""Testy vrstvy B – dostupnosť hráčov."""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.players import REPLACEMENT, missing_by_team_game, pie_parts

STAT_COLS = ["pts", "fgm", "fga", "ftm", "fta", "oreb", "dreb", "ast", "stl", "blk", "tov", "pf"]


def line(game, date, team, pid, minutes, quality, season=2025):
    """Riadok box score; quality 1 = priemer, 3 = hviezda, 0 = slabý."""
    stats = dict.fromkeys(STAT_COLS, 0)
    stats.update(pts=int(8 * quality), fgm=int(3 * quality), fga=int(3 * quality) + 3, dreb=int(2 * quality))
    stats["ast"] = int(2 * quality)
    return {
        "game_id": game,
        "date": pd.Timestamp(date),
        "season": season,
        "team": team,
        "player_id": pid,
        "min": minutes,
        **stats,
    }


def season_of_games(n_games, star_plays_until=None, bench_plays_until=None):
    """Team AAA: hviezda (id 1), priemerný (2), lavička (3). Súper BBB: 3 priemerní hráči."""
    rows = []
    for i in range(n_games):
        gid, date = f"G{i:03d}", pd.Timestamp("2024-10-22") + pd.Timedelta(days=2 * i)
        if star_plays_until is None or i < star_plays_until:
            rows.append(line(gid, date, "AAA", 1, 36, 3))
        rows.append(line(gid, date, "AAA", 2, 30, 1))
        if bench_plays_until is None or i < bench_plays_until:
            rows.append(line(gid, date, "AAA", 3, 15, 0.3))
        for pid in (11, 12, 13):
            rows.append(line(gid, date, "BBB", pid, 32, 1))
    return pd.DataFrame(rows)


def missing(df, game, team="AAA"):
    m = missing_by_team_game(df)
    return m[(m["game_id"] == game) & (m["team"] == team)].iloc[0]


def test_pie_shares_of_one_game_sum_to_one():
    p = pie_parts(season_of_games(1))
    assert (p["pie_num"] / p["pie_den"]).sum() == pytest.approx(1.0)


def test_full_roster_means_nothing_missing():
    assert missing(season_of_games(12), "G011")["missing"] == 0


def test_missing_star_costs_more_than_missing_bench_player():
    star = missing(season_of_games(12, star_plays_until=11), "G011")
    bench = missing(season_of_games(12, bench_plays_until=11), "G011")
    assert star["n_missing"] == 1 and bench["n_missing"] == 1
    assert star["missing"] > bench["missing"] >= 0


def test_long_absence_fades_out():
    df = season_of_games(30, star_plays_until=11)
    m = missing_by_team_game(df)
    aaa = m[m["team"] == "AAA"].set_index("game_id")["missing"]
    assert aaa["G011"] > aaa["G015"] > 0
    assert aaa["G022"] == 0  # po 10 zápasoch bez hráča už nechýba „nový“ výpadok


def test_traded_player_is_not_missing_for_old_team():
    df = season_of_games(12)
    # hráč 3 od zápasu 10 hrá za BBB
    df.loc[(df["player_id"] == 3) & (df["game_id"] >= "G010"), "team"] = "BBB"
    assert missing(df, "G011")["n_missing"] == 0


def test_new_season_resets_rotation():
    old = season_of_games(12)
    new = season_of_games(1, star_plays_until=0)
    new["game_id"] = "N000"
    new["date"] = pd.Timestamp("2025-10-22")
    new["season"] = 2026
    assert missing(pd.concat([old, new]), "N000")["n_missing"] == 0


def test_unknown_player_has_replacement_value():
    df = season_of_games(3, star_plays_until=2)  # hviezda odohrala len 2 zápasy
    assert missing(df, "G002")["missing"] == pytest.approx(0.0)
    assert REPLACEMENT < 0


@settings(max_examples=15, deadline=None)
@given(st.integers(min_value=5, max_value=25), st.integers(min_value=0, max_value=1000))
def test_missing_does_not_depend_on_future_games(k, seed):
    rng = np.random.default_rng(seed)
    df = season_of_games(26, star_plays_until=int(rng.integers(6, 26)))
    df["pts"] = rng.integers(0, 40, len(df))
    full = missing_by_team_game(df)
    cut = missing_by_team_game(df[df["game_id"] < f"G{k:03d}"])
    merged = cut.merge(full, on=["game_id", "team"], suffixes=("_cut", "_full"))
    assert len(merged) == len(cut)
    np.testing.assert_allclose(merged["missing_cut"], merged["missing_full"])
