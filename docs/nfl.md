# NFL (plán 28. 10. 2026)

Petrove rozhodnutia 28. 10. 2026: NFL ako ďalší šport s **prednosťou pred tenisom** (sezóna beží, tenis stačí
do januára), dáta z **nflverse `games.csv` s uvedením zdroja**, tipy zamyká **GitHub Actions** (cron-job.org),
ostré meranie **G2 do konca základnej časti**. Pravidlá sú rovnaké ako pri ostatných športoch (`docs/sporty.md`):
nekomerčné, žiadne kurzy ani logá, žiadne kľúče a surové dáta v repozitári, brány s hranicami stanovenými
vopred, zmenu modelu len navrhnem a schvaľuje Peter.

## Termíny (overené 28. 10. 2026)

- Sezóna 2026: 272 zápasov základnej časti (18 týždňov), k 26. 10. odohraných 7 týždňov a 107 zápasov.
- Koniec základnej časti 10. 1. 2027, play-off od 16. 1. 2027, **Super Bowl LXI 14. 2. 2027** (SoFi Stadium).
- Ostáva ~165 zápasov základnej časti a 13 zápasov play-off.

## Zdroje a podmienky

| Zdroj | Na čo | Podmienky | Stav |
|:--|:--|:--|:--|
| nflverse `nfldata/data/games.csv` (Lee Sharpe) | história 1999 – 2026 a rozpis: skóre, týždeň, typ zápasu, neutrálne ihrisko, dni odpočinku, štartujúci quarterback (aj na najbližší týždeň), ESPN ID zápasu, štadión | licencia v repozitári `nfldata` nie je uvedená (repozitár nflverse-data je CC BY 4.0); holé fakty, nekomerčne, so zdrojom „nflverse / Lee Sharpe“ – Petrovo rozhodnutie 28. 10. | ✅ overené 28. 10. (commit `a6b91bf`, aktualizácia 28. 10. 11:45 UTC) |
| 538 `nfl_elo.csv` | referencia: Elo a Elo upravené o quarterbacka od roku 1920 | CC BY 4.0 | archívnu kópiu na archive.org overí sonda |
| ESPN NFL | živý rozpis, výsledky, zranenia (ako NBA) | rovnaký stav ako ESPN pri NBA a NHL | overí sonda |

**`games.csv` obsahuje stávkové stĺpce** (`away_moneyline`, `home_moneyline`, `spread_line`, `away_spread_odds`,
`home_spread_odds`, `total_line`, `under_odds`, `over_odds`). Sťahovač ich **zahodí hneď pri načítaní**
(zoznam povolených stĺpcov, nie zakázaných), nikde sa neuložia, nepoužijú ani nezobrazia; test to stráži.

Čo ukázal `games.csv` (28. 10.): 7 548 zápasov 1999 – 2026; sezóny 2023 – 2025 po 285 zápasoch
(272 základná časť + 13 play-off), domáci vyhrali 56,5 / 54,7 / 53,3 %, remíza 1 (2025), 6 – 8 zápasov
na neutrálnej pôde za sezónu. Všetkých 107 odohraných zápasov 2026 má oboch štartujúcich quarterbackov,
najbližší týždeň už tiež.

## Architektúra

NFL začína v `src/team_pulse/nfl/`. Spoločné jadro (#55 – 58) ho neskôr presunie do `sports/`. Do appky ide
NFL až po jadre.

```
src/team_pulse/nfl/
  games.py        games.csv → jednotný zápas; povolené stĺpce, stávkové sa nenačítajú
  espn.py         živé výsledky a zranenia (ako NBA), párovanie cez ESPN ID zápasu
  elo.py          Elo tímov podľa 538: výhoda domáceho, váha rozdielu skóre, návrat k priemeru medzi sezónami
  qb.py           hodnota štartujúceho quarterbacka (vrstva po Ele)
  model.py        vrstvy: Elo, quarterback, odpočinok (voľný týždeň, štvrtok, cestovanie)
  backtest.py     tréningové / testovacie sezóny, log loss, Brier, kalibrácia, baseline
  predict.py      zamknutie tipov: archive/nfl/predictions/YYYY-MM-DD.json
  app_data.py     app/public/data/nfl/*.json (po jadre)
.github/workflows/nfl.yml   v hracie dni z cron-job.org, zamkne tipy dňa pred prvým výkopom
scripts/probe_nfl.py        overenie archívu 538 a ESPN NFL z Macu
reports/nfl_live.md         ostré tipy a vyhodnotenie
```

Vrstvy (každá musí na testovacích sezónach zlepšiť log loss aspoň o 0,0005, inak sa nepridá):

1. **Elo tímov** (replikácia 538, porovnanie s archívom `nfl_elo.csv`).
2. **Quarterback:** v NFL najsilnejší faktor jedného zápasu; náhradník namiesto štartujúceho quarterbacka
   výrazne zníži šancu tímu.
3. **Odpočinok:** voľný týždeň, zápas vo štvrtok po nedeli, cestovanie a časové pásma.

## NFL špecifiká

- **Zamknutie:** všetky zápasy začínajú po 15:30 nášho času (aj Londýn a Nemecko), stačí jeden beh v hracie dni
  pred prvým výkopom; do tipu sa uloží štartujúci quarterback. Zmena quarterbacka po zamknutí tip nemení.
- **Remíza** (raz za sezónu) sa nevyhodnocuje ako trafená ani netrafená; v Ele sa počíta ako polovica.
- **Neutrálne ihrisko** (zahraničné zápasy, Super Bowl): bez výhody domáceho.
- **Play-off** sa tipuje a vyhodnocuje rovnako ako základná časť.

## Brány

- **G0-NFL** (backtest): kritériá v `docs/gate-nfl-G0.md`, stanovené 28. 10. **pred** prvým behom modelu.
- **G2-NFL:** od prvého ostrého tipu do konca základnej časti 10. 1. 2027 (~100 – 130 zápasov); hranica
  log loss sa stanoví pred spustením (95. percentil v rovnako dlhých oknách backtestu, ako pri NHL).
- Do appky ide NFL po G0 s označením **beta** (po jadre), beta zmizne po G2.

## Časový plán

| Kedy | Čo |
|:--|:--|
| 28. – 30. 10. | sonda z Macu (archív 538, ESPN NFL); kritériá G0 vopred |
| do ~6. 11. | `games.py`, Elo, backtest, G0-NFL; vrstva quarterback |
| od ~9. týždňa (od 5. 11.) | `nfl.yml` naostro mimo appky, `reports/nfl_live.md`, G2-NFL do 10. 1. |
| po jadre | NFL v appke (beta) |
| 14. 2. 2027 | Super Bowl, koniec sezóny |
