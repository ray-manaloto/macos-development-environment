#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"
mkdir -p "$UV_CACHE_DIR" 2>/dev/null || true

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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

check_cmd() {
  local name="$1"
  if have_cmd "$name"; then
    log "ok: command $name"
    return 0
  fi
  log "missing command: $name"
  return 1
}

main() {
  setup_path
  local failures=0

  if ! have_cmd uv; then
    log "missing command: uv"
    failures=1
  else
    INSTALLED_TOOLS="$(uv_installed_tools)"
    for tool in aider-chat open-interpreter crewai; do
      if tool_present "$tool"; then
        log "ok: uv tool $tool"
      else
        log "missing uv tool: $tool"
        failures=1
      fi
    done
  fi

  for cmd in claude codex gemini openwork create-agent-chat-app mcp-inspector opencode; do
    if ! check_cmd "$cmd"; then
      failures=1
    fi
  done

  if [[ "$failures" -ne 0 ]]; then
    log "Agent tool verification FAILED."
    return 1
  fi

  log "Agent tool verification PASSED."
}

main "$@"
