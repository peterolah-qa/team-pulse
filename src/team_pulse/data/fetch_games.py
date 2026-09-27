"""Stiahne výsledky NBA zápasov z nba_api a uloží ich ako jeden riadok na zápas.

Spustenie:  uv run python -m team_pulse.data.fetch_games --from 2001 --to 2026
(sezóna sa označuje rokom, v ktorom končí: 2025-26 = 2026)
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

OUT = Path("data/raw/games.parquet")
SEASON_TYPES = {"Regular Season": False, "Playoffs": True}
# COVID bublina v Orlande: bez divákov a cestovania → žiadna domáca výhoda
BUBBLE = (pd.Timestamp("2020-07-30"), pd.Timestamp("2020-10-11"))


def season_label(end_year: int) -> str:
    """2026 -> '2025-26' (formát, ktorý chce nba_api)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def current_abbr() -> dict[int, str]:
    """TEAM_ID -> dnešná skratka (SEA a OKC majú rovnaké ID, takže rating sa prenesie)."""
    from nba_api.stats.static import teams

    return {t["id"]: t["abbreviation"] for t in teams.get_teams()}


def fix_franchise(team: str, end_year: int) -> str:
    """NBA v roku 2014 pripísala históriu Charlotte Hornets (1988–2002) dnešnému Charlotte (CHA).
    Pre model je však team z rokov 2001–2002 ten istý, ktorý sa v 2002 presťahoval do New Orleans."""
    return "NOP" if team == "CHA" and end_year <= 2002 else team


def normalize(raw: pd.DataFrame, end_year: int, playoff: bool, abbr: dict[int, str]) -> pd.DataFrame:
    """Z dvoch riadkov na zápas (jeden za každý team) urobí jeden riadok domáci vs. hostia."""
    df = raw.copy()
    df["is_home"] = df["MATCHUP"].str.contains(" vs. ", regex=False)
    home = df[df["is_home"]].set_index("GAME_ID")
    away = df[~df["is_home"]].set_index("GAME_ID")
    both = home.index.intersection(away.index)
    home, away = home.loc[both], away.loc[both]
    out = pd.DataFrame(
        {
            "game_id": both,
            "date": pd.to_datetime(home["GAME_DATE"]).values,
            "season": end_year,
            "playoff": playoff,
            "home": home["TEAM_ID"].map(abbr).fillna(home["TEAM_ABBREVIATION"]).values,
            "away": away["TEAM_ID"].map(abbr).fillna(away["TEAM_ABBREVIATION"]).values,
            "pts_home": home["PTS"].astype(int).values,
            "pts_away": away["PTS"].astype(int).values,
        }
    )
    out["home"] = [fix_franchise(t, end_year) for t in out["home"]]
    out["away"] = [fix_franchise(t, end_year) for t in out["away"]]
    return out.sort_values(["date", "game_id"]).reset_index(drop=True)


def mark_neutral(games: pd.DataFrame) -> pd.DataFrame:
    """Označí zápasy bez domácej výhody (bublina 2020)."""
    out = games.copy()
    out["neutral"] = out["date"].between(*BUBBLE)
    return out


def fetch_season(end_year: int, season_type: str, retries: int = 3) -> pd.DataFrame:
    from nba_api.stats.endpoints import leaguegamefinder

    for attempt in range(1, retries + 1):
        try:
            r = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_label(end_year),
                league_id_nullable="00",
                season_type_nullable=season_type,
                timeout=60,
            )
            return r.get_data_frames()[0]
        except Exception as e:  # sieť, timeout, dočasná blokácia
            if attempt == retries:
                raise
            wait = 5 * attempt
            print(f"  chyba ({e.__class__.__name__}), skúšam znova o {wait} s")
            time.sleep(wait)
    raise RuntimeError("nedosiahnuteľné")


def main(first: int, last: int, out: Path = OUT) -> pd.DataFrame:
    abbr = current_abbr()
    parts = []
    for year in range(first, last + 1):
        for stype, playoff in SEASON_TYPES.items():
            raw = fetch_season(year, stype)
            if raw.empty:
                continue
            games = normalize(raw, year, playoff, abbr)
            parts.append(games)
            print(f"{season_label(year)} {stype:<14} {len(games):>5} zápasov")
            time.sleep(1.0)  # šetrný limit na stats.nba.com
    all_games = pd.concat(parts, ignore_index=True).sort_values(["date", "game_id"]).reset_index(drop=True)
    all_games = mark_neutral(all_games)
    out.parent.mkdir(parents=True, exist_ok=True)
    all_games.to_parquet(out, index=False)
    print(f"\nUložené: {out}  ({len(all_games)} zápasov, {all_games['home'].nunique()} teamov)")
    return all_games


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2001)
    ap.add_argument("--to", dest="last", type=int, default=2026)
    a = ap.parse_args()
    main(a.first, a.last)
