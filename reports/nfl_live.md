# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-02 00:43 UTC: zamknutých tipov 14, vyhodnotených 12, čaká na výsledok 2.

**Spolu: 9 z 12 (75,0 %), log loss 0,4870, Brier 0,1552**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       12 |            9 | 75,0 %     | 0,4870     |

## Posledný týždeň (8.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| CAR @ GB  | GB    | 66 %    | 19:27      | ✅  |
| ARI @ DAL | DAL   | 69 %    | 33:30      | ❌  |
| ATL @ TB  | TB    | 55 %    | 0:16       | ✅  |
| BAL @ BUF | BUF   | 73 %    | 10:36      | ✅  |
| CLE @ PIT | PIT   | 68 %    | 6:27       | ✅  |
| IND @ JAX | JAX   | 79 %    | 7:42       | ✅  |
| LV @ NYJ  | NYJ   | 52 %    | 38:33      | ❌  |
| MIN @ DET | MIN   | 54 %    | 15:19      | ❌  |
| TEN @ CIN | CIN   | 84 %    | 36:43      | ✅  |
| LAC @ LA  | LA    | 77 %    | 9:24       | ✅  |
| KC @ DEN  | DEN   | 65 %    | 24:28      | ✅  |
| NE @ MIA  | NE    | 70 %    | 24:19      | ✅  |
