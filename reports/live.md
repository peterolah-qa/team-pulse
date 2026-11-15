# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-15 · uložené predpovede 197 · s výsledkom 188 · čaká na výsledok 9

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 188 | sezóny 2023/24 – 2025/26 |
| Presnosť | 68,1 % (± 6,7 p. b.) | 67,3 % |
| Log loss | 0,5960 | 0,5996 |
| Brier | 0,2060 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 45 | 55,6 % | 60,0 % |
| 60 – 70 % | 57 | 64,8 % | 52,6 % |
| 70 – 80 % | 46 | 74,2 % | 78,3 % |
| 80 – 90 % | 33 | 83,8 % | 84,8 % |
| 90 – 100 % | 7 | 92,1 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 182 | 67,6 % |
| stredná | 1 | 100,0 % |
| nízka | 5 | 80,0 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-14 | CHI @ MIN | 87,9 % | 117 : 106 | ✗ |
| 2026-11-14 | BKN @ MEM | 66,5 % | 110 : 129 | ✓ |
| 2026-11-14 | DET @ MIA | 40,4 % | 117 : 137 | ✗ |
| 2026-11-14 | DAL @ CLE | 51,7 % | 117 : 127 | ✓ |
| 2026-11-14 | DEN @ NOP | 17,1 % | 116 : 108 | ✓ |
| 2026-11-13 | OKC @ LAC | 34,3 % | 112 : 113 | ✗ |
| 2026-11-13 | POR @ SAC | 30,6 % | 120 : 107 | ✓ |
| 2026-11-13 | GSW @ SAS | 84,4 % | 85 : 123 | ✓ |
| 2026-11-13 | UTA @ HOU | 93,0 % | 118 : 125 | ✓ |
| 2026-11-13 | MEM @ NOP | 49,7 % | 142 : 111 | ✓ |
| 2026-11-13 | ATL @ CHI | 32,6 % | 117 : 125 | ✗ |
| 2026-11-13 | CLE @ MIA | 52,4 % | 121 : 133 | ✓ |
| 2026-11-13 | MIL @ ORL | 75,5 % | 99 : 107 | ✓ |
| 2026-11-13 | NYK @ IND | 17,6 % | 104 : 106 | ✗ |
| 2026-11-12 | CHA @ PHX | 63,0 % | 96 : 101 | ✓ |
| 2026-11-12 | DAL @ MIN | 73,7 % | 94 : 133 | ✓ |
| 2026-11-12 | DET @ WAS | 20,0 % | 144 : 140 | ✓ |
| 2026-11-12 | TOR @ PHI | 72,1 % | 112 : 123 | ✓ |
| 2026-11-11 | OKC @ POR | 47,5 % | 108 : 118 | ✗ |
| 2026-11-11 | GSW @ HOU | 73,5 % | 108 : 115 | ✓ |

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
