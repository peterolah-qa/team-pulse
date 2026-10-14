"""NHL archív tipov: zamknutie do začiatku zápasu a vyhodnotenie po zápase (bez siete)."""

import json
import math
from datetime import UTC, date, datetime

import pandas as pd
import pytest

from team_pulse.nhl import archive as ar
from team_pulse.nhl import fetch_games as fg


def tip(gid, home, away, p_home, start="2026-10-13T23:00:00Z", day="2026-10-13"):
    return {
        "game_id": gid,
        "date": day,
        "tipoff_utc": start,
        "kind": "regular",
        "neutral": False,
        "p_home": p_home,
        "tip": home if p_home > 0.5 else away,
        "home": {"team": home, "elo": 1500.0, "reasons": {}},
        "away": {"team": away, "elo": 1500.0, "reasons": {}},
    }


def data(*tips):
    days = {}
    for t in tips:
        days.setdefault(t["date"], []).append(t)
    return {"generated_at": "x", "sport": "nhl", "model": "nhl-v1", "days": days}


AT = lambda h, m=0: datetime(2026, 10, 13, h, m, tzinfo=UTC)  # noqa: E731


def stored(tmp_path, day="2026-10-13"):
    return json.loads((tmp_path / f"{day}.json").read_text(encoding="utf-8"))["games"]


def test_lock_until_start_then_keep(tmp_path):
    early, late = tip("1", "DET", "NJD", 0.59), tip("2", "SJS", "BOS", 0.43, start="2026-10-14T02:00:00Z")
    assert ar.lock(data(early, late), AT(14), tmp_path) == 2
    assert stored(tmp_path)["1"]["locked_at"] == "2026-10-13T14:00:00+00:00"
    # o 23:30 prvý zápas už beží: nový tip sa neuloží, druhý sa ešte prepíše
    changed = tip("1", "DET", "NJD", 0.40), tip("2", "SJS", "BOS", 0.45, start="2026-10-14T02:00:00Z")
    assert ar.lock(data(*changed), AT(23, 30), tmp_path) == 1
    games = stored(tmp_path)
    assert games["1"]["p_home"] == 0.59 and games["2"]["p_home"] == 0.45
    assert list(games) == ["1", "2"]  # podľa začiatku zápasu


def results(*rows):
    df = pd.DataFrame(
        [
            {
                "game_id": int(g),
                "season": 2027,
                "game_type": "R",
                "date": "2026-10-13",
                "start_utc": "2026-10-13T23:00:00Z",
                "home_abbr": h,
                "away_abbr": a,
                "goals_home": gh,
                "goals_away": ga,
                "state": "OFF",
                "last_period": lp,
                "neutral": False,
            }
            for g, h, a, gh, ga, lp in rows
        ],
        columns=fg.COLUMNS,
    )
    return fg.finished_games(df)


def test_evaluate_hits_misses_and_extra_time(tmp_path):
    ar.lock(
        data(tip("1", "DET", "NJD", 0.59), tip("2", "CBJ", "FLA", 0.59), tip("3", "MTL", "BUF", 0.58)),
        AT(14),
        tmp_path,
    )
    res = results(
        ("1", "DET", "NJD", 3, 2, "OT"), ("2", "CBJ", "FLA", 1, 4, "REG")
    )  # 3. zápas ešte nie je dohratý
    df = ar.evaluate(ar.load_tips(tmp_path), res)
    assert df[["game_id", "hit", "score"]].values.tolist() == [["1", True, "2:3 pp"], ["2", False, "4:1"]]
    expected = -(math.log(0.59) + math.log(1 - 0.59)) / 2
    assert ar.log_loss(df) == pytest.approx(expected)


def test_tip_locked_after_start_does_not_count(tmp_path):
    t = {**tip("1", "DET", "NJD", 0.59), "model": "nhl-v1", "locked_at": "2026-10-13T23:05:00+00:00"}
    (tmp_path / "2026-10-13.json").write_text(json.dumps({"games": {"1": t}}), encoding="utf-8")
    assert ar.evaluate(ar.load_tips(tmp_path), results(("1", "DET", "NJD", 3, 2, "REG"))).empty


def test_report(tmp_path):
    assert "Zatiaľ žiadny dohratý zápas" in ar.to_markdown(pd.DataFrame())
    ar.lock(data(tip("1", "DET", "NJD", 0.59), tip("2", "CBJ", "FLA", 0.41)), AT(14), tmp_path)
    md = ar.to_markdown(
        ar.evaluate(
            ar.load_tips(tmp_path), results(("1", "DET", "NJD", 3, 2, "SO"), ("2", "CBJ", "FLA", 1, 4, "REG"))
        )
    )
    assert "**Spolu: 2 z 2 (100,0 %)" in md
    assert "| NJD @ DET | DET   | 59 %    | 2:3 sn" in md
    assert "| 13. 10.     |        2 |            2 | 100,0 %" in md


def test_main_writes_report(tmp_path, monkeypatch, capsys):
    ar.lock(data(tip("1", "DET", "NJD", 0.59)), AT(14), tmp_path / "a")
    cur = pd.DataFrame(
        [
            {
                "game_id": 1,
                "season": 2027,
                "game_type": "R",
                "date": "2026-10-13",
                "start_utc": "2026-10-13T23:00:00Z",
                "home_abbr": "DET",
                "away_abbr": "NJD",
                "goals_home": 1,
                "goals_away": 2,
                "state": "OFF",
                "last_period": "REG",
                "neutral": False,
            }
        ],
        columns=fg.COLUMNS,
    )
    monkeypatch.setattr(ar, "fetch_season", lambda session, year: cur)
    monkeypatch.setattr(ar, "today_et", lambda now=None: date(2026, 10, 14))
    df = ar.main(tmp_path / "a", tmp_path / "live.md")
    assert df["hit"].tolist() == [False]
    assert "tip vyšiel 0 z 1" in capsys.readouterr().out and (tmp_path / "live.md").exists()
