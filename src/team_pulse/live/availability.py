"""Vrstva B naživo: kto dnes chýba a aká silná je dostupná súpiska.

V backteste sme to brali z box score (kto nenastúpil). Naživo to isté skladáme z:
  * aktuálnych súpisiek (live.roster) a Injury Reportu ESPN (live.injuries),
  * histórie hráčov (hodnota PIE a typické minúty) – rovnaké výpočty ako pri učení.

Výstup pre každý team: missing, strength (v rovnakých jednotkách ako pri učení)
a zoznam chýbajúcich hráčov s dopadom (na dôvody „prečo“ v appke).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from team_pulse.players import (
    CAREER_MIN_WINDOW,
    MAX_MIN,
    REPLACEMENT,
    ROOKIE_MIN,
    ROTATION_WINDOW,
    player_values,
)

TOP_N = 11  # pri učení sa sila rátala z hráčov, ktorí nastúpili – v NBA typicky 10–12 na zápas


@dataclass
class Snapshot:
    value: dict[int, float]  # hodnota po poslednom zápase (PIE − 0,10)
    typical_min: dict[int, float]  # priemer minút z posledných 20 zápasov
    current_team: dict[int, str]  # team z posledného zápasu
    name: dict[int, str] = field(default_factory=dict)


def player_snapshot(players: pd.DataFrame) -> Snapshot:
    p = player_values(players)
    last = p.groupby("player_id").tail(1).set_index("player_id")
    typical = p.groupby("player_id")["min"].apply(lambda s: s.tail(CAREER_MIN_WINDOW).mean())
    names = last["player"].to_dict() if "player" in last else {}
    return Snapshot(last["value"].to_dict(), typical.to_dict(), last["team"].to_dict(), names)


def season_rotation(players: pd.DataFrame, season: int) -> dict[str, dict[int, float]]:
    """Očakávané minúty hráčov z posledných 10 zápasov teamu v tejto sezóne (0, ak nehral).

    Ako pri učení: počíta sa od prvého zápasu hráča za team (čerstvá posila nemá nuly
    za zápasy pred príchodom) a hráč, ktorý medzitým hral za iný team, sa nepočíta.
    """
    current = players.sort_values(["date", "game_id"]).groupby("player_id")["team"].last()
    s = players[players["season"] == season]
    out: dict[str, dict[int, float]] = {}
    for team, grp in s.groupby("team"):
        order = grp.drop_duplicates("game_id").sort_values("date")["game_id"].tolist()
        window = order[-ROTATION_WINDOW:]
        idx = {g: i for i, g in enumerate(order)}
        grp = grp.assign(order_idx=grp["game_id"].map(idx))
        first = grp.groupby("player_id")["order_idx"].min()
        mins = grp[grp["game_id"].isin(window)].groupby("player_id")["min"].sum()
        rot = {}
        for pid, total in mins.items():
            if current.get(pid) != team or total <= 0:
                continue
            games_with_team = sum(1 for g in window if idx[g] >= first[pid])
            rot[int(pid)] = float(total) / max(games_with_team, 1)
        out[team] = rot
    return out


def _above_replacement(pid: int, snap: Snapshot) -> float:
    return max(snap.value.get(pid, REPLACEMENT) - REPLACEMENT, 0.0)


def team_availability(
    team: str,
    roster_ids: set[int],
    p_out: dict[int, float],
    snap: Snapshot,
    rotation: dict[str, dict[int, float]],
    top_n: int = TOP_N,
) -> dict:
    """missing, strength a zoznam chýbajúcich (hráč, pravdepodobnosť výpadku, dopad)."""
    rot = rotation.get(team, {})
    missing, absent = 0.0, []
    for pid, exp_min in rot.items():
        p = 1.0 if pid not in roster_ids else p_out.get(pid, 0.0)  # z rotácie odišiel → chýba
        if p <= 0:
            continue
        impact = exp_min / 48 * _above_replacement(pid, snap)
        missing += p * impact
        name = snap.name.get(pid, str(pid))
        absent.append({"player_id": pid, "player": name, "p_out": p, "impact": impact})

    expected = {}
    for pid in roster_ids:
        typical = snap.typical_min.get(pid, ROOKIE_MIN)
        expected[pid] = min(typical, MAX_MIN) * (1 - p_out.get(pid, 0.0))
    top = sorted(expected, key=expected.get, reverse=True)[:top_n]
    strength = sum(expected[pid] / 48 * _above_replacement(pid, snap) for pid in top)
    # zranení zo súpisky (aj mimo rotácie tejto sezóny, napr. na jej začiatku) – na texty dôvodov
    listed = {a["player_id"] for a in absent}
    for pid in roster_ids:
        p = p_out.get(pid, 0.0)
        if p > 0 and pid not in listed:
            impact = min(snap.typical_min.get(pid, ROOKIE_MIN), MAX_MIN) / 48 * _above_replacement(pid, snap)
            name = snap.name.get(pid, str(pid))
            absent.append({"player_id": pid, "player": name, "p_out": p, "impact": impact})
    absent = [a for a in absent if a["impact"] > 0]
    absent.sort(key=lambda a: a["p_out"] * a["impact"], reverse=True)
    return {"missing": missing, "strength": strength, "absent": absent}


def p_out_for_game(injuries: pd.DataFrame, game_date: pd.Timestamp) -> dict[int, float]:
    """Spárované zranenia → player_id: pravdepodobnosť výpadku v daný deň.

    Ak má hráč očakávaný návrat až po zápase, je OUT bez ohľadu na stav (pred sezónou
    ESPN označuje takmer všetkých ako day-to-day).
    """
    out: dict[int, float] = {}
    for r in injuries.dropna(subset=["player_id"]).itertuples():
        p = float(r.p_out)
        if pd.notna(r.return_date) and r.return_date.normalize() > game_date.normalize():
            p = 1.0
        out[int(r.player_id)] = max(p, out.get(int(r.player_id), 0.0))
    return out
