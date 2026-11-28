# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-28 03:17 UTC: zamknutých tipov 72, vyhodnotených 61, čaká na výsledok 11.

**Spolu: 42 z 61 (68,9 %), log loss 0,5587, Brier 0,1898**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |
|       10 |       14 |            9 | 64,3 %     | 0,5970     |
|       11 |       13 |            9 | 69,2 %     | 0,5486     |
|       12 |        5 |            2 | 40,0 %     | 0,7079     |

## Posledný týždeň (12.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| GB @ LA   | LA    | 67 %    | 13:26      | ✅  |
| CHI @ DET | DET   | 57 %    | 39:35      | ❌  |
| PHI @ DAL | DAL   | 65 %    | 39:38      | ❌  |
| KC @ BUF  | BUF   | 70 %    | 10:13      | ✅  |
| DEN @ PIT | DEN   | 59 %    | 5:27       | ❌  |
