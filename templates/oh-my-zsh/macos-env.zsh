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

# UV cache directory
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"

# Go tool installs
export GOBIN="${GOBIN:-$HOME/.local/bin}"

# Python toolchain behavior
export UV_NO_MANAGED_PYTHON=1

# PATH ordering (mise > local wrappers > bun > pixi > uv > brew).
typeset -U path
path_rest=($path)
path_rest=(${path_rest:#$HOME/.local/share/mise/shims})
path_rest=(${path_rest:#$HOME/.local/share/mise/bin})
path_rest=(${path_rest:#$HOME/.local/bin})
path_rest=(${path_rest:#$HOME/.bun/bin})
path_rest=(${path_rest:#$HOME/.pixi/bin})
path_rest=(${path_rest:#$HOME/.amp/bin})
path_rest=(${path_rest:#$HOME/.antigravity/antigravity/bin})
path_rest=(${path_rest:#$HOME/.oh-my-zsh/custom/bin})
path_rest=(${path_rest:#/opt/google-cloud-sdk/bin})
path_rest=(${path_rest:#/opt/homebrew/opt/curl/bin})
path=(
  "$HOME/.local/share/mise/shims"
  "$HOME/.local/share/mise/bin"
  "$HOME/.local/bin"
  "$HOME/.bun/bin"
  "$HOME/.pixi/bin"
  "$HOME/.amp/bin"
  "$HOME/.antigravity/antigravity/bin"
  "$HOME/.oh-my-zsh/custom/bin"
  "/opt/google-cloud-sdk/bin"
  "/opt/homebrew/opt/curl/bin"
  $path_rest
)
unset path_rest

# Secrets from Keychain (set MDE_AUTOLOAD_SECRETS=0 to disable).
mde_load_keychain_secret() {
  local label="$1"
  if command -v security >/dev/null 2>&1; then
    security find-generic-password -s "$label" -w 2>/dev/null || true
  fi
}

mde_export_secret() {
  local label="$1"
  local env_var="$2"
  if [[ -n "${(P)env_var:-}" ]]; then
    return 0
  fi
  local value=""
  value="$(mde_load_keychain_secret "$label")"
  if [[ -n "$value" ]]; then
    export "$env_var"="$value"
  fi
}

if [[ "${MDE_AUTOLOAD_SECRETS:-1}" == "1" ]]; then
  mde_export_secret "mde-openai-api-key" OPENAI_API_KEY
  mde_export_secret "mde-anthropic-api-key" ANTHROPIC_API_KEY
  mde_export_secret "mde-gemini-api-key" GEMINI_API_KEY
  mde_export_secret "mde-langsmith-api-key" LANGSMITH_API_KEY
  mde_export_secret "mde-langsmith-workspace-id" LANGSMITH_WORKSPACE_ID
  mde_export_secret "mde-github-token" GITHUB_TOKEN
  mde_export_secret "mde-github-mcp-pat" GITHUB_MCP_PAT
fi

