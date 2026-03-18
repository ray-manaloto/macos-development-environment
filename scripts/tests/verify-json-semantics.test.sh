#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIFY_ALL="$ROOT_DIR/scripts/verify-all.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

check_fail_cfg="$tmp_dir/check-fail.conf"
cat > "$check_fail_cfg" <<'EOF'
# name|script|severity|extra|platforms|allowed_skip_platforms_for_hard_checks
hard-skip-not-allowed|scripts/does-not-exist.sh|hard||macos|
EOF

check_allow_cfg="$tmp_dir/check-allow.conf"
cat > "$check_allow_cfg" <<'EOF'
# name|script|severity|extra|platforms|allowed_skip_platforms_for_hard_checks
hard-skip-allowed|scripts/does-not-exist.sh|hard||macos|devcontainer
EOF

set +e
out_fail="$(MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$check_fail_cfg" "$VERIFY_ALL" --json 2>/dev/null)"
status_fail=$?
set -e
if (( status_fail != 0 )) && printf '%s' "$out_fail" | grep -q '"overall":"fail"' \
  && printf '%s' "$out_fail" | grep -q '"skip_allowed":false'; then
  pass "hard skip without policy fails in JSON mode and exits non-zero"
else
  fail "unexpected hard skip should fail (exit=$status_fail output=$out_fail)"
fi

set +e
out_allow="$(MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$check_allow_cfg" "$VERIFY_ALL" --json 2>/dev/null)"
status_allow=$?
set -e
if (( status_allow == 0 )) && printf '%s' "$out_allow" | grep -q '"overall":"pass"' \
  && printf '%s' "$out_allow" | grep -q '"skip_allowed":true'; then
  pass "hard skip with explicit allow policy remains overall pass"
else
  fail "allowed hard skip should remain pass (exit=$status_allow output=$out_allow)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
