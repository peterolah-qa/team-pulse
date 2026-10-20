# Brána G2 – NHL: predbežne: niečo neplatí

Obdobie 13. 10. – 26. 10. 2026 (dni v USA), kritériá `docs/gate-nhl-G2.md`. Stav k 20. 10. 2026, obdobie ešte beží – hodnotia sa dni do 19. 10.
Vytvorené skriptom `team_pulse.gate_g2` (nezávislý prepočet z archívu, nie z reportu).

| Kritérium | | Stav |
|:--|:-:|:--|
| 1. Tip zamknutý pred začiatkom | ✅ | 51 z 51 zápasov v rozpise NHL |
| 2. Zápas dohratý a vyhodnotený v reporte | ❌ | 51 z 51 zápasov |
| 3. Prepočet = report | ❌ | 51 zápasov, vyšlo 31, log loss 0,6449 |
| 4. Log loss ≤ 0,7101 | ✅ | 0,6449 (51 zápasov) |

| | Obdobie G2 |
|:--|--:|
| Zápasy s výsledkom | 51 |
| Tip vyšiel | 31 (60,8 %) |
| Log loss modelu | 0,6449 (hranica 0,7101) |
| Log loss baseline „vždy domáci“ (54,3 %) | 0,6747 |

## Problémy

- 2. Zápas dohratý a vyhodnotený v reporte: 19. 10.: prepočet (4, 3), report None
- 3. Prepočet = report: Spolu: prepočet (31, 51, '0,6449'), report (28, 47, '0,6454')
- 3. Prepočet = report: 19. 10.: prepočet (4, 3), report None
