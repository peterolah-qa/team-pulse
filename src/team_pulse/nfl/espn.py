"""ESPN NFL scoreboard: rozpis a výsledky (rovnaký zdroj ako zranenia NBA).

Párovanie s nflverse games.csv cez ESPN ID zápasu (stĺpec espn). Skratky ESPN sa prevedú na skratky
games.csv (WSH → WAS, LAR → LA).
"""

from __future__ import annotations

import requests

URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
ESPN_TO_NFLVERSE = {"WSH": "WAS", "LAR": "LA"}
FINAL = "STATUS_FINAL"


def team(abbr: str) -> str:
    return ESPN_TO_NFLVERSE.get(abbr, abbr)


def parse_scoreboard(data: dict) -> list[dict]:
    """Jeden záznam na zápas: espn_id, kickoff_utc, home, away, neutral, state, final, skóre."""
    out = []
    for ev in data.get("events", []):
        comp = ev["competitions"][0]
        side = {c["homeAway"]: c for c in comp["competitors"]}
        if set(side) != {"home", "away"}:
            raise ValueError(f"zápas {ev.get('id')}: chýba domáci alebo hosť")
        status = comp["status"]["type"]["name"]
        final = status == FINAL

        def score(c: dict, final: bool = final) -> int | None:
            return int(c["score"]) if final and c.get("score") not in (None, "") else None

        out.append(
            {
                "espn_id": str(ev["id"]),
                "kickoff_utc": comp["date"],
                "home": team(side["home"]["team"]["abbreviation"]),
                "away": team(side["away"]["team"]["abbreviation"]),
                "neutral": bool(comp.get("neutralSite")),
                "state": status,
                "final": final,
                "score_home": score(side["home"]),
                "score_away": score(side["away"]),
            }
        )
    return out


def fetch(week: int | None = None, session: requests.Session | None = None) -> list[dict]:
    params = {"week": week} if week else None
    r = (session or requests.Session()).get(URL, params=params, timeout=30)
    r.raise_for_status()
    return parse_scoreboard(r.json())
