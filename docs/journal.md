# Denník projektu Team Pulse

Čo sa urobilo, prečo a s akým výsledkom. Najnovšie hore. Podrobnosti sú v `docs/gate-*.md`,
`reports/*.md`, na boardoch „Team Pulse“ a „Team Pulse – športy“ a v histórii commitov.
Denník vznikol 13. 10. 2026, staršie záznamy sú doplnené spätne z commitov a brán.

## 20. 10. 2026

- **Redizajn – celý ekosystém obrazoviek (Petrovo zadanie 11:58).** Smer: analytický terminál (Bloomberg,
  FiveThirtyEight), nie stávková kancelária. Peter rozhodol: karusely vnútri obrazoviek (medzi záložkami len dok),
  Zápasy na mobile ako balíček kariet s prepínačom na zoznam, všetko v jednom kroku so screenshotmi pred patchom.
  - **Paleta podľa významu:** úrovne formy Silný smaragd (#10B981, žiara #00F2FE), Stabilný indigo (#6366F1),
    Oslabený jantár (#F59E0B), Kritický rubín (#F43F5E); podklad #0B0F19, karty #181E31 s okrajom #242D46.
    Tip už nie je žltý: fialovo-modrá žiara (#7C3AED → #2563EB). Stabilný je indigo, aby sa nemýlil s tipom
    (oba by inak boli fialové), jantár zostal len Oslabenému.
  - **Odznak teamu:** kruh vo farbách dresu so skratkou a prstencom: pri NBA Pulse vo farbe úrovne, pri NHL
    šanca na výhru v zápase (NHL Pulse nemá, nič sa nedopočítava). Žiadne logá.
  - **Zápasy:** pás dní hore (počet zápasov a najistejší tip dňa, zvolený deň svieti), Karty / Zoznam (appka si
    pamätá), balíček kariet so švihom, šípkami aj klávesnicou a ukazovateľom „Zápas 2 z 3“. Karta: Pulse
    (NBA) alebo bilancia a Elo (NHL), šanca, tip a najviac 4 dôvody v Elo bodoch v prospech tipu (NHL z rozpadu
    tipu). Vedľa prehľad dňa: počet zápasov, priemerná šanca favorita, všetky tipy dňa naraz, najistejší tip,
    liga podľa formy (NHL: najsilnejší podľa Ela) a model. Na počítači karty v mriežke a prehľad v stĺpci.
  - **Tipy:** ukazovatele (najistejší tip, počet, všetky naraz), graf: stĺpce = šanca tipu, čiara s plochou =
    súčin od prvého po daný; pri každom riadku pruh súčinu.
  - **Teamy (NBA):** 4 úrovne ako karusel so záložkami (na počítači 4 stĺpce), Kritickí jemne pulzujú; pri teame
    Pulse, prstenec a posun oproti normálu („dnes −3 Elo · Bez I. Varga (?) −12“). NHL ostáva poradie podľa Ela.
  - **Model:** presnosť, log loss, Brier ako ukazovatele, kalibrácia, prínos vrstiev (log loss a zmena oproti
    predchádzajúcej vrstve, napr. kalibrované Elo +0,0007 = horšie, únava −0,0034), váhy po rozkliknutí.
  - **Prechody:** obrazovka sa jemne zjaví a posunie, nie pri zmene dňa ani zobrazenia; pri obmedzení pohybu nič.
  - **Chyba nájdená testom pred odovzdaním:** kontajner kariet mal atribút `data-mode`, takže klik na šípku
    balíčka appka vzala ako „prepni zobrazenie“ a karty prekreslila. Opravené (len tlačidlá, iný atribút).
  - Detail NBA zápasu dostal prstence Pulse, inak čaká na etapu 3.
  - **Testy:** pytest 410 (vrátane testu na skutočnej odpovedi štatistík NHL), Playwright 147 (E2E, prístupnosť
    v tmavej aj svetlej téme, nové `screens.spec.ts`: pás dní, balíček, švih, šípky, klávesnica, prehľad dňa,
    Teamy, NHL karty) + 28 vizuálnych (nové snapshoty, aj Zápasy ako zoznam).

- **Redizajn appky – rozhodnutie.** Petrovi sa súčasný vzhľad nepáči: farby, neprehľadnosť, amatérsky dojem,
  písmo a 3D mince teamov, celkovo chaos a málo užitočných funkcií. Zvolený štýl „Odvážny a hravý“, nasadiť
  hneď, keď bude hotový. Najprv 5 variantov na plátne (Dres, Plagát, Tabuľa, Nálepky, Lano), potom Peter dodal
  návrh zo Stitch „Luminous Pulse“ (detail NHL zápasu SJS @ MTL). Ten sa berie s úpravami podľa pravidiel:
  - kurzy, „hodnota“, férový kurz a „Pridať na tiket“ vypustené (nekomerčné, bez kurzov) → karta Istota tipu
    a tlačidlo Sledovať zápas,
  - rozpad Ela so skutočnými číslami modelu namiesto vymyslených,
  - namiesto „energia 100 % / 45 %“ fakty: dni voľna, back-to-back, 3. zápas za 4 dni, zápas výjazdu, posun pásma,
  - potvrdení brankári vypustení (o 10:15 štartéra nikto nepozná, vrstva G zamietnutá),
  - forma, vzájomné zápasy a porovnanie štatistík z API NHL len ako informácia (model NHL sa počas G2-NHL nemení).
- **Pravidlo počas G2 NBA – zmena (Petrovo rozhodnutie 20. 10.).** Obrazovky appky vrátane NBA sa smú meniť
  (redizajn). Mení sa len appka (`app/`), nie model, predikcie, archív, ranná úloha ani `predict.yml`, každá zmena
  len so zelenými testami. Archív NBA tipov sa commituje pred buildom appky, meranie G2 tým nie je dotknuté.
  Zapísané v `docs/sporty.md`.
- **Návrhy z iného nástroja (Peter vložil 20. 10.).** Prijaté: hlavná karta a tip vystúpia nad ostatné, Elo trend,
  prichytené Sledovať zápas, porovnanie s poradím v lige; neskôr kompaktný / podrobný zoznam, Moje teamy hore,
  Bilancia (board). Zamietnuté: oficiálne logá NHL aj štylizované siluety (ochranné známky, pravidlo bez log),
  kalkulačka kurzov, Kellyho kritérium, „value bet“, ROI, tiket a pohyb kurzov (pravidlo bez kurzov a stávok).
  Radar namiesto pruhov neodporúčaný: pri dvoch teamoch a 6 číslach sa pruhy s poradím čítajú presnejšie.
- **Etapa 1 – dizajnový systém** (celá appka): tmavé plochy, fialová = aktívne, zlatá = tip a šanca favorita,
  azúrová = Elo; Space Grotesk na čísla a nadpisy, Inter na text; ploché karty, vystúpi len hlavná karta
  zápasu; plávajúci dok; odznak so skratkou vo farbách dresu namiesto 3D mincí; bez pozadia ihriska a 3D náklonu.
  Svetlá téma s kontrastom WCAG AA (axe v oboch témach).
- **Etapa 2 – detail NHL zápasu.** Hlavná karta (čas, aréna, bilancia, posledných 5, šanca, tip, odpočinok), istota
  tipu, „Prečo X % pre …“ v Elo bodoch, Elo trend, odpočinok a cestovanie, forma v sezóne, porovnanie s poradím
  v lige, vzájomné zápasy, chýbajúci hráči, zdieľanie odkazu a prichytené Sledovať zápas (upozornenie v appke po
  dohraní, pamäť len v zariadení).
- **NHL kontext zápasu** (`team_pulse.nhl.context`, beží v `app_data` v Predikciách, chyba nezastaví tipy):
  - rozpad tipu: šanca z archívu prevedená na Elo body. Keď sa z rozpisu klubov dajú znova spočítať vstupy modelu
    a model z nich dá presne zamknutú šancu, rozpad je po položkách a „prepočítaný“; inak Elo, domáci ľad, únava
    z archívu a zvyšok. Súčet vždy sedí na zamknutú šancu. Test: rozpis → skutočná predikcia → kontext dá presne
    tú istú šancu a rovnaké čísla odpočinku ako model.
  - Oprava môjho návrhu z rána: „+146 Elo → 71 %“ pri SJS @ MTL bolo neúplné, model má aj konštantu (+19,5 Elo)
    a vplyv odpočinku a výjazdu. Po rannom zamknutí 20. 10. (šanca 0,716), overené sondou na skutočnom rozpise:
    Elo +91,0, domáci ľad +20,0, konštanta +19,5, MTL 2 dni voľna −13,4, SJS bez dňa voľna −1,2, SJS back-to-back
    +38,5, SJS 3. zápas za 4 dni +1,1, SJS 4. zápas výjazdu +7,2 = +162,7 Elo → MTL 72 %.
  - forma, odpočinok, vzájomné zápasy (táto a minulá sezóna) z rozpisov klubov; štatistiky NHL (presilovky,
    oslabenia, strely) len po kontrole tvaru a len pre klub, ktorému sedí počet zápasov a výhier s rozpisom.
  - rozpisy sa nesťahujú pri každom behu: posledná verzia zo zverejnenej appky (`data/nhl/cache.json`), znova len
    klub s novým zápasom, starší než 6 h alebo bez zápasu s tipom. Minulá sezóna sa už nemení.
  - sonda `scripts/probe_nhl_context.py` (Mac): overí rozpad na dnešných skutočných tipoch a štatistiky NHL,
    odpoveď štatistík uloží do `tests/fixtures/nhl_team_summary.json`. Z cloudu sa API NHL nedá volať.
- **Sonda so skutočnými dátami (Mac, 11:40) – OK.** Štatistiky NHL: 32 klubov, tvar sedí, počet zápasov a výhier
  sedí s rozpisom pri 32 z 32. Zápasy s tipom: 13, rozpad overený pri 13 z 13 (model z rozpisu = zamknutá šanca).
  SJS @ MTL: Centre Bell, SJS 4-4-1, MTL 4-3-1, SJS back-to-back a 4. zápas výjazdu, MTL 2 dni voľna; vzájomné
  zápasy len 2 (v minulej sezóne hrali dvakrát, v tejto ešte nie). Odpoveď štatistík uložená ako
  `tests/fixtures/nhl_team_summary.json`, test na nej kontroluje tvar a poradie v lige.
- **Board:** `scripts/board_redizajn2.sh` – hotové kroky ekosystému (paleta, Zápasy, počítač, Tipy, Teamy, Model),
  „Redizajn 4“ uzavretý, Moje teamy a Bilancia ostávajú otvorené.
- **Board (doobeda):** `scripts/board_redizajn.sh` – míľnik „R – Redizajn appky“, hotové etapy 1 a 2, kontext NHL a Sledovať
  zápas; ďalej overenie so skutočnými dátami, detail NBA, zoznamy, Moje teamy, Bilancia, Sledovať pre NBA,
  nová ikona, testy a kontrola na iPhone.
- **Testy:** pytest 409, Playwright 129 (E2E, prístupnosť v tmavej aj svetlej téme) + 26 vizuálnych (nové
  snapshoty), ruff čistý. Test parsera G2 upravený: report NBA má od 20. 10. riadok základnej časti už pred
  prvým výsledkom, tabuľku až s výsledkami (`gate_g2 nba` na dnešných dátach: predbežne splnené, 0 dohratých).
- **G2-NHL predbežne k 20. 10. – všetky 4 kritériá splnené** (`5096fd6`): 51 z 51 tipov zamknutých pred
  začiatkom, všetky dohraté a vyhodnotené, nezávislý prepočet = report (vyšlo 31, log loss 0,6449), hranica
  0,7101. Prvá verzia reportu (v `8888dee`) bola z rána pred NHL úlohou, preto hlásila chýbajúci 19. 10.
- **Ranné úlohy 20. 10. prešli:** NBA stav 10:00 (`3c44b15`), NHL 10:15 (`5860614`, noc 19. 10.: tip vyšiel 3 z 4,
  zamknutých 13 tipov).

## 19. 10. 2026

- **Kontrola celého projektu pred G2 NBA.** Kód sa od 15. 10. nemenil, len tipy, výsledky a stav.
  Testy: pytest 369, Playwright 115 (E2E, prístupnosť) + 26 vizuálnych, ruff čistý, v repe žiadne
  tokeny. GitHub Actions 15. – 19. 10.: 248 behov, 2 chyby – 15. 10. časový limit pri zverejnení na
  Pages (GitHub, archív bol uložený predtým) a 16. 10. sa nepodarilo pushnúť archív NBA tipov (dva behy
  naraz, viď nižšie; poistka „Kontrola archívu“ beh označila, tipy zamkol ďalší beh o 30 min).
  Log na Macu: NBA ranná úloha bežala každý deň 15. – 19. 10. (19. 10. bez zmeny, preto bez commitu),
  NHL každý deň o 10:15.
- **cron-job.org: job Kontroly zdrojov spúšťal Predikcie.** Vznikol kópiou jobu Predikcie a URL ostala
  na `predict.yml`, preto každý deň o 11:30 bežali Predikcie dvakrát naraz a Kontrola zdrojov sa
  z cron-job.org nespustila ani raz. Opravené na `health.yml`, čas 13:30 (11:30 UTC). Test run 16:43:
  Kontrola zdrojov cez `workflow_dispatch` prešla, Predikcie navyše nespustil.
- **Zistenie na po G2 (`docs/napady.md` D2):** beh Predikcií, ktorý čaká v rade, začne zo starého
  commitu a pri pushi archívu narazí na konflikt v tom istom súbore. Bez dvojitého jobu je to zriedkavé,
  oprava v `predict.yml` až po zmrazení.
- **NHL zranenia v appke – PR #88 zlúčený** (`44846ba`). Pred zlúčením overené na aktuálnom `main`
  (pytest 374, Playwright 119 + 26 vizuálnych), po zlúčení CI, Appka aj Predikcie zelené. Mení len NHL.
- **G2 NBA – pripravenosť.** Stav s opravenou históriou, rozpis 20. 10. sedí s NBC (BOS @ DET 15:00 ET,
  PHI @ NYK 19:00 ET, OKC @ SAS 21:30 ET), v období 20. 10. – 2. 11. je 107 zápasov, žiadny na
  neutrálnej pôde.
- **G2-NHL v polovici.** Všetkých 62 zápasov 13. – 20. 10. má tip zamknutý pred začiatkom (overené proti
  nezávislému rozpisu NHL). Vyhodnotených 47: tip vyšiel 28 (59,6 %), log loss 0,6454 (hranica 0,7101).
- **Vyhodnotenie brán G2 – skript** `team_pulse.gate_g2` (`nba` / `nhl`, výstup `reports/gate_g2_<šport>.md`,
  návratový kód 1 pri nesplnení). Overuje kritériá z `docs/gate-G2.md` a `docs/gate-nhl-G2.md` bez
  zmeny: tipy zamknuté pred začiatkom podľa rozpisu (NBA zo stavu, NHL z API NHL), výsledky, nezávislý
  prepočet z archívov oproti reportom, stav do 12:00 z histórie gitu (NBA), hranice log loss
  a baseline. Pred koncom obdobia hodnotí predbežne. 18 testov: reporty v nich píše skutočný kód
  prevádzky a upravený report skript odhalí. NBA kód sa nemenil.
- **Nápady na vylepšenia** (`docs/napady.md`): používateľ, model, kvalita, prevádzka, bezpečnosť,
  prezentácia. Odporúčané: Mac sa ráno sám zobudí (dnes), strážca dát a živej appky (počas G2),
  začiatok sezóny podľa zmien v súpiske (po G2). Čaká na Petrov výber.

## 15. 10. 2026

- **NBA história znova stiahnutá a overená.** 33 410 zápasov (+10), 2024/25 aj 2025/26 po 1230
  zápasov, každý team 82, v každej 5 na neutrálnej pôde. Opravený stav (`e81443f`): Elo ORL −1,9,
  MEM +1,6, ostatné do 0,4 – presne podľa simulácie po prenose cez leto. #74 uzavretá.
- **Prvé automatické ranné behy prešli.** NBA stav 10:08 (`cd2b999`, archív +7 výsledkov), NHL 10:15
  (`798189e`, noc 14. 10.: tip vyšiel 1 z 2, zamknutých 13 tipov). Všetkých 31 NHL tipov v archíve je
  zamknutých pred začiatkom zápasu.
- **NBA – oprava zápasov na neutrálnej pôde** (`normalize()` v `team_pulse.data.fetch_games`, #74).
  nba_api ich od 2024/25 zapisuje v oboch riadkoch ako „HOSTIA @ DOMÁCI“ bez „vs.“, preto vypadli
  (10 zápasov). Teraz sa párujú podľa tohto zápisu (zhoduje sa s domácimi v rozpise NBA) a dostanú
  neutral=True. Dva riadky, ktoré sa nedajú spárovať, sú chyba namiesto tichého vypadnutia. Test na
  skutočných dátach (`tests/fixtures/nba_neutral_games.json`, `scripts/probe_nba_neutral.py`).
  Simulácia: všetky teamy 82 zápasov, Elo ±2,6 bodu, backtest log loss 0,59963 → 0,59975. Hranica
  G2 ostáva 0,6739 (na opravených dátach 0,6751, ponechaná prísnejšia stanovená vopred).
- **F1 – záložné spúšťanie z cron-job.org – návod** (board #89, súvisí s #86). Plán GitHubu môže
  behy `f1.yml` odložiť o hodiny, preto Peter pridá na cron-job.org job (klon jobu Predikcie): POST na
  `.../actions/workflows/f1.yml/dispatches`, telo `{"ref":"main"}`, sobota a nedeľa každú hodinu
  (minúta 11) a pondelok 06:11 UTC. Plán v `f1.yml` ostáva ako záloha. Claude job nepridáva sám
  (účet a token sú Petrove).
- **NHL – zranenia z ESPN v appke** (PR #88, board #59). Nový `team_pulse.nhl.injuries`: ESPN
  `hockey/nhl/injuries` → kluby NHL (ESPN LA, NJ, SJ, TB → LAK, NJD, SJS, TBL), stavy nehrá / trest /
  dlhodobo (IR) / otázny. `nhl.app_data` ich pridá do `nhl/predictions.json`, appka ich ukáže v detaile
  zápasu v sekcii „Chýbajúci hráči“. Len informácia: model NHL ich nepoužíva a tipy sa nemenia (brána
  G2-NHL). Keď ESPN zlyhá, sekcia sa neukáže. Naostro: 128 hráčov z 30 klubov, všetky skratky sedia.
  pytest 369 passed, Playwright zelené, CI zelené. Zlúčenie čaká na Petra.

## 14. 10. 2026

- **Extraliga – zdroj dát zatiaľ bez povolenia, nič sa nesťahuje** (board #64). Oficiálny web
  hockeyslovakia.sk nemá verejné API a jeho `robots.txt` výslovne zakazuje AI roboty (ClaudeBot,
  anthropic-ai, GPTBot a ďalšie) – Claude ho preto nečíta ani nesťahuje. Otvorený zdroj zápasov
  s licenciou (ako Jolpica pre F1) sa nenašiel; stránky tretích strán (hstats, HockeyDB, QuantHockey)
  majú len súhrny alebo dáta bez licencie, prevzaté z oficiálneho webu. Ďalší krok: Peter požiada
  SZĽH o súhlas s použitím výsledkov v nekomerčnej appke. Bez súhlasu #65 a #66 stoja.
- **F1 – ostrá prevádzka modelu B mimo appky nasadená** (PR #87, board #68, #86). Peter schválil
  `docs/gate-f1-shadow.md` pred prvým tipom. `team_pulse.f1.live` + workflow `f1.yml` (sobota a nedeľa
  každú hodinu, pondelok ráno): Elo po dojazdených pretekoch, tip po kvalifikácii a pred štartom do
  `archive/f1/predictions`, vyhodnotenie do `reports/f1_live.md`. Zmrazený model B v
  `state/f1_state.json` (Elo po kole 17). Generálka na Singapure 2026: šance živej prevádzky = backtest
  (rozdiel 5·10⁻⁷). `predict.yml` sa nemenil. Zlúčené merge commitom, aby ostal commit kritérií
  `c1995c6`. Prvý ručný beh na `main` zelený. Prvý tip: Austin, kvalifikácia 24. 10. 21:00 UTC.
- **F1 – model B a návrh ostrého merania mimo appky** (`docs/gate-f1-shadow.md`, `reports/f1_model_b.md`,
  board #86). Peter po G0-F1 zvolil nový model meraný naostro mimo appky. Model B = model A + Elo
  jazdcov aj tímov vynulované pri zmene technických pravidiel (2017, 2022, 2026, dané FIA, nie ladené).
  Orientačne na už videných dátach 2026 kolá 1 – 17: 1,1061 vs. kvalifikácia 1,1473 – **nie dôkaz**.
  Návrh merania: tipy po kvalifikácii na 6 zostávajúcich pretekoch 2026 (vlastný workflow `f1.yml`,
  `predict.yml` ostáva zmrazený), kritérium log loss víťaza ≤ kvalifikácia − 0,0005. Riziko: záporná
  váha Ela tímu (prekrýva sa s Elom jazdca). Čaká na schválenie pred Austinom (24. 10.).
- **F1 – brána G0-F1 nesplnená** (vetva `f1`, `docs/gate-f1-G0.md`, `reports/f1_backtest.md`, board #67,
  #68, #70, #81). Kritériá schválil Peter pred meraním (commit `c1995c6`): tip po kvalifikácii (zmena
  oproti #70), tréning 2014 – 2025, test 2026 kolá 1 – 17, kritérium log loss víťaza o ≥ 0,0005 nižší
  než lepšia baseline. Zdroj Jolpica-F1 (CC BY-NC-SA 4.0, limit 500/h): sťahovač `team_pulse.f1.fetch`
  s cache, 269 pretekov, kontrola úplnosti, contract test na skutočnej odpovedi. Model: Elo jazdca +
  Elo tímu (tímy cez premenovania) + miesto v kvalifikácii, podmienený logit. Výsledok na teste:
  model 1,2009, baseline kvalifikácia 1,1473 (presnosť 58,8 % vs. 70,6 %), rozdiel −0,0537 → ❌.
  Príčina: Elo prenesené zo sezóny 2025 do nových pravidiel 2026 (model favorizoval Russella, keď
  z pole position štartoval Antonelli) a model verí Elu viac než kvalifikácii; z pole vyhral v 2026
  12 zo 17 pretekov (v tréningu 54,8 %). Na starých pravidlách 2023 – 2025 model kvalifikáciu jasne
  porazil (1,0227 vs. 1,3101). Model sa na teste neladil, meranie sa neopakovalo. F1 do appky nejde,
  G2-F1 sa posúva, ďalší postup rozhodne Peter.
- **Kontrola zdrojov cez cron-job.org – návod** (board #85). Plán GitHubu ju spúšťa s oneskorením
  až 9 h, preto Peter pridá na cron-job.org druhý job (kópia jobu Predikcie): POST na
  `.../actions/workflows/health.yml/dispatches`, telo `{"ref":"main"}`, denne 11:30 UTC. Job Predikcie
  ostáva zapnutý, bežia oba. Presun behov Actions mimo špičky sa nerobil – repozitár je verejný,
  minúty sú zadarmo.
- **NHL v appke (beta), nový dizajn, aktualizácia Actions** (PR #82, board: #61, #79, #80, #83, #84).
  NHL: prepínač NBA / NHL hore (pamätá si výber), zápasy, tipy, výsledky (pp / sn), detail zápasu
  (Elo, domáce prostredie, únava), liga podľa Ela, model; štítok BETA do prejdenia G2-NHL.
  Dáta skladá `team_pulse.nhl.app_data` v `predict.yml`: zamknuté tipy z `archive/nhl/predictions`
  + výsledky z API NHL, nič sa neprepočítava (model NHL počas G2-NHL nemenený). **Odchýlka od plánu
  (#79):** namiesto commitu z rannej úlohy sa zmenil `predict.yml` – NHL krok s `continue-on-error`
  (chyba NHL nezastaví NBA) a spúšťanie pri pushi do `archive/nhl/**`; zmena pred zmrazením 20. 10.
  Dizajn: pruh šancí pri zápase, graf „šanca, že vyjdú všetky“ v Tipoch, graf Pulse vo forme teamov,
  dva stĺpce na počítači, svetlá téma podľa systému (WCAG AA), väčšie popisy osí. Actions: nové
  verzie akcií (koniec varovania o Node 20), CI s `permissions: contents: read` a archívom
  FiveThirtyEight z cache. Testy: pytest 342, Playwright 141 (vizuálne v obraze Playwright 1.56.1 /
  Ubuntu 24.04, a11y aj vo svetlej téme). Prvý ostrý beh po zlúčení zelený: 13 zápasov NHL s tipom,
  19 výsledkov, 32 teamov. Zistenie: plán GitHubu spúšťa Kontrolu zdrojov až o 9 h neskôr (12. 10.
  o 20:23 namiesto 11:30), Predikcie ťahá takmer celé cron-job.org.
- **Nové poradie a brány po športoch** (`docs/sporty.md`). Každý šport má vlastné G0 a G2, do appky
  ide po G0 s označením beta. Poradie: NHL v appke (15. – 19. 10.) → F1 (6 zostávajúcich pretekov
  2026 ako G2-F1) → extraliga → spoločné jadro pri treťom športe. Počas G2 NBA sa nemení kód NBA,
  appka môže dostať nový šport cez krátku vetvu so zelenými testami.
- **Kritériá G2 NBA a G2-NHL – návrh** (`docs/gate-G2.md`, `docs/gate-nhl-G2.md`, čaká na schválenie).
  Hranice z backtestu (`scripts/g2_reference.py` → `reports/g2_reference.md`): log loss za 14 dní
  ≤ 95. percentil 14-dňových okien testovacích sezón, NBA 0,6739, NHL 0,7101. Zistenie: NHL prehrá
  s baseline „vždy domáci“ v 24,5 % 14-dňových okien, NBA len v 3,1 %, preto je porazenie baseline
  kritériom len pri NBA. Začiatok sezóny je pri NBA ťažší (log loss 0,634, celá sezóna 0,597).
- **Chyba v NBA histórii: chýbajú zápasy na neutrálnej pôde** – 5 v 2024/25 aj 2025/26 (Mexiko,
  Paríž, Berlín, Londýn, semifinále NBA Cupu), niektoré teamy majú 79 – 81 zápasov. V období G2
  taký zápas nie je, prvý je 7. 11. (DEN @ IND, Mexiko). Oprava pred 20. 10., najneskôr pred 7. 11.
- **NBA – poistka „len z `main`“** (schválená, pred G2). Ranná NBA úloha na inej vetve skončí chybou
  skôr, než niečo stiahne alebo commitne. Kontrolu (`require_branch`) používa aj NHL úloha.
- **NHL – prvý automatický beh** (skúšobne o 12:22): commit „NHL 2026-10-14: noc 13. 10. tip vyšiel
  8 z 16, zamknuté tipy 13“ prešiel na GitHub.
- **Chyba: NBA stav z 14. 10. skončil vo vetve `nhl`.** Ranná NBA úloha commituje do vetvy, na ktorej
  je priečinok na Macu, a ten bol od 13. 10. na `nhl`. `main` mal do 12:04 stav z 13. 10. (dopad len
  na prípravné zápasy, sezóna začína 20. 10.). Oprava: `nhl` zlúčená do `main` (`e5d91d1`), vetva
  zmazaná, CI aj predikcie zelené. Pravidlo: priečinok na Macu ostáva na `main` (`docs/sporty.md`).
- **NHL v `main`.** Kód, model, archív a reporty NHL sú v `main`, mimo appky. Kód NBA sa nezmenil.
- **NHL – ranná úloha** `team_pulse.nhl.daily` (launchd 10:15, `scripts/install_nhl_daily.sh`):
  beží len na `main`, počká na NBA úlohu a na git, vyhodnotí noc, zamkne tipy na dnes a zajtra,
  commitne archív a report. Pri chybe upozornenie v macOS a záznam v `~/Library/Logs/team-pulse-nhl.log`.
- **NHL – prvá ostrá noc (13./14. 10.).** 16 zápasov, tip vyšiel 8 (50,0 %), log loss 0,6921.
  Overené nezávisle z archívu: všetky tipy zamknuté 7 h pred prvým zápasom, počet aj log loss sedia.
  Priemerná šanca tipu 56,4 % → čakali sme ~9 trafených; 8 z 16 alebo menej vyjde pri presnosti
  57,6 % v 36 % nocí. Jedna noc nič nehovorí, zmysel má až súčet za dlhšie obdobie (G2-NHL = 14 dní,
  ~100 zápasov). Elo sa po noci pohlo správne (COL po výhre v DAL +2,4, DAL −2,3).
- **NHL – tipy na 14./15. 10.** zamknuté (13 zápasov), tipy na 14. 10. prepočítané po nočných výsledkoch.

## 13. 10. 2026

- **Spúšťanie predikcií cez cron-job.org.** Plánované behy GitHubu chodili 4 – 5× denne namiesto
  68 (medzery 4 – 8 h). cron-job.org každých 30 min volá `workflow_dispatch` pre `predict.yml`
  (token len na `team-pulse`, Actions read/write, platí do ~11. 1. 2027). Test 204, beh sa spustil.
  Prvý beh spadol na zverejnení Pages (GitHub nenašiel artefakt), po Re-run prešiel aj s commitom
  archívu – chyba bola na strane GitHubu.
- **Predikcie: archív tipov pred zverejnením na Pages** (`6f25971`). Doteraz chyba Pages preskočila
  aj commit archívu a zamknuté tipy z behu sa stratili. Teraz sa archív commitne hneď po predpovediach,
  neúspešný push nezastaví zverejnenie a beh skončí červeno (krok Kontrola archívu). Prvý beh: zelený.
- **NHL – archív tipov a vyhodnotenie.** `predict` zamkne tipy do `archive/nhl/predictions/`
  (prepísať sa dajú len do začiatku zápasu). `team_pulse.nhl.archive` ráno porovná tipy
  s výsledkami → `reports/nhl_live.md`. Prvé ostré tipy: noc 13./14. 10., 16 zápasov.
- **NHL – živé tipy (vetva `nhl`).** Finálny model `models/nhl_v1.json` (Elo + únava, váhy
  z 21 612 zápasov 2008/09 – 2025/26, test 57,6 % / log loss 0,6713). `team_pulse.nhl.predict`
  stiahne aktuálnu sezónu z API NHL, spočíta Elo a únavu a vypíše tipy na najbližšie dni
  (`app/public/data/nhl/predictions.json`). Do appky pôjde až po G2 NBA.
- **NHL – Glicko-2 zamietnuté.** Samotný rating: log loss 0,6807 (Elo 0,6730). Namiesto Ela
  v modeli s únavou 0,6741 oproti 0,6713 (horšie o 0,0028), navyše k Elu zlepšenie 0,0000.
  Ladenie na tréningu smeruje k čo najmenšej neistote, teda späť k obyčajnému Elu. Glicko
  nepozná rozdiel gólov, Elo áno. Report `reports/nhl_glicko.md`.
- **NHL – vrstva G (brankár) zamietnutá.** História brankárov 2005/06 – 2025/26 je úplná
  (každý zápas má štartujúcich brankárov oboch klubov). Očakávaný brankár zlepšil log loss
  o 0,0001, skutočný o 0,0000 (hranica 0,0005). Štartujúceho brankára 9 h pred zápasom
  neukazuje NHL ani ESPN. Report `reports/nhl_goalies.md`.
- **NHL – vrstva C (únava) schválená.** Log loss 0,6730 → 0,6713, presnosť 57,2 → 57,6 %.
  Back-to-back: domáci −49 Elo, hostia +34 Elo pre domácich. NHL model = Elo + únava.
- **Brána G0-NHL splnená.** 27 166 zápasov 2005/06 – 2025/26, Elo 57,2 %, log loss 0,6730
  oproti lepšej baseline 0,6836. Zistenie: rozpis len podľa dnešných 32 klubov stratí zápas
  ATL – PHX, sťahovač sa preto pýta aj na zaniknuté skratky a kontroluje počty zápasov.
  `docs/gate-nhl-G0.md`.
- **Plán viac športov.** Jeden repozitár, `main` = to, čo beží, krátke vetvy na jednu vec.
  Poradie: NHL → spoločné jadro (po G2) → NHL v appke → Tipos extraliga → F1 (sezóna 2027).
  Nový board „Team Pulse – športy“ (5 fáz, 22 úloh). `docs/sporty.md`.
- **Upozornenia v appke** na dohrané zápasy (tip vyšiel / nevyšiel) a počet nových výsledkov
  na záložke Výsledky.
- **Kontrola zdrojov:** prípravné zápasy proti klubom mimo NBA už nehlásia chybu, dôvod chyby
  sa ukáže v Annotations, workflowy na Ubuntu 24.04.

## 9. 10. 2026

- Dizajn Aréna (3D mince teamov, karty s hĺbkou), farby Fialová a zlatá, nová ikona (lopta + pulz).
- Prerobené UI: zápasy a výsledky v našom čase, tip na víťaza, karta Tipy (zápasy podľa šance,
  bez kurzov). Výsledky len zo včera a z dneška.

## 7. 10. 2026

- Výsledky a štatistiky hráčov z ESPN hneď po zápase, archív tipov zamknutý 24 h pred zápasom.
- Ranná úloha na Macu zlyhala 6. 10. na `git pull` po prebudení → opakovanie a pokračovanie.

## 5. 10. 2026

- Výsledky posledných dní so štatistikami hráčov a naším tipom, prípravné zápasy so štítkom.

## 27. 9. 2026

- Brána G0: Elo 66,4 %, zhoda s archívom FiveThirtyEight 99,81 % zápasov.
- Brána G1: Elo + únava + chýbajúci hráči + sila súpisky, log loss 0,6108 → 0,5996,
  presnosť 67,3 %. Zamietnuté: dynamický K (0,0003 < 0,0005), zvýšená váha súpisky na začiatku
  sezóny (váha ≈ 0).
- Finálny NBA model v1 (29 603 zápasov), denná aktualizácia z Macu, predikcia v cloude,
  GitHub Pages, denná kontrola zdrojov.
- Brána G3: PWA appka, E2E, vizuálne a a11y testy, deploy.

## Čaká

- F1: pridať job na cron-job.org pre `f1.yml` (#89) pred Austinom (24. 10.), po testovacom behu overiť.
- NHL zranenia: overiť sekciu „Chýbajúci hráči“ v detaile NHL zápasu na živej appke.
- Extraliga: Peter pošle žiadosť o súhlas SZĽH (#64); až po súhlase história a backtest (#65).
- F1: overiť prvý zamknutý tip po kvalifikácii v Austine (24./25. 10., `archive/f1/predictions/2026-18.json`);
  vyhodnotenie modelu B 7. 12. (#86).
- Obnoviť token pre cron-job.org pred 11. 1. 2027 (inak sa predikcie spúšťajú len plánom GitHubu).
- G2 NBA: 20. 10. – 2. 11. 2026, vyhodnotenie 3. 11. ráno: `uv run python -m team_pulse.gate_g2 nba`.
  Model, predikcie, archív, ranná úloha a `predict.yml` sa do 3. 11. nemenia, obrazovky appky áno (20. 10.).
- G2-NHL: 13. – 26. 10. 2026, vyhodnotenie 27. 10. ráno po NHL úlohe (z Macu, potrebuje API NHL):
  `uv run python -m team_pulse.gate_g2 nhl`.
- Nápady: Peter vyberie z `docs/napady.md`, vybrané pôjdu na board.
- Redizajn: po deployi kroku 2 `bash scripts/board_redizajn2.sh`, kontrola na iPhone (švih kariet, pás dní).
  Ďalej etapa 3 (detail NBA), Moje teamy, Bilancia, Sledovať pre NBA, nová ikona, etapa 5 (testy, iPhone).
