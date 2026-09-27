"""Vrstva C – príznaky únavy z rozpisu zápasov.

Pre každý zápas a každý team (domáci aj hostia) vypočíta:
    rest      dni od posledného zápasu (1 = back-to-back, max. 7)
    b2b       2. zápas za 2 dni
    three_in4 3. zápas za 4 dni
    km        cestovanie od posledného zápasu (vzdušnou čiarou)
    tz_east   posun o časové pásma na východ (hodiny), ťažší smer
    road      poradie zápasu na aktuálnom výjazde (0 = doma)
    altitude  hosť z nízko položeného mesta hrá vo výške nad 1000 m

Používa len dátumy a miesta zápasov, nie výsledky → rozpis je známy vopred,
žiadny únik dát z budúcnosti.
"""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd

from team_pulse.arenas import Arena, distance_km, location

MAX_REST = 7
HIGH_ALTITUDE_M = 1000
BUBBLE_HOST = "ORL"  # zápasy bubliny 2020 sa hrali pri Orlande

FEATURES = ["rest", "b2b", "three_in4", "km", "tz_east", "road", "altitude"]


class _State(NamedTuple):
    season: int
    date: pd.Timestamp
    where: Arena
    road: int
    recent: tuple[pd.Timestamp, ...]


def game_location(home: str, season: int, neutral: bool) -> Arena:
    return location(BUBBLE_HOST if neutral else home, season)


def add_features(games: pd.DataFrame) -> pd.DataFrame:
    """Vráti zápasy (chronologicky) doplnené o stĺpce home_<príznak> a away_<príznak>."""
    g = games.sort_values(["date"], kind="stable").reset_index(drop=True).copy()
    neutral = g["neutral"].astype(bool) if "neutral" in g else pd.Series(False, index=g.index)
    last: dict[str, _State] = {}
    cols: dict[str, list[float]] = {f"{s}_{f}": [] for s in ("home", "away") for f in FEATURES}

    for i, r in enumerate(g.itertuples(index=False)):
        nt = bool(neutral.iat[i])
        where = game_location(r.home, r.season, nt)
        updates = {}
        for side, team in (("home", r.home), ("away", r.away)):
            prev = last.get(team)
            same_season = prev is not None and prev.season == r.season
            if same_season:
                rest = min((r.date - prev.date).days, MAX_REST)
                km = distance_km(prev.where, where)
                tz_east = max(where.utc_offset - prev.where.utc_offset, 0)
                recent = tuple(d for d in prev.recent if (r.date - d).days <= 3)
            else:
                rest, km, tz_east, recent = MAX_REST, 0.0, 0, ()
            is_road = side == "away" and not nt
            road = (prev.road + 1 if same_season and prev.road > 0 else 1) if is_road else 0
            base = location(team, r.season)
            high_here = where.altitude_m > HIGH_ALTITUDE_M
            altitude = int(is_road and high_here and base.altitude_m < HIGH_ALTITUDE_M)

            values = {
                "rest": rest,
                "b2b": int(rest == 1),
                "three_in4": int(len(recent) >= 2),
                "km": km,
                "tz_east": tz_east,
                "road": road,
                "altitude": altitude,
            }
            for f in FEATURES:
                cols[f"{side}_{f}"].append(values[f])
            updates[team] = _State(r.season, r.date, where, road, recent + (r.date,))
        last.update(updates)

    for c, v in cols.items():
        g[c] = v
    return g
