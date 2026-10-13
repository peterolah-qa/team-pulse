"""Vrstva G pre NHL – kvalita brankára pred zápasom.

Kvalita brankára = o koľko gólov na zápas chytá viac než priemerný brankár ligy, len z jeho
predchádzajúcich zápasov:

    q = (zákroky + PRIOR · ligové %) / (strely + PRIOR) − ligové %   →   × SHOTS gólov na zápas

Staršie zápasy majú menšiu váhu (DECAY na každý ďalší zápas brankára). PRIOR stiahne brankára
s málo strelami k priemeru (nováčik ani náhradník nie je hneď zázrak ani katastrofa).
Ligové % zákrokov = celá predchádzajúca sezóna (v prvej sezóne dát jej vlastný priemer, tá sa nehodnotí).

Pre každý zápas a klub dva príznaky:
    expected  vážený priemer brankárov klubu podľa podielu štartov v posledných LAST zápasoch
              → dá sa spočítať VŽDY pred zápasom (netreba vedieť, kto chytá)
    known     brankár, ktorý naozaj začal → funguje len vtedy, keď štartujúceho poznáme pred zápasom
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque

import pandas as pd

PRIOR = 1500.0  # strel „priemerného brankára“, ku ktorým sa výkon sťahuje
DECAY = 0.99  # váha zápasu spred 100 zápasov brankára ≈ 0,37
SHOTS = 30.0  # strely na zápas (prepočet % zákrokov na góly)
LAST = 10  # koľko posledných zápasov klubu rozhoduje o tom, kto je jednotka
DOUBLE = -1  # klub nemá v dátach práve jedného, kto začal (chýba alebo sú dvaja)


def league_save_pct(goalies: pd.DataFrame) -> dict[int, float]:
    """% zákrokov ligy použité v sezóne s: celá sezóna s − 1 (prvá sezóna: vlastná)."""
    by = goalies.groupby("season")[["saves", "shots_against"]].sum()
    pct = (by["saves"] / by["shots_against"]).to_dict()
    seasons = sorted(pct)
    return {s: pct[seasons[i - 1]] if i else pct[s] for i, s in enumerate(seasons)}


def add_features(games: pd.DataFrame, goalies: pd.DataFrame) -> pd.DataFrame:
    """Doplní home_goalie_expected/known a away_goalie_expected/known (góly na zápas nad priemer).

    Zápasy aj brankári idú chronologicky; príznak zápasu sa spočíta pred tým, než sa doň započíta výkon.
    """
    order = ["start_utc" if "start_utc" in games else "date", "game_id"]
    g = games.sort_values(order, kind="stable").reset_index(drop=True).copy()
    league = league_save_pct(goalies)
    starter: dict[tuple[int, str], int] = {}
    played: dict[int, list[tuple[int, str, bool, int, int]]] = defaultdict(list)
    for x in goalies.itertuples(index=False):
        played[x.game_id].append((x.player_id, x.team, bool(x.started), x.saves, x.shots_against))
    for gid, rows in played.items():
        for pid, team, started, _, _ in rows:
            if started:  # dvaja „začínajúci“ v jednom klube = chyba dát
                starter[(gid, team)] = DOUBLE if (gid, team) in starter else pid
    saves: dict[int, float] = defaultdict(float)
    shots: dict[int, float] = defaultdict(float)
    recent: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=LAST))
    cols: dict[str, list[float]] = {
        f"{s}_goalie_{k}": [] for s in ("home", "away") for k in ("expected", "known")
    }
    known_ok: list[bool] = []

    def quality(pid: int, lg: float) -> float:
        return ((saves[pid] + PRIOR * lg) / (shots[pid] + PRIOR) - lg) * SHOTS

    for r in g.itertuples(index=False):
        lg = league.get(r.season, 0.905)
        ok = True
        for side, team in (("home", r.home), ("away", r.away)):
            starts = recent[team]
            expected = (
                sum(n * quality(pid, lg) for pid, n in Counter(starts).items()) / len(starts)
                if starts
                else 0.0
            )
            pid = starter.get((r.game_id, team), DOUBLE)
            ok = ok and pid != DOUBLE
            cols[f"{side}_goalie_expected"].append(expected)
            cols[f"{side}_goalie_known"].append(quality(pid, lg) if pid != DOUBLE else expected)
        known_ok.append(ok)
        for pid, team, started, sv, sh in played.get(r.game_id, ()):  # až po zápase: výkon a kto začal
            saves[pid] = saves[pid] * DECAY + sv
            shots[pid] = shots[pid] * DECAY + sh
            if started:
                recent[team].append(pid)

    for c, v in cols.items():
        g[c] = v
    g["goalie_expected_diff"] = g["home_goalie_expected"] - g["away_goalie_expected"]
    g["goalie_known_diff"] = g["home_goalie_known"] - g["away_goalie_known"]
    g["goalie_known_ok"] = known_ok  # oba kluby majú v dátach práve jedného, kto začal
    return g
