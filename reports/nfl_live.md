# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-16 01:00 UTC: zamknutých tipov 43, vyhodnotených 41, čaká na výsledok 2.

**Spolu: 30 z 41 (73,2 %), log loss 0,5285, Brier 0,1745**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |
|       10 |       12 |            8 | 66,7 %     | 0,5512     |

## Posledný týždeň (10.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| WAS @ NYG | NYG   | 65 %    | 24:21      | ❌  |
| NE @ DET  | DET   | 54 %    | 10:35      | ✅  |
| BUF @ NYJ | BUF   | 84 %    | 31:12      | ✅  |
| CAR @ NO  | NO    | 56 %    | 20:17      | ❌  |
| HOU @ CLE | HOU   | 55 %    | 24:27      | ❌  |
| JAX @ TEN | JAX   | 83 %    | 40:23      | ✅  |
| KC @ ATL  | KC    | 60 %    | 35:13      | ✅  |
| MIA @ IND | IND   | 60 %    | 22:24      | ✅  |
| MIN @ GB  | GB    | 56 %    | 30:10      | ❌  |
| LA @ ARI  | LA    | 71 %    | 34:6       | ✅  |
| SEA @ LV  | SEA   | 71 %    | 21:13      | ✅  |
| SF @ DAL  | SF    | 66 %    | 46:40      | ✅  |
