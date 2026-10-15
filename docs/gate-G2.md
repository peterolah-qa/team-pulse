# Brána G2 – NBA: 14 dní ostrej prevádzky (stanovené vopred, 14. 10. 2026)

Obdobie: zápasy základnej časti s dátumom **20. 10. – 2. 11. 2026** (dni v USA, ET).
Vyhodnotenie: ráno 3. 11. 2026. Počas obdobia sa kód NBA nemení (model, predikcie, archív,
ranná úloha, `predict.yml`).

Hranice sú stanovené pred meraním z backtestu (`scripts/g2_reference.py` → `reports/g2_reference.md`)
a počas obdobia sa nemenia.

## Prečo takto

14 dní je asi 100 zápasov. To stačí na overenie, že prevádzka beží bez chyby a že model nie je
pokazený, ale nie na dôkaz, že je lepší než v backteste. Porovnanie s trhom (kurzy) brána nemeria,
kurzy nepoužívame. Začiatok sezóny je pre model ťažší: v backteste mal v prvých 14 dňoch log loss
0,634 (celá sezóna 0,597), lebo Elo prenesené cez leto a nové súpisky sú menej presné.

## Kritériá – všetky musia platiť

**Prevádzka (bez výnimky)**

1. Každý zápas základnej časti z obdobia má v archíve (`archive/predictions/`) tip zamknutý
   pred začiatkom zápasu.
2. Každý z týchto zápasov má v archíve výsledok (`archive/results/`).
3. Nezávislý prepočet z archívu (počet zápasov, trafené tipy, log loss) sa zhoduje s `reports/live.md`.
4. Každý deň obdobia je do 12:00 (náš čas) v `main` stav z Macu (`state/state.json`) s výsledkami
   všetkých zápasov predchádzajúceho dňa v USA. Overí sa z histórie commitov stavu.

**Model (hranice z backtestu)**

5. Log loss modelu za obdobie ≤ **0,6739**. To je 95. percentil log loss v 14-dňových oknách
   základnej časti testovacích sezón 2023/24 – 2025/26 (483 okien). Všetky tri začiatky sezón
   v backteste boli pod hranicou (0,620 / 0,648 / 0,634).
6. Log loss modelu je nižší než baseline „vždy domáci“ (58,7 %, z tréningových sezón) na tých istých
   zápasoch. V backteste model s baseline prehral len v 3,1 % 14-dňových okien.

Presnosť a kalibrácia sa len zapíšu (v backteste 14-dňové okná 58,1 – 78,5 %, medián 67,2 %).

## Keď brána neprejde

Zapíše sa príčina. Oprava ide až po skončení obdobia, potom sa meranie opakuje 14 dní.
Model sa počas merania nemení. Zmenu modelu len navrhnem, schvaľuje Peter.

## Oprava dát pred začiatkom (14. 10. 2026)

V histórii NBA chýbali zápasy na neutrálnej pôde: 5 v sezóne 2024/25 (Mexiko, 2× Paríž,
2× semifinále NBA Cupu vo Vegas) a 5 v sezóne 2025/26 (Mexiko, Berlín, Londýn, 2× semifinále
NBA Cupu). nba_api ich od 2024/25 zapisuje bez „vs.“ a `normalize()` ich zahodil. Oprava ich páruje
podľa zápisu „HOSTIA @ DOMÁCI“, ktorý sa zhoduje s rozpisom NBA, a označí ich ako neutrálne. Všetky
teamy majú teraz v oboch sezónach 82 zápasov. Elo sa zmenilo najviac o 2,6 bodu, backtest
nepatrne (log loss 0,59963 → 0,59975). V období G2 taký zápas nie je, prvý je 7. 11. 2026
(DEN @ IND, Mexiko).

Na opravených dátach by hranica kritéria 5 vyšla 0,6751. Ostáva **0,6739**, ktorá bola stanovená
vopred a je prísnejšia.
