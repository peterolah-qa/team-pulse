# NHL – návrh vrstvy C (únava z rozpisu)

Elo z brány G0-NHL (K 6, domáca výhoda 30, prenos 0.8). Tréning do 2022/23 (17676 zápasov), test 2023/24 – 2025/26 (3936 zápasov základnej časti, model ich nevidel).

## Rozhodnutie: ✅ zlepšuje, navrhujem pridať

Kritérium: log loss s únavou o ≥ 0,0005 nižší než bez nej.

Bez únavy 0,6730 · s únavou 0,6713 · rozdiel 0,0017

## Porovnanie na testovacích sezónach

| model                        |   zápasy | presnosť   | log loss   | Brier   |
|:-----------------------------|---------:|:-----------|:-----------|:--------|
| A: Elo                       |     3936 | 57,2 %     | 0,6730     | 0,2402  |
| A kalibrované (Elo + domáci) |     3936 | 57,2 %     | 0,6732     | 0,2403  |
| A + C (+ únava)              |     3936 | 57,6 %     | 0,6713     | 0,2394  |

## Naučené váhy v Elo bodoch

Kladné = pomáha domácim, záporné = pomáha hosťom.

| príznak                                   |   Elo |
|:------------------------------------------|------:|
| domáca výhoda (len mimo neutrálneho ľadu) |  20.5 |
| domáci: dni oddychu                       |  -5.4 |
| domáci: back-to-back                      | -48.5 |
| domáci: 3. zápas za 4 dni                 |  -9.4 |
| domáci: posun na východ (h)               |  -4.2 |
| hostia: dni oddychu                       |   1.2 |
| hostia: back-to-back                      |  34.4 |
| hostia: 3. zápas za 4 dni                 |   3.7 |
| hostia: posun na východ (h)               |  -2   |
| hostia: poradie zápasu na výjazde         |   2.1 |

Back-to-back má v teste 15,1 % klubov v zápase, 3. zápas za 4 dni 18,5 %.

## Kalibrácia pred (čisté Elo)

| pásmo        |   zápasy | predpoveď   | skutočnosť   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     2427 | 54,7 %      | 52,5 %       |
| (0.6, 0.7]   |     1225 | 64,2 %      | 62,8 %       |
| (0.7, 0.8]   |      280 | 73,6 %      | 72,9 %       |
| (0.8, 0.9]   |        4 | 81,7 %      | 75,0 %       |

## Kalibrácia po (A + C)

| pásmo        |   zápasy | predpoveď   | skutočnosť   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     2368 | 54,7 %      | 52,7 %       |
| (0.6, 0.7]   |     1229 | 64,3 %      | 62,6 %       |
| (0.7, 0.8]   |      321 | 73,5 %      | 72,9 %       |
| (0.8, 0.9]   |       18 | 81,1 %      | 88,9 %       |
