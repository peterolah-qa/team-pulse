# F1 – model B (návrh po G0-F1, orientačne)

Elo vynulované pri zmene technických pravidiel (2017, 2022, 2026), inak rovnako ako model A.
**Test 2026 kolá 1 – 17 sme po G0-F1 už videli – čísla nižšie nie sú dôkaz ani brána.**
Rozhodne ostré meranie na 6 zostávajúcich pretekoch 2026 (docs/gate-f1-shadow.md).

Kritériá: docs/gate-f1-G0.md (stanovené 14. 10. 2026 pred meraním). Tip po kvalifikácii,
hodnotí sa víťaz. Tréning 2014 – 2025 (252 pretekov, 2014 rozbeh Ela), test 2026 kolá 1 – 17
(17 pretekov). Dáta: Jolpica-F1 (CC BY-NC-SA 4.0).

## Test: 2026 kolá 1 – 17

| Model | Presnosť (favorit vyhral) | Log loss víťaza | Brier pódia |
|---|---|---|---|
| model | 64,7 % | 1,1061 | 0,0695 |
| kvalifikácia | 70,6 % | 1,1473 | 0,0705 |
| šampionát | 35,3 % | 1,8677 | 0,0980 |

Rozdiel oproti lepšej baseline: **0,0411** (hranica 0,0005) →
**orientačne, nie kritérium**.

## Staré pravidlá: 2023 – 2025 (len zápis)

Váhy z 2015 – 2022, preto sú tieto sezóny pre model neznáme.

| Model | Presnosť | Log loss víťaza | Brier pódia |
|---|---|---|---|
| model | 65,7 % | 1,0278 | 0,0679 |
| kvalifikácia | 61,4 % | 1,3101 | 0,0716 |
| šampionát | 47,1 % | 1,6296 | 0,0917 |

## Model

Elo jazdca K 48, Elo tímu K 8, prenos do novej sezóny 0.5
(vybrané na 2023 – 2025 z 100 kombinácií). Váhy logitu (2015 – 2025):
kvalifikácia 0,805, Elo jazdca 1,455, Elo tímu -0,909 (na 100 Elo).

## Preteky 2026

| Kolo | Veľká cena | Favorit modelu | Víťaz | Šanca víťaza |
|---|---|---|---|---|
| 1 | Australian | RUS 42,5 % | RUS (kval. 1.) | 42,5 % |
| 2 | Chinese | ANT 43,8 % | ANT (kval. 1.) | 43,8 % |
| 3 | Japanese | ANT 50,2 % | ANT (kval. 1.) | 50,2 % |
| 4 | Miami | ANT 54,9 % | ANT (kval. 1.) | 54,9 % |
| 5 | Canadian | RUS 48,7 % | ANT (kval. 2.) | 27,9 % |
| 6 | Monaco | ANT 61,5 % | ANT (kval. 1.) | 61,5 % |
| 7 | Barcelona | RUS 31,2 % | HAM (kval. 2.) | 28,9 % |
| 8 | Austrian | RUS 41,7 % | RUS (kval. 1.) | 41,7 % |
| 9 | British | ANT 58,5 % | LEC (kval. 2.) | 10,6 % |
| 10 | Belgian | ANT 57,5 % | ANT (kval. 1.) | 57,5 % |
| 11 | Hungarian | HAM 41,4 % | NOR (kval. 1.) | 27,7 % |
| 12 | Dutch | NOR 38,6 % | NOR (kval. 1.) | 38,6 % |
| 13 | Italian | GAS 28,3 % | ANT (kval. 7.) | 3,3 % |
| 14 | Spanish | NOR 38,9 % | ANT (kval. 2.) | 36,6 % |
| 15 | Azerbaijan | RUS 53,5 % | RUS (kval. 1.) | 53,5 % |
| 16 | Bahrain in Malaysia | VER 37,8 % | VER (kval. 1.) | 37,8 % |
| 17 | Singapore | VER 40,7 % | VER (kval. 1.) | 40,7 % |
