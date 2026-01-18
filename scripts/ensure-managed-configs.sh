#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/templates"
MANAGED_MARKER="Managed by macos-development-environment"

sync_file() {
  local src="$1"
  local dest="$2"
  local dest_dir

  if [[ ! -f "$src" ]]; then
    echo "template missing: $src" >&2
    return 1
  fi

  dest_dir="$(dirname "$dest")"
  mkdir -p "$dest_dir"

  if [[ -f "$dest" ]] && ! grep -q "$MANAGED_MARKER" "$dest"; then
    echo "skipping unmanaged file: $dest" >&2
    return 0
  fi

  cp "$src" "$dest"
}

sync_file "$TEMPLATE_DIR/oh-my-zsh/macos-env.zsh" \
  "$HOME/.oh-my-zsh/custom/macos-env.zsh"
sync_file "$TEMPLATE_DIR/oh-my-zsh/aliases.zsh" \
  "$HOME/.oh-my-zsh/custom/aliases.zsh"
sync_file "$TEMPLATE_DIR/tmux.conf" "$HOME/.tmux.conf"

echo "Managed configs synced."
