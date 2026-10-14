"""NHL sťahovač: spracovanie rozpisu klubov a kontrola úplnosti (bez siete).

Tvar zápasu je podľa skutočnej odpovede api-web.nhle.com (zápas 2024020001, NJD – BUF v Prahe).
Contract test na uloženej ukážke:  uv run python scripts/probe_nhl.py  (z Macu)
"""

import json
from pathlib import Path

import pandas as pd
import pytest
import requests

from team_pulse.nhl import fetch_games as fg

FIX = Path(__file__).parent / "fixtures"


def game(gid, home="BUF", away="NJD", gh=1, ga=4, season=20242025, gtype=2, state="OFF", last="REG",
         start="2024-10-04T17:00:00Z", date="2024-10-04", neutral=None):  # fmt: skip
    g = {
        "id": gid,
        "season": season,
        "gameType": gtype,
        "gameDate": date,
        "venue": {"default": "O2 Czech Republic"},
        "startTimeUTC": start,
        "easternUTCOffset": "-04:00",
        "gameState": state,
        "gameScheduleState": "OK",
        "awayTeam": {"id": 1, "abbrev": away, "score": ga},
        "homeTeam": {"id": 7, "abbrev": home, "score": gh},
        "periodDescriptor": {"number": 3, "periodType": "REG", "maxRegulationPeriods": 3},
        "gameOutcome": {"lastPeriodType": last},
    }
    if state == "FUT":  # budúci zápas: bez skóre a výsledku
        del g["awayTeam"]["score"], g["homeTeam"]["score"], g["gameOutcome"]
    if neutral is not None:
        g["neutralSite"] = neutral
    return g


def test_parse_game_from_real_shape():
    row = fg.parse_game(game(2024020001, neutral=True))
    assert row == {
        "game_id": 2024020001, "season": 2025, "game_type": "R", "date": "2024-10-04",
        "start_utc": "2024-10-04T17:00:00Z", "home_abbr": "BUF", "away_abbr": "NJD", "goals_home": 1,
        "goals_away": 4, "state": "OFF", "last_period": "REG", "neutral": True,
    }  # fmt: skip


def test_parse_future_game_has_no_score():
    row = fg.parse_game(game(2026020500, state="FUT"))
    assert row["goals_home"] is None and row["last_period"] is None and row["neutral"] is False


def test_season_frame_dedups_and_keeps_only_regular_and_playoff():
    raw = [
        game(1, state="FUT"),  # z rozpisu jedného klubu ešte nedohraný
        game(1, gh=3, ga=2, last="SO"),  # z rozpisu súpera už dohraný → vyhrá dohraná verzia
        game(1, state="FUT"),
        game(2, gtype=1),  # príprava
        game(3, gtype=4),  # All-Star
        game(4, gtype=3, start="2025-04-20T23:00:00Z"),  # playoff
    ]
    df = fg.season_frame(raw)
    assert df["game_id"].tolist() == [1, 4]
    first = df.iloc[0]
    assert (first["state"], first["goals_home"], first["last_period"]) == ("OFF", 3, "SO")
    assert df["game_type"].tolist() == ["R", "P"]


def test_expected_regular_matches_league_size():
    e = fg.EXPECTED_REGULAR
    assert set(e) == set(range(2006, 2028))
    assert e[2010] == 30 * 82 // 2 and e[2018] == 31 * 82 // 2 and e[2022] == 32 * 82 // 2
    assert e[2013] == 30 * 48 // 2 and e[2021] == 31 * 56 // 2 and e[2027] == 32 * 84 // 2


def season_of(n, end_year=2010, state="OFF"):
    rows = [fg.parse_game(game(i, season=int(fg.season_id(end_year)), state=state)) for i in range(n)]
    return pd.DataFrame(rows, columns=fg.COLUMNS)


def test_check_complete_catches_missing_game():
    # skutočný prípad: rozpis len podľa dnešných klubov stratí zápas ATL – PHX (1229 namiesto 1230)
    with pytest.raises(ValueError, match="1229 zápasov základnej časti, liga ich mala 1230"):
        fg.check_complete(season_of(1229), 2010, finished_season=True)
    fg.check_complete(season_of(1230), 2010, finished_season=True)


def test_check_complete_finished_season_must_be_fully_played():
    df = season_of(1230)
    df.loc[5, "state"] = "FUT"
    with pytest.raises(ValueError, match="1 zápasov nie je dohratých"):
        fg.check_complete(df, 2010, finished_season=True)
    fg.check_complete(season_of(1344, 2027, state="FUT"), 2027, finished_season=False)  # rozohratá sezóna


def test_check_complete_unknown_season():
    with pytest.raises(ValueError, match="EXPECTED_REGULAR"):
        fg.check_complete(season_of(10, 2030), 2030, finished_season=True)


def test_finished_games_maps_relocated_clubs_and_drops_unplayed():
    df = fg.season_frame([
        game(1, home="ATL", away="PHX", gh=2, ga=3, last="OT"),
        game(2, home="ARI", away="WPG", gh=5, ga=1),
        game(3, home="UTA", away="SEA", state="FUT"),
    ])  # fmt: skip
    out = fg.finished_games(df)
    assert out[["home", "away"]].values.tolist() == [["WPG", "UTA"], ["UTA", "WPG"]]
    assert out[["home_abbr", "away_abbr"]].values.tolist() == [["ATL", "PHX"], ["ARI", "WPG"]]
    assert out["goals_home"].dtype.kind == "i" and str(out["date"].dtype).startswith("datetime64")


def test_finished_game_without_winner_is_an_error():
    with pytest.raises(ValueError, match="bez víťaza"):
        fg.finished_games(fg.season_frame([game(1, gh=2, ga=2)]))


def test_fetch_season_asks_defunct_clubs_too(monkeypatch):
    """Zápas dvoch zaniknutých klubov je len v ich rozpisoch – bez ATL/PHX by chýbal."""
    asked = []

    def fake_club(session, team, end_year):
        asked.append(team)
        if team in ("ATL", "PHX"):
            return [game(2009020999, home="ATL", away="PHX", season=20092010)]
        if team == "TOR":
            return [game(2009020001, home="TOR", away="MTL", season=20092010)]
        return []

    monkeypatch.setattr(fg, "fetch_club", fake_club)
    df = fg.fetch_season(None, 2010, pause=0)
    assert sorted(df["game_id"]) == [2009020001, 2009020999]
    assert {"ATL", "PHX", "ARI"} <= set(asked) and len(asked) == 35


class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code, self.body = status, body

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.urls = list(responses), []

    def get(self, url, timeout):
        self.urls.append(url)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_fetch_club_url_404_and_retry(monkeypatch):
    monkeypatch.setattr(fg.time, "sleep", lambda s: None)
    s = FakeSession([FakeResponse(404)])
    assert fg.fetch_club(s, "SEA", 2015) == []
    assert s.urls == ["https://api-web.nhle.com/v1/club-schedule-season/SEA/20142015"]

    ok = FakeResponse(200, {"games": [game(1)]})
    s = FakeSession([requests.ConnectionError("x"), FakeResponse(503), ok])
    assert len(fg.fetch_club(s, "TOR", 2025)) == 1

    s = FakeSession([FakeResponse(500)] * 4)
    with pytest.raises(RuntimeError, match="TOR 2024/25"):
        fg.fetch_club(s, "TOR", 2025)


def test_labels():
    assert fg.season_id(2026) == "20252026" and fg.season_label(2026) == "2025/26"


# --- contract test na skutočnej odpovedi (scripts/probe_nhl.py) ---------------------------


@pytest.mark.skipif(not (FIX / "nhl_club_schedule.json").exists(), reason="ukážka z Macu ešte nie je")
def test_contract_club_schedule():
    data = json.loads((FIX / "nhl_club_schedule.json").read_text(encoding="utf-8"))
    df = fg.season_frame(data["games"])
    done = fg.finished_games(df)
    assert len(done) >= 2
    assert set(done["game_type"]) <= {"R", "P"}
    assert done["last_period"].isin(["REG", "OT", "SO"]).all()
    assert done["start_utc"].str.endswith("Z").all()


def test_main_checks_every_season_and_saves_finished_games(monkeypatch, tmp_path, capsys):
    def fake_season(session, year, pause=0.25):
        sid = int(fg.season_id(year))
        games = [game(year * 10 + 1, season=sid, start=f"{year - 1}-10-10T23:00:00Z", last="OT", gh=3, ga=2)]
        games.append(game(year * 10 + 2, season=sid, start=f"{year - 1}-10-11T23:00:00Z", state="FUT"))
        return fg.season_frame(games)

    monkeypatch.setattr(fg, "fetch_season", fake_season)
    monkeypatch.setattr(fg, "EXPECTED_REGULAR", {2026: 2, 2027: 2})
    out = tmp_path / "nhl.parquet"
    with pytest.raises(ValueError, match="2025/26: 1 zápasov nie je dohratých"):
        fg.main(2026, 2027, out)  # odohratá sezóna s nedohratým zápasom → nič sa neuloží
    assert not out.exists()

    monkeypatch.setattr(fg, "EXPECTED_REGULAR", {2027: 2})
    saved = fg.main(2027, 2027, out, current=2027)  # rozohratá sezóna: uložia sa len dohraté
    assert out.exists() and saved["game_id"].tolist() == [20271]
    assert pd.read_parquet(out)["last_period"].tolist() == ["OT"]
    assert "2026/27  základná časť    1  playoff   0  (predĺženie 1, nájazdy 0)" in capsys.readouterr().out
