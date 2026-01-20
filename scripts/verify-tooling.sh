#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_status=0

if [[ -x "$SCRIPT_DIR/verify-agent-tools.sh" ]]; then
  log "Running agent tool verification."
  if ! "$SCRIPT_DIR/verify-agent-tools.sh"; then
    run_status=1
  fi
else
  log "Agent tool verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-langchain-tools.sh" ]]; then
  log "Running LangChain tool verification."
  if ! "$SCRIPT_DIR/verify-langchain-tools.sh"; then
    run_status=1
  fi
else
  log "LangChain tool verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-ai-research-skills.sh" ]]; then
  log "Running AI research skills verification."
  if ! "$SCRIPT_DIR/verify-ai-research-skills.sh"; then
    run_status=1
  fi
else
  log "AI research skills verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/setup-skypilot-aws.sh" ]]; then
  log "Running SkyPilot AWS verification."
  if ! "$SCRIPT_DIR/setup-skypilot-aws.sh"; then
    run_status=1
  fi
else
  log "SkyPilot setup script missing."
  run_status=1
fi

if [[ "$run_status" -eq 0 ]]; then
  log "Tooling verification PASSED."
  exit 0
fi

log "Tooling verification FAILED."
exit 1
