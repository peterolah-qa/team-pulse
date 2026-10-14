# Referencia pre brány G2 (14 dní ostrej prevádzky)

Vypočítané 14. 10. 2026 skriptom `scripts/g2_reference.py` z backtestu: model naučený len na
tréningových sezónach, hodnotí sa základná časť testovacích sezón 2023/24 – 2025/26.

## NBA

Baseline „vždy domáci“: domáci vyhrávajú 58,7 % zápasov (tréningové sezóny).

| obdobie | zápasy | log loss modelu | log loss baseline | presnosť |
|:--|--:|--:|--:|--:|
| celé testovacie sezóny | 3680 | 0,5967 | 0,6919 | 67,7 % |
| prvých 14 dní 2023/24 (od 24. 10.) | 103 | 0,6198 | 0,6795 | 61,2 % |
| prvých 14 dní 2024/25 (od 22. 10.) | 107 | 0,6484 | 0,7103 | 60,7 % |
| prvých 14 dní 2025/26 (od 21. 10.) | 102 | 0,6339 | 0,6844 | 63,7 % |
| začiatky sezón spolu | 312 | 0,6342 | 0,6917 | 61,9 % |

**14-dňové okná** základnej časti testovacích sezón: 483 okien, medián 103 zápasov na okno.

- Log loss modelu: 5. percentil 0,5014, medián 0,6034, **95. percentil 0,6739** (hranica „model nie je pokazený“).
- Presnosť: 5. percentil 58,1 %, medián 67,2 %, 95. percentil 78,5 %.
- Model prehral s baseline „vždy domáci“ v 3,1 % okien. Toľko by podmienku „porazí baseline za 14 dní“ nesplnil aj dobrý model, preto nie je kritériom brány.

## NHL

Baseline „vždy domáci“: domáci vyhrávajú 54,3 % zápasov (tréningové sezóny).

| obdobie | zápasy | log loss modelu | log loss baseline | presnosť |
|:--|--:|--:|--:|--:|
| celé testovacie sezóny | 3936 | 0,6713 | 0,6896 | 57,6 % |
| prvých 14 dní 2023/24 (od 10. 10.) | 82 | 0,6605 | 0,6863 | 58,5 % |
| prvých 14 dní 2024/25 (od 04. 10.) | 70 | 0,6764 | 0,6895 | 55,7 % |
| prvých 14 dní 2025/26 (od 07. 10.) | 97 | 0,6643 | 0,6924 | 59,8 % |
| začiatky sezón spolu | 249 | 0,6664 | 0,6896 | 58,2 % |

**14-dňové okná** základnej časti testovacích sezón: 535 okien, medián 103 zápasov na okno.

- Log loss modelu: 5. percentil 0,6283, medián 0,6697, **95. percentil 0,7101** (hranica „model nie je pokazený“).
- Presnosť: 5. percentil 49,1 %, medián 58,0 %, 95. percentil 65,4 %.
- Model prehral s baseline „vždy domáci“ v 24,5 % okien. Toľko by podmienku „porazí baseline za 14 dní“ nesplnil aj dobrý model, preto nie je kritériom brány.
