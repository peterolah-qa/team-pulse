# Denník projektu Team Pulse

Čo sa urobilo, prečo a s akým výsledkom. Najnovšie hore. Podrobnosti sú v `docs/gate-*.md`,
`reports/*.md`, na boardoch „Team Pulse“ a „Team Pulse – športy“ a v histórii commitov.
Denník vznikol 13. 10. 2026, staršie záznamy sú doplnené spätne z commitov a brán.

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

- Extraliga: Peter pošle žiadosť o súhlas SZĽH (#64); až po súhlase história a backtest (#65).
- F1: overiť prvý zamknutý tip po kvalifikácii v Austine (24./25. 10., `archive/f1/predictions/2026-18.json`);
  vyhodnotenie modelu B 7. 12. (#86).
- Kontrola zdrojov: pridať job na cron-job.org o 11:30 UTC (#85), job Predikcie nechať zapnutý.
- Obnoviť token pre cron-job.org pred 11. 1. 2027 (inak sa predikcie spúšťajú len plánom GitHubu).
- Schváliť kritériá G2 NBA a G2-NHL, potom `bash scripts/board_plan2.sh` (boardy podľa nového poradia).
- NBA: oprava zápasov na neutrálnej pôde v histórii (pred 20. 10., najneskôr pred 7. 11.).
- G2 NBA: 20. 10. – 2. 11. 2026, vyhodnotenie 3. 11. Kód NBA sa do 3. 11. nemení.
- G2-NHL: 13. – 26. 10. 2026, vyhodnotenie 27. 10.
- NHL: overiť prvý automatický beh 15. 10. (commit „NHL 2026-10-15: …“ a log).
