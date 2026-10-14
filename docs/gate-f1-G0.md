# Brána G0-F1: backtest (kritériá stanovené vopred, 14. 10. 2026)

Kritériá schválil Peter 14. 10. 2026 pred stiahnutím histórie a pred akýmkoľvek meraním.
Počas merania sa nemenia. Výsledok sa dopíše nižšie do časti „Vyhodnotenie“.

## Rozhodnutia

- **Tip sa zamyká po kvalifikácii** (pred štartom pretekov), nie pred ňou. Model teda pozná
  poradie z kvalifikácie. Mení sa tým aj brána G2-F1 (karta #70).
- **Poradie z kvalifikácie, nie oficiálne poradie na štarte.** Tresty za výmenu dielov sa často
  oznámia až po zamknutí tipu, preto backtest aj ostrá prevádzka používajú to isté: výsledok
  kvalifikácie Veľkej ceny (nie šprintu). Jazdec bez času v kvalifikácii je na konci poradia.
- **Hodnotí sa len víťaz pretekov.** Šanca na pódium sa počíta a zapíše, nie je kritériom
  (pri 17 pretekoch by druhé kritérium bolo skôr náhoda).

## Dáta a rozdelenie

- Zdroj: Jolpica-F1 (`api.jolpi.ca/ergast/f1`), licencia CC BY-NC-SA 4.0 (nekomerčne,
  s uvedením zdroja). Limit 4 požiadavky/s a 500/h: sťahuje sa po celých sezónach, s cache,
  z Macu. Stiahnuté dáta sa necommitujú.
- **Tréning: sezóny 2014 – 2025** (hybridné motory). Parametre modelu aj baseline sa učia a ladia
  len tu.
- **Test: sezóna 2026, kolá 1 – 17** (Austrália – Singapur, nové technické pravidlá). Model pri
  ladení test nevidí. Počas sezóny sa hodnotenie jazdcov a tímov priebežne aktualizuje: tip na
  kolo k vidí len kolá pred k a kvalifikáciu kola k.
- Sezóny 2023 – 2025 sa zapíšu zvlášť (ako sa model správa so starými pravidlami), kritériom nie sú.
- Šprinty môžu vstupovať do hodnotenia jazdcov, ale nehodnotia sa.

## Metrika

Log loss víťaza: pre každé preteky −ln(šanca, ktorú model dal skutočnému víťazovi), priemer
cez preteky. Šance všetkých jazdcov na štarte dávajú spolu 1. Pre porovnanie sa zapíše aj
presnosť (favorit modelu vyhral) a Brier skóre šance na pódium.

## Baseline (pravdepodobnosti naučené na tréningových sezónach)

1. **Kvalifikácia:** šanca na víťazstvo podľa miesta v kvalifikácii (podiel víťazstiev z daného
   miesta v rokoch 2014 – 2025, vyhladený), znormované na jazdcov na štarte.
2. **Šampionát:** šanca podľa poradia jazdca v šampionáte pred pretekmi (pred 1. kolom poradie
   z konca minulej sezóny, nováčikovia na konci), naučená rovnako.

Poradie z kvalifikácie je pri F1 veľmi silný údaj, preto je baseline 1 prísna.

## Kritériá – všetky musia platiť

1. **Úplnosť dát:** každá sezóna 2014 – 2026 (do 17. kola) má všetky preteky a kvalifikácie
   podľa kalendára Jolpica, počet jazdcov v každých pretekoch sedí.
2. **Log loss víťaza modelu na teste je o ≥ 0,0005 nižší než lepšia z oboch baseline.**
3. **Test úniku dát prechádza:** tip na kolo k nikdy nevidí výsledok kola k ani neskorších kôl
   (overené aj úmyselnou chybou).
4. **Contract test** odpovede Jolpica (preteky, kvalifikácia) na skutočnej odpovedi.

Pravidlo vrstiev ako pri NBA a NHL: každá ďalšia vrstva modelu musí na teste zlepšiť log loss
aspoň o 0,0005, inak sa nepridá. Zmenu modelu len navrhnem, schvaľuje Peter.

## Po bráne

Prejde → tipy od Veľkej ceny USA (Austin, kvalifikácia 24. 10., preteky 25. 10.) a F1 v appke
ako beta. Neprejde → zapíše sa príčina, F1 sa do appky nedostane a G2-F1 sa posunie.

## Vyhodnotenie (14. 10. 2026)

| Kritérium | Cieľ | Výsledok | Stav |
|---|---|---|---|
| Úplnosť dát | všetky preteky a kvalifikácie, počty jazdcov podľa Jolpica | 2014 – 2026 (do 17. kola), 269 pretekov, 5 479 riadkov; malé polia (18 – 19) overené proti API | ✅ |
| Log loss víťaza vs. lepšia baseline | rozdiel ≥ 0,0005 | 1,2009 vs. 1,1473 (kvalifikácia), rozdiel **−0,0537** | ❌ |
| Test úniku dát | prechádza | prechádza, overené aj úmyselnou chybou | ✅ |
| Contract test Jolpica | prechádza | skutočná odpoveď (Singapur 2026, výsledky, kvalifikácia, šprint) | ✅ |

**Rozhodnutie: brána G0-F1 nesplnená.** Model sa na teste neladil a meranie sa neopakovalo.

| Test 2026 kolá 1 – 17 | Presnosť | Log loss víťaza | Brier pódia |
|---|---|---|---|
| Model (Elo jazdca + Elo tímu + kvalifikácia) | 58,8 % | 1,2009 | 0,0694 |
| Baseline kvalifikácia | 70,6 % | 1,1473 | 0,0705 |
| Baseline šampionát | 35,3 % | 1,8677 | 0,0980 |

### Príčina

- **Nové pravidlá 2026 prehodili poradie.** Elo jazdcov a tímov sa prenieslo zo sezóny 2025
  (prenos 0,5). Model preto favorizoval Russella aj v pretekoch, kde z 1. miesta kvalifikácie
  štartoval Antonelli (kolá 2, 3, 5, 13, 14); Antonelli vyhral 8 zo 17 pretekov.
- **Model verí Elu viac než kvalifikácii** (váhy 1,37 a 0,78 na 100 Elo). Na starých pravidlách
  to fungovalo: 2023 – 2025 (pre váhy neznáme) model 1,0227 vs. kvalifikácia 1,3101.
- **Kvalifikácia je v 2026 silnejšia než v minulosti:** z 1. miesta vyhral 12 zo 17 pretekov
  (70,6 %), v tréningu 2014 – 2025 len 54,8 %. Tabuľka baseline je z tréningu, takže ju to
  ešte podceňuje – model by musel byť ešte lepší.
- Šanca na pódium (len zápis) je u modelu o niečo lepšia (Brier 0,0694 vs. 0,0705).

Podľa pravidla: F1 sa do appky nedostane, G2-F1 sa posúva. Ďalší postup rozhodne Peter.
Podrobnosti: reports/f1_backtest.md.
