# Naučené váhy

Tréning: sezóny 2003/04 – 2022/23 (25672 zápasov). Test: 2023/24 – 2025/26 (3931 zápasov), ktoré model pri učení nevidel.

## Porovnanie na testovacích sezónach

| model                                |    n | accuracy   |   log_loss |   brier |
|:-------------------------------------|-----:|:-----------|-----------:|--------:|
| A: Elo (HCA 70)                      | 3931 | 66.4 %     |     0.6108 |  0.2116 |
| A kalibrované (naučené Elo + domáci) | 3931 | 66.3 %     |     0.6115 |  0.2119 |
| A + C (naučené Elo + únava)          | 3931 | 66.8 %     |     0.6081 |  0.2104 |
| A + B + C (+ chýbajúci hráči)        | 3931 | 67.3 %     |     0.6039 |  0.2087 |

## Naučené váhy v Elo bodoch – A + B + C (+ chýbajúci hráči)

Kladné = pomáha domácim, záporné = pomáha hosťom. `home_*` sa týka domácich, `away_*` hostí.
Príklad: `away_b2b = +20` znamená, že back-to-back hostí dá domácim výhodu 20 Elo.
`*_missing` = Elo za 1 bod PIE chýbajúcej kvality (hviezda na 36 min. ≈ 5–7 bodov).

|                |   Elo |
|:---------------|------:|
| home           |  57.1 |
| home_missing   | -27.9 |
| away_missing   |  26.9 |
| home_rest      |   1.7 |
| home_b2b       | -31.2 |
| home_three_in4 |  -5.6 |
| home_km        |   3   |
| home_tz_east   | -11.5 |
| home_road      |   0   |
| away_rest      |   0.5 |
| away_b2b       |  40.1 |
| away_three_in4 |   5.5 |
| away_km        |   0.8 |
| away_tz_east   |  -6   |
| away_road      |  -3.7 |
| away_altitude  |  31.9 |

## Kalibrácia pred (čisté Elo)

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1198 | 55.0 %      | 54.8 %       |
| (0.6, 0.7]   |     1128 | 64.9 %      | 63.0 %       |
| (0.7, 0.8]   |      923 | 74.7 %      | 71.4 %       |
| (0.8, 0.9]   |      577 | 84.3 %      | 85.1 %       |
| (0.9, 1.0]   |      105 | 92.3 %      | 88.6 %       |

## Kalibrácia po (A + B + C (+ chýbajúci hráči))

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1198 | 55.0 %      | 57.3 %       |
| (0.6, 0.7]   |     1080 | 64.9 %      | 61.7 %       |
| (0.7, 0.8]   |      943 | 74.8 %      | 72.3 %       |
| (0.8, 0.9]   |      594 | 84.5 %      | 84.8 %       |
| (0.9, 1.0]   |      116 | 92.2 %      | 92.2 %       |
