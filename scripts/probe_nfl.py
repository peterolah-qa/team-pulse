"""Sonda: zdroje pre NFL. Spustiť raz z Macu, výstup vložiť do chatu.

Overí a vypíše:
  1. 538 nfl_elo.csv: pôvodná adresa a kópia v archive.org (referencia pre G0-NFL, CC BY 4.0),
  2. ESPN NFL scoreboard (aktuálny týždeň): zápasy, stavy, skratky tímov, čas výkopu, ESPN ID zápasu
     a či sedia s ESPN ID v nflverse games.csv (týždeň 8: CAR @ GB = 401873023),
  3. ESPN NFL zranenia: počet záznamov, quarterbacky a ich stavy.
Skrátenú odpoveď scoreboardu uloží do tests/fixtures/nfl_espn_scoreboard.json (contract test, G0-NFL bod 5).

Spustenie (z Macu):  uv run python scripts/probe_nfl.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import requests

ELO_538 = "projects.fivethirtyeight.com/nfl-api/nfl_elo.csv"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
KNOWN = {"401873023": "CAR @ GB"}  # z games.csv (commit a6b91bf), týždeň 8, 29. 10. 2026
FIXTURE = Path("tests/fixtures/nfl_espn_scoreboard.json")
HEADERS = {"User-Agent": "team-pulse probe (non-commercial; github.com/peterolah-qa/team-pulse)"}  # len ASCII

session = requests.Session()
session.headers.update(HEADERS)


def elo_538() -> None:
    print("== 1. 538 nfl_elo.csv")
    try:
        r = session.head(f"https://{ELO_538}", timeout=30, allow_redirects=True)
        print(f"pôvodná adresa: HTTP {r.status_code}, konečná adresa {r.url}")
    except requests.RequestException as e:
        print(f"pôvodná adresa: {type(e).__name__}")
    r = session.get("https://archive.org/wayback/available", params={"url": ELO_538}, timeout=30)
    snap = (r.json().get("archived_snapshots") or {}).get("closest") if r.ok else None
    if not snap:
        print("archive.org: kópia nenájdená")
        return
    raw = snap["url"].replace(f"/{snap['timestamp']}/", f"/{snap['timestamp']}id_/", 1)
    h = session.head(raw, timeout=60, allow_redirects=True)
    size = h.headers.get("Content-Length")
    print(f"archive.org: kópia z {snap['timestamp']}, HTTP {h.status_code}, veľkosť {size} B\n  {raw}")


def trim_event(ev: dict) -> dict:
    """Len polia, ktoré sťahovač potrebuje (contract test)."""
    comp = ev["competitions"][0]
    return {
        "id": ev["id"],
        "date": ev["date"],
        "week": ev.get("week"),
        "season": ev.get("season"),
        "status": {"type": comp["status"]["type"]},
        "competitions": [
            {
                "id": comp["id"],
                "date": comp["date"],
                "neutralSite": comp.get("neutralSite"),
                "status": {"type": comp["status"]["type"]},
                "competitors": [
                    {
                        "homeAway": c["homeAway"],
                        "score": c.get("score"),
                        "winner": c.get("winner"),
                        "team": {k: c["team"].get(k) for k in ("id", "abbreviation", "displayName")},
                    }
                    for c in comp["competitors"]
                ],
            }
        ],
    }


def scoreboard() -> None:
    print("\n== 2. ESPN NFL scoreboard")
    r = session.get(f"{ESPN}/scoreboard", timeout=30)
    print(f"HTTP {r.status_code}")
    if not r.ok:
        return
    data = r.json()
    events = data.get("events", [])
    print(f"týždeň {data.get('week')}, sezóna {data.get('season')}, zápasov {len(events)}")
    print("stavy:", dict(Counter(e["competitions"][0]["status"]["type"]["name"] for e in events)))
    for ev in events[:16]:
        comp = ev["competitions"][0]
        teams = {c["homeAway"]: c["team"]["abbreviation"] for c in comp["competitors"]}
        note = f"  ← games.csv: {KNOWN[ev['id']]}" if ev["id"] in KNOWN else ""
        game = f"{teams.get('away')} @ {teams.get('home')}"
        print(f"  {ev['id']} {ev['date']} {game} neutral={comp.get('neutralSite')}{note}")
    if events:
        print("polia zápasu:", ", ".join(sorted(events[0])))
        print("polia súťaže:", ", ".join(sorted(events[0]["competitions"][0])))
        FIXTURE.write_text(
            json.dumps({"events": [trim_event(e) for e in events[:3]]}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"skrátená odpoveď (3 zápasy) → {FIXTURE}")


def injuries() -> None:
    print("\n== 3. ESPN NFL zranenia")
    r = session.get(f"{ESPN}/injuries", timeout=30)
    print(f"HTTP {r.status_code}")
    if not r.ok:
        return
    teams = r.json().get("injuries", [])
    rows = [i for t in teams for i in t.get("injuries", [])]
    qbs = [i for i in rows if ((i.get("athlete") or {}).get("position") or {}).get("abbreviation") == "QB"]
    print(f"tímov {len(teams)}, záznamov {len(rows)}, z toho QB {len(qbs)}")
    print("stavy QB:", dict(Counter(i.get("status") for i in qbs)))
    if rows:
        print("polia záznamu:", ", ".join(sorted(rows[0])))


def main() -> int:
    for step in (elo_538, scoreboard, injuries):
        try:
            step()
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(f"!! {step.__name__}: {type(e).__name__}: {e}")
    print("\nHotovo. Celý výstup vlož do chatu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
