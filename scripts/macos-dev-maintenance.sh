#!/usr/bin/env bash
set -euo pipefail

export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"
export GIT_TERMINAL_PROMPT=0

MDE_AUTOFIX="${MDE_AUTOFIX:-0}"
MDE_AUTOFIX_STRICT="${MDE_AUTOFIX_STRICT:-0}"
MDE_UPDATE_OMZ="${MDE_UPDATE_OMZ:-0}"
MDE_UV_CACHE_PRUNE="${MDE_UV_CACHE_PRUNE:-0}"
MDE_UPDATE_MCP="${MDE_UPDATE_MCP:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-platform.sh
source "$SCRIPT_DIR/lib/mde-platform.sh"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"
MDE_PLATFORM="${MDE_PLATFORM:-$(mde_detect_platform)}"
LOCK_DIR="${TMPDIR:-/tmp}/macos_dev_maintenance.lock"
LOCK_PID_FILE="$LOCK_DIR/pid"
LOCK_HELD_EXIT_CODE=75
BREW=""

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

with_stable_cwd() {
  local stable_dir="${MDE_STABLE_CWD:-}"
  local tmp_dir=""

  if [[ -n "$stable_dir" && -d "$stable_dir" ]]; then
    (
      cd "$stable_dir"
      "$@"
    )
    return $?
  fi

  tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t mde-stable-cwd)"
  (
    cd "$tmp_dir"
    "$@"
  )
  local rc=$?
  rm -rf "$tmp_dir"
  return "$rc"
}

load_runtime_secrets() {
  mde_load_secrets
  mde_export_alias_if_unset GITHUB_MCP_PAT GITHUB_TOKEN
}

ensure_gcloud_sdk_location() {
  if ! mde_is_macos; then
    return 0
  fi
  local src="$HOME/google-cloud-sdk"
  local helper="/usr/local/sbin/mde-gcloud-migrate"

  if [[ ! -d "$src" ]]; then
    return 0
  fi

  if [[ ! -x "$helper" ]]; then
    log "gcloud SDK in $src; install sudo helper to migrate."
    return 0
  fi

  if sudo -n "$helper"; then
    log "gcloud SDK migration completed."
  else
    log "gcloud SDK migration skipped (sudo not permitted)."
  fi
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  local base="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:$home/.amp/bin:$home/.antigravity/antigravity/bin:$home/.oh-my-zsh/custom/bin"
  if mde_is_macos; then
    export PATH="$base:/opt/google-cloud-sdk/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  else
    export PATH="$base:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  fi
  export UV_CACHE_DIR="${UV_CACHE_DIR:-$(mde_default_uv_cache_dir)}"
  mkdir -p "$UV_CACHE_DIR" 2>/dev/null || true
}

find_brew() {
  if have_cmd brew; then
    BREW="$(command -v brew)"
    return 0
  fi
  if [[ -x /opt/homebrew/bin/brew ]]; then
    BREW="/opt/homebrew/bin/brew"
    return 0
  fi
  if [[ -x /usr/local/bin/brew ]]; then
    BREW="/usr/local/bin/brew"
    return 0
  fi
  return 1
}

resolve_homebrew_curl() {
  local candidate
  local path_candidate=""

  if have_cmd curl; then
    path_candidate="$(command -v curl)"
  fi

  for candidate in \
    "${HOMEBREW_CURL_PATH:-}" \
    "/usr/bin/curl" \
    "$path_candidate" \
    "/opt/homebrew/opt/curl/bin/curl" \
    "/usr/local/opt/curl/bin/curl"
  do
    [[ -n "$candidate" ]] || continue
    [[ -x "$candidate" ]] || continue
    if "$candidate" --version >/dev/null 2>&1; then
      export HOMEBREW_CURL_PATH="$candidate"
      return 0
    fi
  done

  return 1
}

brew_has() {
  [[ -n "$BREW" ]] || return 1
  "$BREW" list --formula "$1" >/dev/null 2>&1
}

backup_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    local backup
    backup="${dir}.bak.$(date +%Y%m%d%H%M%S)"
    mv "$dir" "$backup"
    log "Backed up $dir to $backup"
  fi
}

ensure_mise_global() {
  if ! have_cmd mise; then
    if have_cmd curl; then
      log "Installing mise (missing)."
      curl -fsSL https://mise.run | sh || return 1
      export PATH="$HOME/.local/bin:$PATH"
    else
      log "mise missing and curl not available."
      return 1
    fi
  fi

  log "Ensuring global mise tools."
  mise use -g --yes python@latest node@latest bun@latest go@latest rust@latest || true
  mise reshim || true
}

remove_manager() {
  local name="$1"
  local dir="$2"

  if [[ -n "$BREW" ]] && brew_has "$name"; then
    log "Uninstalling brew formula: $name"
    "$BREW" uninstall "$name" || true
  fi

  backup_dir "$dir"
}

remove_conflicting_managers() {
  log "Removing conflicting runtime managers."
  remove_manager "nvm" "$HOME/.nvm"
  remove_manager "volta" "$HOME/.volta"
  remove_manager "asdf" "$HOME/.asdf"
  remove_manager "pyenv" "$HOME/.pyenv"

  if [[ -d "$HOME/miniconda3" || -d "$HOME/anaconda3" ]]; then
    log "Conda detected (not auto-removed)."
  fi
}

remove_brew_runtimes() {
  local formula

  log "Removing brew-managed runtimes (strict mode)."
  for formula in node go rust; do
    if brew_has "$formula"; then
      log "Uninstalling brew formula: $formula"
      "$BREW" uninstall "$formula" || true
    fi
  done

  if [[ -n "$BREW" ]]; then
    if brew_has llvm; then
      log "Keeping brew Python (llvm depends on it)."
      return 0
    fi
    if have_cmd rg; then
      "$BREW" list --formula | rg '^python(@|$)' || true
    else
      "$BREW" list --formula | grep -E '^python(@|$)' || true
    fi | while read -r formula; do
      log "Uninstalling brew formula: $formula"
      "$BREW" uninstall "$formula" || true
    done
  fi
}

sync_managed_configs() {
  if [[ -x "$SCRIPT_DIR/ensure-managed-configs.sh" ]]; then
    "$SCRIPT_DIR/ensure-managed-configs.sh" || true
  else
    log "ensure-managed-configs.sh missing; skipping config sync."
  fi
}

ensure_tmux_plugins() {
  local tpm_dir="$HOME/.tmux/plugins/tpm"
  if [[ -d "$tpm_dir" ]]; then
    return 0
  fi
  if have_cmd git; then
    git clone https://github.com/tmux-plugins/tpm "$tpm_dir" || true
  fi
}

update_brew() {
  if ! mde_is_macos; then
    log "platform=$MDE_PLATFORM; skipping Homebrew updates."
    return 0
  fi
  if ! find_brew; then
    log "brew not found; skipping Homebrew updates."
    return 0
  fi

  export HOMEBREW_NO_BOTTLE_SOURCE_FALLBACK=1
  export HOMEBREW_NO_INSTALL_CLEANUP=1
  export HOMEBREW_CACHE="$HOME/Library/Caches/Homebrew"
  export HOMEBREW_LOGS="$HOME/Library/Logs/Homebrew"

  if ! resolve_homebrew_curl; then
    log "Homebrew update skipped: no working curl found."
    return 1
  fi

  log "Homebrew update."
  "$BREW" update || return 1
  "$BREW" upgrade --formula -v || return 1

  local outdated_casks=()
  while IFS= read -r cask; do
    [[ -z "$cask" ]] && continue
    [[ "$cask" == "osquery" ]] && continue
    outdated_casks+=("$cask")
  done < <("$BREW" outdated --cask || true)
  if (( ${#outdated_casks[@]} > 0 )); then
    "$BREW" upgrade --cask -v "${outdated_casks[@]}" || return 1
  fi

  return 0
}

ensure_gpg() {
  if have_cmd gpg; then
    return 0
  fi
  if find_brew; then
    log "Installing gnupg (gpg) via Homebrew."
    "$BREW" install gnupg || return 1
    return 0
  fi
  log "gpg missing and brew not available."
  return 1
}

update_mise() {
  if ! have_cmd mise; then
    log "mise not found; skipping runtime updates."
    return 0
  fi

  # Guard: ~/package.json causes bun to hoist npm installs into ~/node_modules/,
  # breaking mise per-version isolation. See scripts/tests/mise-npm-version-isolation.test.sh.
  if [[ -f "$HOME/package.json" ]]; then
    log "WARNING: ~/package.json detected — this breaks mise npm tool isolation (bun hoisting)."
    log "Remove it with: mv ~/package.json ~/package.json.bak.\$(date +%s)"
  fi

  log "mise self-update + upgrade."
  mise self-update --yes || return 1

  mise upgrade --yes || return 1
  log "Regenerating mise lock file."
  mise lock || true
  mise reshim || true
  return 0
}

update_bun() {
  if ! have_cmd bun; then
    return 0
  fi

  local bun_path
  bun_path="$(command -v bun)"
  case "$bun_path" in
    "$HOME/.local/share/mise/installs/bun/"*)
      ;;
    *)
      with_stable_cwd bun upgrade || return 1
      ;;
  esac

  log "Skipping blanket bun global update; repo-managed Node CLIs are refreshed by dedicated installers."
  return 0
}

cleanup_claude_cli() {
  local cleanup="$SCRIPT_DIR/cleanup-claude-cli.sh"
  if [[ -x "$cleanup" ]]; then
    "$cleanup" || return 1
  fi
  return 0
}

cleanup_gemini_cli() {
  local cleanup="$SCRIPT_DIR/cleanup-gemini-cli.sh"
  if [[ -x "$cleanup" ]]; then
    "$cleanup" || return 1
  fi
  return 0
}


update_uv() {
  if ! have_cmd uv; then
    return 0
  fi

  local uv_path
  uv_path="$(command -v uv)"
  case "$uv_path" in
    "$HOME/.local/share/mise/installs/"*|"$HOME/.local/share/mise/shims/"*)
      log "uv is mise-managed; skipping uv self update."
      ;;
    /opt/homebrew/*|/usr/local/*)
      log "uv is Homebrew-managed; skipping uv self update."
      ;;
    *)
      uv self update || return 1
      ;;
  esac

  local tool=""
  local failures=0

  while IFS= read -r tool; do
    [[ -n "$tool" ]] || continue
    if ! uv tool upgrade "$tool"; then
      failures=1
    fi
  done < <(uv tool list 2>/dev/null | awk 'NF && $1 !~ /^-/ {print $1}')

  if [[ "$failures" -ne 0 ]]; then
    return 1
  fi
  return 0
}

prune_uv_cache() {
  if [[ "$MDE_UV_CACHE_PRUNE" != "1" ]]; then
    return 0
  fi
  if ! have_cmd uv; then
    return 0
  fi
  log "Pruning uv cache."
  uv cache prune || return 1
  return 0
}

update_pixi() {
  if ! have_cmd pixi; then
    return 0
  fi
  if ! pixi self-update 2>/dev/null; then log "pixi self-update unavailable; skipping."; fi
  pixi global update || return 1
  return 0
}

update_mcp_servers() {
  local repo_root="$(cd "$SCRIPT_DIR/.." && pwd)"
  local mcp_script="$repo_root/scripts/setup-mcp-servers.sh"

  if [[ ! -x "$mcp_script" ]]; then
    log "MCP setup script missing; skipping MCP sync."
    return 0
  fi

  log "Syncing MCP servers."
  with_stable_cwd "$mcp_script" || return 1
  return 0
}

update_oh_my_zsh() {
  if [[ "$MDE_UPDATE_OMZ" != "1" ]]; then
    return 0
  fi
  if [[ -d "$HOME/.oh-my-zsh/.git" ]]; then
    log "Updating oh-my-zsh."
    git -C "$HOME/.oh-my-zsh" pull --ff-only || return 1
  fi
  return 0
}

prune_stale_tools() {
  log "Pruning stale tools migrated to mise."

  # --- uv tools migrated to mise pipx/aqua/github backends ---
  if have_cmd uv; then
    local uv_tools_to_prune=(
      langchain-cli langgraph-cli langsmith-fetch
      aider-chat open-interpreter crewai skypilot
    )
    local installed_uv=""
    installed_uv="$(uv tool list 2>/dev/null | awk 'NF && $1 !~ /^-/ {print $1}')" || true
    for tool in "${uv_tools_to_prune[@]}"; do
      if echo "$installed_uv" | grep -qx "$tool"; then
        log "  Removing uv tool: $tool"
        uv tool uninstall "$tool" 2>/dev/null || true
      fi
    done
  fi

  # --- bun globals migrated to mise npm/github backends ---
  if have_cmd bun; then
    local bun_globals_to_prune=(
      "@anthropic-ai/claude-code"
      "@openai/codex"
      "@google/gemini-cli"
      "openwork"
      "create-agent-chat-app"
      "@modelcontextprotocol/inspector"
    )
    for pkg in "${bun_globals_to_prune[@]}"; do
      if bun pm ls -g 2>/dev/null | grep -q "$pkg"; then
        log "  Removing bun global: $pkg"
        bun remove -g "$pkg" 2>/dev/null || true
      fi
    done
  fi

  # --- mise orphan version cleanup ---
  if have_cmd mise; then
    log "  Pruning orphan mise versions."
    mise prune --yes 2>/dev/null || true
  fi
}

ensure_learning_db() {
  local learn_script="$SCRIPT_DIR/mde-learn.sh"
  if [[ ! -x "$learn_script" ]]; then
    log "mde-learn.sh not found; skipping learning DB init."
    return 0
  fi
  log "Ensuring learning DB."
  "$learn_script" init || true
}

consolidate_learnings() {
  local learn_script="$SCRIPT_DIR/mde-learn.sh"
  if [[ ! -x "$learn_script" ]]; then
    return 0
  fi
  log "Consolidating learnings."
  "$learn_script" consolidate || true
}

run_validation() {
  log "Running post-update validation."

  if have_cmd mise; then
    log "  mise doctor:"
    mise doctor 2>&1 | head -30 || true
  fi

  local test_script="$SCRIPT_DIR/tests/mde-declarative-tools.test.sh"
  if [[ -x "$test_script" ]]; then
    log "  Declarative tools validation:"
    bash "$test_script" || true
  fi
}

acquire_lock() {
  local holder_pid=""
  local attempts=0

  while true; do
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      printf '%s\n' "$$" > "$LOCK_PID_FILE"
      return 0
    fi

    holder_pid=""
    if [[ -f "$LOCK_PID_FILE" ]]; then
      holder_pid="$(cat "$LOCK_PID_FILE" 2>/dev/null || true)"
    fi

    if [[ "$holder_pid" =~ ^[0-9]+$ ]] && kill -0 "$holder_pid" 2>/dev/null; then
      log "Another maintenance run is in progress (pid $holder_pid); exiting."
      return "$LOCK_HELD_EXIT_CODE"
    fi

    if [[ "$attempts" -ge 1 ]]; then
      log "Another maintenance run is in progress; exiting."
      return "$LOCK_HELD_EXIT_CODE"
    fi

    log "Found stale maintenance lock; clearing."
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    attempts=$((attempts + 1))
  done
}

release_lock() {
  rm -f "$LOCK_PID_FILE" 2>/dev/null || true
  rmdir "$LOCK_DIR" 2>/dev/null || rm -rf "$LOCK_DIR" 2>/dev/null || true
}

main() {
  if acquire_lock; then
    :
  else
    local lock_status=$?
    exit "$lock_status"
  fi
  trap 'release_lock' EXIT

  setup_path
  ensure_learning_db || true
  ensure_gcloud_sdk_location || true
  mde_load_secrets || true
  load_runtime_secrets || true
  if [[ -x "$SCRIPT_DIR/secrets-smoke-test.sh" ]]; then
    "$SCRIPT_DIR/secrets-smoke-test.sh" || true
  fi

  failures=0
  update_brew || failures=1
  update_mise || failures=1
  prune_stale_tools || true
  update_bun || failures=1
  cleanup_claude_cli || failures=1
  cleanup_gemini_cli || failures=1
  update_uv || failures=1
  prune_uv_cache || failures=1
  update_pixi || failures=1
  if [[ "$MDE_UPDATE_MCP" == "1" ]]; then
    update_mcp_servers || failures=1
  fi
  if mde_is_devcontainer; then
    log "platform=devcontainer; forcing MDE_UPDATE_OMZ=0"
    MDE_UPDATE_OMZ=0
  fi
  update_oh_my_zsh || failures=1

  # Config sync is idempotent (MANAGED_MARKER guard) and safe to run
  # unconditionally. Gating it behind MDE_AUTOFIX caused template-deploy
  # drift (6 missing aliases, stale env vars). See docs/decision-log.md.
  sync_managed_configs

  if [[ "$MDE_AUTOFIX" == "1" ]]; then
    mise_ready=0
    if ensure_mise_global; then
      mise_ready=1
    fi

    ensure_gpg || true

    if [[ "$mise_ready" == "1" ]]; then
      remove_conflicting_managers
    else
      log "Skipping manager cleanup (mise not available)."
    fi
    ensure_tmux_plugins

    if [[ "$mise_ready" == "1" && "$MDE_AUTOFIX_STRICT" == "1" ]]; then
      if find_brew; then
        remove_brew_runtimes
      fi
    fi
  fi

  consolidate_learnings || true
  run_validation

  if [[ "$failures" -ne 0 ]]; then
    exit 1
  fi
}

main "$@"
