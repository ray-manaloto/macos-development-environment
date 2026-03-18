#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \[32mPASS\[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \[31mFAIL\[0m %s\n' "$1"; }

MAINT_SCRIPT="scripts/macos-dev-maintenance.sh"
AGENT_STACK_SCRIPT="scripts/install-agent-stack.sh"
LANGCHAIN_SCRIPT="scripts/install-langchain-cli-tools.sh"
RUNNER_SCRIPT="scripts/teams/run-mde-update-remediation-team.sh"
VALIDATOR_SCRIPT="scripts/teams/validate-mde-update-remediation-output.sh"
PROMPTS_DIR="prompts/agent-team/mde-update-remediation"
DOC_SCRIPT="docs/teams/mde-update-remediation-team.md"


echo "=== MDE Update Remediation Tests ==="

if grep -q 'resolve_homebrew_curl()' "$MAINT_SCRIPT" && grep -q 'HOMEBREW_CURL_PATH' "$MAINT_SCRIPT"; then
  pass "maintenance script validates and exports HOMEBREW_CURL_PATH before brew update"
else
  fail "maintenance script is missing Homebrew curl hardening"
fi

if grep -q 'with_stable_cwd()' "$MAINT_SCRIPT" && grep -q 'mktemp -d' "$MAINT_SCRIPT" && grep -q 'Skipping blanket bun global update' "$MAINT_SCRIPT"; then
  pass "maintenance avoids the unsafe blanket bun global update path"
else
  fail "maintenance still uses the unsafe blanket bun global update path"
fi

if grep -q 'with_stable_cwd()' "$AGENT_STACK_SCRIPT" && grep -q 'mktemp -d' "$AGENT_STACK_SCRIPT" && grep -q 'with_stable_cwd bun add -g' "$AGENT_STACK_SCRIPT"; then
  pass "agent stack bun installs run from an isolated working directory"
else
  fail "agent stack bun installs do not use an isolated working directory"
fi

if grep -q 'with_stable_cwd()' "$LANGCHAIN_SCRIPT" && grep -q 'mktemp -d' "$LANGCHAIN_SCRIPT" && grep -q 'with_stable_cwd bun add -g' "$LANGCHAIN_SCRIPT"; then
  pass "langchain tool bun installs run from an isolated working directory"
else
  fail "langchain tool bun installs do not use an isolated working directory"
fi

if grep -q 'Skipping npm-backed mise tools during upgrade' "$MAINT_SCRIPT" \
  && grep -q 'mise upgrade --yes "${exclude_args' "$MAINT_SCRIPT" \
  && grep -q 'else' "$MAINT_SCRIPT" \
  && grep -q 'mise upgrade --yes || return 1' "$MAINT_SCRIPT"; then
  pass "maintenance script excludes npm-backed mise tools from blanket mise upgrade and handles empty excludes"
else
  fail "maintenance script still mishandles the empty npm exclude case"
fi

if ! grep -q 'uv tool upgrade --all' "$MAINT_SCRIPT" && grep -q 'managed_tools=' "$MAINT_SCRIPT"; then
  pass "maintenance uv upgrades skip repo-managed ephemeral tools"
else
  fail "maintenance uv upgrades still use the unsafe blanket all-tools path"
fi

if grep -q 'tool_refresh_is_best_effort()' "$LANGCHAIN_SCRIPT" && grep -q 'refresh skipped for existing best-effort tool' "$LANGCHAIN_SCRIPT"; then
  pass "langchain installer skips noisy refreshes for existing best-effort tools"
else
  fail "langchain installer still attempts noisy refreshes for best-effort tools"
fi

VERIFY_SCRIPT="scripts/verify-langchain-tools.sh"

if grep -q 'optional_tools=' "$VERIFY_SCRIPT" && grep -q 'langgraph-engineer|--help|soft' "$VERIFY_SCRIPT"; then
  pass "langgraph-engineer verification is optional and soft"
else
  fail "langgraph-engineer verification is still hard-required"
fi

if grep -q 'MDE_UPDATE_REMEDIATION_ITEM_ID' "$RUNNER_SCRIPT" \
  && grep -q 'MDE_UPDATE_REMEDIATION_EVIDENCE_PATH' "$RUNNER_SCRIPT" \
  && grep -q 'PROOF_COMMAND=' "$RUNNER_SCRIPT" \
  && grep -q 'SUCCESS_CRITERION=' "$RUNNER_SCRIPT" \
  && grep -q 'run_update_attempt()' "$RUNNER_SCRIPT"; then
  pass "team runner supports generic remediation items with explicit proof metadata"
else
  fail "team runner is missing generic remediation item controls"
fi

if grep -q 'ITEM_ID_INPUT=' "$VALIDATOR_SCRIPT" \
  && grep -q 'EVIDENCE_INPUT=' "$VALIDATOR_SCRIPT" \
  && grep -q 'EVIDENCE_BASENAME=' "$VALIDATOR_SCRIPT" \
  && grep -q 'latest log still contains updater error lines' "$VALIDATOR_SCRIPT"; then
  pass "validator accepts generic remediation items and preserves strict mde:update log enforcement"
else
  fail "validator is missing generic remediation item enforcement"
fi

if grep -q 'mde-modernization-matrix.json' "$PROMPTS_DIR"/log-triage-agent.md \
  && grep -q 'mde-modernization-matrix.json' "$PROMPTS_DIR"/maintenance-remediation-agent.md \
  && grep -q 'scripts/install-agent-stack.sh /absolute/path/to/evidence.log' "$DOC_SCRIPT"; then
  pass "team runner assets reference the modernization matrix and generic evidence-driven invocation"
else
  fail "team runner assets are missing modernization matrix or generic invocation guidance"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
