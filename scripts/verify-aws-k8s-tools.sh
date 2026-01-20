#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

check_cmd() {
  local cmd="$1"
  local required="$2"

  if command -v "$cmd" >/dev/null 2>&1; then
    log "ok: $cmd"
    return 0
  fi

  if [[ "$required" == "1" ]]; then
    log "missing: $cmd"
    return 1
  fi

  log "optional missing: $cmd"
  return 0
}

setup_path

failures=0

for cmd in aws kubectl helm; do
  if ! check_cmd "$cmd" 1; then
    failures=1
  fi
done

for cmd in eksctl k9s kubectx kubens stern session-manager-plugin; do
  check_cmd "$cmd" 0 || true
  done

if [[ "$failures" -ne 0 ]]; then
  log "AWS/Kubernetes tool verification FAILED."
  exit 1
fi

log "AWS/Kubernetes tool verification PASSED."
