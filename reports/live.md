# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-10 · uložené predpovede 160 · s výsledkom 154 · čaká na výsledok 6

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 154 | sezóny 2023/24 – 2025/26 |
| Presnosť | 67,5 % (± 7,4 p. b.) | 67,3 % |
| Log loss | 0,5936 | 0,5996 |
| Brier | 0,2053 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 35 | 55,9 % | 60,0 % |
| 60 – 70 % | 48 | 64,6 % | 50,0 % |
| 70 – 80 % | 39 | 74,1 % | 76,9 % |
| 80 – 90 % | 27 | 83,6 % | 88,9 % |
| 90 – 100 % | 5 | 91,7 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 150 | 67,3 % |
| nízka | 4 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-09 | NOP @ GSW | 80,6 % | 87 : 138 | ✓ |
| 2026-11-09 | SAS @ PHX | 28,8 % | 122 : 96 | ✓ |
| 2026-11-09 | DEN @ HOU | 62,0 % | 100 : 110 | ✓ |
| 2026-11-09 | IND @ DAL | 69,2 % | 122 : 125 | ✓ |
| 2026-11-09 | MEM @ TOR | 65,9 % | 118 : 102 | ✗ |
| 2026-11-09 | WAS @ DET | 83,4 % | 111 : 122 | ✓ |
| 2026-11-09 | CLE @ CHA | 40,5 % | 112 : 124 | ✗ |
| 2026-11-09 | LAL @ ATL | 56,0 % | 124 : 114 | ✗ |
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
