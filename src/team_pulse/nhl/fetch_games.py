"""Stiahne históriu zápasov NHL z verejného API (api-web.nhle.com) – jeden riadok na zápas.

Zdroj: rozpis sezóny každého klubu (club-schedule-season). Zápas je v rozpise oboch klubov,
spojí sa podľa game_id. Pýtame sa aj na zaniknuté skratky (ATL, PHX, ARI): bez nich chýba
zápas, v ktorom hrali dva zaniknuté kluby proti sebe (ATL – PHX, raz za sezónu do 2010/11).

Kontrola úplnosti: počet zápasov základnej časti v rozpise musí presne sedieť (EXPECTED_REGULAR)
a odohraté sezóny musia mať všetky zápasy dohraté. Inak sa nič neuloží.

Spustenie (z Macu):  uv run python -m team_pulse.nhl.fetch_games --from 2006 --to 2026
(sezóna = rok, v ktorom končí: 2025/26 = 2026)
Výstup:             data/raw/nhl_games.parquet (necommituje sa)
"""

from __future__ import annotations

import argparse
import time
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

OUT = Path("data/raw/nhl_games.parquet")
ET = ZoneInfo("America/New_York")
URL = "https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}"

CURRENT = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", "FLA", "LAK", "MIN",
    "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA",
    "VAN", "VGK", "WPG", "WSH",
]  # fmt: skip
DEFUNCT = ["ATL", "PHX", "ARI"]
# Presťahované kluby: rating pokračuje pod dnešnou skratkou (hráči a súpiska išli s nimi).
FRANCHISE = {"ATL": "WPG", "PHX": "UTA", "ARI": "UTA"}

GAME_TYPES = {2: "R", 3: "P"}  # základná časť, playoff (príprava a All-Star sa vynechajú)
FINISHED = {"OFF", "FINAL"}
COLUMNS = [
    "game_id", "season", "game_type", "date", "start_utc", "home_abbr", "away_abbr",
    "goals_home", "goals_away", "state", "last_period", "neutral",
]  # fmt: skip

# Zápasy základnej časti podľa rozpisu ligy (30 teamov × 82 / 2 = 1230 …).
EXPECTED_REGULAR = {
    **dict.fromkeys(range(2006, 2013), 1230),
    2013: 720,  # výluka: 48 zápasov na team
    **dict.fromkeys(range(2014, 2018), 1230),
    2018: 1271,  # Vegas: 31 teamov
    2019: 1271,
    2020: 1082,  # COVID: sezóna prerušená, zvyšok zrušený
    2021: 868,  # COVID: 56 zápasov na team
    **dict.fromkeys(range(2022, 2027), 1312),  # Seattle: 32 teamov
    2027: 1344,  # 84 zápasov na team
}


def season_id(end_year: int) -> str:
    """2026 → '20252026' (formát API)."""
    return f"{end_year - 1}{end_year}"


def season_label(end_year: int) -> str:
    """2026 → '2025/26'."""
    return f"{end_year - 1}/{str(end_year)[-2:]}"


def today_et(now: datetime | None = None) -> date:
    """Dnešný deň v USA (ET): dátumy zápasov NHL sú podľa ET."""
    return (now or datetime.now(UTC)).astimezone(ET).date()


def season_of(day: date) -> int:
    """Sezóna = rok, v ktorom končí. Nová sezóna NHL začína v septembri/októbri."""
    return day.year + 1 if day.month >= 8 else day.year


def franchise(abbr: str) -> str:
    return FRANCHISE.get(abbr, abbr)


def parse_game(g: dict) -> dict:
    """Jeden zápas z rozpisu klubu → riadok. Skóre je prázdne, kým sa zápas nedohrá."""
    home, away = g["homeTeam"], g["awayTeam"]
    return {
        "game_id": int(g["id"]),
        "season": int(str(g["season"])[4:]),
        "game_type": GAME_TYPES.get(int(g["gameType"])),
        "date": g["gameDate"],
        "start_utc": g.get("startTimeUTC"),
        "home_abbr": home["abbrev"],
        "away_abbr": away["abbrev"],
        "goals_home": home.get("score"),
        "goals_away": away.get("score"),
        "state": g.get("gameState"),
        "last_period": (g.get("gameOutcome") or {}).get("lastPeriodType"),
        "neutral": bool(g.get("neutralSite", False)),
    }


def season_frame(raw_games: list[dict]) -> pd.DataFrame:
    """Zápasy zo všetkých rozpisov klubov jednej sezóny: bez duplicít, len základná časť a playoff."""
    by_id: dict[int, dict] = {}
    for g in raw_games:
        row = parse_game(g)
        if row["game_type"] is None:
            continue
        old = by_id.get(row["game_id"])
        if old is None or (old["state"] not in FINISHED and row["state"] in FINISHED):
            by_id[row["game_id"]] = row
    df = pd.DataFrame(list(by_id.values()), columns=COLUMNS)
    return df.sort_values(["start_utc", "game_id"], kind="stable").reset_index(drop=True)


def check_complete(df: pd.DataFrame, end_year: int, finished_season: bool) -> None:
    """Rozpis musí mať presne toľko zápasov základnej časti ako liga.

    Odohratá sezóna musí byť celá dohraná (rozohratá sa kontroluje len podľa rozpisu)."""
    regular = df[df["game_type"] == "R"]
    expected = EXPECTED_REGULAR.get(end_year)
    if expected is None:
        raise ValueError(f"{season_label(end_year)}: nepoznám počet zápasov, doplň EXPECTED_REGULAR")
    if len(regular) != expected:
        raise ValueError(
            f"{season_label(end_year)}: v rozpise je {len(regular)} zápasov základnej časti, "
            f"liga ich mala {expected}"
        )
    if finished_season:
        open_games = df[~df["state"].isin(FINISHED)]
        if len(open_games):
            ids = ", ".join(map(str, open_games["game_id"].head(5)))
            n = len(open_games)
            raise ValueError(f"{season_label(end_year)}: {n} zápasov nie je dohratých ({ids} …)")


def finished_games(df: pd.DataFrame) -> pd.DataFrame:
    """Dohraté zápasy so skóre a tímami pod dnešnou skratkou klubu (kvôli Elo)."""
    out = df[df["state"].isin(FINISHED) & df["goals_home"].notna() & df["goals_away"].notna()].copy()
    out["goals_home"] = out["goals_home"].astype(int)
    out["goals_away"] = out["goals_away"].astype(int)
    if (out["goals_home"] == out["goals_away"]).any():
        bad = out.loc[out["goals_home"] == out["goals_away"], "game_id"].tolist()
        raise ValueError(f"dohratý zápas bez víťaza: {bad[:5]}")
    out["home"] = out["home_abbr"].map(franchise)
    out["away"] = out["away_abbr"].map(franchise)
    out["date"] = pd.to_datetime(out["date"])
    return out.reset_index(drop=True)


def fetch_club(session: requests.Session, team: str, end_year: int, retries: int = 4) -> list[dict]:
    """Rozpis jedného klubu. Klub, ktorý v sezóne neexistoval, vráti prázdny zoznam (alebo 404)."""
    url = URL.format(team=team, season=season_id(end_year))
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json().get("games") or []
        except (requests.RequestException, ValueError) as e:
            if attempt == retries:
                raise RuntimeError(f"{team} {season_label(end_year)}: {e.__class__.__name__}: {e}") from e
            wait = 3 * attempt
            print(f"  {team}: chyba ({e.__class__.__name__}), skúšam znova o {wait} s")
            time.sleep(wait)
    return []


def fetch_season(session: requests.Session, end_year: int, pause: float = 0.25) -> pd.DataFrame:
    raw: list[dict] = []
    for team in CURRENT + DEFUNCT:
        raw.extend(fetch_club(session, team, end_year))
        time.sleep(pause)
    return season_frame(raw)


def summary(df: pd.DataFrame) -> str:
    reg = df[df["game_type"] == "R"]
    lp = reg["last_period"].value_counts()
    return (
        f"základná časť {len(reg):>4}  playoff {int((df['game_type'] == 'P').sum()):>3}  "
        f"(predĺženie {int(lp.get('OT', 0))}, nájazdy {int(lp.get('SO', 0))})"
    )


def main(first: int, last: int, out: Path = OUT, current: int | None = None) -> pd.DataFrame:
    """`current` = rozohratá sezóna (kontroluje sa len rozpis, uložia sa dohraté zápasy)."""
    session = requests.Session()
    parts = []
    for year in range(first, last + 1):
        df = fetch_season(session, year)
        check_complete(df, year, finished_season=year != current)
        done = finished_games(df)
        parts.append(done)
        print(f"{season_label(year)}  {summary(done)}")
    games = pd.concat(parts, ignore_index=True).sort_values(["start_utc", "game_id"], kind="stable")
    games = games.reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    games.to_parquet(out, index=False)
    print(f"\nUložené: {out}  ({len(games)} zápasov, {games['home'].nunique()} klubov)")
    return games


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2006)
    ap.add_argument("--to", dest="last", type=int, default=2026)
    ap.add_argument("--current", type=int, default=None, help="rozohratá sezóna, napr. 2027")
    a = ap.parse_args()
    main(a.first, a.last, current=a.current)
