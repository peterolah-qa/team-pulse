# Backtest NFL – vrstva A (Elo tímov)

Dáta: nflverse games.csv (commit `a6b91bf`), zdroj nflverse / Lee Sharpe (github.com/nflverse/nfldata). Stávkové stĺpce sa nenačítali. Zahrievanie 1999 – 2009 (nemeria sa), tréning 2010 – 2022 (3496 zápasov), test 2023 – 2025 (854 zápasov, z toho 39 play-off; 1 remíza sa nevyhodnocuje). Každá predpoveď používa len zápasy pred ňou.

## Brána G0-NFL: ✅ splnené

Kritériá: docs/gate-nfl-G0.md (stanovené 28. 10. 2026 pred meraním).

| # | Kritérium | Výsledok |
|---|---|---|
| 1 | Úplnosť dát 2010 – 2025 | všetky počty sedia |
| 2 | Log loss Ela vs. lepšia baseline (≥ 0,0005) | Elo 0,6341, baseline 0,6611, rozdiel 0,0270 |
| 3 | Test úniku dát | tests/test_nfl.py |
| 4 | Stávkové stĺpce sa nenačítajú | tests/test_nfl.py |
| 5 | Contract test ESPN NFL | tests/test_nfl.py |

## Porovnanie na testovacích sezónach

| model                       |   zápasy | presnosť   | log loss   | Brier   |
|:----------------------------|---------:|:-----------|:-----------|:--------|
| Elo ladené na tréningu      |      854 | 63,9 %     | 0,6341     | 0,2218  |
| Elo štart (FiveThirtyEight) |      854 | 63,9 %     | 0,6348     | 0,2220  |
| Baseline: vždy domáci       |      854 | 54,1 %     | 0,6895     | 0,2482  |
| Baseline: lepšia bilancia   |      854 | 59,5 %     | 0,6611     | 0,2342  |

Log loss a Brier: nižšie = lepšie.

Domáci (mimo neutrálnych ihrísk) vyhrali 54,6 % testovacích zápasov.

## Parametre Ela (ladené len na tréningu)

Zvolené: K 20, výhoda domáceho 48 Elo, prenos do sezóny 0,6; play-off × 1,2 a nový klub 1300 pevne podľa FiveThirtyEight. Štart FiveThirtyEight: K 20, výhoda domáceho 48, prenos 0,667.

|   K |   výhoda domáceho | prenos do sezóny   | log loss (tréning)   |
|----:|------------------:|:-------------------|:---------------------|
|  20 |                48 | 0,6                | 0,6299               |
|  20 |                40 | 0,6                | 0,6299               |
|  20 |                55 | 0,6                | 0,6303               |
|  20 |                48 | 0,667              | 0,6304               |
|  20 |                40 | 0,667              | 0,6304               |

## Baseline (naučené na tréningu)

- Vždy domáci: 56,2 % (na neutrálnom ihrisku 50 %)
- Lepšia bilancia: σ(0,274 · domáci + 1,31 · rozdiel bilancií)

## Kalibrácia (test)

Keď model dá favoritovi X %, vyhrá favorit naozaj cca X %?

| pásmo        |   zápasy | predpoveď   | skutočnosť   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |      346 | 55,0 %      | 54,6 %       |
| (0.6, 0.7]   |      251 | 64,5 %      | 67,3 %       |
| (0.7, 0.8]   |      183 | 74,2 %      | 69,4 %       |
| (0.8, 0.9]   |       68 | 83,5 %      | 80,9 %       |
| (0.9, 1.0]   |        6 | 91,0 %      | 100,0 %      |

## Po sezónach (test)

|   season |   zápasy | presnosť   | log loss   | Brier   |
|---------:|---------:|:-----------|:-----------|:--------|
|     2023 |      285 | 60,4 %     | 0,6582     | 0,2325  |
|     2024 |      285 | 67,0 %     | 0,6104     | 0,2110  |
|     2025 |      284 | 64,4 %     | 0,6338     | 0,2219  |
