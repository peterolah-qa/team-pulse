"""Vrstva C pre NHL – príznaky únavy z rozpisu zápasov.

Pre každý zápas a každý klub (domáci aj hostia):
    rest      dni od posledného zápasu v sezóne (1 = back-to-back, najviac 7)
    b2b       2. zápas za 2 dni
    three_in4 3. zápas za 4 dni
    tz_east   posun o časové pásma na východ od posledného zápasu (hodiny), ťažší smer
    road      poradie zápasu na aktuálnom výjazde (0 = doma)

Len dátumy a miesta zápasov, nie výsledky → rozpis je známy vopred, žiadny únik z budúcnosti.
Neutrálny ľad (Európa, bublina 2020) nemá známe pásmo: posun sa tam nepočíta a nikto nie je na výjazde.
"""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd

MAX_REST = 7
MAX_TZ = 3

# Časové pásmo haly podľa skratky v čase zápasu (štandardný čas, UTC). Arizona nemá letný čas,
# rozdiel 1 h pol roka zanedbávame. ATL, PHX a ARI sú zaniknuté skratky.
UTC_OFFSET = {
    **dict.fromkeys(
        ["BOS", "BUF", "CAR", "CBJ", "DET", "FLA", "MTL", "NJD", "NYI", "NYR", "OTT", "PHI", "PIT", "TBL",
         "TOR", "WSH", "ATL"], -5),
    **dict.fromkeys(["CHI", "DAL", "MIN", "NSH", "STL", "WPG"], -6),
    **dict.fromkeys(["CGY", "COL", "EDM", "UTA", "PHX", "ARI"], -7),
    **dict.fromkeys(["ANA", "LAK", "SJS", "SEA", "VAN", "VGK"], -8),
}  # fmt: skip

FEATURES = ["rest", "b2b", "three_in4", "tz_east", "road"]


class _State(NamedTuple):
    season: int
    day: pd.Timestamp
    offset: int | None  # pásmo posledného zápasu, None = neutrálny ľad
    road: int
    recent: tuple[pd.Timestamp, ...]


def add_features(games: pd.DataFrame) -> pd.DataFrame:
    """Zápasy chronologicky, doplnené o stĺpce home_<príznak> a away_<príznak>.

    Očakávané stĺpce: game_id, season, date, home, away, home_abbr, [start_utc], [neutral]
    (home/away = klub pre Elo, home_abbr = skratka v čase zápasu kvôli mestu).
    """
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    g = games.sort_values(order, kind="stable").reset_index(drop=True).copy()
    neutral = g["neutral"].astype(bool).to_numpy() if "neutral" in g else [False] * len(g)
    days = pd.to_datetime(g["date"]).dt.normalize()
    last: dict[str, _State] = {}
    cols: dict[str, list[int]] = {f"{s}_{f}": [] for s in ("home", "away") for f in FEATURES}

    for i, r in enumerate(g.itertuples(index=False)):
        nt = bool(neutral[i])
        day = days.iat[i]
        here = None if nt else UTC_OFFSET[r.home_abbr]
        for side, team in (("home", r.home), ("away", r.away)):
            prev = last.get(team)
            same = prev is not None and prev.season == r.season
            if same:
                rest = min((day - prev.day).days, MAX_REST)
                recent = tuple(d for d in prev.recent if (day - d).days <= 3)
                moved = here is not None and prev.offset is not None
                tz_east = min(max(here - prev.offset, 0), MAX_TZ) if moved else 0
            else:
                rest, recent, tz_east = MAX_REST, (), 0
            on_road = side == "away" and not nt
            road = ((prev.road + 1) if same and prev.road > 0 else 1) if on_road else 0
            values = {"rest": rest, "b2b": int(rest == 1), "three_in4": int(len(recent) >= 2),
                      "tz_east": tz_east, "road": road}  # fmt: skip
            for f in FEATURES:
                cols[f"{side}_{f}"].append(values[f])
            last[team] = _State(r.season, day, here, road, recent + (day,))

    for c, v in cols.items():
        g[c] = v
    return g
