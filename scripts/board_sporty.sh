#!/usr/bin/env bash
# Team Pulse – nový board „Team Pulse – športy“ (NHL, jadro, extraliga, F1). Plán: docs/sporty.md
# Board vznikne kópiou boardu „Team Pulse“ (rovnaké stĺpce a zobrazenia, bez úloh).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_sporty.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"
TITLE="Team Pulse – športy"

project_number () {  # $1 názov boardu → číslo alebo nič
  gh project list --owner "$OWNER" --limit 100 --format json --jq ".projects[] | select(.title==\"$1\") | .number"
}

NUM=$(project_number "$TITLE")
if [ -z "$NUM" ]; then
  OLD=$(project_number "Team Pulse")
  if [ -n "$OLD" ]; then
    NUM=$(gh project copy "$OLD" --source-owner "$OWNER" --target-owner "$OWNER" --title "$TITLE" --format json --jq '.number')
  else
    NUM=$(gh project create --owner "$OWNER" --title "$TITLE" --format json --jq '.number')
  fi
  echo "Nový board: $TITLE (#$NUM)"
fi
gh project link "$NUM" --owner "$OWNER" --repo "$REPO" >/dev/null 2>&1 || true

# štítky: existujúce sa nemenia
label () { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 || true; }
label nhl       0b6e99 "NHL"
label extraliga 1d4ed8 "Tipos extraliga"
label f1        e10600 "Formula 1"
label core      6f42c1 "Spoločné jadro pre všetky športy"
label model     fbca04 "Model a backtest"
label app       0e8a16 "Appka"
label test      c5def5 "Testy a brány"
label infra     5319e7 "Workflowy, deploy, zdroje"
label docs      0075ca "Dokumentácia"

# míľniky = fázy z docs/sporty.md
M1="Š1 – NHL: dáta a backtest"
M2="Š2 – Spoločné jadro (po G2)"
M3="Š3 – NHL v appke"
M4="Š4 – Tipos extraliga"
M5="Š5 – F1 (sezóna 2027)"
MILESTONES=$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
milestone () {
  grep -Fxq -- "$1" <<< "$MILESTONES" || gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
}
milestone "$M1" "Sťahovač histórie, hokejové Elo, backtest. Len vetva nhl, NBA sa počas G2 nemení."
milestone "$M2" "core/ + sports/nba/, appka a výstupy bez zmeny. Od 4. 11. po G2."
milestone "$M3" "Živé dáta NHL, prepínač športu, hokejové štatistiky, 14 dní ostro."
milestone "$M4" "Overiť zdroj a podmienky, história, backtest, appka."
milestone "$M5" "Model pretekov cez zimu, ostro od prvých pretekov 2027."

EXISTING=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url --jq '.[] | "\(.title)\t\(.url)"')

add () {  # $1 názov, $2 štítky, $3 míľnik, $4 popis, $5 done|open
  URL=$(awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$EXISTING")
  if [ -n "$URL" ]; then
    gh project item-add "$NUM" --owner "$OWNER" --url "$URL" >/dev/null
    echo "= $1 (už je na boarde)"
    return
  fi
  URL=$(gh issue create --repo "$REPO" --title "$1" --label "$2" --milestone "$3" --body "$4")
  gh project item-add "$NUM" --owner "$OWNER" --url "$URL" >/dev/null
  if [ "$5" = "done" ]; then
    gh issue close "$URL" --reason completed --comment "Hotové: docs/sporty.md" >/dev/null
    echo "✓ $1"
  else
    echo "○ $1"
  fi
}

# Š1 – NHL: dáta a backtest
add "Plán: viac športov v jednej appke" "docs" "$M1" \
  'docs/sporty.md: architektúra (core + sports), fázy Š1 – Š5, pravidlá, brána G0-NHL stanovená vopred.' "done"
add "NHL: overiť zdroje dát (API NHL, ESPN hokej)" "nhl,infra" "$M1" \
  'Ukážky odpovedí (rozpis, výsledky, box score, súpisky, zranenia) do tests/fixtures/nhl_*.json pre contract testy. Spúšťa sa z Macu.' open
add "NHL: sťahovač histórie zápasov 2005/06 – 2025/26" "nhl" "$M1" \
  'Jeden riadok na zápas: dátum, domáci, hostia, góly, predĺženie alebo nájazdy, typ zápasu. data/raw/nhl_games.parquet sa necommituje. Testy na fixtures.' open
add "NHL: hokejové Elo (vrstva A)" "nhl,model" "$M1" \
  'K, domáca výhoda, násobič podľa rozdielu gólov. Parametre ladené len na tréningových sezónach. Test úniku dát.' open
add "NHL: backtest a baseline" "nhl,model,test" "$M1" \
  'reports/nhl_backtest.md: presnosť, log loss, Brier, kalibrácia, po sezónach. Baseline: vždy domáci, lepšia bilancia.' open
add "Brána G0-NHL: rozhodnutie" "nhl,docs" "$M1" \
  'Kritérium z docs/sporty.md: log loss Ela na testovacích sezónach o ≥ 0,0005 nižší než obe baseline. Výsledok do docs/gate-nhl-G0.md.' open

# Š2 – Spoločné jadro (po G2)
add "Jadro: core/ + sports/nba/ bez zmeny správania" "core" "$M2" \
  'Presun modulov a importov. Všetky pytest a Playwright testy zelené, denný beh na Macu aj v cloude ide ďalej. Až po skončení G2 (3. 11.).' open
add "Jadro: rovnaké JSON výstupy pred a po presune" "core,test" "$M2" \
  'Zlatý test: z rovnakého stavu vznikne rovnaký predictions, teams a model JSON.' open
add "Jadro: dáta appky po športoch (data/nba/…)" "core,app" "$M2" \
  'Appka číta data/<šport>/. Staré cesty fungujú, kým sa nainštalovaná appka neaktualizuje.' open
add "Jadro: workflow a kontrola zdrojov na šport" "core,infra" "$M2" \
  'Vlastný rozvrh pre každý šport, jeden spoločný deploy na Pages. Kontrola zdrojov hlási, ktorý šport zlyhal.' open

# Š3 – NHL v appke
add "NHL: živé dáta – rozpis, výsledky, zranenia (ESPN hokej)" "nhl" "$M3" \
  'ESPN adaptéry s parametrom športu (hockey/nhl). Archív tipov a zamknutie 24 h pred zápasom ako pri NBA.' open
add "NHL: návrh vrstiev – brankár, únava" "nhl,model" "$M3" \
  'Kandidáti: kto chytá, back-to-back, cestovanie. Každá vrstva musí zlepšiť log loss na teste o ≥ 0,0005, inak sa nepridá. Schvaľuje Peter.' open
add "Appka: prepínač športu NBA / NHL" "app" "$M3" \
  'Hore v appke, pamätá si posledný výber. E2E, a11y a vizuálne testy pre oba športy.' open
add "Appka: hokejové štatistiky hráčov" "app,nhl" "$M3" \
  'Výsledok: góly, asistencie, body, +/−, čas na ľade. Brankári: zákroky a úspešnosť.' open
add "Brána G2-NHL: 14 dní ostrej prevádzky" "nhl,test" "$M3" \
  'Ako G2 pri NBA: tipy zamknuté pred zápasom, vyhodnotenie v reports/live.md.' open

# Š4 – Tipos extraliga
add "Extraliga: overiť zdroj dát a podmienky používania" "extraliga" "$M4" \
  'hockeyslovakia.sk: robots.txt a podmienky používania, prípadne súhlas SZĽH. Bez povolenia sa nesťahuje.' open
add "Extraliga: história a backtest s hokejovým Elo" "extraliga,model" "$M4" \
  'Rovnaké kritérium ako G0-NHL, hranica stanovená pred meraním.' open
add "Extraliga: v appke a ostré meranie" "extraliga,app" "$M4" \
  'Prepínač športu a 14 dní ostrej prevádzky.' open

# Š5 – F1 (sezóna 2027)
add "F1: zdroje dát (Jolpica, OpenF1)" "f1,infra" "$M5" \
  'História pretekov a kvalifikácií, rozpis 2027. Overiť dostupnosť a limity.' open
add "F1: model pretekov a backtest" "f1,model" "$M5" \
  'Šanca na víťaza a pódium. Od 2026 platia nové pravidlá, staršie sezóny predpovedajú horšie.' open
add "F1: obrazovky v appke" "f1,app" "$M5" \
  'Preteky, jazdci, tímy. Bez lôg, len farby tímov.' open
add "F1: ostrá prevádzka od prvých pretekov 2027" "f1,test" "$M5" \
  'Tipy zamknuté pred štartom, vyhodnotenie po pretekoch.' open

echo "Hotovo: https://github.com/users/$OWNER/projects/$NUM"
