"""Testy archívu predpovedí a vyhodnotenia ostrej prevádzky."""

import json
import subprocess

import pandas as pd

from team_pulse.archive import fill_results, load_archive, lock_games, missing_games, report, update
from team_pulse.daily import git_commit_if_changed, git_pull

TIP = "2026-10-20 23:30:00+00:00"
META = {"model": "v1", "injuries_timestamp": "2026-10-20T21:00:00Z"}
BACKTEST = {"accuracy": 0.6729, "log_loss": 0.5996, "brier": 0.2068, "test_seasons": "2023/24 – 2025/26"}


def side(team, conf="vysoká"):
    return {
        "team": team,
        "elo": 1500.0,
        "elo_today": 1490.0,
        "pulse": 48.3,
        "tier": "Oslabený",
        "normal_tier": "Stabilný",
        "dropped": False,
        "confidence": conf,
        "layers": {},
        "reasons": [],
        "contributions": {"x": 1.0},
    }


def game(gid="0022600001", p=0.6, tip=TIP, home="DET", away="CHI"):
    return {
        "game_id": gid,
        "date": "2026-10-20",
        "tipoff_utc": tip,
        "neutral": False,
        "home_adv": 43.8,
        "p_home": p,
        "margin_home": 3.0,
        "home": side(home),
        "away": side(away),
        "what_if": [{"a": 1}],
    }


def at(ts):
    return pd.Timestamp(ts, tz="UTC")


def saved(tmp_path, day="2026-10-20"):
    return json.loads((tmp_path / f"{day}.json").read_text(encoding="utf-8"))["games"]


def test_lock_inside_window(tmp_path):
    changed = lock_games({"2026-10-20": [game()]}, META, at("2026-10-20 22:00"), tmp_path)
    rec = saved(tmp_path)["0022600001"]
    assert changed == ["CHI @ DET"]
    assert rec["p_home"] == 0.6 and rec["model"] == "v1"
    assert "what_if" not in rec and "contributions" not in rec["home"]


def test_no_lock_too_early(tmp_path):
    assert lock_games({"2026-10-20": [game()]}, META, at("2026-10-19 23:29"), tmp_path) == []
    assert not (tmp_path / "2026-10-20.json").exists()


def test_lock_a_day_ahead(tmp_path):
    """GitHub plánované behy vynecháva, preto sa ukladá už 24 h vopred a prepisuje až do začiatku."""
    assert lock_games({"2026-10-20": [game()]}, META, at("2026-10-19 23:31"), tmp_path) == ["CHI @ DET"]


def test_no_lock_after_tipoff(tmp_path):
    assert lock_games({"2026-10-20": [game()]}, META, at("2026-10-20 23:30"), tmp_path) == []
    assert lock_games({"2026-10-20": [game()]}, META, at("2026-10-21 01:00"), tmp_path) == []


def test_newer_prediction_before_tipoff_overwrites(tmp_path):
    lock_games({"2026-10-20": [game(p=0.6)]}, META, at("2026-10-20 22:00"), tmp_path)
    lock_games({"2026-10-20": [game(p=0.55)]}, META, at("2026-10-20 23:15"), tmp_path)
    assert saved(tmp_path)["0022600001"]["p_home"] == 0.55


def test_record_frozen_after_tipoff(tmp_path):
    lock_games({"2026-10-20": [game(p=0.6)]}, META, at("2026-10-20 23:15"), tmp_path)
    lock_games({"2026-10-20": [game(p=0.9)]}, META, at("2026-10-20 23:45"), tmp_path)  # už sa hrá
    assert saved(tmp_path)["0022600001"]["p_home"] == 0.6


def test_same_prediction_is_not_a_change(tmp_path):
    lock_games({"2026-10-20": [game()]}, META, at("2026-10-20 22:00"), tmp_path)
    before = (tmp_path / "2026-10-20.json").read_text(encoding="utf-8")
    newer_meta = {**META, "injuries_timestamp": "2026-10-20T22:10:00Z"}
    assert lock_games({"2026-10-20": [game()]}, newer_meta, at("2026-10-20 22:15"), tmp_path) == []
    assert (tmp_path / "2026-10-20.json").read_text(encoding="utf-8") == before  # žiadny commit navyše


def test_late_game_keeps_us_date(tmp_path):
    """Zápas z 20. 10. o 22:00 ET je v UTC už 21. 10.; súbor má dátum zápasu v USA."""
    late = game(gid="0022600002", tip="2026-10-21 02:00:00+00:00", home="LAL", away="GSW")
    lock_games({"2026-10-20": [game(), late]}, META, at("2026-10-21 01:00"), tmp_path)
    assert list(saved(tmp_path)) == ["0022600002"]  # 1. zápas už začal, ten neskorý ešte nie


def test_missing_tipoff_is_skipped(tmp_path):
    assert lock_games({"2026-10-20": [game(tip="")]}, META, at("2026-10-20 22:00"), tmp_path) == []
    assert lock_games({"2026-10-20": [game(tip="NaT")]}, META, at("2026-10-20 22:00"), tmp_path) == []


def history(rows):
    return pd.DataFrame(rows, columns=["game_id", "date", "home", "away", "pts_home", "pts_away"]).assign(
        date=lambda d: pd.to_datetime(d["date"])
    )


def locked_two(tmp_path):
    preds = tmp_path / "pred"
    games = [game(p=0.7), game(gid="0022600003", p=0.4, home="NYK", away="BOS")]
    lock_games({"2026-10-20": games}, META, at("2026-10-20 23:00"), preds)
    return preds


def test_fill_results_by_game_id(tmp_path):
    preds, results = locked_two(tmp_path), tmp_path / "res"
    hist = history(
        [
            ("0022600001", "2026-10-20", "DET", "CHI", 110, 100),
            ("0022600003", "2026-10-20", "NYK", "BOS", 0, 0),  # ešte nedohraný
            ("0022600009", "2026-10-20", "MIA", "ORL", 99, 98),  # nie je v archíve
        ]
    )
    assert fill_results(hist, preds, results) == 1
    assert fill_results(hist, preds, results) == 0  # druhý beh nič nepridá
    stored = json.loads((results / "2026-10-20.json").read_text(encoding="utf-8"))["games"]
    assert stored == {"0022600001": {"pts_home": 110, "pts_away": 100}}


def test_load_archive_and_metrics(tmp_path):
    preds, results = locked_two(tmp_path), tmp_path / "res"
    hist = history(
        [
            ("0022600001", "2026-10-20", "DET", "CHI", 110, 100),  # tip DET 70 % ✓
            ("0022600003", "2026-10-20", "NYK", "BOS", 120, 100),  # tip BOS 60 % ✗
        ]
    )
    fill_results(hist, preds, results)
    df = load_archive(preds, results)
    assert len(df) == 2 and df["home_won"].tolist() == [True, True]
    md = report(df, BACKTEST, missing=[])
    assert "| Presnosť | 50,0 %" in md and "67,3 %" in md
    assert "bez uloženej predpovede: **0**" in md


def test_report_waits_for_results(tmp_path):
    df = load_archive(locked_two(tmp_path), tmp_path / "res")
    md = report(df, BACKTEST)
    assert "čaká na výsledok 2" in md and "Zatiaľ žiadny zápas s výsledkom" in md


def test_report_empty_archive(tmp_path):
    assert "Sezóna začína 20. 10." in report(load_archive(tmp_path / "x", tmp_path / "y"), BACKTEST)


def test_missing_games_listed(tmp_path):
    preds = locked_two(tmp_path)
    hist = history(
        [
            ("0022600001", "2026-10-20", "DET", "CHI", 110, 100),
            ("0022600009", "2026-10-20", "MIA", "ORL", 99, 98),
            ("0022500999", "2026-04-10", "MIA", "ORL", 99, 98),  # pred začiatkom archívu
        ]
    )
    assert missing_games(hist, load_archive(preds, tmp_path / "res")) == ["2026-10-20 ORL @ MIA"]


def test_update_writes_report(tmp_path):
    preds = locked_two(tmp_path)
    out = tmp_path / "reports" / "live.md"
    hist = history([("0022600001", "2026-10-20", "DET", "CHI", 110, 100)])
    assert update(hist, BACKTEST, out, preds, tmp_path / "res") == 1
    first = out.read_text(encoding="utf-8")
    update(hist, BACKTEST, out, preds, tmp_path / "res")
    assert out.read_text(encoding="utf-8") == first  # bez nových dát sa report nemení


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def test_commit_several_paths_and_new_folder(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "state.json").write_text("{}\n")
    assert git_commit_if_changed(
        ["state.json", "archive/results", "live.md"], "prvý", push=False, cwd=tmp_path
    )
    (tmp_path / "archive" / "results").mkdir(parents=True)
    (tmp_path / "archive" / "results" / "2026-10-20.json").write_text("{}\n")
    (tmp_path / "live.md").write_text("# report\n")
    (tmp_path / "other.txt").write_text("nie\n")
    assert git_commit_if_changed(
        ["state.json", "archive/results", "live.md"], "archív", push=False, cwd=tmp_path
    )
    files = git(tmp_path, "show", "--name-only", "--format=", "HEAD").split()
    assert files == ["archive/results/2026-10-20.json", "live.md"]  # other.txt sa necommitol


def test_pull_with_push_from_cloud(tmp_path):
    """Mac commitne stav, medzitým cloud poslal archív: pull --rebase ich spojí bez konfliktu."""
    origin, mac, cloud = tmp_path / "origin.git", tmp_path / "mac", tmp_path / "cloud"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    for repo in (mac, cloud):
        git(tmp_path, "clone", "-q", str(origin), str(repo))
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "T")
    (mac / "state.json").write_text("{}\n")
    git(mac, "add", ".")
    git(mac, "commit", "-qm", "start")
    git(mac, "push", "-q", "origin", "HEAD:main")
    git(cloud, "pull", "-q", "origin", "main")
    (cloud / "archive").mkdir()
    (cloud / "archive" / "a.json").write_text("{}\n")
    git(cloud, "add", ".")
    git(cloud, "commit", "-qm", "archív")
    git(cloud, "push", "-q", "origin", "HEAD:main")
    git(mac, "branch", "-q", "--set-upstream-to=origin/main")
    (mac / "state.json").write_text('{"a": 1}\n')
    (mac / "lokalne.txt").write_text("neuložené\n")
    assert git_commit_if_changed("state.json", "stav", push=True, cwd=mac)
    git_pull(cwd=cloud)
    assert (cloud / "state.json").read_text() == '{"a": 1}\n'
    assert (mac / "archive" / "a.json").exists()


def test_preseason_kept_apart_from_g2(tmp_path):
    preds, results = tmp_path / "pred", tmp_path / "res"
    pre = {**game(gid="0012600001", p=0.8, tip="2026-10-10 23:30:00+00:00"), "kind": "preseason"}
    lock_games({"2026-10-10": [pre]}, META, at("2026-10-10 23:00"), preds)
    reg = {**game(p=0.7), "kind": "regular"}
    lock_games({"2026-10-20": [reg]}, META, at("2026-10-20 23:00"), preds)
    hist = history([("0022600001", "2026-10-20", "DET", "CHI", 110, 100)])
    pre_res = history([("0012600001", "2026-10-10", "DET", "CHI", 90, 100)])  # z rozpisu, nie z histórie
    out = tmp_path / "live.md"
    assert update(hist, BACKTEST, out, preds, results, preseason=pre_res) == 2
    md = out.read_text(encoding="utf-8")
    assert "| Presnosť | 100,0 %" in md  # len základná časť
    assert "## Príprava (skúška archívu, mimo G2)" in md and "presnosť 0,0 %" in md
    assert "bez uloženej predpovede: **0**" in md


def test_only_preseason_in_archive(tmp_path):
    pre = {**game(gid="0012600001"), "kind": "preseason"}
    lock_games({"2026-10-20": [pre]}, META, at("2026-10-20 23:00"), tmp_path / "p")
    md = report(load_archive(tmp_path / "p", tmp_path / "r"), BACKTEST)
    assert "Sezóna začína 20. 10." in md and "Uložené predpovede 1 · s výsledkom 0" in md


def test_results_for_app_add_our_prediction(tmp_path):
    from team_pulse.predict import results_for_app

    lock_games({"2026-10-20": [game(p=0.62)]}, META, at("2026-10-20 23:00"), tmp_path)
    state = {
        "results": [
            {"game_id": "0022600001", "date": "2026-10-20", "home": "DET", "away": "CHI", "box": {}},
            {"game_id": "0022600005", "date": "2026-10-20", "home": "MIA", "away": "ORL", "box": {}},
            {"game_id": "0022600009", "date": "2026-10-19", "home": "LAL", "away": "GSW", "box": {}},
        ]
    }
    assert [r["p_home"] for r in results_for_app(state, tmp_path, tmp_path / "box")] == [None, 0.62, None]


# --- výsledky a štatistiky hráčov z ESPN (cloud) -------------------------------------------


def espn_event(eid, home, away, completed=True, pts=(100, 90), slug="regular-season"):
    return {
        "id": eid,
        "date": "2026-10-20T23:00Z",
        "season": {"year": 2027, "type": 2, "slug": slug},
        "competitions": [
            {
                "neutralSite": False,
                "status": {"type": {"state": "post" if completed else "in", "completed": completed}},
                "competitors": [
                    {"homeAway": "home", "team": {"abbreviation": home}, "score": str(pts[0])},
                    {"homeAway": "away", "team": {"abbreviation": away}, "score": str(pts[1])},
                ],
            }
        ],
    }


def our_schedule():
    return pd.DataFrame(
        {
            "game_id": ["0022600001"],
            "date": pd.to_datetime(["2026-10-20"]),
            "kind": ["regular"],
            "home": ["UTA"],
            "away": ["DEN"],
        }
    )


class Espn:
    def __init__(self, events):
        self.events, self.summaries = events, []

    def scoreboard(self, day):
        return {"events": self.events if day == "20261020" else []}

    def summary(self, espn_id):
        self.summaries.append(espn_id)
        return json.loads(open("tests/fixtures/espn_summary.json", encoding="utf-8").read())


def test_parse_boxscore_from_espn_summary():
    from team_pulse.live.boxscore import parse_boxscore

    box = parse_boxscore(json.loads(open("tests/fixtures/espn_summary.json", encoding="utf-8").read()))
    assert set(box) == {"UTA", "DEN"}  # ESPN „UTAH“ → UTA
    assert box["UTA"][0] == {
        "player": "Jaren Jackson Jr.",
        "min": 18,
        "pts": 11,
        "reb": 6,
        "ast": 1,
        "blk": 2,
        "stl": 0,
    }
    assert [p["player"] for p in box["UTA"]] == [
        "Jaren Jackson Jr.",
        "Lauri Markkanen",
    ]  # bez DNP, podľa minút
    assert box["DEN"][0]["player"] == "Nikola Jokić" and box["DEN"][0]["reb"] == 9


def test_live_results_saved_once_per_game(tmp_path):
    from team_pulse.archive import update_live_results

    espn = Espn(
        [
            espn_event("1", "UTAH", "DEN"),  # dohraný, v našom rozpise
            espn_event("2", "BOS", "NY", completed=False),  # ešte sa hrá
            espn_event("3", "PHX", "XYZ"),  # klub mimo NBA
            espn_event("4", "MIA", "ORL", slug="preseason"),  # dohraný, nie je v rozpise
        ]
    )
    today = pd.Timestamp("2026-10-21")
    added = update_live_results(our_schedule(), today, espn.scoreboard, espn.summary, tmp_path)
    assert added == ["DEN @ UTA", "ORL @ MIA"] and espn.summaries == ["1", "4"]
    games = json.loads((tmp_path / "2026-10-20.json").read_text(encoding="utf-8"))["games"]
    assert games["0022600001"]["kind"] == "regular" and games["0022600001"]["pts_home"] == 100
    assert games["0022600001"]["box"]["UTA"][0]["player"] == "Jaren Jackson Jr."
    assert games["espn-4"]["kind"] == "preseason"

    assert update_live_results(our_schedule(), today, espn.scoreboard, espn.summary, tmp_path) == []
    assert espn.summaries == ["1", "4"]  # box score sa druhýkrát nesťahuje

    espn.events[0] = espn_event("1", "UTAH", "DEN", pts=(101, 90))  # opravené skóre
    assert update_live_results(our_schedule(), today, espn.scoreboard, espn.summary, tmp_path) == [
        "DEN @ UTA"
    ]


def test_live_results_survive_box_score_error(tmp_path):
    from team_pulse.archive import update_live_results

    espn = Espn([espn_event("1", "UTAH", "DEN")])

    def broken(_):
        raise ConnectionError("ESPN nedostupné")

    today = pd.Timestamp("2026-10-21")
    assert update_live_results(our_schedule(), today, espn.scoreboard, broken, tmp_path) == ["DEN @ UTA"]
    assert saved(tmp_path)["0022600001"]["box"] == {}  # skóre je, štatistiky sa skúsia znova
    assert update_live_results(our_schedule(), today, espn.scoreboard, espn.summary, tmp_path) == [
        "DEN @ UTA"
    ]
    assert saved(tmp_path)["0022600001"]["box"]


def test_results_for_app_merge_cloud_and_mac(tmp_path):
    from team_pulse.archive import update_live_results
    from team_pulse.predict import results_for_app

    box_dir = tmp_path / "box"
    espn = Espn([espn_event("1", "UTAH", "DEN"), espn_event("4", "MIA", "ORL", slug="preseason")])
    update_live_results(our_schedule(), pd.Timestamp("2026-10-21"), espn.scoreboard, espn.summary, box_dir)
    mac_box = {
        "UTA": [{"player": "Mac", "min": 30, "pts": 1, "reb": 1, "ast": 1, "blk": 1, "stl": 1}],
        "DEN": [],
    }
    state = {
        "results": [
            {"game_id": "0022600001", "date": "2026-10-20", "kind": "regular", "home": "UTA", "away": "DEN",
             "pts_home": 100, "pts_away": 90, "box": mac_box},
            {"game_id": "0012600001", "date": "2026-10-16", "kind": "preseason", "home": "LAL", "away": "GSW",
             "pts_home": 99, "pts_away": 98, "box": {}},
            {"game_id": "0012600002", "date": "2026-10-15", "kind": "preseason", "home": "LAL", "away": "GSW",
             "pts_home": 99, "pts_away": 98, "box": {}},
            {"game_id": "0012600003", "date": "2026-10-14", "kind": "preseason", "home": "LAL", "away": "GSW",
             "pts_home": 99, "pts_away": 98, "box": {}},
        ]
    }  # fmt: skip
    res = results_for_app(state, tmp_path / "pred", box_dir)
    assert [r["game_id"] for r in res] == [
        "0012600002",
        "0012600001",
        "0022600001",
        "espn-4",
    ]  # posledné 3 dni
    by_id = {r["game_id"]: r for r in res}
    assert by_id["0022600001"]["box"] == mac_box  # Mac má prednosť
    assert by_id["espn-4"]["box"]["UTA"]  # príprava len z ESPN, aj so štatistikami
