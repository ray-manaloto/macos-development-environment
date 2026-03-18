#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GUARD="$ROOT_DIR/scripts/mde-command-guard.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
home_dir="$tmp_dir/home"
real_bin="$tmp_dir/real-bin"
guard_bin="$tmp_dir/guard-bin"
telemetry_dir="$tmp_dir/telemetry"
mkdir -p "$home_dir" "$real_bin" "$guard_bin" "$telemetry_dir"

cat > "$real_bin/brew" <<'SCRIPT'
#!/usr/bin/env bash
printf 'REAL_BREW:%s\n' "$*"
SCRIPT
chmod +x "$real_bin/brew"
ln -s "$GUARD" "$guard_bin/brew"

set +e
blocked_output="$(env -i HOME="$home_dir" PATH="$guard_bin:$real_bin:/usr/bin:/bin" MDE_TELEMETRY_DIR="$telemetry_dir" brew install ripgrep 2>&1)"
blocked_status=$?
set -e
if (( blocked_status == 97 )) && printf '%s' "$blocked_output" | grep -q 'blocked for agents'; then
  pass 'brew install is blocked by the agent command guard'
else
  fail "expected blocked brew install (exit=$blocked_status output=$blocked_output)"
fi

pass_output="$(env -i HOME="$home_dir" PATH="$guard_bin:$real_bin:/usr/bin:/bin" MDE_TELEMETRY_DIR="$telemetry_dir" brew --version 2>&1)"
if printf '%s' "$pass_output" | grep -q 'REAL_BREW:--version'; then
  pass 'non-install brew commands pass through the guard'
else
  fail "expected passthrough brew --version output (output=$pass_output)"
fi

cat > "$tmp_dir/exceptions.json" <<'JSON'
{
  "version": 1,
  "exceptions": [
    {
      "tool": "llvm",
      "targets": ["llvm"],
      "allowed_installers": ["brew"],
      "reason": "host compiler exception",
      "review_by": "2026-12-31"
    }
  ]
}
JSON

allowed_output="$(env -i HOME="$home_dir" PATH="$guard_bin:$real_bin:/usr/bin:/bin" MDE_TELEMETRY_DIR="$telemetry_dir" MDE_MISE_EXCEPTION_ALLOWLIST="$tmp_dir/exceptions.json" MDE_ALLOW_UNMANAGED_INSTALL=1 brew install llvm 2>&1)"
if printf '%s' "$allowed_output" | grep -q 'REAL_BREW:install llvm'; then
  pass 'exception override allows a registered unmanaged install target'
else
  fail "expected override passthrough for llvm (output=$allowed_output)"
fi

telemetry_file="$(find "$telemetry_dir" -type f -name '*-events.jsonl' | head -n1 || true)"
if [[ -n "$telemetry_file" ]] && grep -q 'policy.command.blocked' "$telemetry_file" && grep -q 'policy.exception.used' "$telemetry_file"; then
  pass 'telemetry records blocked commands and exception overrides'
else
  fail 'expected telemetry events for blocked and exception-allowed commands'
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
