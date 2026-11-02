# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-02 · uložené predpovede 107 · s výsledkom 92 · čaká na výsledok 15

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 92 | sezóny 2023/24 – 2025/26 |
| Presnosť | 64,1 % (± 9,8 p. b.) | 67,3 % |
| Log loss | 0,6358 | 0,5996 |
| Brier | 0,2235 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 19 | 55,8 % | 68,4 % |
| 60 – 70 % | 33 | 64,3 % | 42,4 % |
| 70 – 80 % | 20 | 73,7 % | 75,0 % |
| 80 – 90 % | 19 | 83,9 % | 84,2 % |
| 90 – 100 % | 1 | 90,3 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 92 | 64,1 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-01 | TOR @ LAL | 70,1 % | 125 : 131 | ✓ |
| 2026-11-01 | LAC @ GSW | 52,7 % | 112 : 124 | ✓ |
| 2026-11-01 | BKN @ IND | 63,1 % | 98 : 90 | ✗ |
| 2026-11-01 | BOS @ ORL | 41,5 % | 108 : 97 | ✓ |
| 2026-10-31 | OKC @ HOU | 53,0 % | 98 : 119 | ✓ |
| 2026-10-31 | MIN @ SAS | 80,5 % | 111 : 121 | ✓ |
| 2026-10-31 | CLE @ MIL | 27,3 % | 136 : 111 | ✓ |
| 2026-10-31 | SAC @ MEM | 64,8 % | 105 : 136 | ✓ |
| 2026-10-31 | ATL @ NOP | 38,4 % | 99 : 121 | ✗ |
| 2026-10-31 | PHI @ CHA | 64,3 % | 109 : 104 | ✗ |
| 2026-10-31 | POR @ UTA | 37,6 % | 112 : 90 | ✓ |
| 2026-10-30 | DEN @ PHX | 42,9 % | 127 : 120 | ✓ |
| 2026-10-30 | LAL @ GSW | 40,2 % | 95 : 112 | ✗ |
| 2026-10-30 | LAC @ MIN | 63,9 % | 101 : 127 | ✓ |
| 2026-10-30 | HOU @ DAL | 38,1 % | 111 : 116 | ✗ |
| 2026-10-30 | IND @ MIA | 81,1 % | 125 : 145 | ✓ |
| 2026-10-30 | ORL @ TOR | 65,6 % | 121 : 114 | ✗ |
| 2026-10-30 | NYK @ PHI | 37,2 % | 93 : 98 | ✗ |
| 2026-10-30 | DET @ BKN | 20,8 % | 110 : 94 | ✓ |
| 2026-10-30 | CHI @ BOS | 85,7 % | 111 : 125 | ✓ |

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
