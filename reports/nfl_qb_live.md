# NFL – ostré tipy (`nfl-elo-qb-v1`)

Model `nfl-elo-qb-v1` (Elo z G0-NFL + náhradník quarterback −65 Elo), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-11-12 – 2027-01-10: log loss ≤ 0,6602 (`docs/gate-nfl-qb-G2.md`).

Stav k 2026-11-23 01:40 UTC: zamknutých tipov 27, vyhodnotených 25, čaká na výsledok 2.

**Spolu: 17 z 25 (68,0 %), log loss 0,5484, Brier 0,1876**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|       10 |       14 |            9 | 64,3 %     | 0,5649     |
|       11 |       11 |            8 | 72,7 %     | 0,5274     |

## Posledný týždeň (11.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| IND @ HOU | HOU   | 72 %    | 3:26       | ✅  |
| ARI @ KC  | KC    | 86 %    | 7:34       | ✅  |
| BAL @ CAR | CAR   | 56 %    | 33:35      | ✅  |
| JAX @ NYG | JAX   | 75 %    | 18:23      | ❌  |
| MIA @ BUF | BUF   | 93 %    | 9:26       | ✅  |
| NO @ CHI  | CHI   | 82 %    | 13:21      | ✅  |
| TB @ DET  | DET   | 73 %    | 21:31      | ✅  |
| TEN @ DAL | DAL   | 75 %    | 30:51      | ✅  |
| NYJ @ LAC | LAC   | 64 %    | 27:24      | ❌  |
| LV @ DEN  | DEN   | 88 %    | 24:38      | ✅  |
| PIT @ PHI | PIT   | 73 %    | 16:19      | ❌  |
