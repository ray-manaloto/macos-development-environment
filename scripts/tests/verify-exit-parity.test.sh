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

cfg_disallow="$tmp_dir/disallow.conf"
cat > "$cfg_disallow" <<'EOF'
# name|script|severity|extra|platforms|allowed_skip_platforms_for_hard_checks
hard-platform-skip-disallow|scripts/health-check.sh|hard||macos|
EOF

cfg_allow="$tmp_dir/allow.conf"
cat > "$cfg_allow" <<'EOF'
# name|script|severity|extra|platforms|allowed_skip_platforms_for_hard_checks
hard-platform-skip-allow|scripts/health-check.sh|hard||macos|devcontainer
EOF

set +e
MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$cfg_disallow" "$VERIFY_ALL" >/dev/null 2>&1
status_plain_disallow=$?
MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$cfg_disallow" "$VERIFY_ALL" --json >/dev/null 2>&1
status_json_disallow=$?
set -e
if (( status_plain_disallow != 0 && status_json_disallow != 0 )); then
  pass "non-JSON and JSON both fail for disallowed hard skip"
else
  fail "exit parity failed for disallowed hard skip (plain=$status_plain_disallow json=$status_json_disallow)"
fi

set +e
MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$cfg_allow" "$VERIFY_ALL" >/dev/null 2>&1
status_plain_allow=$?
MDE_PLATFORM=devcontainer MDE_VERIFY_CONFIG="$cfg_allow" "$VERIFY_ALL" --json >/dev/null 2>&1
status_json_allow=$?
set -e
if (( status_plain_allow == 0 && status_json_allow == 0 )); then
  pass "non-JSON and JSON both pass for allowed hard skip"
else
  fail "exit parity failed for allowed hard skip (plain=$status_plain_allow json=$status_json_allow)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
