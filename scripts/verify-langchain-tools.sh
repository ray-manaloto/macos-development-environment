#!/usr/bin/env bash
set -euo pipefail

INCLUDE_INTERNAL="${INCLUDE_INTERNAL:-1}"
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

  if [[ "$failures" -ne 0 ]]; then
    log "LangChain tool verification FAILED."
    return 1
  fi

  log "LangChain tool verification PASSED."
}

main "$@"
