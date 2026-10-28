# Bejzbal: MLB a LVBP (plán 28. 10. 2026)

Petrovo rozhodnutie 28. 10. 2026: bejzbal ako ďalší šport, **MLB aj venezuelská LVBP naraz**, tipy zamyká
**ranná úloha na Macu** ako pri NHL. Pravidlá sú rovnaké ako pri ostatných športoch (`docs/sporty.md`):
nekomerčné, žiadne kurzy ani logá, žiadne kľúče a surové dáta v repozitári, brány s hranicami stanovenými
vopred, zmenu modelu len navrhnem a schvaľuje Peter.

## Prečo dve ligy a čo z toho plynie

| | MLB | LVBP (Venezuela) |
|:--|:--|:--|
| Sezóna | základná časť 24. / 25. 3. – 26. 9. 2027 | 2026/27: od 12. 10. do 27. 12. 2026, potom round robin a finále (január) |
| Rozsah | 30 tímov, 2 430 zápasov | 8 tímov × 56 zápasov = 224 zápasov |
| História | Retrosheet od roku 1871 | zdroj treba overiť (MLB Stats API zimné ligy?) |
| Vzor modelu | 538 MLB Elo s úpravou za štartujúceho nadhadzovača | žiadny |
| Ostré meranie | od Opening Day 2027 | ešte túto sezónu, ak zdroj a G0 stihneme do polovice novembra |

- **Šport = model, liga = zdroj dát** (ako hokej: NHL a extraliga). Kód modelu je spoločný, parametre
  (K, výhoda domáceho, váhy vrstiev) sa učia **pre každú ligu zvlášť**. Úroveň a štýl lig sa líšia
  a hráči MLB v zimných ligách počas sezóny prichádzajú a odchádzajú.
- **LVBP je časovo kritická:** základná časť končí 27. 12. Bez povoleného zdroja histórie sa LVBP
  nerobí (rovnako ako extraliga pri SZĽH) a ostáva len MLB.
- **Riziko MLB:** kolektívna zmluva končí 1. 12. 2026, liga poslala tímom postup pre lockout. Ak sa sezóna
  2027 posunie, posunie sa aj G2-MLB. Model a G0 sa robia z histórie, lockout ich nezastaví.

## Architektúra

Bejzbal začína v `src/team_pulse/baseball/` (ako NHL v `nhl/`). Spoločné jadro (#55 – 58, od 4. 11.)
ho neskôr presunie do `sports/` spolu s NBA a NHL. Do appky ide bejzbal až po jadre: je to tretí šport v appke.

```
src/team_pulse/baseball/
  sources/
    retrosheet.py   história MLB: game logy → data/raw/baseball/ (necommituje sa); skóre, extra smeny,
                    štartujúci nadhadzovači, dvojzápasy (číslo zápasu dňa)
    statsapi.py     MLB Stats API: rozpis, výsledky, ohlásení nadhadzovači (MLB, zimné ligy)
    lvbp.py         história LVBP z povoleného zdroja (po overení)
  games.py          jednotný zápas: liga, id, dátum, domáci / hostia, skóre, stav, nadhadzovači, ihrisko
  elo.py            Elo teamov (replikácia 538 na MLB, rovnaký kód s parametrami LVBP)
  pitchers.py       kĺzavé hodnotenie štartujúceho nadhadzovača (game score) z doterajších štartov
  model.py          logistická regresia: rozdiel Elo, domáci, nadhadzovač, cestovanie a odpočinok
  backtest.py       tréningové / testovacie sezóny, log loss, Brier, kalibrácia, baseline „vždy domáci“
  predict.py        zamknutie tipov: archive/baseball/<liga>/predictions/YYYY-MM-DD.json
  daily.py          ranná úloha na Macu 10:30 (po NBA 10:00 a NHL 10:15), len na main
  app_data.py       app/public/data/baseball/<liga>/*.json (po jadre)
scripts/probe_baseball.py   overenie zdrojov a podmienok z Macu
reports/<liga>_live.md      ostré tipy a vyhodnotenie
```

Model sa stavia po vrstvách ako pri NBA a NHL. Každá vrstva musí na testovacích sezónach zlepšiť log loss
aspoň o 0,0005, inak sa nepridá:

1. **Elo teamov.** MLB: replikácia 538 z ich `mlb_elo.csv` (CC BY 4.0), ak sa nájde archívna kópia;
   inak vlastné Elo a ladenie K a výhody domáceho na tréningových sezónach.
2. **Štartujúci nadhadzovač:** úprava podľa kĺzavého hodnotenia jeho posledných štartov oproti priemeru tímu.
   V bejzbale je to najsilnejší faktor jedného zápasu.
3. **Cestovanie, odpočinok, dvojzápasy:** malé vplyvy, každý len ak prejde hranicou.

## Bejzbalové špecifiká

- **Ohlásený nadhadzovač** sa uloží do zamknutého tipu. Ak tím pred zápasom nadhadzovača vymení, tip sa
  nemení a vyhodnotí sa normálne; appka pri zápase ukáže, kto naozaj nastúpil. Ak nadhadzovač ráno nie je
  ohlásený, tip je bez tejto vrstvy a v tipe sa to zapíše.
- **Odložené zápasy** (dážď) sa nevyhodnocujú. Náhradný termín je nový zápas s novým tipom.
- **Dvojzápasy v jeden deň:** zápas sa rozlišuje podľa ID, nie podľa dvojice tímov a dátumu.
- **Remízy** v bejzbale nie sú (extra smeny). Prerušený a nedohraný zápas sa nevyhodnocuje.
- **Zmena pravidiel v MLB v roku 2023** (časový limit na nadhod, zákaz shiftu, väčšie bázy): testovacie
  sezóny MLB 2023 – 2025, staršie sezóny len na tréning a s kontrolou, či sa vzťahy nezmenili.
- **Zápasy na neutrálnej pôde** (MLB v Tokiu, Soule, Londýne, Mexiku) bez výhody domáceho. Zápas, ktorý začne
  skôr než ranné zamknutie, tip nedostane (rovnaké pravidlo ako NBA a NHL).
- Bejzbal je náhodnejší než hokej. Hranice brán G0 sa stanovia z dát pred meraním, nie podľa očakávania.

## Zdroje a podmienky

| Zdroj | Na čo | Podmienky | Stav |
|:--|:--|:--|:--|
| Retrosheet | história MLB | voľné použitie; pri každom zverejnení povinná veta „The information used here was obtained free of charge from and is copyrighted by Retrosheet…“ (README, appka) | overiť sondou |
| MLB Stats API | denný rozpis, výsledky, nadhadzovači | MLB Advanced Media: podľa doterajších znalostí len „individual, non-commercial, non-bulk“; preto len malé denné dopyty, žiadne hromadné sťahovanie histórie | overiť znenie a pokrytie zimných líg |
| 538 `mlb_elo.csv` | referencia pre G0-MLB | CC BY 4.0; pôvodná adresa projects.fivethirtyeight.com zrejme zanikla | hľadať archívnu kópiu |
| LVBP história | backtest LVBP | zdroj a podmienky neznáme; stránka, ktorá zakazuje roboty alebo AI, sa nepoužije | overiť sondou |

Z cloudového prostredia sú tieto zdroje zablokované, overuje ich sonda `scripts/probe_baseball.py` z Macu.

## Brány

- **G0-MLB** a **G0-LVBP** (backtest): kritériá v `docs/gate-mlb-G0.md` a `docs/gate-lvbp-G0.md`, napísané
  **pred** prvým behom backtestu. Obsah: replikácia (MLB, ak je referencia), log loss pod baseline
  „vždy domáci“, prínos každej vrstvy aspoň 0,0005, kalibrácia.
- **G2-LVBP** (ostré tipy mimo appky): od spustenia rannej úlohy do konca základnej časti 27. 12. 2026,
  hranica log loss stanovená z backtestu vopred (95. percentil ako pri NHL).
- **G2-MLB:** prvých 14 dní sezóny 2027 (25. 3. – 7. 4., vyhodnotenie 8. 4.); pri lockoute sa posunie.
- Do appky ide bejzbal po G0 s označením **beta** (po jadre), beta zmizne po G2 danej ligy.

## Časový plán

| Kedy | Čo |
|:--|:--|
| 28. 10. – 1. 11. | sonda zdrojov z Macu, rozhodnutie o zdroji LVBP; kritériá G0 |
| 2. – 15. 11. | LVBP: história, Elo, G0-LVBP; ranná úloha na Macu, ostré tipy mimo appky od ~16. 11. |
| od 4. 11. | spoločné jadro (#55 – 58), bejzbal pripravený na presun do `sports/` |
| november – december | MLB: história z Retrosheetu, replikácia Elo, vrstva nadhadzovača, G0-MLB do ~20. 12. |
| 27. 12. | koniec základnej časti LVBP, vyhodnotenie G2-LVBP |
| január – marec 2027 | bejzbal v appke (beta) nad dátami MLB 2026 a LVBP |
| 25. 3. 2027 | ostré tipy MLB, G2-MLB |

Ďalší šport po bejzbale: **tenis** (Petrov nápad 28. 10.), návrh architektúry až po dokončení bejzbalu.
