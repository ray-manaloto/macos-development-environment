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
DATE_STAMP="${MDE_UPDATE_REMEDIATION_DATE:-$(date +%F)}"
OUT_DIR="${MDE_UPDATE_REMEDIATION_OUT_DIR:-reports/mde-update-remediation}"
ARTIFACT_DIR="${MDE_UPDATE_REMEDIATION_ARTIFACT_DIR:-.artifacts/mde-update-remediation}"
ITEM_ID_INPUT="${1:-${MDE_UPDATE_REMEDIATION_ITEM_ID:-mde:update}}"
EVIDENCE_INPUT="${2:-${MDE_UPDATE_REMEDIATION_EVIDENCE_PATH:-$REPO_ROOT/mde-update-results.20260213.log}}"
MAX_ATTEMPTS="${MDE_UPDATE_REMEDIATION_MAX_ATTEMPTS:-3}"
ERROR_REGEX='^error:|mise ERROR|ERROR task failed|Install completed with failures'

if [[ "$ITEM_ID_INPUT" = /* || "$ITEM_ID_INPUT" == *.log || -f "$ITEM_ID_INPUT" ]]; then
  ITEM_ID="mde:update"
  EVIDENCE_INPUT="$ITEM_ID_INPUT"
else
  ITEM_ID="$ITEM_ID_INPUT"
fi

ITEM_TITLE="${MDE_UPDATE_REMEDIATION_ITEM_TITLE:-$ITEM_ID}"
PROOF_COMMAND="${MDE_UPDATE_REMEDIATION_PROOF_COMMAND:-}"
SUCCESS_CRITERION="${MDE_UPDATE_REMEDIATION_SUCCESS_CRITERION:-}"
DOMAIN_HINT="${MDE_UPDATE_REMEDIATION_DOMAIN:-$ITEM_ID $EVIDENCE_INPUT}"
ACTIVE_DOMAIN="$("$REPO_ROOT/scripts/mde-domain-classify.sh" "$DOMAIN_HINT")"
export MDE_ACTIVE_DOMAIN="$ACTIVE_DOMAIN"

if [[ -z "$PROOF_COMMAND" ]]; then
  case "$ITEM_ID" in
    mde:update)
      PROOF_COMMAND="mise run mde:update"
      ;;
    mde:*)
      PROOF_COMMAND="mise run $ITEM_ID"
      ;;
    scripts/*)
      PROOF_COMMAND="bash $ITEM_ID"
      ;;
    *)
      PROOF_COMMAND="true"
      ;;
  esac
fi

if [[ -z "$SUCCESS_CRITERION" ]]; then
  if [[ "$ITEM_ID" == "mde:update" ]]; then
    SUCCESS_CRITERION="zero updater error lines in the latest log"
  else
    SUCCESS_CRITERION="proof command completes and target-specific validations pass"
  fi
fi

if [[ "$EVIDENCE_INPUT" = /* ]]; then
  EVIDENCE_PATH="$EVIDENCE_INPUT"
else
  EVIDENCE_PATH="$REPO_ROOT/$EVIDENCE_INPUT"
fi

if [[ ! -x "$RUNNER" ]]; then
  echo "Runner is not executable: $RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR" "$ARTIFACT_DIR" "docs/plans"
"$REPO_ROOT/scripts/teams/run-mde-domain-team.sh" --domain "$ACTIVE_DOMAIN" --trigger "$ITEM_ID"

count_error_lines() {
  local evidence_path="$1"
  if [[ "$ITEM_ID" != "mde:update" || ! -f "$evidence_path" ]]; then
    printf '0\n'
    return 0
  fi
  local count
  count="$(rg -n -e "$ERROR_REGEX" "$evidence_path" 2>/dev/null | wc -l | tr -d ' ')"
  printf '%s\n' "${count:-0}"
}

run_update_attempt() {
  if [[ "$ITEM_ID" != "mde:update" ]]; then
    return 0
  fi
  local attempt="$1"
  local attempt_log="$ARTIFACT_DIR/${DATE_STAMP}-attempt-${attempt}.log"

  echo "[mde-update-remediation] rerun attempt $attempt"
  (
    cd "$REPO_ROOT"
    mise run mde:update 2>&1 | tee "$attempt_log"
  )
  cp "$attempt_log" "$EVIDENCE_PATH"
}

run_subagent() {
  local id="$1"
  local objective="$2"
  local prompt_file="$3"
  local output_file="$4"
  local error_count
  error_count="$(count_error_lines "$EVIDENCE_PATH")"

  echo "[mde-update-remediation] running $id"
  "$RUNNER" "Subagent: $id
Date: $DATE_STAMP
Domain: $ACTIVE_DOMAIN
Remediation item id: $ITEM_ID
Remediation item title: $ITEM_TITLE
Objective: $objective
Prompt template: $prompt_file
Output file: $output_file
Evidence path: $EVIDENCE_PATH
Proof command: $PROOF_COMMAND
Success criterion: $SUCCESS_CRITERION
Current error line count: $error_count
Max rerun attempts: $MAX_ATTEMPTS
Requirements:
- Load `skills/mde-agent-runtime-contract` before task work.
- Use the modernization matrix and ownership registry as primary contract inputs.
- Read configs/mde-domain-catalog.json, configs/mde-reference-sources.json, configs/mde-preset-catalog.json, and configs/mde-learning-registry.json.
- Use reports/mde-domain-sdlc/$ACTIVE_DOMAIN as the delegated domain baseline before writing remediation specs or plans.
- Use the supplied evidence path as primary source evidence.
- Use real repository files and real execution evidence.
- Do not invoke scripts/teams/run-mde-update-remediation-team.sh from inside subagent execution.
- Do not use placeholder, stub, or mock content.
- Write all required output before finishing.
"
}

run_subagent "log-triage-agent" "Classify failures in the supplied mde-update log" "prompts/agent-team/mde-update-remediation/log-triage-agent.md" "$OUT_DIR/${DATE_STAMP}-01-log-triage.md"

run_subagent "maintenance-remediation-agent" "Review maintenance and installer scripts for grounded fixes" "prompts/agent-team/mde-update-remediation/maintenance-remediation-agent.md" "$OUT_DIR/${DATE_STAMP}-02-maintenance-remediation.md" &
pid_a=$!
run_subagent "parity-sync-agent" "Audit native macOS and devcontainer parity" "prompts/agent-team/mde-update-remediation/parity-sync-agent.md" "$OUT_DIR/${DATE_STAMP}-03-parity-sync.md" &
pid_b=$!
wait "$pid_a"
wait "$pid_b"

attempt=0
if [[ "$ITEM_ID" == "mde:update" && ! -f "$EVIDENCE_PATH" ]]; then
  attempt=1
  run_update_attempt "$attempt"
fi

while [[ "$ITEM_ID" == "mde:update" && "$(count_error_lines "$EVIDENCE_PATH")" != "0" && "$attempt" -lt "$MAX_ATTEMPTS" ]]; do
  attempt=$((attempt + 1))
  run_update_attempt "$attempt"
done

run_subagent "validation-agent" "Define rerun criteria and proof commands" "prompts/agent-team/mde-update-remediation/validation-agent.md" "$OUT_DIR/${DATE_STAMP}-04-validation.md"
run_subagent "spec-agent" "Write the remediation spec" "prompts/agent-team/mde-update-remediation/spec-agent.md" "docs/plans/${DATE_STAMP}-mde-update-remediation-spec.md"
run_subagent "plan-agent" "Write the sequenced next-step plan" "prompts/agent-team/mde-update-remediation/plan-agent.md" "docs/plans/${DATE_STAMP}-mde-update-remediation-plan.md"

VALIDATOR="${MDE_UPDATE_REMEDIATION_VALIDATOR:-scripts/teams/validate-mde-update-remediation-output.sh}"
echo "[mde-update-remediation] validating outputs with $VALIDATOR"
"$VALIDATOR" "$DATE_STAMP" "$OUT_DIR" "$ITEM_ID" "$EVIDENCE_PATH"

echo "[mde-update-remediation] complete"
echo "outputs: $OUT_DIR"
