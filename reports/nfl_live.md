# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-10 17:00 UTC: zamknutých tipov 43, vyhodnotených 29, čaká na výsledok 14.

**Spolu: 22 z 29 (75,9 %), log loss 0,5191, Brier 0,1697**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |       15 |           12 | 80,0 %     | 0,4975     |

## Posledný týždeň (9.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| JAX @ BAL | JAX   | 60 %    | 33:10      | ✅  |
| CIN @ ATL | CIN   | 64 %    | 34:17      | ✅  |
| CLE @ NO  | NO    | 51 %    | 22:23      | ✅  |
| DAL @ IND | IND   | 50 %    | 27:23      | ❌  |
| DEN @ CAR | DEN   | 69 %    | 26:21      | ✅  |
| DET @ MIA | DET   | 70 %    | 19:9       | ✅  |
| LA @ WAS  | LA    | 63 %    | 20:13      | ✅  |
| NYG @ PHI | NYG   | 51 %    | 19:11      | ✅  |
| NYJ @ KC  | KC    | 80 %    | 12:35      | ✅  |
| HOU @ LAC | HOU   | 59 %    | 44:22      | ✅  |
| LV @ SF   | SF    | 80 %    | 17:38      | ✅  |
| ARI @ SEA | SEA   | 82 %    | 3:17       | ✅  |
| GB @ NE   | NE    | 66 %    | 45:27      | ❌  |
| TB @ CHI  | CHI   | 72 %    | 24:27      | ✅  |
| BUF @ MIN | MIN   | 51 %    | 23:6       | ❌  |
