#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# NFL na boarde „Team Pulse – športy“ (28. 10. 2026): míľniky Š12 a Š13 a úlohy podľa docs/nfl.md.
# Zdôvodnenie: docs/journal.md (28. 10.). Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_nfl.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

SPORTY=$(gh project list --owner "$OWNER" --limit 100 --format json \
  --jq '.projects[] | select(.title=="Team Pulse – športy") | .number')
if [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse – športy“"
  exit 1
fi

gh label create nfl --repo "$REPO" --color 013369 --description "NFL" >/dev/null 2>&1 || true

M12="Š12 – NFL: dáta, model a G0"
M13="Š13 – NFL naostro (G2) a v appke"
MILESTONES=$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
milestone () {
  grep -Fxq -- "$1" <<< "$MILESTONES" || gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
}
milestone "$M12" "nflverse games.csv (bez stávkových stĺpcov), Elo podľa 538, quarterback, odpočinok; G0-NFL do ~6. 11. Prednosť pred tenisom."
milestone "$M13" "nfl.yml v GitHub Actions od ~9. týždňa, G2-NFL do 10. 1. 2027; appka (beta) po jadre."

EXISTING=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url --jq '.[] | "\(.title)\t\(.url)"')

add () {  # $1 názov, $2 štítky, $3 míľnik, $4 popis, $5 done|open
  local url
  url=$(awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$EXISTING")
  if [ -n "$url" ]; then
    gh project item-add "$SPORTY" --owner "$OWNER" --url "$url" >/dev/null
    echo "= $1 (už je na boarde)"
  else
    url=$(gh issue create --repo "$REPO" --title "$1" --label "$2" --milestone "$3" --body "$4")
    gh project item-add "$SPORTY" --owner "$OWNER" --url "$url" >/dev/null
    echo "○ $1"
  fi
  if [ "$5" = "done" ] && [ "$(gh issue view "$url" --json state --jq .state)" != "CLOSED" ]; then
    gh issue close "$url" --reason completed --comment "Hotové 28. 10.: docs/nfl.md, docs/gate-nfl-G0.md" >/dev/null
    echo "✓ $1"
  fi
}

# Š12 – dáta, model, G0
add "NFL: plán a architektúra" "nfl,docs" "$M12" \
  'docs/nfl.md: prednosť pred tenisom, nflverse games.csv so zdrojom, zámok v GitHub Actions, vrstvy Elo / quarterback / odpočinok, G2 do konca základnej časti.' done
add "NFL: kritériá G0 vopred" "nfl,test" "$M12" \
  'docs/gate-nfl-G0.md stanovené 28. 10. pred prvým behom: test 2023 – 2025, lepšia baseline (vždy domáci, bilancia), ≥ 0,0005, úplnosť, únik, stávkové stĺpce, contract ESPN.' done
add "NFL: sonda z Macu (archív 538, ESPN NFL)" "nfl,infra" "$M12" \
  'uv run python scripts/probe_nfl.py: archív nfl_elo.csv, ESPN scoreboard (ID zápasov = games.csv), zranenia QB; skrátená odpoveď do tests/fixtures.' open
add "NFL: games.csv bez stávkových stĺpcov" "nfl,model" "$M12" \
  'nfl/games.py: zoznam povolených stĺpcov, pripnutý commit pre G0 (a6b91bf), počty zápasov po sezónach, test že žiadny stávkový stĺpec sa nenačíta. Zdroj: nflverse / Lee Sharpe.' open
add "NFL: Elo tímov (replikácia 538)" "nfl,model" "$M12" \
  'nfl/elo.py: výhoda domáceho, váha rozdielu skóre, návrat k priemeru medzi sezónami; porovnanie s archívom nfl_elo.csv (ak je dostupný).' open
add "Brána G0-NFL" "nfl,test" "$M12" \
  'Backtest podľa docs/gate-nfl-G0.md, cieľ do ~6. 11.' open
add "NFL: vrstva quarterback" "nfl,model" "$M12" \
  'Hodnota štartujúceho quarterbacka; pridá sa len pri zlepšení log loss aspoň o 0,0005 na testovacích sezónach.' open
add "NFL: vrstva odpočinok a cestovanie" "nfl,model" "$M12" \
  'Voľný týždeň, štvrtok po nedeli, časové pásma; len ak zlepší log loss aspoň o 0,0005.' open

# Š13 – naostro a appka
add "NFL: zamykanie tipov v GitHub Actions (nfl.yml)" "nfl,infra" "$M13" \
  'V hracie dni z cron-job.org, zamkne tipy dňa pred prvým výkopom (najskôr 15:30 nášho času), uloží štartujúcich quarterbackov; archive/nfl/predictions, reports/nfl_live.md.' open
add "Brána G2-NFL: do konca základnej časti 10. 1. 2027" "nfl,test" "$M13" \
  'Od prvého ostrého tipu do 10. 1. 2027 (~100 – 130 zápasov), hranica log loss stanovená pred prvým tipom (95. percentil okien backtestu).' open
add "NFL v appke (beta)" "nfl,app" "$M13" \
  'Po jadre (#55 – 58): prepínač športu, Zápasy po týždňoch, Tipy, Výsledky, Teamy, Model; quarterback pri zápase; bez lôg, farby a skratky tímov.' open

echo "Hotovo: https://github.com/users/$OWNER/projects/$SPORTY"
