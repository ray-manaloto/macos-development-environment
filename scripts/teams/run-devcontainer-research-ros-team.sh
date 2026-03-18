#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$REPO_ROOT/scripts/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
"$REPO_ROOT/scripts/mde-agent-preflight.sh" --quiet >/dev/null
export MDE_AGENT_PREFLIGHT_PASSED=1
export MDE_AGENT_CONTEXT=1
mde_prepare_guard_dir >/dev/null

RUNNER="${MULTI_AGENT_RUNNER:-$REPO_ROOT/scripts/agent-runner.sh}"
DATE_STAMP="${ROS_TEAM_DATE:-$(date +%F)}"
OUT_DIR="${ROS_TEAM_OUT_DIR:-reports/research-ros}"
ARTIFACT_DIR="${ROS_TEAM_ARTIFACT_DIR:-.artifacts/research-ros}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  echo "Set MULTI_AGENT_RUNNER to a valid executable runner. See docs/multi-agent-runner.md" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$ARTIFACT_DIR"

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  local output_file="$4"

  echo "[research-ros] running $id"
  "$RUNNER" "Subagent: $id
Date: $DATE_STAMP
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Requirements:
- Load `skills/mde-agent-runtime-contract` before task work.
- Activate and use required skills before task work.
- Use source-priority stack and query rules from docs/research/devcontainer-ros-workflow.md.
- Write outputs to the requested file paths.
- Keep outputs concise, evidence-backed, and decision-complete.
"
}

run_subagent \
  "scout-agent" \
  "Generate candidate source pool with query logs and discovery records" \
  "prompts/agent-team/devcontainer-research-ros/scout-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-phase-a-candidates.md"

run_subagent \
  "repo-mining-agent" \
  "Mine shortlisted repositories and extract scored patterns" \
  "prompts/agent-team/devcontainer-research-ros/repo-mining-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-phase-b-repo-mining.md"

run_subagent \
  "social-signal-agent" \
  "Mine social/blog sources for implementation lessons" \
  "prompts/agent-team/devcontainer-research-ros/social-signal-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-phase-c-social-signals.md"

run_subagent \
  "validation-agent" \
  "Map patterns to local acceptance contract" \
  "prompts/agent-team/devcontainer-research-ros/validation-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-phase-d-validation-mapping.md"

run_subagent \
  "synthesis-agent" \
  "Produce decision records, research bundle, and final spec" \
  "prompts/agent-team/devcontainer-research-ros/synthesis-agent.md" \
  "docs/plans/${DATE_STAMP}-devcontainer-research-ros-spec.md"

VALIDATOR="${ROS_TEAM_VALIDATOR:-scripts/teams/validate-devcontainer-research-ros-output.sh}"
echo "[research-ros] validating outputs with $VALIDATOR"
"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR"

echo "[research-ros] complete"
echo "outputs: $OUT_DIR"
echo "artifacts: $ARTIFACT_DIR"
