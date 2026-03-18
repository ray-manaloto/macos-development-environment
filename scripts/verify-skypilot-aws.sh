#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

status=0
setup_path

# Check AWS credentials file exists
if [[ -f "$HOME/.aws/credentials" ]]; then
  log "AWS credentials file: present"
else
  log "AWS credentials file: MISSING"
  status=1
fi

# Check AWS config file exists
if [[ -f "$HOME/.aws/config" ]]; then
  log "AWS config file: present"
else
  log "AWS config file: MISSING"
  status=1
fi

# Check sky CLI present
if command -v sky >/dev/null 2>&1; then
  log "SkyPilot CLI: present ($(sky --version 2>/dev/null || echo unknown))"
  # sky check is read-only (validates credentials, does not write)
  if sky check aws 2>/dev/null; then
    log "SkyPilot AWS check: passed"
  else
    log "SkyPilot AWS check: failed"
    status=1
  fi
else
  log "SkyPilot CLI: not found"
  status=1
fi

exit "$status"
