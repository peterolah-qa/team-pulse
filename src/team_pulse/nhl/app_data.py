"""NHL v appke (beta): zamknuté tipy z archívu + výsledky z API NHL → app/public/data/nhl/.

Tipy počíta a zamyká ranná úloha na Macu (team_pulse.nhl.daily → archive/nhl/predictions).
Tu sa nič nepočíta, model sa nemení (brána G2-NHL): len sa poskladá to, čo appka ukáže.
Beží v GitHub Actions pri každom builde appky (predict.yml), chyba NHL nezastaví NBA.

  predictions.json  zápasy, ktoré sa ešte nedohrali (s tipom), výsledky za posledné dni, teamy podľa Ela,
                    zranenia z ESPN (len informácia, model ich nepoužíva), pri každom zápase kontext
                    pre detail (team_pulse.nhl.context: rozpad tipu, Elo trend, forma, odpočinok,
                    vzájomné zápasy, štatistiky)
  model.json        presnosť a vrstvy modelu (rovnaký tvar ako NBA model.json)
  cache.json        rozpisy klubov pre ďalší beh (aby sa nesťahovali pri každom builde)

Spustenie:  uv run python -m team_pulse.nhl.app_data
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import requests

from team_pulse.model_store import load
from team_pulse.nhl import context as cx
from team_pulse.nhl import injuries as inj
from team_pulse.nhl.archive import ARCHIVE, load_tips
from team_pulse.nhl.fetch_games import FINISHED, franchise, season_of, today_et
from team_pulse.nhl.model import MODEL

OUT = Path("app/public/data/nhl")
SCORE_URL = "https://api-web.nhle.com/v1/score/{day}"
RESULT_DAYS = 3  # dni ET dozadu vrátane dneška: appka ukazuje výsledky zo včera a z dneška nášho času
GAME_TYPES = {2: "regular", 3: "playoff"}  # príprava (1) sa netipuje
TEST_SEASONS = "2023/24 – 2025/26"  # testovacie sezóny G0-NHL (docs/gate-nhl-G0.md)


def fetch_results(days: list[date], session: requests.Session | None = None) -> list[dict]:
    """Dohraté zápasy základnej časti a playoff z API NHL za dané dni (ET)."""
    s = session or requests.Session()
    out = []
    for day in days:
        r = s.get(SCORE_URL.format(day=day.isoformat()), timeout=20)
        r.raise_for_status()
        out += [parse_result(g) for g in r.json().get("games") or []]
    return [g for g in out if g is not None]


def parse_result(g: dict) -> dict | None:
    kind = GAME_TYPES.get(g.get("gameType"))
    home, away = g.get("homeTeam") or {}, g.get("awayTeam") or {}
    if (
        kind is None
        or g.get("gameState") not in FINISHED
        or home.get("score") is None
        or away.get("score") is None
    ):
        return None
    return {
        "game_id": str(g["id"]),
        "date": g["gameDate"],
        "tipoff_utc": g["startTimeUTC"],
        "kind": kind,
        "home": franchise(home["abbrev"]),
        "away": franchise(away["abbrev"]),
        "goals_home": int(home["score"]),
        "goals_away": int(away["score"]),
        "last_period": (g.get("gameOutcome") or {}).get("lastPeriodType"),
    }


def _side(s: dict) -> dict:
    """Dôvody ako v NBA: [(text, Elo)] od najväčšieho vplyvu."""
    reasons = sorted(s.get("reasons", {}).items(), key=lambda kv: -abs(kv[1]))
    return {"team": s["team"], "elo": s["elo"], "reasons": [[t, round(e)] for t, e in reasons]}


def _game(t: dict) -> dict:
    return {
        "game_id": t["game_id"],
        "date": t["date"],
        "tipoff_utc": t["tipoff_utc"],
        "kind": t.get("kind", "regular"),
        "neutral": t.get("neutral", False),
        "p_home": t["p_home"],
        "locked_at": t["locked_at"],
        "home": _side(t["home"]),
        "away": _side(t["away"]),
    }


def teams(tips: list[dict]) -> list[dict]:
    """Elo každého klubu z jeho posledného tipu (pred zápasom). Zoradené od najsilnejšieho."""
    last: dict[str, tuple[str, float]] = {}
    for t in sorted(tips, key=lambda x: (x["tipoff_utc"], x["game_id"])):
        for side in ("home", "away"):
            last[t[side]["team"]] = (t["date"], t[side]["elo"])
    rows = [{"team": k, "elo": round(e, 1), "as_of": d} for k, (d, e) in last.items()]
    return sorted(rows, key=lambda r: (-r["elo"], r["team"]))


def build(tips: list[dict], results: list[dict], now: datetime, model: str) -> dict:
    """Zápasy od včera (ET), ktoré sa ešte nedohrali, + výsledky s tipom zamknutým pred začiatkom."""
    first = (today_et(now) - timedelta(days=1)).isoformat()
    done = {r["game_id"] for r in results}
    by_id = {t["game_id"]: t for t in tips}
    days: dict[str, list[dict]] = {}
    for t in sorted(tips, key=lambda x: (x["tipoff_utc"], x["game_id"])):
        if t["date"] >= first and t["game_id"] not in done:
            days.setdefault(t["date"], []).append(_game(t))

    def p_home(r: dict) -> float | None:
        t = by_id.get(r["game_id"])
        ok = t is not None and datetime.fromisoformat(t["locked_at"]) < datetime.fromisoformat(
            r["tipoff_utc"].replace("Z", "+00:00")
        )
        return t["p_home"] if ok else None  # tip zamknutý až po začiatku sa neráta (ako vo vyhodnotení)

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "sport": "nhl",
        "beta": True,
        "model": model,
        "last_locked": max((t["locked_at"] for t in tips), default=None),
        "days": dict(sorted(days.items())),
        "results": [
            {**r, "p_home": p_home(r)} for r in sorted(results, key=lambda r: (r["tipoff_utc"], r["game_id"]))
        ],
        "teams": teams(tips),
    }


def model_info(path: Path = MODEL) -> dict:
    m = json.loads(path.read_text(encoding="utf-8"))
    return {
        "version": m["version"],
        "created": m["created"],
        "train_seasons": m["train_seasons"],
        "n_games": m["n_games"],
        "test_metrics": {**m["test_metrics"], "test_seasons": TEST_SEASONS},
        "calibration": m.get("calibration", []),
        "versions": m["versions"],
        "elo_weights": m["elo_weights"],
    }


def add_context(
    data: dict,
    tips: list[dict],
    results: list[dict],
    now: datetime,
    cache: dict,
    fetch: cx.Fetch | None = None,
    summary: dict | None = None,
    pause: float = 0.25,
) -> tuple[dict, list[str]]:
    """Ku každému zápasu s tipom doplní `ctx` pre detail. Tipy sa nemenia. Vráti (nová cache, problémy).

    summary: odpoveď štatistík NHL (None = nepodarilo sa ju stiahnuť, štatistiky sa vynechajú)."""
    model = load(MODEL)
    by_id = {t["game_id"]: t for t in tips}
    games = [g for gs in data["days"].values() for g in gs]
    need: dict[str, set[str]] = {}
    for g in games:
        for side in ("home", "away"):
            need.setdefault(g[side]["team"], set()).add(g["game_id"])
    season = season_of(today_et(now))
    session = requests.Session()
    fetch = fetch or (lambda team, year: cx.fetch_club(team, year, session))
    cache, fetched, problems = cx.schedules(need, season, results, now, cache, fetch, pause)
    stats: dict[str, dict] = {}
    if summary is not None:
        parsed = cx.team_stats(summary, cx.team_ids(cache), season)
        stats, wrong = cx.check_stats(parsed["teams"], cache, season)
        problems += parsed["problems"] + wrong
    for g in games:
        g["ctx"] = cx.game_context(by_id[g["game_id"]], tips, cache, model, stats)
    data["context_at"] = now.isoformat(timespec="seconds")
    data["stats_at"] = now.isoformat(timespec="seconds") if stats else None
    verified = sum(1 for g in games if g["ctx"]["edge"]["verified"])
    print(f"NHL kontext: {len(games)} zápasov, rozpad overený {verified}, stiahnuté rozpisy {fetched}, "
          f"štatistiky {len(stats)} klubov")  # fmt: skip
    return cache, problems


def main(out: Path = OUT, archive: Path = ARCHIVE, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    tips = load_tips(archive)
    today = today_et(now)
    try:
        results = fetch_results([today - timedelta(days=n) for n in range(RESULT_DAYS - 1, -1, -1)])
    except (requests.RequestException, ValueError, KeyError) as e:
        # bez výsledkov appka aj tak ukáže tipy; dohraté zápasy budú mať štítok „po zápase“
        print(f"::warning::NHL výsledky sa nepodarilo stiahnuť: {e.__class__.__name__}: {e}")
        results = []
    model = json.loads(MODEL.read_text(encoding="utf-8"))["version"]
    data = build(tips, results, now, model)
    try:
        raw = inj.fetch()
        data["injuries"], data["injuries_timestamp"] = inj.parse(raw), raw.get("timestamp")
    except (requests.RequestException, ValueError, KeyError) as e:
        # bez zranení appka ukáže tipy ako doteraz, len bez zoznamu chýbajúcich hráčov
        print(f"::warning::NHL zranenia sa nepodarilo stiahnuť: {e.__class__.__name__}: {e}")
        data["injuries"], data["injuries_timestamp"] = None, None
    out.mkdir(parents=True, exist_ok=True)
    try:
        summary = cx.fetch_summary(season_of(today))
    except (requests.RequestException, ValueError) as e:
        print(f"::warning::NHL štatistiky klubov sa nepodarilo stiahnuť: {e.__class__.__name__}: {e}")
        summary = None
    try:
        cache, problems = add_context(data, tips, results, now, cx.load_cache(), summary=summary)
        for p in problems:
            print(f"::warning::NHL kontext: {p}")
        (out / "cache.json").write_text(json.dumps(cache, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as e:  # kontext je len doplnok: tipy a výsledky sa zverejnia aj bez neho
        print(f"::warning::NHL kontext zápasov sa nepodaril: {e.__class__.__name__}: {e}")
        for g in (g for gs in data["days"].values() for g in gs):
            g.pop("ctx", None)
        data["context_at"] = data["stats_at"] = None
    (out / "predictions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out / "model.json").write_text(
        json.dumps(model_info(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    n = sum(len(g) for g in data["days"].values())
    rs, ts = len(data["results"]), len(data["teams"])
    ij = sum(len(p) for p in (data["injuries"] or {}).values())
    print(f"NHL pre appku: {n} zápasov s tipom, {rs} výsledkov, {ts} teamov, {ij} zranených → {out}")
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    main(ap.parse_args().out)
