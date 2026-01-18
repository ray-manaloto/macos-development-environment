#!/usr/bin/env bash
set -euo pipefail

RUNNER="${MULTI_AGENT_RUNNER:-}"
EXTRA_ARGS=()
PARALLEL="${MULTI_AGENT_PARALLEL:-0}"

if [[ -z "$RUNNER" ]]; then
  echo "MULTI_AGENT_RUNNER is not set. See docs/multi-agent-runner.md" >&2
  exit 1
fi

if [[ -n "${MULTI_AGENT_RUNNER_ARGS:-}" ]]; then
  read -r -a EXTRA_ARGS <<< "$MULTI_AGENT_RUNNER_ARGS"
fi

run_task() {
  local task="$1"
  "$RUNNER" "${EXTRA_ARGS[@]}" "$task"
}

TASKS=(
  "Review the macOS dev environment repo for correctness and risks."
  "Run QA validation for scripts and document any failures."
  "Ensure docs are consistent with scripts and repo layout."
)

if [[ "$PARALLEL" == "1" ]]; then
  pids=()
  for task in "${TASKS[@]}"; do
    run_task "$task" &
    pids+=("$!")
  done

  failed=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed=1
    fi
  done
  exit "$failed"
fi

for task in "${TASKS[@]}"; do
  run_task "$task"
done
