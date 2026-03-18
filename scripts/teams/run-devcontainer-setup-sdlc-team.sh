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
DATE_STAMP="${DEVCONTAINER_SDLC_DATE:-$(date +%F)}"
OUT_DIR="${DEVCONTAINER_SDLC_OUT_DIR:-reports/devcontainer-sdlc}"
ARTIFACT_DIR="${DEVCONTAINER_SDLC_ARTIFACT_DIR:-.artifacts/devcontainer-sdlc}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$ARTIFACT_DIR"
export SDLC_TEAM_IN_PROGRESS=1

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  local output_file="$4"

  echo "[devcontainer-sdlc] running $id"
  "$RUNNER" "Subagent: $id
Date: $DATE_STAMP
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Requirements:
- Load 'skills/mde-agent-runtime-contract' before task work.
- Use real implementation evidence; no stubs/mocks.
- Write all required outputs before finishing.
- Keep output decision-complete and directly actionable.
- Include adopted vs rejected guidance from rio/dotfiles and samhvw8/dotfiles when relevant to the role.
- Include actual devcontainer smoke evidence; do not describe unrun commands as completed.
- Record explicit sign-off language for architecture, QA, security, and devops deliverables.
- Do not invoke scripts/teams/run-devcontainer-setup-sdlc-team.sh from inside subagent execution.
"
}

run_subagent "sdlc-product-manager" "Define scope and measurable acceptance outcomes" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-product-manager.md" "$OUT_DIR/${DATE_STAMP}-01-product-requirements.md"
run_subagent "sdlc-architect" "Define architecture and technical decisions" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-architect.md" "$OUT_DIR/${DATE_STAMP}-02-architecture-design.md"
run_subagent "sdlc-implementation" "Create executable implementation plan" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-implementation.md" "$OUT_DIR/${DATE_STAMP}-03-implementation-plan.md"

run_subagent "sdlc-functional-qa" "Validate functional acceptance criteria" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-functional-qa.md" "$OUT_DIR/${DATE_STAMP}-04-functional-qa.md" &
pid_a=$!
run_subagent "sdlc-nonfunctional-qa" "Validate non-functional robustness" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-nonfunctional-qa.md" "$OUT_DIR/${DATE_STAMP}-05-nonfunctional-qa.md" &
pid_b=$!
run_subagent "sdlc-security" "Validate security and policy controls" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-security.md" "$OUT_DIR/${DATE_STAMP}-06-security-review.md" &
pid_c=$!
wait "$pid_a"
wait "$pid_b"
wait "$pid_c"

run_subagent "sdlc-devops" "Define CI/CD and release runbook" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-devops.md" "$OUT_DIR/${DATE_STAMP}-07-devops-release.md"
run_subagent "sdlc-docs" "Publish final handoff docs" "prompts/agent-team/devcontainer-setup-sdlc/sdlc-docs.md" "$OUT_DIR/${DATE_STAMP}-08-docs-handoff.md"

VALIDATOR="${DEVCONTAINER_SDLC_VALIDATOR:-scripts/teams/validate-devcontainer-setup-sdlc-output.sh}"
echo "[devcontainer-sdlc] validating outputs with $VALIDATOR"
"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR"

echo "[devcontainer-sdlc] complete"
echo "outputs: $OUT_DIR"
