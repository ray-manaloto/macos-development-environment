#!/usr/bin/env bash
# Managed by macos-development-environment.
set -euo pipefail

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

load_op_secret() {
  local ref_var="$1"
  local env_var="$2"
  local ref
  local value
  local token=""

  ref="${!ref_var:-}"
  if [[ -z "$ref" || -n "${!env_var:-}" ]]; then
    return 0
  fi

  if [[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    token="$OP_SERVICE_ACCOUNT_TOKEN"
  elif have_cmd security; then
    token="$(security find-generic-password -s mde-op-sa -w 2>/dev/null || true)"
  fi

  if [[ -z "$token" ]] || ! have_cmd op; then
    return 0
  fi

  export OP_SERVICE_ACCOUNT_TOKEN="$token"
  value="$(op read "$ref" 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf -v "$env_var" '%s' "$value"
    export "$env_var"
  fi
}

load_keychain_secret() {
  local label="$1"
  local env_var="$2"
  local value

  if [[ -n "${!env_var:-}" || ! $(command -v security 2>/dev/null) ]]; then
    return 0
  fi

  value="$(security find-generic-password -s "$label" -w 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf -v "$env_var" '%s' "$value"
    export "$env_var"
  fi
}

if [[ -z "${LANGSMITH_API_KEY:-}" ]]; then
  load_op_secret MDE_OP_LANGSMITH_API_KEY_REF LANGSMITH_API_KEY
  load_keychain_secret "mde-langsmith-api-key" LANGSMITH_API_KEY
fi

if [[ -z "${LANGSMITH_WORKSPACE_ID:-}" && -z "${LANGCHAIN_WORKSPACE_ID:-}" ]]; then
  load_op_secret MDE_OP_LANGSMITH_WORKSPACE_ID_REF LANGSMITH_WORKSPACE_ID
  load_keychain_secret "mde-langsmith-workspace-id" LANGSMITH_WORKSPACE_ID
fi

self_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
cmd_name="$(basename "$0")"

find_other_cmd() {
  local name="$1"
  local self="$2"
  local entry
  local candidate

  IFS=':' read -r -a entries <<< "$PATH"
  for entry in "${entries[@]}"; do
    candidate="$entry/$name"
    if [[ "$candidate" == "$self" ]]; then
      continue
    fi
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

resolve_uv_cmd() {
  local tool_name="$1"
  local cmd="$2"
  local tool_dir=""
  local candidate=""

  if ! have_cmd uv; then
    return 1
  fi

  tool_dir="$(uv tool dir 2>/dev/null || true)"
  if [[ -z "$tool_dir" ]]; then
    return 1
  fi

  candidate="$tool_dir/$tool_name/bin/$cmd"
  if [[ -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  return 1
}

case "$cmd_name" in
  langsmith-fetch)
    uv_tool="langsmith-fetch"
    ;;
  langsmith-migrator)
    uv_tool="langsmith-data-migration-tool"
    ;;
  langsmith-mcp-server)
    uv_tool="langsmith-mcp-server"
    ;;
  *)
    echo "Unknown LangSmith CLI invocation: $cmd_name" >&2
    exit 1
    ;;
esac

target="$(find_other_cmd "$cmd_name" "$self_path" || true)"
if [[ -n "$target" ]]; then
  exec "$target" "$@"
fi

target="$(resolve_uv_cmd "$uv_tool" "$cmd_name" || true)"
if [[ -n "$target" ]]; then
  exec "$target" "$@"
fi

echo "${cmd_name} not found. Run scripts/install-langchain-cli-tools.sh." >&2
exit 1
