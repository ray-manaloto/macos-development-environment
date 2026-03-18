#!/usr/bin/env bash
# shellcheck disable=SC2329
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Devcontainer uses a minimal pinned tool set. The full tool catalog is in
# .chezmoisource/dot_config/mise/config.toml.tmpl (deployed via chezmoi apply).
DEVCONTAINER_MISE_CONFIG="$REPO_ROOT/.devcontainer/mise.toml"
DEVCONTAINER_MISE_LOCK="$REPO_ROOT/.devcontainer/mise.lock"

export MDE_PLATFORM=devcontainer
export MDE_ENV_AUTOLOAD=0
export MDE_AUTOLOAD_SECRETS=0
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$HOME/.local/run}"

REQ_PASS=0
REQ_FAIL=0
OPT_PASS=0
OPT_FAIL=0

BOOTSTRAP_STATE_DIR="$XDG_STATE_HOME/macos-development-environment"
BOOTSTRAP_HASH_FILE="$BOOTSTRAP_STATE_DIR/devcontainer-bootstrap.sha256"
GLOBAL_MISE_DIR="$XDG_CONFIG_HOME/mise"
GLOBAL_MISE_CONFIG="$GLOBAL_MISE_DIR/config.toml"
GLOBAL_MISE_LOCK="$GLOBAL_MISE_DIR/mise.lock"

ensure_bootstrap_dirs() {
  mkdir -p \
    "$BOOTSTRAP_STATE_DIR" \
    "$GLOBAL_MISE_DIR" \
    "$XDG_CACHE_HOME/zsh" \
    "$XDG_DATA_HOME/zsh" \
    "$XDG_RUNTIME_DIR" \
    "$HOME/.oh-my-zsh/custom/completions"
}

setup_mise_path() {
  export PATH="$HOME/.local/share/mise/shims:$HOME/.local/share/mise/bin:$HOME/.local/bin:$PATH"
}

hash_cmd() {
  if command -v sha256sum >/dev/null 2>&1; then
    printf 'sha256sum\n'
    return 0
  fi
  if command -v shasum >/dev/null 2>&1; then
    printf 'shasum -a 256\n'
    return 0
  fi
  return 1
}

hash_file() {
  local file="$1"
  local cmd
  cmd="$(hash_cmd)"
  $cmd "$file" | awk '{print $1}'
}

bootstrap_manifest_hash() {
  local file
  local cmd
  cmd="$(hash_cmd)"
  {
    for file in \
      "$REPO_ROOT/.devcontainer/post-create.sh" \
      "$DEVCONTAINER_MISE_CONFIG" \
      "$DEVCONTAINER_MISE_LOCK" \
      "$REPO_ROOT/scripts/ensure-managed-configs.sh"; do
      printf '%s  %s\n' "$(hash_file "$file")" "${file#$REPO_ROOT/}"
    done

    if [[ -d "$REPO_ROOT/.chezmoisource" ]]; then
      while IFS= read -r file; do
        printf '%s  %s\n' "$(hash_file "$file")" "${file#$REPO_ROOT/}"
      done < <(find "$REPO_ROOT/.chezmoisource" -type f | LC_ALL=C sort)
    fi
  } | $cmd | awk '{print $1}'
}

global_mise_config_synced() {
  cmp -s "$DEVCONTAINER_MISE_CONFIG" "$GLOBAL_MISE_CONFIG" &&
    cmp -s "$DEVCONTAINER_MISE_LOCK" "$GLOBAL_MISE_LOCK"
}

sync_devcontainer_mise_config() {
  install -m 0644 "$DEVCONTAINER_MISE_CONFIG" "$GLOBAL_MISE_CONFIG"
  install -m 0644 "$DEVCONTAINER_MISE_LOCK" "$GLOBAL_MISE_LOCK"
}

bootstrap_tools_missing() {
  local tool
  setup_mise_path
  for tool in chezmoi python3 bun uv pixi; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

bootstrap_refresh_required() {
  local current_hash="$1"
  local previous_hash=""

  if [[ -f "$BOOTSTRAP_HASH_FILE" ]]; then
    previous_hash="$(<"$BOOTSTRAP_HASH_FILE")"
  fi

  if [[ "$previous_hash" != "$current_hash" ]]; then
    return 0
  fi

  if ! global_mise_config_synced; then
    return 0
  fi

  if bootstrap_tools_missing; then
    return 0
  fi

  return 1
}

run_required() {
  local label="$1"
  shift
  echo "[required] $label"
  if "$@"; then
    REQ_PASS=$((REQ_PASS + 1))
    return 0
  fi
  REQ_FAIL=$((REQ_FAIL + 1))
  echo "[required] FAILED: $label" >&2
  return 1
}

verify_baked_baseline() {
  setup_mise_path
  command -v mise >/dev/null 2>&1
}

trust_repo_mise_configs() {
  mise trust -y "$REPO_ROOT/.mise.toml"
  mise trust -y "$DEVCONTAINER_MISE_CONFIG"
}

install_devcontainer_tooling() {
  local current_hash

  current_hash="$(bootstrap_manifest_hash)"
  sync_devcontainer_mise_config

  if ! bootstrap_refresh_required "$current_hash"; then
    echo "devcontainer bootstrap is current; skipping reinstall."
    return 0
  fi

  mise install --locked
}

sync_managed_configs() {
  (cd "$REPO_ROOT" && scripts/ensure-managed-configs.sh)
}

run_verification_checks() {
  local status_json=""

  (cd "$REPO_ROOT" && mise run mde:verify)
  (cd "$REPO_ROOT" && mise run mde:drift)
  status_json="$(cd "$REPO_ROOT" && mise run mde:status)"
  printf '%s\n' "$status_json" | jq -e . >/dev/null
}

persist_bootstrap_state() {
  bootstrap_manifest_hash >"$BOOTSTRAP_HASH_FILE"
}

ensure_bootstrap_dirs
run_required "verify baked devcontainer baseline" verify_baked_baseline || true
run_required "trust repo mise configs" trust_repo_mise_configs || true
run_required "install devcontainer bootstrap tooling" install_devcontainer_tooling || true
run_required "sync managed configs" sync_managed_configs || true
run_required "run container verification checks" run_verification_checks || true
run_required "persist devcontainer bootstrap state" persist_bootstrap_state || true

echo
echo "Bootstrap summary:"
echo "  required: pass=$REQ_PASS fail=$REQ_FAIL"
echo "  optional: pass=$OPT_PASS fail=$OPT_FAIL"

if (( REQ_FAIL > 0 )); then
  exit 1
fi

exit 0
