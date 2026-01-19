#!/usr/bin/env zsh
# Managed by macos-development-environment.
# Put local overrides in a separate custom file to avoid conflicts.

# Ensure ~/.local/bin is available for mise/uv tools.
if [ -f "$HOME/.local/bin/env" ]; then
  . "$HOME/.local/bin/env"
fi

# mise (preferred runtime manager).
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate zsh)"
fi

# bun
export BUN_INSTALL="$HOME/.bun"
if [ -s "$BUN_INSTALL/_bun" ]; then
  source "$BUN_INSTALL/_bun"
fi

# GitHub token exports (best-effort).
if command -v gh >/dev/null 2>&1; then
  export GITHUB_TOKEN="$(gh auth token 2>/dev/null)"
  export GITHUB_MCP_PAT="$GITHUB_TOKEN"
fi

# Python toolchain behavior
export UV_NO_MANAGED_PYTHON=1

# PATH ordering (mise > bun > pixi > uv > brew).
typeset -U path
path_rest=($path)
path_rest=(${path_rest:#$HOME/.local/share/mise/shims})
path_rest=(${path_rest:#$HOME/.local/share/mise/bin})
path_rest=(${path_rest:#$HOME/.bun/bin})
path_rest=(${path_rest:#$HOME/.pixi/bin})
path_rest=(${path_rest:#$HOME/.amp/bin})
path_rest=(${path_rest:#$HOME/.antigravity/antigravity/bin})
path_rest=(${path_rest:#$HOME/.local/bin})
path_rest=(${path_rest:#$HOME/.oh-my-zsh/custom/bin})
path_rest=(${path_rest:#/opt/homebrew/opt/curl/bin})
path=(
  "$HOME/.local/share/mise/shims"
  "$HOME/.local/share/mise/bin"
  "$HOME/.bun/bin"
  "$HOME/.pixi/bin"
  "$HOME/.amp/bin"
  "$HOME/.antigravity/antigravity/bin"
  "$HOME/.local/bin"
  "$HOME/.oh-my-zsh/custom/bin"
  "/opt/homebrew/opt/curl/bin"
  $path_rest
)
unset path_rest
