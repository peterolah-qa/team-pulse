# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-24 · uložené predpovede 261 · s výsledkom 258 · čaká na výsledok 3

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 258 | sezóny 2023/24 – 2025/26 |
| Presnosť | 67,8 % (± 5,7 p. b.) | 67,3 % |
| Log loss | 0,6037 | 0,5996 |
| Brier | 0,2090 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 61 | 55,8 % | 60,7 % |
| 60 – 70 % | 77 | 64,9 % | 55,8 % |
| 70 – 80 % | 63 | 74,5 % | 73,0 % |
| 80 – 90 % | 47 | 84,3 % | 85,1 % |
| 90 – 100 % | 10 | 91,9 % | 90,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 243 | 67,1 % |
| stredná | 3 | 100,0 % |
| nízka | 12 | 75,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-23 | SAS @ SAC | 27,6 % | 123 : 107 | ✓ |
| 2026-11-23 | UTA @ LAL | 90,3 % | 94 : 109 | ✓ |
| 2026-11-23 | LAC @ HOU | 81,4 % | 104 : 116 | ✓ |
| 2026-11-23 | PHX @ NOP | 32,9 % | 123 : 119 | ✓ |
| 2026-11-23 | CLE @ CHI | 31,7 % | 108 : 122 | ✗ |
| 2026-11-23 | BKN @ MIN | 87,0 % | 116 : 142 | ✓ |
| 2026-11-23 | MIL @ TOR | 79,4 % | 116 : 111 | ✗ |
| 2026-11-23 | OKC @ IND | 25,9 % | 120 : 125 | ✗ |
| 2026-11-23 | POR @ PHI | 55,5 % | 128 : 111 | ✗ |
| 2026-11-23 | MEM @ CHA | 58,5 % | 117 : 111 | ✗ |
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
