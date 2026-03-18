#!/usr/bin/env bash
# Test: mise npm tool version isolation
# Validates that npm-backed mise tools are isolated from ~/node_modules/ hoisting.
# Root cause this prevents: a ~/package.json causes bun to hoist all npm installs
# into ~/node_modules/, breaking per-version isolation.
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0
SKIP=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
skip() { SKIP=$((SKIP + 1)); printf '  \033[33mSKIP\033[0m %s\n' "$1"; }

echo "=== mise npm Version Isolation Tests ==="

# ── Guard: ~/package.json must not exist ──
if [[ -f "$HOME/package.json" ]]; then
  fail "~/package.json exists (causes bun hoisting)"
else
  pass "no ~/package.json"
fi

# ── Guard: ~/node_modules/ must not exist ──
if [[ -d "$HOME/node_modules" ]]; then
  fail "~/node_modules/ exists (stale shared deps)"
else
  pass "no ~/node_modules/"
fi

# ── Guard: ~/bun.lock must not exist ──
if [[ -f "$HOME/bun.lock" ]]; then
  fail "~/bun.lock exists (companion to rogue package.json)"
else
  pass "no ~/bun.lock"
fi

# ── Binary version matches mise version ──
# Maps: binary_name -> mise_tool_name
declare -A TOOL_MAP=(
  [gemini]=gemini-cli
  [claude]=claude
  [devcontainer]=devcontainer
  [biome]="npm:@biomejs/biome"
  [codex]="npm:@openai/codex"
)

for bin in "${!TOOL_MAP[@]}"; do
  tool="${TOOL_MAP[$bin]}"
  bin_path="$(command -v "$bin" 2>/dev/null || true)"

  if [[ -z "$bin_path" ]]; then
    skip "$bin not installed"
    continue
  fi

  # Get version from binary
  bin_version="$("$bin" --version 2>/dev/null | head -1 | sed 's/^[^0-9]*//' | sed 's/[[:space:]].*//' || true)"

  # Get version from mise (the active/configured version)
  # mise ls shows: tool version [source] [requested]
  # We want the version that has a source (config.toml)
  mise_version="$(mise ls "$tool" 2>/dev/null | awk '$3 ~ /config/ {print $2}' | head -1 || true)"
  if [[ -z "$mise_version" ]]; then
    # Fallback: just get the latest installed version
    mise_version="$(mise ls "$tool" 2>/dev/null | tail -1 | awk '{print $2}' || true)"
  fi

  if [[ -z "$bin_version" || -z "$mise_version" ]]; then
    skip "$bin: could not determine versions (bin=$bin_version mise=$mise_version)"
    continue
  fi

  if [[ "$bin_version" == "$mise_version" ]]; then
    pass "$bin version matches mise: $bin_version"
  else
    fail "$bin version mismatch: binary=$bin_version mise=$mise_version"
  fi
done

# ── Symlinks must not resolve to ~/node_modules/ ──
echo ""
echo "--- Symlink isolation checks ---"

mise_installs="$HOME/.local/share/mise/installs"
if [[ -d "$mise_installs" ]]; then
  bad_links=0
  checked=0
  # Check binary symlinks in npm-* and alias dirs (gemini-cli, claude, etc.)
  while IFS= read -r link; do
    target="$(readlink -f "$link" 2>/dev/null || true)"
    if [[ "$target" == "$HOME/node_modules/"* ]]; then
      fail "symlink escapes to ~/node_modules/: $(basename "$(dirname "$(dirname "$link")")")/$(basename "$link") -> $target"
      bad_links=$((bad_links + 1))
    fi
    checked=$((checked + 1))
  done < <(find "$mise_installs" -maxdepth 5 -path "*/bin/*" -type l 2>/dev/null | grep -E '(npm-|gemini-cli|claude|devcontainer)' || true)

  if [[ "$bad_links" -eq 0 && "$checked" -gt 0 ]]; then
    pass "all $checked mise symlinks are self-contained"
  elif [[ "$checked" -eq 0 ]]; then
    skip "no symlinks found to check in mise installs"
  fi
else
  skip "mise installs directory not found"
fi

# ── Summary ──
echo ""
echo "=== Results: $PASS passed, $FAIL failed, $SKIP skipped ==="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
