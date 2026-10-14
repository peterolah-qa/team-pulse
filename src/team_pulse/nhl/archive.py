"""Archív NHL tipov a ich vyhodnotenie po zápasoch (ostrá skúška na vetve nhl).

Zamknutie: každý beh `team_pulse.nhl.predict` uloží tipy do archive/nhl/predictions/<deň ET>.json.
Tip sa dá prepísať len do začiatku zápasu, po začiatku ostane posledný tip spred zápasu.
Vyhodnotenie: tip vs. skutočný výsledok, presnosť a log loss po dňoch → reports/nhl_live.md.

Spustenie (z Macu, ráno po zápasoch):  uv run python -m team_pulse.nhl.archive
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from team_pulse.nhl.fetch_games import fetch_season, finished_games, season_of, today_et

ARCHIVE = Path("archive/nhl/predictions")
REPORT = Path("reports/nhl_live.md")
EXTRA = {"OT": " pp", "SO": " sn"}  # po predĺžení, po samostatných nájazdoch


def _start(g: dict) -> datetime:
    return datetime.fromisoformat(g["tipoff_utc"].replace("Z", "+00:00"))


def lock(data: dict, now: datetime, archive: Path = ARCHIVE) -> int:
    """Uloží tipy na zápasy, ktoré ešte nezačali. Vráti počet zamknutých tipov."""
    archive.mkdir(parents=True, exist_ok=True)
    locked = 0
    for day, games in data["days"].items():
        path = archive / f"{day}.json"
        stored = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"games": {}}
        changed = False
        for g in games:
            if _start(g) <= now:
                continue  # zápas začal: platí tip zamknutý pred začiatkom
            stored["games"][g["game_id"]] = {
                **g,
                "model": data["model"],
                "locked_at": now.isoformat(timespec="seconds"),
            }
            locked += 1
            changed = True
        if changed:
            stored["games"] = dict(
                sorted(stored["games"].items(), key=lambda kv: (kv[1]["tipoff_utc"], kv[0]))
            )
            path.write_text(json.dumps(stored, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return locked


def load_tips(archive: Path = ARCHIVE) -> list[dict]:
    tips = []
    for path in sorted(archive.glob("*.json")):
        tips += json.loads(path.read_text(encoding="utf-8"))["games"].values()
    return tips


def evaluate(tips: list[dict], results: pd.DataFrame) -> pd.DataFrame:
    """Jeden riadok na dohratý zápas s tipom zamknutým pred začiatkom."""
    res = {str(r.game_id): r for r in results.itertuples(index=False)}
    rows = []
    for t in tips:
        r = res.get(t["game_id"])
        if r is None or datetime.fromisoformat(t["locked_at"]) >= _start(t):
            continue
        home_won = r.goals_home > r.goals_away
        winner = t["home"]["team"] if home_won else t["away"]["team"]
        p_tip = t["p_home"] if t["tip"] == t["home"]["team"] else 1 - t["p_home"]
        rows.append({
            "date": t["date"], "game_id": t["game_id"], "away": t["away"]["team"], "home": t["home"]["team"],
            "tip": t["tip"], "p_tip": p_tip, "p_home": t["p_home"], "home_won": home_won,
            "hit": t["tip"] == winner,
            "score": f"{r.goals_away}:{r.goals_home}{EXTRA.get(r.last_period, '')}",
        })  # fmt: skip
    return pd.DataFrame(rows)


def log_loss(df: pd.DataFrame) -> float:
    p = df["p_home"].clip(1e-6, 1 - 1e-6)
    y = df["home_won"].astype(float)
    return float(-(y * p.map(math.log) + (1 - y) * (1 - p).map(math.log)).mean())


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _day(iso: str) -> str:
    d = datetime.fromisoformat(iso)
    return f"{d.day}. {d.month}."


def to_markdown(df: pd.DataFrame) -> str:
    head = (
        "# NHL – ostré tipy\n\n"
        "Tipy zamknuté pred začiatkom zápasu (`team_pulse.nhl.predict`), vyhodnotené po zápase. "
        "Model Elo + únava, v teste 2023/24 – 2025/26 mal presnosť 57,6 %.\n\n"
    )
    if df.empty:
        return head + "Zatiaľ žiadny dohratý zápas so zamknutým tipom.\n"
    days = (
        df.groupby("date")
        .agg(zapasy=("hit", "size"), vyslo=("hit", "sum"))
        .assign(presnost=lambda d: (d["vyslo"] / d["zapasy"]).map(_pct))
        .reset_index()
    )
    days["date"] = days["date"].map(_day)
    days.columns = ["deň (USA)", "zápasy", "tip vyšiel", "presnosť"]
    last = df[df["date"] == df["date"].max()].copy()
    last["zápas"] = last["away"] + " @ " + last["home"]
    last["šanca"] = last["p_tip"].map(lambda p: f"{round(p * 100)} %")
    last["výsledok"] = last["score"]
    last[""] = last["hit"].map({True: "✅", False: "❌"})
    last = last[["zápas", "tip", "šanca", "výsledok", ""]]
    return (
        head
        + f"**Spolu: {int(df['hit'].sum())} z {len(df)} ({_pct(df['hit'].mean())}), log loss "
        + f"{log_loss(df):.4f}".replace(".", ",")
        + "**\n\n"
        + f"## Po dňoch\n\n{days.to_markdown(index=False)}\n\n"
        + f"## Posledný deň ({_day(df['date'].max())})\n\n"
        + "Výsledok je hostia : domáci, pp = po predĺžení, sn = po nájazdoch.\n\n"
        + f"{last.to_markdown(index=False)}\n"
    )


def main(archive: Path = ARCHIVE, out: Path = REPORT) -> pd.DataFrame:
    now = datetime.now(UTC)
    current = fetch_season(requests.Session(), season_of(today_et(now)))
    df = evaluate(load_tips(archive), finished_games(current))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(df), encoding="utf-8")
    if df.empty:
        print("Zatiaľ žiadny dohratý zápas so zamknutým tipom.")
    else:
        hits, n = int(df["hit"].sum()), len(df)
        print(f"Spolu: tip vyšiel {hits} z {n} ({hits / n:.1%}), log loss {log_loss(df):.4f}")
        for r in df[df["date"] == df["date"].max()].itertuples(index=False):
            mark = "✅" if r.hit else "❌"
            print(f"{mark} {r.away} @ {r.home}  tip {r.tip} {round(r.p_tip * 100)} %  {r.score}")
    print(f"Report: {out}")
    return df


if __name__ == "__main__":
    main()
