"""F1: sťahovač (aj contract test na skutočnej odpovedi Jolpica), Elo, logit, pódium, únik dát (bez siete)."""

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from team_pulse.f1 import backtest as bt
from team_pulse.f1 import fetch as f
from team_pulse.f1 import model as m

FIX = Path(__file__).parent / "fixtures"


def real(name: str) -> dict:
    return json.loads((FIX / f"f1_{name}_2026_17.json").read_text(encoding="utf-8"))


def fixture_getter(path: str) -> dict:
    """Skutočné odpovede Jolpica pre Singapur 2026 (kolo 17) namiesto celej sezóny."""
    kind = path.split("?")[0].removeprefix("2026").strip("/").removesuffix(".json") or "race"
    return real({"race": "race", "results": "results", "qualifying": "qualifying", "sprint": "sprint"}[kind])


# --- sťahovač -------------------------------------------------------------------------------


def test_start_utc():
    assert f.start_utc("2026-10-25", "20:00:00Z") == "2026-10-25T20:00:00Z"
    assert f.start_utc("2014-03-16", None) == "2014-03-16T12:00:00Z"


def test_contract_real_jolpica_response():
    cal, res, spr = f.season_frames(fixture_getter, 2026)
    assert cal.loc[0, ["round", "race", "start_utc"]].tolist() == [
        17,
        "Singapore Grand Prix",
        "2026-10-11T12:00:00Z",
    ]
    assert len(res) == 22 and res["position"].tolist() == list(range(1, 23))
    win = res.iloc[0]
    assert (win["code"], win["constructor"], win["quali"], win["grid"]) == ("VER", "red_bull", 1, 1)
    assert res["quali"].notna().all() and set(res["race"]) == {"Singapore Grand Prix"}
    assert len(spr) == 22 and spr["points"].sum() > 0


def test_pages_are_merged_even_when_a_race_is_split(monkeypatch):
    """total = počet riadkov výsledkov; stránka môže preteky rozdeliť (2 + 1 riadok)."""
    pages = {
        0: {"MRData": {"total": "3", "RaceTable": {"Races": [
            {"round": "1", "Results": [{"a": 1}, {"a": 2}]}]}}},
        2: {"MRData": {"total": "3", "RaceTable": {"Races": [{"round": "1", "Results": [{"a": 3}]}]}}},
    }  # fmt: skip
    monkeypatch.setattr(f, "PAGE", 2)
    got = f.fetch_all(lambda p: pages[int(p.split("offset=")[1])], 2026, "results")
    assert len(got) == 1 and [x["a"] for x in got[0]["Results"]] == [1, 2, 3]


def test_check_complete_reports_missing_and_small_fields():
    cal = pd.DataFrame({"season": [2025] * 3, "round": [1, 2, 3], "race": ["A", "B", "C"],
                        "start_utc": ["2025-03-01T12:00:00Z", "2025-03-08T12:00:00Z",
                                      "2099-01-01T12:00:00Z"]})  # fmt: skip
    res = pd.DataFrame({"season": [2025] * 10, "round": [2] * 10, "quali": [1.0] * 10})
    problems = f.check_complete(cal, res, datetime(2025, 6, 1, tzinfo=UTC))
    assert problems == [
        "2025/1 A: chýbajú výsledky",
        "2025/2 B: len 10 jazdcov",
    ]  # budúce preteky sa nekontrolujú


# --- model ----------------------------------------------------------------------------------


def race(season, rnd, order, teams=None, quali=None):
    n = len(order)
    return pd.DataFrame({
        "season": season, "round": rnd, "driver": order, "code": [d[:3].upper() for d in order],
        "constructor": teams or [f"t{i // 2}" for i in range(n)], "quali": quali or list(range(1, n + 1)),
        "position": list(range(1, n + 1)), "points": [25.0, 18.0, 15.0] + [0.0] * (n - 3), "race": f"R{rnd}",
    })  # fmt: skip


def season_of(season, rounds, order):
    return pd.concat([race(season, r, order) for r in range(1, rounds + 1)], ignore_index=True)


def test_pairwise_is_zero_sum_and_rewards_winner():
    d = m._pairwise(np.full(4, 1500.0), np.array([1, 2, 3, 4]))
    assert d.sum() == pytest.approx(0) and d[0] > 0 > d[3]


def test_elo_uses_only_earlier_races():
    """Únik dát: rating v pretekoch k sa nezmení, keď zmením výsledok pretekov k aj neskorších."""
    drivers = ["a", "b", "c", "d", "e", "f"]
    base = season_of(2025, 6, drivers)
    changed = base.copy()
    late = changed["round"] >= 4
    changed.loc[late, "position"] = (
        changed.loc[late].groupby("round")["position"].transform(lambda s: s[::-1].to_numpy())
    )
    p = m.EloParams(32, 32, 0.7)
    a, b = m.elo_ratings(base, p), m.elo_ratings(changed, p)
    key = ["season", "round", "driver"]
    a, b = a.set_index(key).sort_index(), b.set_index(key).sort_index()
    upto4 = a.index.get_level_values("round") <= 4
    assert np.allclose(a.loc[upto4, ["elo_driver", "elo_team"]], b.loc[upto4, ["elo_driver", "elo_team"]])
    assert not np.allclose(a.loc[~upto4, "elo_driver"], b.loc[~upto4, "elo_driver"])  # neskôr sa už líšia


def test_leak_check_catches_a_deliberate_leak(monkeypatch):
    """Úmyselná chyba (rating po pretekoch namiesto pred) musí test úniku zhodiť."""
    drivers = ["a", "b", "c", "d"]
    base = season_of(2025, 3, drivers)
    changed = base.copy()
    changed.loc[changed["round"] == 2, "position"] = [4, 3, 2, 1]
    real_pairwise = m._pairwise

    def leaky(df, p):  # rating po pretekoch
        out = []
        for g in m.races(df):
            r = np.full(len(g), m.MEAN) + p.k_driver * real_pairwise(
                np.full(len(g), m.MEAN), g["position"].to_numpy()
            )
            out.append(g.assign(elo_driver=r, elo_team=r))
        return pd.concat(out, ignore_index=True)

    a, b = leaky(base, m.EloParams()), leaky(changed, m.EloParams())
    r2 = lambda d: d[d["round"] == 2].sort_values("driver")["elo_driver"].to_numpy()  # noqa: E731
    assert not np.allclose(r2(a), r2(b))


def test_new_season_regresses_to_mean_and_lineage_keeps_team_rating():
    df = pd.concat([season_of(2024, 3, ["a", "b", "c", "d"]),
                    race(2025, 1, ["a", "b", "c", "d"], teams=["rb", "rb", "x", "x"])],
                   ignore_index=True)  # fmt: skip
    df.loc[df["season"] == 2024, "constructor"] = ["toro_rosso", "toro_rosso", "x", "x"] * 3
    r = m.elo_ratings(df, m.EloParams(32, 32, 0.5))
    end24 = m.elo_ratings(df[df["season"] == 2024], m.EloParams(32, 32, 0.5))
    first25 = r[(r["season"] == 2025)].set_index("driver")
    a_last = end24[end24["round"] == 3].set_index("driver")
    assert first25.loc["a", "elo_team"] > m.MEAN  # toro_rosso → rb: rating pokračuje
    assert abs(first25.loc["a", "elo_driver"] - m.MEAN) < abs(a_last.loc["a", "elo_driver"] - m.MEAN)


def test_quali_slot_puts_missing_last():
    df = race(2025, 1, ["a", "b", "c", "d"], quali=[1, 2, None, 3])
    assert m.quali_slot(df).tolist() == [1, 2, 4, 3]


def test_softmax_and_podium_sum_per_race():
    p = m.softmax_by_race(np.array([2.0, 1.0, 0.0, 3.0, 0.0, -1.0, 0.5]), np.array([1, 1, 1, 2, 2, 2, 2]))
    assert p[:3].sum() == pytest.approx(1) and p[3:].sum() == pytest.approx(1)
    pod = m.podium(p[3:])
    assert pod.sum() == pytest.approx(3) and (pod <= 1 + 1e-12).all() and pod[0] > pod[1]


def test_fit_logit_recovers_weight():
    rng = np.random.default_rng(1)
    x, won, rid = [], [], []
    for r in range(400):
        xr = rng.normal(size=(10, 1))
        p = np.exp(1.5 * xr[:, 0])
        won += list(np.eye(10)[rng.choice(10, p=p / p.sum())])
        x.append(xr)
        rid += [r] * 10
    w = m.fit_logit(np.vstack(x), np.array(won), np.array(rid))
    assert w[0] == pytest.approx(1.5, abs=0.25)


# --- backtest -------------------------------------------------------------------------------


def test_championship_rank_previous_season_then_cumulative_with_sprints():
    res = pd.concat([race(2024, 1, ["a", "b", "c", "d"]), race(2025, 1, ["d", "c", "b", "e"]),
                     race(2025, 2, ["a", "b", "c", "d"])], ignore_index=True)  # fmt: skip
    spr = pd.DataFrame({"season": [2025], "round": [1], "driver": ["a"], "points": [30.0]})
    r = bt.championship_rank(res, spr)
    first = r[(res["season"] == 2025) & (res["round"] == 1)].tolist()
    assert first == [4, 3, 2, 5]  # d, c, b podľa 2024 (a bol 1., ale tu nejde), nováčik e na konci
    second = dict(
        zip(
            res.loc[res["round"] == 2].loc[res["season"] == 2025, "driver"],
            r[(res["season"] == 2025) & (res["round"] == 2)],
            strict=True,
        )
    )
    assert second["a"] == 1 and second["d"] == 2  # a: 30 zo šprintu > d: 25
    assert r[res["season"] == 2024].isna().all()  # bez minulej sezóny v dátach


def test_score_counts_winner_log_loss_and_accuracy():
    df = race(2025, 1, ["a", "b", "c", "d"])
    s = bt.score(df, np.array([0.5, 0.3, 0.1, 0.1]))
    assert s.log_loss == pytest.approx(-np.log(0.5)) and s.accuracy == 1.0 and s.races == 1


def test_regulation_change_resets_ratings_to_mean():
    df = pd.concat([season_of(2025, 3, ["a", "b", "c", "d"]), season_of(2026, 1, ["a", "b", "c", "d"])])
    keep = m.elo_ratings(df, m.EloParams(32, 32, 0.9))
    reset = m.elo_ratings(df, m.EloParams(32, 32, 0.9, resets=(2026,)))
    first26 = lambda r: r[r["season"] == 2026][["elo_driver", "elo_team"]].to_numpy()  # noqa: E731
    assert np.allclose(first26(reset), m.MEAN)
    assert not np.allclose(first26(keep), m.MEAN)
