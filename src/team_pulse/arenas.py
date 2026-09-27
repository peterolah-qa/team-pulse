"""Arény: poloha, časové pásmo a nadmorská výška podľa teamu a sezóny.

Presťahované franšízy majú viac riadkov (napr. OKC = Seattle do 2008, potom Oklahoma City).
"""

from __future__ import annotations

import math
from functools import cache, lru_cache
from pathlib import Path
from typing import NamedTuple

import pandas as pd

CSV = Path(__file__).with_name("arenas.csv")
EARTH_RADIUS_KM = 6371.0


class Arena(NamedTuple):
    city: str
    lat: float
    lon: float
    utc_offset: int
    altitude_m: int


@lru_cache(maxsize=1)
def table() -> pd.DataFrame:
    return pd.read_csv(CSV)


@cache
def location(team: str, season: int) -> Arena:
    t = table()
    row = t[(t["team"] == team) & (t["from_season"] <= season) & (t["to_season"] >= season)]
    if len(row) != 1:
        raise KeyError(f"žiadna (alebo viac) aréna pre {team} v sezóne {season}")
    r = row.iloc[0]
    return Arena(r["city"], float(r["lat"]), float(r["lon"]), int(r["utc_offset"]), int(r["altitude_m"]))


# zápasy základnej časti na neutrálnej pôde (NBA Global Games, Mexiko)
NEUTRAL_SITES = {
    "Mexico City": Arena("Mexico City", 19.404, -99.096, -6, 2240),
    "Paris": Arena("Paris", 48.839, 2.378, 1, 35),
    "London": Arena("London", 51.508, 0.003, 0, 10),
    "Manchester": Arena("Manchester", 53.488, -2.244, 0, 40),
    "Berlin": Arena("Berlin", 52.507, 13.443, 1, 35),
    "Abu Dhabi": Arena("Abu Dhabi", 24.470, 54.600, 4, 5),
}


def neutral_site(city: str | None) -> Arena | None:
    return NEUTRAL_SITES.get(city) if city else None


def distance_km(a: Arena, b: Arena) -> float:
    """Vzdušná vzdialenosť (haversine)."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))
