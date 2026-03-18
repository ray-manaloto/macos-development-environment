#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

main() {
  setup_path
  mde_load_secrets

  local endpoint="${OPENLIT_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT:-}}"
  local required="${MDE_OPENLIT_REQUIRED:-0}"
  local check="${MDE_OPENLIT_CHECK:-0}"

  if [[ -z "$endpoint" ]]; then
    if [[ "$required" == "1" ]]; then
      log "missing: OpenLIT endpoint (set OPENLIT_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT)"
      exit 1
    fi
    log "OpenLIT not configured (endpoint missing)."
    exit 0
  fi

  log "ok: OpenLIT endpoint set"

  if [[ "$check" == "1" ]]; then
    if command -v curl >/dev/null 2>&1; then
      if curl -s --max-time 3 "$endpoint" >/dev/null 2>&1; then
        log "ok: OpenLIT endpoint reachable"
      else
        log "warn: OpenLIT endpoint not reachable"
      fi
    else
      log "warn: curl not available to check OpenLIT endpoint"
    fi
  fi
}

main "$@"
