#!/usr/bin/env bash
set -euo pipefail

INCLUDE_INTERNAL="${INCLUDE_INTERNAL:-1}"
SMOKE_MODE="${MDE_LANGCHAIN_SMOKE:-1}"
SMOKE_TIMEOUT="${MDE_LANGCHAIN_SMOKE_TIMEOUT:-8}"
SMOKE_STRICT="${MDE_LANGCHAIN_SMOKE_STRICT:-0}"
LANGSMITH_PING="${MDE_LANGSMITH_PING:-1}"
LANGSMITH_ENDPOINT="${LANGSMITH_ENDPOINT:-${LANGSMITH_API_URL:-https://api.smith.langchain.com}}"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"
mkdir -p "$UV_CACHE_DIR" 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

mde_load_secrets
mde_export_alias_if_unset LANGCHAIN_WORKSPACE_ID LANGSMITH_WORKSPACE_ID

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "missing command: $1"
    return 1
  fi
  return 0
}

uv_installed_tools() {
  uv tool list 2>/dev/null | awk 'NF && $1 !~ /^-/{print $1}'
}

tool_present() {
  local name="$1"
  if mde_have_cmd rg; then
    printf '%s\n' "$INSTALLED_TOOLS" | rg -qx "$name"
    return $?
  fi
  printf '%s\n' "$INSTALLED_TOOLS" | grep -Fxq "$name"
}

run_with_timeout() {
  local timeout="$1"
  shift

  if [[ -z "$timeout" || "$timeout" == "0" ]]; then
    "$@"
    return $?
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$timeout" "$@" <<'PY'
import subprocess
import sys

try:
    timeout = int(sys.argv[1])
except ValueError:
    timeout = 0
cmd = sys.argv[2:]
try:
    subprocess.run(cmd, check=True, timeout=timeout or None)
except subprocess.TimeoutExpired:
    print(f"timed out after {timeout}s", file=sys.stderr)
    sys.exit(124)
except subprocess.CalledProcessError as exc:
    sys.exit(exc.returncode)
PY
  else
    "$@"
  fi
}

tool_python() {
  local name="$1"
  local home="${HOME:-/Users/rmanaloto}"
  local python="$home/.local/share/uv/tools/$name/bin/python"
  if [[ -x "$python" ]]; then
    printf '%s' "$python"
    return 0
  fi
  return 1
}

smoke_import() {
  local tool="$1"
  local module="$2"
  local failures_ref="$3"
  local python_path=""

  python_path="$(tool_python "$tool" || true)"
  if [[ -z "$python_path" ]]; then
    log "missing python for $tool"
    eval "$failures_ref=1"
    return 1
  fi

  if run_with_timeout "$SMOKE_TIMEOUT" "$python_path" - "$module" <<'PYDOC' >/dev/null 2>&1
import importlib
import sys

importlib.import_module(sys.argv[1])
PYDOC
  then
    log "ok: import $module"
    return 0
  fi

  log "failed: import $module"
  eval "$failures_ref=1"
  return 1
}

ensure_langsmith_key() {
  mde_load_secrets
  [[ -n "${LANGSMITH_API_KEY:-}" ]]
}

langsmith_api_ping() {
  if [[ "$LANGSMITH_PING" != "1" ]]; then
    log "LangSmith API ping skipped (MDE_LANGSMITH_PING=0)."
    return 0
  fi

  if ! mde_have_cmd curl; then
    log "missing command: curl (LangSmith ping skipped)"
    return 1
  fi

  local api_key=""
  api_key="${LANGSMITH_API_KEY:-}"

  if [[ -z "$api_key" ]]; then
    log "missing LANGSMITH_API_KEY (LangSmith ping failed)"
    return 1
  fi

  local workspace_id="${LANGSMITH_WORKSPACE_ID:-${LANGCHAIN_WORKSPACE_ID:-}}"

  local endpoint="${LANGSMITH_ENDPOINT%/}"
  local url="${endpoint}/datasets?limit=1"
  local code=""
  local header_args=("-H" "x-api-key: ${api_key}")

  if [[ -n "$workspace_id" ]]; then
    header_args+=("-H" "X-Tenant-Id: ${workspace_id}")
  fi

  code="$(curl -s -o /dev/null -w "%{http_code}" "${header_args[@]}" "$url" || true)"

  case "$code" in
    200)
      log "ok: LangSmith API key validated"
      return 0
      ;;
    401|403)
      if [[ -z "$workspace_id" ]]; then
        log "LangSmith API key rejected (HTTP $code). Set LANGSMITH_WORKSPACE_ID for service keys."
      else
        log "LangSmith API key rejected (HTTP $code)"
      fi
      return 1
      ;;
    000|"" )
      log "LangSmith API ping failed (network error)"
      return 1
      ;;
    *)
      log "LangSmith API ping unexpected status: $code"
      return 1
      ;;
  esac
}

smoke_command() {
  local cmd="$1"
  local args="$2"
  local failures_ref="$3"
  local severity="${4:-hard}"

  if ! mde_have_cmd "$cmd"; then
    log "missing command: $cmd"
    eval "$failures_ref=1"
    return 1
  fi

  if [[ "$cmd" == "deepacp" && "$SMOKE_STRICT" != "1" ]]; then
    if [[ ! -t 1 ]]; then
      log "skip: $cmd (no TTY; set MDE_LANGCHAIN_SMOKE_STRICT=1 to force)"
      return 0
    fi
  fi

  if [[ "$SMOKE_MODE" != "1" ]]; then
    log "ok: command $cmd"
    return 0
  fi

  local arg_list=()
  if [[ -n "$args" ]]; then
    IFS=' ' read -r -a arg_list <<< "$args"
  fi

  if run_with_timeout "$SMOKE_TIMEOUT" "$cmd" "${arg_list[@]}" >/dev/null 2>&1; then
    log "ok: smoke $cmd"
    return 0
  fi

  local status=$?
  local prefix="failed"
  if [[ "$severity" == "soft" ]]; then
    prefix="warn"
  fi

  if [[ "$status" == "124" ]]; then
    log "${prefix}: timeout $cmd"
    if [[ "$severity" == "soft" ]]; then
      return 0
    fi
  else
    log "${prefix}: $cmd"
    if [[ "$severity" == "soft" ]]; then
      return 0
    fi
  fi

  eval "$failures_ref=1"
  return 1
}

main() {
  setup_path

  if ! require_cmd uv; then
    log "LangChain tool verification skipped (uv missing)."
    return 1
  fi

  INSTALLED_TOOLS="$(uv_installed_tools)"

  local failures=0
  local tools=(
    langchain-cli
    langchain-model-profiles
    langgraph-cli
    langgraph-gen
    langsmith-fetch
    langsmith-data-migration-tool
    langsmith-mcp-server
    mcpdoc
    deepagents-cli
    pylon-data-extractor
  )

  local optional_tools=(
    langgraph-engineer
  )

  local internal_tools=(
    langc
    docs-monorepo
    langchain-plugin
    learning-langchain
    mcp-simple-streamablehttp-stateless
  )

  if [[ "$INCLUDE_INTERNAL" == "1" ]]; then
    optional_tools+=("${internal_tools[@]}")
  fi

  for tool in "${tools[@]}"; do
    if tool_present "$tool"; then
      log "ok: uv tool $tool"
    else
      log "missing uv tool: $tool"
      failures=1
    fi
  done

  for tool in "${optional_tools[@]}"; do
    if tool_present "$tool"; then
      log "ok: optional uv tool $tool"
    else
      log "warn: missing optional uv tool: $tool"
    fi
  done

  for wrapper in langsmith-fetch langsmith-migrator langsmith-mcp-server; do
    if [[ -x "$HOME/.local/bin/$wrapper" ]]; then
      log "ok: wrapper $wrapper"
    else
      log "missing wrapper: $wrapper"
      failures=1
    fi
  done

  local command_checks=(
    "langchain|--help|soft"
    "langchain-cli|--help"
    "langchain-profiles|--help"
    "langgraph|--help"
    "langgraph-gen|--help"
    "langgraph-engineer|--help|soft"
    "langsmith-fetch|--help"
    "langsmith-migrator|--help|soft"
    "langsmith-mcp-server|--help"
    "mcpdoc|--help"
    "deepagents|help"
    "deepagents-cli|help"
    "pylon-extract|--help"
    "docs|--help|soft"
    "langgraph-dev|--help|soft"
    "mcp-simple-streamablehttp-stateless|--help|soft"
  )

  for entry in "${command_checks[@]}"; do
    local cmd=""
    local args=""
    local severity="hard"
    IFS='|' read -r cmd args severity <<< "$entry"
    smoke_command "$cmd" "$args" failures "$severity"
  done

  if ! langsmith_api_ping; then
    failures=1
  fi

  if [[ "$failures" -ne 0 ]]; then
    log "LangChain tool verification FAILED."
    return 1
  fi

  log "LangChain tool verification PASSED."
}

main "$@"
