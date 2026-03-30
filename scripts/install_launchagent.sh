#!/usr/bin/env bash
set -euo pipefail

APP_NAME="com.sideswipe.agent"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="$HOME/Applications/Sideswipe"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/$APP_NAME.plist"
LOG_DIR="$HOME/Library/Logs/sideswipe"

mkdir -p "$PLIST_DIR"
mkdir -p "$LOG_DIR"

# Install a copy outside of protected folders (Documents can be blocked for background agents).
mkdir -p "$HOME/Applications"
rsync -a --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$ROOT_DIR/" "$INSTALL_DIR/"

# Copy virtualenv too (needed for mediapipe/opencv deps), but avoid huge caches.
if [[ -d "$ROOT_DIR/.venv" ]]; then
  rsync -a --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'pip-wheel-metadata' \
    --exclude 'share' \
    "$ROOT_DIR/.venv/" "$INSTALL_DIR/.venv/"
fi

# Prefer the installed virtualenv python to ensure dependencies are available.
PY_BIN="$INSTALL_DIR/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  # Fallback to repo venv python if present
  PY_BIN="$ROOT_DIR/.venv/bin/python"
fi
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="$(command -v python3 || true)"
fi
if [[ -z "${PY_BIN:-}" ]] || [[ ! -x "$PY_BIN" ]]; then
  echo "python not found. Create .venv or install Python 3 and try again." >&2
  exit 1
fi

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${APP_NAME}</string>

  <key>ProgramArguments</key>
  <array>
    <string>${PY_BIN}</string>
  <string>${INSTALL_DIR}/src/agent.py</string>
    <string>--headless</string>
    <string>--quiet</string>
  </array>

  <key>WorkingDirectory</key>
  <string>${INSTALL_DIR}</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>${LOG_DIR}/agent.out.log</string>

  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/agent.err.log</string>
</dict>
</plist>
PLIST


# Modern macOS prefers bootstrap/bootout under the GUI domain.
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/$APP_NAME" >/dev/null 2>&1 || true
launchctl kickstart -k "gui/$(id -u)/$APP_NAME" >/dev/null 2>&1 || true

echo "Installed LaunchAgent: $PLIST_PATH"
echo "Logs: $LOG_DIR"
echo "To uninstall: ./scripts/uninstall_launchagent.sh"