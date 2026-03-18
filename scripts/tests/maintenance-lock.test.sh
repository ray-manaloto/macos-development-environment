#!/usr/bin/env bash
# Test: Maintenance lock recovery behavior
# Validates stale lock recovery implementation exists in maintenance script.
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Maintenance Lock Tests ==="

MAINT_SCRIPT="scripts/macos-dev-maintenance.sh"

if grep -Eq '^LOCK_PID_FILE=' "$MAINT_SCRIPT"; then
  pass "LOCK_PID_FILE is defined"
else
  fail "LOCK_PID_FILE is missing"
fi

if grep -Eq '^acquire_lock\(\)' "$MAINT_SCRIPT"; then
  pass "acquire_lock function exists"
else
  fail "acquire_lock function missing"
fi

if grep -Eq "kill -0 \"\\\$holder_pid\"" "$MAINT_SCRIPT"; then
  pass "live lock holder PID check exists"
else
  fail "live lock holder PID check missing"
fi

if grep -Eq 'Found stale maintenance lock; clearing\.' "$MAINT_SCRIPT"; then
  pass "stale lock recovery log exists"
else
  fail "stale lock recovery branch missing"
fi

if grep -Eq 'if ! acquire_lock; then|if acquire_lock; then' "$MAINT_SCRIPT"; then
  pass "main uses acquire_lock"
else
  fail "main does not use acquire_lock"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
