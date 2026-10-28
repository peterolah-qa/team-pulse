# Brána G0-ATP a G0-WTA – kritériá (stanovené 28. 10. 2026 pred meraním)

Backtest tenisového modelu (`docs/tennis.md`) na histórii z archívnej kópie dát Jeffa Sackmanna
(`Aneeshers/tennis-sackmann-archive`, commit `83733587`, CC BY-NC-SA 4.0). Kritériá sú napísané a commitnuté
**pred prvým behom modelu na testovacích sezónach**; po commite sa nemenia. ATP a WTA sú dve samostatné
brány s rovnakými kritériami; každý okruh ide ďalej sám za seba.

## Dáta

- **Zápasy:** dvojhra, hlavné súťaže okruhu (bez kvalifikácie).
  - ATP: úrovne G, M, A, F, O; bez Next Gen Finals (iné pravidlá: kratšie sety).
  - WTA: úrovne G, PM, P, I, F, O a W okrem turnajov WTA 125 (názov obsahuje „125“).
  - Bez Davis Cupu a BJK Cupu (D) a turnajov ITF vo WTA dátach (50+H, 35+H a podobné).
- **Kontumácia (W/O)** sa nepoužije nikde. **Skreč (RET)** sa nevyhodnocuje; či skreč mení Elo, sa rozhodne
  len na tréningových sezónach.
- **Poradie zápasov:** podľa dátumu turnaja, turnaja a kola (R128 → … → F, skupina RR pred SF, BR pred F),
  v kole podľa `match_num`. Hráč hrá v kole najviac raz, takže tip na zápas používa len výsledky
  predchádzajúcich kôl a turnajov.
- **Sezóny:**
  - zahrievanie Ela (len výpočet hodnotení, nič sa nemeria ani neladí): 1990 – 2014,
  - tréning (ladenie parametrov Ela, váh vrstiev a baseline): 2015 – 2022,
  - **test: 2023 – 2025.** Sezóna 2026 (do Roland Garros) a doplnená medzera z ESPN sa do G0 nerátajú.

## Baseline (naučené len na tréningu)

1. **Rebríček:** šanca vyššie postaveného hráča = σ(β · (ln rank_súpera − ln rank_hráča)), β z tréningu;
   hráč bez rebríčka má rank 1 500.
2. **Body v rebríčku:** σ(β · (ln body_hráča − ln body_súpera)), β z tréningu; hráč bez bodov má 1 bod.

Porovnáva sa s **lepšou** z týchto dvoch baseline na testovacích sezónach.

## Kritériá (pre každý okruh zvlášť)

| # | Kritérium | Cieľ |
|---|---|---|
| 1 | Úplnosť dát | počet zápasov v backteste = počet v archíve po filtroch, po sezónach; žiadny zápas dvakrát |
| 2 | Log loss Ela na teste vs. lepšia baseline | Elo nižšie aspoň o **0,0005** |
| 3 | Test úniku dát | prechádza, overené aj úmyselnou chybou (tip so znalosťou výsledku musí test zhodiť) |
| 4 | Contract test ESPN tenis | prechádza na tvare skutočnej odpovede (sonda 28. 10. 2026) |

Presnosť, Brier a kalibrácia (pásma po 10 p. b.) sa zapíšu, ale bránu nerozhodujú.

## Vrstvy po G0

Povrch, na 3 / 5 setov a únava sa pridávajú po jednej. Každá musí na testovacích sezónach zlepšiť log loss
aspoň o **0,0005** oproti modelu bez nej; inak sa nepridá. Zmenu modelu navrhnem, schvaľuje Peter.

## Po bráne

Prejde → okruh ide do appky ako beta (po jadre) a ostré meranie G2 na Australian Open 17. – 31. 1. 2027
(kritériá G2 sa stanovia pred 1. 1. 2027). Neprejde → zapíše sa príčina, oprava a nové meranie na tých istých
testovacích sezónach sa nepovažuje za nezávislé (zapíše sa ako druhý pokus).
