# NFL – ostré tipy (`nfl-elo-qb-v1`)

Model `nfl-elo-qb-v1` (Elo z G0-NFL + náhradník quarterback −65 Elo), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-11-12 – 2027-01-10: log loss ≤ 0,6602 (`docs/gate-nfl-qb-G2.md`).

Stav k 2026-11-19 02:32 UTC: zamknutých tipov 27, vyhodnotených 14, čaká na výsledok 13.

**Spolu: 9 z 14 (64,3 %), log loss 0,5649, Brier 0,1926**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|       10 |       14 |            9 | 64,3 %     | 0,5649     |

## Posledný týždeň (10.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| WAS @ NYG | NYG   | 57 %    | 24:21      | ❌  |
| NE @ DET  | DET   | 54 %    | 10:35      | ✅  |
| BUF @ NYJ | BUF   | 84 %    | 31:12      | ✅  |
| CAR @ NO  | NO    | 56 %    | 20:17      | ❌  |
| HOU @ CLE | HOU   | 55 %    | 24:27      | ❌  |
| JAX @ TEN | JAX   | 83 %    | 40:23      | ✅  |
| KC @ ATL  | KC    | 60 %    | 35:13      | ✅  |
| MIA @ IND | IND   | 60 %    | 22:24      | ✅  |
| MIN @ GB  | GB    | 56 %    | 30:10      | ❌  |
| LA @ ARI  | LA    | 78 %    | 34:6       | ✅  |
| SEA @ LV  | SEA   | 63 %    | 21:13      | ✅  |
| SF @ DAL  | SF    | 66 %    | 46:40      | ✅  |
| PIT @ CIN | CIN   | 59 %    | 18:38      | ✅  |
| LAC @ BAL | BAL   | 62 %    | 23:20      | ❌  |
