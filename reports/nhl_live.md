# NHL – ostré tipy

Tipy zamknuté pred začiatkom zápasu (`team_pulse.nhl.predict`), vyhodnotené po zápase. Model Elo + únava, v teste 2023/24 – 2025/26 mal presnosť 57,6 %.

**Spolu: 37 z 62 (59,7 %), log loss 0,6599**

## Po dňoch

| deň (USA)   |   zápasy |   tip vyšiel | presnosť   |
|:------------|---------:|-------------:|:-----------|
| 13. 10.     |       16 |            8 | 50,0 %     |
| 14. 10.     |        2 |            1 | 50,0 %     |
| 15. 10.     |       11 |            7 | 63,6 %     |
| 16. 10.     |        2 |            2 | 100,0 %    |
| 17. 10.     |       14 |            9 | 64,3 %     |
| 18. 10.     |        2 |            1 | 50,0 %     |
| 19. 10.     |        4 |            3 | 75,0 %     |
| 20. 10.     |       11 |            6 | 54,5 %     |

## Posledný deň (20. 10.)

Výsledok je hostia : domáci, pp = po predĺžení, sn = po nájazdoch.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| SJS @ MTL | MTL   | 72 %    | 4:3 pp     | ❌  |
| COL @ NJD | COL   | 53 %    | 3:4        | ❌  |
| ANA @ NYI | NYI   | 61 %    | 2:3        | ✅  |
| LAK @ WSH | WSH   | 63 %    | 5:2        | ❌  |
| TOR @ CBJ | CBJ   | 61 %    | 6:2        | ❌  |
| WPG @ STL | STL   | 55 %    | 1:2        | ✅  |
| BOS @ DAL | DAL   | 57 %    | 2:3 pp     | ✅  |
| MIN @ EDM | EDM   | 52 %    | 3:4 pp     | ✅  |
| DET @ SEA | SEA   | 52 %    | 3:4 sn     | ✅  |
| CAR @ VAN | CAR   | 71 %    | 6:3        | ✅  |
| TBL @ VGK | VGK   | 53 %    | 6:2        | ❌  |
