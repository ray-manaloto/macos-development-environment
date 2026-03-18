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

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
  esac
done

RUNNER="${MULTI_AGENT_RUNNER:-$REPO_ROOT/scripts/agent-runner.sh}"
DATE_STAMP="${CLAUDE_FLOW_LEARNING_DATE:-$(date +%F)}"
OUT_DIR="${CLAUDE_FLOW_LEARNING_OUT_DIR:-reports/claude-flow-learning}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$REPO_ROOT/.artifacts/claude-flow-learning"

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  shift 3
  local outputs=("$@")
  local task

  task="Team: claude-flow-learning-team
Subagent: $id
Date: $DATE_STAMP
Objective: $objective
Prompt template: $prompt_file
Requirements:
- Use the claude-flow CLI for all memory and neural operations.
- Do not use unmanaged global install commands.
- Write all declared output files before finishing.
"

  for output_file in "${outputs[@]}"; do
    task+="Output file: $output_file
"
  done

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] Would run subagent: $id"
    echo "  Objective: $objective"
    echo "  Prompt: $prompt_file"
    for output_file in "${outputs[@]}"; do
      echo "  Output: $output_file"
    done
    echo ""
    return 0
  fi

  "$RUNNER" "$task"
}

# Stage 1
run_subagent \
  "learning-scout" \
  "Discover new patterns, tools, and approaches from cloned repos and online sources" \
  "prompts/agent-team/claude-flow-learning/learning-scout.md" \
  "$OUT_DIR/${DATE_STAMP}-01-scout-discovery.md" \
  "$OUT_DIR/${DATE_STAMP}-01-pattern-candidates.jsonl"

# Stage 2 (both run sequentially but logically parallel)
run_subagent \
  "memory-analyst" \
  "Analyze current memory DB contents, find gaps, duplicates, and stale patterns" \
  "prompts/agent-team/claude-flow-learning/memory-analyst.md" \
  "$OUT_DIR/${DATE_STAMP}-02-memory-analysis.md"
run_subagent \
  "framework-comparator" \
  "Compare claude-flow learning features against other agent frameworks" \
  "prompts/agent-team/claude-flow-learning/framework-comparator.md" \
  "$OUT_DIR/${DATE_STAMP}-02-framework-comparison.md"

# Stage 3
run_subagent \
  "pattern-synthesizer" \
  "Distill findings from stages 1-2 into actionable pattern records" \
  "prompts/agent-team/claude-flow-learning/pattern-synthesizer.md" \
  "$OUT_DIR/${DATE_STAMP}-03-synthesized-patterns.md" \
  "$OUT_DIR/${DATE_STAMP}-03-pattern-records.jsonl"

# Stage 4
run_subagent \
  "learning-optimizer" \
  "Apply improvements: store new patterns, prune stale ones, tune neural config" \
  "prompts/agent-team/claude-flow-learning/learning-optimizer.md" \
  "$OUT_DIR/${DATE_STAMP}-04-optimization-report.md" \
  "$OUT_DIR/${DATE_STAMP}-04-applied-changes.jsonl"

echo "==> Claude-flow learning team run complete: $OUT_DIR"
