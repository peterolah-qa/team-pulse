#!/usr/bin/env bash
# Nainštaluje dennú aktualizáciu (team_pulse.daily) ako úlohu macOS launchd.
# Beží každý deň o 10:00; ak Mac v tom čase spí, spustí sa hneď po prebudení.
#
#   bash scripts/install_daily.sh            nainštalovať / aktualizovať
#   bash scripts/install_daily.sh --remove   odinštalovať
#   tail -f ~/Library/Logs/team-pulse-daily.log   sledovať log
set -euo pipefail

LABEL="dev.qavant.teampulse.daily"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/team-pulse-daily.log"
DOMAIN="gui/$(id -u)"

if [[ "${1:-}" == "--remove" ]]; then
  launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Odinštalované."
  exit 0
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
UV="$(command -v uv)"
mkdir -p "$(dirname "$PLIST")" "$(dirname "$LOG")"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$UV</string><string>run</string><string>python</string><string>-m</string><string>team_pulse.daily</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
EOF

launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "Nainštalované: $LABEL (každý deň o 10:00)"
echo "Repo: $REPO"
echo "Log:  $LOG"
echo "Spustiť hneď na skúšku: launchctl kickstart $DOMAIN/$LABEL"
