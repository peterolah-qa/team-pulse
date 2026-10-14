# F1 – backtest (brána G0-F1)

Kritériá: docs/gate-f1-G0.md (stanovené 14. 10. 2026 pred meraním). Tip po kvalifikácii,
hodnotí sa víťaz. Tréning 2014 – 2025 (252 pretekov, 2014 rozbeh Ela), test 2026 kolá 1 – 17
(17 pretekov). Dáta: Jolpica-F1 (CC BY-NC-SA 4.0).

## Test: 2026 kolá 1 – 17

| Model | Presnosť (favorit vyhral) | Log loss víťaza | Brier pódia |
|---|---|---|---|
| model | 58,8 % | 1,2009 | 0,0694 |
| kvalifikácia | 70,6 % | 1,1473 | 0,0705 |
| šampionát | 35,3 % | 1,8677 | 0,0980 |

Rozdiel oproti lepšej baseline: **-0,0537** (hranica 0,0005) →
**kritérium nesplnené**.

## Staré pravidlá: 2023 – 2025 (len zápis)

Váhy z 2015 – 2022, preto sú tieto sezóny pre model neznáme.

| Model | Presnosť | Log loss víťaza | Brier pódia |
|---|---|---|---|
| model | 65,7 % | 1,0227 | 0,0678 |
| kvalifikácia | 61,4 % | 1,3101 | 0,0716 |
| šampionát | 47,1 % | 1,6296 | 0,0917 |

## Model

Elo jazdca K 48, Elo tímu K 8, prenos do novej sezóny 0.5
(vybrané na 2023 – 2025 z 100 kombinácií). Váhy logitu (2015 – 2025):
kvalifikácia 0,779, Elo jazdca 1,373, Elo tímu -0,456 (na 100 Elo).

## Preteky 2026

| Kolo | Veľká cena | Favorit modelu | Víťaz | Šanca víťaza |
|---|---|---|---|---|
| 1 | Australian | RUS 65,1 % | RUS (kval. 1.) | 65,1 % |
| 2 | Chinese | RUS 39,8 % | ANT (kval. 1.) | 26,4 % |
| 3 | Japanese | RUS 41,7 % | ANT (kval. 1.) | 30,8 % |
| 4 | Miami | ANT 34,2 % | ANT (kval. 1.) | 34,2 % |
| 5 | Canadian | RUS 62,0 % | ANT (kval. 2.) | 14,6 % |
| 6 | Monaco | ANT 44,1 % | ANT (kval. 1.) | 44,1 % |
| 7 | Barcelona | RUS 46,4 % | HAM (kval. 2.) | 21,9 % |
| 8 | Austrian | RUS 53,1 % | RUS (kval. 1.) | 53,1 % |
| 9 | British | ANT 49,7 % | LEC (kval. 2.) | 14,5 % |
| 10 | Belgian | ANT 43,1 % | ANT (kval. 1.) | 43,1 % |
| 11 | Hungarian | NOR 34,4 % | NOR (kval. 1.) | 34,4 % |
| 12 | Dutch | NOR 42,5 % | NOR (kval. 1.) | 42,5 % |
| 13 | Italian | RUS 37,8 % | ANT (kval. 7.) | 2,8 % |
| 14 | Spanish | NOR 44,5 % | ANT (kval. 2.) | 28,4 % |
| 15 | Azerbaijan | RUS 58,8 % | RUS (kval. 1.) | 58,8 % |
| 16 | Bahrain in Malaysia | VER 48,7 % | VER (kval. 1.) | 48,7 % |
| 17 | Singapore | VER 48,7 % | VER (kval. 1.) | 48,7 % |
