#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUX_CONF="$HOME/.tmux.conf"
STATUS_SCRIPT="$SCRIPT_DIR/status-dashboard.sh"
PLUGINS_DIR="$HOME/.tmux/plugins"
TPM_DIR="$PLUGINS_DIR/tpm"
REQUIRED_PLUGINS=("tmux-sensible" "tmux-resurrect" "tmux-continuum")

failures=0
warnings=0

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

warn() {
  warnings=$((warnings + 1))
  log "WARN: $*"
}

fail() {
  failures=$((failures + 1))
  log "FAIL: $*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

file_has() {
  local pattern="$1"
  local file="$2"

  if have_cmd rg; then
    rg -Fq "$pattern" "$file"
  else
    grep -Fq "$pattern" "$file"
  fi
}

check_cmd() {
  local name="$1"
  if have_cmd "$name"; then
    log "ok: $name"
  else
    fail "missing command: $name"
  fi
}

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    log "ok: $path"
  else
    fail "missing file: $path"
  fi
}

check_dir() {
  local path="$1"
  if [[ -d "$path" ]]; then
    log "ok: $path"
  else
    fail "missing directory: $path"
  fi
}

check_tmux_config() {
  if [[ ! -f "$TMUX_CONF" ]]; then
    return 1
  fi

  if ! file_has "Managed by macos-development-environment" "$TMUX_CONF"; then
    warn "tmux config not managed"
  fi

  if ! file_has "status-dashboard.sh --tmux" "$TMUX_CONF"; then
    fail "tmux config missing dashboard status-right"
  fi

  for plugin in "${REQUIRED_PLUGINS[@]}"; do
    if ! file_has "tmux-plugins/${plugin}" "$TMUX_CONF"; then
      fail "tmux config missing plugin: ${plugin}"
    fi
  done
}

check_tmux_runtime() {
  local session="mde-verify-$$"
  local created_session=0
  local status_line=""
  local status_right=""

  if ! tmux list-sessions >/dev/null 2>&1; then
    tmux new-session -d -s "$session"
    created_session=1
  fi

  if ! tmux source-file "$TMUX_CONF" >/dev/null 2>&1; then
    fail "tmux failed to source config"
  fi

  status_line="$(tmux show -g status 2>/dev/null || true)"
  if [[ -z "$status_line" ]]; then
    fail "tmux status check failed"
  elif [[ "$status_line" != "status on" ]]; then
    fail "tmux status bar is off"
  fi

  status_right="$(tmux show -g status-right 2>/dev/null || true)"
  if [[ -z "$status_right" ]]; then
    fail "tmux status-right check failed"
  elif [[ "$status_right" != *"status-dashboard.sh --tmux"* ]]; then
    fail "tmux status-right missing dashboard"
  fi

  if [[ -x "$STATUS_SCRIPT" ]]; then
    if ! "$STATUS_SCRIPT" --tmux >/dev/null 2>&1; then
      fail "status-dashboard --tmux failed"
    else
      log "ok: status-dashboard --tmux"
    fi
  else
    fail "status-dashboard script missing or not executable"
  fi

  if [[ "$created_session" -eq 1 ]]; then
    tmux kill-session -t "$session" >/dev/null 2>&1 || true
  fi
}


main() {
  setup_path
  log "Starting tmux verification."

  check_cmd tmux
  check_file "$TMUX_CONF"
  check_dir "$TPM_DIR"
  for plugin in "${REQUIRED_PLUGINS[@]}"; do
    check_dir "$PLUGINS_DIR/$plugin"
  done

  check_tmux_config

  if (( failures == 0 )); then
    check_tmux_runtime
  fi

  if (( failures != 0 )); then
    log "Tmux verification FAILED (${failures} failures, ${warnings} warnings)."
    return 1
  fi

  log "Tmux verification PASSED (${warnings} warnings)."
}

main "$@"
