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

log "Running sudo setup tasks for $TARGET_USER."

if [[ -x "$SCRIPT_DIR/setup-gcloud-sudo-all.sh" ]]; then
  log "Running gcloud sudo setup."
  "$SCRIPT_DIR/setup-gcloud-sudo-all.sh"
else
  log "gcloud sudo setup script missing; skipping."
fi

if [[ -x "$SCRIPT_DIR/setup-newsyslog-rotation.sh" ]]; then
  log "Installing log rotation config."
  "$SCRIPT_DIR/setup-newsyslog-rotation.sh"
else
  log "Log rotation setup script missing; skipping."
fi

log "Sudo setup tasks complete."
