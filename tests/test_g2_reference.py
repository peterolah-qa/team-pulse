"""Referencia pre brány G2: okná, začiatky sezón, baseline z tréningu (bez dát z data/raw)."""

import importlib.util
import math
import re
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("g2_reference", Path("scripts/g2_reference.py"))
g2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g2)


def frame(season=2025, days=20, start="2024-10-22", p=0.5, home_won=1, train=False):
    d = pd.DataFrame({"date": pd.date_range(start, periods=days, freq="D")})
    return d.assign(season=season, p=p, home_won=home_won, train=train, test=not train, regular=True)


def test_scores_use_home_rate_from_training_regular_season_only():
    train = pd.concat([frame(2020, 4, "2019-10-01", home_won=1, train=True),
                       frame(2020, 4, "2019-11-01", home_won=0, train=True)])  # fmt: skip
    playoff = frame(2020, 10, "2020-04-20", home_won=1, train=True).assign(regular=False)
    scored, rate = g2.add_scores(pd.concat([train, playoff, frame()], ignore_index=True))
    assert rate == 0.5  # playoff sa do baseline nepočíta
    test = scored[scored["test"]]
    assert test["ll"].iloc[0] == pytest.approx(math.log(2))
    assert test["hit"].eq(False).all()  # šanca 0,5 nie je tip na domácich, domáci vyhrali


def test_windows_and_season_start():
    scored, _ = g2.add_scores(pd.concat([frame(2020, 2, "2019-10-01", train=True), frame(days=20)]))
    test = scored[scored["test"]]
    win = g2.windows(test)
    assert len(win) == 20 - 14 + 1 and (win["n"] == 14).all()
    start = g2.season_starts(test)
    assert len(start) == 14 and start["date"].max() == pd.Timestamp("2024-11-04")


def test_windows_skip_empty_breaks():
    gap = pd.concat([frame(days=14), frame(days=14, start="2024-12-01")])  # 2 týždne bez zápasov medzi
    scored, _ = g2.add_scores(pd.concat([frame(2020, 2, "2019-10-01", train=True), gap]))
    win = g2.windows(scored[scored["test"]])
    assert (win["n"] > 0).all()
    assert len(win) < len(pd.date_range("2024-10-22", "2024-11-30"))


def test_report_has_both_sports_and_limits():
    r = g2.reference(pd.concat([frame(2020, 30, "2019-10-01", train=True), frame(days=30)]))
    md = g2.to_markdown({"NBA": r, "NHL": r}, pd.Timestamp("2026-10-14").date())
    assert "## NBA" in md and "## NHL" in md and "95. percentil" in md
    assert not re.search(r"\bnan\b", md, re.IGNORECASE)
