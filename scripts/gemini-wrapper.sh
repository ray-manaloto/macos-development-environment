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

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  load_op_secret MDE_OP_GEMINI_API_KEY_REF GEMINI_API_KEY
  load_keychain_secret "mde-gemini-api-key" GEMINI_API_KEY
fi

if [[ -z "${GITHUB_MCP_PAT:-}" ]]; then
  load_op_secret MDE_OP_GITHUB_TOKEN_REF GITHUB_MCP_PAT
  load_keychain_secret "mde-github-mcp-pat" GITHUB_MCP_PAT
  if [[ -z "${GITHUB_MCP_PAT:-}" ]]; then
    load_keychain_secret "mde-github-token" GITHUB_MCP_PAT
  fi
  if [[ -z "${GITHUB_MCP_PAT:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
    export GITHUB_MCP_PAT="$GITHUB_TOKEN"
  fi
fi

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
