#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRIFT="$ROOT_DIR/scripts/mde-drift-check.sh"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

HOST_PYTHON="$(python3 -c 'import sys; print(sys.executable)' 2>/dev/null || python -c 'import sys; print(sys.executable)')"

write_passthrough_python_shim() {
  local target="$1"
  cat > "$target" <<SCRIPT
#!/usr/bin/env bash
exec "$HOST_PYTHON" "\$@"
SCRIPT
  chmod +x "$target"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
tmp_home="$tmp_dir/home"
mkdir -p "$tmp_home/.local/share/mise/shims"

pre_path="/usr/bin:/bin"
post_path="/usr/bin:/bin"

set +e
pre_warn_output="$(env -i HOME="$tmp_home" PATH="$pre_path" MDE_PLATFORM=linux MDE_DRIFT_ENFORCE=0 "$DRIFT" 2>&1)"
pre_warn_status=$?
set -e
if (( pre_warn_status == 0 )) && printf '%s' "$pre_warn_output" | grep -q 'warnings'; then
  pass 'pre-remediation drift warnings are non-failing when enforcement is disabled'
else
  fail "expected non-failing warnings before remediation (exit=$pre_warn_status output=$pre_warn_output)"
fi

set +e
pre_enforce_output="$(env -i HOME="$tmp_home" PATH="$pre_path" MDE_PLATFORM=linux MDE_DRIFT_ENFORCE=1 "$DRIFT" 2>&1)"
pre_enforce_status=$?
set -e
if (( pre_enforce_status != 0 )) && printf '%s' "$pre_enforce_output" | grep -q 'Enforcement mode'; then
  pass 'pre-remediation drift warnings fail under enforcement'
else
  fail "expected enforcement failure before remediation (exit=$pre_enforce_status output=$pre_enforce_output)"
fi

write_passthrough_python_shim "$tmp_home/.local/share/mise/shims/python"
write_passthrough_python_shim "$tmp_home/.local/share/mise/shims/python3"

for cmd in node bun go uv pixi codex devcontainer rustc; do
  cat > "$tmp_home/.local/share/mise/shims/$cmd" <<'SCRIPT'
#!/usr/bin/env bash
exit 0
SCRIPT
  chmod +x "$tmp_home/.local/share/mise/shims/$cmd"
done

set +e
post_output="$(env -i HOME="$tmp_home" PATH="$post_path" MDE_PLATFORM=linux MDE_DRIFT_ENFORCE=1 "$DRIFT" 2>&1)"
post_status=$?
set -e
if (( post_status == 0 )) && printf '%s' "$post_output" | grep -q 'clean (no policy violations)'; then
  pass 'post-remediation state is clean in enforcement mode'
else
  fail "expected clean drift state after remediation (exit=$post_status output=$post_output)"
fi

devcontainer_home="$tmp_dir/devcontainer-home"
mkdir -p "$devcontainer_home/.local/share/mise/shims"

write_passthrough_python_shim "$devcontainer_home/.local/share/mise/shims/python"
write_passthrough_python_shim "$devcontainer_home/.local/share/mise/shims/python3"

for cmd in bun uv pixi chezmoi; do
  cat > "$devcontainer_home/.local/share/mise/shims/$cmd" <<'SCRIPT'
#!/usr/bin/env bash
exit 0
SCRIPT
  chmod +x "$devcontainer_home/.local/share/mise/shims/$cmd"
done

set +e
devcontainer_output="$(env -i HOME="$devcontainer_home" PATH="$post_path" MDE_PLATFORM=devcontainer MDE_DRIFT_ENFORCE=1 "$DRIFT" 2>&1)"
devcontainer_status=$?
set -e
if (( devcontainer_status == 0 )) \
  && printf '%s' "$devcontainer_output" | grep -q 'clean (no policy violations)' \
  && ! printf '%s' "$devcontainer_output" | grep -Eq "required mise-managed command '(node|go|codex|devcontainer)'"; then
  pass 'devcontainer enforcement uses the devcontainer bootstrap manifest instead of host-global runtime requirements'
else
  fail "expected devcontainer drift to stay scoped to the bootstrap manifest (exit=$devcontainer_status output=$devcontainer_output)"
fi

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
