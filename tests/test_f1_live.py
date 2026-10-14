"""F1 naostro (model B): update Ela, zamknutie po kvalifikácii a pred štartom, vyhodnotenie (bez siete).

Odpovede Jolpica sú skutočné (Singapur 2026, kolo 17): tests/fixtures/f1_*_2026_17.json.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from team_pulse.f1 import live
from team_pulse.f1.model import Elo, EloParams, elo_ratings

FIX = Path(__file__).parent / "fixtures"
QUALI_DONE = datetime(2026, 10, 10, 20, 0, tzinfo=UTC)  # po kvalifikácii, pred štartom (11. 10. 12:00)
AFTER_RACE = datetime(2026, 10, 12, 8, 0, tzinfo=UTC)


def real(name: str) -> dict:
    return json.loads((FIX / f"f1_{name}_2026_17.json").read_text(encoding="utf-8"))


def getter(quali: bool = True, results: bool = True):
    """Kalendár s jediným kolom 17; kvalifikácia/výsledky podľa toho, či už sú v Jolpica."""

    def empty(kind: str) -> dict:
        d = real(kind)
        d["MRData"]["RaceTable"]["Races"] = []
        return d

    def get(path: str) -> dict:
        if path.startswith("2026.json"):
            return real("race")
        if "/qualifying" in path:
            return real("qualifying") if quali else empty("qualifying")
        if "/results" in path:
            return real("results") if results else empty("results")
        raise AssertionError(path)

    return get


def state(last_round: int = 16) -> dict:
    """Malý stav: jazdci zo Singapuru, Verstappen a Red Bull silnejší než priemer."""
    q = real("qualifying")["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"]
    drivers = {x["Driver"]["driverId"]: 1500.0 for x in q}
    teams = {x["Constructor"]["constructorId"]: 1500.0 for x in q}
    drivers["max_verstappen"], teams["red_bull"] = 1600.0, 1550.0
    table = [0.0] + [0.55 * 0.6**i for i in range(26)]
    params = {"k_driver": 48.0, "k_team": 8.0, "carry": 0.5, "resets": [2017, 2022, 2026]}
    return {"model": "f1-b", "params": params,
            "weights": [0.8, 1.45, -0.9], "quali_table": table, "season": 2026, "last_round": last_round,
            "drivers": drivers, "teams": teams}  # fmt: skip


def test_lock_after_quali_writes_tip_with_consistent_probabilities(tmp_path):
    path = live.lock(state(), getter(), QUALI_DONE, tmp_path)
    t = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "2026-17.json" and t["round"] == 17 and t["model"] == "f1-b"
    assert t["locked_at"] == "2026-10-10T20:00:00+00:00"
    ds = t["drivers"]
    assert len(ds) == 22 and ds[0]["code"] == "VER"  # pole + najvyššie Elo
    assert sum(d["p_win"] for d in ds) == pytest.approx(1, abs=1e-5)
    assert sum(d["p_win_quali"] for d in ds) == pytest.approx(1, abs=1e-5)
    assert sum(d["p_podium"] for d in ds) == pytest.approx(3, abs=1e-4)
    assert [d["p_win"] for d in ds] == sorted((d["p_win"] for d in ds), reverse=True)


def test_no_tip_before_quali_and_none_after_start(tmp_path):
    assert live.lock(state(), getter(quali=False), QUALI_DONE, tmp_path) is None
    assert (
        live.lock(state(), getter(), datetime(2026, 10, 11, 12, 1, tzinfo=UTC), tmp_path) is None
    )  # sezóna ďalej nemá kolo
    assert not list(tmp_path.glob("*.json"))


def test_lock_refuses_when_previous_race_not_counted(tmp_path):
    with pytest.raises(RuntimeError, match="chýba výsledok kola 16"):
        live.lock(state(last_round=15), getter(), QUALI_DONE, tmp_path)


def test_update_applies_finished_race_once():
    s, done = live.update(state(), getter(), AFTER_RACE)
    assert done == [17] and s["last_round"] == 17
    assert s["drivers"]["max_verstappen"] > 1600.0  # vyhral
    s2, done2 = live.update(s, getter(), AFTER_RACE)
    assert done2 == [] and s2["drivers"] == s["drivers"]


def test_update_waits_for_results():
    s, done = live.update(state(), getter(results=False), AFTER_RACE)
    assert done == [] and s["last_round"] == 16


def test_incremental_update_equals_batch():
    """Elo z ostrej prevádzky (kolo po kole) = Elo z backtestu (všetko naraz)."""
    rng = np.random.default_rng(3)
    drivers = [f"d{i}" for i in range(8)]
    rows = []
    for r in range(1, 5):
        for i, (d, pos) in enumerate(zip(drivers, rng.permutation(8) + 1, strict=True)):
            rows.append(
                {"season": 2026, "round": r, "driver": d, "constructor": f"t{i // 2}", "position": pos}
            )
    df = pd.DataFrame(rows)
    p = EloParams(48, 8, 0.5, (2026,))
    batch = Elo(p, {}, {})
    elo_ratings(df, p, batch)
    step = Elo(p, {}, {})
    elo_ratings(df[df["round"] <= 2], p, step)
    for r in (3, 4):
        step.enter_season(2026)
        step.apply(df[df["round"] == r].sort_values("position"))
    assert step.drivers == pytest.approx(batch.drivers) and step.teams == pytest.approx(batch.teams)


def test_evaluate_stores_result_and_scores_only_tips_locked_before_start(tmp_path):
    live.lock(state(), getter(), QUALI_DONE, tmp_path)
    df = live.evaluate(getter(), AFTER_RACE, tmp_path)
    t = json.loads((tmp_path / "2026-17.json").read_text(encoding="utf-8"))
    assert t["result"]["winner"] == "max_verstappen" and len(t["result"]["podium"]) == 3
    r = df.iloc[0]
    assert r["winner"] == "VER" and bool(r["hit"]) and r["ll"] == pytest.approx(-np.log(r["p_winner"]))
    assert not bool(r["measured"])  # Singapur je pred ostrým meraním (od kola 18)
    # tip „zamknutý“ až po štarte sa neráta
    t["locked_at"] = "2026-10-11T12:05:00+00:00"
    (tmp_path / "2026-17.json").write_text(json.dumps(t), encoding="utf-8")
    assert live.evaluate(getter(), AFTER_RACE, tmp_path).empty


def test_report_counts_only_measured_races():
    base = {"race": "X Grand Prix", "fav": "VER", "fav_p": 0.5, "winner": "VER", "p_winner": 0.5,
            "p_winner_quali": 0.4, "hit": True, "ll": 0.69, "ll_quali": 0.92, "brier": 0.05}  # fmt: skip
    df = pd.DataFrame([{**base, "season": 2026, "round": 17, "measured": False},
                       {**base, "season": 2026, "round": 18, "measured": True}])  # fmt: skip
    md = live.to_markdown(df)
    assert "Po 1 zo 6 pretekov" in md and "| 18 |" in md and "| 17 |" not in md
    assert "Zatiaľ žiadne" in live.to_markdown(df.iloc[:0])
