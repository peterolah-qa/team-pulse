# Tenis: ATP a WTA (plán 28. 10. 2026)

Petrove rozhodnutia 28. 10. 2026: tenis ako ďalší šport (bejzbal pozastavený), **okruhy ATP aj WTA**,
tipy zamyká **GitHub Actions každých 30 minút** (spúšťané z cron-job.org ako predikcie). Pravidlá sú rovnaké
ako pri ostatných športoch (`docs/sporty.md`): nekomerčné, žiadne kurzy ani logá, žiadne kľúče a surové dáta
v repozitári, brány s hranicami stanovenými vopred, zmenu modelu len navrhnem a schvaľuje Peter.

## Rozsah

- **Dvojhra mužov (ATP) a žien (WTA)**, hlavné súťaže okruhov vrátane grandslamov, Turnaja majstrov a United
  Cupu. Bez štvorhry, challengerov a ITF.
- **Šport = model, okruh = liga:** kód modelu je spoločný, parametre (K, váha povrchu, vrstvy) a brány
  sú pre ATP a WTA zvlášť.

## Termíny

- Sezóna 2026 končí ATP Finals v Turíne 15. – 22. 11. 2026.
- Sezóna 2027: United Cup od 1. 1. 2027, Brisbane od 4. 1., **Australian Open od 17. 1. 2027**.
- Ostré meranie (G2) teda až v januári; do konca sezóny 2026 sa stavia história, model a G0.

## Zdroje a podmienky

| Zdroj | Na čo | Podmienky | Stav |
|:--|:--|:--|:--|
| Jeff Sackmann `tennis_atp`, `tennis_wta` | história zápasov od roku 1968: hráči, rebríček, povrch, kolo, skóre, dĺžka | CC BY-NC-SA 4.0 (nekomerčne, uviesť autora, rovnaká licencia pri ďalšom šírení) | **pôvodné repozitáre vracajú 404** (hlásenie z 19. 9. 2026; overené 28. 10.: súbor 2024 HTTP 404) |
| Archívna kópia `Aneeshers/tennis-sackmann-archive` | to isté, snímka ATP a WTA z júna 2026 | rovnaká licencia CC BY-NC-SA 4.0, kópia si nenárokuje vlastníctvo | ✅ overené 28. 10.: commit `83733587` (25. 6. 2026), zápasy do turnajov začínajúcich 25. 5. 2026 (Roland Garros) |
| ESPN tenis | živý rozpis, výsledky, doplnenie medzery jún – november 2026 | rovnaký typ podmienok ako ESPN pri NBA a NHL (osobné, nekomerčné) | ✅ sonda 28. 10. (nižšie) |
| ~~TML-Database~~ | – | dáta zoškrabané z webu ATP | nepoužijeme |
| ~~tennis-data.co.uk~~ | – | obsahuje stávkové kurzy | nepoužijeme |

**Čo ukázala archívna kópia** (overené priamo 28. 10.): ATP ~2 900 – 3 100 a WTA ~2 600 – 2 800 zápasov
za sezónu 2021 – 2025 (2020 polovica, covid), 49 stĺpcov vrátane rebríčka, povrchu, kola, `best_of`, dĺžky
a štatistík podania. Skreče (RET) 60 – 110 a kontumácie (W/O) ~20 za sezónu a okruh. Treba:
- vybrať len hlavné súťaže: ATP úrovne G, M, A, F (a O – olympiáda), WTA G, PM, P, I, F (a O);
  Davis Cup a BJK Cup (D) a turnaje ITF vo WTA dátach (W, 50+H, 35+H) sa nerátajú,
- zjednotiť povrch (WTA 2025 má „clay“ aj „Clay“, niektoré zápasy bez povrchu – doplniť podľa turnaja),
- **doplniť medzeru jún – november 2026** (tráva, Wimbledon, US Open, ázijská časť sezóny) z ESPN,
  inak by Elo pred januárom nepoznalo pol roka výsledkov.

**Čo ukázala sonda ESPN** (28. 10. 2026, ATP aj WTA, dnes, zajtra a 15. 7. 2026):
- `scoreboard?dates=` vráti **celé turnaje daného týždňa** (všetky dni, aj kvalifikáciu), nie len jeden deň.
  Dnes a zajtra je preto odpoveď rovnaká; sťahovač berie zápasy podľa ich vlastného `startDate`.
- Zápas má `id`, `startDate`, `round`, `status` a dvoch hráčov s ESPN ID, menom a `winner`. Stavy:
  `STATUS_SCHEDULED`, `STATUS_IN_PROGRESS`, `STATUS_FINAL`, `STATUS_RETIRED`, `STATUS_WALKOVER`
  (skreč a kontumácia sa dajú rozlíšiť).
- **Naplánované zápasy majú oboch hráčov aj čas** (napr. Viedeň 19 a Bazilej 18 naplánovaných, všetky so známymi
  hráčmi) – tip sa dá zamknúť pred začiatkom.
- **Medzera sa dá doplniť:** 15. 7. 2026 vrátil Båstad, Gstaad, Umag a 6 turnajov WTA, všetko dohraté.
- Treba: (1) zápasy deduplikovať podľa `id` – spoločné turnaje (Båstad) sú v odpovedi ATP aj WTA, okruh sa
  určí podľa skupiny `mens-singles` / `womens-singles`, nie podľa adresy; (2) vynechať kvalifikáciu (kolo
  „Qualifying …“), ako v histórii; (3) **rozlíšiť úroveň turnaja**: ESPN WTA ukazuje aj WTA 125 (Curitiba,
  Valle d'Aosta, Querétaro), ktoré sa nerátajú – zoznam turnajov hlavných okruhov s párovaním názvov
  ESPN ↔ história (napr. „Erste Bank Open“ = Vienna) bude v súbore s testami; (4) ID hráčov ESPN sú iné než
  v histórii – párovanie mien v `players.py`.

Sackmann je autor dát, archívna kópia je len miesto, odkiaľ sa dajú stiahnuť. V README a v appke sa uvedie
Jeff Sackmann, licencia CC BY-NC-SA 4.0 a odkaz na pôvodné repozitáre aj na kópiu. Kópia sa používa
v pripnutom commite (nemenná), aby sa história nemohla potichu zmeniť.

## Architektúra

Tenis začína v `src/team_pulse/tennis/`. Spoločné jadro (#55 – 58, od 4. 11.) ho neskôr presunie do
`sports/`. Do appky ide tenis až po jadre.

```
src/team_pulse/tennis/
  history.py      archív Sackmann (pripnutý commit) → data/raw/tennis/ (necommituje sa)
  espn.py         živé zápasy a výsledky ATP / WTA, doplnenie medzery od júna 2026
  players.py      jednotné ID hráča (Sackmann ↔ ESPN), kontrola mien a krajín
  matches.py      jednotný zápas: okruh, turnaj, povrch, kolo, na 3 / 5 setov, hráči, víťaz, skóre, stav
  elo.py          Elo hráča: celkové + podľa povrchu (tvrdý, antuka, tráva), K klesá s počtom zápasov
  model.py        vrstvy: Elo a povrch, na 3 / 5 setov, únava (zápasy a sety za posledné dni)
  backtest.py     tréningové / testovacie sezóny, log loss, Brier, kalibrácia, baseline rebríček
  predict.py      zamknutie tipov: archive/tennis/<okruh>/predictions/YYYY-MM-DD.json
  app_data.py     app/public/data/tennis/*.json (po jadre)
.github/workflows/tennis.yml   každých 30 min z cron-job.org + záložný plán GitHubu
scripts/probe_tennis.py        overenie zdrojov z Macu
reports/tennis_live.md         ostré tipy a vyhodnotenie
```

Model sa stavia po vrstvách. Každá vrstva musí na testovacích sezónach zlepšiť log loss aspoň o 0,0005,
inak sa nepridá:

1. **Elo hráča** (celkové), K klesá s počtom odohraných zápasov (prístup 538 a Tennis Abstract).
2. **Povrch:** zmes celkového Ela a Ela na danom povrchu, váha z tréningových sezón.
3. **Na 3 alebo 5 setov:** v dlhšom zápase má favorit väčšiu šancu (grandslamy mužov).
4. **Únava:** zápasy a odohrané sety za posledné dni.

## Tenisové špecifiká

- **Zamknutie tipu:** súper je často známy až pár hodín pred zápasom (víťaz predchádzajúceho kola) a zápasy
  sa hrajú vo všetkých časových pásmach. Beh každých 30 minút zamkne tip hneď, ako sú známi obaja hráči,
  vždy pred začiatkom zápasu. Zamknutý tip sa už nemení; zápas bez tipu pred začiatkom sa nevyhodnocuje.
- **Skreč a kontumácia** (RET, W/O) sa nevyhodnocujú, rovnako ako odložený zápas.
- **Výhoda domáceho** v tenise nie je (domáca krajina sa môže skúsiť ako vrstva, len ak prejde hranicou).
- **Baseline:** vyššie postavený hráč v rebríčku vyhrá (silná baseline), plus logistická šanca z rebríčka.
  Pre predstavu: US Open 2016 (117 zápasov ATP) rebríček 72,7 % a Brier 0,185, Elo 538 75,2 % a 0,171.
  Hranice brán sa stanovia z dát pred meraním.
- **Appka:** záložky Zápasy (podľa turnaja a dňa), Tipy, Výsledky, Hráči (namiesto Teamov), Model.
  Bez lôg turnajov, krajina len ako kód (napr. SVK).

## Brány

- **G0-ATP** a **G0-WTA** (backtest): kritériá v `docs/gate-tennis-G0.md`, stanovené 28. 10. **pred** prvým
  behom. Testovacie sezóny 2023 – 2025; Elo musí mať log loss aspoň o 0,0005 nižší než lepšia baseline
  z rebríčka alebo bodov; úplnosť dát, test úniku, contract test ESPN; vrstvy každá aspoň 0,0005.
- **G2-tenis:** Australian Open 17. – 31. 1. 2027 (dvojhra mužov aj žien, ~250 zápasov), vyhodnotenie
  po finále; hranice stanovené vopred.
- Do appky ide tenis po G0 s označením **beta** (po jadre), beta zmizne po G2.

## Časový plán

| Kedy | Čo |
|:--|:--|
| 28. 10. – 1. 11. | sonda zdrojov z Macu (archív Sackmann, ESPN); kritériá G0 vopred |
| od 4. 11. | spoločné jadro (#55 – 58) |
| november – polovica decembra | história, doplnenie medzery z ESPN, Elo, vrstvy, G0-ATP a G0-WTA |
| december | sezóna nehrá: `tennis.yml` a zamykanie sa overia prehratím archívnych dní (ako by bežali naostro) |
| január 2027 | ostré tipy a tenis v appke (beta) od United Cupu 1. 1., G2 na Australian Open 17. – 31. 1. |
