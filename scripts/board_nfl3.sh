#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# NFL: vrstva quarterback schválená, druhý model od týždňa 10 (28. 10. 2026). Predpoklad: bash scripts/board_nfl2.sh.
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_nfl3.sh
set -euo pipefail

REPO="peterolah-qa/team-pulse"
num () { gh issue list --repo "$REPO" --state all --limit 1000 --json number,title,state \
  --jq ".[] | select(.title==\"$1\") | \"\(.number) \(.state)\""; }

n=$(num "NFL: vrstva quarterback")
if [ -n "$n" ] && [ "${n#* }" != "CLOSED" ]; then
  gh issue close "${n% *}" --repo "$REPO" --reason completed \
    --comment "Schválená 28. 10. (len náhradník): −65 Elo, test log loss 0,63412 → 0,63050, presnosť 64,4 %. Nováčik zamietnutý. reports/nfl_qb.md" >/dev/null
  echo "✓ #${n% *} NFL: vrstva quarterback"
fi
n=$(num "NFL: druhý model Elo + quarterback od týždňa 10")
if [ -n "$n" ] && [ "${n#* }" != "CLOSED" ]; then
  gh issue comment "${n% *}" --repo "$REPO" \
    --body "28. 10.: implementované (nfl-elo-qb-v1 v team_pulse.nfl.predict), prvé tipy týždeň 10 (12. 11.), brána docs/gate-nfl-qb-G2.md (log loss ≤ 0,6602). Zavrieť po prvých zamknutých tipoch." >/dev/null
  echo "~ #${n% *} komentár"
fi
