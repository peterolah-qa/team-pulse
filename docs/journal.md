# Denník projektu Team Pulse

Čo sa urobilo, prečo a s akým výsledkom. Najnovšie hore. Podrobnosti sú v `docs/gate-*.md`,
`reports/*.md`, na boardoch „Team Pulse“ a „Team Pulse – športy“ a v histórii commitov.
Denník vznikol 13. 10. 2026, staršie záznamy sú doplnené spätne z commitov a brán.

## 13. 10. 2026

- **Spúšťanie predikcií cez cron-job.org.** Plánované behy GitHubu chodili 4 – 5× denne namiesto
  68 (medzery 4 – 8 h). cron-job.org každých 30 min volá `workflow_dispatch` pre `predict.yml`
  (token len na `team-pulse`, Actions read/write, platí do ~11. 1. 2027). Test 204, beh sa spustil.
  Prvý beh spadol na zverejnení Pages (GitHub nenašiel artefakt), po Re-run prešiel aj s commitom
  archívu – chyba bola na strane GitHubu.
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

- Obnoviť token pre cron-job.org pred 11. 1. 2027 (inak sa predikcie spúšťajú len plánom GitHubu).
- G2 NBA: 20. 10. – 3. 11. 2026, 14 dní ostrej prevádzky. Kód NBA sa do 3. 11. nemení.
- NHL: vyhodnotiť prvé ostré tipy (noc 13./14. 10.), potom ostré meranie G2-NHL.
