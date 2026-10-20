"""Vyhodnotenie brán G2: kritériá z docs/gate-G2.md a docs/gate-nhl-G2.md (bez siete).

Reporty v testoch píše skutočný kód prevádzky (team_pulse.archive, team_pulse.nhl.archive),
vyhodnotenie ich musí nezávisle potvrdiť a upravený report musí odhaliť.
"""

import json
import os
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from team_pulse import archive as nba_archive
from team_pulse import gate_g2 as g2
from team_pulse.nhl import archive as nhl_archive
from team_pulse.nhl import fetch_games as nhl_fetch

BACKTEST = {"accuracy": 0.673, "log_loss": 0.5996, "brier": 0.2068, "test_seasons": "2023/24 – 2025/26"}


# --- NBA ---------------------------------------------------------------------------------------------

NBA_GAMES = [  # game_id, deň ET, začiatok UTC, domáci, hostia, šanca domácich, body domácich, hostí
    ("0022600001", "2026-10-20", "2026-10-20 19:00:00+00:00", "DET", "BOS", 0.40, 101, 110),
    ("0022600002", "2026-10-20", "2026-10-20 23:00:00+00:00", "NYK", "PHI", 0.70, 120, 100),
    ("0022600003", "2026-10-21", "2026-10-21 23:00:00+00:00", "ORL", "ATL", 0.60, 99, 104),
]


def nba_state(games=NBA_GAMES):
    base = {"season": 2027, "kind": "regular", "neutral": False, "arena_city": ""}
    sched = [{**base, "game_id": gid, "date": day, "tipoff_utc": tip, "home": h, "away": a}
             for gid, day, tip, h, a, *_ in games]  # fmt: skip
    sched.append({"game_id": "0012600099", "date": "2026-10-16", "tipoff_utc": "2026-10-16 23:00:00+00:00",
                  "season": 2027, "kind": "preseason", "home": "DET", "away": "BOS", "neutral": False,
                  "arena_city": ""})  # fmt: skip
    return {"schedule": sched, "last_result": "2026-10-21"}


def write_nba_archive(tmp_path, games=NBA_GAMES, lock_offset="-1h"):
    pred, res = tmp_path / "predictions", tmp_path / "results"
    pred.mkdir(), res.mkdir()
    for day in sorted({g[1] for g in games}):
        day_games = [g for g in games if g[1] == day]
        tips = {gid: {"game_id": gid, "kind": "regular", "tipoff_utc": tip,
                      "locked_at": (pd.Timestamp(tip) + pd.Timedelta(lock_offset)).isoformat(),
                      "p_home": p, "home": {"team": h}, "away": {"team": a}}
                for gid, _, tip, h, a, p, *_ in day_games}  # fmt: skip
        (pred / f"{day}.json").write_text(json.dumps({"date": day, "games": tips}))
        results = {gid: {"pts_home": ph, "pts_away": pa} for gid, *_, ph, pa in day_games}
        (res / f"{day}.json").write_text(json.dumps({"date": day, "games": results}))
    return pred, res


def nba_report(pred, res):
    return nba_archive.report(nba_archive.load_archive(pred, res), BACKTEST)


def morning_states(*days, hour="10:05"):
    """Ranné commity stavu: (deň, last_result) → [(čas UTC, last_result)]."""
    return [(pd.Timestamp(f"{d} {hour}", tz="Europe/Bratislava").tz_convert("UTC"), lr) for d, lr in days]


GOOD_HISTORY = morning_states(
    ("2026-10-20", "2026-06-13"), ("2026-10-21", "2026-10-20"), ("2026-10-22", "2026-10-21")
)


def nba_eval(tmp_path, asof=date(2026, 10, 22), history=GOOD_HISTORY, report=None, **kw):
    pred, res = write_nba_archive(tmp_path, **kw)
    tips, results = g2.nba_archive(pred, res)
    text = report if report is not None else nba_report(pred, res)
    gate = g2.Gate("nba", date(2026, 10, 20), date(2026, 10, 21), 0.6739, 0.5873, True, "docs/gate-G2.md",
                   Path("reports/live.md"))  # fmt: skip
    return g2.evaluate_nba(nba_state(), tips, results, text, history, asof, gate)


def by_name(checks):
    return {c.name.split(".")[0]: c for c in checks}


def test_nba_all_criteria_pass_and_report_matches(tmp_path):
    checks, period, final = nba_eval(tmp_path)
    assert final and all(c.ok for c in checks), [(c.name, c.problems) for c in checks]
    assert len(period) == 3 and int(period["hit"].sum()) == 2  # BOS (tip hostia) a NYK áno, ORL doma prehral
    c = by_name(checks)
    assert set(c) == {"1", "2", "3", "4", "5", "6"}


def test_nba_tampered_report_is_detected(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    pred, res = write_nba_archive(a)
    text = nba_report(pred, res).replace("| Zápasy | 3 |", "| Zápasy | 4 |")
    checks, _, _ = nba_eval(b, report=text)
    c3 = by_name(checks)["3"]
    assert not c3.ok and "Zápasy: prepočet 3, report 4" in c3.problems[0]


def test_nba_tip_locked_after_start_fails(tmp_path):
    checks, _, _ = nba_eval(tmp_path, lock_offset="+1min")
    c1 = by_name(checks)["1"]
    assert not c1.ok and len(c1.problems) == 3 and "zamknuté po začiatku" in c1.problems[0]


def test_nba_missing_tip_and_result(tmp_path):
    pred, res = write_nba_archive(tmp_path, games=NBA_GAMES[:2])  # zápas 21. 10. v archíve chýba
    tips, results = g2.nba_archive(pred, res)
    gate = g2.Gate("nba", date(2026, 10, 20), date(2026, 10, 21), 0.6739, 0.5873, True, "", Path(""))
    checks, _, _ = g2.evaluate_nba(nba_state(), tips, results, nba_report(pred, res), GOOD_HISTORY,
                                   date(2026, 10, 22), gate)  # fmt: skip
    c = by_name(checks)
    assert not c["1"].ok and "bez tipu: 2026-10-21 ATL @ ORL" in c["1"].problems
    assert not c["2"].ok and "bez výsledku: 2026-10-21 ATL @ ORL" in c["2"].problems


def test_nba_state_deadline():
    sched = g2.nba_schedule(nba_state(), date(2026, 10, 20), date(2026, 10, 21))
    late = morning_states(("2026-10-21", "2026-10-20")) + morning_states(
        ("2026-10-22", "2026-10-21"), hour="12:01"
    )
    c = g2.nba_state_check(late, sched, date(2026, 10, 20), date(2026, 10, 21))
    assert not c.ok and c.problems == ["22. 10. do 12:00: stav s výsledkami do 2026-10-20, chýba 2026-10-21"]
    assert g2.nba_state_check(GOOD_HISTORY, sched, date(2026, 10, 20), date(2026, 10, 21)).ok


def test_nba_state_not_needed_after_day_without_games():
    sched = g2.nba_schedule(
        nba_state(NBA_GAMES[2:]), date(2026, 10, 20), date(2026, 10, 21)
    )  # 20. 10. bez zápasu
    c = g2.nba_state_check(
        morning_states(("2026-10-22", "2026-10-21")), sched, date(2026, 10, 20), date(2026, 10, 21)
    )
    assert c.ok and c.detail == "1 z 1 rán"


def test_nba_model_limits(tmp_path):
    bad = [
        (gid, d, tip, h, a, 0.95 if p < 0.5 else 0.05, ph, pa) for gid, d, tip, h, a, p, ph, pa in NBA_GAMES
    ]
    checks, _, _ = nba_eval(tmp_path, games=bad)
    c = by_name(checks)
    assert not c["5"].ok and not c["6"].ok  # sebavedomo zle → nad hranicou aj horší než baseline


def test_interim_before_end(tmp_path):
    checks, period, final = nba_eval(tmp_path, asof=date(2026, 10, 21))
    assert not final and len(period) == 2  # hodnotí sa len 20. 10.
    md = g2.to_markdown(g2.NBA, checks, period, date(2026, 10, 21), final)
    assert "predbežne" in md and "obdobie ešte beží" in md


def test_state_history_from_git(tmp_path):
    def git(*args, when=None):
        env = {**os.environ, "GIT_AUTHOR_DATE": when or "", "GIT_COMMITTER_DATE": when or ""}
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, env=env)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "T")
    (tmp_path / "state").mkdir()
    for when, lr in (
        ("2026-10-21T10:05:00+02:00", "2026-10-20"),
        ("2026-10-22T10:07:00+02:00", "2026-10-21"),
    ):
        (tmp_path / "state" / "state.json").write_text(json.dumps({"last_result": lr}))
        git("add", ".")
        git("commit", "-q", "-m", "stav", when=when)
    hist = g2.state_history(cwd=tmp_path)
    assert hist == [
        (pd.Timestamp("2026-10-21T08:05:00Z"), "2026-10-20"),
        (pd.Timestamp("2026-10-22T08:07:00Z"), "2026-10-21"),
    ]


# --- NHL ---------------------------------------------------------------------------------------------

NHL_GAMES = [  # game_id, deň ET, začiatok UTC, domáci, hostia, šanca domácich, góly domácich, hostí, stav
    (2026020001, "2026-10-13", "2026-10-13T23:00:00Z", "DET", "NJD", 0.59, 4, 5, "OFF"),
    (2026020002, "2026-10-13", "2026-10-14T02:00:00Z", "UTA", "TOR", 0.59, 5, 4, "OFF"),
    (2026020003, "2026-10-14", "2026-10-14T23:30:00Z", "WSH", "MTL", 0.52, 5, 4, "OFF"),
]
NHL_GATE = g2.Gate("nhl", date(2026, 10, 13), date(2026, 10, 14), 0.7101, 0.5434, False, "", Path(""))


def nhl_season(games=NHL_GAMES):
    base = {"season": 2027, "game_type": "R", "last_period": "REG", "neutral": False}
    rows = [{**base, "game_id": gid, "date": d, "start_utc": tip, "home_abbr": h, "away_abbr": a,
             "goals_home": gh, "goals_away": ga, "state": st}
            for gid, d, tip, h, a, _, gh, ga, st in games]  # fmt: skip
    return pd.DataFrame(rows, columns=nhl_fetch.COLUMNS)


def write_nhl_tips(tmp_path, games=NHL_GAMES):
    for day in sorted({g[1] for g in games}):
        tips = {str(gid): {"game_id": str(gid), "date": d, "tipoff_utc": tip, "p_home": p,
                           "tip": h if p > 0.5 else a, "home": {"team": h}, "away": {"team": a},
                           "locked_at": (pd.Timestamp(tip) - pd.Timedelta("7h")).isoformat()}
                for gid, d, tip, h, a, p, *_ in games if d == day}  # fmt: skip
        (tmp_path / f"{day}.json").write_text(json.dumps({"games": tips}))
    return tmp_path


def nhl_report(archive_dir, season):
    done = nhl_fetch.finished_games(season)
    return nhl_archive.to_markdown(nhl_archive.evaluate(nhl_archive.load_tips(archive_dir), done))


def test_nhl_all_criteria_pass(tmp_path):
    season = nhl_season()
    tips = g2.nhl_tips(write_nhl_tips(tmp_path))
    checks, period, final = g2.evaluate_nhl(
        season, tips, nhl_report(tmp_path, season), date(2026, 10, 15), NHL_GATE
    )
    assert final and all(c.ok for c in checks), [(c.name, c.problems) for c in checks]
    assert len(period) == 3 and int(period["hit"].sum()) == 2
    assert {c.name.split(".")[0] for c in checks} == {"1", "2", "3", "4"}


def test_nhl_unfinished_game_and_tampered_report(tmp_path):
    games = [*NHL_GAMES[:2], (*NHL_GAMES[2][:6], None, None, "PPD")]  # zápas 14. 10. odložený
    season = nhl_season(games)
    tips = g2.nhl_tips(write_nhl_tips(tmp_path, games))
    report = nhl_report(tmp_path, season).replace("**Spolu: 1 z 2", "**Spolu: 2 z 2")
    checks, _, _ = g2.evaluate_nhl(season, tips, report, date(2026, 10, 15), NHL_GATE)
    c = by_name(checks)
    assert not c["2"].ok and any(
        "nedohraný alebo odložený: 2026-10-14 MTL @ WSH" in p for p in c["2"].problems
    )
    assert not c["3"].ok and "Spolu" in c["3"].problems[0]


def test_nhl_missing_tip_and_relocated_club(tmp_path):
    games = [*NHL_GAMES, (2026020004, "2026-10-14", "2026-10-15T02:00:00Z", "ARI", "LAK", 0.5, 2, 3, "OFF")]
    season = nhl_season(games)
    tips = g2.nhl_tips(write_nhl_tips(tmp_path))  # tip na štvrtý zápas chýba
    checks, _, _ = g2.evaluate_nhl(season, tips, nhl_report(tmp_path, season), date(2026, 10, 15), NHL_GATE)
    c1 = by_name(checks)["1"]
    assert not c1.ok and c1.problems == ["bez tipu: 2026-10-14 LAK @ UTA"]  # ARI → UTA ako v appke


def test_nhl_model_limit():
    df = g2.scored(pd.DataFrame({"p_home": [0.9, 0.9], "home_won": [False, False]}), 0.5434)
    (c,) = g2.model_checks(df, NHL_GATE, 4)
    assert not c.ok and c.name == "4. Log loss ≤ 0,7101"


# --- reporty z repa (kontrakt formátu) ---------------------------------------------------------------


def test_parsers_read_current_reports():
    total, days = g2.parse_nhl_report(Path("reports/nhl_live.md").read_text(encoding="utf-8"))
    if total is not None:
        assert sum(n for n, _ in days.values()) == total[1] and sum(h for _, h in days.values()) == total[0]
    text = Path("reports/live.md").read_text(encoding="utf-8")
    if "| Zápasy |" in text:  # riadok základnej časti je tam od 20. 10., tabuľka až s výsledkami
        assert set(g2.parse_nba_report(text)) == {"Zápasy", "Presnosť", "Log loss", "Brier"}
    else:
        assert g2.parse_nba_report(text) is None


def test_gates_match_documents():
    nba_doc = Path(g2.NBA.doc).read_text(encoding="utf-8")
    nhl_doc = Path(g2.NHL.doc).read_text(encoding="utf-8")
    assert "**0,6739**" in nba_doc and "20. 10. – 2. 11. 2026" in nba_doc and "58,7 %" in nba_doc
    assert "**0,7101**" in nhl_doc and "13. 10. – 26. 10. 2026" in nhl_doc and "54,3 %" in nhl_doc
    assert (g2.NBA.ll_limit, g2.NHL.ll_limit) == (0.6739, 0.7101)
    assert (round(g2.NBA.home_rate * 100, 1), round(g2.NHL.home_rate * 100, 1)) == (58.7, 54.3)


@pytest.mark.parametrize(("asof", "last", "final"), [
    (date(2026, 10, 20), date(2026, 10, 19), False),
    (date(2026, 10, 27), date(2026, 10, 26), True),
    (date(2026, 11, 5), date(2026, 10, 26), True),
])  # fmt: skip
def test_days_done(asof, last, final):
    assert g2.days_done(g2.NHL, asof) == (last, final)
