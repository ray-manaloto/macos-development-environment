#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

bun_gemini="$HOME/.bun/bin/gemini"
if [[ -e "$bun_gemini" ]]; then
  rm -f "$bun_gemini"
  log "Removed bun-provided gemini binary (use MDE wrapper)."
fi
