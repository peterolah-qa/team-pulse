# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-10-25 · uložené predpovede 43 · s výsledkom 36 · čaká na výsledok 7

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 36 | sezóny 2023/24 – 2025/26 |
| Presnosť | 61,1 % (± 15,9 p. b.) | 67,3 % |
| Log loss | 0,6107 | 0,5996 |
| Brier | 0,2152 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 9 | 55,1 % | 44,4 % |
| 60 – 70 % | 13 | 64,2 % | 46,2 % |
| 70 – 80 % | 8 | 74,9 % | 75,0 % |
| 80 – 90 % | 6 | 84,4 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 36 | 61,1 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-24 | GSW @ PHX | 77,3 % | 122 : 131 | ✓ |
| 2026-10-24 | NOP @ DEN | 87,7 % | 135 : 141 | ✓ |
| 2026-10-24 | HOU @ ATL | 53,5 % | 121 : 114 | ✗ |
| 2026-10-24 | SAS @ DAL | 17,6 % | 122 : 106 | ✓ |
| 2026-10-24 | WAS @ CHI | 67,7 % | 124 : 120 | ✗ |
| 2026-10-24 | MIL @ PHI | 84,8 % | 116 : 127 | ✓ |
| 2026-10-24 | BKN @ CLE | 87,1 % | 121 : 125 | ✓ |
| 2026-10-24 | MIA @ CHA | 62,4 % | 110 : 115 | ✓ |
| 2026-10-23 | POR @ SAC | 32,9 % | 128 : 120 | ✓ |
| 2026-10-23 | LAC @ LAL | 71,9 % | 117 : 125 | ✓ |
| 2026-10-23 | MEM @ GSW | 71,9 % | 111 : 108 | ✗ |
| 2026-10-23 | NOP @ UTA | 52,1 % | 119 : 120 | ✓ |
| 2026-10-23 | HOU @ SAS | 68,2 % | 114 : 110 | ✗ |
| 2026-10-23 | DET @ MIA | 46,2 % | 128 : 111 | ✓ |
| 2026-10-23 | TOR @ WAS | 25,9 % | 112 : 102 | ✓ |
| 2026-10-23 | MIN @ ORL | 54,8 % | 115 : 93 | ✗ |
| 2026-10-23 | DAL @ IND | 59,1 % | 121 : 105 | ✗ |
| 2026-10-23 | ATL @ CHA | 63,6 % | 128 : 81 | ✗ |
| 2026-10-23 | NYK @ BOS | 42,1 % | 103 : 107 | ✗ |
| 2026-10-23 | CHI @ MIL | 57,7 % | 132 : 125 | ✗ |

## Príprava (skúška archívu, mimo G2)

Uložené predpovede 60 · s výsledkom 60 · presnosť 50,0 %

Hviezdy v príprave hrajú menej a model je naučený na základnú časť, takže tieto čísla nič nehovoria o kvalite modelu. Overujú len, že sa predpovede ukladajú a výsledky dopĺňajú.

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-16 | DEN @ LAL | 53,9 % | 121 : 106 | ✗ |
| 2026-10-16 | UTA @ PHX | 78,0 % | 119 : 116 | ✗ |
| 2026-10-16 | POR @ GSW | 44,7 % | 118 : 128 | ✗ |
| 2026-10-16 | SAC @ SAS | 90,5 % | 97 : 126 | ✓ |
| 2026-10-16 | WAS @ NOP | 75,9 % | 106 : 107 | ✓ |
| 2026-10-16 | CHA @ MEM | 26,4 % | 98 : 116 | ✗ |
| 2026-10-16 | MIN @ CHI | 40,4 % | 116 : 133 | ✗ |
| 2026-10-16 | ATL @ DAL | 41,8 % | 135 : 111 | ✓ |
| 2026-10-16 | MIL @ IND | 61,5 % | 128 : 127 | ✗ |
| 2026-10-16 | TOR @ DET | 76,8 % | 125 : 129 | ✓ |
