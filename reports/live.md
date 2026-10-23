# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-10-23 · uložené predpovede 28 · s výsledkom 16 · čaká na výsledok 12

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 16 | sezóny 2023/24 – 2025/26 |
| Presnosť | 68,8 % (± 22,7 p. b.) | 67,3 % |
| Log loss | 0,5996 | 0,5996 |
| Brier | 0,2077 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 2 | 53,5 % | 100,0 % |
| 60 – 70 % | 8 | 63,1 % | 50,0 % |
| 70 – 80 % | 4 | 76,0 % | 75,0 % |
| 80 – 90 % | 2 | 82,1 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 16 | 68,8 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-10-22 | DEN @ OKC | 68,3 % | 84 : 96 | ✓ |
| 2026-10-22 | CLE @ PHI | 62,2 % | 106 : 114 | ✓ |
| 2026-10-21 | SAC @ LAC | 75,5 % | 96 : 121 | ✓ |
| 2026-10-21 | PHX @ POR | 64,4 % | 83 : 124 | ✓ |
| 2026-10-21 | GSW @ LAL | 79,1 % | 105 : 127 | ✓ |
| 2026-10-21 | DAL @ HOU | 83,0 % | 110 : 128 | ✓ |
| 2026-10-21 | IND @ NOP | 64,8 % | 123 : 120 | ✗ |
| 2026-10-21 | UTA @ MEM | 55,5 % | 103 : 123 | ✓ |
| 2026-10-21 | CHI @ TOR | 81,3 % | 92 : 135 | ✓ |
| 2026-10-21 | CHA @ BKN | 27,0 % | 110 : 103 | ✓ |
| 2026-10-21 | MIN @ MIA | 60,2 % | 131 : 106 | ✗ |
| 2026-10-21 | MIL @ WAS | 51,5 % | 116 : 128 | ✓ |
| 2026-10-21 | ATL @ ORL | 62,3 % | 132 : 125 | ✗ |
| 2026-10-20 | OKC @ SAS | 61,6 % | 116 : 104 | ✗ |
| 2026-10-20 | PHI @ NYK | 76,2 % | 106 : 100 | ✗ |
| 2026-10-20 | BOS @ DET | 61,4 % | 113 : 121 | ✓ |

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
