# NFL (plán 28. 10. 2026)

Petrove rozhodnutia 28. 10. 2026: NFL ako ďalší šport s **prednosťou pred tenisom** (sezóna beží, tenis stačí
do januára), dáta z **nflverse `games.csv` s uvedením zdroja**, tipy zamyká **GitHub Actions** (cron-job.org),
ostré meranie **G2 do konca základnej časti**. Večer 28. 10. po G0: **ostré tipy čo najskôr – od týždňa 8**,
G2 meria čisté Elo (`docs/gate-nfl-G2.md`); vrstva quarterback popri tom ako druhý model od týždňa 10 (ak ju Peter
schváli), s vlastnou bránou. Pravidlá sú rovnaké ako pri ostatných športoch (`docs/sporty.md`):
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

NFL začína v `src/team_pulse/nfl/`. Spoločné jadro (#55 – 58) ho neskôr presunie do `sports/`. Do appky išla
NFL 28. 10. ako beta ešte pred jadrom (Petrovo rozhodnutie, cesta 1): `nfl.yml` zapisuje dáta do `app/public/nfl`,
build appky v `predict.yml` (zmrazený do 3. 11.) ich zverejní bez zmeny workflowu.

```
src/team_pulse/nfl/
  games.py        games.csv → jednotný zápas; povolené stĺpce, stávkové sa nenačítajú
  espn.py         živé výsledky a zranenia (ako NBA), párovanie cez ESPN ID zápasu
  elo.py          Elo tímov podľa 538: výhoda domáceho, váha rozdielu skóre, návrat k priemeru medzi sezónami
  qb.py           vrstva quarterback: náhradník namiesto bežného štartéra −65 Elo (schválená 28. 10.)
  model.py        vrstvy: Elo, quarterback, odpočinok (voľný týždeň, štvrtok, cestovanie)
  backtest.py     tréningové / testovacie sezóny, log loss, Brier, kalibrácia, baseline
  predict.py      zamknutie tipov: archive/nfl/predictions/YYYY-MM-DD.json
  app_data.py     app/public/nfl/*.json (commitujú sa, build appky ich zverejní)
.github/workflows/nfl.yml   3× denne: tipy na najbližší týždeň (keď je predchádzajúci dohraný), vyhodnotenie
scripts/probe_nfl.py        overenie archívu 538 a ESPN NFL z Macu
reports/nfl_live.md         ostré tipy a vyhodnotenie
```

Vrstvy (každá musí na testovacích sezónach zlepšiť log loss aspoň o 0,0005, inak sa nepridá):

1. **Elo tímov** (replikácia 538, porovnanie s archívom `nfl_elo.csv`).
2. **Quarterback:** v NFL najsilnejší faktor jedného zápasu; náhradník namiesto štartujúceho quarterbacka
   výrazne zníži šancu tímu.
3. **Odpočinok:** voľný týždeň, zápas vo štvrtok po nedeli, cestovanie a časové pásma.

## NFL špecifiká

- **Zamknutie:** `nfl.yml` 3× denne zamkne celý najbližší týždeň, len čo je predchádzajúci dohraný (zvyčajne
  v utorok, pred štvrtkovým zápasom). Zápas, ktorý už začal, tip nedostane. Do tipu sa uloží očakávaný štartujúci
  quarterback z games.csv a commit games.csv. Zmena quarterbacka po zamknutí tip nemení.
- **Remíza** (raz za sezónu) sa nevyhodnocuje ako trafená ani netrafená; v Ele sa počíta ako polovica.
- **Neutrálne ihrisko** (zahraničné zápasy, Super Bowl): bez výhody domáceho.
- **Play-off** sa tipuje a vyhodnocuje rovnako ako základná časť.

## Brány

- **G0-NFL** (backtest): kritériá v `docs/gate-nfl-G0.md`, stanovené 28. 10. **pred** prvým behom modelu.
- **G2-NFL** (`docs/gate-nfl-G2.md`): týždne 8 – 18, výkop 29. 10. 2026 – 10. 1. 2027 (~165 zápasov), model
  `nfl-elo-v1`; log loss ≤ 0,6620 (95. percentil 165-zápasových okien testovacích sezón).
- Do appky ide NFL po G0 s označením **beta** (po jadre), beta zmizne po G2.

## Časový plán

| Kedy | Čo |
|:--|:--|
| 28. – 30. 10. | sonda z Macu (archív 538, ESPN NFL); kritériá G0 vopred |
| do ~6. 11. | `games.py`, Elo, backtest, G0-NFL; vrstva quarterback |
| od 8. týždňa (29. 10.) | `nfl.yml` naostro mimo appky (3× denne), `reports/nfl_live.md`, G2-NFL do 10. 1. |
| 28. 10. | vrstva quarterback schválená (náhradník −65 Elo, `reports/nfl_qb.md`) |
| od 10. týždňa (12. 11.) | druhý model `nfl-elo-qb-v1`, G2-NFL-QB do 10. 1. (`docs/gate-nfl-qb-G2.md`) |
| 28. 10. | NFL v appke (beta): `app/public/nfl` z `nfl.yml`, bez zmeny `predict.yml` (Peter: cesta 1) |
| od 4. 11. | spoločné jadro (#55 – 58) hneď po G2 NBA, pred tenisom |
| 14. 2. 2027 | Super Bowl, koniec sezóny |
