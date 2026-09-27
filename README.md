# Team Pulse

![CI](https://github.com/peterolah-qa/team-pulse/actions/workflows/ci.yml/badge.svg)

Model stavu NBA teamov: pred každým zápasom priradí teamu jednu zo 4 úrovní
(Silný / Stabilný / Oslabený / Kritický) a vysvetlí prečo. Základ je Elo model
FiveThirtyEight, nad ním vlastné vrstvy (dostupnosť hráčov, únava, istota).

> Neoficiálny osobný projekt, bez spojenia s NBA, na štatistické účely.
> Nie je to stávková služba.

## Výsledky – fáza 0a (vrstva A: Elo)

**Replikácia FiveThirtyEight** – naše Elo prepočítané na 33 094 zápasoch od roku 2000
a porovnané s archívom FiveThirtyEight:

| Metrika | Výsledok |
|---|---|
| Priemerná odchýlka Elo | 0,008 bodu |
| Zápasy s odchýlkou pod 1 Elo | 99,81 % |
| Max. odchýlka pravdepodobnosti | 0,7 p. b. |

**Backtest** – sezóny 2003/04 – 2025/26, každá predpoveď len z dát pred zápasom:

| Model | Presnosť | Log loss | Brier |
|---|---|---|---|
| **Elo, domáca výhoda +70 (náš variant)** | **66,4 %** | **0,6108** | **0,2116** |
| Elo FiveThirtyEight (+100) | 66,1 % | 0,6145 | 0,2131 |
| Baseline: lepšia bilancia | 63,8 % | 0,6578 | 0,2325 |
| Baseline: vždy domáci | 58,5 % | 0,6793 | 0,2431 |

Celý report vrátane kalibrácie: [reports/backtest.md](reports/backtest.md)

## Výsledky – fáza 0b (vrstvy B + C, naučené váhy)

Logistická regresia sa učí na sezónach 2003/04 – 2022/23 a testuje na 2023/24 – 2025/26
(3 931 zápasov, ktoré pri učení nevidela):

| Model | Presnosť | Log loss | Brier |
|---|---|---|---|
| A: Elo (FiveThirtyEight, HCA 70) | 66,4 % | 0,6108 | 0,2116 |
| + C: únava (back-to-back, časové pásma, výška…) | 66,8 % | 0,6081 | 0,2104 |
| + B: chýbajúci hráči | 67,3 % | 0,6039 | 0,2087 |
| **+ sila súpisky** | **67,3 %** | **0,5996** | **0,2068** |

Zamietnuté vylepšenia a ich dôvody sú v [docs/gate-G1.md](docs/gate-G1.md),
naučené váhy v [reports/learned.md](reports/learned.md).

## Ako je to otestované

| Test | Čo stráži |
|---|---|
| Test úniku dát pre každú vrstvu | Únava, hráči aj sila súpisky nezávisia od budúcich zápasov |
| Unit testy | Vzorce proti ručne spočítaným príkladom a skutočným číslam z archívu |
| Property-based (Hypothesis) | Pravdepodobnosť 0–1, súčet Elo sa nemení, víťaz vždy získa |
| Replikácia | Zhoda s archívom FiveThirtyEight na 33 094 zápasoch |
| Únik dát z budúcnosti | Zmena výsledku zápasu nezmení žiadnu skoršiu predpoveď |
| CI | Lint + všetky testy pri každom pushi |

## Spustenie

```bash
uv sync
uv run python -m team_pulse.data.fetch_games --from 2001 --to 2026   # stiahne výsledky
uv run python -m team_pulse.backtest                                 # backtest + report
curl -L -o data/ref/nba_elo.csv https://raw.githubusercontent.com/Neil-Paine-1/NBA-elo/main/nba_elo.csv
uv run pytest                                                        # všetky testy
```

## Roadmapa

- [x] **0a** – Elo (vrstva A), replikácia, backtest, CI → brána G0 ✅
- [x] **0b** – Dostupnosť hráčov, únava, sila súpisky, naučené váhy → brána G1 ✅
- [ ] **1** – Dátový agent + databáza → brána G2
- [ ] **2** – Web appka (PWA, cyberpunk dizajn) → brána G3
- [ ] **3** – Portfólio

## Zdroje

- Metodika Elo: FiveThirtyEight, archív [Neil-Paine-1/NBA-elo](https://github.com/Neil-Paine-1/NBA-elo)
- Dáta: [nba_api](https://github.com/swar/nba_api) (stats.nba.com)
