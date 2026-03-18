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
DATE_STAMP="${MDE_AUTORESEARCH_DATE:-$(date +%F)}"
OUT_DIR="${MDE_AUTORESEARCH_OUT_DIR:-reports/mde-autoresearch}"
VALIDATOR="${MDE_AUTORESEARCH_VALIDATOR:-$REPO_ROOT/scripts/teams/validate-mde-autoresearch-output.sh}"
MODE="${MDE_AUTORESEARCH_MODE:-incremental}"

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$REPO_ROOT/.artifacts/mde-autoresearch"

DOMAIN_HINT="${MDE_AUTORESEARCH_DOMAIN_HINT:-mde:research:autoimprove ${MDE_AUTORESEARCH_SCOPE:-host setup tooling automation}}"
DOMAIN="${MDE_ACTIVE_DOMAIN:-${MDE_DOMAIN:-$($REPO_ROOT/scripts/mde-domain-classify.sh "$DOMAIN_HINT")}}"
export MDE_ACTIVE_DOMAIN="$DOMAIN"
"$REPO_ROOT/scripts/teams/run-mde-domain-team.sh" --domain "$DOMAIN" --trigger "mde:research:autoimprove"

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  shift 3
  local outputs=("$@")
  local task

  task="Team: mde-autoresearch-team
Subagent: $id
Date: $DATE_STAMP
Domain: $DOMAIN
Objective: $objective
Prompt template: $prompt_file
Mode: $MODE
Requirements:
- Use domain classification against configs/mde-domain-catalog.json before proposing repo-wide setup or tooling changes.
- delegate domain authority work through scripts/teams/run-mde-domain-team.sh before finalizing repo-wide decisions.
- Delegate domain-owned adoption, remediation, and starter-bundle decisions to scripts/teams/run-mde-domain-team.sh and the reports/mde-domain-sdlc/$DOMAIN baseline before synthesis or guidance updates are accepted.
- Read configs/mde-reference-sources.json, configs/mde-preset-catalog.json, and configs/mde-learning-registry.json alongside the runtime contract sources.
- Keep the run bounded, evidence-backed, and tied to the active domain baseline.
- Do not use unmanaged global install commands.
- Write all declared output files before finishing.
"

  for output_file in "${outputs[@]}"; do
    task+="Output file: $output_file
"
  done

  "$RUNNER" "$task"
}

run_subagent \
  "scout-agent" \
  "Discover candidate sources and upstream repos for mode=$MODE" \
  "prompts/agent-team/mde-autoresearch/scout-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-01-scout.md" \
  "$OUT_DIR/${DATE_STAMP}-discovery-records.jsonl"
run_subagent \
  "repo-mining-agent" \
  "Mine shortlisted repositories for portable implementation patterns" \
  "prompts/agent-team/mde-autoresearch/repo-mining-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-02-repo-mining.md" \
  "$OUT_DIR/${DATE_STAMP}-pattern-records.jsonl"
run_subagent \
  "docs-tutorial-agent" \
  "Extract practical lessons from tutorials, docs, release notes, and blogs" \
  "prompts/agent-team/mde-autoresearch/docs-tutorial-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-03-docs-tutorials.md"
run_subagent \
  "social-signal-agent" \
  "Mine social and discussion sources for grounded implementation signals" \
  "prompts/agent-team/mde-autoresearch/social-signal-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-04-social-signals.md" \
  "$OUT_DIR/${DATE_STAMP}-social-pattern-records.jsonl"
run_subagent \
  "tooling-eval-agent" \
  "Score adopt/adapt/reject decisions for discovered tools and patterns" \
  "prompts/agent-team/mde-autoresearch/tooling-eval-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-05-tooling-eval.md"
run_subagent \
  "tool-ownership-agent" \
  "Classify discovered tools into ownership buckets" \
  "prompts/agent-team/mde-autoresearch/tool-ownership-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-06-tool-ownership.md"
run_subagent \
  "runner-enforcement-agent" \
  "Assess contract coverage across runners, prompts, and automation surfaces" \
  "prompts/agent-team/mde-autoresearch/runner-enforcement-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-07-runner-enforcement.md"
run_subagent \
  "migration-agent" \
  "Translate accepted ownership decisions into migration candidates" \
  "prompts/agent-team/mde-autoresearch/migration-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-08-migration.md"
run_subagent \
  "validation-agent" \
  "Define acceptance criteria and proof commands for accepted changes" \
  "prompts/agent-team/mde-autoresearch/validation-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-09-validation.md" \
  "$OUT_DIR/${DATE_STAMP}-acceptance-records.jsonl"
run_subagent \
  "synthesis-agent" \
  "Write final decisions and the bounded implementation summary" \
  "prompts/agent-team/mde-autoresearch/synthesis-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-10-synthesis.md" \
  "$OUT_DIR/${DATE_STAMP}-decision-records.jsonl" \
  "$OUT_DIR/${DATE_STAMP}-summary.md"
run_subagent \
  "telemetry-agent" \
  "Assess telemetry and provenance coverage for this run" \
  "prompts/agent-team/mde-autoresearch/telemetry-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-11-telemetry.md"
run_subagent \
  "guidance-consolidator-agent" \
  "Consolidate accepted guidance updates for AGENTS and skills" \
  "prompts/agent-team/mde-autoresearch/guidance-consolidator-agent.md" \
  "$OUT_DIR/${DATE_STAMP}-12-guidance.md"

"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR" "$DOMAIN"
