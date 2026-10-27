# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-10-27 · uložené predpovede 56 · s výsledkom 52 · čaká na výsledok 4

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 52 | sezóny 2023/24 – 2025/26 |
| Presnosť | 63,5 % (± 13,1 p. b.) | 67,3 % |
| Log loss | 0,6397 | 0,5996 |
| Brier | 0,2236 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 12 | 55,6 % | 58,3 % |
| 60 – 70 % | 17 | 64,2 % | 47,1 % |
| 70 – 80 % | 12 | 73,9 % | 75,0 % |
| 80 – 90 % | 11 | 84,4 % | 81,8 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 52 | 63,5 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-26 | GSW @ DEN | 85,9 % | 134 : 114 | ✗ |
| 2026-10-26 | MEM @ UTA | 61,5 % | 110 : 105 | ✗ |
| 2026-10-26 | ATL @ HOU | 67,4 % | 110 : 120 | ✓ |
| 2026-10-26 | PHX @ OKC | 74,2 % | 114 : 125 | ✓ |
| 2026-10-26 | IND @ MIL | 58,6 % | 102 : 110 | ✓ |
| 2026-10-26 | DAL @ MIA | 72,2 % | 113 : 109 | ✗ |
| 2026-10-26 | CHI @ BOS | 85,1 % | 99 : 134 | ✓ |
| 2026-10-26 | MIN @ CLE | 66,2 % | 125 : 127 | ✓ |
| 2026-10-26 | WAS @ CHA | 81,9 % | 103 : 110 | ✓ |
| 2026-10-25 | MEM @ SAC | 61,5 % | 123 : 112 | ✗ |
| 2026-10-25 | DET @ PHI | 43,8 % | 106 : 93 | ✓ |
| 2026-10-25 | LAC @ OKC | 81,7 % | 101 : 108 | ✓ |
| 2026-10-25 | TOR @ MIN | 70,1 % | 94 : 117 | ✓ |
| 2026-10-25 | ORL @ NYK | 87,6 % | 111 : 102 | ✗ |
| 2026-10-25 | IND @ BKN | 43,5 % | 136 : 109 | ✓ |
| 2026-10-25 | LAL @ UTA | 28,5 % | 132 : 123 | ✓ |
| 2026-10-24 | GSW @ PHX | 77,3 % | 122 : 131 | ✓ |
| 2026-10-24 | NOP @ DEN | 87,7 % | 135 : 141 | ✓ |
| 2026-10-24 | HOU @ ATL | 53,5 % | 121 : 114 | ✗ |
| 2026-10-24 | SAS @ DAL | 17,6 % | 122 : 106 | ✓ |

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
