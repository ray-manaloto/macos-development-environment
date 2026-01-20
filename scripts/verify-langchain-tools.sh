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

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

uv_installed_tools() {
  uv tool list 2>/dev/null | awk 'NF && $1 !~ /^-/{print $1}'
}

tool_present() {
  local name="$1"
  if have_cmd rg; then
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

load_op_secret() {
  local ref_var="$1"
  local env_var="$2"
  local ref=""
  local token=""
  local value=""

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
  local value=""

  if [[ -n "${!env_var:-}" || ! $(command -v security 2>/dev/null) ]]; then
    return 0
  fi

  value="$(security find-generic-password -s "$label" -w 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf -v "$env_var" '%s' "$value"
    export "$env_var"
  fi
}

ensure_langsmith_key() {
  if [[ -n "${LANGSMITH_API_KEY:-}" ]]; then
    return 0
  fi
  load_op_secret MDE_OP_LANGSMITH_API_KEY_REF LANGSMITH_API_KEY
  load_keychain_secret "mde-langsmith-api-key" LANGSMITH_API_KEY
  [[ -n "${LANGSMITH_API_KEY:-}" ]]
}

langsmith_api_ping() {
  if [[ "$LANGSMITH_PING" != "1" ]]; then
    log "LangSmith API ping skipped (MDE_LANGSMITH_PING=0)."
    return 0
  fi

  if ! have_cmd curl; then
    log "missing command: curl (LangSmith ping skipped)"
    return 1
  fi

  local api_key=""
  if have_cmd security; then
    api_key="$(security find-generic-password -s mde-langsmith-api-key -w 2>/dev/null || true)"
  fi

  if [[ -z "$api_key" ]]; then
    api_key="${LANGSMITH_API_KEY:-}"
  fi

  if [[ -z "$api_key" ]]; then
    load_op_secret MDE_OP_LANGSMITH_API_KEY_REF LANGSMITH_API_KEY
    api_key="${LANGSMITH_API_KEY:-}"
  fi

  if [[ -z "$api_key" ]]; then
    log "missing LANGSMITH_API_KEY (LangSmith ping failed)"
    return 1
  fi

  local workspace_id="${LANGSMITH_WORKSPACE_ID:-${LANGCHAIN_WORKSPACE_ID:-}}"
  if [[ -z "$workspace_id" ]] && have_cmd security; then
    workspace_id="$(security find-generic-password -s mde-langsmith-workspace-id -w 2>/dev/null || true)"
  fi

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

  if ! have_cmd "$cmd"; then
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
  if [[ "$status" == "124" ]]; then
    log "timeout: $cmd"
  else
    log "failed: $cmd"
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
    langgraph-engineer
    langsmith-fetch
    langsmith-data-migration-tool
    langsmith-mcp-server
    mcpdoc
    deepagents-cli
    deepagents-acp
    pylon-data-extractor
  )

  local internal_tools=(
    langc
    docs-monorepo
    langchain-plugin
    learning-langchain
    mcp-simple-streamablehttp-stateless
  )

  if [[ "$INCLUDE_INTERNAL" == "1" ]]; then
    tools+=("${internal_tools[@]}")
  fi

  for tool in "${tools[@]}"; do
    if tool_present "$tool"; then
      log "ok: uv tool $tool"
    else
      log "missing uv tool: $tool"
      failures=1
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
    "langchain|--help"
    "langchain-cli|--help"
    "langchain-profiles|--help"
    "langgraph|--help"
    "langgraph-gen|--help"
    "langgraph-engineer|--help"
    "langsmith-fetch|--help"
    "langsmith-migrator|--help"
    "langsmith-mcp-server|--help"
    "mcpdoc|--help"
    "deepagents|help"
    "deepagents-cli|help"
    "pylon-extract|--help"
    "docs|--help"
    "langgraph-dev|--help"
    "mcp-simple-streamablehttp-stateless|--help"
  )

  for entry in "${command_checks[@]}"; do
    local cmd=""
    local args=""
    IFS='|' read -r cmd args <<< "$entry"
    smoke_command "$cmd" "$args" failures
  done

  smoke_import "deepagents-acp" "deepagents_acp.server" failures

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
