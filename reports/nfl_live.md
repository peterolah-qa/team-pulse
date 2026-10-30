# NFL – ostré tipy (`nfl-elo-v1`)

Model `nfl-elo-v1` (Elo z brány G0-NFL: K 20, výhoda domáceho 48, prenos 0,6), tipy zamknuté pred výkopom (`team_pulse.nfl.predict`), výsledky z nflverse games.csv (zdroj nflverse / Lee Sharpe). Brána G2 2026-10-29 – 2027-01-10: log loss ≤ 0,6620 (`docs/gate-nfl-G2.md`).

Stav k 2026-10-30 15:55 UTC: zamknutých tipov 14, vyhodnotených 1, čaká na výsledok 13.

**Spolu: 1 z 1 (100,0 %), log loss 0,4164, Brier 0,1160**

## Po týždňoch

|   týždeň |   zápasy |   tip vyšiel | presnosť   | log loss   |
|---------:|---------:|-------------:|:-----------|:-----------|
|        8 |        1 |            1 | 100,0 %    | 0,4164     |

## Posledný týždeň (8.)

Výsledok je hostia : domáci.

| zápas    | tip   | šanca   | výsledok   |    |
|:---------|:------|:--------|:-----------|:---|
| CAR @ GB | GB    | 66 %    | 19:27      | ✅  |
