"""Stiahne históriu F1 z Jolpica-F1 (api.jolpi.ca/ergast/f1) – jeden riadok na jazdca v pretekoch.

Zdroj: kalendár, výsledky pretekov, kvalifikácia Veľkej ceny a šprinty po celých sezónach
(stránky po 100 riadkov). Licencia CC BY-NC-SA 4.0: nekomerčne, s uvedením zdroja.
Limit 4 požiadavky/s a 500/h: medzi požiadavkami pauza, odpovede sa ukladajú do cache
(odjazdené sezóny sa už nesťahujú znova).

Kontrola úplnosti: každé odjazdené preteky z kalendára majú výsledky aj kvalifikáciu
a aspoň MIN_DRIVERS jazdcov. Inak sa nič neuloží.

Spustenie (z Macu):  uv run python -m team_pulse.f1.fetch --from 2014 --to 2026
Výstup:             data/raw/f1_results.parquet, data/raw/f1_sprints.parquet (necommitujú sa)
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.jolpi.ca/ergast/f1"
OUT = Path("data/raw/f1_results.parquet")
SPRINTS = Path("data/raw/f1_sprints.parquet")
CACHE = Path("data/raw/f1_cache")
PAGE = 100  # najviac, čo Jolpica vráti naraz
PAUSE = 0.3  # s medzi požiadavkami (limit 4/s)
MIN_DRIVERS = 18

TABLES = {"races": "Races", "results": "Races", "qualifying": "Races", "sprint": "Races"}

Getter = Callable[[str], dict]


def start_utc(day: str, clock: str | None) -> str:
    """'2026-10-25' + '20:00:00Z' → '2026-10-25T20:00:00Z'. Bez času poludnie (staré sezóny)."""
    return f"{day}T{(clock or '12:00:00Z').rstrip('Z')}Z"


def quali_start(r: dict) -> str | None:
    q = r.get("Qualifying")
    return start_utc(q["date"], q.get("time")) if q else None


def http_getter(
    session: requests.Session | None = None, cache: Path = CACHE, fresh: set[int] = frozenset()
) -> Getter:
    """GET s cache na disku. Sezóny v `fresh` (rozjazdená) sa sťahujú vždy znova."""
    s = session or requests.Session()

    def get(path: str) -> dict:
        season = int(path[:4])  # "2026.json?…" aj "2026/results.json?…"
        file = cache / (
            path.replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "-") + ".json"
        )
        if season not in fresh and file.exists():
            return json.loads(file.read_text(encoding="utf-8"))
        for attempt in range(1, 4):
            time.sleep(PAUSE)
            r = s.get(f"{BASE}/{path}", timeout=30)
            if r.status_code == 429:  # prekročený limit: počkaj a skús znova
                time.sleep(20 * attempt)
                continue
            r.raise_for_status()
            data = r.json()
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(json.dumps(data), encoding="utf-8")
            return data
        raise RuntimeError(f"Jolpica: {path} stále 429 (limit), skús o hodinu")

    return get


def fetch_all(get: Getter, season: int, kind: str) -> list[dict]:
    """Všetky preteky sezóny pre daný druh (results/qualifying/sprint), spojené zo stránok."""
    races: dict[str, dict] = {}
    offset = 0
    while True:
        path = f"{season}.json" if kind == "races" else f"{season}/{kind}.json"
        mr = get(f"{path}?limit={PAGE}&offset={offset}")["MRData"]
        for r in mr["RaceTable"]["Races"]:
            key = r["round"]
            if key in races:  # preteky rozdelené medzi dve stránky
                for list_key in ("Results", "QualifyingResults", "SprintResults"):
                    if list_key in r:
                        races[key].setdefault(list_key, []).extend(r[list_key])
            else:
                races[key] = r
        offset += PAGE
        if offset >= int(mr["total"]):
            return list(races.values())


def season_frames(get: Getter, season: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(kalendár, výsledky s kvalifikáciou, šprinty) jednej sezóny."""
    cal = pd.DataFrame(
        [
            {
                "season": season, "round": int(r["round"]), "race": r["raceName"],
                "start_utc": start_utc(r["date"], r.get("time")),
                "quali_utc": quali_start(r),
            }
            for r in fetch_all(get, season, "races")
        ],
        columns=["season", "round", "race", "start_utc", "quali_utc"],
    )  # fmt: skip
    quali = {
        (int(r["round"]), q["Driver"]["driverId"]): int(q["position"])
        for r in fetch_all(get, season, "qualifying")
        for q in r.get("QualifyingResults", [])
    }
    rows = []
    for r in fetch_all(get, season, "results"):
        for x in r.get("Results", []):
            d = x["Driver"]["driverId"]
            rows.append({
                "season": season, "round": int(r["round"]), "driver": d,
                "code": x["Driver"].get("code") or d[:3].upper(),
                "constructor": x["Constructor"]["constructorId"],
                "team": x["Constructor"]["name"], "quali": quali.get((int(r["round"]), d)),
                "grid": int(x["grid"]), "position": int(x["position"]), "status": x["status"],
                "points": float(x["points"]), "laps": int(x["laps"]),
            })  # fmt: skip
    sprint = [
        {"season": season, "round": int(r["round"]), "driver": x["Driver"]["driverId"],
         "position": int(x["position"]), "points": float(x["points"])}
        for r in fetch_all(get, season, "sprint")
        for x in r.get("SprintResults", [])
    ]  # fmt: skip
    res = pd.DataFrame(rows, columns=[
        "season", "round", "driver", "code", "constructor", "team", "quali", "grid", "position", "status",
        "points", "laps",
    ])  # fmt: skip
    res = res.merge(cal[["season", "round", "race", "start_utc"]], on=["season", "round"], how="left")
    return cal, res, pd.DataFrame(sprint, columns=["season", "round", "driver", "position", "points"])


def check_complete(cal: pd.DataFrame, res: pd.DataFrame, now: datetime) -> list[str]:
    """Odjazdené preteky (štart pred `now`) bez výsledkov, bez kvalifikácie alebo s malým poľom."""
    problems = []
    done = cal[pd.to_datetime(cal["start_utc"]) < now]
    for r in done.itertuples(index=False):
        rows = res[(res["season"] == r.season) & (res["round"] == r.round)]
        label = f"{r.season}/{r.round} {r.race}"
        if rows.empty:
            problems.append(f"{label}: chýbajú výsledky")
        elif len(rows) < MIN_DRIVERS:
            problems.append(f"{label}: len {len(rows)} jazdcov")
        elif rows["quali"].isna().all():
            problems.append(f"{label}: chýba kvalifikácia")
    return problems


def main(first: int, last: int, get: Getter | None = None, now: datetime | None = None,
         out: Path = OUT, sprints_out: Path = SPRINTS) -> pd.DataFrame:  # fmt: skip
    now = now or datetime.now(UTC)
    get = get or http_getter(fresh={now.year})
    cals, results, sprints = [], [], []
    for season in range(first, last + 1):
        cal, res, spr = season_frames(get, season)
        cals.append(cal)
        results.append(res)
        sprints.append(spr)
        print(
            f"{season}: {len(cal)} pretekov v kalendári, {res['round'].nunique()} odjazdených, "
            f"{len(spr)} riadkov šprintov"
        )
    cal, res = pd.concat(cals, ignore_index=True), pd.concat(results, ignore_index=True)
    problems = check_complete(cal, res, now)
    if problems:
        raise RuntimeError("Neúplné dáta, nič sa neuložilo:\n  " + "\n  ".join(problems))
    res = res.sort_values(["season", "round", "position"], kind="stable").reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out, index=False)
    pd.concat(sprints, ignore_index=True).to_parquet(sprints_out, index=False)
    print(
        f"Uložené: {out} ({len(res)} riadkov, {res.groupby(['season', 'round']).ngroups} pretekov), "
        f"{sprints_out}"
    )
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2014)
    ap.add_argument("--to", dest="last", type=int, default=datetime.now(UTC).year)
    a = ap.parse_args()
    main(a.first, a.last)
