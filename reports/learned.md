# Naučené váhy

Tréning: sezóny 2003/04 – 2022/23 (25672 zápasov). Test: 2023/24 – 2025/26 (3931 zápasov), ktoré model pri učení nevidel.

## Porovnanie na testovacích sezónach

| model                                |    n | accuracy   |   log_loss |   brier |
|:-------------------------------------|-----:|:-----------|-----------:|--------:|
| A: Elo (HCA 70)                      | 3931 | 66.4 %     |     0.6108 |  0.2116 |
| A kalibrované (naučené Elo + domáci) | 3931 | 66.3 %     |     0.6115 |  0.2119 |
| A + C (naučené Elo + únava)          | 3931 | 66.8 %     |     0.6081 |  0.2104 |
| A + B + C (+ chýbajúci hráči)        | 3931 | 67.3 %     |     0.6039 |  0.2087 |
| A + B + C + sila súpisky             | 3931 | 67.3 %     |     0.5996 |  0.2068 |

## Naučené váhy v Elo bodoch – A + B + C + sila súpisky

Kladné = pomáha domácim, záporné = pomáha hosťom. `home_*` sa týka domácich, `away_*` hostí.
Príklad: `away_b2b = +20` znamená, že back-to-back hostí dá domácim výhodu 20 Elo.
`*_missing` = Elo za 1 bod PIE chýbajúcej kvality (hviezda na 36 min. ≈ 5–7 bodov).

|                |   Elo |
|:---------------|------:|
| home           |  69.9 |
| home_missing   | -24.2 |
| away_missing   |  22.4 |
| strength_diff  |  11.1 |
| home_rest      |   1.9 |
| home_b2b       | -35.7 |
| home_three_in4 |  -5.9 |
| home_km        |   3.6 |
| home_tz_east   | -14.4 |
| home_road      |   0   |
| away_rest      |   0.5 |
| away_b2b       |  47.3 |
| away_three_in4 |   6.8 |
| away_km        |   0.9 |
| away_tz_east   |  -7.3 |
| away_road      |  -4.9 |
| away_altitude  |  47.2 |

## Kalibrácia pred (čisté Elo)

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1198 | 55.0 %      | 54.8 %       |
| (0.6, 0.7]   |     1128 | 64.9 %      | 63.0 %       |
| (0.7, 0.8]   |      923 | 74.7 %      | 71.4 %       |
| (0.8, 0.9]   |      577 | 84.3 %      | 85.1 %       |
| (0.9, 1.0]   |      105 | 92.3 %      | 88.6 %       |

## Kalibrácia po (A + B + C + sila súpisky)

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1168 | 54.8 %      | 55.1 %       |
| (0.6, 0.7]   |     1114 | 64.9 %      | 62.7 %       |
| (0.7, 0.8]   |      924 | 74.6 %      | 74.6 %       |
| (0.8, 0.9]   |      608 | 84.3 %      | 82.9 %       |
| (0.9, 1.0]   |      117 | 91.8 %      | 94.0 %       |
