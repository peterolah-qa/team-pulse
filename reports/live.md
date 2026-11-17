# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-17 · uložené predpovede 210 · s výsledkom 205 · čaká na výsledok 5

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 205 | sezóny 2023/24 – 2025/26 |
| Presnosť | 69,3 % (± 6,3 p. b.) | 67,3 % |
| Log loss | 0,5918 | 0,5996 |
| Brier | 0,2038 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 49 | 55,8 % | 63,3 % |
| 60 – 70 % | 61 | 64,7 % | 54,1 % |
| 70 – 80 % | 50 | 74,3 % | 78,0 % |
| 80 – 90 % | 38 | 83,9 % | 84,2 % |
| 90 – 100 % | 7 | 92,1 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 198 | 68,7 % |
| stredná | 1 | 100,0 % |
| nízka | 6 | 83,3 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-16 | PHX @ DEN | 83,5 % | 117 : 105 | ✗ |
| 2026-11-16 | GSW @ NOP | 37,2 % | 94 : 115 | ✗ |
| 2026-11-16 | POR @ MIN | 57,1 % | 98 : 106 | ✓ |
| 2026-11-16 | HOU @ MIA | 58,2 % | 110 : 128 | ✓ |
| 2026-11-16 | PHI @ BKN | 36,8 % | 135 : 123 | ✓ |
| 2026-11-16 | MEM @ WAS | 41,6 % | 136 : 120 | ✓ |
| 2026-11-16 | CHI @ CLE | 77,6 % | 115 : 126 | ✓ |
| 2026-11-16 | ORL @ BOS | 77,4 % | 115 : 105 | ✗ |
| 2026-11-15 | OKC @ SAC | 20,9 % | 125 : 103 | ✓ |
| 2026-11-15 | ATL @ MIL | 30,7 % | 113 : 106 | ✓ |
| 2026-11-15 | HOU @ WAS | 19,9 % | 147 : 119 | ✓ |
| 2026-11-15 | NYK @ TOR | 29,3 % | 112 : 108 | ✓ |
| 2026-11-15 | DAL @ BOS | 89,0 % | 94 : 131 | ✓ |
| 2026-11-15 | SAS @ UTA | 12,5 % | 110 : 102 | ✓ |
| 2026-11-15 | CHA @ LAC | 58,8 % | 105 : 113 | ✓ |
| 2026-11-15 | LAL @ PHX | 39,4 % | 131 : 123 | ✓ |
| 2026-11-15 | IND @ PHI | 82,1 % | 124 : 131 | ✓ |
| 2026-11-14 | CHI @ MIN | 87,9 % | 117 : 106 | ✗ |
| 2026-11-14 | BKN @ MEM | 66,5 % | 110 : 129 | ✓ |
| 2026-11-14 | DET @ MIA | 40,4 % | 117 : 137 | ✗ |

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
