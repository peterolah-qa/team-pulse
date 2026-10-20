# Team Pulse – viac športov (plán 13. 10. 2026, nové poradie 14. 10. 2026)

Jedna appka Team Pulse, hore prepínač športu. Každý šport má vlastný model, vlastné dáta
a vlastné brány. Prvý šport je NBA (beží), ďalej NHL, F1 a Tipos extraliga.
Úlohy a stav: board **Team Pulse – športy** (`scripts/board_sporty.sh`).

## Architektúra

Jeden repozitár, jedna vetva `main` = to, čo beží. Vetvy len krátko na jednu vec
(napr. `nhl`) a do `main` idú až po zelených testoch. Žiadna vetva na šport natrvalo:
spoločné opravy by sa museli ručne prenášať a vetvy by sa rozišli.

NHL je v `main` od 14. 10. 2026, v appke ako beta (Š2): tipy z archívu + výsledky z API NHL
(`team_pulse.nhl.app_data` v `predict.yml`, chyba NHL nezastaví NBA). Ranné úlohy na Macu (NBA 10:00, NHL 10:15)
commitujú do vetvy, na ktorej je priečinok – priečinok na Macu preto ostáva na `main`
a vývoj ide v krátkych vetvách mimo ranného času. NHL úloha na inej vetve odmietne bežať.

```
team-pulse/
  src/team_pulse/
    core/          spoločné: archív tipov, zamknutie 24 h pred zápasom, vyhodnotenie,
                   backtest metriky, Pulse a úrovne, kontrola zdrojov, zápis JSON
    sports/
      nba/         nba_api + ESPN basketbal, Elo + únava + hráči (dnešný kód)
      nhl/         API NHL + ESPN hokej, hokejové Elo
      extraliga/   hockeyslovakia.sk (ak to podmienky dovolia), hokejové Elo z nhl/
      f1/          Jolpica, model pretekov
  app/             jedna appka, rovnaké obrazovky, data/<šport>/*.json
  .github/workflows/  rozvrh na šport, jeden spoločný deploy na Pages
```

Šport = typ modelu (basketbal, hokej, F1). Liga = zdroj dát. Hokejový model sa robí raz
na NHL (veľa dát) a extraliga k nemu pridá len vlastný zdroj.

Adresa appky ostáva `peterolah-qa.github.io/team-pulse/`. Premenovanie repozitára by
rozbilo appku nainštalovanú na ploche.

## Pravidlá (rovnaké ako pri NBA)

- Nekomerčné, žiadne kurzy ani odkazy na stávkové kancelárie, žiadne logá (farby teamov áno).
- Žiadne kľúče v repozitári, stiahnuté surové dáta sa necommitujú.
- Každá vrstva modelu musí na testovacích sezónach zlepšiť log loss aspoň o 0,0005.
  Hranica sa stanoví pred meraním. Zmenu modelu len navrhnem, schvaľuje Peter.
- Každý šport má vlastné brány: G0 (backtest) a G2 (ostré meranie). Hranice sa stanovia vopred.
- Šport ide do appky po prejdení G0 s označením **beta**. Beta zmizne po prejdení jeho G2.
  Model športu sa počas jeho G2 nemení.
- Počas G2 NBA (20. 10. – 2. 11. 2026, vyhodnotenie 3. 11.) sa kód NBA nemení: model, predikcie,
  archív, ranná úloha, `predict.yml`. Appka (aj obrazovky NBA) sa meniť smie – od 20. 10. redizajn,
  Petrovo rozhodnutie – len so zelenými testami (E2E, prístupnosť, vizuálne). Archív NBA tipov sa
  commituje pred buildom appky, takže chyba appky meranie G2 nepokazí.
- Detail zápasu ukazuje len skutočné čísla: rozpad tipu sa sčíta presne na zamknutú šancu, forma,
  odpočinok a štatistiky sú len informácia a model sa podľa nich nemení. Žiadne kurzy, „hodnota“
  ani tiket, žiadne logá ani siluety lôg.

## Fázy

| Fáza | Obsah | Kedy | Brána |
|---|---|---|---|
| Š1 – NHL: dáta a backtest | sťahovač histórie, hokejové Elo, backtest, ostré tipy mimo appky | hotovo 13. 10. | G0-NHL ✅ |
| Š2 – NHL v appke (beta) | prepínač športu, zápasy, tipy, výsledky NHL; dáta z rannej NHL úlohy | hotovo 14. 10. (pred G2 NBA) | G2-NHL 13. – 26. 10. |
| Š3 – F1 | zdroj (Jolpica), história, model pretekov, backtest; tipy od Austinu (zamknuté po kvalifikácii), potom appka (beta) | 15. 10. – 1. 11. | G0-F1 (`docs/gate-f1-G0.md`), G2-F1 = 6 pretekov do 6. 12. |
| Š4 – Tipos extraliga | overiť zdroj a podmienky, história, backtest, appka | po Š3 | G0 + G2 extraliga |
| Š5 – Spoločné jadro | `core/` podľa toho, čo majú športy naozaj spoločné; výstupy bez zmeny | pri treťom športe, najskôr 4. 11. | všetky testy zelené, rovnaké JSON |

Prečo toto poradie: NHL je najbližšie k hotovému a jej G2 už beží (tipy sa zamykajú od 13. 10.).
F1 má pevný termín, sezóna 2026 končí 6. 12. a 6 zostávajúcich pretekov poslúži ako ostré meranie.
Spoločné jadro až keď budú tri športy, dovtedy by sme hádali, čo je naozaj spoločné.

## Brány po športoch

| Šport | G0 – backtest | G2 – ostré meranie |
|---|---|---|
| NBA | ✅ 27. 9. (`docs/gate-G0.md`, `docs/gate-G1.md`) | 20. 10. – 2. 11. (`docs/gate-G2.md`) |
| NHL | ✅ 13. 10. (`docs/gate-nhl-G0.md`) | 13. – 26. 10. (`docs/gate-nhl-G2.md`) |
| F1 | ❌ 14. 10. (`docs/gate-f1-G0.md`): model A horší než kvalifikácia | namiesto G2: model B naostro mimo appky, 6 pretekov 25. 10. – 6. 12. (`docs/gate-f1-shadow.md`, workflow `f1.yml`) |
| Extraliga | stanoví sa pred backtestom | stanoví sa |

Hranice G2 pre NBA a NHL vychádzajú z backtestu (`scripts/g2_reference.py` → `reports/g2_reference.md`).
Vyhodnotenie G2: `uv run python -m team_pulse.gate_g2 nba|nhl` → `reports/gate_g2_<šport>.md`.

Detail NHL zápasu v appke: kontext z `team_pulse.nhl.context` (rozpad tipu, Elo trend, forma, odpočinok,
vzájomné zápasy, štatistiky NHL). Sonda so skutočnými dátami: `uv run python scripts/probe_nhl_context.py`.

## Brána G0-NHL (stanovené vopred, 13. 10. 2026)

- Sezóny: 2005/06 – 2025/26 (od zavedenia nájazdov, každý zápas má víťaza).
  Tréning do 2022/23, test 2023/24 – 2025/26, ako pri NBA. Prvé 3 sezóny sú rozbeh Ela.
- Hodnotí sa len základná časť (playoff sa zapisuje do Ela, ale nehodnotí).
- **Kritérium:** log loss Ela na testovacích sezónach je o ≥ 0,0005 nižší než obe
  baseline („vždy domáci“, „lepšia bilancia“). Pravdepodobnosti baseline sa naučia
  z tréningových sezón (podiel výhier domácich, výhry teamu s lepšou bilanciou), takže sú
  silnejšie než pevných 60 % pri NBA.
- Parametre Ela (K, domáca výhoda, prenos do sezóny) sa ladia len na tréningových sezónach.
- Test úniku dát prechádza (predpoveď nikdy nevidí výsledok zápasu, ktorý predpovedá).
- Presnosť sa len zapíše. Hokej je náhodnejší než basketbal: NBA má 67 %,
  pri NHL rátame skôr s 58 – 60 %.

### Spustenie NHL (z Macu)

```
uv run python scripts/probe_nhl.py                                # ukážky odpovedí, kontrola zdrojov
uv run python -m team_pulse.nhl.fetch_games --from 2006 --to 2026  # história, cca 7 min
uv run python -m team_pulse.nhl.backtest                          # reports/nhl_backtest.md
uv run python -m team_pulse.nhl.daily                             # vyhodnotenie noci + tipy → GitHub
bash scripts/install_nhl_daily.sh                                 # to isté každé ráno o 10:15
```

Sťahovač si pýta rozpis každého klubu vrátane zaniknutých skratiek (ATL, PHX, ARI)
a skontroluje, že počet zápasov základnej časti presne sedí s ligou. Inak nič neuloží.

## Čím sa športy líšia

| | NBA | NHL / extraliga | F1 |
|---|---|---|---|
| Výsledok | výhra / prehra | výhra / prehra (aj po predĺžení alebo nájazdoch) | poradie 20 jazdcov |
| Model | Elo + únava + hráči | Elo + únava (brankár a Glicko-2 zamietnuté) | víťaz a pódium, nie dvojica |
| Štatistiky | MIN, B, D, A, BL | G, A, body, +/−, zákroky brankára | kolá, zastávky, poradie |

## Zdroje dát

- NHL: `api-web.nhle.com` a `api.nhle.com/stats` (bez kľúča, neoficiálne zdokumentované),
  ESPN `hockey/nhl` (rovnaký tvar ako `basketball/nba`). Sťahuje sa z Macu
  alebo z GitHub Actions.
- Extraliga: verejné API nie je. Web hockeyslovakia.sk v `robots.txt` zakazuje AI roboty
  (overené 14. 10. 2026), otvorený zdroj s licenciou sa nenašiel. Bez súhlasu SZĽH sa nesťahuje (#64).
- F1: Jolpica (nástupca Ergast), licencia CC BY-NC-SA 4.0 – nekomerčne, v appke uviesť zdroj;
  limit 4 požiadavky/s, 500/h. OpenF1 (živá telemetria) model nepotrebuje.
