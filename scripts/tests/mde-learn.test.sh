#!/usr/bin/env bash
# Test: mde-learn.sh learning lifecycle wrapper
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0
SCRIPT="scripts/mde-learn.sh"

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== mde-learn.sh Learning Lifecycle Tests ==="

# --- Prerequisite: script exists and is executable ---
if [[ -x "$SCRIPT" ]]; then
  pass "mde-learn.sh exists and is executable"
else
  fail "mde-learn.sh missing or not executable"
  echo "Results: $PASS passed, $FAIL failed"
  exit 1
fi

# --- Syntax check ---
if bash -n "$SCRIPT" 2>/dev/null; then
  pass "mde-learn.sh passes bash -n syntax check"
else
  fail "mde-learn.sh has syntax errors"
fi

# --- init: creates memory DB ---
if bash "$SCRIPT" init 2>/dev/null; then
  pass "mde-learn.sh init exits 0"
else
  fail "mde-learn.sh init failed"
fi

if [[ -f ".swarm/memory.db" ]]; then
  pass "init created .swarm/memory.db"
else
  fail "init did not create .swarm/memory.db"
fi

# --- store + search round-trip ---
if bash "$SCRIPT" store "test-learn-key" "test-learn-value-$$" 2>/dev/null; then
  pass "mde-learn.sh store exits 0"
else
  fail "mde-learn.sh store failed"
fi

if bash "$SCRIPT" search "test-learn" 2>/dev/null; then
  pass "mde-learn.sh search exits 0"
else
  fail "mde-learn.sh search failed"
fi

# --- status ---
if bash "$SCRIPT" status 2>/dev/null; then
  pass "mde-learn.sh status exits 0"
else
  fail "mde-learn.sh status failed"
fi

# --- consolidate ---
if bash "$SCRIPT" consolidate 2>/dev/null; then
  pass "mde-learn.sh consolidate exits 0"
else
  fail "mde-learn.sh consolidate failed"
fi

# --- usage: unknown subcommand prints help ---
if ! bash "$SCRIPT" unknown-cmd 2>/dev/null; then
  pass "unknown subcommand exits non-zero"
else
  fail "unknown subcommand should exit non-zero"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]] || exit 1
