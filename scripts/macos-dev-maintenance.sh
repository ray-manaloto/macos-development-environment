#!/usr/bin/env bash
set -euo pipefail

export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"

MDE_AUTOFIX="${MDE_AUTOFIX:-0}"
MDE_AUTOFIX_STRICT="${MDE_AUTOFIX_STRICT:-0}"
MDE_UPDATE_OMZ="${MDE_UPDATE_OMZ:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK_DIR="${TMPDIR:-/tmp}/macos_dev_maintenance.lock"
BREW=""

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

load_op_secret() {
  local ref_var="$1"
  local env_var="$2"
  local ref
  local value

  ref="${!ref_var:-}"
  if [[ -z "$ref" ]]; then
    return 0
  fi
  if [[ -n "${!env_var:-}" ]]; then
    return 0
  fi

  value="$(op read "$ref" 2>/dev/null || true)"
  if [[ -z "$value" ]]; then
    log "1Password read failed for $ref_var."
    return 0
  fi

  printf -v "$env_var" '%s' "$value"
  export "$env_var"
  return 0
}

load_1password_secrets() {
  local token="${OP_SERVICE_ACCOUNT_TOKEN:-}"

  if [[ -z "$token" ]] && have_cmd security; then
    token="$(security find-generic-password -s mde-op-sa -w 2>/dev/null || true)"
  fi

  if [[ -z "$token" ]]; then
    return 0
  fi

  if ! have_cmd op; then
    log "1Password CLI not found; skipping secrets load."
    return 0
  fi

  export OP_SERVICE_ACCOUNT_TOKEN="$token"

  load_op_secret MDE_OP_GITHUB_TOKEN_REF GITHUB_TOKEN
  load_op_secret MDE_OP_GITHUB_MCP_PAT_REF GITHUB_MCP_PAT
  load_op_secret MDE_OP_OPENAI_API_KEY_REF OPENAI_API_KEY
  load_op_secret MDE_OP_ANTHROPIC_API_KEY_REF ANTHROPIC_API_KEY
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.bun/bin:$home/.pixi/bin:$home/.local/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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
  if ! find_brew; then
    log "brew not found; skipping Homebrew updates."
    return 0
  fi

  export HOMEBREW_NO_BOTTLE_SOURCE_FALLBACK=1
  export HOMEBREW_NO_INSTALL_CLEANUP=1
  export HOMEBREW_CACHE="$HOME/Library/Caches/Homebrew"
  export HOMEBREW_LOGS="$HOME/Library/Logs/Homebrew"

  log "Homebrew update."
  "$BREW" update || return 1
  "$BREW" upgrade --formula -v || return 1

  local outdated_casks=()
  mapfile -t outdated_casks < <("$BREW" outdated --cask | grep -v '^osquery$' || true)
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
  log "mise self-update + upgrade."
  mise self-update || return 1
  mise upgrade --yes || return 1
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
      bun upgrade || return 1
      ;;
  esac

  bun update -g --latest || return 1
  return 0
}

update_uv() {
  if ! have_cmd uv; then
    return 0
  fi

  local uv_path
  uv_path="$(command -v uv)"
  case "$uv_path" in
    /opt/homebrew/*|/usr/local/*)
      ;;
    *)
      uv self update || return 1
      ;;
  esac

  uv tool upgrade --all || return 1
  return 0
}

update_pixi() {
  if ! have_cmd pixi; then
    return 0
  fi
  pixi self-update || return 1
  pixi global update || return 1
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

main() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "Another maintenance run is in progress; exiting."
    exit 0
  fi
  trap 'rmdir "$LOCK_DIR"' EXIT

  setup_path
  load_1password_secrets || true

  failures=0
  update_brew || failures=1
  update_mise || failures=1
  update_bun || failures=1
  update_uv || failures=1
  update_pixi || failures=1
  update_oh_my_zsh || failures=1

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
    sync_managed_configs
    ensure_tmux_plugins

    if [[ "$mise_ready" == "1" && "$MDE_AUTOFIX_STRICT" == "1" ]]; then
      if find_brew; then
        remove_brew_runtimes
      fi
    fi
  fi

  if [[ "$failures" -ne 0 ]]; then
    exit 1
  fi
}

main "$@"
