"""Backtest NHL: tréning a test sa nemiešajú, baseline aj parametre len z tréningu, report."""

import re

import numpy as np
import pandas as pd
import pytest

from team_pulse.nhl import backtest as bt

SMALL_GRID = {"k": [6.0, 8.0], "hca": [30.0, 50.0], "carryover": [0.7]}
TEAMS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


def league(seed=1, first=2018, last=2026):
    """Malá liga so skutočnou silou teamov: 6 teamov, každý s každým 6× za sezónu + 3 zápasy playoff."""
    rng = np.random.default_rng(seed)
    strength = dict(zip(TEAMS, rng.normal(0, 60, len(TEAMS)), strict=True))
    rows, gid = [], 0
    for season in range(first, last + 1):
        day = pd.Timestamp(f"{season - 1}-10-10")
        pairs = [(h, a) for h in TEAMS for a in TEAMS if h != a] * 3
        for i, (h, a) in enumerate(pairs + [("AAA", "BBB")] * 3):
            p = 1 / (1 + 10 ** (-(strength[h] - strength[a] + 35) / 400))
            home_won = rng.random() < p
            margin = int(rng.integers(1, 4))
            loser = int(rng.integers(0, 4))
            gh, ga = (loser + margin, loser) if home_won else (loser, loser + margin)
            gid += 1
            rows.append({
                "game_id": gid, "season": season, "game_type": "P" if i >= len(pairs) else "R",
                "start_utc": (day + pd.Timedelta(hours=12 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "home": h, "away": a, "goals_home": gh, "goals_away": ga,
                "last_period": "OT" if margin == 1 and i % 4 == 0 else "REG",
            })  # fmt: skip
        strength = {t: s * 0.8 + rng.normal(0, 25) for t, s in strength.items()}
    return pd.DataFrame(rows)


def test_split_burn_in_train_test_and_only_regular_season():
    g = league()
    train, test = bt.split(g)
    assert sorted(g.loc[train, "season"].unique()) == [2021, 2022, 2023]  # 2018–2020 = rozbeh
    assert sorted(g.loc[test, "season"].unique()) == [2024, 2025, 2026]
    assert set(g.loc[train | test, "game_type"]) == {"R"}
    assert not (train & test).any()


def test_record_category_uses_only_the_past():
    g = league()
    cat = bt.record_category(g)
    first_of_season = g.groupby("season").head(1).index
    assert (cat[first_of_season] == 0).all()
    changed = swap(g, g.index >= 100)
    pd.testing.assert_series_equal(cat[:101], bt.record_category(changed)[:101])


def swap(g, mask):
    """Otočí výsledok vybraných zápasov (víťaz ↔ porazený)."""
    out = g.copy()
    gh, ga = out["goals_home"].to_numpy().copy(), out["goals_away"].to_numpy().copy()
    out["goals_home"], out["goals_away"] = np.where(mask, ga, gh), np.where(mask, gh, ga)
    return out


def flip_test_seasons(g):
    return swap(g, bt.split(g)[1].to_numpy())


def test_baselines_and_parameters_learned_only_from_training():
    g = league()
    train, _ = bt.split(g)
    flipped = flip_test_seasons(g)
    assert bt.fit_baselines(g, train) == bt.fit_baselines(flipped, bt.split(flipped)[0])
    assert (flipped["goals_home"] != g["goals_home"]).any()
    tuned = bt.tune(flipped, bt.split(flipped)[0], SMALL_GRID)
    pd.testing.assert_frame_equal(bt.tune(g, train, SMALL_GRID), tuned)


def test_baseline_probabilities_are_training_frequencies():
    g = league()
    train, _ = bt.split(g)
    fit = bt.fit_baselines(g, train)
    won = g["goals_home"] > g["goals_away"]
    assert fit["home_rate"] == pytest.approx(won[train].mean())
    probs = bt.baseline_probs(g, fit)
    assert probs["Baseline: vždy domáci"].nunique() == 1
    assert set(probs["Baseline: lepšia bilancia"].round(10)) <= {round(v, 10) for v in fit["record"].values()}


def test_backtest_summary_gate_and_report():
    r = bt.backtest(league(), SMALL_GRID)
    models = r["summary"]["model"].tolist()
    assert models == ["Elo ladené na tréningu", "Elo štart (FiveThirtyEight)", "Baseline: vždy domáci",
                      "Baseline: lepšia bilancia"]  # fmt: skip
    assert (r["summary"]["n"] == r["counts"]["test"]).all()
    g = r["gate"]
    assert g["passed"] == (g["elo"] <= g["baseline"] - bt.THRESHOLD)
    assert r["tuned"].k in SMALL_GRID["k"] and r["tuned"].hca in SMALL_GRID["hca"]
    md = bt.to_markdown(r)
    assert "## Brána G0-NHL" in md and "2023/24 – 2025/26" in md and "Po sezónach (test)" in md
    assert not re.search(r"\bnan\b", md, re.IGNORECASE)


def test_backtest_needs_test_seasons():
    with pytest.raises(ValueError, match="testovacie"):
        bt.backtest(league(last=2023), SMALL_GRID)
