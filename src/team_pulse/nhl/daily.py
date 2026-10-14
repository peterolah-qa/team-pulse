"""Ranná NHL úloha z Macu: vyhodnotenie noci → tipy na dnes a zajtra → GitHub.

  1. beží len na vetve main (inak by commit skončil v cudzej vetve) a počká, kým dobehne
     ranná NBA úloha (team_pulse.daily) – obe commitujú v tom istom priečinku,
  2. stiahne novinky z GitHubu (archív NBA tipov commituje cloud),
  3. zamknuté tipy porovná s výsledkami → reports/nhl_live.md (team_pulse.nhl.archive),
  4. zamkne tipy na dnes a zajtra (dni podľa ET) → archive/nhl/predictions (team_pulse.nhl.predict),
  5. archív a report commitne a pošle na GitHub (len keď sa zmenili).

Pri chybe pošle upozornenie do macOS a chybu zapíše do logu.

Spustenie:  uv run python -m team_pulse.nhl.daily [--no-push]
Automaticky každé ráno o 10:15: bash scripts/install_nhl_daily.sh
"""

from __future__ import annotations

import argparse
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from team_pulse.daily import git_commit_if_changed, git_pull
from team_pulse.nhl import archive, predict
from team_pulse.nhl.fetch_games import today_et

DAYS = 2  # dnes a zajtra (ET): tipy na zajtra sa ráno po ďalšej noci prepočítajú
BRANCH = "main"
NBA_JOB = r"team_pulse\.daily"  # ranná NBA úloha (nezhoduje sa s team_pulse.nhl.daily)
GIT_LOCK = Path(".git/index.lock")
WAIT_S = 30
MAX_WAIT_S = 30 * 60
LOG = "~/Library/Logs/team-pulse-nhl.log"


def current_branch(cwd: Path | None = None) -> str:
    r = subprocess.run(["git", "branch", "--show-current"], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()


def nba_running() -> bool:
    return subprocess.run(["pgrep", "-f", NBA_JOB], capture_output=True).returncode == 0


def wait_for_nba(
    running: Callable[[], bool] = nba_running,
    lock: Path = GIT_LOCK,
    sleep: Callable[[float], None] = time.sleep,
    wait_s: float = WAIT_S,
    max_wait_s: float = MAX_WAIT_S,
) -> float:
    """Počká, kým nebeží NBA úloha a git nemá zámok. Vráti čakanie v sekundách, po limite chyba."""
    waited = 0.0
    while running() or lock.exists():
        if waited >= max_wait_s:
            why = "beží NBA úloha" if running() else f"existuje {lock} (po páde gitu ho treba zmazať)"
            raise RuntimeError(f"čakám {waited / 60:.0f} min a stále {why}")
        if waited == 0:
            print("Čakám, kým dobehne ranná NBA úloha / git …")
        sleep(wait_s)
        waited += wait_s
    return waited


def locked_count(data: dict, now: datetime) -> int:
    """Koľko tipov sa zamklo: zápasy, ktoré ešte nezačali (rovnaké pravidlo ako archive.lock)."""
    return sum(1 for games in data["days"].values() for g in games if archive._start(g) > now)


def commit_message(df: pd.DataFrame, locked: int, day: date) -> str:
    """„NHL 2026-10-14: noc 13. 10. tip vyšiel 8 z 16, zamknuté tipy 13“ (noc = včerajší deň ET)."""
    msg = f"NHL {day.isoformat()}:"
    night = (day - timedelta(days=1)).isoformat()
    last = df[df["date"] == night] if not df.empty else df
    if not last.empty:
        msg += f" noc {archive._day(night)} tip vyšiel {int(last['hit'].sum())} z {len(last)},"
    return msg + f" zamknuté tipy {locked}"


def notify(text: str) -> None:
    """Upozornenie v macOS (Centrum hlásení). Mimo macOS sa ticho preskočí."""
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{safe}" with title "Team Pulse NHL"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def main(push: bool, days: int = DAYS) -> bool:
    """Vráti True, ak vznikol commit."""
    print(f"=== {datetime.now():%Y-%m-%d %H:%M} NHL ===")
    branch = current_branch()
    if branch != BRANCH:
        raise RuntimeError(f"priečinok je na vetve „{branch}“, NHL úloha beží len na {BRANCH}")
    wait_for_nba()
    if push:
        try:
            git_pull()
        except RuntimeError as e:  # pokračuj, pred odoslaním sa pull skúsi znova
            print(f"Stiahnutie noviniek zlyhalo, pokračujem: {e}")

    df = archive.main()
    now = datetime.now(UTC)
    data = predict.main(days, archive=archive.ARCHIVE, now=now)
    message = commit_message(df, locked_count(data, now), today_et(now))

    if not push:
        print("--no-push: zmeny sú len lokálne, necommitovali sa")
        return False
    if git_commit_if_changed([archive.ARCHIVE, archive.REPORT], message):
        print(f"Commitnuté a poslané na GitHub: {message}")
        return True
    print("Nič sa nezmenilo, nič sa necommitovalo")
    return False


def run(push: bool) -> None:
    try:
        main(push)
    except Exception as e:
        notify(f"Ranná úloha zlyhala: {str(e)[:120]} – log {LOG}")
        raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true", help="necommitovať a neposielať na GitHub")
    run(push=not ap.parse_args().no_push)
