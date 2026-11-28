# NFL – ostré tipy (`nfl-elo-qb-v1`)

Model `nfl-elo-qb-v1` (Elo z G0-NFL + náhradník quarterback −65 Elo), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-11-12 – 2027-01-10: log loss ≤ 0,6602 (`docs/gate-nfl-qb-G2.md`).

Stav k 2026-11-28 03:17 UTC: zamknutých tipov 43, vyhodnotených 32, čaká na výsledok 11.

**Spolu: 20 z 32 (62,5 %), log loss 0,5958, Brier 0,2085**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|       10 |       14 |            9 | 64,3 %     | 0,5649     |
|       11 |       13 |            9 | 69,2 %     | 0,5661     |
|       12 |        5 |            2 | 40,0 %     | 0,7596     |

## Posledný týždeň (12.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| GB @ LA   | LA    | 67 %    | 13:26      | ✅  |
| CHI @ DET | DET   | 57 %    | 39:35      | ❌  |
| PHI @ DAL | DAL   | 73 %    | 39:38      | ❌  |
| KC @ BUF  | BUF   | 70 %    | 10:13      | ✅  |
| DEN @ PIT | DEN   | 59 %    | 5:27       | ❌  |
