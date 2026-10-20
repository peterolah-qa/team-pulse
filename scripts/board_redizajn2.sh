#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Redizajn appky, druhý krok (20. 10. 2026 popoludní): celý ekosystém obrazoviek podľa Petrovho zadania –
# paleta podľa úrovní formy, pás dní, balíček kariet, prehľad dňa, Tipy, Teamy ako karusel, Model, počítač.
# Predpoklad: bash scripts/board_redizajn.sh (míľnik „R – Redizajn appky“). Zdôvodnenie: docs/journal.md (20. 10.).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_redizajn2.sh
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
  echo "Chýba míľnik „$M“ (najprv bash scripts/board_redizajn.sh)"
  exit 1
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

# --- hotové v tomto kroku ---
add "$NBA,$SPORTY" "Paleta podľa úrovní formy, tip ako žiara" "app,design" \
  'Silný smaragd, Stabilný indigo, Oslabený jantár, Kritický rubín; tip fialovo-modrá žiara namiesto žltej. Odznak teamu s prstencom: NBA Pulse, NHL šanca na výhru. Kontrast WCAG AA v oboch témach.' "done"
add "$NBA,$SPORTY" "Zápasy: pás dní, balíček kariet a prehľad dňa" "app,design" \
  'Pás dní s počtom zápasov a najistejším tipom, Karty / Zoznam, balíček so švihom, šípkami a klávesnicou („Zápas 2 z 3“), karta s dôvodmi v prospech tipu, prehľad dňa (súčin tipov, najistejší tip, liga podľa formy, model).' "done"
add "$NBA,$SPORTY" "Počítač: Zápasy ako prehľad v dvoch stĺpcoch" "app,design" \
  'Karty dňa v mriežke vľavo, widgety prehľadu dňa vpravo; Teamy ako 4 stĺpce úrovní.' "done"
add "$NBA,$SPORTY" "Tipy: ukazovatele a graf súčinu šancí" "app,design" \
  'Najistejší tip, počet tipov, všetky naraz; graf: stĺpce = šanca tipu, čiara = súčin od prvého; pruh súčinu pri riadku.' "done"
add "$NBA" "Teamy: 4 úrovne formy ako karusel" "app,design" \
  'Silní / Stabilní / Oslabení / Kritickí so záložkami a švihom, Pulse s prstencom, posun oproti normálu a hlavný dôvod.' "done"
add "$NBA,$SPORTY" "Model: ukazovatele, kalibrácia a prínos vrstiev" "app,design" \
  'Presnosť, log loss, Brier; kalibračná krivka; log loss každej vrstvy a zmena oproti predchádzajúcej; váhy po rozkliknutí.' "done"
add "$NBA,$SPORTY" "README: aktuálny stav projektu" "docs" \
  'Obrazovky po redizajne, športy a brány (NBA, NHL, F1, extraliga), NHL model, testy, štruktúra, zdroje, obmedzenia, plán; nové screenshoty.' "done"
url=$(url_of "Redizajn 4: Zápasy, Tipy, Výsledky, Teamy")
if [ -n "$url" ] && [ "$(state_of "Redizajn 4: Zápasy, Tipy, Výsledky, Teamy")" != "CLOSED" ]; then
  gh issue close "$url" --reason completed \
    --comment "Hotové v kroku 2 redizajnu (pás dní, balíček kariet, prepínač Karty / Zoznam, Tipy, Teamy). Moje teamy pokračujú v samostatnej úlohe." >/dev/null
  echo "✓ Redizajn 4: Zápasy, Tipy, Výsledky, Teamy"
fi

echo "Hotovo: https://github.com/users/$OWNER/projects/$NBA a /projects/$SPORTY"
