"""Súpisky aktuálnej sezóny a párovanie mien hráčov ESPN ↔ nba_api.

ESPN pozná hráča menom („Nikola Jokić“, „Jaren Jackson Jr.“), náš model podľa player_id
z nba_api. Párujeme podľa normalizovaného mena v rámci teamu, potom bez teamu
(čerstvý prestup, ESPN ešte nemá aktuálny team), nakoniec podľa priezviska + iniciály
(„Herb Jones“ = „Herbert Jones“).

Spustenie (z Macu):  uv run python -m team_pulse.live.roster
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROSTER = Path("data/live/roster.parquet")
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_name(name: str) -> str:
    """'Nikola Jokić' → 'nikola jokic', 'P.J. Washington Jr.' → 'pj washington'."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", "").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z ]+", " ", s)
    parts = [p for p in s.split() if p not in SUFFIXES]
    return " ".join(parts)


def _initial_last(norm: str) -> str:
    parts = norm.split()
    return f"{parts[0][0]} {parts[-1]}" if len(parts) >= 2 else norm


def parse_roster(raw: pd.DataFrame, abbr: dict[int, str]) -> pd.DataFrame:
    """Výstup CommonAllPlayers → player_id, player, team (len hráči v teame)."""
    df = raw[raw["TEAM_ID"].astype(int) != 0].copy()
    pairs = zip(df["TEAM_ID"], df["TEAM_ABBREVIATION"], strict=True)
    out = pd.DataFrame(
        {
            "player_id": df["PERSON_ID"].astype(int),
            "player": df["DISPLAY_FIRST_LAST"],
            "team": [abbr.get(int(t), a) for t, a in pairs],
        }
    )
    out["norm"] = out["player"].map(normalize_name)
    return out.reset_index(drop=True)


def match_injuries(injuries: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    """Doplní k zraneniam player_id a spôsob párovania (team / name / initial / None)."""
    inj = injuries.copy()
    inj["norm"] = inj["player"].map(normalize_name)
    by_team = {(r.team, r.norm): r.player_id for r in roster.itertuples()}
    name_counts = roster["norm"].value_counts()
    by_name = {r.norm: r.player_id for r in roster.itertuples() if name_counts[r.norm] == 1}
    roster_il = roster.assign(il=roster["norm"].map(_initial_last))
    il_counts = roster_il.groupby(["team", "il"]).size()
    by_initial = {
        (r.team, r.il): r.player_id for r in roster_il.itertuples() if il_counts[(r.team, r.il)] == 1
    }

    ids, methods = [], []
    for r in inj.itertuples():
        if (r.team, r.norm) in by_team:
            ids.append(by_team[(r.team, r.norm)])
            methods.append("team")
        elif r.norm in by_name:
            ids.append(by_name[r.norm])
            methods.append("name")
        elif (r.team, _initial_last(r.norm)) in by_initial:
            ids.append(by_initial[(r.team, _initial_last(r.norm))])
            methods.append("initial")
        else:
            ids.append(None)
            methods.append(None)
    inj["player_id"] = pd.array(ids, dtype="Int64")
    inj["match"] = methods
    return inj.drop(columns="norm")


def fetch_roster(season: str = "2026-27") -> pd.DataFrame:
    from nba_api.stats.endpoints import commonallplayers

    from team_pulse.data.fetch_games import current_abbr

    raw = commonallplayers.CommonAllPlayers(
        is_only_current_season=1, league_id="00", season=season, timeout=60
    ).get_data_frames()[0]
    return parse_roster(raw, current_abbr())


def main() -> None:
    from team_pulse.live.injuries import fetch_injuries, parse_injuries

    roster = fetch_roster()
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    roster.to_parquet(ROSTER, index=False)
    print(f"Súpisky: {len(roster)} hráčov v {roster['team'].nunique()} teamoch → {ROSTER}")

    inj = match_injuries(parse_injuries(fetch_injuries()), roster)
    ok = inj["player_id"].notna()
    print(f"Zranenia spárované: {ok.sum()} / {len(inj)} ({ok.mean():.0%})")
    print("Spôsob párovania:", inj["match"].value_counts(dropna=False).to_dict())
    if (~ok).any():
        print("\nNespárovaní (zvyčajne nováčikovia bez zmluvy alebo two-way hráči):")
        print(inj.loc[~ok, ["team", "player", "status"]].to_string(index=False))
    print(json.dumps({"roster": len(roster), "matched": int(ok.sum()), "total": len(inj)}))


if __name__ == "__main__":
    main()
