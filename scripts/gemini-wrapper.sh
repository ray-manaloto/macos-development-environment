#!/usr/bin/env bash
# Managed by macos-development-environment.
set -euo pipefail

mise_shims="$HOME/.local/share/mise/shims"
mise_bin="$HOME/.local/share/mise/bin"
if [[ -d "$mise_shims" ]]; then
  export PATH="$mise_shims:$mise_bin:$PATH"
fi

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

mde_load_secrets
mde_export_alias_if_unset GITHUB_MCP_PAT GITHUB_TOKEN

has_extension_flag() {
  local arg=""
  for arg in "$@"; do
    if [[ "$arg" == "--extensions" || "$arg" == "-e" ]]; then
      return 0
    fi
  done
  return 1
}

collect_extensions() {
  local extensions_dir="$HOME/.gemini/extensions"
  local ext_path=""
  local ext_name=""

  if [[ ! -d "$extensions_dir" ]]; then
    return 0
  fi

  while IFS= read -r ext_path; do
    ext_name="$(basename "$ext_path")"
    if [[ "$ext_name" == "mcp-toolbox" ]]; then
      continue
    fi
    printf '%s\n' "$ext_name"
  done < <(find "$extensions_dir" -mindepth 1 -maxdepth 1 -type d -print 2>/dev/null | sort)
}

if ! have_cmd bunx; then
  echo "bunx not found. Install bun or ensure it is on PATH." >&2
  exit 1
fi

gemini_args=()
if ! has_extension_flag "$@"; then
  if [[ -n "${MDE_GEMINI_EXTENSIONS:-}" ]]; then
    read -r -a gemini_exts <<< "$MDE_GEMINI_EXTENSIONS"
    if [[ "${#gemini_exts[@]}" -gt 0 ]]; then
      gemini_args+=(--extensions "${gemini_exts[@]}")
    fi
  elif [[ -z "${MDE_GEMINI_ENABLE_MCP_TOOLBOX:-}" && ! -f "./tools.yaml" ]]; then
    gemini_exts=()
    while IFS= read -r ext; do
      gemini_exts+=("$ext")
    done < <(collect_extensions)
    if [[ "${#gemini_exts[@]}" -gt 0 ]]; then
      gemini_args+=(--extensions "${gemini_exts[@]}")
    fi
  fi
fi

exec bunx -y @google/gemini-cli@latest "${gemini_args[@]}" "$@"
