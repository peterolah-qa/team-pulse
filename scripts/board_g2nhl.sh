#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Board po bráne G2-NHL (28. 10. 2026): G2-NHL splnená, NHL bez bety, vizuálne snímky z CI
# a upratanie hotových / duplicitných úloh. Zdôvodnenie: docs/journal.md (28. 10.).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_g2nhl.sh
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

ISSUES=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url,state \
  --jq '.[] | "\(.title)\t\(.url)\t\(.state)"')
url_of ()   { awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$ISSUES"; }

close_no () {  # $1 číslo, $2 dôvod (completed | not planned), $3 komentár
  if [ "$(gh issue view "$1" --repo "$REPO" --json state --jq .state)" != "CLOSED" ]; then
    gh issue close "$1" --repo "$REPO" --reason "$2" --comment "$3" >/dev/null
    echo "✓ #$1"
  else
    echo "= #$1 (už zavreté)"
  fi
}

done_issue () {  # $1 boardy (čísla oddelené čiarkou), $2 míľnik, $3 názov, $4 štítky, $5 popis
  local url
  url=$(url_of "$3")
  if [ -z "$url" ]; then
    url=$(gh issue create --repo "$REPO" --title "$3" --label "$4" --milestone "$2" --body "$5")
    echo "+ $3"
  else
    echo "= $3"
  fi
  local board
  for board in ${1//,/ }; do
    gh project item-add "$board" --owner "$OWNER" --url "$url" >/dev/null
  done
  if [ "$(gh issue view "$url" --json state --jq .state)" != "CLOSED" ]; then
    gh issue close "$url" --reason completed --comment "Hotové 28. 10. 2026." >/dev/null
    echo "✓ $3"
  fi
}

close_no 63 completed \
  "Splnená 28. 10. 2026: 98 z 98 tipov zamknutých pred začiatkom a vyhodnotených, prepočet = report, log loss 0,6686 (hranica 0,7101), tip vyšiel 59 z 98 (60,2 %). reports/gate_g2_nhl.md"
close_no 85 completed \
  "Hotové: cron-job.org spúšťa Kontrolu zdrojov každý deň (od 25. 10. o 12:30 UTC = 13:30 po zmene času), plán GitHubu ostáva ako záloha."
close_no 59 completed \
  "Hotové: rozpis, výsledky a zranenia (ESPN) sú v appke od 14. 10., kontext zápasu od 20. 10. Overenie na živej appke pokračuje v #94."
close_no 35 completed \
  "Hotové: stav modelu z Macu a predpovede ako JSON sa publikujú na GitHub Pages (predict.yml) od G2."
close_no 47 "not planned" \
  "Duplicitné s #101 (Redizajn 5: testy a kontrola na iPhone), ručná kontrola PWA na iPhone pokračuje tam."

done_issue "$SPORTY" "Š2 – NHL v appke (beta)" "NHL bez označenia beta" "app,nhl" \
  'Po splnení G2-NHL: preč „beta“ pri prepínači aj poznámka na obrazovkách NHL, na Model NHL výsledok G2-NHL, dáta "beta": false. Model, tipy a archív bez zmeny.'
done_issue "$NBA,$SPORTY" "R – Redizajn appky" "Vizuálne snímky z CI (workflow Appka, snimky)" "test,infra" \
  'Ručné spustenie workflow Appka s voľbou snimky na vetve (nie main): testy + nové snímky z prehliadača CI, commit do vetvy. Lokálny prehliadač kreslí písmo inak.'

echo "Otvorené ostáva: #34 a #75 (G2 NBA 3. 11.), #89 (F1 cron-job.org pred 31. 10.), #94, #95, #97 – #99, #101."
echo "Hotovo: https://github.com/users/$OWNER/projects/$NBA a /projects/$SPORTY"
