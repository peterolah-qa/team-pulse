"""Ostré tipy NFL: zamknutie pred výkopom a vyhodnotenie, dva modely s vlastnými bránami G2.

- `nfl-elo-v1` = Elo z brány G0-NFL (K 20, výhoda domáceho 48, prenos 0,6), od týždňa 8, docs/gate-nfl-G2.md.
- `nfl-elo-qb-v1` = to isté Elo + náhradník quarterback (−65 Elo, team_pulse.nfl.qb), od týždňa 10,
  docs/gate-nfl-qb-G2.md. Schválil Peter 28. 10. 2026.
Počas svojej G2 sa žiadny model nemení.

Postup pri každom spustení:
  1. Stiahne najnovší games.csv (nflverse, commit sa zapíše do tipu), načíta len povolené stĺpce.
  2. Elo prejde všetky odohrané zápasy.
  3. Zamkne tipy na zápasy **najbližšieho neodohraného týždňa**, ktoré ešte nezačali – len ak sú všetky
     predchádzajúce týždne sezóny dohraté (inak by tip nepoznal výsledky z minulého týždňa).
     Zamknutý tip sa už nikdy neprepíše.
  4. Vyhodnotí všetky zamknuté tipy s výsledkom → reports/nfl_live.md.

Spustenie:  uv run python -m team_pulse.nfl.predict
Výstup:     archive/nfl/predictions/<sezóna>-w<týždeň>.json, reports/nfl_live.md (Elo)
            archive/nfl/qb/predictions/…, reports/nfl_qb_live.md (Elo + quarterback)
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from team_pulse.nfl import games as G
from team_pulse.nfl.elo import NflEloParams, diff, expected, run
from team_pulse.nfl.qb import BACKUP_PENALTY, adjusted_diff, backup_flags

MODEL = "nfl-elo-v1"
PARAMS = NflEloParams(k=20.0, hfa=48.0, carryover=0.6)
ARCHIVE = Path("archive/nfl/predictions")
REPORT = Path("reports/nfl_live.md")
ET = ZoneInfo("America/New_York")
COMMITS = "https://api.github.com/repos/nflverse/nfldata/commits/master"
G2_FROM = "2026-10-29"  # prvý deň G2-NFL (týždeň 8)
G2_TO = "2027-01-10"  # koniec základnej časti
G2_LIMIT = 0.6620  # hranica log loss G2-NFL (docs/gate-nfl-G2.md)


@dataclass(frozen=True)
class Model:
    name: str
    label: str
    backup_penalty: float  # 0 = bez vrstvy quarterback
    start: tuple[int, int]  # (sezóna, týždeň) prvých tipov
    archive: Path
    report: Path
    gate: str
    g2_from: str
    g2_to: str
    g2_limit: float


ELO = Model(
    MODEL,
    "Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6",
    0.0,
    (2026, 8),
    ARCHIVE,
    REPORT,
    "docs/gate-nfl-G2.md",
    G2_FROM,
    G2_TO,
    G2_LIMIT,
)
ELO_QB = Model(
    "nfl-elo-qb-v1",
    f"Elo z G0-NFL + náhradník quarterback −{BACKUP_PENALTY:g} Elo",
    BACKUP_PENALTY,
    (2026, 10),
    Path("archive/nfl/qb/predictions"),
    Path("reports/nfl_qb_live.md"),
    "docs/gate-nfl-qb-G2.md",
    "2026-11-12",
    G2_TO,
    0.6602,
)
MODELS = (ELO, ELO_QB)


def kickoff_utc(day: pd.Timestamp, gametime: object) -> pd.Timestamp | None:
    """Dátum a čas výkopu z games.csv (čas je vždy ET) → UTC. Bez času nevieme, kedy začína → None."""
    if not isinstance(gametime, str) or ":" not in gametime:
        return None
    hh, mm = (int(x) for x in gametime.split(":"))
    local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=ET)
    return pd.Timestamp(local.astimezone(UTC))


def latest_commit(session: requests.Session) -> str:
    token = os.environ.get("GITHUB_TOKEN")  # v GitHub Actions: vyšší limit API
    headers = {"Authorization": f"Bearer {token}"} if token else None
    r = session.get(COMMITS, headers=headers, timeout=30)
    r.raise_for_status()
    return str(r.json()["sha"])


def week_file(season: int, week: int, archive: Path = ARCHIVE) -> Path:
    return archive / f"{season}-w{week:02d}.json"


def locked(archive: Path = ARCHIVE) -> dict[str, dict]:
    """Všetky už zamknuté tipy podľa game_id."""
    out: dict[str, dict] = {}
    for f in sorted(archive.glob("*.json")):
        for t in json.loads(f.read_text(encoding="utf-8"))["tips"]:
            out[t["game_id"]] = t
    return out


def next_week(games: pd.DataFrame) -> tuple[int, int] | None:
    """(sezóna, týždeň) najbližšieho týždňa s neodohraným zápasom v poslednej sezóne, alebo None."""
    season = int(games["season"].max())
    open_ = games[(games["season"] == season) & ~games["played"]]
    return (season, int(open_["week"].min())) if len(open_) else None


def tips_for_week(
    games: pd.DataFrame,
    season: int,
    week: int,
    now: pd.Timestamp,
    commit: str,
    already: set[str],
    model: Model = ELO,
) -> tuple[list[dict], list[str]]:
    """Nové tipy modelu na zápasy týždňa, ktoré ešte nezačali. Vráti (tipy, problémy)."""
    if (season, week) < model.start:
        return [], []
    problems = []
    earlier = games[(games["season"] == season) & (games["week"] < week) & ~games["played"]]
    if len(earlier):
        names = ", ".join(f"{r.away} @ {r.home} ({r.week}. týždeň)" for r in earlier.itertuples())
        return [], [f"predchádzajúce týždne nie sú dohraté: {names} – tipy sa nezamkli"]
    r = run(games, PARAMS)
    flags = backup_flags(r) if model.backup_penalty else None
    week_games = r[(r["season"] == season) & (r["week"] == week)]
    tips = []
    for i, g in zip(week_games.index, week_games.itertuples(index=False), strict=True):
        if g.game_id in already or g.played:
            continue
        ko = kickoff_utc(g.date, g.gametime)
        if ko is None:
            problems.append(f"{g.away} @ {g.home}: chýba čas výkopu – bez tipu")
            continue
        if ko <= now:
            problems.append(f"{g.away} @ {g.home}: už začal ({ko:%Y-%m-%d %H:%M} UTC) – bez tipu")
            continue
        d = diff(g.elo_home_pre, g.elo_away_pre, PARAMS, bool(g.neutral), bool(g.playoff))
        extra = {}
        if flags is not None:
            bh, ba = int(flags.at[i, "home_backup"]), int(flags.at[i, "away_backup"])
            d = adjusted_diff(d, bh, ba, model.backup_penalty)
            extra = {
                "home_backup": bh,
                "away_backup": ba,
                "home_primary_qb_id": flags.at[i, "home_primary"],
                "away_primary_qb_id": flags.at[i, "away_primary"],
            }
        tips.append(
            {
                "game_id": g.game_id,
                "espn_id": None if pd.isna(g.espn_id) else str(g.espn_id),
                "season": season,
                "week": week,
                "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ"),
                "home": g.home,
                "away": g.away,
                "neutral": bool(g.neutral),
                "playoff": bool(g.playoff),
                "elo_home": round(float(g.elo_home_pre), 1),
                "elo_away": round(float(g.elo_away_pre), 1),
                "elo_diff": round(d, 1),
                "p_home": round(expected(d), 4),
                "home_qb": None if pd.isna(g.home_qb) else g.home_qb,
                "away_qb": None if pd.isna(g.away_qb) else g.away_qb,
                **extra,
                "model": model.name,
                "games_commit": commit,
                "locked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return tips, problems


def save(
    tips: list[dict], season: int, week: int, archive: Path = ARCHIVE, model: str = MODEL
) -> Path | None:
    """Pridá nové tipy do súboru týždňa; existujúce tipy sa nemenia."""
    if not tips:
        return None
    f = week_file(season, week, archive)
    old = json.loads(f.read_text(encoding="utf-8"))["tips"] if f.exists() else []
    have = {t["game_id"] for t in old}
    new = [t for t in tips if t["game_id"] not in have]
    all_tips = sorted(old + new, key=lambda t: (t["kickoff_utc"], t["game_id"]))
    f.parent.mkdir(parents=True, exist_ok=True)
    body = {"sport": "nfl", "season": season, "week": week, "model": model, "tips": all_tips}
    f.write_text(json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return f


def evaluate(tips: dict[str, dict], games: pd.DataFrame, model: Model = ELO) -> pd.DataFrame:
    """Zamknuté tipy s výsledkom (remíza sa nevyhodnocuje). Tip = domáci pri p_home > 0,5, inak hostia."""
    res = games.set_index("game_id")
    rows = []
    for gid, t in tips.items():
        if gid not in res.index:
            continue
        g = res.loc[gid]
        if not g["played"] or g["tie"]:
            continue
        home_won = bool(g["score_home"] > g["score_away"])
        p = min(max(float(t["p_home"]), 1e-6), 1 - 1e-6)
        pick_home = p > 0.5
        rows.append(
            {
                "game_id": gid,
                "week": int(t["week"]),
                "kickoff_utc": t["kickoff_utc"],
                "zapas": f"{t['away']} @ {t['home']}",
                "tip": t["home"] if pick_home else t["away"],
                "sanca": p if pick_home else 1 - p,
                "vysledok": f"{int(g['score_away'])}:{int(g['score_home'])}",
                "hit": pick_home == home_won,
                "ll": -math.log(p if home_won else 1 - p),
                "brier": (p - float(home_won)) ** 2,
                "g2": model.g2_from <= t["kickoff_utc"][:10] <= model.g2_to,
            }
        )
    return pd.DataFrame(rows).sort_values(["kickoff_utc", "game_id"]) if rows else pd.DataFrame(rows)


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float) -> str:
    return f"{x:.4f}".replace(".", ",")


def report(tips: dict[str, dict], games: pd.DataFrame, now: pd.Timestamp, model: Model = ELO) -> str:
    ev = evaluate(tips, games, model)
    pending = len(tips) - len(ev)
    head = (
        f"# NFL – ostré tipy (`{model.name}`)\n\n"
        f"Model `{model.name}` ({model.label}), tipy zamknuté pred výkopom "
        "(`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). "
        f"Brána G2 {model.g2_from} – {model.g2_to}: log loss ≤ {_num(model.g2_limit)} (`{model.gate}`).\n\n"
        f"Stav k {now:%Y-%m-%d %H:%M} UTC: zamknutých tipov {len(tips)}, vyhodnotených {len(ev)}, "
        f"čaká na výsledok {pending}.\n\n"
    )
    if ev.empty:
        return head + "Zatiaľ žiadny vyhodnotený zápas.\n"
    total = (
        f"**Spolu: {int(ev['hit'].sum())} z {len(ev)} ({_pct(ev['hit'].mean())}), "
        f"log loss {_num(ev['ll'].mean())}, Brier {_num(ev['brier'].mean())}**\n\n"
    )
    weeks = ev.groupby("week").agg(zapasy=("hit", "size"), vyslo=("hit", "sum"), ll=("ll", "mean"))
    weeks["presnosť"] = (weeks["vyslo"] / weeks["zapasy"]).map(_pct)
    weeks["log loss"] = weeks["ll"].map(_num)
    weeks = weeks.drop(columns="ll").rename(columns={"zapasy": "zápasy", "vyslo": "tip vyšiel"})
    weeks.index.name = "týždeň"
    last = ev[ev["week"] == ev["week"].max()].copy()
    last["šanca"] = last["sanca"].map(lambda x: f"{round(x * 100)} %")
    last[""] = last["hit"].map(lambda h: "✅" if h else "❌")
    last = last[["zapas", "tip", "šanca", "vysledok", ""]].rename(
        columns={"zapas": "zápas", "vysledok": "výsledok"}
    )
    return (
        head
        + total
        + f"## Po týždňoch\n\n{weeks.to_markdown()}\n\n"
        + f"## Posledný týždeň ({int(ev['week'].max())}.)\n\nVýsledok je hostia : domáci.\n\n"
        + f"{last.to_markdown(index=False)}\n"
    )


def main(now: datetime | None = None, commit: str | None = None) -> int:
    t = pd.Timestamp(now or datetime.now(UTC))
    session = requests.Session()
    commit = commit or latest_commit(session)
    games = G.load(G.download(commit, session))
    nxt = next_week(games)
    for model in MODELS:
        if nxt:
            new, problems = tips_for_week(games, *nxt, t, commit, set(locked(model.archive)), model)
            f = save(new, *nxt, model.archive, model.name)
            print(f"{model.name}, týždeň {nxt[1]}: nových tipov {len(new)}" + (f" → {f}" if f else ""))
            for tip in new:
                fav = tip["home"] if tip["p_home"] > 0.5 else tip["away"]
                p = max(tip["p_home"], 1 - tip["p_home"])
                print(f"  {tip['kickoff_utc']} {tip['away']} @ {tip['home']}: tip {fav} {p:.0%}")
            for p in problems:
                print(f"! {p}")
        tips = locked(model.archive)
        if tips or (nxt and nxt >= model.start):
            model.report.parent.mkdir(parents=True, exist_ok=True)
            model.report.write_text(report(tips, games, t, model), encoding="utf-8")
            print(f"Report: {model.report}")
    if not nxt:
        print("Sezóna nemá neodohrané zápasy.")
    print(f"games.csv {commit[:7]}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default=None, help="commit nflverse/nfldata (predvolene najnovší)")
    raise SystemExit(main(commit=ap.parse_args().commit))
