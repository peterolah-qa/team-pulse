"""Vrstva quarterback pre NFL: náhradník namiesto bežného štartéra (schválená Petrom 28. 10. 2026).

Bežný štartér tímu = quarterback, ktorý štartoval najčastejšie v posledných 8 odohraných zápasoch tímu
(pri rovnosti ten, kto štartoval naposledy). Ak tím nastúpi s iným quarterbackom, je to „náhradník“ a tím
dostane −BACKUP_PENALTY Elo. Počíta sa len z odohraných zápasov pred zápasom (bez úniku dát). Ak quarterback
zápasu nie je známy, vrstva sa pri ňom nepoužije.

Penalizácia je naučená len na tréningu 2010 – 2022 (mriežka 0 – 195 po 5); na teste 2023 – 2025 zlepšila
log loss o viac než 0,0005 (reports/nfl_qb.md).

Spustenie (report vrstvy):  uv run python -m team_pulse.nfl.qb
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from team_pulse.backtest import metrics
from team_pulse.nfl import games as G
from team_pulse.nfl.backtest import THRESHOLD, home_won, masks
from team_pulse.nfl.elo import NflEloParams, diff, expected, run

WINDOW = 8
BACKUP_PENALTY = 65.0  # naučené na tréningu (reports/nfl_qb.md)
GRID = [float(x) for x in range(0, 200, 5)]
REPORT = Path("reports/nfl_qb.md")


def primary(starts: list[str]) -> str | None:
    """Najčastejší štartér z posledných WINDOW zápasov, pri rovnosti ten, kto štartoval naposledy."""
    last = starts[-WINDOW:]
    if not last:
        return None
    counts = Counter(last)
    top = max(counts.values())
    return next(q for q in reversed(last) if counts[q] == top)


def backup_flags(games: pd.DataFrame) -> pd.DataFrame:
    """Pre každý zápas: bežný štartér oboch tímov a či nastupuje náhradník (0/1). Index ako `games`."""
    order = games.sort_values(["date", "game_id"], kind="stable").index
    hist: dict[str, list[str]] = {}
    rows = {}
    for i in order:
        g = games.loc[i]
        out = {}
        for side in ("home", "away"):
            qb = g[f"{side}_qb_id"]
            prim = primary(hist.get(g[side], []))
            out[f"{side}_primary"] = prim
            out[f"{side}_backup"] = int(isinstance(qb, str) and prim is not None and qb != prim)
        rows[i] = out
        if g["played"]:
            for side in ("home", "away"):
                qb = g[f"{side}_qb_id"]
                if isinstance(qb, str):
                    hist.setdefault(g[side], []).append(qb)
    return pd.DataFrame.from_dict(rows, orient="index").loc[games.index]


def adjusted_diff(
    elo_diff: float, home_backup: int, away_backup: int, penalty: float = BACKUP_PENALTY
) -> float:
    return elo_diff + penalty * (away_backup - home_backup)


def evaluate_layer(games: pd.DataFrame, params: NflEloParams) -> dict[str, object]:
    g = games[games["season"] <= 2025].sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)
    r = run(g, params)
    f = backup_flags(r)
    train, test = masks(r)
    won = home_won(r)
    d0 = np.array(
        [
            diff(h, a, params, n, p)
            for h, a, n, p in zip(r.elo_home_pre, r.elo_away_pre, r.neutral, r.playoff, strict=True)
        ]
    )
    delta = (f["away_backup"] - f["home_backup"]).to_numpy()

    def m(mask: pd.Series, pen: float) -> dict[str, float]:
        p = pd.Series([expected(x) for x in (d0 + pen * delta)[mask.to_numpy()]])
        return metrics(p, won[mask].reset_index(drop=True))

    tuning = pd.DataFrame([{"penalty": pen, **m(train, pen)} for pen in GRID]).sort_values(
        "log_loss", kind="stable"
    )
    best = float(tuning.iloc[0]["penalty"])
    base, layer = m(test, 0.0), m(test, best)
    share = lambda mask: float(np.r_[f["home_backup"][mask], f["away_backup"][mask]].mean())  # noqa: E731
    return {
        "penalty": best,
        "train_gain": float(m(train, 0.0)["log_loss"] - tuning.iloc[0]["log_loss"]),
        "base": base,
        "layer": layer,
        "gain": base["log_loss"] - layer["log_loss"],
        "passed": base["log_loss"] - layer["log_loss"] >= THRESHOLD,
        "share_train": share(train),
        "share_test": share(test),
        "tuning": tuning.head(5),
    }


def _num(x: float) -> str:
    return f"{x:.5f}".replace(".", ",")


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def to_markdown(r: dict[str, object]) -> str:
    b, lay = r["base"], r["layer"]
    verdict = "✅ prejde" if r["passed"] else "❌ neprejde"
    limit = str(THRESHOLD).replace(".", ",")
    top = r["tuning"][["penalty", "log_loss"]].copy()
    top["log_loss"] = top["log_loss"].map(_num)
    top.columns = ["penalizácia (Elo)", "log loss (tréning)"]
    return (
        "# NFL – vrstva quarterback (náhradník)\n\n"
        "Bežný štartér = najčastejší štartujúci quarterback tímu v posledných 8 odohraných zápasoch "
        "(pri rovnosti posledný). Náhradník = iný štartujúci quarterback → tím −penalizácia Elo. "
        "Penalizácia naučená len "
        "na tréningu 2010 – 2022, hodnotí sa test 2023 – 2025 (rovnaké zápasy ako G0-NFL).\n\n"
        f"## Výsledok: {verdict} (hranica zlepšenia {limit})\n\n"
        "| Model (test) | Zápasy | Presnosť | Log loss | Brier |\n|---|---|---|---|---|\n"
        f"| Elo (G0) | {int(b['n'])} | {_pct(b['accuracy'])} | {_num(b['log_loss'])} | {_num(b['brier'])} |\n"
        f"| Elo + náhradník (−{r['penalty']:g} Elo) | {int(lay['n'])} | {_pct(lay['accuracy'])} | "
        f"{_num(lay['log_loss'])} | {_num(lay['brier'])} |\n\n"
        f"Zlepšenie na teste {_num(r['gain'])}, na tréningu {_num(r['train_gain'])}. Náhradník nastúpil "
        f"v {_pct(r['share_train'])} tímových zápasov tréningu a {_pct(r['share_test'])} testu.\n\n"
        f"## Ladenie na tréningu (5 najlepších)\n\n{top.to_markdown(index=False)}\n\n"
        "Zamietnutý kandidát (28. 10.): nováčik (< 8 štartov v kariére, −25 Elo) – na teste +0,00123, "
        "na tréningu len +0,00043 (pod hranicou), riziko náhody.\n"
    )


def main() -> dict[str, object]:
    from team_pulse.nfl.predict import PARAMS

    r = evaluate_layer(G.load(G.download()), PARAMS)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(to_markdown(r), encoding="utf-8")
    print(
        f"penalizácia {r['penalty']:g} Elo, test {r['base']['log_loss']:.5f} → {r['layer']['log_loss']:.5f} "
        f"(zlepšenie {r['gain']:.5f}), presnosť {r['layer']['accuracy']:.1%} → {REPORT}"
    )
    return r


if __name__ == "__main__":
    main()
