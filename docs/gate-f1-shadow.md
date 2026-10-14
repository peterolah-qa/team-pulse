# F1 – model B a ostré meranie mimo appky (NÁVRH, čaká na schválenie Petrom)

Návrh 14. 10. 2026 po nesplnenej bráne G0-F1 (`docs/gate-f1-G0.md`). Platí až po schválení,
najneskôr pred kvalifikáciou v Austine (24. 10. 2026, 21:00 UTC). Po schválení sa nemení.

## Prečo nové meranie

Test 2026 kolá 1 – 17 sme pri G0-F1 videli, ďalší model sa na ňom nedá poctivo zmerať. Jediné
neznáme dáta sú zostávajúce preteky 2026: Austin, Mexiko, Brazília, Las Vegas, Katar, Abu Dhabi.

## Model B (zmrazený po schválení)

Model A z G0-F1 + jedna zmena stanovená vopred: **pri zmene technických pravidiel (2017, 2022,
2026) sa Elo jazdcov aj tímov vynuluje.** Zmeny pravidiel sú dané FIA, nie ladené. Ostatné
ladené len na tréningu 2014 – 2025: Elo jazdca K 48, Elo tímu K 8, prenos do sezóny 0,5;
váhy logitu kvalifikácia 0,805, Elo jazdca 1,455, Elo tímu −0,909 (na 100 Elo).

Riziko: váha Ela tímu je záporná – Elo jazdca zachytáva aj auto a obe sa prekrývajú. Model
to vyvažuje, ale pri prestupe jazdca do slabšieho tímu môže chvíľu preceňovať jazdca.

Orientačne (už videné dáta, **nie dôkaz**, `reports/f1_model_b.md`): 2026 kolá 1 – 17 log loss
1,1061 vs. kvalifikácia 1,1473; na starých pravidlách 2023 – 2025 rovnako dobrý ako model A
(1,0278 vs. 1,0227).

## Prevádzka (mimo appky)

- Tip sa zamkne **po kvalifikácii Veľkej ceny, pred štartom pretekov** do
  `archive/f1/predictions/2026-<kolo>.json` (šanca každého jazdca na víťazstvo a pódium).
- Po pretekoch: vyhodnotenie do `reports/f1_live.md`, Elo sa aktualizuje výsledkom (bežná
  prevádzka modelu, nie zmena).
- Beží vo vlastnom workflow `f1.yml` (sobota po kvalifikácii, nedeľa po pretekoch), nie
  v `predict.yml` – ten je počas G2 NBA zmrazený. Stav modelu v `state/f1_state.json`, takže
  beh potrebuje z Jolpica len pár požiadaviek (limit 500/h).

## Kritériá – všetky musia platiť (6 pretekov 25. 10. – 6. 12. 2026)

**Prevádzka (bez výnimky)**

1. Každé zo 6 pretekov má tip zamknutý po kvalifikácii a pred štartom.
2. Každé je vyhodnotené v `reports/f1_live.md` s výsledkom z Jolpica.
3. Nezávislý prepočet z archívu (log loss, presnosť) sa zhoduje s reportom.

**Model**

4. Log loss víťaza modelu B za 6 pretekov ≤ log loss baseline „kvalifikácia“ − 0,0005
   (tá istá tabuľka z tréningu ako pri G0-F1).

Presnosť a Brier pódia sa len zapíšu. **6 pretekov je malá vzorka:** jeden nečakaný víťaz
z 10. miesta výsledok otočí. Prejdenie znamená „model nie je horší než kvalifikácia a prevádzka
funguje“, nie istotu.

## Po meraní (vyhodnotenie 7. 12. 2026)

Prejde → F1 v appke ako beta od sezóny 2027 (rozpis 2027 ešte nie je zverejnený), G2-F1 na
prvých pretekoch 2027. Neprejde → zapíše sa príčina, F1 sa vráti pred sezónou 2027.
