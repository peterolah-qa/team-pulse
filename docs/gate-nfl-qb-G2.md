# Brána G2-NFL-QB: druhý model Elo + quarterback (stanovené vopred, 28. 10. 2026)

Peter 28. 10. 2026 schválil vrstvu quarterback „náhradník“ (`reports/nfl_qb.md`): tím, ktorý nastúpi s iným
quarterbackom než jeho bežný štartér (najčastejší v posledných 8 odohraných zápasoch), dostane −65 Elo
(naučené len na tréningu 2010 – 2022; na teste 2023 – 2025 log loss 0,63412 → 0,63050, presnosť 63,9 → 64,4 %).

Model `nfl-elo-qb-v1` sa zamyká **popri** `nfl-elo-v1` ako druhý tip k tomu istému zápasu
(`archive/nfl/qb/predictions/`, `reports/nfl_qb_live.md`). Brána G2-NFL čistého Ela (`docs/gate-nfl-G2.md`)
sa tým nemení. Quarterback v tipe je očakávaný štartér z games.csv v čase zamknutia; ak sa po zamknutí zmení,
tip sa nemení.

Obdobie: zápasy základnej časti s výkopom **12. 11. 2026 – 10. 1. 2027** (týždne 10 – 18, 136 zápasov).
Počas obdobia sa model (`team_pulse.nfl.predict.ELO_QB`, `team_pulse.nfl.qb`) nemení.

## Kritériá – všetky musia platiť

1. Každý zápas základnej časti z obdobia má v `archive/nfl/qb/predictions/` tip zamknutý pred výkopom.
2. Každý dohraný zápas obdobia je vyhodnotený v `reports/nfl_qb_live.md` (remíza sa nevyhodnocuje).
3. Nezávislý prepočet z archívu a games.csv sa zhoduje s reportom.
4. Log loss za obdobie ≤ **0,6602**: 95. percentil log loss v oknách 136 po sebe idúcich zápasov základnej časti
   testovacích sezón 2023 – 2025 s týmto modelom (410 okien, medián 0,6349). Týždne 10 – 18 testovacích sezón:
   0,6744 / 0,5599 / 0,6197 – **sezóna 2023 by hranicou neprešla**, takže neúspech je možný aj pri správnom modeli.

Porovnanie s čistým Elom na tých istých zápasoch sa zapíše (rozhoduje, ktorý model ide do appky).

## Po bráne

Prejde a je lepší než čisté Elo na tých istých zápasoch → do appky ide `nfl-elo-qb-v1`. Inak ostáva čisté Elo.
