#!/usr/bin/env bash
# Managed by macos-development-environment.

mde_mcp_have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

mde_mcp_load_keychain_secret() {
  local label="$1"
  local env_var="$2"
  local value=""

  if [[ -n "${!env_var:-}" ]]; then
    return 0
  fi
  if ! mde_mcp_have_cmd security; then
    return 0
  fi

  value="$(security find-generic-password -s "$label" -w 2>/dev/null || true)"
  if [[ -z "$value" ]]; then
    return 0
  fi

  printf -v "$env_var" '%s' "$value"
  export "$env_var"
  return 0
}

mde_mcp_load_op_secret() {
  local ref_var="$1"
  local env_var="$2"
  local ref
  local value
  local token=""

  ref="${!ref_var:-}"
  if [[ -z "$ref" ]]; then
    return 0
  fi
  if [[ -n "${!env_var:-}" ]]; then
    return 0
  fi

  if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    token="$OP_SERVICE_ACCOUNT_TOKEN"
  elif mde_mcp_have_cmd security; then
    token="$(security find-generic-password -s mde-op-sa -w 2>/dev/null || true)"
  fi

  if [[ -z "$token" ]]; then
    return 0
  fi
  if ! mde_mcp_have_cmd op; then
    return 0
  fi

  export OP_SERVICE_ACCOUNT_TOKEN="$token"
  value="$(op read "$ref" 2>/dev/null || true)"
  if [[ -z "$value" ]]; then
    return 0
  fi

  printf -v "$env_var" '%s' "$value"
  export "$env_var"
  return 0
}

mde_mcp_require_secret() {
  local env_var="$1"
  local label="$2"
  local op_ref_var="$3"
  local name="$4"

  mde_mcp_load_op_secret "$op_ref_var" "$env_var"
  mde_mcp_load_keychain_secret "$label" "$env_var"

  if [[ -z "${!env_var:-}" ]]; then
    echo "Missing $name secret. Set $env_var, Keychain $label, or $op_ref_var." >&2
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
