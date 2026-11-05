# Ostrá prevádzka: vyhodnotenie predpovedí

Základná časť: 2026-10-20 – 2026-11-05 · uložené predpovede 123 · s výsledkom 121 · čaká na výsledok 2

Odohrané zápasy bez uloženej predpovede: **0**

| | Ostrá prevádzka | Backtest v1 |
|:--|--:|--:|
| Zápasy | 121 | sezóny 2023/24 – 2025/26 |
| Presnosť | 63,6 % (± 8,6 p. b.) | 67,3 % |
| Log loss | 0,6273 | 0,5996 |
| Brier | 0,2208 | 0,2068 |

Log loss a Brier: nižšie = lepšie. ± je 95 % interval presnosti; pri ~100 zápasoch je asi ±9 p. b., férové porovnanie s backtestom až okolo 500 zápasov.

## Kalibrácia

Keď model dá favoritovi X %, vyhrá favorit naozaj približne X %?

| Pásmo | Zápasy | Predpoveď | Skutočnosť |
|:--|--:|--:|--:|
| 50 – 60 % | 28 | 55,6 % | 60,7 % |
| 60 – 70 % | 38 | 64,7 % | 42,1 % |
| 70 – 80 % | 29 | 73,4 % | 72,4 % |
| 80 – 90 % | 22 | 83,9 % | 86,4 % |
| 90 – 100 % | 4 | 91,8 % | 100,0 % |

## Podľa istoty

| Istota | Zápasy | Presnosť |
|:--|--:|--:|
| vysoká | 118 | 63,6 % |
| nízka | 3 | 66,7 % |

## Posledné zápasy

| Dátum | Zápas | Šanca domácich | Skóre | Tip |
|:--|:--|--:|:--|:--|
| 2026-11-04 | MIA @ LAC | 50,4 % | 117 : 116 | ✗ |
| 2026-11-04 | LAL @ SAC | 26,2 % | 116 : 103 | ✓ |
| 2026-11-04 | DAL @ SAS | 85,5 % | 111 : 112 | ✓ |
| 2026-11-04 | POR @ PHX | 47,3 % | 132 : 119 | ✓ |
| 2026-11-04 | TOR @ DEN | 72,6 % | 109 : 128 | ✓ |
| 2026-11-04 | MIN @ HOU | 74,5 % | 117 : 107 | ✗ |
| 2026-11-04 | CLE @ OKC | 66,2 % | 116 : 124 | ✓ |
| 2026-11-04 | UTA @ NOP | 71,0 % | 113 : 120 | ✓ |
| 2026-11-04 | IND @ MEM | 72,3 % | 107 : 103 | ✗ |
| 2026-11-04 | CHI @ NYK | 90,2 % | 105 : 135 | ✓ |
| 2026-11-04 | CHA @ BKN | 33,9 % | 104 : 114 | ✗ |
| 2026-11-04 | MIL @ BOS | 74,9 % | 102 : 109 | ✓ |
| 2026-11-04 | ATL @ WAS | 45,3 % | 120 : 105 | ✓ |
| 2026-11-04 | PHI @ DET | 58,9 % | 112 : 106 | ✗ |
| 2026-11-02 | MIA @ LAL | 65,5 % | 117 : 138 | ✓ |
| 2026-11-02 | TOR @ LAC | 55,5 % | 125 : 118 | ✗ |
| 2026-11-02 | PHX @ GSW | 55,5 % | 113 : 116 | ✓ |
| 2026-11-02 | POR @ DEN | 74,3 % | 118 : 110 | ✗ |
| 2026-11-02 | UTA @ SAS | 92,0 % | 97 : 119 | ✓ |
| 2026-11-02 | BOS @ HOU | 70,4 % | 93 : 109 | ✓ |

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
