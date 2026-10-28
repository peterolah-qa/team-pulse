"""NFL: načítanie games.csv bez stávkových stĺpcov, Elo bez úniku dát, contract ESPN (brána G0-NFL)."""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from team_pulse.nfl import app_data as A
from team_pulse.nfl import elo, espn
from team_pulse.nfl import games as G
from team_pulse.nfl import predict as P
from team_pulse.nfl import qb as Q
from team_pulse.nfl.backtest import record_diff

FIXTURE = Path("tests/fixtures/nfl_espn_scoreboard.json")

HEADER = (
    "game_id,season,game_type,week,gameday,weekday,gametime,away_team,away_score,home_team,home_score,"
    "location,result,total,overtime,old_game_id,gsis,nfl_detail_id,pfr,pff,espn,ftn,away_rest,home_rest,"
    "away_moneyline,home_moneyline,spread_line,away_spread_odds,home_spread_odds,total_line,under_odds,"
    "over_odds,div_game,roof,surface,temp,wind,away_qb_id,home_qb_id,away_qb_name,home_qb_name,away_coach,"
    "home_coach,referee,stadium_id,stadium"
)


def row(
    gid: str,
    season: int,
    gtype: str,
    week: int,
    day: str,
    away: str,
    a: str,
    home: str,
    h: str,
    loc: str = "Home",
    espn_id: str = "1",
) -> str:
    vals = {
        "game_id": gid,
        "season": season,
        "game_type": gtype,
        "week": week,
        "gameday": day,
        "weekday": "Sunday",
        "gametime": "13:00",
        "away_team": away,
        "away_score": a,
        "home_team": home,
        "home_score": h,
        "location": loc,
        "espn": espn_id,
        "away_rest": 7,
        "home_rest": 7,
        "away_moneyline": -150,
        "home_moneyline": 130,
        "spread_line": -3.5,
        "away_spread_odds": -110,
        "home_spread_odds": -110,
        "total_line": 44.5,
        "under_odds": -110,
        "over_odds": -110,
        "div_game": 0,
        "away_qb_name": "QB A",
        "home_qb_name": "QB H",
    }
    return ",".join(str(vals.get(c, "")) for c in HEADER.split(","))


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    lines = [
        HEADER,
        row("1999_01_OAK_SD", 1999, "REG", 1, "1999-09-12", "OAK", "17", "SD", "20"),
        row("1999_02_STL_OAK", 1999, "REG", 2, "1999-09-19", "STL", "10", "OAK", "10"),
        row("2026_08_CAR_GB", 2026, "REG", 8, "2026-10-29", "CAR", "", "GB", "", espn_id="401873023"),
        row("2025_22_SEA_NE", 2025, "SB", 22, "2026-02-08", "SEA", "27", "NE", "24", loc="Neutral"),
    ]
    p = tmp_path / "games.csv"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_betting_columns_never_loaded(csv_path: Path) -> None:
    g = G.load(csv_path)
    assert not set(G.BETTING) & set(g.columns)
    assert not any(("line" in c) or ("odds" in c) or ("moneyline" in c) for c in g.columns)
    assert not set(G.BETTING) & set(G.ALLOWED)


def test_load_franchises_neutral_ties_unplayed(csv_path: Path) -> None:
    g = G.load(csv_path).set_index("game_id")
    assert (g.loc["1999_01_OAK_SD", "away"], g.loc["1999_01_OAK_SD", "home"]) == ("LV", "LAC")
    assert g.loc["1999_02_STL_OAK", "away"] == "LA"
    assert bool(g.loc["1999_02_STL_OAK", "tie"])
    assert not bool(g.loc["2026_08_CAR_GB", "played"])
    assert g.loc["2026_08_CAR_GB", "espn_id"] == "401873023"
    sb = g.loc["2025_22_SEA_NE"]
    assert bool(sb["neutral"]) and bool(sb["playoff"])


def test_unknown_game_type_rejected(tmp_path: Path) -> None:
    p = tmp_path / "games.csv"
    p.write_text(HEADER + "\n" + row("x", 2026, "PRE", 1, "2026-08-10", "A", "1", "B", "2") + "\n")
    with pytest.raises(ValueError, match="neznámy typ"):
        G.load(p)


def test_expected_counts_known_exceptions() -> None:
    assert G.EXPECTED[2020] == (256, 13)
    assert G.EXPECTED[2022] == (271, 13)
    assert G.EXPECTED[2025] == (272, 13)


def games_frame(results: list[tuple[str, str, int, int]], season: int = 2010) -> pd.DataFrame:
    rows = []
    for i, (home, away, sh, sa) in enumerate(results):
        rows.append(
            {
                "game_id": f"g{i:03d}",
                "season": season,
                "date": pd.Timestamp("2010-09-12") + pd.Timedelta(days=7 * i),
                "home": home,
                "away": away,
                "score_home": sh,
                "score_away": sa,
                "neutral": False,
                "playoff": False,
                "played": True,
                "tie": sh == sa,
            }
        )
    return pd.DataFrame(rows)


def test_elo_matches_formula_one_game() -> None:
    p = elo.START
    nh, na = elo.update(1505.0, 1505.0, 24, 17, p)
    e = elo.expected(p.hfa)
    mult = elo.mov_multiplier(7, p.hfa)
    assert nh == pytest.approx(1505.0 + p.k * mult * (1 - e))
    assert na == pytest.approx(1505.0 - p.k * mult * (1 - e))


def test_tie_counts_as_half() -> None:
    nh, na = elo.update(1505.0, 1505.0, 20, 20, elo.START, neutral=True)
    assert nh == pytest.approx(1505.0) and na == pytest.approx(1505.0)
    nh, _ = elo.update(1600.0, 1400.0, 20, 20, elo.START, neutral=True)
    assert nh < 1600.0  # favorit s remízou stratí


def test_playoff_and_neutral_change_probability() -> None:
    d_reg = elo.diff(1600, 1500, elo.START, neutral=False, playoff=False)
    assert elo.diff(1600, 1500, elo.START, neutral=True, playoff=False) == pytest.approx(100.0)
    assert elo.diff(1600, 1500, elo.START, neutral=False, playoff=True) == pytest.approx(d_reg * 1.2)


TEAMS = st.sampled_from(["A", "B", "C", "D"])
GAME = st.tuples(TEAMS, TEAMS, st.integers(0, 45), st.integers(0, 45)).filter(lambda t: t[0] != t[1])


@settings(max_examples=60, deadline=None)
@given(st.lists(GAME, min_size=3, max_size=25), st.data())
def test_no_leak_future_results_do_not_change_past_predictions(results, data) -> None:
    """Kritérium 3: zmena výsledku zápasu i a neskorších nezmení predpoveď zápasov ≤ i."""
    i = data.draw(st.integers(0, len(results) - 1))
    changed = results[:i] + [(h, a, sa, sh) for h, a, sh, sa in results[i:]]
    base = elo.run(games_frame(results))["prob_home"].to_numpy()
    alt = elo.run(games_frame(changed))["prob_home"].to_numpy()
    assert base[: i + 1] == pytest.approx(alt[: i + 1])


def leaky_run(games: pd.DataFrame) -> pd.DataFrame:
    """Úmyselná chyba: šanca z ratingu PO zápase (pozná vlastný výsledok)."""
    r = elo.run(games)
    r["prob_home"] = [
        elo.expected(h - a + elo.START.hfa)
        for h, a in zip(r["elo_home_post"], r["elo_away_post"], strict=True)
    ]
    return r


def leaks(run_fn, results) -> bool:
    flipped = results[:-1] + [(results[-1][0], results[-1][1], results[-1][3], results[-1][2])]
    a = run_fn(games_frame(results))["prob_home"].iloc[-1]
    b = run_fn(games_frame(flipped))["prob_home"].iloc[-1]
    return abs(a - b) > 1e-12


def test_leak_check_catches_intentional_error() -> None:
    results = [("A", "B", 30, 10), ("B", "C", 7, 21), ("C", "A", 28, 3)]
    assert leaks(leaky_run, results)
    assert not leaks(elo.run, results)


def test_record_diff_uses_only_earlier_games() -> None:
    g = games_frame([("A", "B", 20, 10), ("A", "C", 3, 30), ("B", "C", 10, 10)])
    g["played"] = True
    d = record_diff(g).tolist()
    assert d[0] == 0.0  # 1. zápas sezóny: obaja 0,5
    assert d[1] == pytest.approx(1.0 - 0.5)  # A 1/1, C bez zápasu
    assert d[2] == pytest.approx(0.0 - 1.0)  # B 0/1, C 1/1


def test_contract_espn_scoreboard() -> None:
    """Kritérium 5: skutočný tvar odpovede ESPN (sonda 28. 10. 2026), ID zápasu = games.csv."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    games = espn.parse_scoreboard(data)
    assert len(games) == 3
    first = games[0]
    assert (first["espn_id"], first["away"], first["home"]) == ("401873023", "CAR", "GB")
    assert first["kickoff_utc"] == "2026-10-30T00:15Z"
    assert not first["final"] and first["score_home"] is None
    assert all(set(x) >= {"espn_id", "home", "away", "neutral", "state", "kickoff_utc"} for x in games)


def test_espn_team_codes_match_nflverse() -> None:
    assert espn.team("WSH") == "WAS" and espn.team("LAR") == "LA" and espn.team("GB") == "GB"


# --- ostré tipy (team_pulse.nfl.predict) ---


ANY = dataclasses.replace(P.ELO, start=(0, 0))  # testy na malej sezóne od týždňa 1


def week_games(played_weeks: int, weeks: int = 3) -> pd.DataFrame:
    """Malá sezóna 2026: 2 zápasy týždenne, odohrané prvé `played_weeks` týždne."""
    rows = []
    pairs = [("A", "B"), ("C", "D")]
    for w in range(1, weeks + 1):
        for j, (h, a) in enumerate(pairs):
            played = w <= played_weeks
            rows.append(
                {
                    "game_id": f"2026_{w:02d}_{a}_{h}",
                    "season": 2026,
                    "game_type": "REG",
                    "week": w,
                    "date": pd.Timestamp("2026-09-13") + pd.Timedelta(days=7 * (w - 1)),
                    "gametime": "13:00",
                    "home": h,
                    "away": a,
                    "score_home": 24.0 if played else None,
                    "score_away": 17.0 if played and j == 0 else (27.0 if played else None),
                    "neutral": False,
                    "playoff": False,
                    "played": played,
                    "tie": False,
                    "espn_id": f"40{w}{j}",
                    "home_qb": "QB H",
                    "away_qb": "QB A",
                }
            )
    return pd.DataFrame(rows)


def test_kickoff_utc_handles_daylight_saving() -> None:
    assert P.kickoff_utc(pd.Timestamp("2026-10-29"), "20:15") == pd.Timestamp("2026-10-30 00:15", tz="UTC")
    assert P.kickoff_utc(pd.Timestamp("2026-11-08"), "13:00") == pd.Timestamp("2026-11-08 18:00", tz="UTC")
    assert P.kickoff_utc(pd.Timestamp("2026-11-08"), None) is None


def test_lock_only_next_week_before_kickoff() -> None:
    g = week_games(played_weeks=1)
    assert P.next_week(g) == (2026, 2)
    now = pd.Timestamp("2026-09-20 17:30", tz="UTC")  # 13:30 ET týždňa 2: zápasy o 13:00 ET už začali
    tips, problems = P.tips_for_week(g, 2026, 2, now, "abc", set(), ANY)
    assert tips == [] and len(problems) == 2 and all("už začal" in p for p in problems)
    early = pd.Timestamp("2026-09-19 12:00", tz="UTC")
    tips, problems = P.tips_for_week(g, 2026, 2, early, "abc", set(), ANY)
    assert [t["week"] for t in tips] == [2, 2] and not problems
    assert all(0 < t["p_home"] < 1 and t["model"] == P.MODEL and t["games_commit"] == "abc" for t in tips)


def test_no_tips_if_previous_week_unfinished() -> None:
    g = week_games(played_weeks=1)
    g.loc[g["week"] == 1, ["played", "score_home", "score_away"]] = [False, None, None]
    tips, problems = P.tips_for_week(g, 2026, 2, pd.Timestamp("2026-09-19", tz="UTC"), "abc", set(), ANY)
    assert tips == [] and "nie sú dohraté" in problems[0]


def test_locked_tip_never_overwritten(tmp_path: Path) -> None:
    g = week_games(played_weeks=1)
    now = pd.Timestamp("2026-09-19 12:00", tz="UTC")
    tips, _ = P.tips_for_week(g, 2026, 2, now, "abc", set(), ANY)
    P.save(tips, 2026, 2, tmp_path)
    changed = [dict(t, p_home=0.01) for t in tips]
    P.save(changed, 2026, 2, tmp_path)
    again = P.locked(tmp_path)
    assert {t["p_home"] for t in again.values()} == {t["p_home"] for t in tips}
    tips2, _ = P.tips_for_week(g, 2026, 2, now, "abc", set(again), ANY)
    assert tips2 == []


def test_evaluate_hit_logloss_and_tie_excluded() -> None:
    g = week_games(played_weeks=2)
    tips = {
        "2026_02_B_A": {
            "game_id": "2026_02_B_A",
            "week": 2,
            "kickoff_utc": "2026-09-20T17:00Z",
            "home": "A",
            "away": "B",
            "p_home": 0.6,
        },
        "2026_02_D_C": {
            "game_id": "2026_02_D_C",
            "week": 2,
            "kickoff_utc": "2026-09-20T17:00Z",
            "home": "C",
            "away": "D",
            "p_home": 0.7,
        },
    }
    ev = P.evaluate(tips, g).set_index("game_id")
    assert bool(ev.loc["2026_02_B_A", "hit"]) and not bool(ev.loc["2026_02_D_C", "hit"])  # C prehral 24:27
    assert ev.loc["2026_02_B_A", "ll"] == pytest.approx(-math.log(0.6))
    assert ev.loc["2026_02_D_C", "ll"] == pytest.approx(-math.log(0.3))
    g.loc[g["game_id"] == "2026_02_B_A", ["score_away", "tie"]] = [24.0, True]
    assert "2026_02_B_A" not in set(P.evaluate(tips, g)["game_id"])


def test_models_start_weeks() -> None:
    g = week_games(played_weeks=1)
    early = pd.Timestamp("2026-09-19 12:00", tz="UTC")
    assert P.tips_for_week(g, 2026, 2, early, "abc", set(), P.ELO) == ([], [])  # Elo od týždňa 8
    assert P.ELO.start == (2026, 8) and P.ELO_QB.start == (2026, 10)
    assert P.ELO.archive != P.ELO_QB.archive and P.ELO.report != P.ELO_QB.report


def test_primary_qb_mode_with_recent_tiebreak() -> None:
    assert Q.primary([]) is None
    assert Q.primary(["a", "a", "b"]) == "a"
    assert Q.primary(["a", "b"]) == "b"  # rovnosť → posledný
    assert Q.primary(["x"] * 5 + ["a"] * 8) == "a"  # len posledných 8


def qb_games(home_qbs: list[str | None], played: list[bool]) -> pd.DataFrame:
    rows = []
    for i, (qb, pl) in enumerate(zip(home_qbs, played, strict=True)):
        rows.append(
            {
                "game_id": f"g{i}",
                "season": 2026,
                "week": i + 1,
                "date": pd.Timestamp("2026-09-13") + pd.Timedelta(days=7 * i),
                "home": "A",
                "away": f"X{i}",
                "home_qb_id": qb,
                "away_qb_id": f"x{i}",
                "played": pl,
            }
        )
    return pd.DataFrame(rows)


def test_backup_flags_only_from_played_games() -> None:
    f = Q.backup_flags(qb_games(["a", "a", "b", "a", None], [True, True, True, False, True]))
    assert f["home_backup"].tolist() == [0, 0, 1, 0, 0]  # 1. zápas bez histórie, None = neznámy quarterback
    assert f.loc[3, "home_primary"] == "a"
    g = qb_games(["a", "b", "b"], [True, False, True])  # neodohraný zápas s „b“ sa nepočíta do histórie
    assert Q.backup_flags(g)["home_backup"].tolist() == [0, 1, 1]


def test_qb_model_tip_has_flags_and_penalty() -> None:
    g = week_games(played_weeks=1)
    g["home_qb_id"] = "h1"
    g["away_qb_id"] = "a1"
    g.loc[g["week"] == 2, "home_qb_id"] = "h2"  # týždeň 2: domáci s náhradníkom
    early = pd.Timestamp("2026-09-19 12:00", tz="UTC")
    model = dataclasses.replace(P.ELO_QB, start=(0, 0))
    elo, _ = P.tips_for_week(g, 2026, 2, early, "abc", set(), ANY)
    qb, _ = P.tips_for_week(g, 2026, 2, early, "abc", set(), model)
    for e, q in zip(elo, qb, strict=True):
        assert q["home_backup"] == 1 and q["away_backup"] == 0 and q["model"] == "nfl-elo-qb-v1"
        assert q["elo_diff"] == pytest.approx(e["elo_diff"] - Q.BACKUP_PENALTY, abs=0.11)
        assert q["p_home"] < e["p_home"]


# --- NFL pre appku (team_pulse.nfl.app_data) ---


def tip_for(g: pd.DataFrame, now: pd.Timestamp) -> dict:
    tips, _ = P.tips_for_week(g, 2026, 2, now, "abc", set(), ANY)
    return tips[0]


def test_edge_items_sum_exactly_and_verify_by_recompute() -> None:
    g = week_games(played_weeks=1)
    tip = tip_for(g, pd.Timestamp("2026-09-19 12:00", tz="UTC"))
    e = A.edge(tip, tip["elo_diff"])
    assert sum(v for _, _, v in e["items"]) == pytest.approx(e["total"], abs=1e-9)
    assert [k for k, _, _ in e["items"]] == ["elo", "home"]
    assert e["verified"] is True
    assert A.edge(tip, tip["elo_diff"] + 5)["verified"] is False
    assert A.edge(tip, None)["verified"] is False


def test_edge_playoff_and_neutral() -> None:
    tip = {
        "elo_diff": 120.0,
        "neutral": True,
        "playoff": True,
        "home": "A",
        "p_home": round(elo.expected(120.0), 4),
    }
    e = A.edge(tip, 120.0)
    assert [k for k, _, _ in e["items"]] == ["elo", "playoff"]  # neutrálne ihrisko: bez výhody domáceho
    assert e["items"][0][2] == pytest.approx(100.0) and e["items"][1][2] == pytest.approx(20.0)


def test_build_upcoming_results_and_live() -> None:
    g = week_games(played_weeks=1)
    g["gametime"] = "13:00"
    g["home_qb_id"], g["away_qb_id"] = "h", "a"
    now = pd.Timestamp("2026-09-19 12:00", tz="UTC")
    tips = {t["game_id"]: t for t in P.tips_for_week(g, 2026, 2, now, "abc", set(), ANY)[0]}
    data = A.build(g, tips, {}, now.to_pydatetime(), "abc")
    upcoming = [x for xs in data["days"].values() for x in xs]
    assert {x["game_id"] for x in upcoming} == set(tips)
    assert all(x["edge"]["verified"] for x in upcoming)
    assert all(x["trend"]["home"][-1][1] == x["home"]["elo"] for x in upcoming)  # posledný bod = Elo v tipe
    assert {r["week"] for r in data["results"]} == {1} and all(r["p_home"] is None for r in data["results"])
    assert data["live"]["elo"]["locked"] == 2 and data["live"]["elo"]["n"] == 0
    assert len(data["teams"]) == 4 and data["teams"][0]["elo"] >= data["teams"][-1]["elo"]


def test_result_uses_tip_only_if_locked_before_kickoff() -> None:
    tip = {"locked_at": "2026-09-20T17:00:01Z"}
    assert A._locked_before(tip, "2026-09-20T17:00Z") is None
    assert A._locked_before({"locked_at": "2026-09-20T16:59:59Z"}, "2026-09-20T17:00Z") is not None
