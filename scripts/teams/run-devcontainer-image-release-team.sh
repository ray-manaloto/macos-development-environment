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
DATE_STAMP="${DEVCONTAINER_IMAGE_RELEASE_DATE:-$(date +%F)}"
OUT_DIR="${DEVCONTAINER_IMAGE_RELEASE_OUT_DIR:-reports/devcontainer-image-release}"
ARTIFACT_DIR="${DEVCONTAINER_IMAGE_RELEASE_ARTIFACT_DIR:-.artifacts/devcontainer-image-release}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$ARTIFACT_DIR"

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  local output_file="$4"

  echo "[devcontainer-image-release] running $id"
  "$RUNNER" "Subagent: $id
Date: $DATE_STAMP
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Requirements:
- Use real repository files and real execution evidence.
- Load `skills/mde-agent-runtime-contract` before task work.
- Do not invoke scripts/teams/run-devcontainer-image-release-team.sh from inside subagent execution.
- Do not use placeholder, stub, or mock content.
- Write all required output before finishing.
"
}

run_subagent "image-authoring-agent" "Define image authoring and base-image policy" "prompts/agent-team/devcontainer-image-release/image-authoring-agent.md" "$OUT_DIR/${DATE_STAMP}-01-image-authoring.md"

run_subagent "gha-publish-agent" "Define CI and GHCR publication workflow" "prompts/agent-team/devcontainer-image-release/gha-publish-agent.md" "$OUT_DIR/${DATE_STAMP}-02-gha-publish.md" &
pid_a=$!
run_subagent "dependency-bot-agent" "Define Dependabot update policy" "prompts/agent-team/devcontainer-image-release/dependency-bot-agent.md" "$OUT_DIR/${DATE_STAMP}-03-dependency-bot.md" &
pid_b=$!
wait "$pid_a"
wait "$pid_b"

run_subagent "validation-agent" "Validate build, smoke, and hard gates" "prompts/agent-team/devcontainer-image-release/validation-agent.md" "$OUT_DIR/${DATE_STAMP}-04-validation.md"
run_subagent "docs-agent" "Publish operator handoff" "prompts/agent-team/devcontainer-image-release/docs-agent.md" "$OUT_DIR/${DATE_STAMP}-05-docs-handoff.md"

VALIDATOR="${DEVCONTAINER_IMAGE_RELEASE_VALIDATOR:-scripts/teams/validate-devcontainer-image-release-output.sh}"
echo "[devcontainer-image-release] validating outputs with $VALIDATOR"
"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR"

echo "[devcontainer-image-release] complete"
echo "outputs: $OUT_DIR"
