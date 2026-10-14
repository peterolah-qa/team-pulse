# NHL – test Glicko-2

Tréning do 2022/23 (17676 zápasov), test 2023/24 – 2025/26 (3936 zápasov základnej časti). Parametre Glicko-2 ladené len na tréningu. Glicko-2 berie len výhru/prehru, Elo aj rozdiel gólov.

## Rozhodnutie

- **Glicko-2 namiesto Ela + únava:** ❌ nezlepšuje dosť (zlepšenie -0,0028, hranica 0,0005)
- **Elo + Glicko-2 + únava:** ❌ nezlepšuje dosť (zlepšenie 0,0000, hranica 0,0005)

## Porovnanie na testovacích sezónach

| model                          |   zápasy | presnosť   | log loss   | Brier   |
|:-------------------------------|---------:|:-----------|:-----------|:--------|
| A: Elo (samotné)               |     3936 | 57,2 %     | 0,6730     | 0,2402  |
| A: Glicko-2 (samotné)          |     3936 | 57,5 %     | 0,6807     | 0,2437  |
| A + C (schválené: Elo + únava) |     3936 | 57,6 %     | 0,6713     | 0,2394  |
| Glicko-2 namiesto Ela + únava  |     3936 | 57,8 %     | 0,6741     | 0,2407  |
| Elo + Glicko-2 + únava         |     3936 | 57,5 %     | 0,6713     | 0,2394  |

## Parametre Glicko-2 (ladené na tréningu)

Zvolené: tau 0,2, volatilita 0,06, domáca výhoda 30, neistota po lete +25, prenos do sezóny 0,8. Priemerná neistota klubu v teste 63 bodov.

| tau   | volatilita   |   domáca výhoda |   neistota po lete | prenos   | log loss (tréning)   |
|:------|:-------------|----------------:|-------------------:|:---------|:---------------------|
| 0,2   | 0,06         |              30 |                 25 | 0,8      | 0,6792               |
| 0,5   | 0,06         |              30 |                 25 | 0,8      | 0,6793               |
| 0,2   | 0,06         |              40 |                 25 | 0,8      | 0,6794               |
| 0,5   | 0,06         |              40 |                 25 | 0,8      | 0,6794               |
| 0,2   | 0,06         |              20 |                 25 | 0,8      | 0,6798               |
