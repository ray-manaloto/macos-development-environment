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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$(dscl . -read "/Users/$TARGET_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
if [[ -z "$HOME_DIR" ]]; then
  HOME_DIR="/Users/$TARGET_USER"
fi

GCS_SDK="/opt/google-cloud-sdk/bin/gcloud"

log "Installing/updating sudo helper (idempotent)."
"$SCRIPT_DIR/setup-gcloud-sudo-helper.sh"

if [[ -x /usr/local/sbin/mde-gcloud-migrate ]]; then
  log "Running gcloud migration helper."
  /usr/local/sbin/mde-gcloud-migrate || true
fi

if [[ -d "$HOME_DIR/.config/gcloud" ]]; then
  log "Fixing gcloud config ownership."
  chown -R "$TARGET_USER":staff "$HOME_DIR/.config/gcloud"
fi

if [[ -x "$GCS_SDK" ]]; then
  log "Updating gcloud managed Python (user context)."
  if sudo -u "$TARGET_USER" -H env HOME="$HOME_DIR" CLOUDSDK_CONFIG="$HOME_DIR/.config/gcloud" \
    "$GCS_SDK" components update-macos-python --quiet; then
    log "gcloud Python update complete."
  else
    log "gcloud Python update failed as user; retrying as root."
    "$GCS_SDK" components update-macos-python --quiet || true
    if [[ -d "$HOME_DIR/.config/gcloud" ]]; then
      chown -R "$TARGET_USER":staff "$HOME_DIR/.config/gcloud"
    fi
  fi
else
  log "gcloud not found at $GCS_SDK; skipping Python update."
fi

log "gcloud sudo setup complete."
