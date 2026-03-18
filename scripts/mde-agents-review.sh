#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if [[ -x "$REPO_ROOT/scripts/run-multi-agent.sh" ]]; then
  exec "$REPO_ROOT/scripts/run-multi-agent.sh" "$@"
fi

log "Agent review orchestrator not found at scripts/run-multi-agent.sh"
log "Usage: mde-agents-review [review-target]"
exit 1
