# Brána G0-NFL – kritériá (stanovené 28. 10. 2026 pred meraním)

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
