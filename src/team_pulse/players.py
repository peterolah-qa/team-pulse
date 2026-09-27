"""Vrstva B – dostupnosť hráčov.

Pre každý zápas a team vypočíta `missing` = koľko kvality teamu chýba:

    missing = Σ (očakávané minúty / 48) × (hodnota hráča − náhradník)   cez chýbajúcich hráčov

    hodnota hráča  PIE (Player Impact Estimate, oficiálny ukazovateľ NBA) z jeho
                   posledných 40 zápasov PRED týmto zápasom, mínus priemer 0,10
    očakávané min. priemer minút v posledných 10 zápasoch teamu (0, ak nehral)
    chýbajúci      hráč z rotácie teamu, ktorý v tomto zápase nenastúpil
    náhradník      úroveň náhradníka (PIE 0,07 → −0,03); slabší hráč než náhradník
                   sa počíta ako 0 (jeho absencia teamu nepomôže ani neuškodí)

Vlastnosti:
  * dlhodobá absencia sa sama „vyprchá“: po 10 zápasoch bez hráča sú jeho očakávané
    minúty 0, takže ho model už nepočíta (jeho absencia je už v Elo)
  * prestup: hráč, ktorý nastúpil za iný team, sa v starom teame nepočíta ako chýbajúci
  * nová sezóna: rotácia teamu sa vynuluje (odchody, draft, prestupy cez leto)

Sila súpisky (`strength`): súčet kvality hráčov, ktorí dnes nastúpili, vážený ich typickými
minútami z predchádzajúcich zápasov (aj za iný team). Rieši začiatok sezóny: Elo o letnom
prestupe hviezdy ešte nevie, súpiska áno.

Poznámka: kto nenastúpil, berieme z box score. V ostrej prevádzke to isté povie
oficiálny Injury Report pred zápasom – preto to nie je únik dát.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import pandas as pd

LEAGUE_AVG_PIE = 0.10
REPLACEMENT = 0.07 - LEAGUE_AVG_PIE
VALUE_WINDOW = 40  # zápasov hráča na výpočet hodnoty
MIN_GAMES = 5  # menej odohraných zápasov → hodnota = náhradník
ROTATION_WINDOW = 10  # zápasov teamu na očakávané minúty
CAREER_MIN_WINDOW = 20  # zápasov hráča (za akýkoľvek team) na jeho typické minúty
ROOKIE_MIN = 12.0  # hráč bez histórie
MAX_MIN = 40.0


def pie_parts(players: pd.DataFrame) -> pd.DataFrame:
    """Čitateľ PIE pre každého hráča a súčet za celý zápas (obe teamy)."""
    p = players.copy()
    p["pie_num"] = (
        p["pts"]
        + p["fgm"]
        + p["ftm"]
        - p["fga"]
        - p["fta"]
        + p["dreb"]
        + 0.5 * p["oreb"]
        + p["ast"]
        + p["stl"]
        + 0.5 * p["blk"]
        - p["pf"]
        - p["tov"]
    )
    p["pie_den"] = p.groupby("game_id")["pie_num"].transform("sum")
    return p


def player_values(players: pd.DataFrame) -> pd.DataFrame:
    """Hodnota hráča PO každom jeho zápase (z posledných 40 zápasov vrátane tohto).

    Používa sa až pre neskoršie zápasy, takže predpoveď nikdy nevidí aktuálny zápas.
    """
    p = pie_parts(players).sort_values(["date", "game_id"], kind="stable")
    g = p.groupby("player_id", sort=False)
    num = g["pie_num"].transform(lambda s: s.rolling(VALUE_WINDOW, min_periods=1).sum())
    den = g["pie_den"].transform(lambda s: s.rolling(VALUE_WINDOW, min_periods=1).sum())
    n_games = g.cumcount() + 1
    pie = (num / den).where(n_games >= MIN_GAMES)
    p["value"] = (pie - LEAGUE_AVG_PIE).fillna(REPLACEMENT)
    return p


def missing_by_team_game(players: pd.DataFrame) -> pd.DataFrame:
    """Vráti riadok na (game_id, team): missing, n_missing, strength, games_played."""
    p = player_values(players)
    # pre chýbajúceho hráča použijeme hodnotu po jeho poslednom odohranom zápase
    last_value: dict[int, float] = {}
    current_team: dict[int, str] = {}
    rosters: dict[str, dict[int, deque[float]]] = {}
    team_season: dict[str, int] = {}
    career_min: dict[int, deque[float]] = {}
    team_games: dict[str, int] = {}
    rows = []

    for (_date, game_id, team), grp in p.groupby(["date", "game_id", "team"], sort=True):
        season = int(grp["season"].iat[0])
        if team_season.get(team) != season:
            rosters[team] = {}
            team_season[team] = season
            team_games[team] = 0
        roster = rosters[team]

        played = dict(zip(grp["player_id"], grp["min"], strict=True))
        missing = 0.0
        n_missing = 0
        for pid, mins in roster.items():
            if pid in played or current_team.get(pid) != team:
                continue
            expected = float(np.mean(mins))
            if expected <= 0:
                continue
            above_replacement = max(last_value.get(pid, REPLACEMENT) - REPLACEMENT, 0.0)
            missing += expected / 48 * above_replacement
            n_missing += 1
        strength = 0.0
        for pid in played:
            hist = career_min.get(pid)
            typical = min(float(np.mean(hist)) if hist else ROOKIE_MIN, MAX_MIN)
            strength += typical / 48 * max(last_value.get(pid, REPLACEMENT) - REPLACEMENT, 0.0)
        rows.append((game_id, team, missing, n_missing, strength, team_games[team]))
        team_games[team] += 1

        # aktualizácia po zápase
        for pid in list(roster):
            if pid not in played:
                roster[pid].append(0.0)
                if sum(roster[pid]) == 0:
                    del roster[pid]
        for pid, mins in played.items():
            roster.setdefault(pid, deque(maxlen=ROTATION_WINDOW)).append(float(mins))
            career_min.setdefault(pid, deque(maxlen=CAREER_MIN_WINDOW)).append(float(mins))
            current_team[pid] = team
        for pid, v in zip(grp["player_id"], grp["value"], strict=True):
            last_value[pid] = float(v)

    return pd.DataFrame(rows, columns=["game_id", "team", "missing", "n_missing", "strength", "games_played"])


def add_features(games: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Doplní k zápasom pre home_/away_: missing, n_missing, strength, games_played."""
    m = missing_by_team_game(players)
    cols = ["missing", "n_missing", "strength", "games_played"]
    out = games.copy()
    for side in ("home", "away"):
        mm = m.rename(columns={"team": side, **{c: f"{side}_{c}" for c in cols}})
        out = out.merge(mm, on=["game_id", side], how="left")
        for c in cols:
            out[f"{side}_{c}"] = out[f"{side}_{c}"].fillna(0)
    return out
