#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

run_status=0

setup_path

log "Verify all starting."

if [[ -x "$SCRIPT_DIR/health-check.sh" ]]; then
  log "Running health check."
  if ! "$SCRIPT_DIR/health-check.sh"; then
    run_status=1
  fi
else
  log "Health check script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-tmux-setup.sh" ]]; then
  log "Running tmux verification."
  if ! "$SCRIPT_DIR/verify-tmux-setup.sh"; then
    run_status=1
  fi
else
  log "Tmux verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/status-dashboard.sh" ]]; then
  log "Status dashboard JSON:"
  if ! "$SCRIPT_DIR/status-dashboard.sh" --json; then
    run_status=1
  fi
else
  log "Status dashboard script missing."
  run_status=1
fi

if [[ "$run_status" -eq 0 ]]; then
  log "Verify all: PASS."
  exit 0
fi

log "Verify all: FAIL."
exit 1
