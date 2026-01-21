#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

load_env_file_secrets() {
  local env_file="${MDE_ENV_FILE:-$HOME/.config/macos-development-environment/secrets.env}"
  local override="${MDE_ENV_OVERRIDE:-1}"
  local line key value

  if [[ "${MDE_ENV_AUTOLOAD:-1}" != "1" ]]; then
    return 0
  fi

  if [[ ! -f "$env_file" ]]; then
    return 0
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    [[ "$line" == \#* ]] && continue
    line="${line#export }"
    key="${line%%=*}"
    value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    key="${key#"${key%%[![:space:]]*}"}"
    [[ -z "$key" ]] && continue
    if [[ "$override" != "1" && -n "${!key:-}" ]]; then
      continue
    fi
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value#\"}"
      value="${value%\"}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value#\'}"
      value="${value%\'}"
    fi
    export "$key"="$value"
  done < "$env_file"
}

main() {
  setup_path
  load_env_file_secrets

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
