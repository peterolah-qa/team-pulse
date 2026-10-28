# Brána G2-NFL: ostré tipy do konca základnej časti (stanovené vopred, 28. 10. 2026)

Petrovo rozhodnutie 28. 10. 2026: ostré tipy čo najskôr – **od týždňa 8**, G2 meria čisté Elo z brány G0-NFL.
Vrstva quarterback sa robí popri tom; ak ju Peter schváli, od týždňa 10 sa ku každému zápasu zamyká aj druhý
tip (Elo + quarterback) s vlastnou bránou. Táto brána sa tým nemení.

Obdobie: zápasy základnej časti s výkopom **29. 10. 2026 – 10. 1. 2027** (týždne 8 – 18, ~165 zápasov).
Vyhodnotenie: po poslednom zápase základnej časti, keď ho má nflverse games.csv.
Počas obdobia sa model `nfl-elo-v1` (`team_pulse.nfl.predict.PARAMS`: K 20, výhoda domáceho 48, prenos 0,6,
play-off × 1,2) nemení.

Kritériá sú stanovené pred prvým ostrým tipom a počas obdobia sa nemenia.

## Kritériá – všetky musia platiť

**Prevádzka (bez výnimky)**

1. Každý zápas základnej časti z obdobia (podľa games.csv) má v `archive/nfl/predictions/` tip zamknutý
   pred výkopom (`locked_at` < `kickoff_utc`). Zrušený zápas (bez výsledku a bez náhradného termínu)
   sa nepočíta.
2. Každý dohraný zápas obdobia je vyhodnotený v `reports/nfl_live.md` (remíza sa nevyhodnocuje).
3. Nezávislý prepočet z archívu a games.csv (počet zápasov, trafené tipy, log loss) sa zhoduje s reportom.

**Model (hranica z backtestu)**

4. Log loss modelu za obdobie ≤ **0,6620**. To je 95. percentil log loss v oknách 165 po sebe idúcich
   zápasov základnej časti testovacích sezón 2023 – 2025 (323 okien, rovnaké Elo ako v G0, medián 0,6367).
   Týždne 8 – 18 testovacích sezón boli všetky pod hranicou (0,6563 / 0,5740 / 0,6323).

Presnosť a porovnanie s baseline „vždy domáci“ a „lepšia bilancia“ sa len zapíšu.

## Po bráne

Prejde → NFL v appke bez označenia beta (do appky ide po jadre). Neprejde → zapíše sa príčina, oprava
a nové meranie.
