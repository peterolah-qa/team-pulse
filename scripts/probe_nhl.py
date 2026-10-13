"""Prieskum zdrojov NHL: stiahne ukážky odpovedí a overí, čo sťahovač potrebuje.

  data/probe/nhl_*.json       celé odpovede (necommitujú sa)
  tests/fixtures/nhl_*.json   skrátené ukážky pre contract testy (commitujú sa)

Overí:
  * rozpis klubu (club-schedule-season): skóre, predĺženie a nájazdy, neutrálny ľad
  * zaniknuté skratky (ATL, PHX) vrátia rozpis, inak by chýbal zápas ATL – PHX
  * ESPN hokej (výsledky dňa, zápas, zranenia) má rovnaký tvar ako pri NBA

Spustenie (z Macu):  uv run python scripts/probe_nhl.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import requests

NHL = "https://api-web.nhle.com/v1"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
ESPN_DAY = "20260115"  # štvrtok v sezóne 2025/26, hrá sa

RAW = Path("data/probe")
FIXTURES = Path("tests/fixtures")


def get(url: str) -> dict:
    r = requests.get(url, timeout=30)  # predvolené hlavičky: ESPN blokuje „prehliadač“
    r.raise_for_status()
    return r.json()


def trim(obj: object, n: int = 3) -> object:
    """Každý zoznam skráti na prvých n prvkov (rekurzívne)."""
    if isinstance(obj, list):
        return [trim(x, n) for x in obj[:n]]
    if isinstance(obj, dict):
        return {k: trim(v, n) for k, v in obj.items()}
    return obj


def save(name: str, raw: object, fixture: object) -> None:
    (RAW / f"{name}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    text = json.dumps(fixture, ensure_ascii=False, indent=1) + "\n"
    (FIXTURES / f"{name}.json").write_text(text, encoding="utf-8")


def outcome(g: dict) -> str | None:
    return (g.get("gameOutcome") or {}).get("lastPeriodType")


def club_schedule() -> list[str]:
    raw = get(f"{NHL}/club-schedule-season/TOR/20242025")
    games = raw.get("games") or []
    picked: dict[tuple, dict] = {}
    for g in games:  # jeden zápas z každého typu: príprava, základná časť, playoff × REG/OT/SO
        picked.setdefault((g.get("gameType"), outcome(g)), g)
    save("nhl_club_schedule", raw, {"games": list(picked.values())})
    kinds = Counter((g.get("gameType"), outcome(g)) for g in games)
    neutral = sum(1 for g in games if g.get("neutralSite"))
    problems = []
    if not any(k[1] in ("OT", "SO") for k in kinds):
        problems.append("rozpis klubu nemá gameOutcome.lastPeriodType (predĺženie / nájazdy)")
    if not all("neutralSite" in g for g in games):
        problems.append("niektoré zápasy nemajú neutralSite")
    print(f"TOR 2024/25: {len(games)} zápasov, typy {dict(kinds)}, neutrálny ľad {neutral}")
    print(f"  kľúče zápasu: {sorted(games[0])}" if games else "  žiadne zápasy")
    return problems


def defunct_clubs() -> list[str]:
    seen: dict[str, list[dict]] = {}
    for team in ("ATL", "PHX"):
        try:
            seen[team] = get(f"{NHL}/club-schedule-season/{team}/20092010").get("games") or []
        except requests.HTTPError as e:
            seen[team] = []
            print(f"{team} 2009/10: {e}")
    both = [
        g for g in seen["ATL"]
        if {g["homeTeam"]["abbrev"], g["awayTeam"]["abbrev"]} == {"ATL", "PHX"} and g.get("gameType") == 2
    ]  # fmt: skip
    save("nhl_club_schedule_defunct", seen, {"ATL": len(seen["ATL"]), "PHX": len(seen["PHX"]), "games": both})
    print(f"ATL 2009/10: {len(seen['ATL'])} zápasov, PHX: {len(seen['PHX'])}, ATL – PHX: {len(both)}")
    return (
        []
        if both
        else ["zaniknuté skratky nevrátili zápas ATL – PHX → treba iný zdroj pre 2005/06 – 2010/11"]
    )


def espn_hockey() -> list[str]:
    board = get(f"{ESPN}/scoreboard?dates={ESPN_DAY}")
    events = board.get("events") or []
    save("espn_nhl_scoreboard", board, trim(board))
    print(f"ESPN výsledky {ESPN_DAY}: {len(events)} zápasov")
    problems = [] if events else [f"ESPN scoreboard {ESPN_DAY} je prázdny"]
    if events:
        summary = get(f"{ESPN}/summary?event={events[0]['id']}")
        save("espn_nhl_summary", summary, trim(summary))
        players = summary.get("boxscore", {}).get("players") or []
        labels = [s.get("labels") for t in players[:1] for s in t.get("statistics", [])]
        print(f"ESPN zápas {events[0]['id']}: štatistiky hráčov {labels}")
    inj = get(f"{ESPN}/injuries")
    teams = inj.get("injuries") or []
    save("espn_nhl_injuries", inj, trim(inj))
    print(f"ESPN zranenia: {len(teams)} teamov, {sum(len(t.get('injuries', [])) for t in teams)} hráčov")
    return problems


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    problems = []
    for step in (club_schedule, defunct_clubs, espn_hockey):
        try:
            problems += step()
        except Exception as e:  # zdroj nedostupný alebo iný tvar
            problems.append(f"{step.__name__}: {e.__class__.__name__}: {e}")
    print(
        "\nOK, ukážky sú v tests/fixtures/nhl_*.json"
        if not problems
        else "\nPROBLÉMY:\n- " + "\n- ".join(problems)
    )


if __name__ == "__main__":
    main()
