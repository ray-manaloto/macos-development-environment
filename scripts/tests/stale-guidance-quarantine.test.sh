#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WAVE1="$ROOT_DIR/reports/mise-parallel-2026-03-09/wave1-install-review.md"
WAVE2="$ROOT_DIR/reports/mise-parallel-2026-03-09/wave2-recommended-runbook.md"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Stale Guidance Quarantine Tests ==="

for report in "$WAVE1" "$WAVE2"; do
  if rg -q '^> Historical report:' "$report" && rg -q 'Do not use this as the active runbook' "$report"; then
    pass "$(basename "$report") is explicitly quarantined"
  else
    fail "$(basename "$report") is missing a quarantine warning"
  fi
done

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
