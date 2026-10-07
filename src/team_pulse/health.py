"""Kontrola zdravia: živé zdroje a čerstvosť stavu. Pri probléme skončí chybou → GitHub pošle e-mail.

Kontroluje:
  * ESPN zranenia: dostupné, známe teamy a typy zranení, nie staršie ako 12 h
  * ESPN scoreboard: dostupný a čitateľný
  * state/state.json: ak sa odohrali zápasy (aj príprava) a stav o nich nevie
    → denná aktualizácia z Macu neprebehla

Spustenie:  uv run python -m team_pulse.health
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import pandas as pd

from team_pulse.live.injuries import STATUS, fetch_injuries, parse_injuries
from team_pulse.live.scoreboard import fetch_scoreboard, parse_scoreboard
from team_pulse.state import STATE, load_state, schedule_frame

MAX_INJURY_AGE_H = 12
RESULT_LAG_DAYS = 2  # výsledky z USA prídu s posunom; o 2 dni už musia byť v stave


def check_injuries(data: dict, now: pd.Timestamp) -> list[str]:
    problems = []
    try:
        df = parse_injuries(data)
    except KeyError as e:
        return [f"ESPN zranenia: {e}"]
    if df.empty:
        problems.append("ESPN zranenia: prázdny zoznam")
    types = {i.get("type", {}).get("name") for t in data.get("injuries", []) for i in t.get("injuries", [])}
    unknown = types - set(STATUS)
    if unknown:
        problems.append(f"ESPN zranenia: neznámy typ {sorted(unknown)} – doplniť do live/injuries.py")
    ts = data.get("timestamp")
    if ts:
        age = (now - pd.Timestamp(ts)).total_seconds() / 3600
        if age > MAX_INJURY_AGE_H:
            problems.append(f"ESPN zranenia: dáta sú {age:.0f} h staré")
    return problems


def check_scoreboard(data: dict) -> list[str]:
    try:
        parse_scoreboard(data)
    except (KeyError, IndexError) as e:
        return [f"ESPN scoreboard: nečitateľný formát ({e})"]
    return []


def check_state(state: dict, today: pd.Timestamp) -> list[str]:
    sched = schedule_frame(state)
    if sched.empty:
        return []
    cutoff = today.normalize() - pd.Timedelta(days=RESULT_LAG_DAYS)
    played = sched[sched["date"] <= cutoff]
    if played.empty:
        return []
    expected = played["date"].max()
    # výsledky prípravy nie sú v histórii (last_result), ale Mac ich dáva do state["results"]
    last = max(
        pd.Timestamp(d) for d in [state["last_result"], *(r["date"] for r in state.get("results", []))]
    )
    if expected > last:
        return [
            f"Stav: posledný výsledok {last.date()}, ale zápasy sa hrali aj {expected.date()} "
            "– denná aktualizácia z Macu neprebehla (Mac vypnutý? pozri ~/Library/Logs/team-pulse-daily.log)"
        ]
    return []


def main() -> int:
    now = pd.Timestamp(datetime.now(UTC))
    problems: list[str] = []
    try:
        problems += check_injuries(fetch_injuries(), now)
    except Exception as e:  # zdroj nedostupný
        problems.append(f"ESPN zranenia nedostupné: {e.__class__.__name__}: {e}")
    try:
        problems += check_scoreboard(fetch_scoreboard(now.strftime("%Y%m%d")))
    except Exception as e:
        problems.append(f"ESPN scoreboard nedostupný: {e.__class__.__name__}: {e}")
    try:
        problems += check_state(load_state(STATE), now.tz_localize(None))
    except Exception as e:
        problems.append(f"Stav nečitateľný: {e.__class__.__name__}: {e}")

    if problems:
        print("✗ Problémy:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("✓ Zdroje aj stav sú v poriadku")
    return 0


if __name__ == "__main__":
    sys.exit(main())
