#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"

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
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.bun/bin:$home/.pixi/bin:$home/.local/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

check_cmd() {
  local name="$1"
  local required="$2"

  if have_cmd "$name"; then
    log "ok: $name"
    return 0
  fi

  if [[ "$required" == "1" ]]; then
    fail "missing command: $name"
  else
    warn "missing command: $name"
  fi
}

check_file() {
  local path="$1"
  local required="$2"

  if [[ -f "$path" ]]; then
    log "ok: $path"
    return 0
  fi

  if [[ "$required" == "1" ]]; then
    fail "missing file: $path"
  else
    warn "missing file: $path"
  fi
}

check_secret() {
  local label="$1"

  if ! have_cmd security; then
    warn "security command missing; cannot check $label"
    return 0
  fi

  if security find-generic-password -s "$label" -w >/dev/null 2>&1; then
    log "ok: keychain $label"
  else
    warn "missing keychain item: $label"
  fi
}

check_launchd_job() {
  local label="$1"
  local name="$2"
  local status

  status="$(launchctl list 2>/dev/null | awk -v label="$label" '$3 == label {print $2}' || true)"
  if [[ -z "$status" ]]; then
    fail "$name job not loaded"
    return 1
  fi

  log "ok: $name job loaded"
  if [[ "$status" != "0" ]]; then
    warn "$name job last exit status: $status"
  fi
}

check_launchd() {
  check_launchd_job "com.ray-manaloto.macos-dev-maintenance" "launchd maintenance"
  check_launchd_job "com.ray-manaloto.macos-dev-validation" "launchd validation"
}

check_gcloud() {
  local gcloud_bin=""
  local python_loc=""

  if [[ -x /opt/google-cloud-sdk/bin/gcloud ]]; then
    gcloud_bin="/opt/google-cloud-sdk/bin/gcloud"
  elif have_cmd gcloud; then
    gcloud_bin="$(command -v gcloud)"
    warn "gcloud not in /opt/google-cloud-sdk/bin (found $gcloud_bin)"
  else
    warn "gcloud not installed"
    return 0
  fi

  if [[ -d "$HOME/google-cloud-sdk" ]]; then
    warn "legacy gcloud SDK still in ~/google-cloud-sdk"
  fi

  if python_loc="$($gcloud_bin info --format='value(basic.python_location)' 2>/dev/null)"; then
    if [[ "$python_loc" == *"/.config/gcloud/virtenv/"* ]]; then
      log "ok: gcloud venv"
    else
      warn "gcloud python location unexpected: $python_loc"
    fi
  else
    fail "gcloud info failed"
  fi

  if [[ -d "$HOME/.config/gcloud" ]]; then
    if find "$HOME/.config/gcloud" -not -user "$USER" -print -quit | rg -q .; then
      fail "gcloud config has non-user ownership"
    else
      log "ok: gcloud config ownership"
    fi
  fi
}

check_log_health() {
  local log_file="$LOG_DIR/macos-dev-maintenance.out"
  local recent=""

  if [[ ! -f "$log_file" ]]; then
    warn "maintenance log not found"
    return 0
  fi

  recent="$(awk '/Homebrew update\./{buf="";collect=1} collect{buf=buf $0 "\n"} END{print buf}' "$log_file" 2>/dev/null || true)"
  if [[ -z "$recent" ]]; then
    recent="$(tail -n 200 "$log_file" 2>/dev/null || true)"
  fi
  if [[ -z "$recent" ]]; then
    warn "maintenance log empty"
    return 0
  fi

  if printf '%s' "$recent" | rg -q "mapfile: command not found"; then
    fail "recent maintenance log contains mapfile errors"
  fi
  if printf '%s' "$recent" | rg -q "mise ERROR NetworkError: api request failed with status: 401"; then
    warn "recent maintenance log has mise 401 errors"
  fi
  if printf '%s' "$recent" | rg -q "PermissionError: .*gcloud/virtenv"; then
    warn "recent maintenance log has gcloud venv permission errors"
  fi
}

main() {
  setup_path
  log "Starting health check."
  check_cmd mise 1
  check_cmd brew 0
  check_cmd bun 0
  check_cmd uv 0
  check_cmd pixi 0
  check_cmd rg 1

  check_file "$HOME/.oh-my-zsh/custom/macos-env.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/llvm.zsh" 0
  check_file "/etc/newsyslog.d/com.ray-manaloto.macos-dev-maintenance.conf" 0

  check_launchd
  check_gcloud

  check_secret "mde-github-token"
  check_secret "mde-github-mcp-pat"
  check_secret "mde-openai-api-key"
  check_secret "mde-anthropic-api-key"
  check_secret "mde-langsmith-api-key"

  check_log_health

  if [[ "$failures" -ne 0 ]]; then
    log "Health check FAILED (${failures} failures, ${warnings} warnings)."
    return 1
  fi

  log "Health check PASSED (${warnings} warnings)."
}

main "$@"
