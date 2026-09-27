"""Adaptér: rozpis sezóny z nba_api (ScheduleLeagueV2).

Beží z Macu (stats.nba.com blokuje cloudové IP). Rozpis sa mení zriedka → stačí raz denne.
"""

from __future__ import annotations

import pandas as pd

from team_pulse.live.teams import our_teams

# prvé 3 číslice gameId: 001 príprava, 002 základná časť, 003 All-Star,
# 004 playoff, 005 play-in, 006 finále NBA Cup
COUNTED_TYPES = {"002": "regular", "004": "playoff", "005": "play-in", "006": "cup-final"}


def season_end_year(season_year: str) -> int:
    """'2026-27' → 2027 (rovnaké označenie ako v historických dátach)."""
    start = int(season_year.split("-")[0])
    return start + 1


def parse_schedule(data: dict, include_preseason: bool = False) -> pd.DataFrame:
    ls = data["leagueSchedule"]
    season = season_end_year(ls["seasonYear"])
    teams = our_teams()
    rows = []
    for day in ls["gameDates"]:
        for g in day["games"]:
            kind = COUNTED_TYPES.get(g["gameId"][:3], "preseason" if g["gameId"].startswith("001") else None)
            if kind is None or (kind == "preseason" and not include_preseason):
                continue
            home, away = g["homeTeam"]["teamTricode"], g["awayTeam"]["teamTricode"]
            if home not in teams or away not in teams:
                continue  # zápasy proti zahraničným klubom v príprave
            rows.append(
                {
                    "game_id": g["gameId"],
                    "date": pd.Timestamp(g["gameDateEst"][:10]),  # dátum v USA (ET), ako v histórii
                    "tipoff_utc": pd.Timestamp(g["gameDateTimeUTC"]),
                    "season": season,
                    "kind": kind,
                    "home": home,
                    "away": away,
                    "neutral": bool(g.get("isNeutral", False)),
                    "arena_city": g.get("arenaCity", ""),
                    "status": int(g.get("gameStatus", 1)),  # 1 naplánovaný, 2 hrá sa, 3 skončený
                    "pts_home": int(g["homeTeam"].get("score") or 0),
                    "pts_away": int(g["awayTeam"].get("score") or 0),
                }
            )
    cols = ["game_id", "date", "tipoff_utc", "season", "kind", "home", "away", "neutral"]
    cols += ["arena_city", "status", "pts_home", "pts_away"]
    return pd.DataFrame(rows, columns=cols).sort_values(["tipoff_utc", "game_id"]).reset_index(drop=True)


def fetch_schedule(season_label: str = "2026-27") -> dict:
    from nba_api.stats.endpoints import scheduleleaguev2

    return scheduleleaguev2.ScheduleLeagueV2(league_id="00", season=season_label, timeout=60).get_dict()
