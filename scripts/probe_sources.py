"""Prieskum živých zdrojov: stiahne ukážky odpovedí a uloží ich.

  data/probe/*.json       celé odpovede (necommitujú sa)
  tests/fixtures/*.json   skrátené ukážky pre contract testy (commitujú sa)

Zistenia z prieskumu (27. 9. 2026):
  * ESPN blokuje (403) požiadavky, ktoré sa vydávajú za prehliadač → posielame predvolené hlavičky
  * cdn.nba.com vracia 403 na všetko → rozpis berieme cez nba_api (stats.nba.com)

Spustenie:  uv run python scripts/probe_sources.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests

OPENING_NIGHT = "20261020"  # približne; ak nie je zápas, scoreboard vráti prázdny zoznam
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

RAW = Path("data/probe")
FIXTURES = Path("tests/fixtures")


def trim(obj: object, n: int = 3) -> object:
    """Každý zoznam skráti na prvých n prvkov (rekurzívne)."""
    if isinstance(obj, list):
        return [trim(x, n) for x in obj[:n]]
    if isinstance(obj, dict):
        return {k: trim(v, n) for k, v in obj.items()}
    return obj


def espn(path: str) -> dict:
    r = requests.get(f"{ESPN}/{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def nba_schedule() -> dict:
    from nba_api.stats.endpoints import scheduleleaguev2

    return scheduleleaguev2.ScheduleLeagueV2(league_id="00", season="2026-27", timeout=60).get_dict()


def summary(name: str, data: dict) -> str:
    if name == "espn_injuries":
        teams = data.get("injuries", [])
        n = sum(len(t.get("injuries", [])) for t in teams)
        return f"{len(teams)} teamov, {n} zranení"
    if name == "espn_scoreboard":
        return f"{len(data.get('events', []))} zápasov v deň {OPENING_NIGHT}"
    if name == "nba_schedule":
        ls = data.get("leagueSchedule", {})
        dates = ls.get("gameDates", [])
        games = sum(len(d.get("games", [])) for d in dates)
        first = dates[0].get("gameDate", "?") if dates else "?"
        last = dates[-1].get("gameDate", "?") if dates else "?"
        return f"sezóna {ls.get('seasonYear')}, {len(dates)} hracích dní, {games} zápasov, {first} – {last}"
    return ""


SOURCES = {
    "espn_injuries": lambda: espn("injuries"),
    "espn_scoreboard": lambda: espn(f"scoreboard?dates={OPENING_NIGHT}"),
    "nba_schedule": nba_schedule,
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    print(f"Prieskum {date.today()}\n")
    for name, fetch in SOURCES.items():
        try:
            data = fetch()
        except Exception as e:  # zdroj nedostupný alebo nevracia JSON
            print(f"✗ {name:<16} {e.__class__.__name__}: {e}")
            continue
        raw = json.dumps(data, ensure_ascii=False, indent=1)
        (RAW / f"{name}.json").write_text(raw, encoding="utf-8")
        (FIXTURES / f"{name}.json").write_text(
            json.dumps(trim(data), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"✓ {name:<16} {len(raw) / 1024:>7.0f} kB   {summary(name, data)}")
    print(f"\nUkážky: {FIXTURES}/")


if __name__ == "__main__":
    main()
