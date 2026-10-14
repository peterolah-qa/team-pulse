"""NHL vrstva G: sťahovač brankárov, kvalita brankára pred zápasom a návrh modelu (bez siete)."""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from team_pulse.nhl import fetch_goalies as fgo
from team_pulse.nhl import goalies as gl
from team_pulse.nhl import learned_goalies as lg

FIX = Path(__file__).parent / "fixtures"


# --- sťahovač ------------------------------------------------------------------------------


def test_parse_real_row():
    data = json.loads((FIX / "nhl_goalie_games.json").read_text(encoding="utf-8"))
    row = fgo.parse_row(data["data"][0], 2025, "R")
    assert row == {
        "game_id": 2024020001, "season": 2025, "game_type": "R", "date": "2024-10-04", "team_abbr": "BUF",
        "team": "BUF", "home": True, "player_id": 8480045, "name": "Ukko-Pekka Luukkonen", "started": True,
        "shots_against": 22, "saves": 19, "goals_against": 3, "toi": 3545,
    }  # fmt: skip
    assert data["total"] >= 2 * 1312  # skutočná sezóna 2024/25: aspoň dvaja brankári na zápas


def api_row(gid, team, pid, started=1, home="H", shots=30, saves=27):
    return {"gameId": gid, "gameDate": "2024-10-10", "teamAbbrev": team, "homeRoad": home, "playerId": pid,
            "goalieFullName": f"G{pid}", "gamesStarted": started, "shotsAgainst": shots, "saves": saves,
            "goalsAgainst": shots - saves, "timeOnIce": 3600}  # fmt: skip


class Pages:
    """Podstrčené API: 230 riadkov základnej časti po 100, 3 riadky playoff."""

    def __init__(self, regular=230, playoff=3, lie=0):
        self.data = {
            2: [api_row(i // 2, "TOR", i) for i in range(regular)],
            3: [api_row(9000 + i, "BOS", i) for i in range(playoff)],
        }
        self.lie, self.calls = lie, []

    def get(self, url, params, timeout):
        type_id = int(params["cayenneExp"][-1])
        start = params["start"]
        self.calls.append((type_id, start))
        rows = self.data[type_id]
        body = {"total": len(rows) + self.lie, "data": rows[start : start + params["limit"]]}
        return type("R", (), {"json": lambda s: body, "raise_for_status": lambda s: None})()


def test_fetch_season_pages_through_all_rows():
    s = Pages()
    df = fgo.fetch_season(s, 2025, pause=0)
    assert len(df) == 233 and s.calls == [(2, 0), (2, 100), (2, 200), (3, 0)]
    assert set(df["game_type"]) == {"R", "P"}


def test_fetch_season_refuses_incomplete_download():
    with pytest.raises(ValueError, match="API hlási 235 riadkov, prišlo 230"):
        fgo.fetch_season(Pages(lie=5), 2025, pause=0)


def test_check_starters_finds_missing_and_double_starters():
    games = pd.DataFrame({"game_id": [1, 2, 3], "home": ["WPG", "TOR", "BOS"], "away": ["UTA", "MTL", "NYR"]})
    rows = [
        api_row(1, "ATL", 10), api_row(1, "PHX", 11, home="R"),  # zaniknuté skratky → dnešné kluby
        api_row(2, "TOR", 12), api_row(2, "MTL", 13, home="R"), api_row(2, "MTL", 14, started=1, home="R"),
        api_row(3, "BOS", 15),
    ]  # fmt: skip
    goalies = pd.DataFrame([fgo.parse_row(r, 2010, "R") for r in rows])
    bad = fgo.check_starters(goalies, games)
    assert bad[["game_id", "team", "starters"]].values.tolist() == [[2, "MTL", 2], [3, "NYR", 0]]


# --- kvalita brankára -----------------------------------------------------------------------


def schedule(n, season=2025):
    teams = [("BOS", "TOR"), ("TOR", "BOS")]
    return pd.DataFrame(
        {
            "game_id": range(1, n + 1),
            "season": season,
            "start_utc": [f"2024-10-{10 + i:02d}T23:00:00Z" for i in range(n)],
            "home": [teams[i % 2][0] for i in range(n)],
            "away": [teams[i % 2][1] for i in range(n)],
        }
    )


def goalie_rows(games, starters, saves=27, shots=30):
    """starters: {(game_id, team): player_id}."""
    rows = []
    for r in games.itertuples(index=False):
        for team in (r.home, r.away):
            pid = starters.get((r.game_id, team), 100 if team == "BOS" else 200)
            rows.append(
                {
                    "game_id": r.game_id,
                    "season": r.season,
                    "team": team,
                    "player_id": pid,
                    "started": True,
                    "saves": saves,
                    "shots_against": shots,
                }
            )
    return pd.DataFrame(rows)


def test_first_game_is_neutral_and_quality_follows_saves():
    games = schedule(3)
    gs = goalie_rows(games, {})
    gs.loc[gs["team"] == "BOS", "saves"] = 29  # BOS chytá lepšie
    out = gl.add_features(games, gs).set_index("game_id")
    assert out.loc[1, "home_goalie_expected"] == 0 and out.loc[1, "goalie_known_diff"] == 0
    bos2 = out.loc[2, "away_goalie_known"]  # BOS je v 2. zápase hosť
    assert bos2 > 0 > out.loc[2, "home_goalie_known"]


def test_known_uses_actual_starter_expected_uses_recent_starts():
    games = schedule(4)
    gs = goalie_rows(games, {(4, "TOR"): 201})  # v 4. zápase chytá za TOR náhradník bez histórie
    gs.loc[gs["player_id"] == 200, "saves"] = 29
    out = gl.add_features(games, gs).set_index("game_id")
    # 4. zápas: TOR doma
    assert out.loc[4, "home_goalie_known"] == pytest.approx(0.0)  # nový brankár = priemer ligy
    assert out.loc[4, "home_goalie_expected"] > 0  # jednotka TOR (200) je nad priemerom


def test_goalie_features_do_not_see_the_game_itself_or_the_future():
    games = schedule(6)
    base = gl.add_features(games, goalie_rows(games, {}))
    gs = goalie_rows(games, {})
    gs.loc[(gs["game_id"] >= 4) & (gs["team"] == "BOS"), "saves"] = 10  # BOS: katastrofa od 4. zápasu
    changed = gl.add_features(games, gs)
    cols = ["goalie_expected_diff", "goalie_known_diff"]
    pd.testing.assert_frame_equal(base.loc[:3, cols], changed.loc[:3, cols])
    assert not base.loc[4:, cols].equals(changed.loc[4:, cols])


def test_double_starter_falls_back_to_expected():
    games = schedule(3)
    gs = goalie_rows(games, {})
    extra = gs[(gs["game_id"] == 3) & (gs["team"] == "BOS")].assign(player_id=999)
    out = gl.add_features(games, pd.concat([gs, extra])).set_index("game_id")
    assert not out.loc[3, "goalie_known_ok"] and out.loc[2, "goalie_known_ok"]
    assert out.loc[3, "home_goalie_known"] == out.loc[3, "home_goalie_expected"]


def test_league_save_pct_uses_previous_season():
    gs = pd.DataFrame({"season": [2024, 2025], "saves": [90, 80], "shots_against": [100, 100]})
    assert gl.league_save_pct(gs) == {2024: 0.9, 2025: 0.9}


# --- návrh modelu ---------------------------------------------------------------------------


def league(seed=5):
    """Malá liga 2018–2026, kde brankár naozaj rozhoduje: jednotky chytajú lepšie než náhradníci."""
    rng = np.random.default_rng(seed)
    teams = ["BOS", "TOR", "MTL", "LAK", "SEA", "CHI"]
    games, goalies, gid = [], [], 0
    for season in range(2018, 2027):
        day = pd.Timestamp(f"{season - 1}-10-10")
        for i in range(200):
            h, a = rng.choice(teams, 2, replace=False)
            day += pd.Timedelta(days=int(rng.integers(0, 2)))
            gid += 1
            starters = {t: (teams.index(t) * 10 + (0 if rng.random() < 0.7 else 1)) for t in (h, a)}
            edge = (1 if starters[h] % 10 == 0 else -1) - (1 if starters[a] % 10 == 0 else -1)
            won = rng.random() < 0.54 + 0.06 * edge
            games.append(
                {
                    "game_id": gid,
                    "season": season,
                    "game_type": "R",
                    "date": day,
                    "home": h,
                    "away": a,
                    "start_utc": f"{day.date()}T{(i % 20):02d}:00:00Z",
                    "home_abbr": h,
                    "away_abbr": a,
                    "goals_home": 3 if won else 1,
                    "goals_away": 1 if won else 3,
                    "neutral": False,
                }
            )
            for t in (h, a):
                good = starters[t] % 10 == 0
                goalies.append(
                    {
                        "game_id": gid,
                        "season": season,
                        "team": t,
                        "player_id": starters[t],
                        "started": True,
                        "shots_against": 30,
                        "saves": 28 if good else 26,
                    }
                )
    return pd.DataFrame(games), pd.DataFrame(goalies)


def test_goalie_proposal_report():
    games, goalies = league()
    r = lg.evaluate(games, goalies)
    assert list(r["summary"]["model"]) == [lg.BASE, lg.EXPECTED, lg.KNOWN]
    assert r["coverage"] == 1.0
    d = r["decisions"][lg.KNOWN]
    assert d["accepted"] == (d["gain"] >= lg.THRESHOLD) and d["gain"] > 0  # skutočný brankár tu pomáha
    md = lg.to_markdown(r)
    assert "## Rozhodnutie" in md and "skutočný brankár" in md
    assert not re.search(r"\bnan\b", md, re.IGNORECASE)
