#!/usr/bin/env bash
# Test: uv/mise integration
# Validates that UV_PYTHON_DOWNLOADS=never is set and uv uses mise Python.
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== uv/mise Integration Tests ==="

# Scenario: UV_PYTHON_DOWNLOADS is set in core shell template
env_template="templates/oh-my-zsh/10-mde-core.zsh"
if grep -q 'UV_PYTHON_DOWNLOADS' "$env_template" && grep -q 'never' "$env_template"; then
  pass "UV_PYTHON_DOWNLOADS=never set in env template"
else
  fail "UV_PYTHON_DOWNLOADS=never not found in $env_template"
fi

# Scenario: Old UV_NO_MANAGED_PYTHON is NOT in the env template
if grep -q 'UV_NO_MANAGED_PYTHON' "$env_template"; then
  fail "stale UV_NO_MANAGED_PYTHON still present in $env_template"
else
  pass "UV_NO_MANAGED_PYTHON removed from env template"
fi

# Scenario: UV_PYTHON_DOWNLOADS is set in maintenance script
maint_script="scripts/macos-dev-maintenance.sh"
if grep -q 'UV_PYTHON_DOWNLOADS' "$maint_script"; then
  pass "UV_PYTHON_DOWNLOADS referenced in maintenance script"
else
  fail "UV_PYTHON_DOWNLOADS not found in $maint_script"
fi

# Scenario: mise-config.md uses the correct variable name
mise_doc="docs/mise-config.md"
if grep -q 'UV_PYTHON_DOWNLOADS' "$mise_doc"; then
  pass "docs/mise-config.md uses UV_PYTHON_DOWNLOADS"
else
  fail "docs/mise-config.md missing UV_PYTHON_DOWNLOADS"
fi

if grep -q 'UV_NO_MANAGED_PYTHON' "$mise_doc"; then
  fail "docs/mise-config.md still has stale UV_NO_MANAGED_PYTHON"
else
  pass "docs/mise-config.md clean of stale variable name"
fi

# Scenario: setup-notes.md uses the correct variable name
setup_doc="docs/setup-notes.md"
if grep -q 'UV_PYTHON_DOWNLOADS' "$setup_doc"; then
  pass "docs/setup-notes.md uses UV_PYTHON_DOWNLOADS"
else
  fail "docs/setup-notes.md missing UV_PYTHON_DOWNLOADS"
fi

if grep -q 'UV_NO_MANAGED_PYTHON' "$setup_doc"; then
  fail "docs/setup-notes.md still has stale UV_NO_MANAGED_PYTHON"
else
  pass "docs/setup-notes.md clean of stale variable name"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
