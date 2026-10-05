"""Denná aktualizácia z Macu: výsledky noci → história → stav → GitHub.

  1. stiahne výsledky a box score aktuálnej sezóny (nba_api, funguje len z Macu)
  2. doplní ich do data/raw/games.parquet a players.parquet (bez duplicít)
  3. k predpovediam v archíve doplní výsledky a prepíše reports/live.md
  4. stiahne súpisky a rozpis, zostaví state/state.json
  5. čo sa zmenilo (stav, výsledky, report), commitne a pošle na GitHub → cloud prepočíta predpovede

Pred začiatkom aj pred odoslaním si stiahne novinky z GitHubu (archív predpovedí commituje cloud).

Spustenie:  uv run python -m team_pulse.daily [--no-push]
Automaticky každé ráno o 10:00: bash scripts/install_daily.sh
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd

GAME_KEYS = ["game_id"]
PLAYER_KEYS = ["game_id", "player_id"]


def merge_new(old: pd.DataFrame, new: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, int]:
    """Doplní nové riadky; pri zhode kľúča vyhráva novší (opravené skóre, dohraný zápas)."""
    if new.empty:
        return old, 0
    before = set(map(tuple, old[keys].astype(str).to_numpy())) if not old.empty else set()
    merged = pd.concat([old, new], ignore_index=True).drop_duplicates(keys, keep="last")
    merged = merged.sort_values(["date", *keys], kind="stable").reset_index(drop=True)
    added = sum(1 for k in map(tuple, new[keys].astype(str).to_numpy()) if k not in before)
    return merged, added


def fetch_current_season(season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Zápasy a box score aktuálnej sezóny (základná časť + playoff)."""
    from team_pulse.data import fetch_games, fetch_players

    abbr = fetch_games.current_abbr()
    games, box = [], []
    for stype, playoff in fetch_games.SEASON_TYPES.items():
        raw = fetch_games.fetch_season(season, stype)
        if not raw.empty:
            games.append(fetch_games.normalize(raw, season, playoff, abbr))
        raw_p = fetch_players.fetch_season(season, stype)
        if not raw_p.empty:
            box.append(fetch_players.normalize(raw_p, season, playoff, abbr))
    g = fetch_games.mark_neutral(pd.concat(games, ignore_index=True)) if games else pd.DataFrame()
    p = pd.concat(box, ignore_index=True) if box else pd.DataFrame()
    return g, p


def same_state(path: Path, state: dict) -> bool:
    """Je nový stav rovnaký ako uložený? Čas vytvorenia (generated_at) sa neporovnáva."""
    if not path.exists():
        return False
    strip = lambda d: {k: v for k, v in json.loads(json.dumps(d)).items() if k != "generated_at"}  # noqa: E731
    return strip(json.loads(path.read_text(encoding="utf-8"))) == strip(state)


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def git_pull(cwd: Path | None = None) -> None:
    """Stiahne novinky (napr. archív z cloudu). Neuložené lokálne zmeny odloží a vráti späť."""
    _git("pull", "--rebase", "--autostash", cwd=cwd)


def git_commit_if_changed(
    paths: str | Path | list[str | Path], message: str, push: bool = True, cwd: Path | None = None
) -> bool:
    """Commitne súbory len ak sa zmenili. Vráti True, ak vznikol commit."""
    items = [paths] if isinstance(paths, str | Path) else paths
    names = [str(p) for p in items if (Path(cwd or ".") / p).exists()]
    if not names:
        return False
    _git("add", "--", *names, cwd=cwd)
    if subprocess.run(["git", "diff", "--cached", "--quiet", "--", *names], cwd=cwd).returncode == 0:
        return False
    _git("commit", "-m", message, "--", *names, cwd=cwd)
    if push:
        git_pull(cwd)
        _git("push", cwd=cwd)
    return True


def main(push: bool) -> None:
    from team_pulse.archive import LIVE_REPORT, RESULT_DIR, update
    from team_pulse.learned import GAMES, PLAYERS
    from team_pulse.live.roster import ROSTER, fetch_roster
    from team_pulse.live.schedule import fetch_schedule, parse_schedule
    from team_pulse.model_store import load
    from team_pulse.predict import MODEL
    from team_pulse.state import STATE, build_state, save_state

    if push:
        git_pull()
    schedule = parse_schedule(fetch_schedule())
    season = int(schedule["season"].max())

    new_games, new_box = fetch_current_season(season)
    games, n_games = merge_new(pd.read_parquet(GAMES), new_games, GAME_KEYS)
    players, n_rows = merge_new(pd.read_parquet(PLAYERS), new_box, PLAYER_KEYS)
    games.to_parquet(GAMES, index=False)
    players.to_parquet(PLAYERS, index=False)
    print(f"Sezóna {season}: +{n_games} zápasov, +{n_rows} riadkov box score (spolu {len(games)} zápasov)")
    n_results = update(games, load(MODEL).test_metrics)
    print(f"Archív: +{n_results} výsledkov → {LIVE_REPORT}")

    roster = fetch_roster()
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    roster.to_parquet(ROSTER, index=False)
    state = build_state(games, players, roster, schedule, load(MODEL).elo_params)
    if same_state(STATE, state):
        print("Stav sa nezmenil")
    else:
        save_state(state)
        print(f"Stav: {len(state['elo'])} teamov, posledný výsledok {state['last_result']} → {STATE}")

    message = f"Stav {date.today()}: posledný výsledok {state['last_result']}"
    if n_results:
        message += f", archív +{n_results} výsledkov"
    if not push:
        print("--no-push: zmeny sú len lokálne, necommitovali sa")
    elif git_commit_if_changed([STATE, RESULT_DIR, LIVE_REPORT], message):
        print("Commitnuté a poslané na GitHub → cloud prepočíta predpovede")
    else:
        print("Nič sa nezmenilo, nič sa necommitovalo")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true", help="necommitovať a neposielať na GitHub")
    main(push=not ap.parse_args().no_push)
