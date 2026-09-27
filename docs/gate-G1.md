# Brána G1 – vyhodnotenie (27. 9. 2026)

Kritérium: každá vrstva a vylepšenie musí zlepšiť log loss na testovacích sezónach
(2023/24 – 2025/26, 3 931 zápasov, ktoré model pri učení nevidel) aspoň o 0,0005.
Hranica bola stanovená vopred, pred meraním.

| Krok | Log loss | Zmena | Rozhodnutie |
|---|---|---|---|
| A: Elo (HCA 70) – východisko | 0,6108 | – | – |
| + C: únava (7 príznakov z rozpisu) | 0,6081 | −0,0027 | ✅ prijaté |
| + B: chýbajúci hráči (PIE × minúty) | 0,6039 | −0,0042 | ✅ prijaté |
| + sila súpisky | 0,5996 | −0,0043 | ✅ prijaté |
| Dynamický K (ladené len na tréningu) | – | −0,0003 | ❌ zamietnuté |
| Sila súpisky so zvýšenou váhou na začiatku sezóny | – | váha ≈ 0 | ❌ vyradené |

**Celkovo:** log loss 0,6108 → 0,5996, presnosť 66,4 % → 67,3 %, Brier 0,2116 → 0,2068.

**Rozhodnutie: brána G1 splnená, pokračovať na fázu 1 (dátový agent + databáza).**

## Čo sa model naučil (Elo body)
- Domáca výhoda: cca 68 Elo, časť pôvodnej „výhody“ bola únava a absencie hostí.
- Back-to-back: −36 Elo doma, −47 Elo vonku (≈ 1,3–1,7 bodu). Odhad v drafte −40 sedel.
- Nadmorská výška (Denver, Utah): −47 Elo pre hostí. Draft odhadoval −15, bol podcenený 3×.
- Posun o časové pásmo na východ: −15 Elo za hodinu (domáci po návrate zo západu).
- Samotné kilometre: ≈ 0. Keď model pozná back-to-back a časové pásma, dĺžka cesty nič nepridá.
- Chýbajúca hviezda: rádovo −150 až −200 Elo (≈ 5–7 bodov).

## Známe obmedzenia
- Absencie v backteste pochádzajú z box score (kto nenastúpil). V prevádzke ich dodá
  Injury Report pred zápasom. Hráč k dispozícii, ktorého tréner nepostavil, sa v backteste
  nepočíta ako dostupný → backtest môže byť nepatrne optimistickejší než realita.
- Malé váhy s nečakaným znamienkom (away_tz_east, away_road) sú pravdepodobne šum
  alebo prekryv s inými vstupmi; kandidáti na odstránenie.
- Kalibrácia v pásme 60–70 % je horšia než pri silných favoritoch → sledovať vo fáze 1.
