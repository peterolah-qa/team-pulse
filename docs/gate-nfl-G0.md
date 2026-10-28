# Brána G0-NFL – kritériá (stanovené 28. 10. 2026 pred meraním) a vyhodnotenie

Backtest NFL modelu (`docs/nfl.md`) na histórii z nflverse `games.csv` (pripnutý commit `a6b91bf` repozitára
`nflverse/nfldata`). Kritériá sú napísané a commitnuté **pred prvým behom modelu na testovacích sezónach**;
po commite sa nemenia.

## Dáta

- **Zápasy:** základná časť a play-off (bez prípravných zápasov), sezóny 1999 – 2025.
- **Stávkové stĺpce** sa nenačítajú vôbec (zoznam povolených stĺpcov).
- **Remíza** sa nevyhodnocuje (ani v teste, ani v baseline); v Ele sa počíta ako polovica výhry.
- **Sezóny:**
  - zahrievanie Ela (len výpočet hodnotení, nič sa nemeria ani neladí): 1999 – 2009,
  - tréning (ladenie parametrov Ela, váh vrstiev a baseline): 2010 – 2022,
  - **test: 2023 – 2025** (855 zápasov, bez remíz 854).

## Baseline (naučené len na tréningu)

1. **Vždy domáci:** podiel výhier domácich z tréningu; na neutrálnom ihrisku 50 %.
2. **Lepšia bilancia:** σ(a + b · (bilancia domácich − bilancia hostí)) z doterajších zápasov sezóny,
   na neutrálnom ihrisku bez člena a; v 1. týždni bilancia 0,5. Parametre z tréningu.

Porovnáva sa s **lepšou** z týchto dvoch baseline na testovacích sezónach.

## Kritériá

| # | Kritérium | Cieľ |
|---|---|---|
| 1 | Úplnosť dát | každá sezóna presne podľa NFL (základná časť + play-off: 2010 – 2019 256 + 11, 2020 256 + 13, 2021 272 + 13, 2022 271 + 13 – zrušený BUF – CIN, 2023 – 2025 272 + 13), žiadny zápas dvakrát |
| 2 | Log loss Ela na teste vs. lepšia baseline | Elo nižšie aspoň o **0,0005** |
| 3 | Test úniku dát | prechádza, overené aj úmyselnou chybou (tip so znalosťou výsledku musí test zhodiť) |
| 4 | Stávkové stĺpce | test: načítané dáta neobsahujú žiadny stávkový stĺpec |
| 5 | Contract test ESPN NFL | prechádza na tvare skutočnej odpovede (sonda) |

Presnosť, Brier, kalibrácia (pásma po 10 p. b.) a porovnanie s 538 (priemerný rozdiel šance na zápas
v sezónach 2010 – 2022, ak je archív `nfl_elo.csv` dostupný) sa zapíšu, ale bránu nerozhodujú.

## Vrstvy po G0

Quarterback a odpočinok sa pridávajú po jednej. Každá musí na testovacích sezónach zlepšiť log loss aspoň
o **0,0005** oproti modelu bez nej; inak sa nepridá. Zmenu modelu navrhnem, schvaľuje Peter.

## Po bráne

Prejde → ostré tipy mimo appky (`nfl.yml`, `reports/nfl_live.md`) a G2-NFL do 10. 1. 2027, kritériá G2
sa stanovia pred prvým ostrým tipom. Neprejde → zapíše sa príčina, oprava a nové meranie na tých istých
testovacích sezónach sa zapíše ako druhý pokus.

## Vyhodnotenie (28. 10. 2026): ✅ splnená

Kritériá vyššie boli commitnuté v `87d5549` pred prvým behom modelu. Backtest
`uv run python -m team_pulse.nfl.backtest`, podrobnosti v `reports/nfl_backtest.md`.

| # | Kritérium | Výsledok | Stav |
|---|---|---|---|
| 1 | Úplnosť dát | 2010 – 2025 všetky počty po sezónach sedia | ✅ |
| 2 | Log loss Ela vs. lepšia baseline | 0,6341 vs. 0,6611 (bilancia), rozdiel 0,0270 | ✅ |
| 3 | Test úniku dát | prechádza (Hypothesis: zmena budúcich výsledkov nemení minulé šance), úmyselná chyba zachytená | ✅ |
| 4 | Stávkové stĺpce | žiadny sa nenačíta (zoznam povolených stĺpcov), test prechádza | ✅ |
| 5 | Contract test ESPN NFL | skutočná odpoveď z 28. 10. (`tests/fixtures/nfl_espn_scoreboard.json`), ID zápasu = games.csv | ✅ |

| Model (test 2023 – 2025, 854 zápasov) | Presnosť | Log loss | Brier |
|---|---|---|---|
| Elo ladené na tréningu (K 20, domáci 48, prenos 0,6) | 63,9 % | 0,6341 | 0,2218 |
| Elo štart FiveThirtyEight (K 20, domáci 48, prenos 2/3) | 63,9 % | 0,6348 | 0,2220 |
| Baseline: lepšia bilancia | 59,5 % | 0,6611 | 0,2342 |
| Baseline: vždy domáci | 54,1 % | 0,6895 | 0,2482 |

Zistenia:
- Ladenie na tréningu zmenilo len prenos do sezóny (2/3 → 0,6); prínos na teste je malý (0,0007).
  Prenos 0,6 je na okraji mriežky; na tréningu je optimum medzi 0,55 a 0,6 (rozdiel 0,00002), na výsledku
  to nič nemení.
- Kalibrácia v poriadku: pásmo 60 – 70 % vyhralo 67,3 %, 70 – 80 % vyhralo 69,4 % (183 zápasov).
- Po sezónach 60,4 / 67,0 / 64,4 %; v 2023 bolo veľa zmien quarterbackov – vrstva quarterback je ďalší krok.
- Porovnanie s 538 (`nfl_elo.csv`, informatívne) sa urobí z archívnej kópie na Macu.
