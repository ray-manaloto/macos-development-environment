#!/usr/bin/env bash
set -euo pipefail

if command -v mise >/dev/null 2>&1; then
  echo "## mise runtimes"
  mise ls --installed || true
  echo
fi

if command -v uv >/dev/null 2>&1; then
  echo "## uv tools"
  uv tool list || true
  echo
fi

if command -v pixi >/dev/null 2>&1; then
  echo "## pixi globals"
  pixi global list || true
  echo
fi

if command -v bun >/dev/null 2>&1; then
  echo "## bun globals"
  bun pm -g ls || true
  echo
fi

if command -v brew >/dev/null 2>&1; then
  echo "## homebrew formulae"
  brew list --formula || true
  echo
  echo "## homebrew casks"
  brew list --cask || true
  echo
fi

if command -v pipx >/dev/null 2>&1; then
  echo "## pipx"
  pipx list || true
  echo
fi
