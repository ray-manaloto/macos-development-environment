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
PARALLEL_QA="${OCTOKIT_TEAM_PARALLEL_QA:-1}"
DATE_STAMP="${OCTOKIT_TEAM_DATE:-$(date +%F)}"
OUT_DIR="${OCTOKIT_TEAM_OUT_DIR:-reports/octokit-sdlc}"
ARTIFACT_DIR="${OCTOKIT_TEAM_ARTIFACT_DIR:-.artifacts/octokit-sdlc}"

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

  echo "[octokit-sdlc] running $id"
  "$RUNNER" "Subagent: $id
Date: $DATE_STAMP
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Requirements:
- Load `skills/mde-agent-runtime-contract` before task work.
- Activate and use relevant skills/plugins before doing task work.
- If required skills are missing, add/install them, then continue.
- Write results to the requested output file path.
- Keep output concise and decision-complete.
"
}

run_subagent \
  "spec-planner" \
  "Create implementation-ready spec and task plan" \
  "prompts/agent-team/octokit-sdlc/spec-planner.md" \
  "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-plan.md"

run_subagent \
  "spec-reviewer" \
  "Review spec/plan and return findings + approval status" \
  "prompts/agent-team/octokit-sdlc/spec-reviewer.md" \
  "docs/plans/${DATE_STAMP}-octokit-sdlc-spec-review.md"

run_subagent \
  "bdd-test-designer" \
  "Create BDD tests from approved plan" \
  "prompts/agent-team/octokit-sdlc/bdd-test-designer.md" \
  "docs/plans/${DATE_STAMP}-octokit-sdlc-test-design.md"

run_subagent \
  "coding-agent" \
  "Execute approved plan to pass BDD tests" \
  "prompts/agent-team/octokit-sdlc/coding-agent.md" \
  "$OUT_DIR/coding-agent.log"

if [[ "$PARALLEL_QA" == "1" ]]; then
  run_subagent \
    "qa-functional" \
    "Validate CLI/library behavior" \
    "prompts/agent-team/octokit-sdlc/qa-functional.md" \
    "$OUT_DIR/qa-functional.md" &
  pid_a=$!

  run_subagent \
    "qa-nonfunctional" \
    "Validate reliability, metadata, and security" \
    "prompts/agent-team/octokit-sdlc/qa-nonfunctional.md" \
    "$OUT_DIR/qa-nonfunctional.md" &
  pid_b=$!

  wait "$pid_a"
  wait "$pid_b"
else
  run_subagent \
    "qa-functional" \
    "Validate CLI/library behavior" \
    "prompts/agent-team/octokit-sdlc/qa-functional.md" \
    "$OUT_DIR/qa-functional.md"

  run_subagent \
    "qa-nonfunctional" \
    "Validate reliability, metadata, and security" \
    "prompts/agent-team/octokit-sdlc/qa-nonfunctional.md" \
    "$OUT_DIR/qa-nonfunctional.md"
fi

run_subagent \
  "docs-agent" \
  "Create final human+AI-friendly docs and usage guidance" \
  "prompts/agent-team/octokit-sdlc/docs-agent.md" \
  "$OUT_DIR/docs-validation.md"

VALIDATOR="${OCTOKIT_TEAM_VALIDATOR:-scripts/teams/validate-octokit-sdlc-output.sh}"
echo "[octokit-sdlc] validating outputs with $VALIDATOR"
"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR"

echo "[octokit-sdlc] complete"
echo "outputs: $OUT_DIR"
echo "artifacts: $ARTIFACT_DIR"
