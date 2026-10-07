"""Archív predpovedí a vyhodnotenie ostrej prevádzky (brána G2).

Cloud (predict.yml, večer a v noci, predict --archive):
  lock_games   zápasy, ktoré začínajú do 24 hodín, uloží do archive/predictions/<dátum>.json.
               Kým zápas nezačal, záznam prepíše novšia predpoveď (len ak sa zmenila).
               Po začiatku zápasu sa záznam už nikdy nemení, takže v archíve ostane
               posledná predpoveď pred zápasom a nič z priebehu zápasu.
               Okno je 24 h, lebo GitHub plánované behy často vynechá a zápas nesmie ostať bez predpovede.
  update_live_results  dohrané zápasy z ESPN (skóre + štatistiky hráčov) → archive/boxscores/<dátum>.json
Mac (daily, ráno):
  fill_results k uloženým zápasom doplní výsledok z histórie → archive/results/<dátum>.json
  update       reports/live.md: presnosť, log loss, Brier, kalibrácia, porovnanie s backtestom

Zápasy prípravy sa ukladajú tiež (skúška archívu pred sezónou), ale v reporte sú zvlášť a do G2 sa nerátajú.

<dátum> je dátum zápasu v USA (ET), rovnako ako v rozpise a v appke.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from team_pulse.backtest import calibration, metrics

PRED_DIR = Path("archive/predictions")
RESULT_DIR = Path("archive/results")
LIVE_REPORT = Path("reports/live.md")
LOCK_BEFORE = pd.Timedelta(hours=24)
BOX_DIR = Path("archive/boxscores")
LIVE_DAYS = 3  # koľko posledných dní (ET) kontrolovať na ESPN
PRESEASON = "preseason"
VOLATILE = {"locked_at", "injuries_timestamp"}  # zmena len v týchto poliach nie je nová predpoveď
SIDE_KEYS = [
    "team",
    "elo",
    "elo_today",
    "pulse",
    "tier",
    "normal_tier",
    "dropped",
    "confidence",
    "layers",
    "reasons",
]


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _tipoff(game: dict) -> pd.Timestamp | None:
    tip = pd.to_datetime(game.get("tipoff_utc") or None, utc=True, errors="coerce")
    return None if pd.isna(tip) else tip


def record(game: dict, meta: dict, now: pd.Timestamp) -> dict:
    """Záznam do archívu: šanca a stav oboch teamov, bez scenárov „čo keby“."""
    return {
        "game_id": game["game_id"],
        "kind": game.get("kind", "regular"),
        "tipoff_utc": game["tipoff_utc"],
        "locked_at": now.isoformat(timespec="seconds"),
        "model": meta.get("model"),
        "injuries_timestamp": meta.get("injuries_timestamp"),
        "neutral": game["neutral"],
        "p_home": game["p_home"],
        "margin_home": game["margin_home"],
        "home": {k: game["home"][k] for k in SIDE_KEYS if k in game["home"]},
        "away": {k: game["away"][k] for k in SIDE_KEYS if k in game["away"]},
    }


def _same(a: dict, b: dict) -> bool:
    strip = lambda d: {k: v for k, v in d.items() if k not in VOLATILE}  # noqa: E731
    return strip(a) == strip(b)


def lock_games(
    by_date: dict[str, list[dict]], meta: dict, now: pd.Timestamp, pred_dir: Path = PRED_DIR
) -> list[str]:
    """Uloží predpovede zápasov, ktoré začínajú do LOCK_BEFORE. Vráti zápasy, ktoré pribudli alebo sa zmenili.

    Zápas, ktorý už začal (now >= tipoff), sa nikdy neuloží ani neprepíše.
    """
    now = pd.Timestamp(now)
    now = now.tz_convert("UTC") if now.tzinfo else now.tz_localize("UTC")
    changed = []
    for day, games in by_date.items():
        path = pred_dir / f"{day}.json"
        data = _read(path) or {"date": day, "games": {}}
        dirty = False
        for g in games:
            tip = _tipoff(g)
            if tip is None or not (tip - LOCK_BEFORE <= now < tip):
                continue
            new = record(g, meta, now)
            old = data["games"].get(g["game_id"])
            if old is not None and _same(old, new):
                continue
            data["games"][g["game_id"]] = new
            changed.append(f"{g['away']['team']} @ {g['home']['team']}")
            dirty = True
        if dirty:
            data["games"] = dict(sorted(data["games"].items(), key=lambda kv: (kv[1]["tipoff_utc"], kv[0])))
            _write(path, data)
    return changed


def fill_results(games: pd.DataFrame, pred_dir: Path = PRED_DIR, result_dir: Path = RESULT_DIR) -> int:
    """K uloženým predpovediam doplní výsledky z histórie (podľa game_id). Vráti počet nových výsledkov."""
    played = games[(games["pts_home"] > 0) | (games["pts_away"] > 0)]
    score = {str(r.game_id): (int(r.pts_home), int(r.pts_away)) for r in played.itertuples()}
    added = 0
    for path in sorted(pred_dir.glob("*.json")):
        preds = _read(path)["games"]
        out = result_dir / path.name
        data = _read(out) or {"date": path.stem, "games": {}}
        before = dict(data["games"])
        for gid in preds:
            if gid in score:
                data["games"][gid] = {"pts_home": score[gid][0], "pts_away": score[gid][1]}
        if data["games"] != before:
            added += len(set(data["games"]) - set(before))
            data["games"] = dict(sorted(data["games"].items()))
            _write(out, data)
    return added


def load_archive(pred_dir: Path = PRED_DIR, result_dir: Path = RESULT_DIR) -> pd.DataFrame:
    """Jeden riadok na uložený zápas; home_won je prázdne, kým nie je výsledok."""
    rows = []
    for path in sorted(pred_dir.glob("*.json")):
        results = _read(result_dir / path.name).get("games", {})
        for gid, p in _read(path)["games"].items():
            res = results.get(gid)
            conf = {p["home"].get("confidence"), p["away"].get("confidence")}
            level = "nízka" if "nízka" in conf else "stredná" if "stredná" in conf else "vysoká"
            rows.append(
                {
                    "game_id": gid,
                    "date": path.stem,
                    "kind": p.get("kind", "regular"),
                    "home": p["home"]["team"],
                    "away": p["away"]["team"],
                    "p_home": float(p["p_home"]),
                    "confidence": level,
                    "pts_home": res["pts_home"] if res else None,
                    "pts_away": res["pts_away"] if res else None,
                }
            )
    cols = ["game_id", "date", "kind", "home", "away", "p_home", "confidence", "pts_home", "pts_away"]
    df = pd.DataFrame(rows, columns=cols)
    df["home_won"] = pd.Series(
        [pd.NA if pd.isna(h) else h > a for h, a in zip(df["pts_home"], df["pts_away"], strict=True)],
        dtype="boolean",
    )
    return df


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float) -> str:
    return f"{x:.4f}".replace(".", ",")


def _hits(done: pd.DataFrame) -> pd.Series:
    return (done["p_home"] > 0.5) == done["home_won"].astype(bool)


def _last_games(done: pd.DataFrame, n: int = 20) -> list[str]:
    lines = ["| Dátum | Zápas | Šanca domácich | Skóre | Tip |", "|:--|:--|--:|:--|:--|"]
    for r, ok in list(zip(done.itertuples(), _hits(done), strict=True))[::-1][:n]:
        lines.append(
            f"| {r.date} | {r.away} @ {r.home} | {_pct(r.p_home)} | {int(r.pts_away)} : {int(r.pts_home)} "
            f"| {'✓' if ok else '✗'} |"
        )
    return lines


def _preseason(pre: pd.DataFrame) -> list[str]:
    """Príprava: len skúška archívu a orientačné čísla, do brány G2 sa neráta."""
    done = pre[pre["home_won"].notna()]
    lines = [
        "",
        "## Príprava (skúška archívu, mimo G2)",
        "",
        f"Uložené predpovede {len(pre)} · s výsledkom {len(done)}"
        + (f" · presnosť {_pct(float(_hits(done).mean()))}" if len(done) else ""),
        "",
        "Hviezdy v príprave hrajú menej a model je naučený na základnú časť, takže tieto čísla nič nehovoria "
        "o kvalite modelu. Overujú len, že sa predpovede ukladajú a výsledky dopĺňajú.",
    ]
    if len(done):
        lines += ["", *_last_games(done, 10)]
    return lines


def report(df: pd.DataFrame, backtest: dict, missing: list[str] | None = None) -> str:
    """Markdown report ostrej prevádzky. Nemá v sebe aktuálny čas, takže bez nových dát sa nemení."""
    is_pre = df["kind"] == PRESEASON
    pre, df = df[is_pre], df[~is_pre]
    tail = _preseason(pre) if len(pre) else []
    done = df[df["home_won"].notna()]
    lines = ["# Ostrá prevádzka: vyhodnotenie predpovedí", ""]
    if df.empty:
        lines.append("Zo základnej časti zatiaľ nie je uložená žiadna predpoveď. Sezóna začína 20. 10.")
        return "\n".join([*lines, *tail, ""])
    lines += [
        f"Základná časť: {df['date'].min()} – {df['date'].max()} · uložené predpovede {len(df)} · "
        f"s výsledkom {len(done)} · čaká na výsledok {len(df) - len(done)}",
        "",
    ]
    if missing is not None:
        lines += [
            f"Odohrané zápasy bez uloženej predpovede: **{len(missing)}**"
            + (f" ({', '.join(missing[:10])}{' …' if len(missing) > 10 else ''})" if missing else ""),
            "",
        ]
    if done.empty:
        return "\n".join([*lines, "Zatiaľ žiadny zápas s výsledkom.", *tail, ""])

    m = metrics(done["p_home"], done["home_won"].astype(bool))
    n = len(done)
    ci = 1.96 * math.sqrt(m["accuracy"] * (1 - m["accuracy"]) / n)
    lines += [
        "| | Ostrá prevádzka | Backtest v1 |",
        "|:--|--:|--:|",
        f"| Zápasy | {n} | sezóny {backtest.get('test_seasons', '')} |",
        f"| Presnosť | {_pct(m['accuracy'])} (± {_pct(ci).removesuffix(' %')} p. b.) "
        f"| {_pct(backtest['accuracy'])} |",
        f"| Log loss | {_num(m['log_loss'])} | {_num(backtest['log_loss'])} |",
        f"| Brier | {_num(m['brier'])} | {_num(backtest['brier'])} |",
        "",
        "Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., "
        "férové porovnanie s backtestom až okolo 500 zápasov.",
        "",
        "## Kalibrácia",
        "",
        "Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?",
        "",
        "| Pásmo | Zápasy | Predpoveď | Skutočnosť |",
        "|:--|--:|--:|--:|",
    ]
    cal = calibration(done["p_home"], done["home_won"].astype(bool))
    for r in cal.itertuples():
        lo, hi = round(r.band.left * 100), round(r.band.right * 100)
        lines.append(f"| {max(lo, 50)} – {hi} % | {r.zapasy} | {_pct(r.predpoved)} | {_pct(r.skutocnost)} |")

    lines += ["", "## Podľa istoty", "", "| Istota | Zápasy | Presnosť |", "|:--|--:|--:|"]
    hit = _hits(done)
    for level in ("vysoká", "stredná", "nízka"):
        sel = done["confidence"] == level
        if sel.any():
            lines.append(f"| {level} | {int(sel.sum())} | {_pct(float(hit[sel].mean()))} |")

    lines += ["", "## Posledné zápasy", "", *_last_games(done)]
    return "\n".join([*lines, *tail, ""])


def missing_games(games: pd.DataFrame, archived: pd.DataFrame) -> list[str]:
    """Odohrané zápasy (základná časť, playoff) od začiatku archívu, ku ktorým sa neuložila predpoveď."""
    archived = archived[archived["kind"] != PRESEASON]
    if archived.empty:
        return []
    start = pd.Timestamp(archived["date"].min())
    played = games[
        (pd.to_datetime(games["date"]) >= start) & ((games["pts_home"] > 0) | (games["pts_away"] > 0))
    ]
    done = set(archived["game_id"])
    miss = played[~played["game_id"].astype(str).isin(done)].sort_values(["date", "game_id"])
    return [f"{pd.Timestamp(r.date).date()} {r.away} @ {r.home}" for r in miss.itertuples()]


def update(
    games: pd.DataFrame,
    backtest: dict,
    out: Path = LIVE_REPORT,
    pred_dir: Path = PRED_DIR,
    result_dir: Path = RESULT_DIR,
    preseason: pd.DataFrame | None = None,
) -> int:
    """Denný krok na Macu: výsledky do archívu a nový report. Vráti počet nových výsledkov.

    games      história (základná časť, playoff) z data/raw/games.parquet
    preseason  dohrané zápasy prípravy z rozpisu (v histórii nie sú, Elo ich nepoužíva)
    """
    results = (
        games if preseason is None or preseason.empty else pd.concat([games, preseason], ignore_index=True)
    )
    added = fill_results(results, pred_dir, result_dir)
    archived = load_archive(pred_dir, result_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report(archived, backtest, missing_games(games, archived)), encoding="utf-8")
    return added


def update_live_results(
    schedule: pd.DataFrame,
    today: pd.Timestamp,
    fetch_scoreboard,
    fetch_summary,
    box_dir: Path = BOX_DIR,
    days: int = LIVE_DAYS,
) -> list[str]:
    """Cloud: dohrané zápasy posledných dní z ESPN → archive/boxscores/<dátum>.json.

    Uloží skóre a štatistiky hráčov. Box score každého zápasu sa stiahne len raz
    (znova len keď ešte chýbal alebo sa zmenilo skóre). Vráti zápasy, ktoré pribudli.
    """
    from team_pulse.live.boxscore import parse_boxscore
    from team_pulse.live.scoreboard import parse_scoreboard

    ours = {}
    for r in schedule.itertuples():
        ours[(str(pd.Timestamp(r.date).date()), r.home, r.away)] = (
            str(r.game_id),
            getattr(r, "kind", "regular"),
        )
    added = []
    for back in range(days - 1, -1, -1):
        day = pd.Timestamp(today).normalize() - pd.Timedelta(days=back)
        iso = str(day.date())
        path = box_dir / f"{iso}.json"
        data = _read(path) or {"date": iso, "games": {}}
        dirty = False
        for ev in fetch_scoreboard(day.strftime("%Y%m%d")).get("events", []):
            try:
                r = parse_scoreboard({"events": [ev]}).iloc[0]
            except KeyError:
                continue  # príprava proti klubu mimo NBA
            if not r.completed:
                continue
            espn_kind = "preseason" if ev.get("season", {}).get("slug") == "preseason" else "regular"
            gid, kind = ours.get((iso, r.home, r.away), (f"espn-{r.espn_id}", espn_kind))
            score = (int(r.pts_home), int(r.pts_away))
            old = data["games"].get(gid)
            if old and old["box"] and (old["pts_home"], old["pts_away"]) == score:
                continue
            try:
                box = parse_boxscore(fetch_summary(str(r.espn_id)))
            except Exception as e:  # skúsi sa znova pri ďalšom behu
                print(f"Box score {r.away} @ {r.home}: {e.__class__.__name__}: {e}")
                box = {}
            data["games"][gid] = {
                "game_id": gid,
                "espn_id": str(r.espn_id),
                "date": iso,
                "kind": kind,
                "home": r.home,
                "away": r.away,
                "pts_home": score[0],
                "pts_away": score[1],
                "box": box,
            }
            added.append(f"{r.away} @ {r.home}")
            dirty = True
        if dirty:
            data["games"] = dict(sorted(data["games"].items()))
            _write(path, data)
    return added


def live_results(box_dir: Path = BOX_DIR, files: int = 5) -> list[dict]:
    """Výsledky z ESPN uložené v archíve (posledné dni)."""
    out = []
    for path in sorted(box_dir.glob("*.json"))[-files:]:
        out.extend(_read(path)["games"].values())
    return out
