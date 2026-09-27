# Brána G0 – vyhodnotenie (27. 9. 2026)

| Kritérium | Cieľ | Výsledok | Stav |
|---|---|---|---|
| Presnosť Elo (backtest) | ≥ 66 % | 66,4 % (HCA 70) | ✅ |
| Zhoda s archívom FiveThirtyEight | zhoda | 99,81 % zápasov do 1 Elo, priem. odchýlka 0,008 | ✅ |
| Test úniku dát | prechádza | 50 scenárov, 0 zlyhaní | ✅ |
| CI | zelené | lint + 19 testov | ✅ |

**Rozhodnutie: pokračovať na fázu 0b.**

## Zistenia pre fázu 0b
- Domáca výhoda +70 je lepšia než +100 vo všetkých metrikách → predvolená hodnota pre ďalšiu prácu.
- Model je mierne prehnane sebavedomý (favorit s predpoveďou 75 % vyhrá cca 72 %) →
  riešiť kalibráciou a vrstvami B a C.
- Jediná väčšia odchýlka od archívu (9,6 Elo) je opakovaný zápas ATL – MIA z 2008 → dátová anomália, nie chyba modelu.
