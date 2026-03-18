#!/usr/bin/env bash
# Test: Template-to-deploy synchronization
set -euo pipefail

cd "$(dirname "$0")/../.."

PASS=0
FAIL=0
MANAGED_MARKER="Managed by macos-development-environment"

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

echo "=== Template Sync Tests ==="

for pair in \
  "templates/oh-my-zsh/10-mde-core.zsh:$HOME/.oh-my-zsh/custom/10-mde-core.zsh" \
  "templates/oh-my-zsh/15-mde-platform.zsh:$HOME/.oh-my-zsh/custom/15-mde-platform.zsh" \
  "templates/oh-my-zsh/20-mde-aliases.zsh:$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh" \
  "templates/oh-my-zsh/90-starship.zsh:$HOME/.oh-my-zsh/custom/90-starship.zsh" \
  "templates/zprofile/macos-dev-env.zsh:$HOME/.zprofile.d/macos-dev-env.zsh" \
; do
  src="${pair%%:*}"
  dest="${pair#*:}"
  name="$(basename "$src")"

  if [[ ! -f "$dest" ]]; then
    fail "deployed $name does not exist at $dest"
    continue
  fi

  if diff -q "$src" "$dest" >/dev/null 2>&1; then
    pass "deployed $name matches template"
  else
    fail "deployed $name differs from template"
  fi
done

for deployed in \
  "$HOME/.oh-my-zsh/custom/10-mde-core.zsh" \
  "$HOME/.oh-my-zsh/custom/15-mde-platform.zsh" \
  "$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh" \
; do
  name="$(basename "$deployed")"
  if [[ -f "$deployed" ]] && grep -q "$MANAGED_MARKER" "$deployed"; then
    pass "$name contains MANAGED_MARKER"
  else
    fail "$name missing MANAGED_MARKER"
  fi
done

bun_comp="$HOME/.oh-my-zsh/custom/completions/_bun"
if [[ -L "$bun_comp" ]]; then
  target="$(readlink "$bun_comp")"
  if [[ "$target" == *"/.bun/_bun" ]]; then
    pass "bun completions symlink points to ~/.bun/_bun"
  else
    fail "bun completions symlink points to unexpected target: $target"
  fi
else
  fail "bun completions symlink missing at $bun_comp"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
