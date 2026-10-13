"""NHL vrstva C: príznaky únavy z rozpisu a návrh modelu (bez siete, malé dáta)."""

import re

import numpy as np
import pandas as pd
import pytest

from team_pulse.nhl import learned
from team_pulse.nhl.fetch_games import CURRENT, DEFUNCT
from team_pulse.nhl.schedule import UTC_OFFSET, add_features


def games(rows, season=2025):
    """rows: (deň, domáci, hostia[, neutrálny]) → rozpis s dátumom a skóre."""
    out = []
    for i, r in enumerate(rows):
        day, home, away = r[:3]
        out.append({
            "game_id": i + 1, "season": season, "date": pd.Timestamp(day),
            "start_utc": f"{day}T23:00:00Z", "home": home, "away": away, "home_abbr": home, "away_abbr": away,
            "goals_home": 3, "goals_away": 2, "neutral": len(r) > 3 and bool(r[3]), "game_type": "R",
        })  # fmt: skip
    return pd.DataFrame(out)


def row(df, gid):
    return df.set_index("game_id").loc[gid]


def test_every_club_has_a_time_zone():
    assert set(CURRENT + DEFUNCT) <= set(UTC_OFFSET)


def test_rest_back_to_back_and_three_in_four():
    df = add_features(games([
        ("2024-10-10", "BOS", "TOR"),
        ("2024-10-11", "BOS", "MTL"),  # BOS back-to-back
        ("2024-10-13", "BOS", "OTT"),  # BOS 3. zápas za 4 dni
        ("2024-10-20", "BOS", "TOR"),  # dlhý oddych → najviac 7
    ]))  # fmt: skip
    assert row(df, 1)["home_rest"] == 7 and row(df, 1)["home_b2b"] == 0  # prvý zápas sezóny
    assert (row(df, 2)["home_rest"], row(df, 2)["home_b2b"]) == (1, 1)
    assert (row(df, 3)["home_rest"], row(df, 3)["home_three_in4"]) == (2, 1)
    assert (row(df, 4)["home_rest"], row(df, 4)["away_rest"]) == (7, 7)


def test_time_zone_shift_only_eastwards_and_road_trip():
    df = add_features(games([
        ("2024-10-10", "LAK", "BOS"),  # BOS na západe
        ("2024-10-12", "BOS", "CHI"),  # BOS doma po návrate z PT do ET: +3 h na východ; CHI 1. zápas
        ("2024-10-14", "VAN", "BOS"),  # BOS ide na západ: 0
        ("2024-10-15", "SEA", "BOS"),  # 2. zápas na výjazde
    ]))  # fmt: skip
    assert row(df, 2)["home_tz_east"] == 3 and row(df, 2)["home_road"] == 0
    assert row(df, 3)["away_tz_east"] == 0 and row(df, 3)["away_road"] == 1
    assert row(df, 4)["away_road"] == 2 and row(df, 4)["away_b2b"] == 1


def test_relocated_club_uses_its_city_at_the_time():
    df = games([("2010-01-10", "LAK", "WPG"), ("2010-01-12", "WPG", "MTL")], season=2010)
    df.loc[1, "home_abbr"] = "ATL"  # klub WPG hral v roku 2010 v Atlante (ET)
    assert row(add_features(df), 2)["home_tz_east"] == 3  # z Los Angeles do Atlanty: +3 h
    df.loc[1, "home_abbr"] = "WPG"
    assert row(add_features(df), 2)["home_tz_east"] == 2  # do Winnipegu (CT) by to bolo +2 h


def test_neutral_site_has_no_road_and_no_time_shift():
    df = add_features(games([
        ("2024-10-04", "BUF", "NJD", True),  # Praha
        ("2024-10-08", "BUF", "LAK"),
    ]))  # fmt: skip
    assert row(df, 1)["away_road"] == 0 and row(df, 1)["away_tz_east"] == 0
    assert row(df, 2)["home_tz_east"] == 0  # z neutrálneho ľadu sa posun nepočíta


def test_new_season_resets_rest():
    df = pd.concat([games([("2024-04-15", "BOS", "TOR")], 2024), games([("2024-10-10", "BOS", "TOR")], 2025)])
    df["game_id"] = [1, 2]
    out = add_features(df)
    assert row(out, 2)["home_rest"] == 7


def test_features_do_not_depend_on_results():
    rows = [("2024-10-10", "BOS", "TOR"), ("2024-10-11", "TOR", "MTL"), ("2024-10-12", "MTL", "BOS")]
    a = add_features(games(rows))
    b = games(rows)
    b[["goals_home", "goals_away"]] = [[0, 5], [1, 2], [7, 3]]
    cols = [c for c in a if c.startswith(("home_", "away_")) and c not in ("home_abbr", "away_abbr")]
    pd.testing.assert_frame_equal(a[cols], add_features(b)[cols])


def league(seed=3):
    """Malá liga 2018–2026 s efektom back-to-back, aby mal model čo nájsť."""
    rng = np.random.default_rng(seed)
    teams = ["BOS", "TOR", "MTL", "LAK", "SEA", "CHI"]
    rows, gid = [], 0
    for season in range(2018, 2027):
        day = pd.Timestamp(f"{season - 1}-10-10")
        for i in range(150):
            h, a = rng.choice(teams, 2, replace=False)
            day += pd.Timedelta(days=int(rng.integers(0, 2)))
            gid += 1
            won = rng.random() < 0.55
            rows.append({"game_id": gid, "season": season, "game_type": "R", "date": day,
                         "start_utc": f"{day.date()}T{(i % 20):02d}:00:00Z", "home": h, "away": a,
                         "home_abbr": h, "away_abbr": a, "goals_home": 3 if won else 1,
                         "goals_away": 1 if won else 3, "neutral": False})  # fmt: skip
    return pd.DataFrame(rows)


def test_learned_dataset_and_decision():
    ds = learned.build_dataset(league())
    assert {"elo_prob", "elo_diff", "home", "home_won", "away_b2b"} <= set(ds.columns)
    assert "home_road" not in learned.FATIGUE_COLS and "away_road" in learned.FATIGUE_COLS
    r = learned.evaluate(league())
    d = r["decision"]
    assert d["accepted"] == (d["with"] <= d["without"] - learned.THRESHOLD)
    md = learned.to_markdown(r)
    assert "## Rozhodnutie" in md and "hostia: back-to-back" in md
    assert not re.search(r"\bnan\b", md, re.IGNORECASE)


def test_learned_uses_gate_parameters():
    assert (learned.ELO.k, learned.ELO.hca, learned.ELO.carryover) == pytest.approx((6.0, 30.0, 0.8))
