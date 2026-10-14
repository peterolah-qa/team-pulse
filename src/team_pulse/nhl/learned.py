"""Návrh vrstvy C pre NHL: únava z rozpisu nad hokejovým Elo (logistická regresia).

Rovnaký postup ako pri NBA (team_pulse.learned): váhy sa naučia na tréningových sezónach,
hodnotí sa základná časť testovacích sezón 2023/24 – 2025/26, ktoré model nevidel.
Vrstva sa prijme len vtedy, keď zlepší log loss aspoň o 0,0005 oproti Elo (čistému aj kalibrovanému).
O zaradení do modelu rozhoduje Peter.

Spustenie:  uv run python -m team_pulse.nhl.learned
Výstup:     reports/nhl_learned.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

from team_pulse.backtest import calibration, metrics
from team_pulse.nhl.backtest import TEST, THRESHOLD, TRAIN_LAST, split
from team_pulse.nhl.elo import HockeyEloParams, run
from team_pulse.nhl.fetch_games import OUT as GAMES
from team_pulse.nhl.fetch_games import season_label
from team_pulse.nhl.schedule import FEATURES, add_features

REPORT = Path("reports/nhl_learned.md")
ELO = HockeyEloParams(k=6.0, hca=30.0, carryover=0.8)  # brána G0-NHL, reports/nhl_backtest.md
BASE_COLS = ["elo_diff", "home"]
# domáci nie sú nikdy na výjazde (home_road = 0), preto ho model nedostane
FATIGUE_COLS = [f"{side}_{f}" for side in ("home", "away") for f in FEATURES if (side, f) != ("home", "road")]


def build_dataset(games: pd.DataFrame) -> pd.DataFrame:
    """Jeden riadok na zápas: vstupy modelu (len to, čo bolo známe pred zápasom) a cieľ home_won."""
    elo = run(games, ELO)
    df = add_features(elo)
    out = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "season": df["season"],
            "game_type": df["game_type"],
            "elo_prob": df["prob_home"],
            "elo_diff": (df["elo_home_pre"] - df["elo_away_pre"]) / 100,  # v stovkách Elo
            "home": (~df["neutral"].astype(bool)).astype(int),
            "home_won": (df["goals_home"] > df["goals_away"]).astype(int),
        }
    )
    for c in FATIGUE_COLS:
        out[c] = df[c]
    return out


def fit(train: pd.DataFrame, cols: list[str]) -> LogisticRegression:
    model = LogisticRegression(C=1e6, max_iter=5000)
    model.fit(train[cols], train["home_won"])
    return model


def predict(model: LogisticRegression, df: pd.DataFrame, cols: list[str]) -> pd.Series:
    return pd.Series(model.predict_proba(df[cols])[:, 1], index=df.index)


def elo_equivalents(model: LogisticRegression, cols: list[str]) -> pd.Series:
    """Váhy prepočítané na Elo body: koľko Elo „stojí“ jednotka príznaku."""
    coef = pd.Series(model.coef_[0], index=cols)
    return (coef / (coef["elo_diff"] / 100)).drop("elo_diff")


def evaluate(games: pd.DataFrame) -> dict[str, object]:
    ds = build_dataset(games)
    train_mask, test_mask = split(ds)
    train, test = ds[train_mask], ds[test_mask]
    y = test["home_won"]
    variants = {"A kalibrované (Elo + domáci)": BASE_COLS, "A + C (+ únava)": BASE_COLS + FATIGUE_COLS}
    rows = [{"model": "A: Elo", **metrics(test["elo_prob"], y)}]
    models, preds = {}, {}
    for name, cols in variants.items():
        models[name] = fit(train, cols)
        preds[name] = predict(models[name], test, cols)
        rows.append({"model": name, **metrics(preds[name], y)})
    summary = pd.DataFrame(rows)
    ll = summary.set_index("model")["log_loss"]
    best_a = float(min(ll["A: Elo"], ll["A kalibrované (Elo + domáci)"]))
    with_c = float(ll["A + C (+ únava)"])
    share = {
        f: float(ds.loc[test_mask, [f"home_{f}", f"away_{f}"]].gt(0).mean().mean())
        for f in ("b2b", "three_in4")
    }
    return {
        "summary": summary,
        "weights": elo_equivalents(models["A + C (+ únava)"], variants["A + C (+ únava)"]),
        "decision": {"without": best_a, "with": with_c, "accepted": with_c <= best_a - THRESHOLD},
        "cal_before": calibration(test["elo_prob"], y.astype(bool)),
        "cal_after": calibration(preds["A + C (+ únava)"], y.astype(bool)),
        "n_train": len(train),
        "n_test": len(test),
        "share": share,
    }


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float) -> str:
    return f"{x:.4f}".replace(".", ",")


def _cal(cal: pd.DataFrame) -> str:
    c = cal.copy()
    c["band"] = c["band"].astype(str)
    c["predpoved"] = c["predpoved"].map(_pct)
    c["skutocnost"] = c["skutocnost"].map(_pct)
    c.columns = ["pásmo", "zápasy", "predpoveď", "skutočnosť"]
    return c.to_markdown(index=False)


LABELS = {
    "home": "domáca výhoda (len mimo neutrálneho ľadu)",
    "home_rest": "domáci: dni oddychu",
    "home_b2b": "domáci: back-to-back",
    "home_three_in4": "domáci: 3. zápas za 4 dni",
    "home_tz_east": "domáci: posun na východ (h)",
    "away_rest": "hostia: dni oddychu",
    "away_b2b": "hostia: back-to-back",
    "away_three_in4": "hostia: 3. zápas za 4 dni",
    "away_tz_east": "hostia: posun na východ (h)",
    "away_road": "hostia: poradie zápasu na výjazde",
}


def to_markdown(r: dict[str, object]) -> str:
    s = r["summary"].copy()
    s["n"] = s["n"].astype(int)
    s["accuracy"] = s["accuracy"].map(_pct)
    s["log_loss"] = s["log_loss"].map(_num)
    s["brier"] = s["brier"].map(_num)
    s.columns = ["model", "zápasy", "presnosť", "log loss", "Brier"]
    w = r["weights"]
    weights = pd.DataFrame({"príznak": [LABELS.get(c, c) for c in w.index], "Elo": w.round(1).to_numpy()})
    d = r["decision"]
    verdict = "✅ zlepšuje, navrhujem pridať" if d["accepted"] else "❌ nezlepšuje dosť, nepridávať"
    return (
        "# NHL – návrh vrstvy C (únava z rozpisu)\n\n"
        f"Elo z brány G0-NHL (K {ELO.k:g}, domáca výhoda {ELO.hca:g}, prenos {ELO.carryover:g}). "
        f"Tréning do {season_label(TRAIN_LAST)} ({r['n_train']} zápasov), test {season_label(TEST[0])} – "
        f"{season_label(TEST[1])} ({r['n_test']} zápasov základnej časti, model ich nevidel).\n\n"
        f"## Rozhodnutie: {verdict}\n\n"
        f"Kritérium: log loss s únavou o ≥ {_num(THRESHOLD)} nižší než bez nej.\n\n"
        f"Bez únavy {_num(d['without'])} · s únavou {_num(d['with'])} · "
        f"rozdiel {_num(d['without'] - d['with'])}\n\n"
        f"## Porovnanie na testovacích sezónach\n\n{s.to_markdown(index=False)}\n\n"
        "## Naučené váhy v Elo bodoch\n\n"
        "Kladné = pomáha domácim, záporné = pomáha hosťom.\n\n"
        f"{weights.to_markdown(index=False)}\n\n"
        f"Back-to-back má v teste {_pct(r['share']['b2b'])} klubov v zápase, "
        f"3. zápas za 4 dni {_pct(r['share']['three_in4'])}.\n\n"
        f"## Kalibrácia pred (čisté Elo)\n\n{_cal(r['cal_before'])}\n\n"
        f"## Kalibrácia po (A + C)\n\n{_cal(r['cal_after'])}\n"
    )


def main(path: Path = GAMES, out: Path = REPORT) -> dict[str, object]:
    r = evaluate(pd.read_parquet(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    for row in r["summary"].itertuples(index=False):
        print(
            f"{row.model:<30} presnosť {row.accuracy:6.1%}   log loss {row.log_loss:.4f}   "
            f"Brier {row.brier:.4f}"
        )
    print("\nNaučené váhy (Elo body):")
    print(r["weights"].round(1).to_string())
    d = r["decision"]
    print(
        f"\nVrstva C: {'ZLEPŠUJE' if d['accepted'] else 'NEZLEPŠUJE'} ({d['without']:.4f} → {d['with']:.4f})"
    )
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=Path, default=GAMES)
    a = ap.parse_args()
    main(a.games)
