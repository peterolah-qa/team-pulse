#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Tenis (ATP + WTA) na boarde „Team Pulse – športy“ (28. 10. 2026): míľniky Š10 a Š11 a úlohy podľa
# docs/tennis.md. Predpoklad: bash scripts/board_baseball.sh (štítok tenis, míľnik Š10).
# Zdôvodnenie: docs/journal.md (28. 10.). Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_tennis.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

SPORTY=$(gh project list --owner "$OWNER" --limit 100 --format json \
  --jq '.projects[] | select(.title=="Team Pulse – športy") | .number')
if [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse – športy“"
  exit 1
fi

gh label create tenis --repo "$REPO" --color 65a30d --description "Tenis" >/dev/null 2>&1 || true

M10="Š10 – Tenis"
M11="Š11 – Tenis v appke a G2"
milestone_no () { gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title==\"$1\") | .number"; }
N10=$(milestone_no "$M10")
if [ -z "$N10" ]; then
  gh api "repos/$REPO/milestones" -f title="$M10" >/dev/null
  N10=$(milestone_no "$M10")
fi
gh api -X PATCH "repos/$REPO/milestones/$N10" \
  -f description="ATP + WTA: zdroje (archív Sackmann, ESPN), história, doplnenie medzery jún – nov 2026, Elo + povrch, G0-ATP a G0-WTA do polovice decembra." >/dev/null
[ -n "$(milestone_no "$M11")" ] || gh api "repos/$REPO/milestones" -f title="$M11" \
  -f description="Zamykanie v GitHub Actions každých 30 min, appka (beta) od United Cupu 1. 1. 2027, G2 na Australian Open 17. – 31. 1. 2027." >/dev/null

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
    gh issue close "$url" --reason completed --comment "Hotové 28. 10.: docs/tennis.md" >/dev/null
    echo "✓ $1"
  fi
}

# Š10 – zdroje, história, model, G0
add "Tenis: návrh architektúry" "tenis,docs" "$M10" \
  'docs/tennis.md: ATP + WTA, dvojhra, hlavné súťaže; šport = model / okruh = liga; zamykanie v GitHub Actions každých 30 min; vrstvy, špecifiká, zdroje, brány, plán.' done
add "Tenis: archívna kópia dát Sackmanna" "tenis,infra" "$M10" \
  'Pôvodné repozitáre JeffSackmann/tennis_atp a tennis_wta vracajú 404. Kópia Aneeshers/tennis-sackmann-archive overená 28. 10. (commit 83733587, zápasy do 25. 5. 2026, CC BY-NC-SA 4.0); overené v docs/tennis.md.' done
add "Tenis: sonda ESPN (ATP, WTA)" "tenis,infra" "$M10" \
  'uv run python scripts/probe_tennis.py z Macu: tvar scoreboardu, budúce zápasy s oboma hráčmi a časom, deň z medzery (júl 2026) na doplnenie výsledkov.' open
add "Tenis: uvedenie zdroja a licencia (CC BY-NC-SA 4.0)" "tenis,docs" "$M10" \
  'README a appka: Jeff Sackmann / Tennis Abstract, odkaz na pôvodné repozitáre a na archívnu kópiu, licencia CC BY-NC-SA 4.0, informácia o zmenách (výber súťaží, doplnenie z ESPN).' open
add "Tenis: kritériá G0-ATP a G0-WTA vopred" "tenis,test" "$M10" \
  'docs/gate-tennis-G0.md pred prvým behom backtestu: testovacie sezóny 2023 – 2025, baseline z rebríčka, prínos vrstvy ≥ 0,0005, kalibrácia.' open
add "Tenis: história z archívu (ATP, WTA)" "tenis,model" "$M10" \
  'Pripnutý commit kópie → data/raw/tennis (necommituje sa); len hlavné súťaže (ATP G/M/A/F/O, WTA G/PM/P/I/F/O), zjednotený povrch, RET a W/O označené. Testy na malých ukážkach.' open
add "Tenis: doplnenie medzery jún – november 2026 z ESPN" "tenis,model" "$M10" \
  'Výsledky dvojhry ATP a WTA od konca archívu po koniec sezóny 2026, kontrola počtu zápasov po turnajoch, rovnaký tvar ako história.' open
add "Tenis: jednotné ID hráčov (Sackmann ↔ ESPN)" "tenis,model" "$M10" \
  'Párovanie podľa mena a krajiny, ručné výnimky v súbore, test: každý hráč z medzery a zo živých dát má ID.' open
add "Tenis: Elo hráčov (celkové + povrch)" "tenis,model" "$M10" \
  'K klesá s počtom zápasov; zmes celkového Ela a Ela na povrchu, váha z tréningových sezón; ATP a WTA zvlášť.' open
add "Tenis: vrstvy 3 / 5 setov a únava" "tenis,model" "$M10" \
  'Každá vrstva zvlášť, len ak zlepší log loss aspoň o 0,0005 na testovacích sezónach.' open
add "Brána G0-ATP" "tenis,test" "$M10" 'Backtest ATP podľa docs/gate-tennis-G0.md, cieľ do polovice decembra.' open
add "Brána G0-WTA" "tenis,test" "$M10" 'Backtest WTA podľa docs/gate-tennis-G0.md, cieľ do polovice decembra.' open

# Š11 – naostro a appka
add "Tenis: zamykanie tipov v GitHub Actions každých 30 min" "tenis,infra" "$M11" \
  'tennis.yml z cron-job.org + záložný plán GitHubu: tip sa zamkne, keď sú známi obaja hráči, vždy pred začiatkom; archive/tennis/<okruh>/predictions; v decembri overiť prehratím archívnych dní.' open
add "Tenis v appke (beta)" "tenis,app" "$M11" \
  'Po jadre (#55 – 58): prepínač športu, Zápasy podľa turnaja a dňa, Tipy, Výsledky, Hráči, Model; bez lôg, krajina ako kód.' open
add "Brána G2-tenis: Australian Open 17. – 31. 1. 2027" "tenis,test" "$M11" \
  'Dvojhra mužov aj žien (~250 zápasov), hranice stanovené vopred, vyhodnotenie po finále.' open

echo "Hotovo: https://github.com/users/$OWNER/projects/$SPORTY"
