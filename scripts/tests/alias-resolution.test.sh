#!/usr/bin/env bash
# Test: MDE lifecycle alias resolution
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Alias Resolution Tests ==="

ALIASES_FILE="$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh"

if [[ ! -f "$ALIASES_FILE" ]]; then
  fail "20-mde-aliases.zsh not deployed at $ALIASES_FILE"
  echo "Results: $PASS passed, $FAIL failed"
  exit 1
fi

declare -A EXPECTED_ALIASES=(
  [mde-update]="mde update"
  [mde-update-fast]="mde update-fast"
  [mde-verify]="mde verify"
  [mde-drift]="mde drift"
  [mde-migrate]="mde migrate"
  [mde-agents-review]="mde agents-review"
)

for alias_name in "${!EXPECTED_ALIASES[@]}"; do
  target="${EXPECTED_ALIASES[$alias_name]}"

  if grep -Eq "alias ${alias_name}=['\\\"]${target}['\\\"]" "$ALIASES_FILE"; then
    pass "alias $alias_name is defined"
  else
    fail "alias $alias_name is NOT defined with expected target"
  fi
done

for target_script in \
  scripts/macos-dev-maintenance.sh \
  scripts/mde-verify \
  scripts/mde-drift-check.sh \
  scripts/mde-migrate-to-mise.sh \
  scripts/mde-agents-review.sh \
; do
  if [[ -f "$target_script" ]]; then
    pass "target $target_script exists"
  else
    fail "target $target_script missing"
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
