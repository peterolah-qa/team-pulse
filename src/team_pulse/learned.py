"""Naučené váhy: logistická regresia nad Elo (vrstva A) a únavou (vrstva C).

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

from team_pulse.backtest import calibration, metrics
from team_pulse.elo import EloParams, run
from team_pulse.schedule import FEATURES, add_features

GAMES = Path("data/raw/games.parquet")
REPORT = Path("reports/learned.md")
TRAIN = (2004, 2023)  # 2001–2003 = rozbeh Ela
TEST = (2024, 2026)
ELO_PARAMS = EloParams(hca=70)

BASE_COLS = ["elo_diff", "home"]
# výška sa týka len hostí (domáci sú na svoju halu zvyknutí)
FATIGUE_COLS = [f"home_{f}" for f in FEATURES if f != "altitude"] + [f"away_{f}" for f in FEATURES]


def build_dataset(games: pd.DataFrame) -> pd.DataFrame:
    """Jeden riadok na zápas: vstupy modelu (len dáta pred zápasom) + cieľ home_won."""
    teams = set(games["home"]) | set(games["away"])
    elo = run(games, ELO_PARAMS, initial={t: ELO_PARAMS.mean for t in teams})
    df = add_features(elo)
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


def evaluate(games: pd.DataFrame) -> dict[str, object]:
    ds = build_dataset(games)
    train, test = split(ds)
    y = test["home_won"]

    m_base = fit(train, BASE_COLS)
    m_full = fit(train, BASE_COLS + FATIGUE_COLS)
    p_base = pd.Series(m_base.predict_proba(test[BASE_COLS])[:, 1], index=test.index)
    p_full = pd.Series(m_full.predict_proba(test[BASE_COLS + FATIGUE_COLS])[:, 1], index=test.index)

    rows = [
        {"model": "A: Elo (HCA 70)", **metrics(test["elo_prob"], y)},
        {"model": "A kalibrované (naučené Elo + domáci)", **metrics(p_base, y)},
        {"model": "A + C (naučené Elo + únava)", **metrics(p_full, y)},
    ]
    return {
        "summary": pd.DataFrame(rows),
        "weights": elo_equivalents(m_full, BASE_COLS + FATIGUE_COLS),
        "cal_before": calibration(test["elo_prob"], y.astype(bool)),
        "cal_after": calibration(p_full, y.astype(bool)),
        "n_train": len(train),
        "n_test": len(test),
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
        f"# Naučené váhy – vrstva A + C\n\n"
        f"Tréning: sezóny {_season(TRAIN[0])} – {_season(TRAIN[1])} ({r['n_train']} zápasov). "
        f"Test: {_season(TEST[0])} – {_season(TEST[1])} "
        f"({r['n_test']} zápasov), ktoré model pri učení nevidel.\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{s.to_markdown(index=False)}\n\n"
        f"## Naučené váhy v Elo bodoch\n\n"
        f"Kladné = pomáha domácim, záporné = pomáha hosťom. `home_*` sa týka domácich, `away_*` hostí.\n"
        f"Príklad: `away_b2b = +20` znamená, že back-to-back hostí dá domácim výhodu 20 Elo.\n\n"
        f"{w.to_markdown()}\n\n"
        f"## Kalibrácia pred (čisté Elo)\n\n{_fmt_cal(r['cal_before'])}\n\n"
        f"## Kalibrácia po (A + C)\n\n{_fmt_cal(r['cal_after'])}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> None:
    r = evaluate(pd.read_parquet(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<38} presnosť {row.accuracy:6.1%}   "
            f"log loss {row.log_loss:.4f}   Brier {row.brier:.4f}"
        )
    print("\nNaučené váhy (Elo body):")
    print(r["weights"].round(1).to_string())
    print(f"\nReport: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
