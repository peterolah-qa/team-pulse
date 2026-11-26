# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-26 18:59 UTC: zamknutých tipov 72, vyhodnotených 57, čaká na výsledok 15.

**Spolu: 41 z 57 (71,9 %), log loss 0,5430, Brier 0,1824**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |
|       10 |       14 |            9 | 64,3 %     | 0,5970     |
|       11 |       13 |            9 | 69,2 %     | 0,5486     |
|       12 |        1 |            1 | 100,0 %    | 0,4051     |

## Posledný týždeň (12.)

Výsledok je hostia : domáci.

| zápas   | tip   | šanca   | výsledok   |    |
|:--------|:------|:--------|:-----------|:---|
| GB @ LA | LA    | 67 %    | 13:26      | ✅  |
