#!/usr/bin/env bash
# Team Pulse – issues fázy 2 (PWA appka) na board. Hotové sa hneď zatvoria → board ich presunie do Done.
# Spusti až PO pushnutí kódu fázy 2:  bash scripts/board_faza2.sh
set -euo pipefail

OWNER="peterolah-qa"
FULL="$OWNER/team-pulse"
M="2 – PWA appka (G3)"
NUM=$(gh project list --owner "$OWNER" --format json --jq '.projects[] | select(.title=="Team Pulse") | .number')

add () {  # $1 title, $2 labels, $3 body, $4 done|open
  URL=$(gh issue create --repo "$FULL" --title "$1" --label "$2" --milestone "$M" --body "$3")
  gh project item-add "$NUM" --owner "$OWNER" --url "$URL" >/dev/null
  if [ "$4" = "done" ]; then
    gh issue close "$URL" --reason completed --comment "Hotové v commite fázy 2." >/dev/null
    echo "✓ $1"
  else
    echo "○ $1 (otvorené)"
  fi
}

add "Kostra appky: Vite + TypeScript, router, cyberpunk téma" "app"       "Jedna téma (štýl C), mobile-first, fonty Chakra Petch + Rajdhani, spodná lišta." done
add "PWA: manifest, ikony, service worker"                    "app"       "Stránka a dáta: najprv sieť, pri výpadku posledná verzia. Assets z cache." done
add "Dáta pre appku: predictions/teams/model JSON"            "app,model" "predict.py → app/public/data. Vrstvy, dôvody, čo keby, trend, súpiska, kalibrácia." done
add "Obrazovky Dnes, Zápas, Team, Teamy"                      "app"       "Pulse, úroveň, istota, šanca, vrstvy modelu, trend 10 zápasov, súpiska so zraneniami." done
add "Obrazovka Čo keby"                                       "app"       "Prepínač HRÁ / NEHRÁ, varovanie pri hraničnom prípade." done
add "Obrazovka Model"                                         "app,model" "Presnosť, log loss, kalibračný graf, porovnanie vrstiev, naučené váhy." done
add "Playwright E2E: mobil + desktop"                         "test,app"  "Navigácia, čo keby, prázdne a chybové stavy, žiadne kurzy, bez posúvania do strán na 360 px." done
add "Vizuálna regresia: 6 obrazoviek × 2 zariadenia"           "test,app"  "toHaveScreenshot, screenshoty z Linuxu, v CI s VISUAL=1." done
add "Prístupnosť: axe WCAG 2.1 AA + Lighthouse"               "test,app"  "0 porušení axe. Lighthouse mobil 100/100/100/100." done
add "CI appky + deploy appky na Pages"                        "infra"     "app.yml: build + Playwright. predict.yml: predikcie → build → Pages." done
add "Brána G3: README pre portfólio"                          "docs"      "Screenshoty, architektúra, model, testovanie. docs/gate-G3.md." done
add "Ručná kontrola PWA na iPhone"                            "test,app"  "Safari → Zdieľať → Pridať na plochu. Otvoriť bez siete: majú sa ukázať posledné dáta. (G3 bod 8)" open

echo "Hotovo: https://github.com/users/$OWNER/projects/$NUM"
