#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

run_status=0

setup_path

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

if [[ -x "$SCRIPT_DIR/verify-skypilot-aws.sh" ]]; then
  log "Running SkyPilot AWS verification."
  if ! "$SCRIPT_DIR/verify-skypilot-aws.sh"; then
    run_status=1
  fi
else
  log "SkyPilot AWS verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/sky-status.sh" ]]; then
  log "Running SkyPilot status check."
  if ! "$SCRIPT_DIR/sky-status.sh" --no-aws --strict; then
    run_status=1
  fi
else
  log "SkyPilot status script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-aws-k8s-tools.sh" ]]; then
  log "Running AWS/Kubernetes tool verification."
  if ! "$SCRIPT_DIR/verify-aws-k8s-tools.sh"; then
    run_status=1
  fi
else
  log "AWS/Kubernetes verification script missing."
  run_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-openlit.sh" ]]; then
  log "Running OpenLIT verification."
  if ! "$SCRIPT_DIR/verify-openlit.sh"; then
    run_status=1
  fi
else
  log "OpenLIT verification script missing."
  run_status=1
fi

if [[ "$run_status" -eq 0 ]]; then
  log "Tooling verification PASSED."
  exit 0
fi

log "Tooling verification FAILED."
exit 1
