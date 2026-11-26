# NFL – ostré tipy (`nfl-elo-qb-v1`)

Model `nfl-elo-qb-v1` (Elo z G0-NFL + náhradník quarterback −65 Elo), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-11-12 – 2027-01-10: log loss ≤ 0,6602 (`docs/gate-nfl-qb-G2.md`).

Stav k 2026-11-26 18:59 UTC: zamknutých tipov 43, vyhodnotených 28, čaká na výsledok 15.

**Spolu: 19 z 28 (67,9 %), log loss 0,5597, Brier 0,1922**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|       10 |       14 |            9 | 64,3 %     | 0,5649     |
|       11 |       13 |            9 | 69,2 %     | 0,5661     |
|       12 |        1 |            1 | 100,0 %    | 0,4051     |

## Posledný týždeň (12.)

Výsledok je hostia : domáci.

| zápas   | tip   | šanca   | výsledok   |    |
|:--------|:------|:--------|:-----------|:---|
| GB @ LA | LA    | 67 %    | 13:26      | ✅  |
