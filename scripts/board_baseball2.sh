#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Bejzbal po sonde zdrojov (28. 10. 2026): LVBP vypustená, MLB bez MLB Stats API, bejzbal pozastavený
# (pokračuje sa tenisom). Predpoklad: bash scripts/board_baseball.sh. Zdôvodnenie: docs/journal.md (28. 10.).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_baseball2.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

SPORTY=$(gh project list --owner "$OWNER" --limit 100 --format json \
  --jq '.projects[] | select(.title=="Team Pulse – športy") | .number')
if [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse – športy“"
  exit 1
fi

state () { gh issue view "$1" --repo "$REPO" --json state --jq .state; }
close_no () {  # $1 číslo, $2 dôvod (completed | not planned), $3 komentár
  if [ "$(state "$1")" != "CLOSED" ]; then
    gh issue close "$1" --repo "$REPO" --reason "$2" --comment "$3" >/dev/null
    echo "✓ #$1"
  else
    echo "= #$1 (už zavreté)"
  fi
}
milestone_no () { gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title==\"$1\") | .number"; }

LVBP="LVBP vypustená 28. 10.: jediný štruktúrovaný zdroj je MLB Stats API (podmienky MLBAM len pre individuálne použitie) a nemá ani jedného ohláseného nadhadzovača (model len Elo + domáci, malá vzorka). docs/baseball.md, docs/journal.md."

close_no 116 completed "Sonda prebehla 28. 10. (výstup v docs/journal.md). Retrosheet a archív 538 OK; živé dáta MLB overí sonda ESPN pri pokračovaní bejzbalu."
close_no 117 "not planned" "Rozhodnutie 28. 10.: MLB Stats API nepoužijeme. Podmienky MLBAM: „Only individual, non-commercial, non-bulk use … any other use … prohibited without prior written authorization“. História MLB z Retrosheetu, živé dáta z ESPN."
for n in 118 122 126 129; do close_no "$n" "not planned" "$LVBP"; done

gh issue edit 120 --repo "$REPO" --title "Bejzbal: kritériá G0-MLB vopred" \
  --body 'docs/gate-mlb-G0.md pred prvým behom backtestu: testovacie sezóny 2023 – 2025, baseline „vždy domáci“, prínos vrstvy ≥ 0,0005, kalibrácia, replikácia 538 (archívna kópia mlb_elo.csv).' >/dev/null
echo "~ #120 len MLB"
M9="Š9 – Bejzbal v appke (beta)"
gh issue edit 128 --repo "$REPO" --milestone "$M9" \
  --body 'Ranná úloha na Macu 10:30 pre MLB od 25. 3. 2027: zamknutie tipov (archive/baseball/mlb/predictions), uložený ohlásený nadhadzovač (ESPN), vyhodnotenie, reports/mlb_live.md. Len na main, launchd ako NBA a NHL.' >/dev/null
echo "~ #128 → $M9"

URL=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url \
  --jq '.[] | select(.title=="MLB: živé dáta z ESPN (sonda)") | .url')
if [ -z "$URL" ]; then
  URL=$(gh issue create --repo "$REPO" --title "MLB: živé dáta z ESPN (sonda)" --label "bejzbal,infra" \
    --milestone "Š6 – Bejzbal: zdroje" \
    --body 'Sonda z Macu: rozpis, výsledky a ohlásení nadhadzovači v ESPN MLB (scoreboard, summary), skratky tímov ESPN ↔ Retrosheet, zrušené a odložené zápasy.')
  echo "+ MLB: živé dáta z ESPN (sonda)"
fi
gh project item-add "$SPORTY" --owner "$OWNER" --url "$URL" >/dev/null

M6=$(milestone_no "Š6 – Bejzbal: zdroje")
M7=$(milestone_no "Š7 – Bejzbal: model a G0")
M8=$(milestone_no "Š8 – LVBP naostro mimo appky")
gh api -X PATCH "repos/$REPO/milestones/$M6" -f description="Sonda 28. 10.: Retrosheet a archív 538 OK, MLB Stats API a LVBP nie (podmienky MLBAM). Ďalej sonda ESPN MLB. Pozastavené 28. 10." >/dev/null
gh api -X PATCH "repos/$REPO/milestones/$M7" -f description="História z Retrosheetu, Elo (replikácia 538), nadhadzovač, cestovanie a odpočinok; G0-MLB. Po jadre, do marca 2027." >/dev/null
gh api -X PATCH "repos/$REPO/milestones/$M8" -f state=closed -f description="Vypustené 28. 10.: LVBP len cez MLB Stats API (podmienky MLBAM), bez nadhadzovačov." >/dev/null
echo "~ míľniky Š6, Š7 upravené, Š8 zavretý"

echo "Hotovo: https://github.com/users/$OWNER/projects/$SPORTY"
