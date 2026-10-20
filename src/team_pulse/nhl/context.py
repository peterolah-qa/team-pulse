"""Kontext NHL zápasu pre detail v appke: rozpad tipu, Elo trend, forma, odpočinok, vzájomné zápasy.

Len informácia pre ľudí. Model ani zamknuté tipy sa tu nemenia (brána G2-NHL), všetko sa skladá
z archívu tipov a z verejného API NHL:

  rozpad tipu   šanca domácich z archívu prevedená na Elo body a rozložená na časti modelu. Keď
                sa z rozpisu klubov dajú znova spočítať vstupy modelu a model z nich dá presne
                zamknutú šancu, rozpad je po položkách a „overený“. Inak: Elo, domáci ľad, únava
                z archívu a zvyšok (konštanta modelu a drobné vplyvy). Súčet vždy = zamknutá šanca.
  Elo trend     Elo pred každým zápasom s tipom v archíve (od 13. 10. 2026), posledných 10.
  forma         bilancia sezóny, posledných 5 zápasov, doma / vonku, góly na zápas (rozpis klubu).
  odpočinok     dni voľna, back-to-back, zápas výjazdu – rovnaký výpočet ako vstupy modelu.
  vzájomné      posledné 3 zápasy tejto dvojice v tejto a minulej sezóne.
  štatistiky    presilovky, oslabenia, strely a góly na zápas s poradím v lige (štatistiky NHL).
                Použijú sa len po kontrole tvaru a len pre klub, ktorému sedí počet zápasov a výhier
                s jeho rozpisom. Inak sa neukážu (radšej nič než nesediace čísla).

Rozpisy klubov sa nesťahujú pri každom behu: posledná verzia sa načíta zo zverejnenej appky
(data/nhl/cache.json) a klub sa stiahne znova, len keď odohral zápas, ktorý v nej chýba, rozpis
je starší než 6 h alebo v ňom chýba zápas s tipom. Minulá sezóna sa už nemení.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta

import pandas as pd
import requests

from team_pulse.model_store import StoredModel
from team_pulse.nhl.fetch_games import ET, FINISHED, URL, franchise, season_id
from team_pulse.nhl.schedule import MAX_REST, add_features

SUMMARY_URL = "https://api.nhle.com/stats/rest/en/team/summary"
CACHE_URL = "https://peterolah-qa.github.io/team-pulse/data/nhl/cache.json"
CACHE_VERSION = 1
MAX_AGE = timedelta(hours=6)
LAST = 5  # posledné zápasy vo forme
H2H = 3  # posledné vzájomné zápasy
TREND = 10  # body Elo trendu
GAME_TYPES = {2: "R", 3: "P"}  # základná časť, playoff (príprava sa nepočíta)

# Štatistiky NHL: náš kľúč → (pole v API, menšie je lepšie, rozsah hodnôt na kontrolu tvaru)
STATS = {
    "gf": ("goalsForPerGame", False, (0.0, 12.0)),
    "ga": ("goalsAgainstPerGame", True, (0.0, 12.0)),
    "pp": ("powerPlayPct", False, (0.0, 1.0)),
    "pk": ("penaltyKillPct", False, (0.0, 1.0)),
    "sf": ("shotsForPerGame", False, (0.0, 70.0)),
    "sa": ("shotsAgainstPerGame", True, (0.0, 70.0)),
}
MIN_TEAMS = 30  # menej riadkov = neúplná odpoveď, štatistiky sa nepoužijú

Fetch = Callable[[str, int], list[dict]]


# --- rozpad tipu ---------------------------------------------------------------------------------


def _elo_scale(model: StoredModel) -> float:
    return model.coef[model.features.index("elo_diff")]


def _to_elo(logit: float, model: StoredModel) -> float:
    """Logit šance → Elo body (rovnaká mierka ako elo_weights v modeli)."""
    return logit / _elo_scale(model) * 100


def _round_parts(values: list[float], total: float) -> list[float]:
    """Zaokrúhli na 0,1 tak, aby súčet zaokrúhlených presne sedel so zaokrúhleným súčtom."""
    target = round(total * 10)
    tenths = [v * 10 for v in values]
    base = [math.floor(t) for t in tenths]
    rest = target - sum(base)
    order = sorted(range(len(values)), key=lambda i: -(tenths[i] - base[i]))
    for i in order[: max(rest, 0)]:
        base[i] += 1
    return [b / 10 for b in base]


def _days(n: int) -> str:
    return "deň" if n == 1 else "dni" if 2 <= n <= 4 else "dní"


def _feature_label(name: str, x: float, home: str, away: str) -> str:
    side, feat = name.split("_", 1)
    team = home if side == "home" else away
    n = int(x)
    if feat == "rest":
        free = n - 1
        if n >= MAX_REST:
            return f"{team}: {free} a viac dní voľna"
        return f"{team}: bez dňa voľna" if free == 0 else f"{team}: {free} {_days(free)} voľna"
    labels = {
        "b2b": "back-to-back",
        "three_in4": "3. zápas za 4 dni",
        "tz_east": f"posun o {n} h na východ",
        "road": f"{n}. zápas výjazdu",
    }
    return f"{team}: {labels[feat]}"


def recompute(tip: dict, games: pd.DataFrame, model: StoredModel) -> dict | None:
    """Vstupy modelu pre zápas z tipu znova z rozpisu a Ela v tipe. None, keď zápas v rozpise nie je."""
    if games.empty:
        return None
    feats = add_features(games).set_index("game_id")
    gid = int(tip["game_id"])
    if gid not in feats.index:
        return None
    row = feats.loc[gid]
    if {row["home"], row["away"]} != {tip["home"]["team"], tip["away"]["team"]} or row["home"] != tip["home"][
        "team"
    ]:
        return None
    x = {f: float(row[f]) for f in model.features if f not in ("elo_diff", "home")}
    x["elo_diff"] = (tip["home"]["elo"] - tip["away"]["elo"]) / 100
    x["home"] = 0.0 if tip.get("neutral") else 1.0
    return x


def edge(tip: dict, model: StoredModel, inputs: dict | None = None) -> dict:
    """Prečo má tip svoju šancu: Elo body z pohľadu domácich (kladné = pomáha domácim).

    Položky sa sčítajú presne na `total` a `total` dá zamknutú šancu domácich."""
    home, away = tip["home"]["team"], tip["away"]["team"]
    coef = dict(zip(model.features, model.coef, strict=True))
    scale = _elo_scale(model)
    if inputs is not None:
        z = model.intercept + sum(coef[f] * v for f, v in inputs.items())
        p = 1 / (1 + math.exp(-z))
        if round(p, 3) == round(tip["p_home"], 3):
            items: list[tuple[str, str, float]] = [
                ("elo", "Rozdiel v Elo", inputs["elo_diff"] * 100),
                ("home", f"{home}: domáci ľad", coef["home"] * inputs["home"] / scale * 100),
                ("base", "Konštanta modelu", model.intercept / scale * 100),
            ]
            for f in model.features:
                if f in ("elo_diff", "home") or inputs[f] == 0:
                    continue
                v = coef[f] * inputs[f] / scale * 100
                items.append((f, _feature_label(f, inputs[f], home, away), v))
            items = [it for it in items if it[0] in ("elo", "base") or abs(it[2]) >= 0.05]
            total = _to_elo(z, model)
            parts = _round_parts([v for *_, v in items], total)
            return {
                "verified": True,
                "total": round(total, 1),
                "items": [[k, label, v] for (k, label, _), v in zip(items, parts, strict=True)],
            }
    p = min(max(tip["p_home"], 1e-6), 1 - 1e-6)
    total = _to_elo(math.log(p / (1 - p)), model)
    items = [("elo", "Rozdiel v Elo", tip["home"]["elo"] - tip["away"]["elo"])]
    if not tip.get("neutral"):
        items.append(("home", f"{home}: domáci ľad", coef["home"] / scale * 100))
    for side, sign in (("home", 1.0), ("away", -1.0)):
        team = tip[side]["team"]
        for text, v in sorted(tip[side]["reasons"].items(), key=lambda kv: -abs(kv[1])):
            items.append((f"{side}_reason", f"{team}: {text}", sign * v))
    items.append(("other", "Konštanta modelu a drobné vplyvy", total - sum(v for *_, v in items)))
    parts = _round_parts([v for *_, v in items], total)
    return {
        "verified": False,
        "total": round(total, 1),
        "items": [[k, label, v] for (k, label, _), v in zip(items, parts, strict=True)],
    }


# --- Elo trend z archívu -------------------------------------------------------------------------


def _start(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def trend(tips: Iterable[dict], team: str, until: str) -> list[list]:
    """Elo klubu pred jeho zápasmi s tipom (zamknutým pred začiatkom) do `until` vrátane, posledných 10."""
    pts = []
    for t in tips:
        if t["tipoff_utc"] > until or _start(t["locked_at"]) >= _start(t["tipoff_utc"]):
            continue
        for side in ("home", "away"):
            if t[side]["team"] == team:
                pts.append((t["tipoff_utc"], t["game_id"], t["date"], t[side]["elo"]))
    pts.sort()
    return [[d, round(e, 1)] for *_, d, e in pts[-TREND:]]


# --- rozpisy klubov ------------------------------------------------------------------------------


def compact(g: dict) -> dict | None:
    """Zápas z rozpisu klubu → malý riadok. Príprava a All-Star sa vynechajú."""
    kind = GAME_TYPES.get(int(g.get("gameType", 0)))
    if kind is None:
        return None
    home, away = g["homeTeam"], g["awayTeam"]
    final = g.get("gameState") in FINISHED and home.get("score") is not None and away.get("score") is not None
    return {
        "id": str(g["id"]),
        "season": int(str(g["season"])[4:]),
        "type": kind,
        "date": g["gameDate"],
        "start": g.get("startTimeUTC"),
        "home": franchise(home["abbrev"]),
        "away": franchise(away["abbrev"]),
        "home_abbr": home["abbrev"],
        "away_abbr": away["abbrev"],
        "home_id": home.get("id"),
        "away_id": away.get("id"),
        "neutral": bool(g.get("neutralSite", False)),
        "venue": (g.get("venue") or {}).get("default"),
        "final": final,
        "gh": int(home["score"]) if final else None,
        "ga": int(away["score"]) if final else None,
        "last": (g.get("gameOutcome") or {}).get("lastPeriodType") if final else None,
    }


def fetch_club(team: str, end_year: int, session: requests.Session | None = None) -> list[dict]:
    """Rozpis klubu za sezónu ako malé riadky (bez prípravy)."""
    s = session or requests.Session()
    r = s.get(URL.format(team=team, season=season_id(end_year)), timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return [c for g in r.json().get("games") or [] if (c := compact(g)) is not None]


def load_cache(session: requests.Session | None = None, url: str = CACHE_URL) -> dict:
    """Posledné rozpisy zo zverejnenej appky. Pri chybe alebo inom tvare prázdna cache (stiahne sa všetko)."""
    try:
        r = (session or requests.Session()).get(url, timeout=20)
        if r.status_code != 200:
            return {}
        data = r.json()
    except (requests.RequestException, ValueError):
        return {}
    ok = (
        isinstance(data, dict)
        and data.get("version") == CACHE_VERSION
        and isinstance(data.get("teams"), dict)
    )
    return data if ok else {}


def _fresh(entry: dict | None, team: str, results: list[dict], need: set[str], now: datetime) -> bool:
    """Rozpis z cache stačí: nie je starý, má všetky zápasy s tipom a všetky nedávne výsledky klubu sedia."""
    if not entry or not isinstance(entry.get("games"), list):
        return False
    try:
        if now - datetime.fromisoformat(entry["fetched_at"]) > MAX_AGE:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    by_id = {g.get("id"): g for g in entry["games"]}
    if not need <= by_id.keys():
        return False
    for r in results:
        if team not in (r["home"], r["away"]):
            continue
        g = by_id.get(r["game_id"])
        if (
            g is None
            or not g.get("final")
            or (g.get("gh"), g.get("ga")) != (r["goals_home"], r["goals_away"])
        ):
            return False
    return True


def _done(entry: dict | None) -> bool:
    """Minulá sezóna z cache: celá dohraná, netreba ju sťahovať znova."""
    return bool(entry) and bool(entry.get("games")) and all(g.get("final") for g in entry["games"])


def schedules(
    need: dict[str, set[str]],
    season: int,
    results: list[dict],
    now: datetime,
    cache: dict,
    fetch: Fetch,
    pause: float = 0.25,
) -> tuple[dict, int, list[str]]:
    """Rozpisy klubov (táto a minulá sezóna) pre kluby so zápasom s tipom.

    need: klub → id zápasov s tipom, ktoré musia byť v jeho rozpise.
    Vráti (nová cache, počet stiahnutí, problémy). Keď sa rozpis tejto sezóny nepodarí stiahnuť,
    z cache sa vyhodí (appka pri zápase ukáže len rozpad tipu, nie staré čísla)."""
    teams = {k: dict(v) for k, v in (cache.get("teams") or {}).items() if isinstance(v, dict)}
    fetched, problems = 0, []
    for team in sorted(need):
        entry = teams.setdefault(team, {})
        for year, ok in (
            (season, _fresh(entry.get(str(season)), team, results, need[team], now)),
            (season - 1, _done(entry.get(str(season - 1)))),
        ):
            if ok:
                continue
            try:
                entry[str(year)] = {
                    "fetched_at": now.isoformat(timespec="seconds"),
                    "games": fetch(team, year),
                }
                fetched += 1
                if pause:
                    time.sleep(pause)  # ohľaduplne k API NHL
            except (requests.RequestException, ValueError, KeyError, TypeError) as e:
                problems.append(f"rozpis {team} {year}: {e.__class__.__name__}: {e}")
                if year == season:
                    entry.pop(str(year), None)
    cache = {"version": CACHE_VERSION, "updated": now.isoformat(timespec="seconds"), "teams": teams}
    return cache, fetched, problems


# --- forma, odpočinok, vzájomné zápasy -----------------------------------------------------------


def _played(games: list[dict], team: str, before: str) -> list[dict]:
    rows = [g for g in games if g["final"] and team in (g["home"], g["away"]) and (g["start"] or "") < before]
    return sorted(rows, key=lambda g: (g["start"] or "", g["id"]))


def _outcome(g: dict, team: str) -> tuple[int, int, str]:
    """(góly klubu, góly súpera, W / L / OTL) – prehra po predĺžení alebo nájazdoch = OTL."""
    home = g["home"] == team
    gf, ga = (g["gh"], g["ga"]) if home else (g["ga"], g["gh"])
    if gf > ga:
        return gf, ga, "W"
    return gf, ga, "OTL" if g["last"] in ("OT", "SO") else "L"


def _record(games: list[dict], team: str) -> list[int]:
    out = {"W": 0, "L": 0, "OTL": 0}
    for g in games:
        out[_outcome(g, team)[2]] += 1
    return [out["W"], out["L"], out["OTL"]]


def form(games: list[dict], team: str, before: str) -> dict:
    """Bilancia základnej časti a posledných 5 zápasov klubu pred začiatkom zápasu `before` (UTC)."""
    played = _played(games, team, before)
    regular = [g for g in played if g["type"] == "R"]
    last = []
    for g in reversed(played[-LAST:]):
        gf, ga, res = _outcome(g, team)
        home = g["home"] == team
        last.append({
            "date": g["date"], "opp": g["away"] if home else g["home"], "home": home,
            "gf": gf, "ga": ga, "res": res, "last": g["last"] if g["last"] in ("OT", "SO") else None,
        })  # fmt: skip
    n = len(regular)
    gf = sum(_outcome(g, team)[0] for g in regular)
    ga = sum(_outcome(g, team)[1] for g in regular)
    return {
        "gp": n,
        "record": _record(regular, team),
        "home_record": _record([g for g in regular if g["home"] == team and not g["neutral"]], team),
        "road_record": _record([g for g in regular if g["away"] == team and not g["neutral"]], team),
        "gf_pg": round(gf / n, 2) if n else None,
        "ga_pg": round(ga / n, 2) if n else None,
        "last": last,
    }


def model_frame(games: list[dict], game: dict, lock_day: str) -> pd.DataFrame:
    """Rozpis v tvare, z akého počíta únavu predikcia: dohraté zápasy sezóny + nedohraté od dňa
    zamknutia po deň zápasu (team_pulse.nhl.predict)."""
    rows = {
        g["id"]: g
        for g in games
        if g["season"] == game["season"]
        and (g["final"] or lock_day <= g["date"])
        and g["date"] <= game["date"]
    }
    cols = ["game_id", "season", "date", "start_utc", "home", "away", "home_abbr", "neutral"]
    return pd.DataFrame(
        [
            [
                int(g["id"]),
                g["season"],
                g["date"],
                g["start"],
                g["home"],
                g["away"],
                g["home_abbr"],
                g["neutral"],
            ]
            for g in rows.values()
        ],
        columns=cols,
    )


def rest(inputs: dict | None, games: list[dict], team: str, before: str, side: str) -> dict:
    """Odpočinok a cestovanie klubu: posledný zápas, dni voľna, back-to-back, 3 za 4, výjazd."""
    played = _played(games, team, before)
    prev = played[-1] if played else None
    out: dict = {"prev": None}
    if prev is not None:
        home = prev["home"] == team
        gf, ga, res = _outcome(prev, team)
        out["prev"] = {
            "date": prev["date"],
            "opp": prev["away"] if home else prev["home"],
            "home": home,
            "res": res,
        }
    if inputs is not None:
        out |= {
            "rest": int(inputs[f"{side}_rest"]),
            "b2b": bool(inputs[f"{side}_b2b"]),
            "three_in4": bool(inputs[f"{side}_three_in4"]),
            "tz_east": int(inputs[f"{side}_tz_east"]),
            "road": int(inputs["away_road"]) if side == "away" else 0,
        }
    return out


def h2h(games: list[dict], home: str, away: str, before: str) -> list[dict]:
    """Posledné vzájomné zápasy dvojice (od najnovšieho)."""
    rows = [g for g in _played(games, home, before) if {g["home"], g["away"]} == {home, away}]
    out = []
    for g in reversed(rows[-H2H:]):
        out.append({
            "date": g["date"], "home": g["home"], "away": g["away"], "gh": g["gh"], "ga": g["ga"],
            "last": g["last"] if g["last"] in ("OT", "SO") else None, "type": g["type"],
        })  # fmt: skip
    return out


# --- štatistiky NHL ------------------------------------------------------------------------------


def fetch_summary(end_year: int, session: requests.Session | None = None) -> dict:
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "start": 0,
        "limit": 50,
        "cayenneExp": f"seasonId={season_id(end_year)} and gameTypeId=2",
    }
    r = (session or requests.Session()).get(SUMMARY_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _num(v: object) -> float | None:
    return float(v) if isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v) else None


def team_stats(raw: dict, ids: dict[int, str], end_year: int) -> dict:
    """Štatistiky klubov s poradím v lige. Kontrola tvaru: celá liga, správna sezóna, hodnoty v rozsahu.

    Vráti {"teams": {klub: {...}}, "problems": [...]}; pri zlom tvare sú teams prázdne."""
    rows = raw.get("data") if isinstance(raw, dict) else None
    if not isinstance(rows, list) or len(rows) < MIN_TEAMS:
        n = len(rows) if isinstance(rows, list) else 0
        return {"teams": {}, "problems": [f"štatistiky NHL: {n} klubov, čakal som aspoň {MIN_TEAMS}"]}
    want = int(season_id(end_year))
    clean = []
    for r in rows:
        tid, gp, wins = r.get("teamId"), _num(r.get("gamesPlayed")), _num(r.get("wins"))
        vals = {k: _num(r.get(field)) for k, (field, _, _) in STATS.items()}
        ok = (
            isinstance(tid, int)
            and r.get("seasonId") == want
            and gp is not None
            and wins is not None
            and all(
                v is not None and lo <= v <= hi
                for v, (_, _, (lo, hi)) in zip(vals.values(), STATS.values(), strict=True)
            )
        )
        if not ok:
            return {"teams": {}, "problems": [f"štatistiky NHL: neočakávaný riadok {sorted(r)[:8]}"]}
        clean.append((tid, int(gp), int(wins), vals))
    # poradie v lige: 1 = najlepší, rovnaká hodnota = rovnaké poradie
    ranks: dict[str, dict[int, int]] = {}
    for k, (_, lower, _) in STATS.items():
        ranks[k] = {
            tid: 1 + sum(1 for *_, v2 in clean if (v2[k] < v[k] if lower else v2[k] > v[k]))
            for tid, _, _, v in clean
        }
    teams = {}
    for tid, gp, wins, vals in clean:
        team = ids.get(tid)  # klub, ktorého rozpis ešte nie je v cache, appka zatiaľ neukazuje
        if team is None:
            continue
        teams[team] = {
            "gp": gp,
            "w": wins,
            **{k: round(v, 4) for k, v in vals.items()},
            "rank": {k: ranks[k][tid] for k in STATS},
        }
    return {"teams": teams, "n": len(clean), "problems": []}


def team_ids(cache: dict) -> dict[int, str]:
    """id klubu v API → skratka (z rozpisov v cache)."""
    ids: dict[int, str] = {}
    for entry in (cache.get("teams") or {}).values():
        for season in entry.values():
            for g in season.get("games") or []:
                for side in ("home", "away"):
                    tid = g.get(f"{side}_id")
                    if isinstance(tid, int):
                        ids[tid] = g[side]
    return ids


# --- poskladanie pre appku -----------------------------------------------------------------------


def game_context(
    tip: dict, tips: list[dict], cache: dict, model: StoredModel, stats: dict[str, dict]
) -> dict:
    """Všetko k jednému zápasu s tipom. Bez rozpisu klubov len rozpad z archívu a Elo trend."""
    home, away = tip["home"]["team"], tip["away"]["team"]
    end_year = int(tip["game_id"][:4]) + 1
    teams = cache.get("teams") or {}

    def season_games(team: str, year: int) -> list[dict]:
        return list(((teams.get(team) or {}).get(str(year)) or {}).get("games") or [])

    cur = {t: season_games(t, end_year) for t in (home, away)}
    this = next((g for g in cur[home] if g["id"] == tip["game_id"]), None)
    ok = (
        this is not None
        and this["home"] == home
        and this["away"] == away
        and this["start"] == tip["tipoff_utc"]
        and any(g["id"] == tip["game_id"] for g in cur[away])
    )
    inputs = None
    if ok:
        lock_day = _start(tip["locked_at"]).astimezone(ET).date().isoformat()
        merged = list({g["id"]: g for g in cur[home] + cur[away]}.values())
        inputs = recompute(tip, model_frame(merged, {**this, "season": end_year}, lock_day), model)
    ctx: dict = {
        "edge": edge(tip, model, inputs),
        "trend": {"home": trend(tips, home, tip["tipoff_utc"]), "away": trend(tips, away, tip["tipoff_utc"])},
    }
    if not ok:
        return ctx
    start = tip["tipoff_utc"]
    ctx["venue"] = this["venue"]
    for side, team in (("home", home), ("away", away)):
        ctx[side] = {
            "form": form(cur[team], team, start),
            "rest": rest(inputs, cur[team], team, start, side),
        }
        if team in stats:
            ctx[side]["stats"] = stats[team]
    prev = (teams.get(home) or {}).get(str(end_year - 1))
    if _done(prev):  # bez celej minulej sezóny by „posledné 3“ neplatilo
        ctx["h2h"] = h2h(cur[home] + season_games(home, end_year - 1), home, away, start)
    return ctx


def check_stats(stats: dict[str, dict], cache: dict, end_year: int) -> tuple[dict, list[str]]:
    """Štatistiky len pre kluby, ktorým sedí počet zápasov a výhier s rozpisom (inak sa vynechajú)."""
    teams = cache.get("teams") or {}
    kept, problems = {}, []
    for team, s in stats.items():
        games = ((teams.get(team) or {}).get(str(end_year)) or {}).get("games")
        if not games:
            continue  # klub bez zápasu s tipom, appka jeho štatistiky neukáže
        regular = [g for g in _played(games, team, "9999") if g["type"] == "R"]
        w = sum(1 for g in regular if _outcome(g, team)[2] == "W")
        if (s["gp"], s["w"]) == (len(regular), w):
            kept[team] = s
        else:
            problems.append(
                f"{team}: štatistiky NHL {s['gp']} zápasov / {s['w']} výhier, rozpis {len(regular)} / {w}"
            )
    return kept, problems
