#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }

check_equal() {
  local left="$1"
  local right="$2"
  local label="$3"
  if diff -u "$left" "$right" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label"
  fi
}

echo "=== Chezmoi Template Parity Tests ==="

check_equal \
  "$ROOT_DIR/templates/oh-my-zsh/10-mde-core.zsh" \
  "$ROOT_DIR/.chezmoisource/dot_oh-my-zsh/custom/10-mde-core.zsh" \
  "10-mde-core stays in parity between templates and chezmoi"

check_equal \
  "$ROOT_DIR/templates/oh-my-zsh/15-mde-platform.zsh" \
  "$ROOT_DIR/.chezmoisource/dot_oh-my-zsh/custom/15-mde-platform.zsh" \
  "15-mde-platform stays in parity between templates and chezmoi"

check_equal \
  "$ROOT_DIR/templates/oh-my-zsh/20-mde-aliases.zsh" \
  "$ROOT_DIR/.chezmoisource/dot_oh-my-zsh/custom/20-mde-aliases.zsh" \
  "20-mde-aliases stays in parity between templates and chezmoi"

check_equal \
  "$ROOT_DIR/templates/zprofile/macos-dev-env.zsh" \
  "$ROOT_DIR/.chezmoisource/dot_zprofile.d/macos-dev-env.zsh" \
  "macos-dev-env stays in parity between templates and chezmoi"

echo "Results: $PASS passed, $FAIL failed"
(( FAIL == 0 ))
