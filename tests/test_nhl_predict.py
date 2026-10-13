"""Živé NHL tipy: dni v ET, sezóna, rating pred zápasom, únava v dôvodoch a výstup (bez siete)."""

import json
from datetime import UTC, date, datetime

import pandas as pd
import pytest

from team_pulse.model_store import StoredModel
from team_pulse.nhl import fetch_games as fg
from team_pulse.nhl import predict as pr
from team_pulse.nhl.elo import HockeyEloParams
from team_pulse.nhl.learned import FATIGUE_COLS

P = HockeyEloParams(k=6.0, hca=30.0, carryover=0.8)


def model(**weights) -> StoredModel:
    """Model so známymi váhami: 1 jednotka elo_diff (100 Elo) = 0,5 logitu, domáci +0,1."""
    features = ["elo_diff", "home", *FATIGUE_COLS]
    coef = [0.5, 0.1] + [weights.get(f, 0.0) for f in FATIGUE_COLS]
    elo_w = {f: c / 0.005 for f, c in zip(features[1:], coef[1:], strict=True)}
    return StoredModel(version="nhl-test", features=features, coef=coef, intercept=0.0, elo_params=P.__dict__,
                       train_seasons=[2009, 2026], n_games=1, created="2026-10-13", test_metrics={},
                       elo_weights=elo_w)  # fmt: skip


def history():
    """Minulá sezóna: BOS vyhral všetko, TOR prehral všetko."""
    rows = [(i, 2026, "R", f"2026-03-{i:02d}", "BOS" if i % 2 else "MTL", "MTL" if i % 2 else "BOS")
            for i in range(1, 11)]  # fmt: skip
    df = pd.DataFrame(rows, columns=["game_id", "season", "game_type", "date", "home_abbr", "away_abbr"])
    df["goals_home"] = [4 if h == "BOS" else 1 for h in df["home_abbr"]]
    df["goals_away"] = [1 if h == "BOS" else 4 for h in df["home_abbr"]]
    df["start_utc"] = df["date"] + "T23:00:00Z"
    df["state"], df["last_period"], df["neutral"] = "OFF", "REG", False
    return fg.finished_games(df[fg.COLUMNS])


def game(gid, day, home, away, state="FUT", gh=None, ga=None, season=2027):
    return {"game_id": gid, "season": season, "game_type": "R", "date": day, "start_utc": f"{day}T23:00:00Z",
            "home_abbr": home, "away_abbr": away, "goals_home": gh, "goals_away": ga, "state": state,
            "last_period": "REG" if state == "OFF" else None, "neutral": False}  # fmt: skip


def current():
    return pd.DataFrame(
        [
            game(101, "2026-10-12", "TOR", "MTL", "OFF", 2, 3),  # včera: MTL hral
            game(102, "2026-10-13", "BOS", "MTL", "FUT"),  # dnes: MTL back-to-back
            game(103, "2026-10-14", "TOR", "BOS", "FUT"),  # zajtra: BOS back-to-back
            game(104, "2026-10-20", "MTL", "TOR", "FUT"),  # mimo okna 3 dní
        ],
        columns=fg.COLUMNS,
    )


def test_et_day_and_season():
    assert pr.today_et(datetime(2026, 10, 14, 3, 0, tzinfo=UTC)) == date(2026, 10, 13)  # 23:00 ET
    assert pr.season_of(date(2026, 10, 13)) == 2027 and pr.season_of(date(2027, 4, 10)) == 2027
    assert pr.season_of(date(2026, 6, 20)) == 2026


def test_upcoming_window_and_relocated_clubs():
    cur = current()
    cur.loc[1, "home_abbr"] = "ARI"
    up = pr.upcoming_games(cur, date(2026, 10, 13), 3)
    assert up["game_id"].tolist() == [102, 103] and up.loc[0, "home"] == "UTA"


def test_rating_now_resets_after_summer():
    assert pr.rating_now((1600.0, 2026), 2027, P) == pytest.approx(0.8 * 1600 + 0.2 * 1505)
    assert pr.rating_now((1600.0, 2027), 2027, P) == 1600.0
    assert pr.rating_now(None, 2027, P) == P.new_team


def test_predict_favorite_back_to_back_and_window():
    m = model(away_b2b=0.2, home_b2b=-0.2)
    games = pr.predict(history(), current(), m, date(2026, 10, 13), 3)
    assert [g["game_id"] for g in games] == ["102", "103"]
    bos_home = games[0]
    assert bos_home["tip"] == "BOS" and bos_home["p_home"] > 0.6  # silný BOS doma, MTL po včerajšku
    assert bos_home["away"]["reasons"] == {"back-to-back": -40.0}
    tor_bos = games[1]
    assert tor_bos["away"]["team"] == "BOS" and tor_bos["away"]["reasons"] == {"back-to-back": -40.0}
    assert tor_bos["home"]["elo"] < bos_home["home"]["elo"]
    assert all(0 < g["p_home"] < 1 for g in games)


def test_predict_without_upcoming_games():
    assert pr.predict(history(), current(), model(), date(2026, 11, 1), 3) == []


def test_json_and_terminal_line():
    m = model(away_b2b=0.2)
    games = pr.predict(history(), current(), m, date(2026, 10, 13), 3)
    data = pr.to_json(games, m, datetime(2026, 10, 13, 12, tzinfo=UTC))
    assert list(data["days"]) == ["2026-10-13", "2026-10-14"] and data["sport"] == "nhl"
    json.dumps(data)  # dá sa uložiť
    text = pr.line(games[0])
    assert text.startswith("14. 10. 01:00  MTL @ BOS  tip BOS") and "MTL: back-to-back -40" in text


def test_main_writes_predictions(tmp_path, monkeypatch, capsys):
    hist_path, model_path, out = tmp_path / "games.parquet", tmp_path / "m.json", tmp_path / "nhl" / "p.json"
    history().to_parquet(hist_path, index=False)
    model(away_b2b=0.2).save(model_path)
    monkeypatch.setattr(pr, "fetch_season", lambda session, year: current())
    monkeypatch.setattr(pr, "today_et", lambda now=None: date(2026, 10, 13))
    data = pr.main(3, out, hist_path, model_path)
    assert json.loads(out.read_text(encoding="utf-8")) == data
    printed = capsys.readouterr().out
    assert "Sezóna 2026/27: dohratých 1 zápasov" in printed and "tip BOS" in printed
