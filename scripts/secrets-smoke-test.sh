#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

check_secret() {
  local env_var="$1"

  if [[ -n "${!env_var:-}" ]]; then
    log "secret ok (env): $env_var"
    return 0
  fi

  log "secret missing: $env_var"
  return 1
}

main() {
  local failures=0
  mde_load_secrets

  check_secret GITHUB_TOKEN || failures=1
  check_secret OPENAI_API_KEY || failures=1
  check_secret ANTHROPIC_API_KEY || failures=1
  check_secret LANGSMITH_API_KEY || failures=1
  check_secret GEMINI_API_KEY || failures=1

  if [[ "$failures" -ne 0 ]]; then
    return 1
  fi
}

main "$@"
