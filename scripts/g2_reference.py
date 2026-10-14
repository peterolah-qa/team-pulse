"""Referencia pre brány G2 (NBA, NHL): ako model vychádza v 14-dňových obdobiach testovacích sezón.

Ostré meranie trvá 14 dní (NBA aj NHL ~100 zápasov). To je málo na dôkaz, že je model dobrý,
hranice brány sa preto stanovia vopred z backtestu:
  - začiatok sezóny: prvých 14 dní základnej časti každej testovacej sezóny,
  - všetky 14-dňové okná základnej časti testovacích sezón: rozdelenie log loss modelu
    (95. percentil = hranica „model nie je pokazený“) a podiel okien, v ktorých model
    prehral s baseline „vždy domáci“ (ako často by takú podmienku nesplnil aj dobrý model).

Model sa učí len na tréningových sezónach, presne ako v backteste
(reports/learned.md, reports/nhl_learned.md).
Baseline „vždy domáci“ = podiel výhier domácich v tréningových sezónach.

Spustenie (z Macu, dáta v data/raw):  uv run python scripts/g2_reference.py
Výstup: reports/g2_reference.md
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("reports/g2_reference.md")
DAYS = 14
QUANTILE = 0.95


def _log_loss(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def nba_predictions() -> pd.DataFrame:
    """Predpovede finálneho NBA modelu (Elo + hráči + súpiska + únava) naučeného len na tréningu."""
    from team_pulse import learned as nba

    games = pd.read_parquet(nba.GAMES)
    players = pd.read_parquet(nba.PLAYERS)
    ds = nba.build_dataset(games, players)
    cols = nba.BASE_COLS + nba.PLAYER_COLS + nba.ROSTER_COLS + nba.FATIGUE_COLS
    train, _ = nba.split(ds)
    model = nba.fit(train, cols)
    last_regular = games[~games["playoff"]].groupby("season")["date"].max()
    out = pd.DataFrame({
        "season": ds["season"].astype(int),
        "date": pd.to_datetime(ds["date"]),
        "p": nba.predict(model, ds, cols),
        "home_won": ds["home_won"].astype(int),
        "train": ds["season"].between(*nba.TRAIN),
        "test": ds["season"].between(*nba.TEST),
    })  # fmt: skip
    out["regular"] = out["date"] <= out["season"].map(pd.to_datetime(last_regular))
    return out


def nhl_predictions() -> pd.DataFrame:
    """Predpovede NHL modelu (Elo + únava) naučeného len na tréningu."""
    from team_pulse.nhl import learned as nhl
    from team_pulse.nhl.backtest import split
    from team_pulse.nhl.fetch_games import OUT as GAMES

    games = pd.read_parquet(GAMES)
    ds = nhl.build_dataset(games).merge(games[["game_id", "date"]], on="game_id")
    train, test = split(ds)
    cols = nhl.BASE_COLS + nhl.FATIGUE_COLS
    model = nhl.fit(ds[train], cols)
    return pd.DataFrame({
        "season": ds["season"].astype(int),
        "date": pd.to_datetime(ds["date"]),
        "p": nhl.predict(model, ds, cols),
        "home_won": ds["home_won"].astype(int),
        "train": train,
        "test": test,
        "regular": ds["game_type"] == "R",
    })  # fmt: skip


def add_scores(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Log loss modelu a baseline na zápas, trafený tip. Vráti aj podiel výhier domácich z tréningu."""
    home_rate = float(df.loc[df["train"] & df["regular"], "home_won"].mean())
    y = df["home_won"].to_numpy(float)
    out = df.assign(
        ll=_log_loss(df["p"].to_numpy(), y),
        ll_home=_log_loss(np.full(len(df), home_rate), y),
        hit=(df["p"] > 0.5) == (df["home_won"] == 1),
    )
    return out, home_rate


def season_starts(test: pd.DataFrame, days: int = DAYS) -> pd.DataFrame:
    """Prvých `days` dní základnej časti každej testovacej sezóny."""
    parts = [d[d["date"] < d["date"].min() + pd.Timedelta(days=days)] for _, d in test.groupby("season")]
    return pd.concat(parts)


def windows(test: pd.DataFrame, days: int = DAYS) -> pd.DataFrame:
    """Všetky `days`-dňové okná základnej časti (začiatok každý deň), jeden riadok na okno."""
    rows = []
    for season, d in test.groupby("season"):
        last_start = d["date"].max() - pd.Timedelta(days=days - 1)
        for start in pd.date_range(d["date"].min(), last_start):
            w = d[(d["date"] >= start) & (d["date"] < start + pd.Timedelta(days=days))]
            if len(w):
                rows.append({"season": season, "start": start, "n": len(w), "ll": w["ll"].mean(),
                             "ll_home": w["ll_home"].mean(), "acc": w["hit"].mean()})  # fmt: skip
    return pd.DataFrame(rows)


def totals(df: pd.DataFrame) -> dict[str, float]:
    return {"n": len(df), "ll": df["ll"].mean(), "ll_home": df["ll_home"].mean(), "acc": df["hit"].mean()}


def reference(df: pd.DataFrame) -> dict[str, object]:
    scored, home_rate = add_scores(df)
    test = scored[scored["test"] & scored["regular"]]
    starts = season_starts(test)
    win = windows(test)
    per_start = starts.groupby("season").agg(
        od=("date", "min"),
        n=("ll", "size"),
        ll=("ll", "mean"),
        ll_home=("ll_home", "mean"),
        acc=("hit", "mean"),
    )
    return {
        "home_rate": home_rate,
        "test": totals(test),
        "starts": per_start,
        "starts_all": totals(starts),
        "windows": {
            "count": len(win),
            "n_median": float(win["n"].median()),
            "ll_q": win["ll"].quantile([0.05, 0.5, QUANTILE]).to_dict(),
            "acc_q": win["acc"].quantile([0.05, 0.5, 0.95]).to_dict(),
            "lose_home": float((win["ll"] > win["ll_home"]).mean()),
        },
    }  # fmt: skip


def _n(x: float, d: int = 4) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def _p(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def section(name: str, r: dict[str, object]) -> list[str]:
    t, s, w = r["test"], r["starts_all"], r["windows"]
    q = w["ll_q"]
    lines = [
        f"## {name}",
        "",
        f"Baseline „vždy domáci“: domáci vyhrávajú {_p(r['home_rate'])} zápasov (tréningové sezóny).",
        "",
        "| obdobie | zápasy | log loss modelu | log loss baseline | presnosť |",
        "|:--|--:|--:|--:|--:|",
        f"| celé testovacie sezóny | {t['n']} | {_n(t['ll'])} | {_n(t['ll_home'])} | {_p(t['acc'])} |",
    ]
    for season, row in r["starts"].iterrows():
        label = f"{season - 1}/{str(season)[-2:]}"
        lines.append(
            f"| prvých {DAYS} dní {label} (od {row['od']:%d. %m.}) | {int(row['n'])} | {_n(row['ll'])} | "
            f"{_n(row['ll_home'])} | {_p(row['acc'])} |"
        )
    lines += [
        f"| začiatky sezón spolu | {s['n']} | {_n(s['ll'])} | {_n(s['ll_home'])} | {_p(s['acc'])} |",
        "",
        f"**{DAYS}-dňové okná** základnej časti testovacích sezón: {w['count']} okien, medián "
        f"{w['n_median']:.0f} zápasov na okno.",
        "",
        f"- Log loss modelu: 5. percentil {_n(q[0.05])}, medián {_n(q[0.5])}, "
        f"**{int(QUANTILE * 100)}. percentil {_n(q[QUANTILE])}** (hranica „model nie je pokazený“).",
        f"- Presnosť: 5. percentil {_p(w['acc_q'][0.05])}, medián {_p(w['acc_q'][0.5])}, "
        f"95. percentil {_p(w['acc_q'][0.95])}.",
        f"- Model prehral s baseline „vždy domáci“ v {_p(w['lose_home'])} okien. Toľko by podmienku "
        "„porazí baseline za 14 dní“ nesplnil aj dobrý model, preto nie je kritériom brány.",
        "",
    ]
    return lines


def to_markdown(results: dict[str, dict[str, object]], day: date) -> str:
    head = [
        "# Referencia pre brány G2 (14 dní ostrej prevádzky)",
        "",
        f"Vypočítané {day:%d. %m. %Y} skriptom `scripts/g2_reference.py` z backtestu: model naučený len na",
        "tréningových sezónach, hodnotí sa základná časť testovacích sezón 2023/24 – 2025/26.",
        "",
    ]
    body = [line for name, r in results.items() for line in section(name, r)]
    return "\n".join(head + body)


def main(out: Path = OUT) -> dict[str, dict[str, object]]:
    results = {"NBA": reference(nba_predictions()), "NHL": reference(nhl_predictions())}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_markdown(results, date.today()), encoding="utf-8")
    for name, r in results.items():
        q = r["windows"]["ll_q"][QUANTILE]
        print(f"{name}: hranica log loss za {DAYS} dní (95. percentil) {q:.4f}, "
              f"model prehral s baseline v {r['windows']['lose_home']:.1%} okien")  # fmt: skip
    print(f"Report: {out}")
    return results


if __name__ == "__main__":
    main()
