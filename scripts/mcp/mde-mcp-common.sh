#!/usr/bin/env bash
# Managed by macos-development-environment.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/../lib/mde-secrets.sh"

mde_mcp_have_cmd() {
  mde_have_cmd "$1"
}

mde_mcp_load_keychain_secret() {
  local _label="$1"
  local env_var="$2"
  mde_load_secrets
  [[ -n "${!env_var:-}" ]]
}

mde_mcp_load_op_secret() {
  local _ref_var="$1"
  local env_var="$2"
  mde_load_secrets
  [[ -n "${!env_var:-}" ]]
}

mde_mcp_require_secret() {
  local env_var="$1"
  local _label="$2"
  local _op_ref_var="$3"
  local name="$4"

  mde_load_secrets

  if [[ -z "${!env_var:-}" ]]; then
    echo "Missing $name secret. Set $env_var or configure fnox/mise secret loading." >&2
    return 1
  fi

  return 0
}

mde_mcp_run_node_tool() {
  local package="$1"
  shift || true

  if mde_mcp_have_cmd bunx; then
    exec bunx -y "$package" "$@"
  fi

  if mde_mcp_have_cmd npx; then
    exec npx -y "$package" "$@"
  fi

  echo "Missing bunx or npx to run $package." >&2
  return 1
}
