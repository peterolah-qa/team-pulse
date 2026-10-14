# Backtest NHL – vrstva A (hokejové Elo)

Dáta: 2005/06 – 2025/26. Prvé 3 sezóny sú rozbeh Ela. Tréning do 2022/23 (17676 zápasov), test 2023/24 – 2025/26 (3936 zápasov základnej časti, model ich pri ladení nevidel). Každá predpoveď používa len dáta pred zápasom.

## Brána G0-NHL: ✅ splnené

Kritérium (docs/sporty.md): log loss Ela na teste o ≥ 0,0005 nižší než lepšia z baseline.

Elo 0,6730 · lepšia baseline 0,6836 · rozdiel 0,0107

## Porovnanie na testovacích sezónach

| model                       |   zápasy | presnosť   | log loss   | Brier   |
|:----------------------------|---------:|:-----------|:-----------|:--------|
| Elo ladené na tréningu      |     3936 | 57,2 %     | 0,6730     | 0,2402  |
| Elo štart (FiveThirtyEight) |     3936 | 57,2 %     | 0,6741     | 0,2407  |
| Baseline: vždy domáci       |     3936 | 54,2 %     | 0,6896     | 0,2482  |
| Baseline: lepšia bilancia   |     3936 | 55,4 %     | 0,6836     | 0,2453  |

Log loss a Brier: nižšie = lepšie. Trestajú aj prehnanú istotu, nielen zlý tip.

Domáci vyhrali 54,2 % testovacích zápasov, 22,1 % zápasov rozhodlo predĺženie alebo nájazdy.

## Parametre Ela (ladené len na tréningu)

Zvolené: K 6, domáca výhoda 30 Elo, prenos do sezóny 0,8. Štart FiveThirtyEight: K 6, domáca výhoda 50, prenos 0,7.

|   K |   domáca výhoda | prenos do sezóny   | log loss (tréning)   |
|----:|----------------:|:-------------------|:---------------------|
|   6 |              30 | 0,8                | 0,6726               |
|   7 |              30 | 0,8                | 0,6727               |
|   7 |              30 | 0,7                | 0,6727               |
|   6 |              30 | 0,7                | 0,6727               |
|   5 |              30 | 0,8                | 0,6728               |

## Baseline (naučené na tréningu)

- Vždy domáci: 54,3 %
- Lepšia bilancia: domáci s lepšou bilanciou 60,7 %, s rovnakou 55,2 %, s horšou 48,1 %

## Kalibrácia (test)

Keď model dá favoritovi X %, vyhrá favorit naozaj cca X %?

| pásmo        |   zápasy | predpoveď   | skutočnosť   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     2427 | 54,7 %      | 52,5 %       |
| (0.6, 0.7]   |     1225 | 64,2 %      | 62,8 %       |
| (0.7, 0.8]   |      280 | 73,6 %      | 72,9 %       |
| (0.8, 0.9]   |        4 | 81,7 %      | 75,0 %       |

## Po sezónach (test)

|         |   zápasy | presnosť   | log loss   | Brier   |
|:--------|---------:|:-----------|:-----------|:--------|
| 2023/24 |     1312 | 60,1 %     | 0,6601     | 0,2341  |
| 2024/25 |     1312 | 58,5 %     | 0,6677     | 0,2377  |
| 2025/26 |     1312 | 52,8 %     | 0,6910     | 0,2489  |
