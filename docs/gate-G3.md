# Brána G3 – PWA appka

Dátum: 27. 9. 2026 · Fáza 2 · Rozhodnutie: **prechádza**. Ostáva ručná kontrola inštalácie a offline režimu na mobile (bod 8).

| # | Kritérium | Výsledok |
|---|---|---|
| 1 | 5 obrazoviek z draftu (Dnes, Zápas, Team, Čo keby, Model) + prehľad Teamy | ✅ |
| 2 | Jedna cyberpunk téma, mobile-first, na desktope dva stĺpce | ✅ |
| 3 | Dáta idú z predikcií (JSON), žiadne kurzy ani odkazy na stávkové kancelárie | ✅ test `appka nikde neukazuje kurzy` |
| 4 | E2E testy na mobile aj desktope vrátane prázdnych a chybových stavov | ✅ 14 testov × 2 zariadenia |
| 5 | Prístupnosť: axe WCAG 2.1 A + AA, 0 porušení; prepínač ovládateľný klávesnicou | ✅ 7 testov × 2 zariadenia |
| 6 | Vizuálna regresia | ✅ 6 obrazoviek × 2 zariadenia |
| 7 | Lighthouse (mobil) ≥ 90 v každej kategórii | ✅ 100 / 100 / 100 / 100 |
| 8 | PWA: manifest, ikony, service worker (offline = posledné stiahnuté dáta) | ✅ test dostupnosti manifestu, ikon a sw.js · ☐ ručne: „Pridať na plochu“ na iPhone a offline režim |
| 9 | Automatický deploy: predikcie → build → GitHub Pages každých 15 min | ✅ `predict.yml` |
| 10 | README pre portfólio (screenshoty, architektúra, model, testovanie) | ✅ |

## Poznámky

- **Pulse sa zobrazuje zaokrúhlený nadol.** Hodnota 49,5 je ešte Oslabený, takže appka ukáže 49, nie 50.
- **Dátum a čas zápasu.** Dni sú podľa amerického kalendára, lebo tak ich vedie NBA. Časy začiatku sú v našom čase.
  Keď u nás zápas začína až na druhý deň, pred časom je deň v týždni, napr. „ST 01:00“.
- **Váhy na obrazovke Model** sa ukazujú ako vplyv na dotknutý team. Napr. back-to-back hostí je −49 pre hostí,
  nie +49 pre domácich.
- **Vizuálne screenshoty** sú vygenerované na Linuxe. V CI (Ubuntu) sedia. Na Macu sa vizuálne testy
  bez `VISUAL=1` nespúšťajú, lebo písmo sa vykresľuje inak.

## Ďalej

Brána G2: 14 dní ostrej prevádzky od 20. 10. 2026. Sleduje sa, či je model systematicky istejší ako trh
(na otvárací večer o 2 – 3 body).
