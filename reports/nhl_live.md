# NHL – ostré tipy

Tipy zamknuté pred začiatkom zápasu (`team_pulse.nhl.predict`), vyhodnotené po zápase. Model Elo + únava, v teste 2023/24 – 2025/26 mal presnosť 57,6 %.

**Spolu: 54 z 90 (60,0 %), log loss 0,6635**

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
| 21. 10.     |        2 |            1 | 50,0 %     |
| 22. 10.     |       12 |            5 | 41,7 %     |
| 23. 10.     |        2 |            2 | 100,0 %    |
| 24. 10.     |       12 |            9 | 75,0 %     |

## Posledný deň (24. 10.)

Výsledok je hostia : domáci, pp = po predĺžení, sn = po nájazdoch.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| ANA @ PHI | PHI   | 56 %    | 5:4        | ❌  |
| LAK @ NJD | NJD   | 58 %    | 1:3        | ✅  |
| SJS @ BOS | BOS   | 67 %    | 4:6        | ✅  |
| NYR @ OTT | OTT   | 56 %    | 4:7        | ✅  |
| NSH @ PIT | PIT   | 58 %    | 2:3 pp     | ✅  |
| BUF @ WSH | WSH   | 52 %    | 3:4 pp     | ✅  |
| VGK @ CBJ | VGK   | 54 %    | 1:2 pp     | ❌  |
| CAR @ STL | CAR   | 56 %    | 4:0        | ✅  |
| TOR @ EDM | EDM   | 62 %    | 7:2        | ❌  |
| TBL @ UTA | UTA   | 54 %    | 4:5 pp     | ✅  |
| DET @ CGY | CGY   | 51 %    | 1:4        | ✅  |
| MIN @ SEA | MIN   | 54 %    | 5:1        | ✅  |
