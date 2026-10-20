# Nápady na vylepšenia (19. 10. 2026)

Zásobník nápadov z viacerých pohľadov. Nič z toho sa nerobí bez Petrovho súhlasu. Zmena modelu
platí len po prejdení hranice 0,0005 na testovacích sezónach, stanovenej pred meraním. Počas G2 NBA
(do 3. 11.) sa nemení kód NBA ani `predict.yml`, takže tam je stĺpec „Kedy“.

Náročnosť: XS = do hodiny, S = pol dňa, M = 1 – 2 dni.

## Odporúčané poradie (top 3)

1. **Mac sa ráno sám zobudí (D1)** – dnes, 5 minút. Kritérium 4 brány G2 (stav do 12:00) dnes
   stojí na tom, že je Mac o 10:00 hore.
2. **Strážca dát a appky (C1 + C2)** – počas G2, nový workflow, NBA kód sa nemení. Chyba typu
   „chýbajúce zápasy na neutrálnej pôde“ by sa našla v prvý deň, nie po rokoch, a zistíme aj to,
   keď živá appka ukazuje staré dáta, hoci build prešiel.
3. **Začiatok sezóny podľa zmien v súpiske (B1)** – po G2. Najväčšia zmeraná slabina modelu:
   prvých 14 dní má log loss 0,634, celá sezóna 0,597 (`reports/g2_reference.md`).

## A. Používateľ appky

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| A1 | **Bilancia**: všetky zamknuté tipy oproti výsledkom, presnosť a log loss v čase, porovnanie s baseline, graf kalibrácie (NBA aj NHL) | Predikčná appka stojí na dôvere. Teraz je bilancia len v `reports/*.md`, ktoré v appke nevidno. | M | po G2 |
| A2 | **Obľúbené teamy** (hviezdička): navrchu v Zápasoch a Tipoch, filter | Denné použitie: väčšinu ľudí zaujímajú 1 – 2 teamy. Uloží sa len v prehliadači. | S | po G2 |
| A3 | **Kalendár (.ics) obľúbeného teamu** s naším tipom pri zápase | Zápasy sa objavia v kalendári v telefóne bez otvárania appky. Statické súbory z Actions. | S | po G2 |
| A4 | **Ranný súhrn do Telegramu**: včerajšie tipy ✓/✗, dnešné zápasy s tipom, chyby prevádzky | Zadarmo (Telegram bot + Actions, token ako secret GitHubu). Slúži aj ako kanál upozornení (D). | S | počas G2 (nový workflow) |
| A5 | **Graf „Šanca, že vyjdú všetky“ v Tipoch preformulovať alebo zrušiť** | Násobenie šancí je logika stávkového tiketu. Pravidlá neporušuje, ale k stávkovaniu má najbližšie. Návrh: „Ako isté sú dnešné tipy“ bez násobenia. | S | po G2 |

## B. Model a dáta

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| B1 | **Prenos Ela cez leto podľa kontinuity súpisky** (podiel minút, ktoré v teame ostali): veľké zmeny → silnejší návrat k priemeru | Cieli presne na slabý začiatok sezóny (0,634 vs. 0,597). Kandidát na vrstvu, meria sa hranicou 0,0005. | M | po G2 |
| B2 | **Stráženie modelu po G2** (CUSUM nad log loss oproti očakávaniu z backtestu, hranica stanovená vopred) | G2 trvá 14 dní, sezóna 6 mesiacov. Alarm, keď sa model počas sezóny zhorší (zranenia, zmeny pravidiel). | S | návrh počas G2, beh po G2 |
| B3 | **Kalibrácia pásma 60 – 70 %** (Platt alebo izotonická, učená na tréningu) | Najslabšie pásmo kalibrácie podľa G1. Kandidát na vrstvu, hranica 0,0005. | S | po G2 |
| B4 | **Záložný zdroj výsledkov NBA z ESPN** (už ich sťahujeme do `archive/boxscores`) | Keď Mac nebeží, výsledky a archív by sa doplnili aj tak (kritérium 2 G2). | M | po G2 |

## C. Kvalita a testovanie

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| C1 | **Invarianty dát denne**: každý team 82 zápasov NBA (NHL 2026/27: 84), žiadne duplicity, skóre v rozumnom rozsahu, tip zamknutý pred začiatkom, výsledok do 24 h, stav nie starší než 1 hrací deň | Chyba s neutrálnou pôdou by sa našla hneď. Pri chybe beh zlyhá a príde e-mail. | S | počas G2 (nový workflow) |
| C2 | **Syntetický test živej appky** (Playwright proti `peterolah-qa.github.io/team-pulse`): otvorí appku, skontroluje dnešné zápasy, čas dát nie starší než 2 h, NBA aj NHL | Testy overujú build, nie to, čo naozaj beží. Odhalí staré dáta, chybu Pages aj service workera. | S | počas G2 (nový workflow) |
| C3 | **Mutačné testy** (mutmut) na `elo`, `archive`, `gate_g2` | Zmeria, či testy naozaj chytia chybu v kóde, nielen ho prejdú. | S | kedykoľvek |
| C4 | **Register brán** `docs/brany.md`: všetky G0/G1/G2 (NBA, NHL, F1), commit kritérií, výsledok | Audit na jednom mieste: čo sa stanovilo vopred a kedy. | XS | kedykoľvek |

## D. Prevádzka

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| D1 | **Mac sa každé ráno zobudí o 9:55**: `sudo pmset repeat wakeorpoweron MTWRFSU 09:55:00` (kontrola `pmset -g sched`) | Ranné úlohy bežia o 10:00 a 10:15. Keď Mac spí, spustia sa až po prebudení, čo môže byť po 12:00 (kritérium 4). Pri zatvorenom MacBooku má byť Mac v nabíjačke. | XS | dnes |
| D2 | **Predikcie: beh čakajúci v rade začne zo starého commitu** a pri pushi archívu narazí na konflikt (16. 10.) | Oprava: pred commitom archívu stiahnuť `main` a tipy zamknúť znova. | S | po G2 (`predict.yml`) |
| D3 | **NHL ranná úloha do GitHub Actions** (API NHL odtiaľ funguje, overené v `predict.yml`) | NHL prestane závisieť od Macu. | S | po G2-NHL (27. 10.) |
| D4 | **Upozornenie 14 dní pred vypršaním tokenu** pre cron-job.org (11. 1. 2027) | Bez tokenu predikcie ticho spadnú späť na plán GitHubu (3 – 7 behov denne). | XS | kedykoľvek |

## E. Bezpečnosť

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| E1 | **Akcie v workflowoch pripnuté na commit (SHA)** + Dependabot pre akcie, npm a uv | Ochrana dodávateľského reťazca: tag akcie sa dá prepísať, commit nie. | S | po G2 |
| E2 | **CodeQL a ochrana pred pushom tajomstiev** (zadarmo pre verejné repo) | Automatická kontrola kódu a tokenov pri každom pushi. | XS | kedykoľvek |

## F. Prezentácia (Qavant)

| | Nápad | Prečo | Náročnosť | Kedy |
|---|---|---|---|---|
| F1 | **Prípadová štúdia „Ako overujem predikčnú appku“**: brány stanovené vopred, backtest, ostré meranie, contract, vizuálne, a11y a property testy, incidenty a poučenia z denníka | Silná ukážka QA na dátovom produkte, nie na formulári. | S | kedykoľvek |
| F2 | **Odznaky v README**: CI, stav brán, posledné ostré meranie | Stav projektu na prvý pohľad. | XS | kedykoľvek |
