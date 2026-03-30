#!/usr/bin/env bash
set -euo pipefail

APP_NAME="com.sideswipe.agent"
PLIST_PATH="$HOME/Library/LaunchAgents/$APP_NAME.plist"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  rm -f "$PLIST_PATH"
  echo "Removed LaunchAgent: $PLIST_PATH"
else
  echo "No LaunchAgent found at: $PLIST_PATH"
fi

echo "If it's still running, you can reboot, or try: launchctl remove $APP_NAME (may fail on newer macOS)."