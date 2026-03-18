#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-platform.sh
source "$SCRIPT_DIR/lib/mde-platform.sh"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

MDE_PLATFORM="${MDE_PLATFORM:-$(mde_detect_platform)}"
LOG_DIR="$(mde_default_log_dir)"

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
  local base="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin"
  if mde_is_macos; then
    export PATH="$base:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  else
    export PATH="$base:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  fi
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

check_dir() {
  local path="$1"
  local required="$2"

  if [[ -d "$path" ]]; then
    log "ok: $path"
    return 0
  fi

  if [[ "$required" == "1" ]]; then
    fail "missing directory: $path"
  else
    warn "missing directory: $path"
  fi
}

check_python_runtime() {
  if have_cmd python3; then
    log "ok: python3"
    return 0
  fi
  if have_cmd python; then
    log "ok: python"
    return 0
  fi
  fail "missing command: python3/python"
}

check_mise_npm_backend_bun() {
  local backend=""

  if ! command -v mise >/dev/null 2>&1; then
    fail "mise not available for npm backend check"
    return 1
  fi

  backend="$(mise settings get npm.package_manager 2>/dev/null || true)"
  if [[ "$backend" != "bun" ]]; then
    fail "mise npm.package_manager is '$backend' (expected 'bun')"
    return 1
  fi

  log "ok: mise npm.package_manager is bun"
}

check_claude_path() {
  local expected_shim="$HOME/.local/share/mise/shims/claude"
  local expected_target=""
  local actual=""

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping claude source validation"
    return 0
  fi

  expected_target="$(mise which claude 2>/dev/null || true)"
  if [[ -z "$expected_target" ]]; then
    warn "mise has no claude tool configured"
    return 0
  fi

  if ! command -v claude >/dev/null 2>&1; then
    warn "claude not found in PATH"
    return 0
  fi

  actual="$(command -v claude)"

  if [[ "$actual" != "$expected_shim" ]]; then
    fail "claude source mismatch: $actual (expected mise shim: $expected_shim)"
    return 1
  fi

  if [[ ! "$expected_target" == "$HOME/.local/share/mise/installs/"* ]]; then
    fail "mise target for claude is unexpected: $expected_target"
    return 1
  fi

  log "ok: claude sourced from mise shim ($actual -> $expected_target)"
}

check_claude_zsh_resolution() {
  local expected_shim="$HOME/.local/share/mise/shims/claude"
  local expected_target=""
  local out=""
  local first_line=""
  local alias_line=""
  local cmdv_line=""

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping interactive claude resolution check"
    return 0
  fi

  expected_target="$(mise which claude 2>/dev/null || true)"
  if [[ -z "$expected_target" ]]; then
    warn "claude not installed via mise; skipping interactive zsh resolution check"
    return 0
  fi

  if ! command -v zsh >/dev/null 2>&1; then
    warn "zsh not available; skipping interactive claude resolution check"
    return 0
  fi

  out="$(zsh -lic '
    type -a claude 2>/dev/null || true
    echo "__SEP__"
    alias claude 2>/dev/null || true
    echo "__SEP__"
    command -v claude 2>/dev/null || true
  ' 2>/dev/null || true)"
  first_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==0 && NF{print; exit}')"
  alias_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==1 && NF{print; exit}')"
  cmdv_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==2 && NF{print; exit}')"

  if [[ -n "$alias_line" ]]; then
    fail "interactive zsh has claude alias: $alias_line"
    return 1
  fi

  if [[ "$cmdv_line" != "$expected_shim" ]]; then
    fail "interactive zsh claude mismatch: $cmdv_line (expected $expected_shim)"
    return 1
  fi

  if [[ ! "$first_line" == *"$expected_shim"* ]]; then
    fail "interactive zsh first claude resolution is not mise shim: $first_line"
    return 1
  fi

  log "ok: interactive zsh resolves claude to mise shim ($expected_shim)"
}

check_claude_mise_setup() {
  local backend=""
  local registry_line=""
  local legacy_wrapper="$HOME/.local/bin/claude"

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping claude mise setup checks"
    return 0
  fi

  backend="$(mise settings get npm.package_manager 2>/dev/null || true)"
  if [[ "$backend" != "bun" ]]; then
    fail "mise npm.package_manager is '$backend' (expected 'bun')"
    return 1
  fi

  registry_line="$(mise registry claude 2>/dev/null || true)"
  if [[ "$registry_line" != *"npm:@anthropic-ai/claude-code"* ]]; then
    fail "mise registry claude missing npm backend mapping: $registry_line"
    return 1
  fi

  if [[ -e "$legacy_wrapper" ]]; then
    warn "legacy wrapper exists at $legacy_wrapper (should not be used)"
  fi

  log "ok: mise claude setup"
}

check_gemini_path() {
  local expected_shim="$HOME/.local/share/mise/shims/gemini"
  local expected_target=""
  local actual=""

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping gemini source validation"
    return 0
  fi

  expected_target="$(mise which gemini 2>/dev/null || true)"
  if [[ -z "$expected_target" ]]; then
    warn "mise has no gemini executable configured"
    return 0
  fi

  if ! command -v gemini >/dev/null 2>&1; then
    warn "gemini not found in PATH"
    return 0
  fi

  actual="$(command -v gemini)"

  if [[ "$actual" != "$expected_shim" ]]; then
    fail "gemini source mismatch: $actual (expected mise shim: $expected_shim)"
    return 1
  fi

  if [[ ! "$expected_target" == "$HOME/.local/share/mise/installs/"* ]]; then
    fail "mise target for gemini-cli is unexpected: $expected_target"
    return 1
  fi

  log "ok: gemini sourced from mise shim ($actual -> $expected_target)"
}

check_gemini_zsh_resolution() {
  local expected_shim="$HOME/.local/share/mise/shims/gemini"
  local expected_target=""
  local out=""
  local first_line=""
  local alias_line=""
  local cmdv_line=""

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping interactive gemini resolution check"
    return 0
  fi

  expected_target="$(mise which gemini 2>/dev/null || true)"
  if [[ -z "$expected_target" ]]; then
    warn "gemini not installed via mise; skipping interactive zsh resolution check"
    return 0
  fi

  if ! command -v zsh >/dev/null 2>&1; then
    warn "zsh not available; skipping interactive gemini resolution check"
    return 0
  fi

  out="$(zsh -lic '
    type -a gemini 2>/dev/null || true
    echo "__SEP__"
    alias gemini 2>/dev/null || true
    echo "__SEP__"
    command -v gemini 2>/dev/null || true
  ' 2>/dev/null || true)"
  first_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==0 && NF{print; exit}')"
  alias_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==1 && NF{print; exit}')"
  cmdv_line="$(printf "%s\n" "$out" | awk 'BEGIN{s=0}/^__SEP__/{s++;next} s==2 && NF{print; exit}')"

  if [[ -n "$alias_line" ]]; then
    fail "interactive zsh has gemini alias: $alias_line"
    return 1
  fi

  if [[ "$cmdv_line" != "$expected_shim" ]]; then
    fail "interactive zsh gemini mismatch: $cmdv_line (expected $expected_shim)"
    return 1
  fi

  if [[ ! "$first_line" == *"$expected_shim"* ]]; then
    fail "interactive zsh first gemini resolution is not mise shim: $first_line"
    return 1
  fi

  log "ok: interactive zsh resolves gemini to mise shim ($expected_shim)"
}

check_gemini_mise_setup() {
  local backend=""
  local registry_line=""
  local legacy_wrapper="$HOME/.local/bin/gemini"

  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not available; skipping gemini mise setup checks"
    return 0
  fi

  backend="$(mise settings get npm.package_manager 2>/dev/null || true)"
  if [[ "$backend" != "bun" ]]; then
    fail "mise npm.package_manager is '$backend' (expected 'bun')"
    return 1
  fi

  registry_line="$(mise registry gemini-cli 2>/dev/null || true)"
  if [[ "$registry_line" != *"npm:@google/gemini-cli"* ]]; then
    fail "mise registry gemini-cli missing npm backend mapping: $registry_line"
    return 1
  fi

  if [[ -e "$legacy_wrapper" ]]; then
    warn "legacy wrapper exists at $legacy_wrapper (should not be used)"
  fi

  log "ok: mise gemini setup"
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
  local env_var="$1"

  mde_load_secrets

  if [[ -n "${!env_var:-}" ]]; then
    log "ok: secret env $env_var"
    return 0
  fi

  warn "missing secret env: $env_var"
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
  if ! mde_is_macos; then
    log "n/a: launchd checks skipped on platform=$MDE_PLATFORM"
    return 0
  fi
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
    if find "$HOME/.config/gcloud" -not -user "$USER" -print -quit | grep -q .; then
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

  if printf '%s' "$recent" | grep -q "mapfile: command not found"; then
    fail "recent maintenance log contains mapfile errors"
  fi
  if printf '%s' "$recent" | grep -q "mise ERROR NetworkError: api request failed with status: 401"; then
    warn "recent maintenance log has mise 401 errors"
  fi
  if printf '%s' "$recent" | grep -Eq "PermissionError: .*gcloud/virtenv"; then
    warn "recent maintenance log has gcloud venv permission errors"
  fi
}

check_devcontainer_contract() {
  check_cmd mise 1
  check_cmd jq 1
  check_cmd rg 1
  check_cmd chezmoi 1
  check_cmd bun 1
  check_cmd uv 1
  check_cmd pixi 1
  check_python_runtime
  check_mise_npm_backend_bun

  check_file "$HOME/.config/mise/config.toml" 1
  check_file "$HOME/.config/mise/mise.lock" 1
  check_file "$HOME/.oh-my-zsh/custom/10-mde-core.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/15-mde-platform.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh" 1
  check_file "$HOME/.zprofile.d/macos-dev-env.zsh" 1
  check_dir "$HOME/.oh-my-zsh/custom/completions" 1
}

main() {
  setup_path
  log "Starting health check (platform=$MDE_PLATFORM)."

  if mde_is_devcontainer; then
    check_devcontainer_contract
    if [[ "$failures" -ne 0 ]]; then
      log "Health check FAILED (${failures} failures, ${warnings} warnings)."
      return 1
    fi
    log "Health check PASSED (${warnings} warnings)."
    return 0
  fi

  check_cmd mise 1
  check_cmd brew 0
  check_cmd bun 0
  check_cmd uv 0
  check_cmd pixi 0
  check_cmd rg 1
  check_cmd rustc 1

  check_claude_mise_setup
  check_claude_path
  check_claude_zsh_resolution
  check_gemini_mise_setup
  check_gemini_path
  check_gemini_zsh_resolution

  check_file "$HOME/.oh-my-zsh/custom/10-mde-core.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/15-mde-platform.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh" 1
  check_file "$HOME/.oh-my-zsh/custom/llvm.zsh" 0

  if mde_is_macos; then
    check_file "/etc/newsyslog.d/com.ray-manaloto.macos-dev-maintenance.conf" 0
  fi

  check_launchd
  check_gcloud

  check_secret "GITHUB_TOKEN"
  check_secret "OPENAI_API_KEY"
  check_secret "ANTHROPIC_API_KEY"
  check_secret "LANGSMITH_API_KEY"
  check_secret "GEMINI_API_KEY"

  check_log_health

  if [[ "$failures" -ne 0 ]]; then
    log "Health check FAILED (${failures} failures, ${warnings} warnings)."
    return 1
  fi

  log "Health check PASSED (${warnings} warnings)."
}

main "$@"
