"""NFL v appke (beta): zamknuté tipy z archívu + výsledky a Elo z games.csv → app/public/nfl/.

Tipy zamyká team_pulse.nfl.predict (archive/nfl/…), tu sa nič nezamyká ani nemení: len sa poskladá to,
čo appka ukáže. Súbory sú v app/public/nfl (commitujú sa), build appky ich zverejní bez zmeny predict.yml.

  predictions.json  zápasy s tipom, ktoré sa ešte nedohrali (rozpad tipu v Elo bodoch, quarterbacky,
                    Elo trend, bilancia), výsledky posledných 8 dní, tímy podľa Ela, ostré meranie modelov
  model.json        presnosť, kalibrácia a vrstvy na teste 2023 – 2025 (tvar ako NBA model.json)

Spustenie:  uv run python -m team_pulse.nfl.app_data [--commit SHA]
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from team_pulse.backtest import calibration, metrics
from team_pulse.nfl import games as G
from team_pulse.nfl import predict as P
from team_pulse.nfl.backtest import TEST, TRAIN, baseline_probs, fit_baselines, home_won, masks
from team_pulse.nfl.elo import diff, expected, run
from team_pulse.nfl.qb import BACKUP_PENALTY, adjusted_diff, backup_flags

OUT = Path("app/public/nfl")
RESULT_DAYS = 8  # výsledky za posledný týždeň (NFL hrá raz týždenne)
TREND = 10  # Elo trend: pred posledných 9 odohranými zápasmi + pred týmto zápasom


def _round_items(total: float, items: list[list]) -> list[list]:
    """Položky na desatiny so súčtom presne total (rozdiel zaokrúhlenia ide do prvej položky)."""
    out = [[k, label, round(v, 1)] for k, label, v in items]
    out[0][2] = round(out[0][2] + round(total, 1) - round(sum(x[2] for x in out), 1), 1)
    return out


def edge(tip: dict, recomputed: float | None = None) -> dict:
    """Rozpad zamknutej šance v Elo bodoch z pohľadu domácich; súčet = elo_diff tipu → p_home.

    verified: Elo z aktuálneho games.csv znova dá presne zamknutú šancu (recomputed = rozdiel Ela teraz)."""
    total = float(tip["elo_diff"])
    hfa = 0.0 if tip["neutral"] else P.PARAMS.hfa
    base = total / P.PARAMS.playoff_mult if tip["playoff"] else total
    items = [["elo", "Rozdiel v Elo", base - hfa]]
    if hfa:
        items.append(["home", f"{tip['home']}: domáce ihrisko", hfa])
    if tip["playoff"]:
        items.append(["playoff", "Play-off (rozdiel × 1,2)", total - base])
    return {
        "verified": recomputed is not None
        and bool(round(expected(float(recomputed)), 4) == round(float(tip["p_home"]), 4)),
        "total": round(total, 1),
        "items": _round_items(total, items),
    }


def _locked_before(tip: dict | None, kickoff: str) -> dict | None:
    return tip if tip and tip["locked_at"] < kickoff.replace("Z", ":00Z") else None


def build(games: pd.DataFrame, tips: dict, tips_qb: dict, now: datetime, commit: str) -> dict:
    r = run(games, P.PARAMS)
    season = int(r["season"].max())
    played = r[r["played"]]
    # aktuálne Elo a trend každého tímu
    teams, trend = [], {}
    last_season = played[played["season"] == season]
    for team in sorted(set(r.loc[r["season"] == season, "home"]) | set(r.loc[r["season"] == season, "away"])):
        mine = played[(played["home"] == team) | (played["away"] == team)]
        if mine.empty:
            continue
        last = mine.iloc[-1]
        elo = last["elo_home_post"] if last["home"] == team else last["elo_away_post"]
        pts = [
            [str(g.date.date()), round(float(g.elo_home_pre if g.home == team else g.elo_away_pre), 1)]
            for g in mine.tail(TREND - 1).itertuples()
        ]
        trend[team] = pts
        s = last_season[(last_season["home"] == team) | (last_season["away"] == team)]
        w = int(((s["home"] == team) & (s["score_home"] > s["score_away"])).sum()) + int(
            ((s["away"] == team) & (s["score_away"] > s["score_home"])).sum()
        )
        t = int(s["tie"].sum())
        teams.append(
            {
                "team": team,
                "elo": round(float(elo), 1),
                "as_of": str(last["date"].date()),
                "record": [w, len(s) - w - t, t],
            }
        )
    teams.sort(key=lambda x: (-x["elo"], x["team"]))
    rec = {x["team"]: x["record"] for x in teams}

    def side(tip: dict, s: str, qb: dict | None) -> dict:
        out = {"team": tip[s], "elo": tip[f"elo_{s}"], "qb": tip.get(f"{s}_qb"), "reasons": []}
        if qb and qb.get(f"{s}_backup"):
            out["reasons"] = [[f"náhradník QB {qb.get(f'{s}_qb') or ''}".strip(), -BACKUP_PENALTY]]
        return out

    days: dict[str, list[dict]] = {}
    done = set(played["game_id"])
    for gid, tip in sorted(tips.items(), key=lambda kv: (kv[1]["kickoff_utc"], kv[0])):
        if gid in done:
            continue
        qb = tips_qb.get(gid)
        row = r[r["game_id"] == gid]
        date = str(row["date"].iloc[0].date()) if len(row) else tip["kickoff_utc"][:10]
        now_diff = (
            diff(
                row["elo_home_pre"].iloc[0],
                row["elo_away_pre"].iloc[0],
                P.PARAMS,
                tip["neutral"],
                tip["playoff"],
            )
            if len(row)
            else None
        )
        days.setdefault(date, []).append(
            {
                "game_id": gid,
                "date": date,
                "week": tip["week"],
                "tipoff_utc": tip["kickoff_utc"],
                "kind": "playoff" if tip["playoff"] else "regular",
                "neutral": tip["neutral"],
                "p_home": tip["p_home"],
                "p_home_qb": qb["p_home"] if qb else None,
                "locked_at": tip["locked_at"],
                "home": side(tip, "home", qb),
                "away": side(tip, "away", qb),
                "edge": edge(tip, now_diff),
                "trend": {s: trend.get(tip[s], []) + [[date, tip[f"elo_{s}"]]] for s in ("home", "away")},
                "record": {"home": rec.get(tip["home"]), "away": rec.get(tip["away"])},
            }
        )
    since = (now - timedelta(days=RESULT_DAYS)).date().isoformat()
    results = []
    for g in played[played["date"].dt.date.astype(str) >= since].itertuples():
        ko = P.kickoff_utc(g.date, g.gametime)
        ko_s = ko.strftime("%Y-%m-%dT%H:%MZ") if ko is not None else ""
        t, q = _locked_before(tips.get(g.game_id), ko_s), _locked_before(tips_qb.get(g.game_id), ko_s)
        results.append(
            {
                "game_id": g.game_id,
                "date": str(g.date.date()),
                "week": int(g.week),
                "tipoff_utc": ko_s or None,
                "kind": "playoff" if g.playoff else "regular",
                "home": g.home,
                "away": g.away,
                "score_home": int(g.score_home),
                "score_away": int(g.score_away),
                "p_home": t["p_home"] if t else None,
                "p_home_qb": q["p_home"] if q else None,
            }
        )
    live = {}
    for key, model, t in (("elo", P.ELO, tips), ("qb", P.ELO_QB, tips_qb)):
        ev = P.evaluate(t, r, model)
        live[key] = {
            "model": model.name,
            "from": model.g2_from,
            "to": model.g2_to,
            "limit": model.g2_limit,
            "locked": len(t),
            "n": len(ev),
            "hits": int(ev["hit"].sum()) if len(ev) else 0,
            "log_loss": round(float(ev["ll"].mean()), 4) if len(ev) else None,
        }
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "sport": "nfl",
        "beta": True,
        "model": P.MODEL,
        "model_qb": P.ELO_QB.name,
        "games_commit": commit,
        "last_locked": max((t["locked_at"] for t in tips.values()), default=None),
        "days": dict(sorted(days.items())),
        "results": sorted(results, key=lambda x: (x["tipoff_utc"] or "", x["game_id"])),
        "teams": teams,
        "live": live,
    }


def model_info(games: pd.DataFrame) -> dict:
    """Čísla z testovacích sezón (rovnaké ako reports/nfl_backtest.md a reports/nfl_qb.md)."""
    g = (
        games[games["season"] <= TEST[1]]
        .sort_values(["date", "game_id"], kind="stable")
        .reset_index(drop=True)
    )
    r = run(g, P.PARAMS)
    train, test = masks(r)
    won = home_won(r)
    f = backup_flags(r)
    d = np.array(
        [
            diff(h, a, P.PARAMS, n, p)
            for h, a, n, p in zip(r.elo_home_pre, r.elo_away_pre, r.neutral, r.playoff, strict=True)
        ]
    )
    p_qb = pd.Series(
        [
            expected(adjusted_diff(x, bh, ba))
            for x, bh, ba in zip(d, f["home_backup"], f["away_backup"], strict=True)
        ]
    )
    base = baseline_probs(r, fit_baselines(r, train))
    versions = [
        ("Baseline: vždy domáci", base["Baseline: vždy domáci"]),
        ("Baseline: lepšia bilancia", base["Baseline: lepšia bilancia"]),
        ("Elo (nfl-elo-v1)", r["prob_home"]),
        ("Elo + quarterback (nfl-elo-qb-v1)", p_qb),
    ]
    m = metrics(r.loc[test, "prob_home"], won[test])
    cal = calibration(r.loc[test, "prob_home"], won[test])
    return {
        "version": P.MODEL,
        "created": "2026-10-28",
        "train_seasons": [TRAIN[0], TRAIN[1]],
        "train_label": f"{TRAIN[0]} – {TRAIN[1]}",
        "n_games": int(train.sum()),
        "test_metrics": {
            "accuracy": round(m["accuracy"], 4),
            "log_loss": round(m["log_loss"], 4),
            "brier": round(m["brier"], 4),
            "test_seasons": f"{TEST[0]} – {TEST[1]}",
        },
        "calibration": [
            {
                "band": str(c.band),
                "n": int(c.zapasy),
                "pred": round(float(c.predpoved), 4),
                "actual": round(float(c.skutocnost), 4),
            }
            for c in cal.itertuples()
        ],
        "versions": [
            {"model": name, **{k: round(v, 4) for k, v in metrics(p[test], won[test]).items() if k != "n"}}
            for name, p in versions
        ],
        "elo_weights": {"home": P.PARAMS.hfa, "qb_backup": -BACKUP_PENALTY},
    }


def main(commit: str | None = None, out: Path = OUT, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    session = requests.Session()
    commit = commit or P.latest_commit(session)
    games = G.load(G.download(commit, session))
    data = build(games, P.locked(P.ELO.archive), P.locked(P.ELO_QB.archive), now, commit)
    out.mkdir(parents=True, exist_ok=True)
    (out / "predictions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out / "model.json").write_text(
        json.dumps(model_info(games), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    n = sum(len(x) for x in data["days"].values())
    print(
        f"NFL pre appku: {n} zápasov s tipom, {len(data['results'])} výsledkov, "
        f"{len(data['teams'])} tímov → {out}"
    )
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default=None)
    main(ap.parse_args().commit)
