#!/usr/bin/env bash
# Test: Tool precedence enforcement
# Validates that mise-managed runtimes take precedence over Homebrew/standalone.
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Tool Precedence Tests ==="

# Scenario: mise-managed Python takes precedence over brew
python_path="$(which python3 2>/dev/null || true)"
if [[ -n "$python_path" && "$python_path" == *mise* ]]; then
  pass "python3 resolves via mise ($python_path)"
elif [[ -n "$python_path" ]]; then
  fail "python3 resolves outside mise: $python_path"
else
  fail "python3 not found"
fi

# Scenario: mise-managed node takes precedence
node_path="$(which node 2>/dev/null || true)"
if [[ -n "$node_path" && "$node_path" == *mise* ]]; then
  pass "node resolves via mise ($node_path)"
elif [[ -n "$node_path" ]]; then
  fail "node resolves outside mise: $node_path"
else
  fail "node not found"
fi

# Scenario: mise-managed bun takes precedence over standalone
bun_path="$(which bun 2>/dev/null || true)"
if [[ -n "$bun_path" && "$bun_path" == *mise* ]]; then
  pass "bun resolves via mise ($bun_path)"
elif [[ -n "$bun_path" ]]; then
  fail "bun resolves outside mise: $bun_path"
else
  fail "bun not found"
fi

# Scenario: mise-managed go takes precedence
go_path="$(which go 2>/dev/null || true)"
if [[ -n "$go_path" && "$go_path" == *mise* ]]; then
  pass "go resolves via mise ($go_path)"
elif [[ -n "$go_path" ]]; then
  fail "go resolves outside mise: $go_path"
else
  fail "go not found"
fi

# Scenario: mise-managed rust takes precedence
# Note: mise manages Rust via the cargo/rustup backend, so ~/.cargo/bin is valid
rustc_path="$(which rustc 2>/dev/null || true)"
if [[ -n "$rustc_path" && ("$rustc_path" == *mise* || "$rustc_path" == */.cargo/bin/*) ]]; then
  pass "rustc resolves via mise/cargo ($rustc_path)"
elif [[ -n "$rustc_path" ]]; then
  fail "rustc resolves outside mise: $rustc_path"
else
  fail "rustc not found"
fi

# Scenario: PATH ordering in template -- mise shims listed before Homebrew
# The core template is the source of truth for PATH ordering.
env_template="templates/oh-my-zsh/10-mde-core.zsh"
mise_line="$(grep -n 'mise/shims' "$env_template" | head -1 | cut -d: -f1 || true)"
brew_line="$(grep -n 'homebrew' "$env_template" | head -1 | cut -d: -f1 || true)"

if [[ -n "$mise_line" && -n "$brew_line" && "$mise_line" -lt "$brew_line" ]]; then
  pass "template PATH: mise shims (line $mise_line) before Homebrew (line $brew_line)"
elif [[ -n "$mise_line" && -z "$brew_line" ]]; then
  pass "template PATH: mise shims present, no Homebrew entries"
else
  fail "template PATH ordering: mise_line=$mise_line brew_line=$brew_line"
fi

# Scenario: login-shell PATH template includes mde-managed bin for Fabric and
# similar repo-managed tools installed outside ~/.local/bin wrappers.
zprofile_template="templates/zprofile/macos-dev-env.zsh"
if grep -Fq '$HOME/.local/share/mde/bin' "$zprofile_template"; then
  pass "login-shell PATH template includes ~/.local/share/mde/bin"
else
  fail "login-shell PATH template missing ~/.local/share/mde/bin"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
