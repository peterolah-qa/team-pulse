"""Stav modelu: všetko, čo predikcia potrebuje, v jednom malom JSON súbore.

Mac (má prístup k nba_api) raz denne vytvorí state/state.json:
    Elo teamov · hodnoty a typické minúty hráčov · rotácie · súpisky · rozpis sezóny
Cloud (GitHub Actions) z neho + aktuálnych zranení ESPN spočíta predpovede.
Celá história (stovky MB) tak zostáva na Macu.

Spustenie (z Macu):  uv run python -m team_pulse.state
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from team_pulse.elo import EloParams, rating_for_season, run
from team_pulse.live.availability import Snapshot, player_snapshot, season_rotation

STATE = Path("state/state.json")
STATE_VERSION = 1
TREND_GAMES = 10
RESULT_DAYS = 3  # výsledky a štatistiky hráčov z posledných 3 hracích dní (pre appku)
SCHEDULE_FIELDS = ["game_id", "date", "tipoff_utc", "season", "kind", "home", "away", "neutral", "arena_city"]


def build_state(
    history: pd.DataFrame,
    players: pd.DataFrame,
    roster: pd.DataFrame,
    schedule: pd.DataFrame,
    elo_params: dict,
) -> dict:
    season = int(schedule["season"].max())
    p = EloParams(**elo_params)
    teams = set(history["home"]) | set(history["away"])
    res = run(history, p, initial={t: p.mean for t in teams})
    ratings: dict[str, tuple[float, int]] = {}
    games_of: dict[str, list[dict]] = {}
    for r in res.itertuples(index=False):
        ratings[r.home] = (r.elo_home_post, int(r.season))
        ratings[r.away] = (r.elo_away_post, int(r.season))
        for team, opp, home, pts, opp_pts, e in (
            (r.home, r.away, True, r.pts_home, r.pts_away, r.elo_home_post),
            (r.away, r.home, False, r.pts_away, r.pts_home, r.elo_away_post),
        ):
            entry = {"date": str(r.date.date()), "opp": opp, "home": home, "pts": int(pts)}
            entry.update(opp_pts=int(opp_pts), elo=round(float(e), 1))
            games_of.setdefault(team, []).append(entry)
    rosters = {t: sorted(int(x) for x in g["player_id"]) for t, g in roster.groupby("team")}
    elo = {t: round(rating_for_season(ratings.get(t, (p.mean, season)), season, p), 2) for t in rosters}

    snap = player_snapshot(players)
    rotation = season_rotation(players, season)
    keep = {pid for ids in rosters.values() for pid in ids} | {pid for r in rotation.values() for pid in r}
    names = dict(zip(roster["player_id"].astype(int), roster["player"], strict=True))
    player_info = {
        str(pid): {
            "name": names.get(pid) or snap.name.get(pid, str(pid)),
            "value": round(snap.value[pid], 5) if pid in snap.value else None,
            "typical_min": round(snap.typical_min[pid], 2) if pid in snap.typical_min else None,
        }
        for pid in sorted(keep)
    }
    sched = schedule[schedule["season"] == season][SCHEDULE_FIELDS].copy()
    sched["date"] = sched["date"].dt.strftime("%Y-%m-%d")
    sched["tipoff_utc"] = sched["tipoff_utc"].astype(str)
    return {
        "version": STATE_VERSION,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "season": season,
        "last_result": str(history["date"].max().date()),
        "elo": elo,
        "elo_history": {t: games_of.get(t, [])[-TREND_GAMES:] for t in rosters},
        "rosters": rosters,
        "players": player_info,
        "rotation": {t: {str(pid): round(m, 2) for pid, m in r.items()} for t, r in rotation.items()},
        "schedule": sched.to_dict(orient="records"),
        "results": recent_results(history, players, schedule),
    }


def _box(rows: pd.DataFrame) -> list[dict]:
    """Štatistiky hráčov jedného teamu, zoradené podľa minút."""
    rows = rows.sort_values(["min", "pts"], ascending=False)
    return [
        {
            "player": r.player,
            "min": round(float(r.min)),
            "pts": int(r.pts),
            "reb": int(r.oreb) + int(r.dreb),
            "ast": int(r.ast),
            "blk": int(r.blk),
            "stl": int(r.stl),
        }
        for r in rows.itertuples()
    ]


def recent_results(
    history: pd.DataFrame, players: pd.DataFrame, schedule: pd.DataFrame, days: int = RESULT_DAYS
) -> list[dict]:
    """Dohrané zápasy aktuálnej sezóny z posledných hracích dní: skóre a štatistiky hráčov.

    Základná časť a playoff sú z histórie (box score z nba_api). Príprava len zo skóre v rozpise,
    štatistiky hráčov z prípravy nesťahujeme (do histórie ani do Ela nepatria).
    """
    season = int(schedule["season"].max())
    kinds = schedule["kind"] if "kind" in schedule else pd.Series("regular", index=schedule.index)
    kind_of = dict(zip(schedule["game_id"].astype(str), kinds, strict=True))
    cols = ["game_id", "date", "home", "away", "pts_home", "pts_away"]
    done = history[history["season"] == season][cols].assign(game_id=lambda d: d["game_id"].astype(str))
    done["kind"] = done["game_id"].map(kind_of).fillna("regular")
    if {"kind", "status", "pts_home"} <= set(schedule.columns):
        pre = schedule[(schedule["kind"] == "preseason") & (schedule["status"] == 3)][cols]
        done = pd.concat([done, pre.assign(kind="preseason", game_id=pre["game_id"].astype(str))])
    if done.empty:
        return []
    done["date"] = pd.to_datetime(done["date"])
    last = sorted(done["date"].unique())[-days:]
    done = done[done["date"].isin(last)].sort_values(["date", "game_id"])
    box = players[players["game_id"].astype(str).isin(set(done["game_id"]))]
    by_game = {gid: g for gid, g in box.groupby(box["game_id"].astype(str))}
    out = []
    for r in done.itertuples():
        g = by_game.get(r.game_id)
        out.append(
            {
                "game_id": r.game_id,
                "date": str(pd.Timestamp(r.date).date()),
                "kind": r.kind,
                "home": r.home,
                "away": r.away,
                "pts_home": int(r.pts_home),
                "pts_away": int(r.pts_away),
                "box": {} if g is None else {t: _box(g[g["team"] == t]) for t in (r.home, r.away)},
            }
        )
    return out


def save_state(state: dict, path: Path = STATE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def load_state(path: Path = STATE) -> dict:
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != STATE_VERSION:
        raise ValueError(f"nepodporovaná verzia stavu: {state.get('version')}")
    return state


# --- prevody zo stavu späť na objekty, s ktorými pracuje predikcia --------------------


def snapshot_from_state(state: dict) -> Snapshot:
    ps = state["players"]
    return Snapshot(
        value={int(k): v["value"] for k, v in ps.items() if v["value"] is not None},
        typical_min={int(k): v["typical_min"] for k, v in ps.items() if v["typical_min"] is not None},
        current_team={},
        name={int(k): v["name"] for k, v in ps.items()},
    )


def rotation_from_state(state: dict) -> dict[str, dict[int, float]]:
    return {t: {int(k): v for k, v in r.items()} for t, r in state["rotation"].items()}


def rosters_from_state(state: dict) -> dict[str, set[int]]:
    return {t: set(ids) for t, ids in state["rosters"].items()}


def roster_frame(state: dict) -> pd.DataFrame:
    """Súpiska ako tabuľka (na párovanie mien zranených hráčov)."""
    from team_pulse.live.roster import normalize_name

    rows = [
        {"player_id": pid, "player": state["players"][str(pid)]["name"], "team": t}
        for t, ids in state["rosters"].items()
        for pid in ids
    ]
    df = pd.DataFrame(rows, columns=["player_id", "player", "team"])
    df["norm"] = df["player"].map(normalize_name)
    return df


def schedule_frame(state: dict) -> pd.DataFrame:
    df = pd.DataFrame(state["schedule"])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["tipoff_utc"] = pd.to_datetime(df["tipoff_utc"], utc=True, errors="coerce")
    return df


def main() -> None:
    from team_pulse.learned import GAMES, PLAYERS
    from team_pulse.live.roster import ROSTER, fetch_roster
    from team_pulse.live.schedule import fetch_schedule, parse_schedule
    from team_pulse.model_store import load
    from team_pulse.predict import MODEL

    roster = fetch_roster()
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    roster.to_parquet(ROSTER, index=False)
    state = build_state(
        pd.read_parquet(GAMES),
        pd.read_parquet(PLAYERS),
        roster,
        parse_schedule(fetch_schedule(), include_preseason=True),
        load(MODEL).elo_params,
    )
    path = save_state(state)
    size = path.stat().st_size / 1024
    print(f"Stav sezóny {state['season']}: {len(state['elo'])} teamov, {len(state['players'])} hráčov, ")
    print(f"{len(state['schedule'])} zápasov v rozpise, posledný výsledok {state['last_result']}")
    print(f"Uložené: {path} ({size:.0f} kB)")


if __name__ == "__main__":
    main()
