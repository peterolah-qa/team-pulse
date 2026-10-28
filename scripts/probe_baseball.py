"""Sonda: zdroje pre bejzbal (MLB a LVBP). Spustiť raz z Macu, výstup vložiť do chatu.

Overí a vypíše (nič neukladá, surové dáta sa necommitujú):
  1. MLB Stats API: text copyrightu v odpovedi, jeden deň MLB s ohlásenými nadhadzovačmi a výsledkami,
  2. zimné ligy v MLB Stats API (sportId 17): ktoré ligy a tímy, či je medzi nimi LVBP a koľko zápasov
     základnej časti má po sezónach (história na backtest) a koľko z nich má oboch nadhadzovačov,
  3. Retrosheet: dostupnosť game logov a znenie notice.txt (povinná veta o zdroji),
  4. 538 mlb_elo.csv: pôvodná adresa a kópia v archive.org (referencia pre G0-MLB),
  5. robots.txt stránok o LVBP: či zakazujú roboty alebo AI (takú stránku nepoužijeme).

Spustenie (z Macu):  uv run python scripts/probe_baseball.py
"""

from __future__ import annotations

import sys
import time
from collections import Counter

import requests

STATSAPI = "https://statsapi.mlb.com/api/v1"
MLB_DAY = "2026-09-27"  # posledný deň základnej časti 2026, hrajú všetci
WINTER_SEASONS = range(2010, 2027)  # LVBP 2025/26 = season 2025
RETRO_LOG = "https://www.retrosheet.org/gamelogs/gl2025.zip"
RETRO_NOTICE = "https://www.retrosheet.org/notice.txt"
ELO_538 = "projects.fivethirtyeight.com/mlb-api/mlb_elo.csv"
ROBOTS = [
    "https://www.lvbp.com/robots.txt",
    "https://www.pelotabinaria.com.ve/robots.txt",
    "https://www.retrosheet.org/robots.txt",
]
AI_AGENTS = {"*", "gptbot", "claudebot", "claude-web", "anthropic-ai", "ccbot", "google-extended"}
HEADERS = {"User-Agent": "team-pulse probe (nekomerčný projekt; github.com/peterolah-qa/team-pulse)"}
PAUSE = 0.5  # s medzi dopytmi na MLB Stats API, žiadne hromadné sťahovanie

session = requests.Session()
session.headers.update(HEADERS)


def get(url: str, **params: object) -> requests.Response:
    r = session.get(url, params=params or None, timeout=30)
    time.sleep(PAUSE)
    return r


def blocked_agents(robots: str) -> set[str]:
    """User-agenti (z AI_AGENTS), ktorým robots.txt zakazuje celú stránku (Disallow: /)."""
    out: set[str] = set()
    agents: list[str] = []
    in_rules = False
    for raw in robots.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (x.strip() for x in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
        elif key in {"disallow", "allow"}:
            in_rules = True
            if key == "disallow" and value == "/":
                out |= {a for a in agents if a in AI_AGENTS}
    return out


def mlb_day() -> None:
    print(f"\n== 1. MLB Stats API: MLB {MLB_DAY}")
    r = get(f"{STATSAPI}/schedule", sportId=1, date=MLB_DAY, hydrate="probablePitcher")
    print(f"HTTP {r.status_code}")
    if not r.ok:
        return
    data = r.json()
    print("copyright:", data.get("copyright"))
    games = [g for d in data.get("dates", []) for g in d.get("games", [])]
    pitchers = sum(all(g["teams"][s].get("probablePitcher") for s in ("home", "away")) for g in games)
    states = Counter(g.get("status", {}).get("detailedState") for g in games)
    print(f"zápasov {len(games)}, s oboma nadhadzovačmi {pitchers}, stavy {dict(states)}")
    if games:
        g = games[0]
        h, a = g["teams"]["home"], g["teams"]["away"]
        print(
            f"ukážka: gamePk {g['gamePk']}, {a['team']['name']} @ {h['team']['name']}, "
            f"skóre {a.get('score')}:{h.get('score')}, gameType {g.get('gameType')}, "
            f"doubleHeader {g.get('doubleHeader')} / gameNumber {g.get('gameNumber')}, "
            f"nadhadzovači {a.get('probablePitcher', {}).get('fullName')} – "
            f"{h.get('probablePitcher', {}).get('fullName')}"
        )
        print("polia zápasu:", ", ".join(sorted(g)))


def winter() -> None:
    print("\n== 2. MLB Stats API: zimné ligy (sportId 17)")
    r = get(f"{STATSAPI}/teams", sportId=17, season=2026)
    print(f"HTTP {r.status_code}")
    if not r.ok:
        return
    leagues: dict[int, tuple[str, list[str]]] = {}
    for t in r.json().get("teams", []):
        lg = t.get("league") or {}
        name, names = leagues.setdefault(lg.get("id", 0), (lg.get("name", "?"), []))
        names.append(t.get("name", "?"))
    for lid, (name, names) in sorted(leagues.items()):
        print(f"liga {lid} {name}: {len(names)} tímov – {', '.join(sorted(names))}")
    lvbp = [lid for lid, (name, names) in leagues.items() if "venez" in name.lower()]
    lvbp += [lid for lid, (_, names) in leagues.items() if any("Magallanes" in n for n in names)]
    if not lvbp:
        print("LVBP medzi zimnými ligami nie je.")
        return
    lid = lvbp[0]
    print(f"\nLVBP = liga {lid}, základná časť po sezónach (zápasy / dohraté / s oboma nadhadzovačmi):")
    for season in WINTER_SEASONS:
        r = get(
            f"{STATSAPI}/schedule",
            sportId=17,
            leagueId=lid,
            season=season,
            gameType="R",
            hydrate="probablePitcher",
        )
        if not r.ok:
            print(f"  {season}: HTTP {r.status_code}")
            continue
        games = [g for d in r.json().get("dates", []) for g in d.get("games", [])]
        final = [g for g in games if g.get("status", {}).get("abstractGameState") == "Final"]
        both = sum(all(g["teams"][s].get("probablePitcher") for s in ("home", "away")) for g in final)
        first = games[0]["officialDate"] if games else "-"
        last = games[-1]["officialDate"] if games else "-"
        print(f"  {season}: {len(games)} / {len(final)} / {both}  ({first} – {last})")


def retrosheet() -> None:
    print("\n== 3. Retrosheet")
    r = session.head(RETRO_LOG, timeout=30, allow_redirects=True)
    print(f"{RETRO_LOG}: HTTP {r.status_code}, veľkosť {r.headers.get('Content-Length')} B")
    r = session.get(RETRO_NOTICE, timeout=30)
    print(f"{RETRO_NOTICE}: HTTP {r.status_code}")
    if r.ok:
        print(r.text.strip())


def elo_538() -> None:
    print("\n== 4. 538 mlb_elo.csv")
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
    print(
        f"archive.org: kópia z {snap['timestamp']}, HTTP {h.status_code}, "
        f"veľkosť {h.headers.get('Content-Length')} B\n  {raw}"
    )


def robots() -> None:
    print("\n== 5. robots.txt")
    for url in ROBOTS:
        try:
            r = session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"{url}: {type(e).__name__}")
            continue
        if r.status_code == 404:
            print(f"{url}: 404 (robots.txt neexistuje, nič nezakazuje)")
            continue
        bad = blocked_agents(r.text) if r.ok else set()
        verdict = f"ZAKAZUJE celú stránku pre: {', '.join(sorted(bad))}" if bad else "celú stránku nezakazuje"
        print(f"{url}: HTTP {r.status_code}, {verdict}")


def main() -> int:
    for step in (mlb_day, winter, retrosheet, elo_538, robots):
        try:
            step()
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"!! {step.__name__}: {type(e).__name__}: {e}")
    print("\nHotovo. Celý výstup vlož do chatu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
