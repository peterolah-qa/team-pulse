# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-12 · uložené predpovede 174 · s výsledkom 170 · čaká na výsledok 4

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 170 | sezóny 2023/24 – 2025/26 |
| Presnosť | 67,6 % (± 7,0 p. b.) | 67,3 % |
| Log loss | 0,5900 | 0,5996 |
| Brier | 0,2040 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 41 | 55,8 % | 58,5 % |
| 60 – 70 % | 52 | 64,6 % | 51,9 % |
| 70 – 80 % | 42 | 74,0 % | 76,2 % |
| 80 – 90 % | 29 | 83,8 % | 89,7 % |
| 90 – 100 % | 6 | 92,0 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 165 | 67,3 % |
| stredná | 1 | 100,0 % |
| nízka | 4 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-11 | OKC @ POR | 47,5 % | 108 : 118 | ✗ |
| 2026-11-11 | GSW @ HOU | 73,5 % | 108 : 115 | ✓ |
| 2026-11-11 | ORL @ UTA | 36,4 % | 123 : 108 | ✓ |
| 2026-11-11 | BKN @ NOP | 65,8 % | 145 : 111 | ✗ |
| 2026-11-11 | LAL @ MIL | 14,1 % | 123 : 112 | ✓ |
| 2026-11-11 | DEN @ MEM | 32,0 % | 123 : 118 | ✓ |
| 2026-11-11 | SAS @ CHI | 14,0 % | 124 : 119 | ✓ |
| 2026-11-11 | BOS @ TOR | 39,3 % | 98 : 93 | ✓ |
| 2026-11-11 | CLE @ NYK | 72,3 % | 115 : 107 | ✗ |
| 2026-11-11 | WAS @ IND | 53,8 % | 101 : 114 | ✓ |
| 2026-11-10 | OKC @ POR | 43,1 % | 103 : 123 | ✗ |
| 2026-11-10 | ORL @ SAC | 44,5 % | 107 : 100 | ✓ |
| 2026-11-10 | MIA @ UTA | 26,1 % | 115 : 109 | ✓ |
| 2026-11-10 | LAC @ PHX | 55,0 % | 110 : 133 | ✓ |
| 2026-11-10 | BOS @ PHI | 56,0 % | 123 : 101 | ✗ |
| 2026-11-10 | MIL @ NYK | 93,3 % | 85 : 117 | ✓ |
| 2026-11-09 | NOP @ GSW | 80,6 % | 87 : 138 | ✓ |
| 2026-11-09 | SAS @ PHX | 28,8 % | 122 : 96 | ✓ |
| 2026-11-09 | DEN @ HOU | 62,0 % | 100 : 110 | ✓ |
| 2026-11-09 | IND @ DAL | 69,2 % | 122 : 125 | ✓ |

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
