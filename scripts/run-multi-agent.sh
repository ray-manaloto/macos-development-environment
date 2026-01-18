#!/usr/bin/env bash
set -euo pipefail

RUNNER="${MULTI_AGENT_RUNNER:-}"
EXTRA_ARGS="${MULTI_AGENT_RUNNER_ARGS:-}"

if [[ -z "$RUNNER" ]]; then
  echo "MULTI_AGENT_RUNNER is not set. See docs/multi-agent-runner.md" >&2
  exit 1
fi

run_task() {
  local task="$1"
  $RUNNER $EXTRA_ARGS "$task"
}

run_task "Review the macOS dev environment repo for correctness and risks."
run_task "Run QA validation for scripts and document any failures."
run_task "Ensure docs are consistent with scripts and repo layout."
