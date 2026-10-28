"""Sonda: zdroje pre tenis (ATP a WTA). Spustiť raz z Macu, výstup vložiť do chatu.

Overí a vypíše (nič neukladá, surové dáta sa necommitujú):
  1. pôvodné repozitáre Jeffa Sackmanna (tennis_atp, tennis_wta): sú ešte dostupné?
  2. ESPN tenis (ATP, WTA): dnešný a zajtrajší deň a deň z medzery (júl 2026): turnaje, zápasy dvojhry,
     stavy, či majú budúce zápasy oboch hráčov a čas začiatku; tvar údajov pre sťahovač.

Archívnu kópiu Aneeshers/tennis-sackmann-archive (commit 8373358, 25. 6. 2026) som overil priamo 28. 10.
(docs/tennis.md), sonda ju preto nesťahuje.

Spustenie (z Macu):  uv run python scripts/probe_tennis.py
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta

import requests

SACKMANN = ["JeffSackmann/tennis_atp", "JeffSackmann/tennis_wta"]
GH_API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/tennis/{tour}/scoreboard"
GAP_DAY = "20260715"  # deň z medzery po snímke archívu (jún 2026)
HEADERS = {"User-Agent": "team-pulse probe (non-commercial; github.com/peterolah-qa/team-pulse)"}  # len ASCII

session = requests.Session()
session.headers.update(HEADERS)


def get(url: str, **params: object) -> requests.Response:
    r = session.get(url, params=params or None, timeout=60)
    time.sleep(0.3)
    return r


def sackmann() -> None:
    print("== 1. Pôvodné repozitáre Jeffa Sackmanna")
    for repo in SACKMANN:
        r = get(f"{GH_API}/repos/{repo}")
        raw = session.head(f"{RAW}/{repo}/master/{repo.split('_')[-1]}_matches_2024.csv", timeout=30)
        print(f"{repo}: API HTTP {r.status_code}, súbor 2024 HTTP {raw.status_code}")


def name(x: dict) -> str | None:
    return (x.get("athlete") or {}).get("displayName")


def espn_day(tour: str, day: str) -> None:
    r = get(ESPN.format(tour=tour), dates=day)
    print(f"\n{tour.upper()} {day}: HTTP {r.status_code}")
    if not r.ok:
        return
    events = r.json().get("events", [])
    for ev in events:
        groups = ev.get("groupings") or [
            {"grouping": {"slug": "-"}, "competitions": ev.get("competitions", [])}
        ]
        for g in groups:
            slug = (g.get("grouping") or {}).get("slug", "-")
            comps = g.get("competitions") or []
            states = Counter((c.get("status") or {}).get("type", {}).get("name") for c in comps)
            known = sum(len([x for x in c.get("competitors", []) if name(x)]) == 2 for c in comps)
            print(f"  {ev.get('name')} [{slug}]: {len(comps)} zápasov, oba hráči známi {known}")
            print(f"    stavy {dict(states)}")
            if comps and slug.endswith("singles"):
                c = comps[0]
                players = [
                    f"{name(x)} (id {x.get('id')}, víťaz {x.get('winner')})" for x in c.get("competitors", [])
                ]
                rnd = (c.get("round") or {}).get("displayName")
                print(f"    ukážka: {c.get('date')} kolo {rnd}: {' – '.join(players)}")
                print(f"    polia zápasu: {', '.join(sorted(c))}")
    if not events:
        print("  žiadne turnaje")


def espn() -> None:
    print("\n== 2. ESPN tenis")
    today = datetime.now(UTC)
    days = [today.strftime("%Y%m%d"), (today + timedelta(days=1)).strftime("%Y%m%d"), GAP_DAY]
    for tour in ("atp", "wta"):
        for day in days:
            espn_day(tour, day)


def main() -> int:
    for step in (sackmann, espn):
        try:
            step()
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(f"!! {step.__name__}: {type(e).__name__}: {e}")
    print("\nHotovo. Celý výstup vlož do chatu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
