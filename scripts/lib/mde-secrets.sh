#!/usr/bin/env bash

mde_have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

mde_bootstrap_mise_path() {
  local candidate=""

  for candidate in \
    "$HOME/.local/share/mise/bin" \
    "$HOME/.local/bin"
  do
    [[ -d "$candidate" ]] || continue
    case ":$PATH:" in
      *":$candidate:"*) ;;
      *) export PATH="$candidate:$PATH" ;;
    esac
  done
}

mde_load_mise_env() {
  local env_script=""

  if [[ "${MDE_USE_MISE_SECRETS:-1}" != "1" ]]; then
    return 0
  fi

  if [[ -n "${MDE_MISE_ENV_SOURCED:-}" ]]; then
    return 0
  fi

  export MISE_ENV_CACHE="${MISE_ENV_CACHE:-1}"
  export FNOX_CONFIG_DIR="${FNOX_CONFIG_DIR:-$HOME/.config/fnox}"
  export FNOX_AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
  export SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$FNOX_AGE_KEY_FILE}"

  mde_bootstrap_mise_path
  if ! mde_have_cmd mise; then
    return 0
  fi

  env_script="$(mise env -s bash 2>/dev/null || true)"
  if [[ -z "$env_script" ]]; then
    return 0
  fi

  export MDE_MISE_ENV_SOURCED=1
  eval "$env_script"
}

mde_load_secrets() {
  mde_load_mise_env
}

mde_export_alias_if_unset() {
  local target_var="$1"
  local source_var="$2"

  if [[ -n "${!target_var:-}" || -z "${!source_var:-}" ]]; then
    return 0
  fi

  printf -v "$target_var" '%s' "${!source_var}"
  export "$target_var"
}
