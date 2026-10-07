"""Adaptér: ESPN summary – štatistiky hráčov z dohraného zápasu (box score).

Funguje z cloudu, takže výsledky a štatistiky sú v appke hneď po zápase, aj z prípravy,
bez čakania na rannú aktualizáciu z Macu. Kurzy a tipy, ktoré ESPN v summary posiela
(pickcenter, odds, againstTheSpread), zámerne ignorujeme.
"""

from __future__ import annotations

import requests

from team_pulse.live.teams import from_espn

URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
WANTED = {"MIN": "min", "PTS": "pts", "REB": "reb", "AST": "ast", "BLK": "blk", "STL": "stl"}


def _int(value: object) -> int:
    try:
        return int(float(str(value)))
    except ValueError:
        return 0  # "--" a podobné


def parse_boxscore(data: dict) -> dict[str, list[dict]]:
    """Team → hráči, ktorí hrali (bez DNP), zoradení podľa minút.

    Stĺpce sa hľadajú podľa názvu (MIN, PTS, …), nie podľa poradia. Zmenený formát vyhodí chybu.
    """
    out: dict[str, list[dict]] = {}
    for side in data.get("boxscore", {}).get("players", []):
        team = from_espn(side["team"]["abbreviation"])
        stats = side["statistics"][0]
        labels = stats.get("labels") or stats["names"]
        idx = {key: labels.index(label) for label, key in WANTED.items()}
        rows = []
        for a in stats.get("athletes", []):
            values = a.get("stats") or []
            if a.get("didNotPlay") or len(values) < len(labels):
                continue
            rows.append(
                {"player": a["athlete"]["displayName"], **{k: _int(values[i]) for k, i in idx.items()}}
            )
        rows.sort(key=lambda r: (-r["min"], -r["pts"]))
        out[team] = rows
    return out


def fetch_summary(espn_id: str) -> dict:
    r = requests.get(URL, params={"event": espn_id}, timeout=30)
    r.raise_for_status()
    return r.json()
