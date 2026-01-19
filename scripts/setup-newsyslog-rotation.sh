#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with sudo: sudo $0" >&2
  exit 1
fi

TARGET_USER="${SUDO_USER:-${MDE_TARGET_USER:-}}"
if [[ -z "$TARGET_USER" ]]; then
  echo "SUDO_USER not set. Re-run with sudo or set MDE_TARGET_USER." >&2
  exit 1
fi

HOME_DIR="$(dscl . -read "/Users/$TARGET_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
if [[ -z "$HOME_DIR" ]]; then
  HOME_DIR="/Users/$TARGET_USER"
fi

LOG_DIR="$HOME_DIR/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
CONF_PATH="/etc/newsyslog.d/com.ray-manaloto.macos-dev-maintenance.conf"

install -d -o "$TARGET_USER" -g staff "$LOG_DIR"

cat <<EOF2 > "$CONF_PATH"
# Managed by macos-development-environment.
$LOG_DIR/macos-dev-maintenance.out $TARGET_USER:staff 640 7 10240 * N
$LOG_DIR/macos-dev-validation.out $TARGET_USER:staff 640 7 10240 * N
$LOG_DIR/post-setup-run.log $TARGET_USER:staff 640 7 10240 * N
$LOG_DIR/post-setup-summary.log $TARGET_USER:staff 640 7 10240 * N
EOF2

chmod 644 "$CONF_PATH"

log "Installed newsyslog rotation config: $CONF_PATH"
log "Rotation size: 10MB, count: 7"
