#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Bejzbal (MLB + LVBP) a tenis na boarde „Team Pulse – športy“ (28. 10. 2026): míľniky Š6 – Š10 a úlohy
# podľa docs/baseball.md. Zdôvodnenie: docs/journal.md (28. 10.).
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_baseball.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

SPORTY=$(gh project list --owner "$OWNER" --limit 100 --format json \
  --jq '.projects[] | select(.title=="Team Pulse – športy") | .number')
if [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse – športy“"
  exit 1
fi

label () { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 || true; }
label bejzbal b45309 "Bejzbal (MLB, LVBP)"
label tenis   65a30d "Tenis"

M6="Š6 – Bejzbal: zdroje"
M7="Š7 – Bejzbal: model a G0"
M8="Š8 – LVBP naostro mimo appky"
M9="Š9 – Bejzbal v appke (beta)"
M10="Š10 – Tenis"
MILESTONES=$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
milestone () {
  grep -Fxq -- "$1" <<< "$MILESTONES" || gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
}
milestone "$M6"  "Sonda z Macu: MLB Stats API (MLB, zimné ligy), Retrosheet, archív 538, zdroj LVBP a podmienky. 28. 10. – 1. 11."
milestone "$M7"  "História, Elo, nadhadzovač, cestovanie a odpočinok; G0-LVBP do ~15. 11., G0-MLB do ~20. 12."
milestone "$M8"  "Ranná úloha na Macu 10:30, ostré tipy LVBP mimo appky ~16. 11. – 27. 12., G2-LVBP."
milestone "$M9"  "Po jadre: appka (beta), MLB naostro od 25. 3. 2027, G2-MLB 25. 3. – 7. 4. 2027."
milestone "$M10" "Návrh architektúry, zdroje, model a brány – po bejzbale."

EXISTING=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url --jq '.[] | "\(.title)\t\(.url)"')

add () {  # $1 názov, $2 štítky, $3 míľnik, $4 popis, $5 done|open
  local url
  url=$(awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$EXISTING")
  if [ -n "$url" ]; then
    gh project item-add "$SPORTY" --owner "$OWNER" --url "$url" >/dev/null
    echo "= $1 (už je na boarde)"
    return
  fi
  url=$(gh issue create --repo "$REPO" --title "$1" --label "$2" --milestone "$3" --body "$4")
  gh project item-add "$SPORTY" --owner "$OWNER" --url "$url" >/dev/null
  if [ "$5" = "done" ]; then
    gh issue close "$url" --reason completed --comment "Hotové: docs/baseball.md" >/dev/null
    echo "✓ $1"
  else
    echo "○ $1"
  fi
}

# Š6 – zdroje
add "Bejzbal: plán a architektúra (MLB + LVBP)" "bejzbal,docs" "$M6" \
  'docs/baseball.md: obe ligy naraz, šport = model / liga = zdroj, zamykanie rannou úlohou na Macu, vrstvy modelu, špecifiká (nadhadzovač, odložené zápasy, dvojzápasy), zdroje, brány, plán.' done
add "Bejzbal: sonda zdrojov z Macu" "bejzbal,infra" "$M6" \
  'uv run python scripts/probe_baseball.py: MLB Stats API (copyright, deň MLB s nadhadzovačmi, zimné ligy a LVBP po sezónach), Retrosheet, archív 538 mlb_elo.csv, robots.txt stránok LVBP. Výstup do chatu.' open
add "MLB Stats API: podmienky MLBAM a rozsah použitia" "bejzbal,infra" "$M6" \
  'Overiť znenie podmienok (individual, non-commercial, non-bulk). Použitie len na denný rozpis, výsledky a nadhadzovačov, žiadne hromadné sťahovanie histórie.' open
add "LVBP: zdroj histórie a podmienky" "bejzbal,infra" "$M6" \
  'Povolený zdroj zápasov a nadhadzovačov LVBP (MLB Stats API zimné ligy alebo iný). Stránka, ktorá zakazuje roboty alebo AI, sa nepoužije. Bez zdroja sa LVBP nerobí, ostáva MLB.' open
add "Retrosheet: povinná veta o zdroji (README, appka)" "bejzbal,docs" "$M6" \
  'Text z retrosheet.org/notice.txt pri každom zverejnení dát alebo výsledkov z nich odvodených.' open

# Š7 – model a G0
add "Bejzbal: kritériá G0-MLB a G0-LVBP vopred" "bejzbal,test" "$M7" \
  'docs/gate-mlb-G0.md a docs/gate-lvbp-G0.md pred prvým behom backtestu: testovacie sezóny, baseline „vždy domáci“, prínos vrstvy ≥ 0,0005, kalibrácia, replikácia 538 (MLB).' open
add "MLB: história z Retrosheetu" "bejzbal,model" "$M7" \
  'Game logy → data/raw/baseball/mlb (necommituje sa): skóre, extra smeny, štartujúci nadhadzovači, číslo zápasu dňa, neutrálne ihriská. Testy na malých ukážkach.' open
add "LVBP: história zápasov" "bejzbal,model" "$M7" \
  'Z overeného zdroja: zápasy základnej časti po sezónach, skóre, nadhadzovači, ak sú. Rovnaký tvar zápasu ako MLB (baseball/games.py).' open
add "Bejzbal: Elo teamov (replikácia 538 na MLB)" "bejzbal,model" "$M7" \
  'baseball/elo.py: MLB porovnanie s 538 mlb_elo.csv (ak je archívna kópia), LVBP vlastné parametre (K, výhoda domáceho) z tréningových sezón.' open
add "Bejzbal: vrstva štartujúci nadhadzovač" "bejzbal,model" "$M7" \
  'Kĺzavé hodnotenie posledných štartov oproti priemeru tímu; pridá sa len pri zlepšení log loss aspoň o 0,0005 na testovacích sezónach.' open
add "Bejzbal: vrstvy cestovanie, odpočinok, dvojzápasy" "bejzbal,model" "$M7" \
  'Každá vrstva zvlášť, len ak zlepší log loss aspoň o 0,0005.' open
add "Brána G0-LVBP" "bejzbal,test" "$M7" \
  'Backtest LVBP podľa docs/gate-lvbp-G0.md, cieľ do ~15. 11., aby ostré tipy stihli základnú časť do 27. 12.' open
add "Brána G0-MLB" "bejzbal,test" "$M7" \
  'Backtest MLB podľa docs/gate-mlb-G0.md, testovacie sezóny 2023 – 2025, cieľ do ~20. 12.' open

# Š8 – LVBP naostro
add "Bejzbal: ranná úloha na Macu 10:30" "bejzbal,infra" "$M8" \
  'Zamknutie tipov (archive/baseball/<liga>/predictions), uložený ohlásený nadhadzovač, vyhodnotenie, reports/<liga>_live.md. Len na main, launchd ako NBA a NHL.' open
add "Brána G2-LVBP: ostré tipy do 27. 12." "bejzbal,test" "$M8" \
  'Od spustenia rannej úlohy do konca základnej časti, hranica log loss z backtestu vopred, vyhodnotenie po 27. 12.' open

# Š9 – appka
add "Bejzbal v appke (beta)" "bejzbal,app" "$M9" \
  'Po jadre (#55 – 58): prepínač NBA · NHL · MLB, Zápasy, Tipy, Výsledky, Teamy, Model; karta s ohlásenými nadhadzovačmi, detail s overeným rozpadom tipu. Žiadne logá.' open
add "Brána G2-MLB: 25. 3. – 7. 4. 2027" "bejzbal,test" "$M9" \
  'Prvých 14 dní sezóny MLB 2027, vyhodnotenie 8. 4. Pri lockoute sa posunie so začiatkom sezóny.' open

# Š10 – tenis
add "Tenis: návrh architektúry" "tenis,docs" "$M10" \
  'Petrov nápad 28. 10.: ďalší šport po bejzbale. Okruhy, zdroje a podmienky, model hráčov, brány.' open

echo "Hotovo: https://github.com/users/$OWNER/projects/$SPORTY"
