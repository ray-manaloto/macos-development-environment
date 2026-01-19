#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

check_secret() {
  local label="$1"
  local env_var="$2"

  if [[ -n "${!env_var:-}" ]]; then
    log "secret ok (env): $env_var"
    return 0
  fi

  if have_cmd security; then
    if security find-generic-password -s "$label" -w >/dev/null 2>&1; then
      log "secret ok (keychain): $label"
      return 0
    fi
  fi

  log "secret missing: $env_var ($label)"
  return 1
}

main() {
  local failures=0

  check_secret "mde-github-token" GITHUB_TOKEN || failures=1
  check_secret "mde-openai-api-key" OPENAI_API_KEY || failures=1
  check_secret "mde-anthropic-api-key" ANTHROPIC_API_KEY || failures=1
  check_secret "mde-langsmith-api-key" LANGSMITH_API_KEY || failures=1

  if [[ "$failures" -ne 0 ]]; then
    return 1
  fi
}

main "$@"
