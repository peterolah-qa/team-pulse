"""Vyhodnotenie brán G2 (NBA, NHL) podľa kritérií stanovených vopred.

Kritériá a hranice sú v docs/gate-G2.md (NBA) a docs/gate-nhl-G2.md (NHL), stanovené 14. 10. 2026.
Tu sa len overujú. Prepočet je nezávislý od kódu, ktorý píše reporty: tipy a výsledky sa čítajú
priamo z archívov (JSON), rozpis zo zdroja a čísla v reportoch sa s prepočtom len porovnajú.

NBA (stačí repo s históriou gitu): rozpis zo state/state.json, tipy z archive/predictions,
  výsledky z archive/results, report reports/live.md, stav do 12:00 z histórie state/state.json.
NHL (z Macu, potrebuje API NHL): rozpis a výsledky z API NHL, tipy z archive/nhl/predictions,
  report reports/nhl_live.md.

Pred koncom obdobia je výsledok predbežný (hodnotia sa len dni, ktoré už prebehli).

Spustenie:  uv run python -m team_pulse.gate_g2 nhl      (vyhodnotenie 27. 10. 2026)
            uv run python -m team_pulse.gate_g2 nba      (vyhodnotenie 3. 11. 2026)
Výstup:     reports/gate_g2_<šport>.md, návratový kód 1, keď niektoré kritérium neplatí
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ET = ZoneInfo("America/New_York")
LOCAL = ZoneInfo("Europe/Bratislava")


@dataclass(frozen=True)
class Gate:
    sport: str
    first: date  # prvý deň obdobia (ET)
    last: date  # posledný deň obdobia (ET)
    ll_limit: float  # 95. percentil 14-dňových okien backtestu (scripts/g2_reference.py)
    home_rate: float  # baseline „vždy domáci“ z tréningových sezón (scripts/g2_reference.py)
    beat_baseline: bool  # kritérium „log loss nižší než baseline“ (len NBA)
    doc: str
    report: Path


NBA = Gate(
    "nba",
    date(2026, 10, 20),
    date(2026, 11, 2),
    0.6739,
    0.5873,
    True,
    "docs/gate-G2.md",
    Path("reports/live.md"),
)
NHL = Gate(
    "nhl",
    date(2026, 10, 13),
    date(2026, 10, 26),
    0.7101,
    0.5434,
    False,
    "docs/gate-nhl-G2.md",
    Path("reports/nhl_live.md"),
)
STATE_DEADLINE = time(12, 0)  # NBA: stav s výsledkami predchádzajúcej noci do 12:00 nášho času


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    problems: list[str] = field(default_factory=list)


# --- spoločné ---------------------------------------------------------------------------------------


def utc(value: str) -> pd.Timestamp:
    """'2026-10-20 19:00:00+00:00', '2026-10-20T19:00:00Z' aj '…+00:00' → UTC."""
    return (
        pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")
    )


def log_loss(p_home: pd.Series, home_won: pd.Series) -> pd.Series:
    p = p_home.clip(1e-6, 1 - 1e-6)
    y = home_won.astype(float)
    return -(y * p.map(math.log) + (1 - y) * (1 - p).map(math.log))


def scored(games: pd.DataFrame, home_rate: float) -> pd.DataFrame:
    """Stĺpce p_home, home_won → trafený tip, log loss modelu a baseline „vždy domáci“."""
    out = games.copy()
    out["hit"] = (out["p_home"] > 0.5) == out["home_won"].astype(bool)
    out["ll"] = log_loss(out["p_home"], out["home_won"])
    out["ll_home"] = log_loss(pd.Series(home_rate, index=out.index), out["home_won"])
    return out


def check_locked(schedule: pd.DataFrame, tips: dict[str, dict], label: str) -> Check:
    """Kritérium 1: každý zápas z rozpisu má tip zamknutý pred začiatkom."""
    missing, late = [], []
    for g in schedule.itertuples(index=False):
        t = tips.get(str(g.game_id))
        name = f"{g.date} {g.away} @ {g.home}"
        if t is None:
            missing.append(name)
        elif utc(t["locked_at"]) >= g.tipoff:
            late.append(f"{name} (zamknuté {t['locked_at']}, začiatok {g.tipoff:%Y-%m-%d %H:%M} UTC)")
    problems = [f"bez tipu: {m}" for m in missing] + [f"zamknuté po začiatku: {x}" for x in late]
    return Check(
        "1. Tip zamknutý pred začiatkom",
        not problems,
        f"{len(schedule) - len(missing) - len(late)} z {len(schedule)} zápasov {label}",
        problems,
    )


def model_checks(df: pd.DataFrame, gate: Gate, first_no: int) -> list[Check]:
    """Kritériá modelu za obdobie: log loss pod hranicou, pri NBA aj nižší než baseline."""
    names = [f"{first_no}. Log loss ≤ {_num(gate.ll_limit)}"]
    if gate.beat_baseline:
        names.append(f"{first_no + 1}. Log loss nižší než baseline „vždy domáci“")
    if df.empty:
        return [Check(n, True, "zatiaľ žiadny dohratý zápas") for n in names]
    ll, ll_home = df["ll"].mean(), df["ll_home"].mean()
    out = [Check(names[0], ll <= gate.ll_limit, f"{_num(ll)} ({len(df)} zápasov)")]
    if gate.beat_baseline:
        out.append(Check(names[1], ll < ll_home, f"model {_num(ll)}, baseline {_num(ll_home)}"))
    return out


def summary(df: pd.DataFrame, gate: Gate) -> list[str]:
    if df.empty:
        return []
    return [
        "| | Obdobie G2 |",
        "|:--|--:|",
        f"| Zápasy s výsledkom | {len(df)} |",
        f"| Tip vyšiel | {int(df['hit'].sum())} ({_pct(df['hit'].mean())}) |",
        f"| Log loss modelu | {_num(df['ll'].mean())} (hranica {_num(gate.ll_limit)}) |",
        f"| Log loss baseline „vždy domáci“ ({_pct(gate.home_rate)}) | {_num(df['ll_home'].mean())} |",
        "",
    ]


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float) -> str:
    return f"{x:.4f}".replace(".", ",")


def _day(d: date) -> str:
    """date(2026, 11, 2) → '2. 11.'"""
    return f"{d.day}. {d.month}."


def to_markdown(gate: Gate, checks: list[Check], df: pd.DataFrame, asof: date, final: bool) -> str:
    ok = all(c.ok for c in checks)
    verdict = (
        ("✅ SPLNENÁ" if ok else "❌ NESPLNENÁ")
        if final
        else ("predbežne bez problému" if ok else "predbežne: niečo neplatí")
    )
    days = f"{_day(gate.first)} – {_day(gate.last)} {gate.last.year}"
    done_to = min(asof - timedelta(days=1), gate.last)
    running = "." if final else f", obdobie ešte beží – hodnotia sa dni do {_day(done_to)}"
    lines = [
        f"# Brána G2 – {gate.sport.upper()}: {verdict}",
        "",
        f"Obdobie {days} (dni v USA), kritériá `{gate.doc}`. Stav k {_day(asof)} {asof.year}{running}",
        "Vytvorené skriptom `team_pulse.gate_g2` (nezávislý prepočet z archívu, nie z reportu).",
        "",
        "| Kritérium | | Stav |",
        "|:--|:-:|:--|",
        *[f"| {c.name} | {'✅' if c.ok else '❌'} | {c.detail} |" for c in checks],
        "",
        *summary(df, gate),
    ]
    problems = [(c.name, p) for c in checks for p in c.problems]
    if problems:
        lines += ["## Problémy", ""] + [f"- {name}: {p}" for name, p in problems] + [""]
    return "\n".join(lines)


def days_done(gate: Gate, asof: date) -> tuple[date, bool]:
    """Posledný deň obdobia, ktorý už prebehol (asof je deň v USA), a či je obdobie celé za nami."""
    last = min(gate.last, asof - timedelta(days=1))
    return last, asof > gate.last


# --- NBA ----------------------------------------------------------------------------------------------


def nba_schedule(state: dict, first: date, last: date) -> pd.DataFrame:
    games = pd.DataFrame(state["schedule"])
    games = games[
        (games["kind"] == "regular")
        & (games["date"] >= first.isoformat())
        & (games["date"] <= last.isoformat())
    ]
    games = games.assign(tipoff=games["tipoff_utc"].map(utc), game_id=games["game_id"].astype(str))
    return games.sort_values(["tipoff", "game_id"]).reset_index(drop=True)


def nba_archive(pred_dir: Path, result_dir: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    tips, results = {}, {}
    for path in sorted(pred_dir.glob("*.json")):
        for gid, t in json.loads(path.read_text(encoding="utf-8"))["games"].items():
            tips[gid] = {**t, "date": path.stem}
        res = result_dir / path.name
        if res.exists():
            results.update(json.loads(res.read_text(encoding="utf-8"))["games"])
    return tips, results


def nba_frame(tips: dict[str, dict], results: dict[str, dict], home_rate: float) -> pd.DataFrame:
    """Uložené zápasy základnej časti s výsledkom (rozsah reportu reports/live.md)."""
    rows = [
        {
            "game_id": gid,
            "date": t["date"],
            "p_home": float(t["p_home"]),
            "home_won": results[gid]["pts_home"] > results[gid]["pts_away"],
        }
        for gid, t in tips.items()
        if t.get("kind", "regular") == "regular" and gid in results
    ]
    df = pd.DataFrame(rows, columns=["game_id", "date", "p_home", "home_won"])
    return scored(df, home_rate) if len(df) else df.assign(hit=[], ll=[], ll_home=[])


def parse_nba_report(text: str) -> dict[str, str] | None:
    """Čísla zo sekcie základnej časti v reports/live.md (ako sú vypísané)."""
    rows = dict(re.findall(r"^\| (Zápasy|Presnosť|Log loss|Brier) \| ([^|(]+?)\s*(?:\(|\|)", text, re.M))
    return rows or None


def nba_report_check(df: pd.DataFrame, report_text: str) -> Check:
    """Kritérium 3: nezávislý prepočet = čísla v reports/live.md."""
    rep = parse_nba_report(report_text)
    if df.empty:
        ok = rep is None
        return Check(
            "3. Prepočet = report",
            ok,
            "zatiaľ žiadny zápas s výsledkom" + ("" if ok else ", report má čísla"),
        )
    if rep is None:
        return Check(
            "3. Prepočet = report", False, "report nemá čísla základnej časti", ["report bez tabuľky"]
        )
    y = df["home_won"].astype(float)
    mine = {
        "Zápasy": str(len(df)),
        "Presnosť": _pct(df["hit"].mean()),
        "Log loss": _num(df["ll"].mean()),
        "Brier": _num(((df["p_home"] - y) ** 2).mean()),
    }
    diff = [f"{k}: prepočet {v}, report {rep.get(k)}" for k, v in mine.items() if rep.get(k) != v]
    return Check(
        "3. Prepočet = report", not diff, f"{mine['Zápasy']} zápasov, log loss {mine['Log loss']}", diff
    )


def state_history(
    path: str = "state/state.json", since: date | None = None, cwd: Path | None = None
) -> list[tuple[pd.Timestamp, str]]:
    """(čas commitu v UTC, last_result) pre každý commit stavu v histórii gitu."""
    args = (
        ["git", "log", "--format=%H %cI"] + ([f"--since={since.isoformat()}"] if since else []) + ["--", path]
    )
    out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.split()
    hist = []
    for sha, when in zip(out[::2], out[1::2], strict=True):
        blob = subprocess.run(
            ["git", "show", f"{sha}:{path}"], cwd=cwd, capture_output=True, text=True, check=True
        )
        hist.append((pd.Timestamp(when).tz_convert("UTC"), json.loads(blob.stdout)["last_result"]))
    return sorted(hist)


def nba_state_check(
    history: list[tuple[pd.Timestamp, str]], schedule: pd.DataFrame, first: date, last: date
) -> Check:
    """Kritérium 4: každé ráno do 12:00 nášho času je v main stav s výsledkami predchádzajúceho dňa (ET)."""
    played = set(schedule["date"])
    problems, checked = [], 0
    day = first + timedelta(days=1)
    while day <= last + timedelta(days=1):
        prev = (day - timedelta(days=1)).isoformat()
        if prev in played:
            checked += 1
            deadline = pd.Timestamp(datetime.combine(day, STATE_DEADLINE, LOCAL)).tz_convert("UTC")
            before = [lr for when, lr in history if when <= deadline]
            have = before[-1] if before else None
            if have is None or have < prev:
                problems.append(f"{_day(day)} do 12:00: stav s výsledkami do {have}, chýba {prev}")
        day += timedelta(days=1)
    return Check(
        "4. Stav do 12:00 s výsledkami noci",
        not problems,
        f"{checked - len(problems)} z {checked} rán",
        problems,
    )


def evaluate_nba(
    state: dict,
    tips: dict[str, dict],
    results: dict[str, dict],
    report_text: str,
    history: list[tuple[pd.Timestamp, str]],
    asof: date,
    gate: Gate = NBA,
) -> tuple[list[Check], pd.DataFrame, bool]:
    last, final = days_done(gate, asof)
    sched = nba_schedule(state, gate.first, last)
    checks = [check_locked(sched, tips, "v rozpise")]
    no_result = [f"{g.date} {g.away} @ {g.home}" for g in sched.itertuples() if g.game_id not in results]
    checks.append(
        Check(
            "2. Výsledok v archíve",
            not no_result,
            f"{len(sched) - len(no_result)} z {len(sched)} zápasov",
            [f"bez výsledku: {x}" for x in no_result],
        )
    )
    every = nba_frame(tips, results, gate.home_rate)
    checks.append(nba_report_check(every, report_text))
    checks.append(nba_state_check(history, sched, gate.first, last))
    period = every[every["game_id"].isin(set(sched["game_id"]))]
    checks += model_checks(period, gate, 5)
    return checks, period, final


# --- NHL ----------------------------------------------------------------------------------------------


def nhl_schedule(season: pd.DataFrame, first: date, last: date) -> pd.DataFrame:
    """Zápasy základnej časti z API NHL v období, kluby pod dnešnou skratkou."""
    from team_pulse.nhl.fetch_games import franchise

    g = season[
        (season["game_type"] == "R")
        & (season["date"] >= first.isoformat())
        & (season["date"] <= last.isoformat())
    ]
    return (
        g.assign(
            game_id=g["game_id"].astype(str),
            home=g["home_abbr"].map(franchise),
            away=g["away_abbr"].map(franchise),
            tipoff=g["start_utc"].map(utc),
        )
        .sort_values(["tipoff", "game_id"])
        .reset_index(drop=True)
    )


def nhl_tips(archive: Path) -> dict[str, dict]:
    tips = {}
    for path in sorted(archive.glob("*.json")):
        tips.update(json.loads(path.read_text(encoding="utf-8"))["games"])
    return tips


def nhl_frame(tips: dict[str, dict], season: pd.DataFrame, home_rate: float) -> pd.DataFrame:
    """Tipy zamknuté pred začiatkom s výsledkom z API NHL (rozsah reportu reports/nhl_live.md)."""
    from team_pulse.nhl.fetch_games import FINISHED

    done = season[season["state"].isin(FINISHED)]
    done = done.set_index(done["game_id"].astype(str))
    rows = []
    for gid, t in tips.items():
        if gid not in done.index or utc(t["locked_at"]) >= utc(t["tipoff_utc"]):
            continue
        g = done.loc[gid]
        rows.append(
            {
                "game_id": gid,
                "date": t["date"],
                "p_home": float(t["p_home"]),
                "home_won": int(g["goals_home"]) > int(g["goals_away"]),
            }
        )
    df = pd.DataFrame(rows, columns=["game_id", "date", "p_home", "home_won"])
    return scored(df, home_rate) if len(df) else df.assign(hit=[], ll=[], ll_home=[])


def parse_nhl_report(text: str) -> tuple[tuple[int, int, str] | None, dict[str, tuple[int, int]]]:
    """(tip vyšiel, zápasy, log loss) zo „Spolu“ a {„13. 10.“: (zápasy, tip vyšiel)} z tabuľky po dňoch."""
    m = re.search(r"\*\*Spolu: (\d+) z (\d+) \([^)]*\), log loss ([\d,]+)\*\*", text)
    total = (int(m.group(1)), int(m.group(2)), m.group(3)) if m else None
    days = {
        f"{d}. {mo}.": (int(n), int(h))
        for d, mo, n, h in re.findall(r"^\| (\d+)\. (\d+)\.\s*\|\s*(\d+) \|\s*(\d+) \|", text, re.M)
    }
    return total, days


def nhl_report_checks(
    df: pd.DataFrame, period: pd.DataFrame, sched: pd.DataFrame, report_text: str
) -> list[Check]:
    """Kritérium 2: každý zápas obdobia je dohratý a vyhodnotený v reporte (počty po dňoch sedia).
    Kritérium 3: nezávislý prepočet všetkých tipov = „Spolu“ a tabuľka po dňoch v reports/nhl_live.md."""
    from team_pulse.nhl.fetch_games import FINISHED

    total, days = parse_nhl_report(report_text)
    unfinished = [
        f"{g.date} {g.away} @ {g.home} (stav {g.state})"
        for g in sched.itertuples()
        if g.state not in FINISHED
    ]
    missing = sorted(set(sched["game_id"]) - set(period["game_id"]))
    names = {g.game_id: f"{g.date} {g.away} @ {g.home}" for g in sched.itertuples()}

    def day_rows(frame: pd.DataFrame) -> dict[str, tuple[int, int]]:
        agg = frame.groupby("date")["hit"].agg(["size", "sum"])
        return {f"{int(d[8:10])}. {int(d[5:7])}.": (int(r["size"]), int(r["sum"])) for d, r in agg.iterrows()}

    p2 = [f"nedohraný alebo odložený: {u}" for u in unfinished]
    p2 += [
        f"bez vyhodnotenia: {names[g]}" for g in missing if names.get(g) and g not in {u for u in unfinished}
    ]
    p2 += [
        f"{k}: prepočet {v}, report {days.get(k)}" for k, v in day_rows(period).items() if days.get(k) != v
    ]
    c2 = Check(
        "2. Zápas dohratý a vyhodnotený v reporte", not p2, f"{len(period)} z {len(sched)} zápasov", p2
    )

    if df.empty:
        return [c2, Check("3. Prepočet = report", total is None, "zatiaľ žiadny dohratý zápas")]
    mine = (int(df["hit"].sum()), len(df), _num(df["ll"].mean()))
    p3 = [] if total == mine else [f"Spolu: prepočet {mine}, report {total}"]
    p3 += [f"{k}: prepočet {v}, report {days.get(k)}" for k, v in day_rows(df).items() if days.get(k) != v]
    c3 = Check("3. Prepočet = report", not p3, f"{mine[1]} zápasov, vyšlo {mine[0]}, log loss {mine[2]}", p3)
    return [c2, c3]


def evaluate_nhl(
    season: pd.DataFrame, tips: dict[str, dict], report_text: str, asof: date, gate: Gate = NHL
) -> tuple[list[Check], pd.DataFrame, bool]:
    last, final = days_done(gate, asof)
    sched = nhl_schedule(season, gate.first, last)
    every = nhl_frame(tips, season, gate.home_rate)
    period = every[every["game_id"].isin(set(sched["game_id"]))]
    checks = [
        check_locked(sched, tips, "v rozpise NHL"),
        *nhl_report_checks(every, period, sched, report_text),
    ]
    checks += model_checks(period, gate, 4)
    return checks, period, final


# --- spustenie ------------------------------------------------------------------------------------------


def today_et(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(ET).date()


def main(sport: str, asof: date | None = None, out_dir: Path = Path("reports")) -> bool:
    asof = asof or today_et()
    if sport == "nba":
        gate = NBA
        state = json.loads(Path("state/state.json").read_text(encoding="utf-8"))
        tips, results = nba_archive(Path("archive/predictions"), Path("archive/results"))
        history = state_history(since=gate.first - timedelta(days=2))
        checks, df, final = evaluate_nba(
            state, tips, results, gate.report.read_text(encoding="utf-8"), history, asof
        )
    else:
        import requests

        from team_pulse.nhl.fetch_games import fetch_season

        gate = NHL
        season = fetch_season(requests.Session(), 2027)
        tips = nhl_tips(Path("archive/nhl/predictions"))
        checks, df, final = evaluate_nhl(season, tips, gate.report.read_text(encoding="utf-8"), asof)
    out = out_dir / f"gate_g2_{gate.sport}.md"
    out.write_text(to_markdown(gate, checks, df, asof, final), encoding="utf-8")
    for c in checks:
        print(f"{'✅' if c.ok else '❌'} {c.name}: {c.detail}")
        for p in c.problems[:10]:
            print(f"     {p}")
    ok = all(c.ok for c in checks)
    print(f"\n{'Konečný' if final else 'Predbežný'} výsledok: {'splnené' if ok else 'NESPLNENÉ'} → {out}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sport", choices=["nba", "nhl"])
    ap.add_argument("--asof", type=date.fromisoformat, default=None, help="deň v USA (ET), predvolene dnes")
    a = ap.parse_args()
    raise SystemExit(0 if main(a.sport, a.asof) else 1)
