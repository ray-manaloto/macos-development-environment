#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATUS_SCRIPT="$ROOT_DIR/scripts/status-dashboard.sh"
VERIFY_SCRIPT="$ROOT_DIR/scripts/verify-status-dashboard-json.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$tmp_dir/scripts"
cat > "$tmp_dir/scripts/openlit-control.sh" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "endpoints" ]]; then
  printf '\033[32mhttp://127.0.0.1:4318\tgrpc\033[0m\nhttps://127.0.0.1:3000/ui\r\n'
fi
EOF
chmod +x "$tmp_dir/scripts/openlit-control.sh"

parse_json() {
  if command -v jq >/dev/null 2>&1; then
    jq -e . >/dev/null
    return 0
  fi
  python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null
}

set +e
json_output="$(
  cd "$tmp_dir" &&
    MDE_PLATFORM=devcontainer "$STATUS_SCRIPT" --json
)"
status_json=$?
set -e

if (( status_json == 0 )) && printf '%s\n' "$json_output" | parse_json; then
  pass "status-dashboard emits strict JSON when endpoints contain control characters"
else
  fail "status-dashboard JSON parse failed (exit=$status_json output=$json_output)"
fi

if printf '%s\n' "$json_output" | grep -q '"openlit"'; then
  pass "status-dashboard JSON includes openlit payload"
else
  fail "status-dashboard JSON missing openlit payload"
fi

set +e
(
  cd "$tmp_dir" &&
    MDE_PLATFORM=devcontainer "$VERIFY_SCRIPT"
) >/dev/null 2>&1
status_verify=$?
set -e

if (( status_verify == 0 )); then
  pass "verify-status-dashboard-json succeeds on strict JSON output"
else
  fail "verify-status-dashboard-json failed (exit=$status_verify)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
