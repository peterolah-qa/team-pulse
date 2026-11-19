# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-19 · uložené predpovede 226 · s výsledkom 222 · čaká na výsledok 4

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 222 | sezóny 2023/24 – 2025/26 |
| Presnosť | 68,0 % (± 6,1 p. b.) | 67,3 % |
| Log loss | 0,6091 | 0,5996 |
| Brier | 0,2107 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 53 | 55,8 % | 62,3 % |
| 60 – 70 % | 67 | 64,9 % | 55,2 % |
| 70 – 80 % | 54 | 74,3 % | 75,9 % |
| 80 – 90 % | 40 | 83,9 % | 82,5 % |
| 90 – 100 % | 8 | 91,9 % | 87,5 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 212 | 67,5 % |
| stredná | 1 | 100,0 % |
| nízka | 9 | 77,8 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-18 | PHX @ SAC | 36,3 % | 128 : 107 | ✓ |
| 2026-11-18 | UTA @ LAL | 90,3 % | 109 : 97 | ✗ |
| 2026-11-18 | BOS @ DEN | 60,0 % | 101 : 105 | ✓ |
| 2026-11-18 | GSW @ DAL | 56,8 % | 94 : 116 | ✓ |
| 2026-11-18 | ATL @ OKC | 69,6 % | 117 : 112 | ✗ |
| 2026-11-18 | DET @ NOP | 31,8 % | 122 : 109 | ✓ |
| 2026-11-18 | WAS @ TOR | 68,2 % | 103 : 99 | ✗ |
| 2026-11-18 | CHI @ BKN | 53,2 % | 137 : 107 | ✗ |
| 2026-11-18 | PHI @ ORL | 54,8 % | 121 : 116 | ✗ |
| 2026-11-18 | MIL @ MIA | 85,7 % | 130 : 137 | ✓ |
| 2026-11-18 | HOU @ IND | 22,4 % | 119 : 104 | ✓ |
| 2026-11-18 | MEM @ CLE | 71,8 % | 124 : 121 | ✗ |
| 2026-11-17 | CHA @ LAL | 77,1 % | 114 : 118 | ✓ |
| 2026-11-17 | UTA @ LAC | 81,1 % | 132 : 107 | ✗ |
| 2026-11-17 | DET @ SAS | 72,6 % | 105 : 93 | ✗ |
| 2026-11-17 | POR @ MIN | 62,6 % | 105 : 106 | ✓ |
| 2026-11-17 | NYK @ TOR | 32,8 % | 111 : 102 | ✓ |
| 2026-11-16 | PHX @ DEN | 83,5 % | 117 : 105 | ✗ |
| 2026-11-16 | GSW @ NOP | 37,2 % | 94 : 115 | ✗ |
| 2026-11-16 | POR @ MIN | 57,1 % | 98 : 106 | ✓ |

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
