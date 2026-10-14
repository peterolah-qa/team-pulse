"""NHL: zranenia z ESPN – len informácia v appke, model NHL ich nepoužíva (brána G2-NHL).

ESPN značí niektoré kluby inak než API NHL (LA, NJ, SJ, TB) → preklad na skratky NHL.
Pozor: ESPN blokuje (403) požiadavky, ktoré sa vydávajú za prehliadač → predvolené hlavičky.
"""

from __future__ import annotations

import requests

from team_pulse.nhl.fetch_games import franchise

URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries"
ESPN_TO_NHL = {"LA": "LAK", "NJ": "NJD", "SJ": "SJS", "TB": "TBL", "UTAH": "UTA", "WAS": "WSH"}

# ESPN typ → náš stav; poradie = od najistejšie chýbajúceho
STATUS = {
    "INJURY_STATUS_OUT": "OUT",
    "INJURY_STATUS_SUSPENSION": "SUSP",
    "INJURY_STATUS_IR": "IR",
    "INJURY_STATUS_DAYTODAY": "DTD",
}
ORDER = ["OUT", "SUSP", "IR", "DTD", "?"]


def team(espn_abbr: str) -> str:
    return franchise(ESPN_TO_NHL.get(espn_abbr, espn_abbr))


def parse(data: dict) -> dict[str, list[dict]]:
    """Odpoveď ESPN → {klub NHL: [hráči]}; hráči od najistejšie chýbajúceho, potom podľa mena."""
    out: dict[str, list[dict]] = {}
    for block in data.get("injuries") or []:
        for inj in block.get("injuries") or []:
            athlete = inj.get("athlete") or {}
            abbr = (athlete.get("team") or {}).get("abbreviation")
            if not abbr or not athlete.get("displayName"):
                continue
            details = inj.get("details") or {}
            out.setdefault(team(abbr), []).append(
                {
                    "player": athlete["displayName"],
                    "pos": (athlete.get("position") or {}).get("abbreviation"),
                    "status": STATUS.get((inj.get("type") or {}).get("name", ""), "?"),
                    "injury": details.get("type"),
                    "return_date": details.get("returnDate"),
                    "updated": inj.get("date"),
                }
            )
    for players in out.values():
        players.sort(key=lambda p: (ORDER.index(p["status"]), p["player"]))
    return dict(sorted(out.items()))


def fetch(session: requests.Session | None = None) -> dict:
    r = (session or requests).get(URL, timeout=30)
    r.raise_for_status()
    return r.json()
