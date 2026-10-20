"""Sonda: kontext NHL zápasu so skutočnými dátami (spustiť raz z Macu pred zverejnením detailu).

Overí na dnešných zamknutých tipoch z archívu:
  1. rozpisy klubov: z rovnakých čísel ako ráno model znova vypočíta presne zamknutú šancu (rozpad „overený“),
  2. štatistiky NHL (team/summary): tvar, celá liga a pri každom klube počet zápasov a výhier = jeho rozpis,
  3. ukážka jedného zápasu (forma, odpočinok, vzájomné zápasy, štatistiky) na porovnanie s NHL.com.
Odpoveď štatistík uloží do tests/fixtures/nhl_team_summary.json (skutočný tvar pre testy).

Spustenie:  uv run python scripts/probe_nhl_context.py
Nič nezapisuje do appky ani do archívu, výstup appky ide do dočasného priečinka.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import requests

from team_pulse.nhl import app_data as ad
from team_pulse.nhl import context as cx
from team_pulse.nhl.fetch_games import CURRENT, season_of, today_et

FIXTURE = Path("tests/fixtures/nhl_team_summary.json")


def main() -> int:
    now = datetime.now(UTC)
    season = season_of(today_et(now))
    problems: list[str] = []

    raw = cx.fetch_summary(season)
    FIXTURE.write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Štatistiky NHL: {len(raw.get('data') or [])} riadkov → {FIXTURE}")
    first = (raw.get("data") or [{}])[0]
    print("  polia:", ", ".join(sorted(first)))

    # celá liga: rozpis každého klubu (id → skratka a kontrola počtu zápasov a výhier)
    session = requests.Session()
    teams = {
        t: {str(season): {"fetched_at": now.isoformat(), "games": cx.fetch_club(t, season, session)}}
        for t in CURRENT
    }
    cache = {"version": cx.CACHE_VERSION, "teams": teams}
    parsed = cx.team_stats(raw, cx.team_ids(cache), season)
    problems += parsed["problems"]
    kept, wrong = cx.check_stats(parsed["teams"], cache, season)
    problems += wrong
    print(f"  tvar OK pre {len(parsed['teams'])} klubov, zápasy a výhry sedia s rozpisom: {len(kept)} z 32")

    # celý beh appky do dočasného priečinka (bez cache, všetko čerstvé)
    with tempfile.TemporaryDirectory() as tmp:
        ad.cx.load_cache = lambda *_a, **_k: {}  # type: ignore[assignment]
        data = ad.main(out=Path(tmp))
    games = [g for gs in data["days"].values() for g in gs]
    verified = [g for g in games if g["ctx"]["edge"]["verified"]]
    print(
        f"\nZápasy s tipom: {len(games)}, rozpad overený (model z rozpisu = zamknutá šanca): {len(verified)}"
    )
    for g in games:
        if not g["ctx"]["edge"]["verified"]:
            problems.append(f"rozpad neoverený: {g['away']['team']} @ {g['home']['team']} ({g['game_id']})")
    if games:
        g = games[0]
        c = g["ctx"]
        print(f"\nUkážka {g['away']['team']} @ {g['home']['team']}, {c.get('venue')}, domáci {g['p_home']}")
        for _k, label, v in c["edge"]["items"]:
            print(f"  {label:<38} {v:+7.1f}")
        print(f"  {'spolu (Elo)':<38} {c['edge']['total']:+7.1f}")
        for side in ("away", "home"):
            if side in c:
                f, r = c[side]["form"], c[side]["rest"]
                last = " ".join(f"{x['res']}{x['gf']}:{x['ga']}" for x in f["last"])
                print(f"  {g[side]['team']}: bilancia {f['record']}, posledné {last}, odpočinok {r}")
                if "stats" in c[side]:
                    print(f"    štatistiky {c[side]['stats']}")
        print(f"  vzájomné: {c.get('h2h')}")
    print("\nOK" if not problems else "\nPROBLÉMY:\n- " + "\n- ".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
