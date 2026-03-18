#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=scripts/lib/mde-cache-policy.sh
source "$ROOT_DIR/scripts/lib/mde-cache-policy.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT
export HOME="$tmp_home"
export MDE_PLATFORM="macos"

mde_prepare_cache_dirs
report="$(mde_cache_policy_env_report)"

for key in UV_CACHE_DIR PIPX_HOME PIPX_BIN_DIR BUN_INSTALL GOCACHE GOMODCACHE CARGO_HOME RUSTUP_HOME; do
  if printf '%s\n' "$report" | grep -q "^${key}="; then
    pass "cache report includes $key"
  else
    fail "cache report missing $key"
  fi
  value="$(printf '%s\n' "$report" | sed -n "s/^${key}=//p")"
  if [[ -d "$value" && -w "$value" ]]; then
    pass "$key directory is writable"
  else
    fail "$key directory is not writable"
  fi
done

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
