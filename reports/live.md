# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-10-29 · uložené predpovede 71 · s výsledkom 68 · čaká na výsledok 3

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 68 | sezóny 2023/24 – 2025/26 |
| Presnosť | 64,7 % (± 11,4 p. b.) | 67,3 % |
| Log loss | 0,6221 | 0,5996 |
| Brier | 0,2173 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 12 | 55,6 % | 58,3 % |
| 60 – 70 % | 23 | 64,4 % | 47,8 % |
| 70 – 80 % | 17 | 73,6 % | 70,6 % |
| 80 – 90 % | 15 | 84,3 % | 86,7 % |
| 90 – 100 % | 1 | 90,3 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 68 | 64,7 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-28 | LAL @ LAC | 72,1 % | 103 : 87 | ✗ |
| 2026-10-28 | OKC @ DAL | 27,0 % | 96 : 120 | ✗ |
| 2026-10-28 | SAS @ UTA | 19,7 % | 117 : 111 | ✓ |
| 2026-10-28 | DEN @ NOP | 33,8 % | 104 : 91 | ✓ |
| 2026-10-28 | GSW @ MIN | 68,3 % | 119 : 114 | ✗ |
| 2026-10-28 | HOU @ MIL | 28,9 % | 132 : 100 | ✓ |
| 2026-10-28 | NYK @ CHI | 21,8 % | 133 : 127 | ✓ |
| 2026-10-28 | ORL @ TOR | 60,7 % | 99 : 129 | ✓ |
| 2026-10-28 | PHI @ IND | 18,8 % | 114 : 109 | ✓ |
| 2026-10-28 | CHA @ DET | 62,8 % | 89 : 97 | ✓ |
| 2026-10-28 | WAS @ CLE | 86,5 % | 111 : 121 | ✓ |
| 2026-10-28 | MIA @ ATL | 66,9 % | 129 : 117 | ✗ |
| 2026-10-27 | POR @ LAL | 65,7 % | 136 : 129 | ✗ |
| 2026-10-27 | SAC @ SAS | 90,3 % | 103 : 130 | ✓ |
| 2026-10-27 | DET @ NYK | 70,1 % | 97 : 111 | ✓ |
| 2026-10-27 | BKN @ BOS | 87,5 % | 124 : 125 | ✓ |
| 2026-10-26 | GSW @ DEN | 85,9 % | 134 : 114 | ✗ |
| 2026-10-26 | MEM @ UTA | 61,5 % | 110 : 105 | ✗ |
| 2026-10-26 | ATL @ HOU | 67,4 % | 110 : 120 | ✓ |
| 2026-10-26 | PHX @ OKC | 74,2 % | 114 : 125 | ✓ |

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
