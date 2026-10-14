"""Ranná NHL úloha: len na main, čaká na NBA úlohu, poradie krokov, commit a upozornenie (bez siete)."""

import subprocess
from datetime import UTC, date, datetime

import pandas as pd
import pytest

from team_pulse.nhl import archive
from team_pulse.nhl import daily as nd

NOW = datetime(2026, 10, 14, 8, 15, tzinfo=UTC)  # 10:15 u nás, 4:15 ET


def evaluated(rows):
    return pd.DataFrame(rows, columns=["date", "game_id", "hit"])


def predictions():
    return {"days": {
        "2026-10-13": [{"game_id": "1", "tipoff_utc": "2026-10-13T23:00:00Z"}],  # už sa hralo
        "2026-10-14": [{"game_id": "2", "tipoff_utc": "2026-10-14T23:30:00Z"}],
        "2026-10-15": [{"game_id": "3", "tipoff_utc": "2026-10-15T23:00:00Z"},
                       {"game_id": "4", "tipoff_utc": "2026-10-16T02:00:00Z"}],
    }}  # fmt: skip


def test_wait_for_nba_waits_until_done(tmp_path):
    states = iter([True, True, False])
    slept = []
    waited = nd.wait_for_nba(lambda: next(states), tmp_path / "index.lock", slept.append, wait_s=30)
    assert waited == 60 and slept == [30, 30]


def test_wait_for_nba_waits_for_git_lock_and_gives_up(tmp_path):
    lock = tmp_path / "index.lock"
    lock.write_text("")
    with pytest.raises(RuntimeError, match="index.lock"):
        nd.wait_for_nba(lambda: False, lock, lambda s: None, wait_s=30, max_wait_s=90)


def test_wait_for_nba_no_wait_when_free(tmp_path):
    assert nd.wait_for_nba(lambda: False, tmp_path / "index.lock", lambda s: pytest.fail("čakal")) == 0


def test_nba_pattern_does_not_match_nhl_job():
    import re

    assert re.search(nd.NBA_JOB, "uv run python -m team_pulse.daily")
    assert not re.search(nd.NBA_JOB, "uv run python -m team_pulse.nhl.daily")


def test_locked_count_only_games_not_started():
    assert nd.locked_count(predictions(), NOW) == 3


def test_commit_message_last_night_only():
    df = evaluated([("2026-10-12", "a", True), ("2026-10-13", "b", True), ("2026-10-13", "c", False)])
    day = date(2026, 10, 14)
    assert nd.commit_message(df, 13, day) == "NHL 2026-10-14: noc 13. 10. tip vyšiel 1 z 2, zamknuté tipy 13"
    # včera (15. 10.) sa nehralo → bez noci
    assert nd.commit_message(df, 5, date(2026, 10, 16)) == "NHL 2026-10-16: zamknuté tipy 5"
    assert nd.commit_message(pd.DataFrame(), 0, day) == "NHL 2026-10-14: zamknuté tipy 0"


@pytest.fixture
def steps(monkeypatch):
    """Nahradí sieť a git: zapisuje poradie krokov."""
    calls = []
    monkeypatch.setattr(nd, "current_branch", lambda: "main")
    monkeypatch.setattr(nd, "wait_for_nba", lambda: calls.append("wait"))
    monkeypatch.setattr(nd, "git_pull", lambda: calls.append("pull"))
    night = evaluated([("2026-10-13", "b", True)])
    monkeypatch.setattr(nd.archive, "main", lambda: calls.append("archive") or night)

    def fake_predict(days, archive=None, now=None):
        calls.append(("predict", days, archive))
        return predictions()

    def fake_commit(paths, message):
        calls.append(("commit", [str(p) for p in paths], message))
        return True

    monkeypatch.setattr(nd.predict, "main", fake_predict)
    monkeypatch.setattr(nd, "git_commit_if_changed", fake_commit)
    fixed = type("FixedNow", (datetime,), {"now": staticmethod(lambda tz=None: NOW)})
    monkeypatch.setattr(nd, "datetime", fixed)
    return calls


def test_main_order_and_commit(steps):
    assert nd.main(push=True)
    assert steps[:4] == ["wait", "pull", "archive", ("predict", 2, archive.ARCHIVE)]
    _, paths, message = steps[4]
    assert paths == ["archive/nhl/predictions", "reports/nhl_live.md"]
    assert message == "NHL 2026-10-14: noc 13. 10. tip vyšiel 1 z 1, zamknuté tipy 3"


def test_main_no_push_does_not_touch_git(steps):
    assert not nd.main(push=False)
    assert "pull" not in steps and not any(isinstance(s, tuple) and s[0] == "commit" for s in steps)


def test_main_refuses_other_branch(steps, monkeypatch):
    monkeypatch.setattr(nd, "current_branch", lambda: "feature")
    with pytest.raises(RuntimeError, match="feature"):
        nd.main(push=True)
    assert steps == []


def test_run_notifies_and_fails(monkeypatch):
    sent = []
    monkeypatch.setattr(nd, "notify", sent.append)
    monkeypatch.setattr(nd, "main", lambda push: (_ for _ in ()).throw(RuntimeError("API NHL nedostupné")))
    with pytest.raises(RuntimeError):
        nd.run(push=True)
    assert "API NHL nedostupné" in sent[0]


def test_notify_escapes_quotes(monkeypatch):
    seen = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: seen.append(args))
    nd.notify('git: "main" \\ zlyhal')
    assert seen[0][2] == 'display notification "git: \\"main\\" \\\\ zlyhal" with title "Team Pulse NHL"'


def test_current_branch_in_real_repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    assert nd.current_branch(tmp_path) == "main"
