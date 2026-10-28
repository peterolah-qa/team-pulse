#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Tenis po sonde ESPN (28. 10. 2026): sonda a kritériá G0 hotové. Predpoklad: bash scripts/board_tennis.sh.
# Zdôvodnenie: docs/journal.md (28. 10.). Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_tennis2.sh
set -euo pipefail

REPO="peterolah-qa/team-pulse"

done_title () {  # $1 názov úlohy, $2 komentár
  local n
  n=$(gh issue list --repo "$REPO" --state all --limit 1000 --json number,title,state \
    --jq ".[] | select(.title==\"$1\") | \"\(.number) \(.state)\"")
  if [ -z "$n" ]; then echo "! chýba: $1"; return; fi
  if [ "${n#* }" = "CLOSED" ]; then echo "= #${n% *} (už zavreté)"; return; fi
  gh issue close "${n% *}" --repo "$REPO" --reason completed --comment "$2" >/dev/null
  echo "✓ #${n% *} $1"
}

done_title "Tenis: sonda ESPN (ATP, WTA)" \
  "Sonda 28. 10.: scoreboard vráti celé turnaje týždňa, naplánované zápasy majú hráčov aj čas, RET/W/O vlastný stav, medzera od júla sa dá doplniť. Zistenia v docs/tennis.md."
done_title "Tenis: kritériá G0-ATP a G0-WTA vopred" \
  "docs/gate-tennis-G0.md stanovené 28. 10. pred prvým behom modelu (test 2023 – 2025, lepšia baseline z rebríčka alebo bodov, ≥ 0,0005)."
