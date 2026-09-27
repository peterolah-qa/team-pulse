"""Adaptér: zranenia z ESPN.

Pozor: ESPN blokuje (403) požiadavky, ktoré sa vydávajú za prehliadač → predvolené hlavičky.
"""

from __future__ import annotations

import re

import pandas as pd
import requests

from team_pulse.live.teams import from_espn

URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"

# ESPN typ → náš stav a pravdepodobnosť, že hráč NEnastúpi (váha pre vrstvu B)
STATUS = {
    "INJURY_STATUS_OUT": ("OUT", 1.0),
    "INJURY_STATUS_SUSPENSION": ("OUT", 1.0),
    "INJURY_STATUS_DOUBTFUL": ("DOUBTFUL", 0.75),
    "INJURY_STATUS_QUESTIONABLE": ("QUESTIONABLE", 0.5),
    "INJURY_STATUS_DAYTODAY": ("QUESTIONABLE", 0.5),  # ESPN „day-to-day“ = rozhodne sa pred zápasom
    "INJURY_STATUS_PROBABLE": ("PROBABLE", 0.1),
}
UNKNOWN = ("QUESTIONABLE", 0.5)

_ESPN_ID = re.compile(r"/id/(\d+)")


def espn_player_id(athlete: dict) -> int | None:
    for link in athlete.get("links", []):
        m = _ESPN_ID.search(link.get("href", ""))
        if m:
            return int(m.group(1))
    return None


def parse_injuries(data: dict) -> pd.DataFrame:
    rows = []
    for team_block in data.get("injuries", []):
        for inj in team_block.get("injuries", []):
            athlete = inj.get("athlete", {})
            espn_team = athlete.get("team", {}).get("abbreviation")
            type_name = inj.get("type", {}).get("name", "")
            status, weight = STATUS.get(type_name, UNKNOWN)
            details = inj.get("details", {})
            ret = details.get("returnDate")
            rows.append(
                {
                    "team": from_espn(espn_team),
                    "player": athlete.get("displayName", ""),
                    "espn_id": espn_player_id(athlete),
                    "status": status,
                    "p_out": weight,
                    "espn_type": type_name,
                    "updated": pd.Timestamp(inj["date"]) if inj.get("date") else pd.NaT,
                    "return_date": pd.Timestamp(ret) if ret else pd.NaT,
                    "comment": inj.get("shortComment", ""),
                }
            )
    cols = ["team", "player", "espn_id", "status", "p_out", "espn_type", "updated", "return_date", "comment"]
    return pd.DataFrame(rows, columns=cols)


def fetch_injuries() -> dict:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    return r.json()
