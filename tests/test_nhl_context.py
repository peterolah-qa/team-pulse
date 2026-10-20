"""Kontext NHL zápasu pre detail v appke (bez siete).

Hlavný test: rozpisy klubov → skutočná predikcia (team_pulse.nhl.predict) → zamknutý tip → kontext.
Rozpad tipu musí z rovnakého rozpisu dať presne zamknutú šancu a odpočinok rovnaké čísla ako model.
"""

import json
import math
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from team_pulse.model_store import load
from team_pulse.nhl import context as cx
from team_pulse.nhl.fetch_games import finished_games, season_frame
from team_pulse.nhl.model import MODEL
from team_pulse.nhl.predict import predict

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 20, 8, 15, tzinfo=UTC)  # ranná NHL úloha 20. 10.
IDS = {"MTL": 8, "SJS": 28, "OTT": 9, "BOS": 6, "TOR": 10, "CHI": 16}


def raw(gid, day, home, away, gh=None, ga=None, last="REG", hour=23, season=20262027, gtype=2, venue=None):
    """Zápas v tvare rozpisu klubu z API NHL (ako tests/fixtures/nhl_club_schedule.json)."""
    final = gh is not None
    g = {
        "id": gid, "season": season, "gameType": gtype, "gameDate": day,
        "venue": {"default": venue or f"Hala {home}"}, "neutralSite": False,
        "startTimeUTC": f"{day}T{hour:02d}:00:00Z", "gameState": "OFF" if final else "FUT",
        "homeTeam": {"id": IDS[home], "abbrev": home, **({"score": gh} if final else {})},
        "awayTeam": {"id": IDS[away], "abbrev": away, **({"score": ga} if final else {})},
    }  # fmt: skip
    if final:
        g["gameOutcome"] = {"lastPeriodType": last}
    return g


# Sezóna 2026/27 do rána 20. 10.: SJS hrá 19. 10. v Ottawe (back-to-back, 4. zápas výjazdu),
# MTL naposledy 17. 10. doma. Večer 20. 10. SJS @ MTL.
CURRENT = [
    raw(2026020001, "2026-10-08", "MTL", "TOR", 4, 2),
    raw(2026020002, "2026-10-09", "SJS", "CHI", 1, 3),
    raw(2026020010, "2026-10-11", "BOS", "MTL", 2, 3, "OT"),
    raw(2026020011, "2026-10-12", "SJS", "BOS", 5, 1),
    raw(2026020020, "2026-10-14", "MTL", "CHI", 1, 2, "SO"),
    raw(2026020021, "2026-10-15", "TOR", "SJS", 3, 2),
    raw(2026020030, "2026-10-17", "MTL", "OTT", 6, 3),
    raw(2026020031, "2026-10-17", "BOS", "SJS", 2, 4, hour=17),
    raw(2026020040, "2026-10-19", "OTT", "SJS", 3, 1),
    raw(2026020141, "2026-10-20", "MTL", "SJS", venue="Bell Centre"),
    raw(2026020150, "2026-10-22", "SJS", "MTL"),
]
PREVIOUS = [
    raw(2025020500, "2025-12-01", "MTL", "SJS", 3, 2, season=20252026),
    raw(2025020900, "2026-01-20", "SJS", "MTL", 4, 3, "SO", season=20252026),
    raw(2025021100, "2026-03-02", "MTL", "SJS", 5, 1, season=20252026),
    raw(2025021200, "2026-03-20", "SJS", "MTL", 2, 0, season=20252026),
    raw(2025020100, "2025-10-20", "MTL", "TOR", 2, 1, season=20252026),
]


@pytest.fixture(scope="module")
def model():
    return load(MODEL)


def club(games: list[dict], team: str) -> list[dict]:
    return [
        c for g in games if team in (g["homeTeam"]["abbrev"], g["awayTeam"]["abbrev"]) if (c := cx.compact(g))
    ]


def cache_for(teams=("MTL", "SJS"), fetched=NOW) -> dict:
    return {
        "version": cx.CACHE_VERSION,
        "teams": {
            t: {
                "2027": {"fetched_at": fetched.isoformat(), "games": club(CURRENT, t)},
                "2026": {"fetched_at": fetched.isoformat(), "games": club(PREVIOUS, t)},
            }
            for t in teams
        },
    }


@pytest.fixture(scope="module")
def tips(model):
    """Tipy zo skutočnej predikcie, zamknuté ráno 20. 10. (ako team_pulse.nhl.daily)."""
    history = finished_games(season_frame(PREVIOUS))
    out = predict(history, season_frame(CURRENT), model, date(2026, 10, 20), days=3)
    return [{**t, "model": model.version, "locked_at": NOW.isoformat(timespec="seconds")} for t in out]


def tip_of(tips, gid="2026020141"):
    return next(t for t in tips if t["game_id"] == gid)


def p_from(total: float, model) -> float:
    scale = model.coef[model.features.index("elo_diff")]
    return 1 / (1 + math.exp(-total * scale / 100))


def test_compact_reads_real_club_schedule_and_skips_preseason():
    games = json.loads((FIXTURES / "nhl_club_schedule.json").read_text(encoding="utf-8"))["games"]
    rows = [cx.compact(g) for g in games]
    assert rows.count(None) == sum(1 for g in games if g["gameType"] == 1)
    done = [r for r in rows if r]
    assert all(r["type"] in ("R", "P") and r["venue"] and r["home_id"] for r in done)
    assert all((r["gh"] is None) == (not r["final"]) for r in done)


def test_edge_is_verified_and_sums_exactly_to_locked_probability(tips, model):
    t = tip_of(tips)
    ctx = cx.game_context(t, tips, cache_for(), model, {})
    e = ctx["edge"]
    assert e["verified"] is True
    assert round(sum(v for *_, v in e["items"]), 1) == e["total"]
    assert round(p_from(e["total"], model), 3) == t["p_home"]
    keys = [k for k, *_ in e["items"]]
    assert keys[:3] == ["elo", "home", "base"] and "away_b2b" in keys and "away_road" in keys
    labels = dict((k, label) for k, label, _ in e["items"])
    assert labels["away_b2b"] == "SJS: back-to-back"
    assert labels["away_road"] == "SJS: 4. zápas výjazdu"
    assert labels["home_rest"] == "MTL: 2 dni voľna"
    assert labels["away_rest"] == "SJS: bez dňa voľna"
    assert dict((k, v) for k, _, v in e["items"])["elo"] == round(t["home"]["elo"] - t["away"]["elo"], 1)


def test_every_predicted_tip_is_verified(tips, model):
    """Aj zápas o dva dni (SJS doma, MTL na výjazde) – rovnaký výpočet ako predikcia."""
    for t in tips:
        e = cx.game_context(t, tips, cache_for(), model, {})["edge"]
        assert e["verified"] is True, t["game_id"]
        assert round(p_from(e["total"], model), 3) == t["p_home"]


def test_edge_without_schedule_falls_back_to_archive_reasons_and_still_sums(tips, model):
    t = tip_of(tips)
    e = cx.game_context(t, tips, {}, model, {})["edge"]
    assert e["verified"] is False
    assert [k for k, *_ in e["items"]] == ["elo", "home", "away_reason", "other"]
    assert round(sum(v for *_, v in e["items"]), 1) == e["total"]
    assert round(p_from(e["total"], model), 3) == t["p_home"]
    b2b = next(v for k, label, v in e["items"] if k == "away_reason")
    assert b2b == pytest.approx(-t["away"]["reasons"]["back-to-back"], abs=0.1)  # pomáha domácim


def test_edge_with_changed_schedule_is_not_verified(tips, model):
    """Zápas presunutý po zamknutí: z nového rozpisu vyjde iná šanca → rozpad z archívu."""
    moved = [
        g if g["id"] != 2026020040 else raw(2026020040, "2026-10-18", "OTT", "SJS", 3, 1) for g in CURRENT
    ]
    cache = cache_for()
    cache["teams"]["SJS"]["2027"]["games"] = club(moved, "SJS")
    e = cx.game_context(tip_of(tips), tips, cache, model, {})["edge"]
    assert e["verified"] is False


def test_rest_matches_model_inputs_and_facts(tips, model):
    ctx = cx.game_context(tip_of(tips), tips, cache_for(), model, {})
    assert ctx["away"]["rest"] == {
        "prev": {"date": "2026-10-19", "opp": "OTT", "home": False, "res": "L"},
        "rest": 1, "b2b": True, "three_in4": True, "tz_east": 0, "road": 4,
    }  # fmt: skip
    assert ctx["home"]["rest"]["rest"] == 3 and ctx["home"]["rest"]["b2b"] is False
    assert ctx["home"]["rest"]["prev"] == {"date": "2026-10-17", "opp": "OTT", "home": True, "res": "W"}
    assert ctx["venue"] == "Bell Centre"


def test_form_record_last_five_and_goals(tips, model):
    f = cx.game_context(tip_of(tips), tips, cache_for(), model, {})["home"]["form"]
    assert f["gp"] == 4
    assert f["record"] == [3, 0, 1]  # výhra po predĺžení je výhra, prehra po nájazdoch = OTL
    assert f["home_record"] == [2, 0, 1] and f["road_record"] == [1, 0, 0]
    assert [(x["opp"], x["res"], x["gf"], x["ga"], x["last"]) for x in f["last"]] == [
        ("OTT", "W", 6, 3, None), ("CHI", "OTL", 1, 2, "SO"),
        ("BOS", "W", 3, 2, "OT"), ("TOR", "W", 4, 2, None),
    ]  # fmt: skip
    assert f["gf_pg"] == 3.5 and f["ga_pg"] == 2.25


def test_h2h_last_three_across_seasons_newest_first(tips, model):
    h = cx.game_context(tip_of(tips), tips, cache_for(), model, {})["h2h"]
    assert [(x["date"], x["home"], x["gh"], x["ga"], x["last"]) for x in h] == [
        ("2026-03-20", "SJS", 2, 0, None), ("2026-03-02", "MTL", 5, 1, None),
        ("2026-01-20", "SJS", 4, 3, "SO"),
    ]  # fmt: skip


def test_h2h_needs_complete_previous_season(tips, model):
    cache = cache_for()
    del cache["teams"]["MTL"]["2026"]
    assert "h2h" not in cx.game_context(tip_of(tips), tips, cache, model, {})


def test_trend_uses_only_tips_locked_before_start_up_to_the_game():
    t = lambda gid, start, elo, locked: {  # noqa: E731
        "game_id": gid, "date": start[:10], "tipoff_utc": start, "locked_at": locked,
        "home": {"team": "MTL", "elo": elo}, "away": {"team": "SJS", "elo": 1450.0},
    }  # fmt: skip
    tips = [
        t("3", "2026-10-15T23:00:00Z", 1520.0, "2026-10-15T08:15:00+00:00"),
        t("1", "2026-10-13T23:00:00Z", 1500.0, "2026-10-13T08:15:00+00:00"),
        t("2", "2026-10-14T23:00:00Z", 1510.0, "2026-10-14T23:30:00+00:00"),  # zamknutý po začiatku
        t("4", "2026-10-17T23:00:00Z", 1530.0, "2026-10-17T08:15:00+00:00"),  # po zápase
    ]
    assert cx.trend(tips, "MTL", "2026-10-15T23:00:00Z") == [["2026-10-13", 1500.0], ["2026-10-15", 1520.0]]


def test_no_context_when_game_missing_from_schedule(tips, model):
    cache = cache_for()
    cache["teams"]["MTL"]["2027"]["games"] = [
        g for g in cache["teams"]["MTL"]["2027"]["games"] if g["id"] != "2026020141"
    ]
    ctx = cx.game_context(tip_of(tips), tips, cache, model, {})
    assert set(ctx) == {"edge", "trend"} and ctx["edge"]["verified"] is False


def test_app_data_main_publishes_context_and_cache(tmp_path, monkeypatch, tips, model):
    """Celý beh ako v predict.yml: tipy z archívu + rozpisy + štatistiky → predictions.json a cache.json."""
    from team_pulse.nhl import app_data as ad

    archive = tmp_path / "archive"
    archive.mkdir()
    day = {t["game_id"]: t for t in tips if t["date"] == "2026-10-20"}
    (archive / "2026-10-20.json").write_text(json.dumps({"games": day}), encoding="utf-8")
    summary = summary_rows()
    for row, team in ((summary["data"][0], "MTL"), (summary["data"][1], "SJS")):
        row["teamId"] = IDS[team]
        row["gamesPlayed"], row["wins"] = (4, 3) if team == "MTL" else (5, 2)
    done = {
        **result("2026020040", "OTT", "SJS", 3, 1),
        "date": "2026-10-19", "tipoff_utc": "2026-10-19T23:00:00Z", "kind": "regular", "last_period": "REG",
    }  # fmt: skip
    monkeypatch.setattr(ad, "fetch_results", lambda *_a, **_k: [done])
    monkeypatch.setattr(ad.inj, "fetch", lambda *_a, **_k: {"injuries": []})
    monkeypatch.setattr(ad.cx, "load_cache", lambda *_a, **_k: {})
    monkeypatch.setattr(
        ad.cx, "fetch_club", lambda team, year, *_a: club(CURRENT if year == 2027 else PREVIOUS, team)
    )
    monkeypatch.setattr(ad.cx, "fetch_summary", lambda *_a, **_k: summary)
    monkeypatch.setattr(ad.cx.time, "sleep", lambda *_a: None)
    out = tmp_path / "out"
    data = ad.main(out=out, archive=archive, now=NOW)
    g = data["days"]["2026-10-20"][0]
    assert g["p_home"] == day["2026020141"]["p_home"]  # tip sa nemení
    assert g["ctx"]["edge"]["verified"] is True and g["ctx"]["venue"] == "Bell Centre"
    assert g["ctx"]["home"]["stats"]["rank"]["gf"] == 32 and g["ctx"]["away"]["stats"]["rank"]["gf"] == 31
    saved = json.loads((out / "predictions.json").read_text(encoding="utf-8"))
    assert saved["days"]["2026-10-20"][0]["ctx"] == g["ctx"] and saved["stats_at"]
    cache = json.loads((out / "cache.json").read_text(encoding="utf-8"))
    assert cache["version"] == cx.CACHE_VERSION and set(cache["teams"]) == {"MTL", "SJS"}


# --- cache rozpisov -------------------------------------------------------------------------------


def result(gid, home, away, gh, ga):
    return {"game_id": gid, "home": home, "away": away, "goals_home": gh, "goals_away": ga}


def test_schedules_reuse_fresh_cache_and_refetch_only_what_changed():
    calls = []

    def fetch(team, year):
        calls.append((team, year))
        return club(CURRENT if year == 2027 else PREVIOUS, team)

    need = {"MTL": {"2026020141"}, "SJS": {"2026020141"}}
    results = [result("2026020040", "OTT", "SJS", 3, 1)]
    cache, n, problems = cx.schedules(need, 2027, results, NOW, cache_for(), fetch, pause=0)
    assert (calls, n, problems) == ([], 0, [])
    # SJS odohral zápas, ktorý v cache nie je dohratý → len SJS tejto sezóny znova
    stale = cache_for()
    for g in stale["teams"]["SJS"]["2027"]["games"]:
        if g["id"] == "2026020040":
            g.update(final=False, gh=None, ga=None)
    cache, n, _ = cx.schedules(need, 2027, results, NOW, stale, fetch, pause=0)
    assert calls == [("SJS", 2027)] and n == 1
    # starý rozpis (viac než 6 h) a chýbajúca minulá sezóna
    old = cache_for(fetched=NOW - timedelta(hours=7))
    del old["teams"]["MTL"]["2026"]
    calls.clear()
    cx.schedules(need, 2027, [], NOW, old, fetch, pause=0)
    assert calls == [("MTL", 2027), ("MTL", 2026), ("SJS", 2027)]


def test_schedules_drop_current_season_when_download_fails():
    def down(team, year):
        raise cx.requests.ConnectionError("bez siete")

    old = cache_for(fetched=NOW - timedelta(hours=7))
    cache, n, problems = cx.schedules({"MTL": {"2026020141"}}, 2027, [], NOW, old, down, pause=0)
    assert n == 0 and "2027" not in cache["teams"]["MTL"] and "2026" in cache["teams"]["MTL"]
    assert problems and problems[0].startswith("rozpis MTL 2027")


def test_load_cache_rejects_other_shapes(monkeypatch):
    class R:
        status_code = 200

        def __init__(self, body):
            self.body = body

        def json(self):
            return self.body

    class S:
        def __init__(self, body):
            self.body = body

        def get(self, *_a, **_k):
            return R(self.body)

    assert cx.load_cache(S({"version": 99, "teams": {}})) == {}
    assert cx.load_cache(S(["zlé"])) == {}
    good = {"version": cx.CACHE_VERSION, "teams": {}}
    assert cx.load_cache(S(good)) == good


# --- štatistiky NHL -------------------------------------------------------------------------------


def summary_rows(n=32, season=20262027):
    rows = []
    for i in range(n):
        rows.append({
            "teamId": 100 + i, "seasonId": season, "gamesPlayed": 5, "wins": 2,
            "goalsForPerGame": 2.0 + i * 0.1, "goalsAgainstPerGame": 4.0 - i * 0.05,
            "powerPlayPct": 0.10 + i * 0.005, "penaltyKillPct": 0.70 + i * 0.005,
            "shotsForPerGame": 25.0 + i * 0.3, "shotsAgainstPerGame": 33.0 - i * 0.2,
        })  # fmt: skip
    return {"data": rows, "total": n}


def test_team_stats_ranks_and_shape_checks():
    raw = summary_rows()
    raw["data"][0]["goalsForPerGame"] = raw["data"][1]["goalsForPerGame"]  # zhoda = rovnaké poradie
    out = cx.team_stats(raw, {131: "MTL", 100: "SJS", 101: "CHI"}, 2027)
    assert out["problems"] == []
    assert out["teams"]["MTL"]["rank"] == {"gf": 1, "ga": 1, "pp": 1, "pk": 1, "sf": 1, "sa": 1}
    assert out["teams"]["SJS"]["rank"]["gf"] == out["teams"]["CHI"]["rank"]["gf"] == 31
    assert out["teams"]["SJS"]["rank"]["ga"] == 32
    bad = summary_rows()
    bad["data"][3]["powerPlayPct"] = 21.5  # percentá namiesto podielu = iný tvar → nič
    assert cx.team_stats(bad, {131: "MTL"}, 2027)["teams"] == {}
    assert cx.team_stats(summary_rows(n=12), {131: "MTL"}, 2027)["teams"] == {}
    assert cx.team_stats(summary_rows(season=20252026), {131: "MTL"}, 2027)["teams"] == {}


def test_check_stats_keeps_only_teams_matching_their_schedule():
    stats = {
        "MTL": {"gp": 4, "w": 2},  # rozpis: 4 zápasy, 3 výhry (aj po predĺžení) → nesedí, vynechá sa
        "SJS": {"gp": 5, "w": 2},
        "CHI": {"gp": 9, "w": 9},  # dnes nehrá → vynechá sa bez problému
    }
    kept, problems = cx.check_stats(stats, cache_for(), 2027)
    assert set(kept) == {"SJS"} and len(problems) == 1 and problems[0].startswith("MTL")


def test_team_ids_from_cached_schedules():
    assert cx.team_ids(cache_for()) == {v: k for k, v in IDS.items()}


def test_team_stats_parse_real_nhl_summary():
    """Skutočná odpoveď štatistík NHL (uložila ju sonda 20. 10. 2026): celá liga, tvar aj poradie."""
    raw = json.loads((FIXTURES / "nhl_team_summary.json").read_text(encoding="utf-8"))
    ids = {r["teamId"]: f"T{r['teamId']}" for r in raw["data"]}
    out = cx.team_stats(raw, ids, 2027)
    assert out["problems"] == [] and out["n"] == 32 and len(out["teams"]) == 32
    for k in cx.STATS:
        ranks = sorted(t["rank"][k] for t in out["teams"].values())
        assert ranks[0] == 1 and ranks[-1] <= 32
    assert all(0 <= t["pp"] <= 1 and 0 <= t["pk"] <= 1 for t in out["teams"].values())
