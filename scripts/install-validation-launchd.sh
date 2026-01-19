#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_SUPPORT="$HOME/Library/Application Support/com.ray-manaloto.macos-dev-maintenance"
LOG_DIR="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
WRAPPER="$APP_SUPPORT/macos_dev_validation"
PLIST="$HOME/Library/LaunchAgents/com.ray-manaloto.macos-dev-validation.plist"

mkdir -p "$APP_SUPPORT" "$LOG_DIR"

cat <<SCRIPT > "$WRAPPER"
#!/usr/bin/env bash
set -euo pipefail

REPO="\${MDE_REPO:-$REPO_ROOT}"
SCRIPT="\${REPO}/scripts/post-setup-run.sh"

if [[ -x "\$SCRIPT" ]]; then
  exec "\$SCRIPT"
fi

echo "macos-dev-validation: missing repo script at \$SCRIPT" >&2
exit 1
SCRIPT

chmod 755 "$WRAPPER"

cat <<EOF2 > "$PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ray-manaloto.macos-dev-validation</string>
  <key>ProgramArguments</key>
  <array>
    <string>$WRAPPER</string>
  </array>
  <key>StartInterval</key>
  <integer>604800</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/macos-dev-validation.out</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/macos-dev-validation.out</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>MDE_REPO</key>
    <string>$REPO_ROOT</string>
  </dict>
  <key>LowPriorityBackgroundIO</key>
  <true/>
  <key>LowPriorityIO</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
EOF2

launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "Installed validation LaunchAgent: $PLIST"
