#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Redizajn appky (20. 10. 2026): návrh „Luminous Pulse“ zo Stitch s úpravami podľa pravidiel projektu.
# Etapy: 1 dizajnový systém, 2 detail NHL, 3 detail NBA, 4 ostatné obrazovky, 5 testy a kontrola na iPhone.
# Rozhodnutie a zdôvodnenie: docs/journal.md (20. 10.), pravidlo pre obrazovky počas G2: docs/sporty.md.
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_redizajn.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

project_number () {  # $1 názov boardu → číslo alebo nič
  gh project list --owner "$OWNER" --limit 100 --format json --jq ".projects[] | select(.title==\"$1\") | .number"
}
NBA=$(project_number "Team Pulse")
SPORTY=$(project_number "Team Pulse – športy")
if [ -z "$NBA" ] || [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse“ alebo „Team Pulse – športy“"
  exit 1
fi

label () { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 || true; }
label design 8b5cf6 "Vzhľad a použiteľnosť appky"

M="R – Redizajn appky"
if [ -z "$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title==\"$M\") | .number")" ]; then
  gh api -X POST "repos/$REPO/milestones" -f title="$M" \
    -f description="Návrh Luminous Pulse (Stitch) s úpravami: bez kurzov a log, len skutočné čísla. Etapy 1 – 5, od 20. 10. 2026." >/dev/null
  echo "▸ $M"
fi

ISSUES=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url,state \
  --jq '.[] | "\(.title)\t\(.url)\t\(.state)"')
url_of ()   { awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$ISSUES"; }
state_of () { awk -F'\t' -v t="$1" '$1 == t { print $3; exit }' <<< "$ISSUES"; }

add () {  # $1 boardy (čísla oddelené čiarkou), $2 názov, $3 štítky, $4 popis, $5 done|open
  local url
  url=$(url_of "$2")
  if [ -z "$url" ]; then
    url=$(gh issue create --repo "$REPO" --title "$2" --label "$3" --milestone "$M" --body "$4")
    echo "+ $2"
  else
    echo "= $2"
  fi
  local board
  for board in ${1//,/ }; do
    gh project item-add "$board" --owner "$OWNER" --url "$url" >/dev/null
  done
  if [ "$5" = "done" ] && [ "$(state_of "$2")" != "CLOSED" ]; then
    gh issue close "$url" --reason completed --comment "Hotové." >/dev/null
    echo "✓ $2"
  fi
}

# --- hotové v tomto kroku (etapa 1 a 2) ---
add "$NBA" "Redizajn 1: dizajnový systém Luminous Pulse" "app,design" \
  'Farby (tmavá aj svetlá téma, kontrast WCAG AA), písmo Space Grotesk + Inter, ploché karty, plávajúci dok, odznaky vo farbách dresu namiesto 3D mincí, bez pozadia ihriska a 3D náklonu. Platí pre NBA aj NHL.' "done"
add "$NBA,$SPORTY" "Redizajn 2: detail NHL zápasu" "app,design,nhl" \
  'Hlavná karta (šanca, tip, bilancia, forma 5, odpočinok), istota tipu, prečo X % (Elo body, súčet = zamknutá šanca), Elo trend, odpočinok a cestovanie, forma v sezóne, porovnanie s poradím v lige, vzájomné zápasy, chýbajúci hráči, zdieľanie. Bez kurzov a log.' "done"
add "$SPORTY" "NHL: kontext zápasu pre detail" "nhl,data" \
  'team_pulse.nhl.context v app_data: rozpad tipu (overený: model z rozpisu znova dá zamknutú šancu), Elo trend z archívu, forma, odpočinok ako vstupy modelu, vzájomné zápasy (táto a minulá sezóna), štatistiky NHL len po kontrole zápasov a výhier. Rozpisy v cache na Pages (sťahuje sa len to, čo sa zmenilo). Model ani tipy sa nemenia (G2-NHL).' "done"
add "$NBA,$SPORTY" "Sledovať zápas (NHL)" "app" \
  'Prichytené tlačidlo v detaile. Po dohraní upozornenie v appke s výsledkom a či tip vyšiel. Len v zariadení (localStorage), nie push mimo appky.' "done"

# --- ďalej ---
add "$SPORTY" "Overiť detail NHL so skutočnými dátami" "nhl,test" \
  'Pred commitom: uv run python scripts/probe_nhl_context.py (rozpad overený pri všetkých tipoch, štatistiky NHL sedia s rozpisom). Po deployi: detail na živej appke (iPhone), varovania v Actions (NHL kontext).' open
add "$NBA" "Redizajn 3: detail NBA zápasu" "app,design" \
  'Rovnaký štýl ako NHL: hlavná karta, istota tipu, prečo X % v Elo bodoch, otázni hráči („čo keby“), forma, Sledovať zápas. Len appka, model a predikcie NBA sa počas G2 nemenia.' open
add "$NBA,$SPORTY" "Redizajn 4: Zápasy, Tipy, Výsledky, Teamy" "app,design" \
  'Nové karty zoznamov, prepínač kompaktný / podrobný zoznam, filter Moje teamy.' open
add "$NBA,$SPORTY" "Moje teamy: pripnuté hore" "app" \
  'Hviezdička pri teame, jeho zápasy hore v zozname a filter. Pamäť v zariadení.' open
add "$NBA,$SPORTY" "Bilancia: úspešnosť tipov naostro" "app" \
  'Tento týždeň a celá sezóna: tip vyšiel X z Y, log loss oproti hranici brány, kalibrácia. Bez ROI a kurzov.' open
add "$NBA" "Sledovať zápas aj pre NBA" "app" \
  'Rovnaké tlačidlo a upozornenie ako pri NHL.' open
add "$NBA" "Nová ikona appky v štýle Luminous Pulse" "app,design" \
  'Ikona na ploche a v prehliadači (fialový pulz na tmavom), maskable verzia, apple-touch-icon.' open
add "$NBA" "Redizajn 5: testy a kontrola na iPhone" "app,test" \
  'E2E, prístupnosť (tmavá aj svetlá téma), vizuálne snapshoty po každej etape, ručná kontrola PWA na iPhone.' open

echo "Hotovo: https://github.com/users/$OWNER/projects/$NBA a /projects/$SPORTY"
