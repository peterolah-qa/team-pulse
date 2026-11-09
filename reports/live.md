# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-09 · uložené predpovede 154 · s výsledkom 146 · čaká na výsledok 8

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 146 | sezóny 2023/24 – 2025/26 |
| Presnosť | 67,8 % (± 7,6 p. b.) | 67,3 % |
| Log loss | 0,5961 | 0,5996 |
| Brier | 0,2064 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 33 | 55,8 % | 63,6 % |
| 60 – 70 % | 45 | 64,5 % | 48,9 % |
| 70 – 80 % | 38 | 74,2 % | 76,3 % |
| 80 – 90 % | 25 | 83,7 % | 88,0 % |
| 90 – 100 % | 5 | 91,7 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 142 | 67,6 % |
| nízka | 4 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-08 | MIA @ SAC | 27,7 % | 114 : 108 | ✓ |
| 2026-11-08 | NOP @ LAC | 60,6 % | 123 : 139 | ✓ |
| 2026-11-08 | BOS @ MIL | 20,0 % | 117 : 97 | ✓ |
| 2026-11-08 | BKN @ DAL | 78,8 % | 93 : 130 | ✓ |
| 2026-11-08 | UTA @ MIN | 85,3 % | 100 : 115 | ✓ |
| 2026-11-08 | LAL @ DET | 77,9 % | 121 : 116 | ✗ |
| 2026-11-08 | PHI @ CHI | 25,3 % | 127 : 121 | ✓ |
| 2026-11-07 | SAS @ POR | 40,1 % | 125 : 103 | ✓ |
| 2026-11-07 | HOU @ PHX | 34,9 % | 99 : 102 | ✗ |
| 2026-11-07 | ORL @ GSW | 66,9 % | 119 : 126 | ✓ |
| 2026-11-07 | WAS @ OKC | 91,7 % | 75 : 114 | ✓ |
| 2026-11-07 | NYK @ CLE | 36,8 % | 109 : 97 | ✓ |
| 2026-11-07 | BKN @ ATL | 80,4 % | 121 : 124 | ✓ |
| 2026-11-07 | DEN @ IND | 20,1 % | 114 : 102 | ✓ |
| 2026-11-06 | SAS @ SAC | 17,7 % | 124 : 109 | ✓ |
| 2026-11-06 | POR @ LAL | 67,0 % | 118 : 124 | ✓ |
| 2026-11-06 | MIN @ NOP | 43,9 % | 115 : 109 | ✓ |
| 2026-11-06 | TOR @ MIL | 41,8 % | 121 : 107 | ✓ |
| 2026-11-06 | OKC @ MEM | 27,1 % | 128 : 97 | ✓ |
| 2026-11-06 | UTA @ DAL | 73,8 % | 100 : 112 | ✓ |

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
