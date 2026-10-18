# NHL – ostré tipy

Tipy zamknuté pred začiatkom zápasu (`team_pulse.nhl.predict`), vyhodnotené po zápase. Model Elo + únava, v teste 2023/24 – 2025/26 mal presnosť 57,6 %.

**Spolu: 27 z 45 (60,0 %), log loss 0,6430**

## Po dňoch

| deň (USA)   |   zápasy |   tip vyšiel | presnosť   |
|:------------|---------:|-------------:|:-----------|
| 13. 10.     |       16 |            8 | 50,0 %     |
| 14. 10.     |        2 |            1 | 50,0 %     |
| 15. 10.     |       11 |            7 | 63,6 %     |
| 16. 10.     |        2 |            2 | 100,0 %    |
| 17. 10.     |       14 |            9 | 64,3 %     |

## Posledný deň (17. 10.)

Výsledok je hostia : domáci, pp = po predĺžení, sn = po nájazdoch.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| NJD @ WSH | WSH   | 59 %    | 2:4        | ✅  |
| CAR @ WPG | CAR   | 60 %    | 3:2        | ✅  |
| VAN @ TBL | TBL   | 74 %    | 2:4        | ✅  |
| SEA @ FLA | FLA   | 60 %    | 3:8        | ✅  |
| NYI @ TOR | TOR   | 53 %    | 4:1        | ❌  |
| BUF @ MTL | MTL   | 52 %    | 3:4 pp     | ✅  |
| SJS @ DET | DET   | 60 %    | 3:4 sn     | ✅  |
| OTT @ PHI | OTT   | 54 %    | 1:3        | ❌  |
| NYR @ CBJ | CBJ   | 52 %    | 0:1 pp     | ✅  |
| DAL @ CHI | DAL   | 63 %    | 4:0        | ✅  |
| STL @ NSH | STL   | 50 %    | 2:5        | ❌  |
| BOS @ LAK | LAK   | 51 %    | 4:1        | ❌  |
| EDM @ UTA | UTA   | 54 %    | 6:2        | ❌  |
| PIT @ VGK | VGK   | 67 %    | 2:6        | ✅  |
