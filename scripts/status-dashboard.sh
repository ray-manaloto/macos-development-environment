#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
MAINT_LOG="$LOG_DIR/macos-dev-maintenance.out"
VALID_LOG="$LOG_DIR/macos-dev-validation.out"
SUMMARY_LOG="$LOG_DIR/post-setup-summary.log"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.bun/bin:$home/.pixi/bin:$home/.local/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

last_match() {
  local file="$1"
  local pattern="$2"

  if [[ ! -f "$file" ]]; then
    printf 'missing'
    return 0
  fi

  awk -v pat="$pattern" '$0 ~ pat {line=$0} END{if(line!="") print line}' "$file" 2>/dev/null || true
}

launchd_status() {
  local label="$1"
  local status

  status="$(launchctl list 2>/dev/null | awk -v label="$label" '$3==label {print $2}' || true)"
  if [[ -z "$status" ]]; then
    printf 'not loaded'
    return 0
  fi

  if [[ "$status" == "0" ]]; then
    printf 'loaded (last exit: 0)'
    return 0
  fi

  printf 'loaded (last exit: %s)' "$status"
}

log_size() {
  local file="$1"
  if [[ -f "$file" ]]; then
    stat -f '%z bytes' "$file" 2>/dev/null || echo "unknown"
  else
    echo "missing"
  fi
}

main() {
  setup_path

  log "Status dashboard"
  log "Maintenance job: $(launchd_status com.ray-manaloto.macos-dev-maintenance)"
  log "Validation job:  $(launchd_status com.ray-manaloto.macos-dev-validation)"

  log "Maintenance log: $MAINT_LOG ($(log_size "$MAINT_LOG"))"
  log "Validation log:  $VALID_LOG ($(log_size "$VALID_LOG"))"
  log "Summary log:     $SUMMARY_LOG ($(log_size "$SUMMARY_LOG"))"

  log "Last maintenance: $(last_match "$MAINT_LOG" "Homebrew update\\.")"
  log "Last validation:  $(last_match "$SUMMARY_LOG" "Post-setup summary")"

  if [[ -x /opt/google-cloud-sdk/bin/gcloud ]]; then
    log "gcloud: /opt/google-cloud-sdk/bin/gcloud"
  elif command -v gcloud >/dev/null 2>&1; then
    log "gcloud: $(command -v gcloud)"
  else
    log "gcloud: not installed"
  fi

  if command -v mise >/dev/null 2>&1; then
    log "mise: $(command -v mise)"
  fi
  if command -v uv >/dev/null 2>&1; then
    log "uv:   $(command -v uv)"
  fi
  if command -v pixi >/dev/null 2>&1; then
    log "pixi: $(command -v pixi)"
  fi
  if command -v bun >/dev/null 2>&1; then
    log "bun:  $(command -v bun)"
  fi
}

main "$@"
