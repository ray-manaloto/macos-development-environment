#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: setup-secrets-env.sh [--force] [--open]

Creates the global secrets env file used by macos-development-environment.
Defaults:
  MDE_ENV_FILE     ~/.config/macos-development-environment/secrets.env
  MDE_ENV_TEMPLATE templates/secrets.env.example

Options:
  --force   Overwrite existing file.
  --open    Open the file in $EDITOR after creation.
USAGE
}

force=0
open_editor=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      ;;
    --open)
      open_editor=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
 done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MDE_ENV_FILE="${MDE_ENV_FILE:-$HOME/.config/macos-development-environment/secrets.env}"
MDE_ENV_TEMPLATE="${MDE_ENV_TEMPLATE:-$repo_root/templates/secrets.env.example}"

if [[ -f "$MDE_ENV_FILE" && "$force" -ne 1 ]]; then
  echo "Secrets file already exists: $MDE_ENV_FILE" >&2
  echo "Use --force to overwrite." >&2
  exit 1
fi

mkdir -p "$(dirname "$MDE_ENV_FILE")"

if [[ -f "$MDE_ENV_TEMPLATE" ]]; then
  cp "$MDE_ENV_TEMPLATE" "$MDE_ENV_FILE"
else
  cat > "$MDE_ENV_FILE" <<'TEMPLATE'
# macos-development-environment secrets (do not commit real keys)
# Save as: ~/.config/macos-development-environment/secrets.env

OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# LangSmith (personal keys only need LANGSMITH_API_KEY)
LANGSMITH_API_KEY=lsv2-...
# LANGSMITH_WORKSPACE_ID=...  # only for service keys (tenant id)

GITHUB_TOKEN=ghp_...
GITHUB_MCP_PAT=ghp_...
TEMPLATE
fi

chmod 600 "$MDE_ENV_FILE" 2>/dev/null || true

echo "Created secrets file: $MDE_ENV_FILE"

if [[ "$open_editor" -eq 1 ]]; then
  "${EDITOR:-vi}" "$MDE_ENV_FILE"
fi
