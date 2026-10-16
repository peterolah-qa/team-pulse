# NHL – ostré tipy

Tipy zamknuté pred začiatkom zápasu (`team_pulse.nhl.predict`), vyhodnotené po zápase. Model Elo + únava, v teste 2023/24 – 2025/26 mal presnosť 57,6 %.

**Spolu: 16 z 29 (55,2 %), log loss 0,6745**

## Po dňoch

| deň (USA)   |   zápasy |   tip vyšiel | presnosť   |
|:------------|---------:|-------------:|:-----------|
| 13. 10.     |       16 |            8 | 50,0 %     |
| 14. 10.     |        2 |            1 | 50,0 %     |
| 15. 10.     |       11 |            7 | 63,6 %     |

## Posledný deň (15. 10.)

Výsledok je hostia : domáci, pp = po predĺžení, sn = po nájazdoch.

| zápas     | tip   | šanca   | výsledok   |    |
|:----------|:------|:--------|:-----------|:---|
| BUF @ TOR | BUF   | 54 %    | 5:4 pp     | ✅  |
| NYI @ OTT | OTT   | 58 %    | 1:2 sn     | ✅  |
| SEA @ TBL | TBL   | 66 %    | 3:4 pp     | ✅  |
| VAN @ FLA | FLA   | 66 %    | 2:3 pp     | ✅  |
| NYR @ NJD | NYR   | 51 %    | 1:7        | ❌  |
| PHI @ DET | DET   | 55 %    | 1:2        | ✅  |
| WPG @ CHI | WPG   | 57 %    | 3:4 pp     | ❌  |
| SJS @ NSH | NSH   | 60 %    | 3:2 sn     | ❌  |
| STL @ MIN | MIN   | 56 %    | 4:5        | ✅  |
| UTA @ EDM | EDM   | 56 %    | 4:2        | ❌  |
| CGY @ VGK | VGK   | 65 %    | 2:6        | ✅  |
