#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

bun_claude="$HOME/.bun/bin/claude"
if [[ -e "$bun_claude" ]]; then
  rm -f "$bun_claude"
  log "Removed bun-provided claude binary (use MDE wrapper)."
fi

aqua_claude="$HOME/.local/share/mise/installs/aqua-anthropics-claude-code"
if [[ -d "$aqua_claude" ]]; then
  rm -rf "$aqua_claude"
  log "Removed stale aqua-managed Claude Code (now using native installer)."
fi
