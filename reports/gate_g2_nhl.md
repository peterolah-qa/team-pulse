# Brána G2 – NHL: ✅ SPLNENÁ

Obdobie 13. 10. – 26. 10. 2026 (dni v USA), kritériá `docs/gate-nhl-G2.md`. Stav k 28. 10. 2026.
Vytvorené skriptom `team_pulse.gate_g2` (nezávislý prepočet z archívu, nie z reportu).

| Kritérium | | Stav |
|:--|:-:|:--|
| 1. Tip zamknutý pred začiatkom | ✅ | 98 z 98 zápasov v rozpise NHL |
| 2. Zápas dohratý a vyhodnotený v reporte | ✅ | 98 z 98 zápasov |
| 3. Prepočet = report | ✅ | 109 zápasov, vyšlo 63, log loss 0,6730 |
| 4. Log loss ≤ 0,7101 | ✅ | 0,6686 (98 zápasov) |

| | Obdobie G2 |
|:--|--:|
| Zápasy s výsledkom | 98 |
| Tip vyšiel | 59 (60,2 %) |
| Log loss modelu | 0,6686 (hranica 0,7101) |
| Log loss baseline „vždy domáci“ (54,3 %) | 0,6774 |
