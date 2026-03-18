#!/usr/bin/env bash
# Test: Maintenance gate fix (P0-2)
# Validates that sync_managed_configs runs unconditionally (outside MDE_AUTOFIX gate)
# while destructive operations remain gated.
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Maintenance Gate Tests ==="

MAINT_SCRIPT="scripts/macos-dev-maintenance.sh"

# Scenario: sync_managed_configs is NOT inside the MDE_AUTOFIX block
# Strategy: find the line number of sync_managed_configs and the MDE_AUTOFIX block,
# verify sync_managed_configs appears BEFORE the if-block.
sync_line=$(grep -n 'sync_managed_configs' "$MAINT_SCRIPT" | head -1 | cut -d: -f1)
autofix_line=$(grep -n 'if \[\[ "$MDE_AUTOFIX"' "$MAINT_SCRIPT" | head -1 | cut -d: -f1)

if [[ -n "$sync_line" && -n "$autofix_line" ]]; then
  if [[ "$sync_line" -lt "$autofix_line" ]]; then
    pass "sync_managed_configs (line $sync_line) runs before MDE_AUTOFIX gate (line $autofix_line)"
  else
    fail "sync_managed_configs (line $sync_line) is still inside MDE_AUTOFIX gate (line $autofix_line)"
  fi
else
  if [[ -z "$sync_line" ]]; then
    fail "sync_managed_configs not found in $MAINT_SCRIPT"
  fi
  if [[ -z "$autofix_line" ]]; then
    fail "MDE_AUTOFIX gate not found in $MAINT_SCRIPT"
  fi
fi

# Scenario: remove_conflicting_managers call (not definition) remains inside MDE_AUTOFIX gate
# Match the indented call site, not the function definition line
remove_line=$(grep -n '^\s\+remove_conflicting_managers' "$MAINT_SCRIPT" | head -1 | cut -d: -f1)
if [[ -n "$remove_line" && -n "$autofix_line" ]]; then
  if [[ "$remove_line" -gt "$autofix_line" ]]; then
    pass "remove_conflicting_managers (line $remove_line) remains gated behind MDE_AUTOFIX"
  else
    fail "remove_conflicting_managers (line $remove_line) escaped the MDE_AUTOFIX gate"
  fi
fi

# Scenario: remove_brew_runtimes remains inside MDE_AUTOFIX_STRICT gate
strict_line=$(grep -n 'MDE_AUTOFIX_STRICT' "$MAINT_SCRIPT" | head -1 | cut -d: -f1)
brew_rm_line=$(grep -n '^\s\+remove_brew_runtimes' "$MAINT_SCRIPT" | head -1 | cut -d: -f1)
if [[ -n "$brew_rm_line" && -n "$strict_line" ]]; then
  if [[ "$brew_rm_line" -gt "$strict_line" ]]; then
    pass "remove_brew_runtimes remains gated behind MDE_AUTOFIX_STRICT"
  else
    fail "remove_brew_runtimes escaped the MDE_AUTOFIX_STRICT gate"
  fi
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
