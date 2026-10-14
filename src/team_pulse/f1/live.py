"""F1 naostro mimo appky: model B, tip po kvalifikácii, vyhodnotenie po pretekoch (docs/gate-f1-shadow.md).

Každý beh (GitHub Actions f1.yml, sobota a nedeľa):
  1. update    dojazdené preteky po poslednom započítanom kole → Elo (state/f1_state.json),
  2. lock      najbližšie preteky: ak je známa kvalifikácia a preteky nezačali, tip do
               archive/f1/predictions/<sezóna>-<kolo>.json (do štartu sa smie prepísať),
  3. evaluate  zamknuté tipy po pretekoch: výsledok sa uloží k tipu, súhrn do reports/f1_live.md.
Model sa nemení: váhy, parametre Ela a tabuľka kvalifikácie sú v stave od 14. 10. 2026.

Spustenie:            uv run python -m team_pulse.f1.live
Stav znova z histórie: uv run python -m team_pulse.f1.live --build-state  (z Macu, len raz)
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from team_pulse.f1.fetch import BASE, quali_start, start_utc
from team_pulse.f1.model import REGULATION_CHANGES, Elo, EloParams, elo_ratings, podium

STATE = Path("state/f1_state.json")
ARCHIVE = Path("archive/f1/predictions")
REPORT = Path("reports/f1_live.md")
MODEL = "f1-b"
MEASURED = (2026, 18)  # ostré meranie od Austinu (sezóna, kolo)
THRESHOLD = 0.0005

Getter = Callable[[str], dict]


def http_get(path: str) -> dict:
    time.sleep(0.3)  # limit Jolpica 4/s
    r = requests.get(f"{BASE}/{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# --- stav modelu -----------------------------------------------------------------------------


def build_state(results: pd.DataFrame, sprints: pd.DataFrame) -> dict:
    """Model B z histórie (ladenie len na tréningu, ako v backteste) + Elo po posledných pretekoch."""
    from team_pulse.f1.backtest import backtest

    r = backtest(results, sprints, resets=REGULATION_CHANGES)
    p: EloParams = r["params"]
    elo = Elo(p, {}, {})
    elo_ratings(results, p, elo)
    return {
        "model": MODEL,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "params": {"k_driver": p.k_driver, "k_team": p.k_team, "carry": p.carry, "resets": list(p.resets)},
        "weights": [float(x) for x in r["weights"]],
        "quali_table": [float(x) for x in r["slot_table"]],
        "season": elo.season,
        "last_round": elo.last_round,
        "drivers": dict(sorted(elo.drivers.items())),
        "teams": dict(sorted(elo.teams.items())),
    }


def to_elo(state: dict) -> Elo:
    p = state["params"]
    params = EloParams(p["k_driver"], p["k_team"], p["carry"], tuple(p["resets"]))
    return Elo(params, dict(state["drivers"]), dict(state["teams"]), state["season"], state["last_round"])


def from_elo(state: dict, elo: Elo) -> dict:
    return {
        **state,
        "season": elo.season,
        "last_round": elo.last_round,
        "drivers": dict(sorted(elo.drivers.items())),
        "teams": dict(sorted(elo.teams.items())),
    }


# --- Jolpica: kalendár, kvalifikácia, výsledky -------------------------------------------------


def calendar(get: Getter, season: int) -> list[dict]:
    races = get(f"{season}.json?limit=100")["MRData"]["RaceTable"]["Races"]
    return [
        {
            "season": season,
            "round": int(r["round"]),
            "race": r["raceName"],
            "start_utc": start_utc(r["date"], r.get("time")),
            "quali_utc": quali_start(r),
        }
        for r in races
    ]


def qualifying(get: Getter, season: int, rnd: int) -> list[dict]:
    races = get(f"{season}/{rnd}/qualifying.json?limit=100")["MRData"]["RaceTable"]["Races"]
    return [
        {
            "driver": q["Driver"]["driverId"],
            "code": q["Driver"].get("code") or q["Driver"]["driverId"][:3].upper(),
            "constructor": q["Constructor"]["constructorId"],
            "team": q["Constructor"]["name"],
            "quali": int(q["position"]),
        }
        for q in (races[0]["QualifyingResults"] if races else [])
    ]


def results(get: Getter, season: int, rnd: int) -> pd.DataFrame:
    races = get(f"{season}/{rnd}/results.json?limit=100")["MRData"]["RaceTable"]["Races"]
    rows = [{"season": season, "round": rnd, "driver": x["Driver"]["driverId"],
             "constructor": x["Constructor"]["constructorId"], "position": int(x["position"])}
            for x in (races[0]["Results"] if races else [])]  # fmt: skip
    return pd.DataFrame(rows, columns=["season", "round", "driver", "constructor", "position"])


# --- 1. update -------------------------------------------------------------------------------


def update(state: dict, get: Getter, now: datetime) -> tuple[dict, list[int]]:
    """Započíta dojazdené preteky po state.last_round (po poradí, bez preskočenia kola)."""
    elo = to_elo(state)
    done = []
    for race in calendar(get, elo.season):
        if race["round"] <= elo.last_round or _ts(race["start_utc"]) > now:
            continue
        res = results(get, race["season"], race["round"])
        if res.empty:  # výsledok ešte nie je v Jolpica: ďalšie kolá musia počkať
            break
        elo.enter_season(race["season"])
        elo.apply(res.sort_values("position"))
        done.append(race["round"])
    return from_elo(state, elo), done


# --- 2. lock ---------------------------------------------------------------------------------


def tip(state: dict, quali: list[dict]) -> list[dict]:
    """Šance jazdcov podľa modelu B (+ baseline kvalifikácia na vyhodnotenie), od favorita."""
    elo = to_elo(state)
    table = np.array(state["quali_table"])
    q = pd.DataFrame(quali)
    slot = q["quali"].clip(upper=len(table) - 1).to_numpy()
    rd, rt = elo.before(q["driver"], q["constructor"])
    x = np.column_stack([np.log(table[slot]), (rd - rd.mean()) / 100.0, (rt - rt.mean()) / 100.0])
    s = x @ np.array(state["weights"])
    p = np.exp(s - s.max())
    p /= p.sum()
    b = table[slot] / table[slot].sum()
    out = q.assign(elo_driver=rd.round(1), elo_team=rt.round(1), p_win=p, p_podium=podium(p), p_win_quali=b)
    return out.sort_values("p_win", ascending=False).to_dict("records")


def lock(state: dict, get: Getter, now: datetime, archive: Path = ARCHIVE) -> Path | None:
    """Tip na najbližšie preteky, ak je známa kvalifikácia a preteky ešte nezačali."""
    nxt = next((r for r in calendar(get, state["season"]) if _ts(r["start_utc"]) > now), None)
    if nxt is None:
        print("Sezóna skončila, žiadne ďalšie preteky.")
        return None
    label = f"{nxt['season']}/{nxt['round']} {nxt['race']}"
    quali = qualifying(get, nxt["season"], nxt["round"])
    if not quali:
        print(f"{label}: kvalifikácia ešte nie je v Jolpica, tip zatiaľ nie.")
        return None
    if state["last_round"] != nxt["round"] - 1:
        raise RuntimeError(
            f"{label}: Elo je po kole {state['last_round']}, chýba výsledok kola {nxt['round'] - 1}"
        )
    drivers = tip(state, quali)
    path = archive / f"{nxt['season']}-{nxt['round']:02d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rounded = [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()} for d in drivers]
    data = {**nxt, "model": MODEL, "locked_at": now.isoformat(timespec="seconds"), "drivers": rounded}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fav = drivers[0]
    print(f"{label}: tip {fav['code']} {fav['p_win']:.1%} (kval. {fav['quali']}.) → {path}")
    return path


# --- 3. evaluate -----------------------------------------------------------------------------


def evaluate(get: Getter, now: datetime, archive: Path = ARCHIVE) -> pd.DataFrame:
    """Po pretekoch doplní k tipu výsledok (víťaz, pódium) a vráti jeden riadok na preteky."""
    rows = []
    for path in sorted(archive.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        start = _ts(t["start_utc"])
        if start > now or _ts(t["locked_at"]) >= start:
            continue  # ešte sa nejazdilo / tip zamknutý až po štarte sa neráta
        if "result" not in t:
            res = results(get, t["season"], t["round"])
            if res.empty:
                continue
            top = res.sort_values("position")["driver"].tolist()
            t["result"] = {"winner": top[0], "podium": top[:3]}
            path.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rows.append(score_tip(t))
    return pd.DataFrame(rows)


def score_tip(t: dict) -> dict:
    by = {d["driver"]: d for d in t["drivers"]}
    win, pod = t["result"]["winner"], set(t["result"]["podium"])
    fav = t["drivers"][0]
    # víťaz mimo kvalifikácie (napr. štart z boxov bez času) – šanca 0 by dala nekonečno, preto min.
    pw = by.get(win, {}).get("p_win", 1e-6)
    pq = by.get(win, {}).get("p_win_quali", 1e-6)
    return {
        "season": t["season"], "round": t["round"], "race": t["race"],
        "fav": fav["code"], "fav_p": fav["p_win"],
        "winner": by.get(win, {}).get("code", win), "p_winner": pw, "p_winner_quali": pq,
        "hit": fav["driver"] == win, "measured": (t["season"], t["round"]) >= MEASURED,
        "ll": -math.log(max(pw, 1e-6)), "ll_quali": -math.log(max(pq, 1e-6)),
        "brier": float(np.mean([(d["p_podium"] - (d["driver"] in pod)) ** 2 for d in t["drivers"]])),
    }  # fmt: skip


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float) -> str:
    return f"{x:.4f}".replace(".", ",")


def to_markdown(df: pd.DataFrame) -> str:
    head = (
        "# F1 – ostré tipy mimo appky (model B)\n\n"
        "Tip zamknutý po kvalifikácii, pred štartom; vyhodnotenie po pretekoch. Kritériá: "
        "docs/gate-f1-shadow.md (6 pretekov 25. 10. – 6. 12. 2026). Dáta: Jolpica-F1 (CC BY-NC-SA 4.0).\n\n"
    )
    m = df[df["measured"]] if not df.empty else df
    if m.empty:
        return head + "Zatiaľ žiadne vyhodnotené preteky.\n"
    margin = m["ll_quali"].mean() - m["ll"].mean()
    rows = "\n".join(
        f"| {r.round} | {r.race.replace(' Grand Prix', '')} | {r.fav} {_pct(r.fav_p)} | {r.winner} | "
        f"{_pct(r.p_winner)} | {_pct(r.p_winner_quali)} | {'✅' if r.hit else '❌'} |"
        for r in m.itertuples(index=False)
    )
    return head + (
        f"**Po {len(m)} zo 6 pretekov:** log loss víťaza model {_num(m['ll'].mean())}, kvalifikácia "
        f"{_num(m['ll_quali'].mean())}, rozdiel {_num(margin)} (hranica {_num(THRESHOLD)}, priebežne "
        f"{'nad' if margin >= THRESHOLD else 'pod'} hranicou). "
        f"Favorit vyhral {int(m['hit'].sum())} z {len(m)}, "
        f"Brier pódia {_num(m['brier'].mean())}.\n\n"
        "| Kolo | Veľká cena | Favorit modelu | Víťaz | Šanca víťaza (model) "
        "| Šanca víťaza (kvalifikácia) | |\n"
        f"|---|---|---|---|---|---|---|\n{rows}\n"
    )


def main(get: Getter = http_get, now: datetime | None = None, state_path: Path = STATE,
         archive: Path = ARCHIVE, report: Path = REPORT) -> dict:  # fmt: skip
    now = now or datetime.now(UTC)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state, done = update(state, get, now)
    if done:
        print(f"Elo: započítané kolá {done}, posledné kolo {state['last_round']}")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lock(state, get, now, archive)
    df = evaluate(get, now, archive)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(to_markdown(df), encoding="utf-8")
    return state


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-state", action="store_true", help="stav modelu B z histórie (data/raw, z Macu)")
    if ap.parse_args().build_state:
        from team_pulse.f1.fetch import OUT, SPRINTS

        s = build_state(pd.read_parquet(OUT), pd.read_parquet(SPRINTS))
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Stav modelu B po {s['season']}/{s['last_round']}: {len(s['drivers'])} jazdcov → {STATE}")
    else:
        main()
