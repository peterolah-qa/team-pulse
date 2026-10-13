"""Adaptér: ESPN scoreboard – zápasy a výsledky v daný deň.

Funguje aj z cloudu (GitHub Actions), kde nba_api blokujú → zdroj výsledkov pre agenta.
Kurzy stávkových kancelárií, ktoré ESPN posiela, zámerne ignorujeme.
"""

from __future__ import annotations

import pandas as pd
import requests

from team_pulse.live.teams import from_espn

URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"


def is_preseason(ev: dict) -> bool:
    season = ev.get("season", {})
    return season.get("slug") == "preseason" or season.get("type") == 1


def parse_scoreboard(data: dict) -> pd.DataFrame:
    """Zápasy dňa. Prípravné zápasy proti klubom mimo NBA (napr. z Austrálie) sa preskočia;
    neznámy team v zápase sezóny je chyba (ESPN zmenila skratku) a contract test ju zachytí."""
    rows = []
    for ev in data.get("events", []):
        comp = ev["competitions"][0]
        sides = {c["homeAway"]: c for c in comp["competitors"]}
        status = comp.get("status", ev.get("status", {})).get("type", {})
        try:
            home = from_espn(sides["home"]["team"]["abbreviation"])
            away = from_espn(sides["away"]["team"]["abbreviation"])
        except KeyError:
            if is_preseason(ev):
                continue
            raise
        rows.append(
            {
                "espn_id": ev["id"],
                "tipoff_utc": pd.Timestamp(ev["date"]),
                "home": home,
                "away": away,
                "neutral": bool(comp.get("neutralSite", False)),
                "state": status.get("state", "pre"),  # pre / in / post
                "completed": bool(status.get("completed", False)),
                "pts_home": int(sides["home"].get("score") or 0),
                "pts_away": int(sides["away"].get("score") or 0),
            }
        )
    cols = ["espn_id", "tipoff_utc", "home", "away", "neutral", "state", "completed", "pts_home", "pts_away"]
    return pd.DataFrame(rows, columns=cols)


def fetch_scoreboard(day: str) -> dict:
    """day vo formáte YYYYMMDD (dátum v USA)."""
    r = requests.get(URL, params={"dates": day}, timeout=30)
    r.raise_for_status()
    return r.json()
