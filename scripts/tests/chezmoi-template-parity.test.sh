#!/usr/bin/env bash
set -euo pipefail

echo "=== Chezmoi Parity Tests (via chezmoi verify) ==="

if ! command -v chezmoi &>/dev/null; then
  printf '  \033[33mSKIP\033[0m chezmoi not installed\n'
  exit 0
fi

if chezmoi verify 2>/dev/null; then
  printf '  \033[32mPASS\033[0m chezmoi verify — all managed files match source state\n'
else
  printf '  \033[31mFAIL\033[0m chezmoi verify — drift detected between source and deployed files\n'
  echo "Run 'chezmoi diff' to see details, then 'chezmoi apply' to reconcile."
  exit 1
fi
