#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENSURE="$ROOT_DIR/scripts/ensure-managed-configs.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
tmp_home="$tmp_dir/home"
tmp_bin="$tmp_dir/bin"
mkdir -p "$tmp_home" "$tmp_bin"

cat > "$tmp_bin/chezmoi" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "diff" ]]; then
  echo "error parsing config file: not trusted" >&2
  exit 1
fi
if [[ "${1:-}" == "apply" ]]; then
  echo "Config files are not trusted." >&2
  exit 1
fi
exit 1
EOF
chmod +x "$tmp_bin/chezmoi"

# Pre-remediation: check mode should detect drift when files are absent.
set +e
pre_output="$(
  HOME="$tmp_home" \
  PATH="$tmp_bin:$PATH" \
  MDE_USE_CHEZMOI=1 \
  MDE_CHEZMOI_SOURCE="$ROOT_DIR/.chezmoisource" \
  "$ENSURE" --check 2>&1
)"
pre_status=$?
set -e

if (( pre_status != 0 )); then
  pass "check mode detects pre-remediation drift"
else
  fail "expected drift before remediation (exit=$pre_status output=$pre_output)"
fi

# Remediation run: apply mode should fallback to legacy sync and succeed.
set +e
output="$(
  HOME="$tmp_home" \
  PATH="$tmp_bin:$PATH" \
  MDE_USE_CHEZMOI=1 \
  MDE_CHEZMOI_SOURCE="$ROOT_DIR/.chezmoisource" \
  "$ENSURE" 2>&1
)"
status=$?
set -e

if (( status == 0 )); then
  pass "ensure-managed-configs exits successfully with trust/parsing chezmoi failure"
else
  fail "ensure-managed-configs should fallback and pass (exit=$status output=$output)"
fi

if printf '%s' "$output" | grep -q "falling back to legacy sync apply"; then
  pass "fallback warning is explicit in output"
else
  fail "expected fallback warning missing"
fi

if [[ -f "$tmp_home/.oh-my-zsh/custom/10-mde-core.zsh" ]]; then
  pass "legacy fallback applied managed shell templates"
else
  fail "fallback did not materialize managed shell templates"
fi

set +e
post_output="$(
  HOME="$tmp_home" \
  PATH="$tmp_bin:$PATH" \
  MDE_USE_CHEZMOI=1 \
  MDE_CHEZMOI_SOURCE="$ROOT_DIR/.chezmoisource" \
  "$ENSURE" --check 2>&1
)"
post_status=$?
set -e

if (( post_status == 0 )) && printf '%s' "$post_output" | grep -q "Managed configs: clean"; then
  pass "post-remediation check mode is clean"
else
  fail "post-remediation check should be clean (exit=$post_status output=$post_output)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
