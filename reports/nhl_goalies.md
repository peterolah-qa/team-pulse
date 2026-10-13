# NHL – návrh vrstvy G (brankár)

Nad schváleným modelom A + C. Tréning do 2022/23 (17676 zápasov), test 2023/24 – 2025/26 (3936 zápasov základnej časti).

Kvalita brankára = góly na zápas nad ligový priemer z jeho predchádzajúcich zápasov (stiahnuté k priemeru o 1500 striel). Očakávaný brankár = mix podľa štartov v posledných 10 zápasoch klubu.

## Rozhodnutie

- **A + C + G očakávaný brankár:** ❌ nezlepšuje dosť (zlepšenie 0,0001, hranica 0,0005); 1 gól chytený navyše za zápas = -27,4 Elo
- **A + C + G skutočný brankár:** ❌ nezlepšuje dosť (zlepšenie 0,0000, hranica 0,0005); 1 gól chytený navyše za zápas = 23,7 Elo

Skutočný brankár je naživo použiteľný len vtedy, keď štartujúceho brankára poznáme pred zápasom.

## Porovnanie na testovacích sezónach

| model                       |   zápasy | presnosť   | log loss   | Brier   |
|:----------------------------|---------:|:-----------|:-----------|:--------|
| A + C (schválené)           |     3936 | 57,6 %     | 0,6713     | 0,2394  |
| A + C + G očakávaný brankár |     3936 | 57,9 %     | 0,6712     | 0,2393  |
| A + C + G skutočný brankár  |     3936 | 57,8 %     | 0,6713     | 0,2394  |

Štartujúci brankár oboch klubov je v dátach pri 100,0 % testovacích zápasov. Priemerný rozdiel očakávaných brankárov: 0,12 gólu na zápas.
