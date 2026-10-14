"""Backtest F1 a brána G0-F1 (kritériá: docs/gate-f1-G0.md, stanovené 14. 10. 2026 pred meraním).

Rozdelenie: tréning 2014 – 2025 (2014 rozbeh Ela), test 2026 kolá 1 – 17.
Ladenie Ela len na tréningu: váhy z 2015 – 2022, výber parametrov podľa 2023 – 2025,
potom váhy znova z 2015 – 2025 a jedno meranie na teste.

Spustenie:  uv run python -m team_pulse.f1.backtest
Výstup:     reports/f1_backtest.md
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from team_pulse.f1.fetch import OUT as RESULTS
from team_pulse.f1.fetch import SPRINTS
from team_pulse.f1.model import (
    FEATURES,
    EloParams,
    elo_ratings,
    features,
    fit_logit,
    podium,
    quali_slot,
    softmax_by_race,
    win_table,
)

REPORT = Path("reports/f1_backtest.md")
BURN_IN = 2014  # rozbeh Ela, nehodnotí sa
TRAIN = (2014, 2025)
FIT_EARLY = (2015, 2022)  # váhy pri ladení parametrov Ela
VALID = (2023, 2025)  # výber parametrov Ela (stále tréning)
TEST_SEASON, TEST_ROUNDS = 2026, (1, 17)
THRESHOLD = 0.0005
GRID = {"k_driver": [8, 16, 24, 32, 48], "k_team": [8, 16, 24, 32, 48], "carry": [0.3, 0.5, 0.7, 0.9]}


def championship_rank(res: pd.DataFrame, sprints: pd.DataFrame) -> pd.Series:
    """Poradie jazdca v šampionáte pred pretekmi (body z pretekov aj šprintov skorších kôl).
    Pred 1. kolom poradie z konca minulej sezóny, jazdci bez minulej sezóny na konci. Bez minulej
    sezóny v dátach (1. kolo prvej sezóny) chýba."""
    pts = pd.concat(
        [res[["season", "round", "driver", "points"]], sprints[["season", "round", "driver", "points"]]]
    )
    wins = res.assign(win=(res["position"] == 1).astype(int))[["season", "round", "driver", "win"]]
    ranks = pd.Series(np.nan, index=res.index)
    seasons = sorted(res["season"].unique())
    for s in seasons:
        rows = res[res["season"] == s]
        for rnd in sorted(rows["round"].unique()):
            m = (res["season"] == s) & (res["round"] == rnd)
            if rnd == rows["round"].min():
                if s - 1 not in seasons:
                    continue
                before_p, before_w = pts[pts["season"] == s - 1], wins[wins["season"] == s - 1]
            else:
                before_p = pts[(pts["season"] == s) & (pts["round"] < rnd)]
                before_w = wins[(wins["season"] == s) & (wins["round"] < rnd)]
            table = (
                pd.DataFrame({"p": before_p.groupby("driver")["points"].sum()})
                .join(before_w.groupby("driver")["win"].sum().rename("w"), how="outer")
                .fillna(0)
            )
            table = table.sort_values(["p", "w"], ascending=False)
            rank = {d: i + 1 for i, d in enumerate(table.index)}
            ranks[m] = res.loc[m, "driver"].map(lambda d: rank.get(d, len(rank) + 1)).to_numpy()  # noqa: B023
    return ranks


@dataclass
class Scores:
    races: int
    log_loss: float
    accuracy: float
    podium_brier: float


def score(df: pd.DataFrame, p: np.ndarray) -> Scores:
    rid = (df["season"] * 100 + df["round"]).to_numpy()
    won = (df["position"] == 1).to_numpy()
    top3 = (df["position"] <= 3).to_numpy()
    ll, hit, brier = [], [], []
    for r in np.unique(rid):
        m = rid == r
        pm = p[m]
        ll.append(-np.log(max(pm[won[m]].sum(), 1e-12)))
        hit.append(bool(won[m][np.argmax(pm)]))
        brier.append(float(((podium(pm) - top3[m]) ** 2).mean()))
    return Scores(len(ll), float(np.mean(ll)), float(np.mean(hit)), float(np.mean(brier)))


def baseline_probs(df: pd.DataFrame, slot_table: np.ndarray, rank_table: np.ndarray) -> dict[str, np.ndarray]:
    rid = (df["season"] * 100 + df["round"]).to_numpy()
    slot = quali_slot(df).clip(upper=len(slot_table) - 1).to_numpy()
    rank = df["champ_rank"].clip(upper=len(rank_table) - 1).to_numpy().astype(int)
    return {
        "kvalifikácia": softmax_by_race(np.log(slot_table[slot]), rid),
        "šampionát": softmax_by_race(np.log(rank_table[rank]), rid),
    }


def in_seasons(df: pd.DataFrame, span: tuple[int, int]) -> pd.Series:
    return df["season"].between(*span)


def model_probs(df: pd.DataFrame, table: np.ndarray, w: np.ndarray) -> np.ndarray:
    x = features(df, table)[FEATURES].to_numpy()
    return softmax_by_race(x @ w, (df["season"] * 100 + df["round"]).to_numpy())


def fit(df: pd.DataFrame, table: np.ndarray, mask: pd.Series) -> np.ndarray:
    d = df[mask]
    x = features(d, table)[FEATURES].to_numpy()
    return fit_logit(
        x, (d["position"] == 1).to_numpy().astype(int), (d["season"] * 100 + d["round"]).to_numpy()
    )


def tune(res: pd.DataFrame, table: np.ndarray, grid: dict[str, list[float]] = GRID) -> pd.DataFrame:
    rows = []
    for kd, kt, c in itertools.product(grid["k_driver"], grid["k_team"], grid["carry"]):
        df = elo_ratings(res, EloParams(kd, kt, c))
        w = fit(df, table, in_seasons(df, FIT_EARLY))
        v = df[in_seasons(df, VALID)]
        rows.append(
            {
                "k_driver": kd,
                "k_team": kt,
                "carry": c,
                "valid_log_loss": score(v, model_probs(v, table, w)).log_loss,
            }
        )
    return pd.DataFrame(rows).sort_values("valid_log_loss").reset_index(drop=True)


def backtest(
    res: pd.DataFrame, sprints: pd.DataFrame, grid: dict[str, list[float]] = GRID
) -> dict[str, object]:
    res = res.copy()
    res["champ_rank"] = championship_rank(res, sprints)
    train = in_seasons(res, TRAIN)
    won = (res["position"] == 1).astype(int)
    slot_table = win_table(quali_slot(res)[train], won[train])
    has_rank = train & res["champ_rank"].notna()
    rank_table = win_table(res.loc[has_rank, "champ_rank"].astype(int), won[has_rank], max_slot=30)

    tuning = tune(res, slot_table, grid)
    best = EloParams(*tuning.loc[0, ["k_driver", "k_team", "carry"]].astype(float))
    df = elo_ratings(res, best)
    df["champ_rank"] = df.set_index(["season", "round", "driver"]).index.map(
        res.set_index(["season", "round", "driver"])["champ_rank"]
    )
    w_valid = fit(df, slot_table, in_seasons(df, FIT_EARLY))
    w = fit(df, slot_table, in_seasons(df, (BURN_IN + 1, TRAIN[1])))

    test = df[(df["season"] == TEST_SEASON) & df["round"].between(*TEST_ROUNDS)]
    valid = df[in_seasons(df, VALID)]
    out: dict[str, object] = {"params": best, "weights": w, "tuning": tuning, "test": {}, "valid": {}}
    for name, part, weights in (("test", test, w), ("valid", valid, w_valid)):
        probs = {
            "model": model_probs(part, slot_table, weights),
            **baseline_probs(part, slot_table, rank_table),
        }
        out[name] = {k: score(part, p) for k, p in probs.items()}
    t = out["test"]
    best_base = min(t["kvalifikácia"].log_loss, t["šampionát"].log_loss)
    out["margin"] = best_base - t["model"].log_loss
    out["passed"] = out["margin"] >= THRESHOLD
    out["n_test"], out["n_train"] = t["model"].races, df[train].groupby(["season", "round"]).ngroups
    out["test_frame"] = test.assign(p=model_probs(test, slot_table, w))
    return out


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    p: EloParams = r["params"]
    w = r["weights"]
    rows = lambda part: "\n".join(  # noqa: E731
        f"| {k} | {_pct(s.accuracy)} | {_num(s.log_loss)} | {_num(s.podium_brier)} |"
        for k, s in r[part].items()
    )
    tf: pd.DataFrame = r["test_frame"]
    per_race = []
    for (_, rnd), g in tf.groupby(["season", "round"]):
        fav = g.loc[g["p"].idxmax()]
        win = g[g["position"] == 1].iloc[0]
        per_race.append(
            f"| {rnd} | {g['race'].iloc[0].replace(' Grand Prix', '')} | {fav['code']} {_pct(fav['p'])} | "
            f"{win['code']} (kval. {int(quali_slot(g).loc[win.name])}.) | {_pct(win['p'])} |"
        )
    return f"""# F1 – backtest (brána G0-F1)

Kritériá: docs/gate-f1-G0.md (stanovené 14. 10. 2026 pred meraním). Tip po kvalifikácii,
hodnotí sa víťaz. Tréning 2014 – 2025 ({r["n_train"]} pretekov, 2014 rozbeh Ela), test 2026 kolá 1 – 17
({r["n_test"]} pretekov). Dáta: Jolpica-F1 (CC BY-NC-SA 4.0).

## Test: 2026 kolá 1 – 17

| Model | Presnosť (favorit vyhral) | Log loss víťaza | Brier pódia |
|---|---|---|---|
{rows("test")}

Rozdiel oproti lepšej baseline: **{_num(r["margin"])}** (hranica {_num(THRESHOLD)}) →
**{"kritérium splnené" if r["passed"] else "kritérium nesplnené"}**.

## Staré pravidlá: 2023 – 2025 (len zápis)

Váhy z 2015 – 2022, preto sú tieto sezóny pre model neznáme.

| Model | Presnosť | Log loss víťaza | Brier pódia |
|---|---|---|---|
{rows("valid")}

## Model

Elo jazdca K {p.k_driver:g}, Elo tímu K {p.k_team:g}, prenos do novej sezóny {p.carry:g}
(vybrané na 2023 – 2025 z {len(r["tuning"])} kombinácií). Váhy logitu (2015 – 2025):
kvalifikácia {_num(w[0], 3)}, Elo jazdca {_num(w[1], 3)}, Elo tímu {_num(w[2], 3)} (na 100 Elo).

## Preteky 2026

| Kolo | Veľká cena | Favorit modelu | Víťaz | Šanca víťaza |
|---|---|---|---|---|
{chr(10).join(per_race)}
"""


def main(results: Path = RESULTS, sprints: Path = SPRINTS, out: Path = REPORT) -> dict[str, object]:
    r = backtest(pd.read_parquet(results), pd.read_parquet(sprints))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(r), encoding="utf-8")
    t = r["test"]
    for k, s in t.items():
        print(
            f"{k:13s} presnosť {s.accuracy:6.1%}  log loss {s.log_loss:.4f}  Brier pódia {s.podium_brier:.4f}"
        )
    print(f"rozdiel oproti lepšej baseline {r['margin']:.4f} → {'SPLNENÉ' if r['passed'] else 'NESPLNENÉ'}")
    print(f"Report: {out}")
    return r


if __name__ == "__main__":
    main()
