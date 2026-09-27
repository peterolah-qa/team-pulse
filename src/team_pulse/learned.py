"""Naučené váhy: logistická regresia nad Elo (A), hráčmi (B) a únavou (C).

Namiesto ručne odhadnutých penalizácií (napr. back-to-back = −40 Elo) sa model
naučí váhy z histórie. Tréning na starších sezónach, test na novších, ktoré model nevidel.

Spustenie:  uv run python -m team_pulse.learned
Výstup:     reports/learned.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

from team_pulse import players as layer_b
from team_pulse.backtest import calibration, metrics
from team_pulse.elo import EloParams, run
from team_pulse.schedule import FEATURES, add_features

GAMES = Path("data/raw/games.parquet")
PLAYERS = Path("data/raw/players.parquet")
REPORT = Path("reports/learned.md")
TRAIN = (2004, 2023)  # 2001–2003 = rozbeh Ela
TEST = (2024, 2026)
ELO_PARAMS = EloParams(hca=70)

BASE_COLS = ["elo_diff", "home"]
# výška sa týka len hostí (domáci sú na svoju halu zvyknutí)
FATIGUE_COLS = [f"home_{f}" for f in FEATURES if f != "altitude"] + [f"away_{f}" for f in FEATURES]
PLAYER_COLS = ["home_missing", "away_missing"]  # v bodoch PIE × podiel minút
# sila súpisky: rozdiel domáci − hostia a jeho váha na začiatku sezóny (kým Elo „nevie“ o prestupoch)
ROSTER_COLS = ["strength_diff"]
EARLY_GAMES = 20


def build_dataset(games: pd.DataFrame, players: pd.DataFrame | None = None) -> pd.DataFrame:
    """Jeden riadok na zápas: vstupy modelu (len dáta pred zápasom) + cieľ home_won."""
    teams = set(games["home"]) | set(games["away"])
    elo = run(games, ELO_PARAMS, initial={t: ELO_PARAMS.mean for t in teams})
    df = add_features(elo)
    if players is not None:
        df = layer_b.add_features(df, players)
    neutral = df["neutral"].astype(bool) if "neutral" in df else pd.Series(False, index=df.index)
    out = pd.DataFrame(
        {
            "season": df["season"],
            "date": df["date"],
            "elo_prob": df["prob_home"],
            "elo_diff": (df["elo_home_pre"] - df["elo_away_pre"]) / 100,  # v stovkách Elo
            "home": (~neutral).astype(int),
            "home_won": (df["pts_home"] > df["pts_away"]).astype(int),
        }
    )
    for c in FATIGUE_COLS:
        out[c] = df[c] / 1000 if c.endswith("_km") else df[c]
    if players is not None:
        for c in PLAYER_COLS:
            out[c] = df[c] * 100
        diff = (df["home_strength"] - df["away_strength"]) * 100
        played = (df["home_games_played"] + df["away_games_played"]) / 2
        early = (1 - played / EARLY_GAMES).clip(lower=0)
        out["strength_diff"] = diff
        out["strength_diff_early"] = diff * early
        out["has_players"] = df["game_id"].isin(set(players["game_id"])).to_numpy()
    return out


def split(ds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = ds[ds["season"].between(*TRAIN)]
    test = ds[ds["season"].between(*TEST)]
    return train, test


def fit(train: pd.DataFrame, cols: list[str]) -> LogisticRegression:
    model = LogisticRegression(C=1e6, max_iter=5000)
    model.fit(train[cols], train["home_won"])
    return model


def elo_equivalents(model: LogisticRegression, cols: list[str]) -> pd.Series:
    """Prepočet váh na Elo body: koľko Elo „stojí“ jednotka príznaku."""
    coef = pd.Series(model.coef_[0], index=cols)
    per_elo = coef["elo_diff"] / 100
    return (coef / per_elo).drop("elo_diff")


def predict(model: LogisticRegression, df: pd.DataFrame, cols: list[str]) -> pd.Series:
    return pd.Series(model.predict_proba(df[cols])[:, 1], index=df.index)


def evaluate(games: pd.DataFrame, players: pd.DataFrame | None = None) -> dict[str, object]:
    ds = build_dataset(games, players)
    train, test = split(ds)
    y = test["home_won"]

    variants = {
        "A kalibrované (naučené Elo + domáci)": BASE_COLS,
        "A + C (naučené Elo + únava)": BASE_COLS + FATIGUE_COLS,
    }
    if players is not None:
        variants["A + B + C (+ chýbajúci hráči)"] = BASE_COLS + PLAYER_COLS + FATIGUE_COLS
        variants["A + B + C + sila súpisky"] = BASE_COLS + PLAYER_COLS + ROSTER_COLS + FATIGUE_COLS

    rows = [{"model": "A: Elo (HCA 70)", **metrics(test["elo_prob"], y)}]
    models, preds = {}, {}
    for name, cols in variants.items():
        models[name] = fit(train, cols)
        preds[name] = predict(models[name], test, cols)
        rows.append({"model": name, **metrics(preds[name], y)})

    best = list(variants)[-1]
    return {
        "summary": pd.DataFrame(rows),
        "weights": elo_equivalents(models[best], variants[best]),
        "best": best,
        "cal_before": calibration(test["elo_prob"], y.astype(bool)),
        "cal_after": calibration(preds[best], y.astype(bool)),
        "n_train": len(train),
        "n_test": len(test),
        "player_coverage": float(ds["has_players"].mean()) if "has_players" in ds else None,
    }


def _fmt_cal(cal: pd.DataFrame) -> str:
    c = cal.copy()
    c["band"] = c["band"].astype(str)
    c["predpoved"] = (c["predpoved"] * 100).map("{:.1f} %".format)
    c["skutocnost"] = (c["skutocnost"] * 100).map("{:.1f} %".format)
    return c.to_markdown(index=False)


def _season(end_year: int) -> str:
    return f"{end_year - 1}/{str(end_year)[-2:]}"


def to_markdown(r: dict[str, object]) -> str:
    s = r["summary"].copy()
    s["n"] = s["n"].astype(int)
    s["accuracy"] = (s["accuracy"] * 100).map("{:.1f} %".format)
    s["log_loss"] = s["log_loss"].map("{:.4f}".format)
    s["brier"] = s["brier"].map("{:.4f}".format)
    w = r["weights"].round(1).rename("Elo").to_frame()
    return (
        f"# Naučené váhy\n\n"
        f"Tréning: sezóny {_season(TRAIN[0])} – {_season(TRAIN[1])} ({r['n_train']} zápasov). "
        f"Test: {_season(TEST[0])} – {_season(TEST[1])} "
        f"({r['n_test']} zápasov), ktoré model pri učení nevidel.\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{s.to_markdown(index=False)}\n\n"
        f"## Naučené váhy v Elo bodoch – {r['best']}\n\n"
        f"Kladné = pomáha domácim, záporné = pomáha hosťom. `home_*` sa týka domácich, `away_*` hostí.\n"
        f"Príklad: `away_b2b = +20` znamená, že back-to-back hostí dá domácim výhodu 20 Elo.\n"
        f"`*_missing` = Elo za 1 bod PIE chýbajúcej kvality (hviezda na 36 min. ≈ 5–7 bodov).\n\n"
        f"{w.to_markdown()}\n\n"
        f"## Kalibrácia pred (čisté Elo)\n\n{_fmt_cal(r['cal_before'])}\n\n"
        f"## Kalibrácia po ({r['best']})\n\n{_fmt_cal(r['cal_after'])}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> None:
    players = pd.read_parquet(PLAYERS) if PLAYERS.exists() else None
    r = evaluate(pd.read_parquet(path), players)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<38} presnosť {row.accuracy:6.1%}   "
            f"log loss {row.log_loss:.4f}   Brier {row.brier:.4f}"
        )
    print("\nNaučené váhy (Elo body):")
    print(r["weights"].round(1).to_string())
    if r["player_coverage"] is not None:
        print(f"\nZápasy s box score hráčov: {r['player_coverage']:.1%}")
    print(f"\nReport: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
