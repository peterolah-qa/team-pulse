# Brána G0-NHL – vyhodnotenie (13. 10. 2026)

Kritérium (docs/sporty.md, stanovené pred meraním): log loss Ela na testovacích sezónach
2023/24 – 2025/26 o ≥ 0,0005 nižší než lepšia z baseline. Baseline aj parametre Ela
sa naučili len na tréningových sezónach.

| Kritérium | Cieľ | Výsledok | Stav |
|---|---|---|---|
| Úplnosť dát | každá sezóna presne podľa ligy | 2005/06 – 2025/26, 27 166 zápasov, všetky počty sedia | ✅ |
| Log loss Ela vs. lepšia baseline | rozdiel ≥ 0,0005 | 0,6730 vs. 0,6836 (rozdiel 0,0107) | ✅ |
| Test úniku dát | prechádza | prechádza, overené aj úmyselnou chybou | ✅ |
| Contract test rozpisu NHL | prechádza | skutočná odpoveď API z 13. 10. 2026 | ✅ |

**Rozhodnutie: brána G0-NHL splnená.**

## Výsledok na teste (3 936 zápasov základnej časti)

| Model | Presnosť | Log loss | Brier |
|---|---|---|---|
| Elo ladené na tréningu (K 6, domáca výhoda 30, prenos 0,8) | 57,2 % | 0,6730 | 0,2402 |
| Elo štart FiveThirtyEight (K 6, domáca výhoda 50, prenos 0,7) | 57,2 % | 0,6741 | 0,2407 |
| Baseline: lepšia bilancia | 55,4 % | 0,6836 | 0,2453 |
| Baseline: vždy domáci | 54,2 % | 0,6896 | 0,2482 |

## Zistenia

- Hokej je náhodnejší než basketbal: Elo 57,2 % (NBA 67,3 %). Domáci vyhrávajú len 54 %,
  22 % zápasov rozhodne predĺženie alebo nájazdy.
- Sezóna 2025/26 len 52,8 %: kluby sa oproti 2024/25 veľmi pohli (Toronto 52 → 32 výhier,
  Buffalo 36 → 50), Elo prenesené z minulej sezóny zavádzalo. Tipy budú kolísať viac ako pri NBA.
- Ladené parametre (domáca výhoda 30 namiesto 50, prenos 0,8 namiesto 0,7) sú lepšie na tréningu
  aj na teste, rozdiel je malý (0,0011).
- Kalibrácia v poriadku: favorit s predpoveďou 64 % vyhral 62,8 %, s 74 % vyhral 72,9 %.
- Rozpis len podľa dnešných 32 klubov stratí zápas ATL – PHX (2009/10 a 2010/11 by mali 1 229
  namiesto 1 230 zápasov). Sťahovač sa preto pýta aj na zaniknuté skratky a kontroluje počty.

Podrobnosti: reports/nhl_backtest.md. Ďalší krok: návrh vrstvy C (únava), reports/nhl_learned.md.

## Vrstva C – únava (schválená 13. 10. 2026)

Elo + únava z rozpisu na teste: log loss 0,6730 → 0,6713 (zlepšenie 0,0017, hranica 0,0005),
presnosť 57,2 % → 57,6 %. Najväčší vplyv má back-to-back: domáci −49 Elo, hostia +34 Elo
pre domácich. Peter vrstvu schválil, NHL model = Elo + únava (reports/nhl_learned.md).

## Zamietnuté kandidáty (13. 10. 2026)

- Vrstva G – brankár: očakávaný brankár +0,0001, skutočný 0,0000 (hranica 0,0005).
  Štartujúceho brankára pred zápasom NHL ani ESPN neukazujú. reports/nhl_goalies.md
- Glicko-2 namiesto Ela: horšie o 0,0028; navyše k Elu: 0,0000. reports/nhl_glicko.md

NHL model ostáva Elo + únava. Denník: docs/journal.md.
