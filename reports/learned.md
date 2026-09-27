# Naučené váhy – vrstva A + C

Tréning: sezóny 2003/04 – 2022/23 (25672 zápasov). Test: 2023/24 – 2025/26 (3931 zápasov), ktoré model pri učení nevidel.

## Porovnanie na testovacích sezónach

| model                                |    n | accuracy   |   log_loss |   brier |
|:-------------------------------------|-----:|:-----------|-----------:|--------:|
| A: Elo (HCA 70)                      | 3931 | 66.4 %     |     0.6108 |  0.2116 |
| A kalibrované (naučené Elo + domáci) | 3931 | 66.3 %     |     0.6115 |  0.2119 |
| A + C (naučené Elo + únava)          | 3931 | 66.8 %     |     0.6081 |  0.2104 |

## Naučené váhy v Elo bodoch

Kladné = pomáha domácim, záporné = pomáha hosťom. `home_*` sa týka domácich, `away_*` hostí.
Príklad: `away_b2b = +20` znamená, že back-to-back hostí dá domácim výhodu 20 Elo.

|                |   Elo |
|:---------------|------:|
| home           |  61.3 |
| home_rest      |   2.1 |
| home_b2b       | -34.1 |
| home_three_in4 |  -5.8 |
| home_km        |   2.9 |
| home_tz_east   | -12.4 |
| home_road      |   0   |
| away_rest      |   0   |
| away_b2b       |  43.4 |
| away_three_in4 |   7   |
| away_km        |  -0.4 |
| away_tz_east   |  -4.9 |
| away_road      |  -4.1 |
| away_altitude  |  35   |

## Kalibrácia pred (čisté Elo)

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1198 | 55.0 %      | 54.8 %       |
| (0.6, 0.7]   |     1128 | 64.9 %      | 63.0 %       |
| (0.7, 0.8]   |      923 | 74.7 %      | 71.4 %       |
| (0.8, 0.9]   |      577 | 84.3 %      | 85.1 %       |
| (0.9, 1.0]   |      105 | 92.3 %      | 88.6 %       |

## Kalibrácia po (A + C)

| band         |   zapasy | predpoved   | skutocnost   |
|:-------------|---------:|:------------|:-------------|
| (0.499, 0.6] |     1245 | 55.0 %      | 57.0 %       |
| (0.6, 0.7]   |     1133 | 64.9 %      | 61.4 %       |
| (0.7, 0.8]   |      910 | 74.9 %      | 73.3 %       |
| (0.8, 0.9]   |      546 | 84.2 %      | 85.0 %       |
| (0.9, 1.0]   |       97 | 92.3 %      | 91.8 %       |
