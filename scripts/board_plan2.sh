#!/usr/bin/env bash
# shellcheck disable=SC1111  # slovenské úvodzovky v textoch sú zámerné
# Boardy po novom poradí fáz (14. 10. 2026): každý šport má vlastné brány, NHL a F1 idú do appky
# ako beta, spoločné jadro až pri treťom športe. Plán: docs/sporty.md, brány: docs/gate-*.md.
# Spustenie (aj opakovane, nič sa nezdvojí):  bash scripts/board_plan2.sh
set -euo pipefail

OWNER="peterolah-qa"
REPO="$OWNER/team-pulse"

project_number () {  # $1 názov boardu → číslo alebo nič
  gh project list --owner "$OWNER" --limit 100 --format json --jq ".projects[] | select(.title==\"$1\") | .number"
}
NBA=$(project_number "Team Pulse")
SPORTY=$(project_number "Team Pulse – športy")
if [ -z "$NBA" ] || [ -z "$SPORTY" ]; then
  echo "Chýba board „Team Pulse“ alebo „Team Pulse – športy“ (najprv bash scripts/board_sporty.sh)"
  exit 1
fi

label () { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 || true; }
label bug d73a4a "Chyba"

# míľniky: premenovanie podľa nového poradia (opakované spustenie len obnoví popis)
milestone_number () {
  gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title==\"$1\") | .number"
}
rename_milestone () {  # $1 starý názov, $2 nový názov, $3 popis
  local n
  n=$(milestone_number "$1")
  [ -n "$n" ] || n=$(milestone_number "$2")
  if [ -z "$n" ]; then echo "Chýba míľnik „$1“"; exit 1; fi
  gh api -X PATCH "repos/$REPO/milestones/$n" -f title="$2" -f description="$3" >/dev/null
  echo "▸ $2"
}
M1="Š1 – NHL: dáta a backtest"
M2="Š2 – NHL v appke (beta)"
M3="Š3 – F1"
M5="Š5 – Spoločné jadro (pri treťom športe)"
rename_milestone "$M1" "$M1" "Sťahovač histórie, hokejové Elo, backtest, ostré tipy, ranná úloha. Hotovo, v main od 14. 10."
rename_milestone "Š3 – NHL v appke" "$M2" "Prepínač športu, zápasy, tipy, výsledky NHL s označením beta. 15. – 19. 10., G2-NHL 13. – 26. 10."
rename_milestone "Š5 – F1 (sezóna 2027)" "$M3" "Zdroj, model pretekov, backtest (G0-F1), tipy od Austinu 25. 10., appka (beta), G2-F1 do 6. 12."
rename_milestone "Š2 – Spoločné jadro (po G2)" "$M5" "core/ podľa toho, čo majú športy naozaj spoločné. Pri treťom športe, najskôr 4. 11."

ISSUES=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title,url,state \
  --jq '.[] | "\(.title)\t\(.url)\t\(.state)"')
url_of ()   { awk -F'\t' -v t="$1" '$1 == t { print $2; exit }' <<< "$ISSUES"; }
state_of () { awk -F'\t' -v t="$1" '$1 == t { print $3; exit }' <<< "$ISSUES"; }

close () {  # $1 názov, $2 url, $3 komentár – zavrie, len ak je otvorená
  [ "$(state_of "$1")" = "CLOSED" ] && return 0
  gh issue close "$2" --reason completed --comment "$3" >/dev/null
  echo "✓ $1"
}

add () {  # $1 board, $2 názov, $3 štítky, $4 míľnik ('' = žiadny), $5 popis, $6 done|open
  local url
  url=$(url_of "$2")
  if [ -z "$url" ]; then
    local args=(--repo "$REPO" --title "$2" --label "$3" --body "$5")
    if [ -n "$4" ]; then args+=(--milestone "$4"); fi
    url=$(gh issue create "${args[@]}")
    echo "+ $2"
  else
    echo "= $2"
  fi
  gh project item-add "$1" --owner "$OWNER" --url "$url" >/dev/null
  if [ "$6" = "done" ]; then close "$2" "$url" "Hotové."; fi
}

retitle () {  # $1 starý názov, $2 nový názov, $3 nový popis (už premenovaná sa preskočí)
  local url
  url=$(url_of "$1")
  if [ -z "$url" ]; then return 0; fi
  gh issue edit "$url" --title "$2" --body "$3" >/dev/null
  echo "✎ $2"
}

done_existing () {  # $1 názov existujúcej úlohy, $2 komentár
  local url
  url=$(url_of "$1")
  if [ -n "$url" ]; then close "$1" "$url" "$2"; fi
}

# --- NBA (board „Team Pulse“) ---
add "$NBA" "Predikcie: cron-job.org každých 30 min, archív pred Pages" "infra" "" \
  'Plánované behy GitHubu chodili 4 – 5× denne. cron-job.org volá workflow_dispatch (token len na team-pulse, platí do ~11. 1. 2027). Archív tipov sa commitne pred buildom a zverejnením, chyba Pages ho nezahodí.' "done"
add "$NBA" "Ranná úloha: stav len z main" "infra" "" \
  '14. 10. skončil stav vo vetve nhl, lebo priečinok na Macu bol na nej. Teraz úloha na inej vetve skončí chybou skôr, než niečo stiahne. Test v tests/test_daily.py.' "done"
add "$NBA" "Brána G2 NBA: kritériá vopred" "docs,test" "" \
  'docs/gate-G2.md: prevádzka bez výnimky (tipy zamknuté, výsledky, prepočet, stav do 12:00), log loss ≤ 0,6739 a nižší než baseline „vždy domáci“. Hranice z backtestu: scripts/g2_reference.py → reports/g2_reference.md.' "done"
add "$NBA" "NBA: zápasy na neutrálnej pôde chýbajú v histórii" "bug,model" "" \
  'V 2024/25 aj 2025/26 chýba 5 zápasov (Mexiko, Paríž, Berlín, Londýn, semifinále NBA Cupu), niektoré teamy majú 79 – 81 zápasov. Oprava a nové stiahnutie histórie pred 20. 10., najneskôr pred 7. 11. (DEN @ IND, Mexiko).' open
add "$NBA" "Brána G2 NBA: vyhodnotenie 3. 11." "test" "" \
  'Obdobie 20. 10. – 2. 11. (dni v USA). Kritériá a výsledok v docs/gate-G2.md.' open

# --- Š1 – NHL: dáta a backtest ---
add "$SPORTY" "NHL: ranná úloha (launchd 10:15)" "nhl,infra" "$M1" \
  'team_pulse.nhl.daily: len na main, počká na NBA úlohu, vyhodnotí noc, zamkne tipy na dnes a zajtra, commit. Pri chybe upozornenie v macOS.' "done"
add "$SPORTY" "NHL: zlúčené do main" "nhl" "$M1" \
  'Vetva nhl zlúčená do main (e5d91d1) a zrušená. Priečinok na Macu ostáva na main.' "done"

# --- Š2 – NHL v appke (beta) ---
done_existing "NHL: návrh vrstiev – brankár, únava" \
  'Únava (vrstva C) prijatá. Brankár (vrstva G) a Glicko-2 zamietnuté: docs/gate-nhl-G0.md, reports/nhl_goalies.md, reports/nhl_glicko.md.'
add "$SPORTY" "Brána G2-NHL: kritériá vopred" "nhl,docs,test" "$M2" \
  'docs/gate-nhl-G2.md: prevádzka bez výnimky, log loss ≤ 0,7101. Porazenie baseline nie je kritériom (v backteste ho model nesplnil v 24,5 % 14-dňových okien).' "done"
retitle "Brána G2-NHL: 14 dní ostrej prevádzky" "Brána G2-NHL: vyhodnotenie 27. 10." \
  'Obdobie 13. – 26. 10. (dni v USA), kritériá v docs/gate-nhl-G2.md. Prejde → NHL v appke bez označenia beta.'
add "$SPORTY" "NHL: dáta pre appku z rannej úlohy" "nhl,infra" "$M2" \
  'Ranná NHL úloha zapíše tipy a výsledky pre appku a commitne ich, push spustí build a zverejnenie. Bez zmeny predict.yml.' open
add "$SPORTY" "Appka: označenie beta pre šport pred jeho G2" "app" "$M2" \
  'Šport po G0 je v appke s označením beta a vysvetlením. Zmizne po prejdení jeho G2.' open

# --- Š3 – F1 ---
add "$SPORTY" "Brána G0-F1: kritériá vopred" "f1,docs,test" "$M3" \
  'Pred backtestom: sezóny a pravidlá 2026, baseline (poradie na štarte, poradie v šampionáte), metrika pre víťaza a pódium, hranica.' open
retitle "F1: ostrá prevádzka od prvých pretekov 2027" "Brána G2-F1: 6 pretekov 25. 10. – 6. 12." \
  'Austin, Mexiko, Brazília, Las Vegas, Katar, Abu Dhabi. Tipy zamknuté pred kvalifikáciou, vyhodnotenie po pretekoch.'
retitle "F1: obrazovky v appke" "F1: v appke (beta)" \
  'Preteky, jazdci, tímy, tip na víťaza a pódium. Bez lôg, len farby tímov. Beta do prejdenia G2-F1.'

echo "Hotovo: https://github.com/users/$OWNER/projects/$SPORTY a /projects/$NBA"
