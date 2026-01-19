#!/usr/bin/env bash
# Managed by macos-development-environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

common_path="$SCRIPT_DIR/mcp/mde-mcp-common.sh"
if [[ ! -f "$common_path" ]]; then
  common_path="$HOME/.local/bin/mde-mcp-common.sh"
fi

# shellcheck source=/dev/null
if [[ -f "$common_path" ]]; then
  source "$common_path"
else
  echo "mde-mcp-common.sh not found. Run scripts/setup-mcp-servers.sh first." >&2
  exit 1
fi

self_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

find_claude() {
  local entry=""
  local candidate=""
  IFS=':' read -r -a entries <<< "$PATH"
  for entry in "${entries[@]}"; do
    candidate="$entry/claude"
    if [[ "$candidate" == "$self_path" ]]; then
      continue
    fi
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_claude() {
  if [[ -n "${MDE_CLAUDE_CLI:-}" && -f "${MDE_CLAUDE_CLI}" ]]; then
    printf '%s\n' "$MDE_CLAUDE_CLI"
    return 0
  fi

  local bun_cli="$HOME/.bun/install/global/node_modules/@anthropic-ai/claude-code/cli.js"
  if [[ -f "$bun_cli" ]]; then
    printf '%s\n' "$bun_cli"
    return 0
  fi

  local found=""
  found="$(find_claude || true)"
  if [[ -n "$found" ]]; then
    printf '%s\n' "$found"
    return 0
  fi

  return 1
}

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  mde_mcp_load_op_secret MDE_OP_GITHUB_TOKEN_REF GITHUB_TOKEN
  mde_mcp_load_keychain_secret "mde-github-token" GITHUB_TOKEN

  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
  fi
fi

claude_bin="$(resolve_claude || true)"
if [[ -z "$claude_bin" ]]; then
  echo "claude CLI not found. Install @anthropic-ai/claude-code or set MDE_CLAUDE_CLI." >&2
  exit 1
fi

exec "$claude_bin" "$@"
