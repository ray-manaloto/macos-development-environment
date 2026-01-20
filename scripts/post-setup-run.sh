#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
SUMMARY_LOG="$LOG_DIR/post-setup-summary.log"
RUN_LOG="$LOG_DIR/post-setup-run.log"
WRAPPER="$HOME/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

mkdir -p "$LOG_DIR"

log "Post-setup run starting." | tee -a "$SUMMARY_LOG"
log "Run log: $RUN_LOG" | tee -a "$SUMMARY_LOG"

run_status=0
if [[ -x "$WRAPPER" ]]; then
  "$WRAPPER" >"$RUN_LOG" 2>&1 || run_status=$?
else
  if [[ -x "$SCRIPT_DIR/macos-dev-maintenance.sh" ]]; then
    "$SCRIPT_DIR/macos-dev-maintenance.sh" >"$RUN_LOG" 2>&1 || run_status=$?
  else
    log "Maintenance script not found." | tee -a "$SUMMARY_LOG"
    run_status=1
  fi
fi

if [[ "$run_status" -eq 0 ]]; then
  log "Maintenance run OK." | tee -a "$SUMMARY_LOG"
else
  log "Maintenance run FAILED (exit $run_status)." | tee -a "$SUMMARY_LOG"
fi

health_status=0
tmux_status=0
tooling_status=0
if [[ -x "$SCRIPT_DIR/health-check.sh" ]]; then
  log "Running health check." | tee -a "$SUMMARY_LOG"
  if ! "$SCRIPT_DIR/health-check.sh" | tee -a "$SUMMARY_LOG"; then
    health_status=1
  fi
else
  log "Health check script missing." | tee -a "$SUMMARY_LOG"
  health_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-tmux-setup.sh" ]]; then
  log "Running tmux verification." | tee -a "$SUMMARY_LOG"
  if ! "$SCRIPT_DIR/verify-tmux-setup.sh" | tee -a "$SUMMARY_LOG"; then
    tmux_status=1
  fi
else
  log "Tmux verification script missing." | tee -a "$SUMMARY_LOG"
  tmux_status=1
fi

if [[ -x "$SCRIPT_DIR/verify-tooling.sh" ]]; then
  log "Running tooling verification." | tee -a "$SUMMARY_LOG"
  if ! "$SCRIPT_DIR/verify-tooling.sh" | tee -a "$SUMMARY_LOG"; then
    tooling_status=1
  fi
else
  log "Tooling verification script missing." | tee -a "$SUMMARY_LOG"
  tooling_status=1
fi

if [[ "$run_status" -eq 0 && "$health_status" -eq 0 && "$tmux_status" -eq 0 && "$tooling_status" -eq 0 ]]; then
  log "Post-setup summary: PASS" | tee -a "$SUMMARY_LOG"
  exit 0
fi

log "Post-setup summary: FAIL" | tee -a "$SUMMARY_LOG"
exit 1
