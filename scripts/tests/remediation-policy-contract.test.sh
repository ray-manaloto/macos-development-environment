#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMEDIATE_SCRIPT="$ROOT_DIR/scripts/mde-remediate.sh"
ALIASES_TEMPLATE="$ROOT_DIR/templates/oh-my-zsh/20-mde-aliases.zsh"
ALIASES_CHEZMOI="$ROOT_DIR/home/dot_oh-my-zsh/custom/20-mde-aliases.zsh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Remediation Policy Contract Tests ==="

if ! rg -q 'install-agent-stack\.sh|install-langchain-cli-tools\.sh' "$REMEDIATE_SCRIPT"; then
  pass "mde-remediate no longer falls back to legacy installer scripts"
else
  fail "mde-remediate still references legacy installer scripts"
fi

if rg -q 'mde-migrate-to-mise\.sh|mde:migrate:global-tools' "$REMEDIATE_SCRIPT"; then
  pass "mde-remediate routes repair through the mise migration path"
else
  fail "mde-remediate is missing a mise migration repair path"
fi

if rg -q 'mise run "\$task_name" -- "\$@"' "$ALIASES_TEMPLATE" \
  && rg -q 'mise run "\$task_name" -- "\$@"' "$ALIASES_CHEZMOI" \
  && rg -q 'mde_run_task "mde:' "$ALIASES_TEMPLATE" \
  && rg -q 'mde_run_task "mde:' "$ALIASES_CHEZMOI"; then
  pass "managed shell aliases dispatch through mise tasks"
else
  fail "managed shell aliases still bypass mise tasks"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
