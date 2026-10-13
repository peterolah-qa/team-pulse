# Team Pulse – viac športov (plán, 13. 10. 2026)

Jedna appka Team Pulse, hore prepínač športu. Každý šport má vlastný model a vlastné dáta,
všetko ostatné je spoločné. Prvý šport je NBA (beží), ďalej NHL, Tipos extraliga a F1.
Úlohy a stav: board **Team Pulse – športy** (`scripts/board_sporty.sh`).

## Architektúra

Jeden repozitár, jedna vetva `main` = to, čo beží. Vetvy len krátko na jednu vec
(napr. `nhl`) a do `main` idú až po zelených testoch. Žiadna vetva na šport natrvalo:
spoločné opravy by sa museli ručne prenášať a vetvy by sa rozišli.

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
- Šport ide do appky až po prejdení backtestu a ostrého merania (14 dní, ako G2).
- Počas G2 NBA (20. 10. – 3. 11. 2026) sa kód NBA nemení.

## Fázy

| Fáza | Obsah | Kedy | Brána |
|---|---|---|---|
| Š1 – NHL: dáta a backtest | sťahovač histórie, hokejové Elo, backtest; len vetva `nhl` | teraz – 3. 11. | G0-NHL |
| Š2 – Spoločné jadro | `core/` + `sports/nba/`, appka a výstupy bez zmeny | od 4. 11. (po G2) | všetky testy zelené, rovnaké JSON |
| Š3 – NHL v appke | živé dáta, prepínač športu, hokejové štatistiky | po Š2 | G2-NHL (14 dní ostro) |
| Š4 – Tipos extraliga | overiť zdroj a podmienky, história, backtest, appka | po Š3 | G0 + G2 extraliga |
| Š5 – F1 | model pretekov, obrazovky | zima 2026/27 | ostro od prvých pretekov 2027 |

## Brána G0-NHL (stanovené vopred, 13. 10. 2026)

- Sezóny: 2005/06 – 2025/26 (od zavedenia nájazdov, každý zápas má víťaza).
  Tréning do 2022/23, test 2023/24 – 2025/26, ako pri NBA. Prvé 3 sezóny sú rozbeh Ela.
- Hodnotí sa len základná časť (playoff sa zapisuje do Ela, ale nehodnotí).
- **Kritérium:** log loss Ela na testovacích sezónach je o ≥ 0,0005 nižší než obe
  baseline („vždy domáci“, „lepšia bilancia“).
- Test úniku dát prechádza (predpoveď nikdy nevidí výsledok zápasu, ktorý predpovedá).
- Presnosť sa len zapíše. Hokej je náhodnejší než basketbal: NBA má 67 %,
  pri NHL rátame skôr s 58 – 60 %.

## Čím sa športy líšia

| | NBA | NHL / extraliga | F1 |
|---|---|---|---|
| Výsledok | výhra / prehra | výhra / prehra (aj po predĺžení alebo nájazdoch) | poradie 20 jazdcov |
| Model | Elo + únava + hráči | Elo, kandidáti: brankár, únava | víťaz a pódium, nie dvojica |
| Štatistiky | MIN, B, D, A, BL | G, A, body, +/−, zákroky brankára | kolá, zastávky, poradie |

## Zdroje dát

- NHL: `api-web.nhle.com` a `api.nhle.com/stats` (bez kľúča, neoficiálne zdokumentované),
  ESPN `hockey/nhl` (rovnaký tvar ako `basketball/nba`). Sťahuje sa z Macu
  alebo z GitHub Actions.
- Extraliga: verejné API nie je. Web hockeyslovakia.sk, najprv overiť podmienky používania.
- F1: Jolpica (nástupca Ergast), OpenF1.
