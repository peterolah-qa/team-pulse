# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-23 21:18 UTC: zamknutých tipov 56, vyhodnotených 55, čaká na výsledok 1.

**Spolu: 40 z 55 (72,7 %), log loss 0,5355, Brier 0,1790**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |
|       10 |       14 |            9 | 64,3 %     | 0,5970     |
|       11 |       12 |            9 | 75,0 %     | 0,5035     |

## Posledný týždeň (11.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| IND @ HOU | HOU   | 72 %    | 3:26       | ✅  |
| ARI @ KC  | KC    | 81 %    | 7:34       | ✅  |
| BAL @ CAR | CAR   | 56 %    | 33:35      | ✅  |
| JAX @ NYG | JAX   | 68 %    | 18:23      | ❌  |
| MIA @ BUF | BUF   | 90 %    | 9:26       | ✅  |
| NO @ CHI  | CHI   | 82 %    | 13:21      | ✅  |
| TB @ DET  | DET   | 73 %    | 21:31      | ✅  |
| TEN @ DAL | DAL   | 75 %    | 30:51      | ✅  |
| NYJ @ LAC | LAC   | 64 %    | 27:24      | ❌  |
| LV @ DEN  | DEN   | 83 %    | 24:38      | ✅  |
| PIT @ PHI | PIT   | 65 %    | 16:19      | ❌  |
| MIN @ SF  | SF    | 54 %    | 10:35      | ✅  |
