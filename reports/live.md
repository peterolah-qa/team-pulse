# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-10-31 · uložené predpovede 88 · s výsledkom 81 · čaká na výsledok 7

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 81 | sezóny 2023/24 – 2025/26 |
| Presnosť | 63,0 % (± 10,5 p. b.) | 67,3 % |
| Log loss | 0,6407 | 0,5996 |
| Brier | 0,2258 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 16 | 56,1 % | 62,5 % |
| 60 – 70 % | 28 | 64,4 % | 42,9 % |
| 70 – 80 % | 18 | 73,9 % | 72,2 % |
| 80 – 90 % | 18 | 84,1 % | 83,3 % |
| 90 – 100 % | 1 | 90,3 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 81 | 63,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-30 | DEN @ PHX | 42,9 % | 127 : 120 | ✓ |
| 2026-10-30 | LAL @ GSW | 40,2 % | 95 : 112 | ✗ |
| 2026-10-30 | LAC @ MIN | 63,9 % | 101 : 127 | ✓ |
| 2026-10-30 | HOU @ DAL | 38,1 % | 111 : 116 | ✗ |
| 2026-10-30 | IND @ MIA | 81,1 % | 125 : 145 | ✓ |
| 2026-10-30 | ORL @ TOR | 65,6 % | 121 : 114 | ✗ |
| 2026-10-30 | NYK @ PHI | 37,2 % | 93 : 98 | ✗ |
| 2026-10-30 | DET @ BKN | 20,8 % | 110 : 94 | ✓ |
| 2026-10-30 | CHI @ BOS | 85,7 % | 111 : 125 | ✓ |
| 2026-10-30 | CHA @ WAS | 31,1 % | 79 : 95 | ✗ |
| 2026-10-29 | MEM @ POR | 82,5 % | 124 : 103 | ✗ |
| 2026-10-29 | SAC @ NOP | 59,6 % | 120 : 132 | ✓ |
| 2026-10-29 | CLE @ ATL | 53,2 % | 111 : 114 | ✓ |
| 2026-10-28 | LAL @ LAC | 72,1 % | 103 : 87 | ✗ |
| 2026-10-28 | OKC @ DAL | 27,0 % | 96 : 120 | ✗ |
| 2026-10-28 | SAS @ UTA | 19,7 % | 117 : 111 | ✓ |
| 2026-10-28 | DEN @ NOP | 33,8 % | 104 : 91 | ✓ |
| 2026-10-28 | GSW @ MIN | 68,3 % | 119 : 114 | ✗ |
| 2026-10-28 | HOU @ MIL | 28,9 % | 132 : 100 | ✓ |
| 2026-10-28 | NYK @ CHI | 21,8 % | 133 : 127 | ✓ |

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
