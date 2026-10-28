#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# NFL po G0 (28. 10. 2026). Predpoklad: bash scripts/board_nfl.sh. Zdôvodnenie: docs/journal.md (28. 10.).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_nfl2.sh
set -euo pipefail

REPO="peterolah-qa/team-pulse"

num () { gh issue list --repo "$REPO" --state all --limit 1000 --json number,title,state \
  --jq ".[] | select(.title==\"$1\") | \"\(.number) \(.state)\""; }
done_title () {  # $1 názov úlohy, $2 komentár
  local n
  n=$(num "$1")
  if [ -z "$n" ]; then echo "! chýba: $1"; return; fi
  if [ "${n#* }" = "CLOSED" ]; then echo "= #${n% *} (už zavreté)"; return; fi
  gh issue close "${n% *}" --repo "$REPO" --reason completed --comment "$2" >/dev/null
  echo "✓ #${n% *} $1"
}

done_title "NFL: sonda z Macu (archív 538, ESPN NFL)" \
  "Sonda 28. 10.: archív nfl_elo.csv (archive.org 6. 3. 2025), ESPN scoreboard týždeň 8 (ID = games.csv), zranenia 62 QB; ukážka v tests/fixtures/nfl_espn_scoreboard.json."
done_title "NFL: games.csv bez stávkových stĺpcov" \
  "src/team_pulse/nfl/games.py: len povolené stĺpce, pripnutý commit a6b91bf, počty po sezónach sedia; test v tests/test_nfl.py."
done_title "Brána G0-NFL" \
  "Splnená 28. 10.: Elo 0,6341 vs. lepšia baseline 0,6611 (rozdiel 0,0270), 63,9 % na 854 zápasoch 2023 – 2025. docs/gate-nfl-G0.md, reports/nfl_backtest.md."

n=$(num "NFL: Elo tímov (replikácia 538)")
if [ -n "$n" ] && [ "${n#* }" != "CLOSED" ]; then
  gh issue comment "${n% *}" --repo "$REPO" \
    --body "28. 10.: Elo hotové (src/team_pulse/nfl/elo.py), G0 splnená. Zostáva porovnanie s archívom 538 nfl_elo.csv na Macu (informatívne)." >/dev/null
  echo "~ #${n% *} komentár"
fi

# Ostré tipy od týždňa 8 (Petrovo rozhodnutie 28. 10. večer)
done_title "NFL: zamykanie tipov v GitHub Actions (nfl.yml)" \
  "Hotové 28. 10.: team_pulse.nfl.predict + .github/workflows/nfl.yml (3× denne a ručne), tipy od týždňa 8, reports/nfl_live.md."
n=$(num "Brána G2-NFL: do konca základnej časti 10. 1. 2027")
if [ -n "$n" ] && [ "${n#* }" != "CLOSED" ]; then
  gh issue edit "${n% *}" --repo "$REPO" \
    --body 'docs/gate-nfl-G2.md (stanovené 28. 10. pred prvým tipom): týždne 8 – 18, výkop 29. 10. 2026 – 10. 1. 2027, model nfl-elo-v1 (čisté Elo), log loss ≤ 0,6620; každý zápas zamknutý pred výkopom a vyhodnotený, nezávislý prepočet = report.' >/dev/null
  echo "~ #${n% *} kritériá G2"
fi
if [ -z "$(num "NFL: druhý model Elo + quarterback od týždňa 10")" ]; then
  url=$(gh issue create --repo "$REPO" --title "NFL: druhý model Elo + quarterback od týždňa 10" --label "nfl,model" \
    --milestone "Š13 – NFL naostro (G2) a v appke" \
    --body 'Ak Peter schváli vrstvu quarterback (do 11. 11.): ku každému zápasu od týždňa 10 druhý zamknutý tip s vlastnou bránou. G2-NFL (čisté Elo) sa nemení.')
  gh project item-add "$(gh project list --owner peterolah-qa --limit 100 --format json --jq '.projects[] | select(.title=="Team Pulse – športy") | .number')" \
    --owner peterolah-qa --url "$url" >/dev/null
  echo "+ NFL: druhý model Elo + quarterback od týždňa 10"
fi
