# Bejzbal: MLB (plán 28. 10. 2026)

Petrove rozhodnutia 28. 10. 2026: bejzbal ako ďalší šport, tipy zamyká **ranná úloha na Macu** ako pri NHL.
Pôvodne MLB aj venezuelská LVBP naraz. Po sonde zdrojov (13:01) **LVBP vypustená a MLB bez MLB Stats API**
(zdôvodnenie nižšie). Pravidlá sú rovnaké ako pri ostatných športoch (`docs/sporty.md`): nekomerčné, žiadne
kurzy ani logá, žiadne kľúče a surové dáta v repozitári, brány s hranicami stanovenými vopred, zmenu modelu
len navrhnem a schvaľuje Peter.

## Zdroje a podmienky

| Zdroj | Na čo | Podmienky | Stav |
|:--|:--|:--|:--|
| Retrosheet | história MLB (game logy: skóre, extra smeny, štartujúci nadhadzovači, dvojzápasy, ihrisko) | voľné použitie; pri každom zverejnení povinná veta: „The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at "www.retrosheet.org".“ (README, appka) | ✅ sonda 28. 10.: game logy dostupné, `notice.txt` overený |
| 538 `mlb_elo.csv` | referencia pre G0-MLB (Elo, úprava za nadhadzovača) | CC BY 4.0 (repozitár fivethirtyeight/data); pôvodná adresa presmeruje na abcnews.com | ✅ kópia na archive.org z 6. 3. 2025 (56 MB), stiahne sa na Macu do `data/ref/` (necommituje sa) |
| ESPN MLB | živé dáta: rozpis, výsledky, ohlásení nadhadzovači | rovnaký typ podmienok ako ESPN pri NBA a NHL (osobné, nekomerčné) | overiť sondou |
| ~~MLB Stats API~~ | – | MLB Advanced Media: „Only individual, non-commercial, non-bulk use … any other use … prohibited without prior written authorization“ | **nepoužijeme** |

**Prečo LVBP nie a MLB bez MLB Stats API** (sonda 28. 10.):
- LVBP má štruktúrované dáta len v MLB Stats API (liga 135, sezóny 2010 – 2026, ~260 zápasov za sezónu,
  2019 – 2021 skrátené), a to **bez jediného ohláseného nadhadzovača** ani v histórii, ani v tejto sezóne.
  Model by bol len Elo a výhoda domáceho, testovacia vzorka ~700 zápasov, ostré meranie do 27. 12. ~120
  zápasov, súpisky sa počas sezóny menia. Malá hodnota za cenu najrizikovejšieho zdroja.
- Podmienky MLBAM výslovne povoľujú len individuálne použitie; verejná appka to prekračuje.
- MLB bez MLBAM stojí na najpevnejších zdrojoch (Retrosheet výslovne dovoľuje akékoľvek použitie, 538 CC BY,
  ESPN v rovnakom stave ako pri NBA a NHL) a sezóna začína až 25. 3. 2027, takže nevzniká súbežný projekt
  s termínom 27. 12.

## Termíny

- Sezóna MLB 2027: základná časť 24. / 25. 3. – 26. 9. 2027 (30 tímov, 2 430 zápasov).
- Kolektívna zmluva MLB končí 1. 12. 2026, liga poslala tímom postup pre lockout. Ak sa sezóna posunie,
  posunie sa aj G2-MLB. Model a G0 sa robia z histórie, lockout ich nezastaví.

## Architektúra

Bejzbal začína v `src/team_pulse/baseball/` (ako NHL v `nhl/`). Spoločné jadro (#55 – 58, od 4. 11.)
ho neskôr presunie do `sports/` spolu s NBA a NHL. Do appky ide bejzbal až po jadre: je to tretí šport v appke.

```
src/team_pulse/baseball/
  retrosheet.py     história: game logy → data/raw/baseball/ (necommituje sa); jeden riadok na zápas
  espn.py           živé dáta: rozpis, výsledky, ohlásení nadhadzovači; skratky ESPN ↔ Retrosheet
  games.py          jednotný zápas: id, dátum, číslo zápasu dňa, domáci / hostia, skóre, stav, nadhadzovači, ihrisko
  elo.py            Elo teamov, replikácia 538 (porovnanie s data/ref/mlb_elo.csv)
  pitchers.py       kĺzavé hodnotenie štartujúceho nadhadzovača z doterajších štartov
  model.py          logistická regresia: rozdiel Elo, domáci, nadhadzovač, cestovanie a odpočinok
  backtest.py       tréningové / testovacie sezóny, log loss, Brier, kalibrácia, baseline „vždy domáci“
  predict.py        zamknutie tipov: archive/baseball/mlb/predictions/YYYY-MM-DD.json
  daily.py          ranná úloha na Macu 10:30 (po NBA 10:00 a NHL 10:15), len na main
  app_data.py       app/public/data/baseball/*.json (po jadre)
scripts/probe_baseball.py   overenie zdrojov z Macu
reports/mlb_live.md         ostré tipy a vyhodnotenie
```

Model sa stavia po vrstvách ako pri NBA a NHL. Každá vrstva musí na testovacích sezónach zlepšiť log loss
aspoň o 0,0005, inak sa nepridá:

1. **Elo teamov:** replikácia 538 z archívnej kópie `mlb_elo.csv`, porovnanie zápas po zápase.
2. **Štartujúci nadhadzovač:** úprava podľa kĺzavého hodnotenia jeho posledných štartov oproti priemeru tímu
   (história z Retrosheetu, ostro ohlásený nadhadzovač z ESPN). V bejzbale je to najsilnejší faktor zápasu.
3. **Cestovanie, odpočinok, dvojzápasy:** malé vplyvy, každý len ak prejde hranicou.

## Bejzbalové špecifiká

- **Ohlásený nadhadzovač** sa uloží do zamknutého tipu. Ak tím pred zápasom nadhadzovača vymení, tip sa
  nemení a vyhodnotí sa normálne; appka pri zápase ukáže, kto naozaj nastúpil. Ak nadhadzovač ráno nie je
  ohlásený, tip je bez tejto vrstvy a v tipe sa to zapíše.
- **Odložené a zrušené zápasy** (dážď) sa nevyhodnocujú. Náhradný termín je nový zápas s novým tipom.
- **Dvojzápasy v jeden deň:** zápas sa rozlišuje podľa ID, v histórii podľa čísla zápasu dňa.
- **Remízy** v bejzbale nie sú (extra smeny). Prerušený a nedohraný zápas sa nevyhodnocuje.
- **Zmena pravidiel v roku 2023** (časový limit na nadhod, zákaz shiftu, väčšie bázy): testovacie sezóny
  2023 – 2025, staršie sezóny na tréning a s kontrolou, či sa vzťahy nezmenili.
- **Zápasy na neutrálnej pôde** (Tokio, Soul, Londýn, Mexiko) bez výhody domáceho. Zápas, ktorý začne skôr
  než ranné zamknutie, tip nedostane (rovnaké pravidlo ako NBA a NHL).
- Bejzbal je náhodnejší než hokej. Hranice brán sa stanovia z dát pred meraním, nie podľa očakávania.

## Brány

- **G0-MLB** (backtest): kritériá v `docs/gate-mlb-G0.md`, napísané **pred** prvým behom backtestu.
  Obsah: replikácia 538, log loss pod baseline „vždy domáci“, prínos každej vrstvy aspoň 0,0005, kalibrácia.
- **G2-MLB:** prvých 14 dní sezóny 2027 (25. 3. – 7. 4., vyhodnotenie 8. 4.); pri lockoute sa posunie.
- Do appky ide MLB po G0 s označením **beta** (po jadre), beta zmizne po G2-MLB.

## Časový plán

| Kedy | Čo |
|:--|:--|
| 28. 10. – 1. 11. | sonda ESPN MLB; kritériá G0-MLB vopred |
| od 4. 11. | spoločné jadro (#55 – 58) má prednosť |
| november – december | história z Retrosheetu, replikácia Elo, vrstva nadhadzovača, G0-MLB do ~20. 12. |
| január – marec 2027 | MLB v appke (beta) nad dátami sezóny 2026, ranná úloha na Macu |
| 25. 3. 2027 | ostré tipy MLB, G2-MLB |

Ďalší šport po bejzbale: **tenis** (Petrov nápad 28. 10.), návrh architektúry až po dokončení bejzbalu.
