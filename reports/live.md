# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-21 · uložené predpovede 241 · s výsledkom 235 · čaká na výsledok 6

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 235 | sezóny 2023/24 – 2025/26 |
| Presnosť | 68,9 % (± 5,9 p. b.) | 67,3 % |
| Log loss | 0,6016 | 0,5996 |
| Brier | 0,2075 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 55 | 55,9 % | 63,6 % |
| 60 – 70 % | 72 | 64,9 % | 56,9 % |
| 70 – 80 % | 57 | 74,4 % | 75,4 % |
| 80 – 90 % | 43 | 84,1 % | 83,7 % |
| 90 – 100 % | 8 | 91,9 % | 87,5 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 223 | 68,6 % |
| stredná | 1 | 100,0 % |
| nízka | 11 | 72,7 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-20 | SAC @ LAL | 87,6 % | 104 : 106 | ✓ |
| 2026-11-20 | HOU @ DEN | 58,7 % | 124 : 133 | ✓ |
| 2026-11-20 | PHX @ UTA | 36,2 % | 111 : 101 | ✓ |
| 2026-11-20 | NOP @ OKC | 86,3 % | 120 : 126 | ✓ |
| 2026-11-20 | WAS @ CHI | 66,2 % | 98 : 94 | ✗ |
| 2026-11-20 | TOR @ DET | 72,8 % | 105 : 102 | ✗ |
| 2026-11-20 | IND @ CLE | 79,1 % | 119 : 128 | ✓ |
| 2026-11-20 | ORL @ BKN | 34,4 % | 113 : 111 | ✓ |
| 2026-11-20 | CHA @ ATL | 67,0 % | 97 : 111 | ✓ |
| 2026-11-19 | LAC @ SAS | 86,6 % | 112 : 124 | ✓ |
| 2026-11-19 | NYK @ MIN | 39,8 % | 102 : 99 | ✓ |
| 2026-11-19 | POR @ MIL | 23,5 % | 124 : 114 | ✓ |
| 2026-11-19 | GSW @ MEM | 58,9 % | 98 : 126 | ✓ |
| 2026-11-18 | PHX @ SAC | 36,3 % | 128 : 107 | ✓ |
| 2026-11-18 | UTA @ LAL | 90,3 % | 109 : 97 | ✗ |
| 2026-11-18 | BOS @ DEN | 60,0 % | 101 : 105 | ✓ |
| 2026-11-18 | GSW @ DAL | 56,8 % | 94 : 116 | ✓ |
| 2026-11-18 | ATL @ OKC | 69,6 % | 117 : 112 | ✗ |
| 2026-11-18 | DET @ NOP | 31,8 % | 122 : 109 | ✓ |
| 2026-11-18 | WAS @ TOR | 68,2 % | 103 : 99 | ✗ |

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
