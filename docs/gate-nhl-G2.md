# Brána G2-NHL: 14 dní ostrej prevádzky (stanovené vopred, 14. 10. 2026)

Obdobie: zápasy základnej časti s dátumom **13. 10. – 26. 10. 2026** (dni v USA, ET). Prvé tipy
boli zamknuté 13. 10. o 16:55 (náš čas), 7 h pred prvým zápasom. Vyhodnotenie: ráno 27. 10. 2026.
Počas obdobia sa model NHL (`models/nhl_v1.json`) nemení.

Hranice sú stanovené z backtestu (`scripts/g2_reference.py` → `reports/g2_reference.md`) a počas
obdobia sa nemenia.

## Prečo takto

Hokej je náhodnejší než basketbal. V 14-dňových oknách backtestu model prehral s baseline
„vždy domáci“ v 24,5 % okien, hoci za celé sezóny je jasne lepší (0,6713 oproti 0,6896).
Podmienka „porazí baseline za 14 dní“ by teda bola lotéria a nie je kritériom. Brána overuje
bezchybnú prevádzku a to, že model nie je pokazený.

## Kritériá – všetky musia platiť

**Prevádzka (bez výnimky)**

1. Každý zápas základnej časti z obdobia (podľa rozpisu NHL) má v `archive/nhl/predictions/`
   tip zamknutý pred začiatkom zápasu.
2. Každý z týchto zápasov je vyhodnotený v `reports/nhl_live.md` s výsledkom podľa API NHL.
3. Nezávislý prepočet z archívu (počet zápasov, trafené tipy, log loss) sa zhoduje s reportom.

**Model (hranica z backtestu)**

4. Log loss modelu za obdobie ≤ **0,7101**. To je 95. percentil log loss v 14-dňových oknách
   základnej časti testovacích sezón 2023/24 – 2025/26 (535 okien). Všetky tri začiatky sezón
   v backteste boli pod hranicou (0,660 / 0,676 / 0,664).

Presnosť a porovnanie s baseline „vždy domáci“ (54,3 %) sa len zapíšu. V backteste mala presnosť
v 14-dňových oknách 49,1 – 65,4 %, medián 58,0 %.

## Po bráne

Prejde → NHL v appke stratí označenie beta. Neprejde → zapíše sa príčina, oprava, nové meranie
14 dní, NHL ostáva v appke ako beta.
