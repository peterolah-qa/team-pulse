# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-28 · uložené predpovede 286 · s výsledkom 281 · čaká na výsledok 5

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 281 | sezóny 2023/24 – 2025/26 |
| Presnosť | 67,3 % (± 5,5 p. b.) | 67,3 % |
| Log loss | 0,6111 | 0,5996 |
| Brier | 0,2123 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 64 | 55,7 % | 62,5 % |
| 60 – 70 % | 86 | 64,9 % | 53,5 % |
| 70 – 80 % | 72 | 74,5 % | 73,6 % |
| 80 – 90 % | 49 | 84,2 % | 83,7 % |
| 90 – 100 % | 10 | 91,9 % | 90,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 262 | 66,4 % |
| stredná | 3 | 100,0 % |
| nízka | 16 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-27 | GSW @ POR | 74,2 % | 94 : 116 | ✓ |
| 2026-11-27 | NOP @ LAC | 67,3 % | 105 : 104 | ✗ |
| 2026-11-27 | DEN @ UTA | 23,0 % | 120 : 107 | ✓ |
| 2026-11-27 | LAL @ SAS | 66,0 % | 96 : 99 | ✓ |
| 2026-11-27 | DAL @ PHX | 67,8 % | 113 : 109 | ✗ |
| 2026-11-27 | MEM @ MIN | 73,8 % | 114 : 109 | ✗ |
| 2026-11-27 | ATL @ BOS | 70,4 % | 87 : 86 | ✗ |
| 2026-11-27 | BKN @ TOR | 76,5 % | 100 : 124 | ✓ |
| 2026-11-27 | PHI @ IND | 33,9 % | 111 : 87 | ✓ |
| 2026-11-27 | MIL @ DET | 84,4 % | 98 : 113 | ✓ |
| 2026-11-27 | MIA @ NYK | 67,2 % | 108 : 105 | ✗ |
| 2026-11-25 | SAS @ POR | 51,8 % | 111 : 116 | ✓ |
| 2026-11-25 | SAC @ GSW | 72,5 % | 110 : 129 | ✓ |
| 2026-11-25 | PHX @ HOU | 71,9 % | 104 : 116 | ✓ |
| 2026-11-25 | BKN @ MIL | 60,6 % | 104 : 97 | ✗ |
| 2026-11-25 | LAC @ MEM | 61,8 % | 97 : 115 | ✓ |
| 2026-11-25 | MIN @ OKC | 62,2 % | 113 : 106 | ✗ |
| 2026-11-25 | CLE @ NYK | 77,3 % | 102 : 121 | ✓ |
| 2026-11-25 | CHI @ CHA | 64,7 % | 107 : 105 | ✗ |
| 2026-11-25 | MIA @ PHI | 55,5 % | 104 : 111 | ✓ |

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
