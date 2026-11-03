# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-02 · uložené predpovede 107 · s výsledkom 107 · čaká na výsledok 0

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 107 | sezóny 2023/24 – 2025/26 |
| Presnosť | 63,6 % (± 9,1 p. b.) | 67,3 % |
| Log loss | 0,6300 | 0,5996 |
| Brier | 0,2218 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 24 | 55,9 % | 62,5 % |
| 60 – 70 % | 36 | 64,6 % | 41,7 % |
| 70 – 80 % | 23 | 73,5 % | 73,9 % |
| 80 – 90 % | 21 | 83,8 % | 85,7 % |
| 90 – 100 % | 3 | 92,3 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 104 | 63,5 % |
| nízka | 3 | 66,7 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-02 | MIA @ LAL | 65,5 % | 117 : 138 | ✓ |
| 2026-11-02 | TOR @ LAC | 55,5 % | 125 : 118 | ✗ |
| 2026-11-02 | PHX @ GSW | 55,5 % | 113 : 116 | ✓ |
| 2026-11-02 | POR @ DEN | 74,3 % | 118 : 110 | ✗ |
| 2026-11-02 | UTA @ SAS | 92,0 % | 97 : 119 | ✓ |
| 2026-11-02 | BOS @ HOU | 70,4 % | 93 : 109 | ✓ |
| 2026-11-02 | MIL @ MIN | 81,0 % | 100 : 112 | ✓ |
| 2026-11-02 | NOP @ MEM | 59,1 % | 135 : 134 | ✗ |
| 2026-11-02 | SAC @ DAL | 69,4 % | 115 : 100 | ✗ |
| 2026-11-02 | CHI @ PHI | 84,7 % | 107 : 126 | ✓ |
| 2026-11-02 | WAS @ ORL | 69,6 % | 103 : 94 | ✗ |
| 2026-11-02 | BKN @ NYK | 94,5 % | 90 : 103 | ✓ |
| 2026-11-02 | ATL @ IND | 28,7 % | 108 : 104 | ✓ |
| 2026-11-02 | DET @ CHA | 41,7 % | 124 : 91 | ✓ |
| 2026-11-02 | OKC @ CLE | 51,6 % | 117 : 112 | ✗ |
| 2026-11-01 | TOR @ LAL | 70,1 % | 125 : 131 | ✓ |
| 2026-11-01 | LAC @ GSW | 52,7 % | 112 : 124 | ✓ |
| 2026-11-01 | BKN @ IND | 63,1 % | 98 : 90 | ✗ |
| 2026-11-01 | BOS @ ORL | 41,5 % | 108 : 97 | ✓ |
| 2026-10-31 | OKC @ HOU | 53,0 % | 98 : 119 | ✓ |

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
