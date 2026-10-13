"""Glicko-2 pre NHL: vzorce podľa Glickmana, sezóny, únik dát a porovnanie s Elo (bez siete)."""

import math
import re

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.nhl import glicko as gk
from team_pulse.nhl import learned_glicko as lgk

SMALL_GRID = {"tau": [0.5], "hca": [30.0], "rd_season": [50.0, 100.0], "carryover": [0.9], "sigma": [0.06]}


def test_glickman_worked_example():
    """Hráč 1500/200/0,06 proti 1400/30 (výhra), 1550/100 a 1700/300 (prehry) → 1464,06 / 151,52 / 0,05999."""
    s = gk.SCALE
    mu, phi, sigma = 0.0, 200 / s, 0.06
    v_inv = dsum = 0.0
    for r, rd, score in [(1400, 30, 1), (1550, 100, 0), (1700, 300, 0)]:
        mj, pj = (r - 1500) / s, rd / s
        e, gj = gk.win_prob(mu, mj, pj), gk.g(pj)
        v_inv += gj * gj * e * (1 - e)
        dsum += gj * (score - e)
    v = 1 / v_inv
    new_sigma = gk._volatility(phi, sigma, v, v * dsum, 0.5)
    new_phi = 1 / math.sqrt(1 / (phi**2 + new_sigma**2) + 1 / v)
    assert 1500 + (mu + new_phi**2 * dsum) * s == pytest.approx(1464.06, abs=0.02)
    assert new_phi * s == pytest.approx(151.52, abs=0.01)
    assert new_sigma == pytest.approx(0.05999, abs=1e-5)


def test_update_one_direction_and_uncertainty():
    mu, phi, sigma = gk.update_one(0.0, 1.0, 0.06, 0.0, 1.0, 1.0, 0.5)
    assert mu > 0 and phi < 1.0 and sigma > 0
    mu2, _, _ = gk.update_one(0.0, 1.0, 0.06, 0.0, 1.0, 0.0, 0.5)
    assert mu2 == pytest.approx(-mu)


def test_uncertainty_pulls_prediction_to_half():
    sure, unsure = gk.win_prob(0.5, 0.0, 0.1), gk.win_prob(0.5, 0.0, 2.0)
    assert 0.5 < unsure < sure


def test_season_reset_regresses_strength_and_raises_uncertainty():
    p = gk.GlickoParams(rd_season=100.0, carryover=0.8)
    mu, phi = gk.season_reset(1.0, 50 / gk.SCALE, p)
    assert mu == pytest.approx(0.8)
    assert phi * gk.SCALE == pytest.approx(math.sqrt(50**2 + 100**2))
    assert gk.season_reset(0.0, 340 / gk.SCALE, p)[1] * gk.SCALE == pytest.approx(gk.MAX_RD)


def frame(rows, season=2025, start="2024-10-10"):
    d = pd.DataFrame(rows, columns=["home", "away", "goals_home", "goals_away"])
    d.insert(0, "game_id", range(1, len(d) + 1))
    d["season"] = season
    d["start_utc"] = pd.date_range(start, periods=len(d), freq="D").strftime("%Y-%m-%dT23:00:00Z")
    return d


def test_run_home_advantage_and_neutral_site():
    g = frame([("A", "B", 3, 2)])
    assert gk.run(g)["glicko_prob"].iat[0] > 0.5
    assert gk.run(g.assign(neutral=True))["glicko_prob"].iat[0] == pytest.approx(0.5)
    assert gk.run(g)["glicko_logit"].iat[0] == 0  # logit je bez domácej výhody (tú pridá model)


def test_run_winner_rises_and_new_season_adds_uncertainty():
    g = pd.concat(
        [frame([("A", "B", 3, 2)] * 3), frame([("A", "B", 3, 2)], 2026, "2025-10-10")], ignore_index=True
    )
    g["game_id"] = range(1, 5)
    res = gk.run(g, gk.GlickoParams(rd_season=100.0))
    assert res["glicko_home_pre"].iat[2] > res["glicko_home_pre"].iat[1] > res["glicko_home_pre"].iat[0]
    assert res["rd_home_pre"].iat[2] < res["rd_home_pre"].iat[1]  # viac zápasov = menšia neistota
    assert res["rd_home_pre"].iat[3] > res["rd_home_pre"].iat[2]  # po lete väčšia


def make_games(n, seed):
    rng = np.random.default_rng(seed)
    teams = ["AAA", "BBB", "CCC", "DDD"]
    home = rng.choice(teams, n)
    away = [rng.choice([t for t in teams if t != h]) for h in home]
    gh = rng.integers(0, 6, n)
    ga = np.where(rng.random(n) < 0.5, gh + 1, np.maximum(gh - 1, 0))
    ga = np.where(ga == gh, gh + 1, ga)
    return frame(list(zip(home, away, gh, ga, strict=True)))


@settings(max_examples=30, deadline=None)
@given(st.integers(min_value=0, max_value=24), st.integers(min_value=0, max_value=10_000))
def test_changing_result_does_not_change_earlier_predictions(k, seed):
    games = make_games(25, seed)
    base = gk.run(games)
    gh, ga = games["goals_home"].to_numpy().copy(), games["goals_away"].to_numpy().copy()
    gh[k:], ga[k:] = ga[k:].copy(), gh[k:].copy()
    after = gk.run(games.assign(goals_home=gh, goals_away=ga))
    cols = ["glicko_home_pre", "glicko_away_pre", "rd_home_pre", "glicko_prob"]
    pd.testing.assert_frame_equal(base.loc[:k, cols], after.loc[:k, cols])


def league(seed=7):
    """Malá liga 2018–2026 so skutočnou silou klubov."""
    rng = np.random.default_rng(seed)
    teams = ["BOS", "TOR", "MTL", "LAK", "SEA", "CHI"]
    strength = dict(zip(teams, rng.normal(0, 60, len(teams)), strict=True))
    rows, gid = [], 0
    for season in range(2018, 2027):
        day = pd.Timestamp(f"{season - 1}-10-10")
        for i in range(120):
            h, a = rng.choice(teams, 2, replace=False)
            day += pd.Timedelta(days=int(rng.integers(0, 2)))
            won = rng.random() < 1 / (1 + 10 ** (-(strength[h] - strength[a] + 30) / 400))
            gid += 1
            rows.append({"game_id": gid, "season": season, "game_type": "R", "date": day,
                         "start_utc": f"{day.date()}T{(i % 20):02d}:00:00Z", "home": h, "away": a,
                         "home_abbr": h, "away_abbr": a, "goals_home": 3 if won else 2,
                         "goals_away": 2 if won else 3, "neutral": False})  # fmt: skip
        strength = {t: s * 0.8 + rng.normal(0, 25) for t, s in strength.items()}
    return pd.DataFrame(rows)


def test_tuning_uses_only_training_seasons():
    g = league()
    test = g["season"] >= 2024
    flipped = g.copy()
    flipped.loc[test, ["goals_home", "goals_away"]] = (
        g.loc[test, ["goals_away", "goals_home"]].to_numpy().copy()
    )
    pd.testing.assert_frame_equal(lgk.tune(g, SMALL_GRID), lgk.tune(flipped, SMALL_GRID))


def test_evaluate_and_report():
    r = lgk.evaluate(league(), SMALL_GRID)
    assert list(r["summary"]["model"]) == [
        "A: Elo (samotné)", "A: Glicko-2 (samotné)", lgk.APPROVED, lgk.REPLACE, lgk.ADD,
    ]  # fmt: skip
    for d in r["decisions"].values():
        assert d["accepted"] == (d["gain"] >= lgk.THRESHOLD)
    md = lgk.to_markdown(r)
    assert "## Rozhodnutie" in md and "Glicko-2 namiesto Ela" in md
    assert not re.search(r"\bnan\b", md, re.IGNORECASE)
