# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-11-07 00:55 UTC: zamknutých tipov 29, vyhodnotených 15, čaká na výsledok 14.

**Spolu: 11 z 15 (73,3 %), log loss 0,5402, Brier 0,1795**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |       14 |           10 | 71,4 %     | 0,5423     |
|        9 |        1 |            1 | 100,0 %    | 0,5107     |

## Posledný týždeň (9.)

Výsledok je hostia : domáci.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| JAX @ BAL | JAX   | 60 %    | 33:10      | ✅  |
