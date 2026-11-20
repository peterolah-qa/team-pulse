# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-20 17:46 UTC: zamknutých tipov 56, vyhodnotených 44, čaká na výsledok 12.

**Spolu: 32 z 44 (72,7 %), log loss 0,5394, Brier 0,1794**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |
|       10 |       14 |            9 | 64,3 %     | 0,5970     |
|       11 |        1 |            1 | 100,0 %    | 0,3235     |

## Posledný týždeň (11.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| IND @ HOU | HOU   | 72 %    | 3:26       | ✅  |
