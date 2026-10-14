#!/usr/bin/env bash
# Nainštaluje rannú NHL úlohu (team_pulse.nhl.daily) ako úlohu macOS launchd.
# Beží každý deň o 10:15 (po NBA úlohe o 10:00, na ktorú počká); ak Mac spí, spustí sa po prebudení.
#
#   bash scripts/install_nhl_daily.sh            nainštalovať / aktualizovať
#   bash scripts/install_nhl_daily.sh --remove   odinštalovať
#   tail -f ~/Library/Logs/team-pulse-nhl.log    sledovať log
set -euo pipefail

LABEL="dev.qavant.teampulse.nhl"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/team-pulse-nhl.log"
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
    <string>$UV</string><string>run</string><string>python</string><string>-m</string><string>team_pulse.nhl.daily</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>15</integer></dict>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
EOF

launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "Nainštalované: $LABEL (každý deň o 10:15)"
echo "Repo: $REPO"
echo "Log:  $LOG"
echo "Spustiť hneď na skúšku: launchctl kickstart $DOMAIN/$LABEL"
