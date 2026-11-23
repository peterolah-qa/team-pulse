# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-23 · uložené predpovede 258 · s výsledkom 248 · čaká na výsledok 10

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 248 | sezóny 2023/24 – 2025/26 |
| Presnosť | 68,5 % (± 5,8 p. b.) | 67,3 % |
| Log loss | 0,6001 | 0,5996 |
| Brier | 0,2071 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 59 | 55,7 % | 62,7 % |
| 60 – 70 % | 75 | 64,8 % | 56,0 % |
| 70 – 80 % | 60 | 74,5 % | 75,0 % |
| 80 – 90 % | 45 | 84,3 % | 84,4 % |
| 90 – 100 % | 9 | 92,0 % | 88,9 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 234 | 67,9 % |
| stredná | 2 | 100,0 % |
| nízka | 12 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-22 | BOS @ GSW | 37,7 % | 87 : 88 | ✗ |
| 2026-11-22 | IND @ NYK | 87,8 % | 106 : 113 | ✓ |
| 2026-11-22 | DAL @ UTA | 53,0 % | 116 : 114 | ✗ |
| 2026-11-22 | DEN @ CHI | 26,7 % | 151 : 145 | ✓ |
| 2026-11-22 | ORL @ WAS | 36,6 % | 96 : 116 | ✗ |
| 2026-11-22 | OKC @ MIA | 48,5 % | 113 : 123 | ✗ |
| 2026-11-22 | DET @ ATL | 54,4 % | 97 : 107 | ✓ |
| 2026-11-21 | BOS @ SAC | 25,0 % | 96 : 97 | ✗ |
| 2026-11-21 | NOP @ SAS | 93,0 % | 91 : 114 | ✓ |
| 2026-11-21 | MEM @ MIN | 76,1 % | 95 : 104 | ✓ |
| 2026-11-21 | LAC @ DAL | 63,5 % | 100 : 110 | ✓ |
| 2026-11-21 | POR @ NYK | 53,8 % | 96 : 97 | ✓ |
| 2026-11-21 | MIL @ PHI | 88,0 % | 129 : 132 | ✓ |
| 2026-11-20 | SAC @ LAL | 87,6 % | 104 : 106 | ✓ |
| 2026-11-20 | HOU @ DEN | 58,7 % | 124 : 133 | ✓ |
| 2026-11-20 | PHX @ UTA | 36,2 % | 111 : 101 | ✓ |
| 2026-11-20 | NOP @ OKC | 86,3 % | 120 : 126 | ✓ |
| 2026-11-20 | WAS @ CHI | 66,2 % | 98 : 94 | ✗ |
| 2026-11-20 | TOR @ DET | 72,8 % | 105 : 102 | ✗ |
| 2026-11-20 | IND @ CLE | 79,1 % | 119 : 128 | ✓ |

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
