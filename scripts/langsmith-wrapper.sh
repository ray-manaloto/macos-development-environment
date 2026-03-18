#!/usr/bin/env bash
# Managed by macos-development-environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

mde_load_secrets
mde_export_alias_if_unset LANGCHAIN_WORKSPACE_ID LANGSMITH_WORKSPACE_ID

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

  if ! mde_have_cmd uv; then
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
