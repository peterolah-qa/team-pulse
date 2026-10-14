"""Prieskum pre vrstvu brankára (NHL): dá sa história aj dnešný štartujúci brankár?

Vrstva má zmysel len vtedy, keď poznáme brankára PRED zápasom aj naživo. Sonda overí:
  1. história: štatistiky brankárov po zápasoch (kto začal, zákroky) z api.nhle.com/stats
     – jedna sezóna na pár požiadavok namiesto 1 300 box score
  2. box score dohraného zápasu: príznak starter
  3. dnešné zápasy pred začiatkom: či NHL alebo ESPN už ukazujú štartujúceho brankára

Bod 3 má zmysel pustiť aj 1 – 2 hodiny pred prvým zápasom večera (vtedy kluby brankára potvrdzujú).

  data/probe/nhl_goalies_*.json       celé odpovede (necommitujú sa)
  tests/fixtures/nhl_goalie_games.json skrátená ukážka histórie pre contract test

Spustenie (z Macu):  uv run python scripts/probe_nhl_goalies.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

NHL = "https://api-web.nhle.com/v1"
STATS = "https://api.nhle.com/stats/rest/en"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
SEASON = "20242025"
WORDS = ("goalie", "starter", "probable", "confirmed", "projected")

RAW = Path("data/probe")
FIXTURES = Path("tests/fixtures")


def get(url: str, params: dict | None = None) -> dict:
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def dump(name: str, data: object) -> None:
    (RAW / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def find_keys(obj: object, path: str = "") -> list[str]:
    """Cesty ku kľúčom, ktoré vyzerajú ako informácia o brankárovi (do hĺbky, prvé 3 prvky zoznamov)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if any(w in k.lower() for w in WORDS):
                out.append(f"{p} = {json.dumps(v, ensure_ascii=False)[:160]}")
            out += find_keys(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            out += find_keys(v, f"{path}[{i}]")
    return out


def history() -> list[str]:
    params = {
        "isAggregate": "false",
        "isGame": "true",
        "start": 0,
        "limit": 100,
        "sort": '[{"property":"gameId","direction":"ASC"}]',
        "cayenneExp": f"seasonId={SEASON} and gameTypeId=2",
    }
    first = get(f"{STATS}/goalie/summary", params)
    rows, total = first.get("data") or [], first.get("total")
    dump("nhl_goalies_history_page", first)
    row = rows[0] if rows else {}
    print(f"História {SEASON}: {total} riadkov brankár × zápas, stránka {len(rows)}")
    print(f"  kľúče: {sorted(row)}")
    sample = {"total": total, "data": rows[:4]}
    (FIXTURES / "nhl_goalie_games.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    problems = []
    if not rows:
        problems.append("štatistiky brankárov po zápasoch sú prázdne")
    elif "gameId" not in row or "gamesStarted" not in row:
        problems.append("v štatistikách chýba gameId alebo gamesStarted")
    if total and total < 2 * 1312:
        problems.append(f"málo riadkov ({total}), čakal som aspoň {2 * 1312} (dvaja brankári na zápas)")
    return problems


def boxscore() -> list[str]:
    box = get(f"{NHL}/gamecenter/2024020001/boxscore")
    dump("nhl_goalies_boxscore", box)
    goalies = [
        g for side in ("homeTeam", "awayTeam") for g in box["playerByGameStats"][side].get("goalies", [])
    ]
    starters = [g["name"]["default"] for g in goalies if g.get("starter")]
    print(f"Box score 2024020001: brankári {len(goalies)}, starter {starters}")
    return [] if len(starters) == 2 else ["box score nemá príznak starter pre oboch brankárov"]


def today() -> list[str]:
    day = datetime.now(ZoneInfo("America/New_York")).date().isoformat()  # zápasy sú podľa dňa v USA
    sched = get(f"{NHL}/score/{day}")
    games = [g for g in sched.get("games", []) if g.get("gameState") in ("FUT", "PRE")]
    print(f"Dnes {day}: {len(sched.get('games', []))} zápasov, pred začiatkom {len(games)}")
    if not games:
        return ["dnes nie je zápas pred začiatkom – pusti sondu v iný deň"]
    g = games[0]
    print(f"  skúšam {g['awayTeam']['abbrev']} @ {g['homeTeam']['abbrev']} ({g['startTimeUTC']})")
    found = {}
    for name, url in {
        "landing": f"{NHL}/gamecenter/{g['id']}/landing",
        "boxscore": f"{NHL}/gamecenter/{g['id']}/boxscore",
        "right-rail": f"{NHL}/gamecenter/{g['id']}/right-rail",
    }.items():
        try:
            data = get(url)
        except requests.HTTPError as e:
            print(f"  NHL {name}: {e}")
            continue
        dump(f"nhl_goalies_pregame_{name}", data)
        found[f"NHL {name}"] = find_keys(data)
    board = get(f"{ESPN}/scoreboard", {"dates": day.replace("-", "")})
    ev = next((e for e in board.get("events", []) if g["homeTeam"]["abbrev"] in e.get("shortName", "")), None)
    if ev:
        summary = get(f"{ESPN}/summary", {"event": ev["id"]})
        dump("nhl_goalies_pregame_espn", summary)
        found["ESPN summary"] = find_keys(summary)
    for src, keys in found.items():
        print(f"  {src}: {len(keys)} kľúčov o brankárovi")
        for k in keys[:8]:
            print(f"    {k}")
    return []


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    problems = []
    for step in (history, boxscore, today):
        try:
            problems += step()
        except Exception as e:  # zdroj nedostupný alebo iný tvar
            problems.append(f"{step.__name__}: {e.__class__.__name__}: {e}")
    print("\nOK" if not problems else "\nPROBLÉMY:\n- " + "\n- ".join(problems))


if __name__ == "__main__":
    main()
