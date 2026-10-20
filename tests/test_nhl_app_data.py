"""NHL pre appku: skladanie tipov z archívu a výsledkov z API NHL (bez siete)."""

import json
from datetime import UTC, datetime
from pathlib import Path

from team_pulse.nhl import app_data as ad

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 14, 15, 0, tzinfo=UTC)  # 14. 10. ET


def tip(
    gid, day, start, home="DET", away="BUF", p_home=0.6, locked="2026-10-13T14:55:00+00:00", reasons=None
):
    return {
        "game_id": gid, "date": day, "tipoff_utc": start, "kind": "regular", "neutral": False,
        "p_home": p_home, "tip": home if p_home > 0.5 else away, "model": "nhl-v1", "locked_at": locked,
        "home": {"team": home, "elo": 1520.0, "reasons": reasons or {}},
        "away": {"team": away, "elo": 1490.0, "reasons": {}},
    }  # fmt: skip


def result(gid, day, start, home="DET", away="BUF", gh=4, ga=3, period="OT"):
    return {
        "game_id": gid, "date": day, "tipoff_utc": start, "kind": "regular", "home": home, "away": away,
        "goals_home": gh, "goals_away": ga, "last_period": period,
    }  # fmt: skip


def score_game(gid=2026020090, state="OFF", game_type=2, home=4, away=3):
    return {
        "id": gid, "gameType": game_type, "gameDate": "2026-10-13", "startTimeUTC": "2026-10-13T22:00:00Z",
        "gameState": state, "homeTeam": {"abbrev": "DET", "score": home},
        "awayTeam": {"abbrev": "NJD", "score": away},
        "gameOutcome": {"lastPeriodType": "OT"},
    }  # fmt: skip


def test_parse_result_finished_regular_game():
    r = ad.parse_result(score_game())
    assert r == {
        "game_id": "2026020090", "date": "2026-10-13", "tipoff_utc": "2026-10-13T22:00:00Z",
        "kind": "regular", "home": "DET", "away": "NJD", "goals_home": 4, "goals_away": 3,
        "last_period": "OT",
    }  # fmt: skip


def test_parse_result_skips_unfinished_and_preseason():
    assert ad.parse_result(score_game(state="LIVE")) is None
    assert ad.parse_result(score_game(state="FUT", home=None, away=None)) is None
    assert ad.parse_result(score_game(game_type=1)) is None


def test_build_drops_finished_and_old_games():
    tips = [
        tip("1", "2026-10-12", "2026-10-12T23:00:00Z"),  # predvčerom (ET) – už nie
        tip("2", "2026-10-13", "2026-10-13T23:00:00Z"),  # včera, dohraný → vo výsledkoch
        tip("3", "2026-10-13", "2026-10-14T02:00:00Z"),  # včera, výsledok ešte nie je
        tip("4", "2026-10-14", "2026-10-14T23:00:00Z"),
    ]
    data = ad.build(tips, [result("2", "2026-10-13", "2026-10-13T23:00:00Z")], NOW, "nhl-v1")
    assert {d: [g["game_id"] for g in gs] for d, gs in data["days"].items()} == {
        "2026-10-13": ["3"],
        "2026-10-14": ["4"],
    }
    assert data["sport"] == "nhl" and data["beta"] is True
    assert [r["game_id"] for r in data["results"]] == ["2"]
    assert data["results"][0]["p_home"] == 0.6


def test_result_without_tip_locked_before_start_has_no_tip():
    late = tip("5", "2026-10-13", "2026-10-13T23:00:00Z", locked="2026-10-13T23:05:00+00:00")
    res = [
        result("5", "2026-10-13", "2026-10-13T23:00:00Z"),
        result("6", "2026-10-13", "2026-10-13T23:30:00Z"),
    ]
    data = ad.build([late], res, NOW, "nhl-v1")
    assert [r["p_home"] for r in data["results"]] == [None, None]


def test_reasons_sorted_by_impact_and_rounded():
    t = tip(
        "7", "2026-10-14", "2026-10-14T23:00:00Z", reasons={"3. zápas za 4 dni": -15.8, "back-to-back": -42.5}
    )
    g = ad.build([t], [], NOW, "nhl-v1")["days"]["2026-10-14"][0]
    assert g["home"]["reasons"] == [["back-to-back", -42], ["3. zápas za 4 dni", -16]]


def test_teams_use_latest_elo_strongest_first():
    a = tip("8", "2026-10-13", "2026-10-13T23:00:00Z", home="DET", away="BUF")
    b = {**tip("9", "2026-10-14", "2026-10-14T23:00:00Z", home="BUF", away="TOR")}
    b["home"] = {**b["home"], "elo": 1600.0}
    assert [(t["team"], t["elo"], t["as_of"]) for t in ad.teams([b, a])] == [
        ("BUF", 1600.0, "2026-10-14"), ("DET", 1520.0, "2026-10-13"), ("TOR", 1490.0, "2026-10-14"),
    ]  # fmt: skip


def test_model_info_has_app_shape():
    m = ad.model_info()
    assert m["test_metrics"]["test_seasons"] == ad.TEST_SEASONS
    assert {"version", "train_seasons", "n_games", "calibration", "versions", "elo_weights"} <= m.keys()


def test_main_writes_files_even_when_api_fails(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "2026-10-14.json").write_text(
        json.dumps({"games": {"4": tip("4", "2026-10-14", "2026-10-14T23:00:00Z")}}), encoding="utf-8"
    )

    def down(*_a, **_k):
        raise ad.requests.ConnectionError("bez siete")

    monkeypatch.setattr(ad, "fetch_results", down)
    monkeypatch.setattr(ad.inj, "fetch", down)
    monkeypatch.setattr(ad.cx, "load_cache", lambda *_a, **_k: {})
    monkeypatch.setattr(ad.cx, "fetch_club", down)
    monkeypatch.setattr(ad.cx, "fetch_summary", down)
    data = ad.main(out=tmp_path / "out", archive=archive, now=NOW)
    assert data["results"] == [] and list(data["days"]) == ["2026-10-14"]
    assert data["injuries"] is None and data["injuries_timestamp"] is None
    ctx = data["days"]["2026-10-14"][0]["ctx"]  # bez rozpisov aspoň rozpad tipu z archívu
    assert set(ctx) == {"edge", "trend"} and ctx["edge"]["verified"] is False
    assert data["stats_at"] is None
    assert json.loads((tmp_path / "out" / "model.json").read_text(encoding="utf-8"))["version"] == "nhl-v1"


def test_main_adds_injuries_without_touching_tips(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    t4 = tip("4", "2026-10-14", "2026-10-14T23:00:00Z")
    (archive / "2026-10-14.json").write_text(json.dumps({"games": {"4": t4}}), encoding="utf-8")
    raw = json.loads((FIXTURES / "espn_nhl_injuries.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(ad, "fetch_results", lambda *_a, **_k: [])
    monkeypatch.setattr(ad.inj, "fetch", lambda *_a, **_k: raw)
    monkeypatch.setattr(ad.cx, "load_cache", lambda *_a, **_k: {})
    monkeypatch.setattr(ad.cx, "fetch_club", lambda *_a, **_k: [])
    monkeypatch.setattr(ad.cx, "fetch_summary", lambda *_a, **_k: {"data": []})
    data = ad.main(out=tmp_path / "out", archive=archive, now=NOW)
    assert data["injuries_timestamp"] == raw["timestamp"]
    assert set(data["injuries"]) == {"ANA", "BUF", "CGY"}
    assert data["days"]["2026-10-14"][0]["p_home"] == t4["p_home"]  # tip sa nemení
    saved = json.loads((tmp_path / "out" / "predictions.json").read_text(encoding="utf-8"))
    assert saved["injuries"] == data["injuries"]
