#!/usr/bin/env bash
set -euo pipefail

RUNNER="${MULTI_AGENT_RUNNER:-}"
EXTRA_ARGS=()
PARALLEL="${MULTI_AGENT_PARALLEL:-0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
"$REPO_ROOT/scripts/mde-agent-preflight.sh" --quiet >/dev/null
export MDE_AGENT_PREFLIGHT_PASSED=1
export MDE_AGENT_CONTEXT=1
mde_prepare_guard_dir >/dev/null

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
