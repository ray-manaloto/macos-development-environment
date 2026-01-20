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

sync_exec() {
  local src="$1"
  local dest="$2"
  local dest_dir

  if [[ ! -f "$src" ]]; then
    echo "wrapper missing: $src" >&2
    return 1
  fi

  dest_dir="$(dirname "$dest")"
  mkdir -p "$dest_dir"

  if [[ -f "$dest" ]] && ! grep -q "$MANAGED_MARKER" "$dest"; then
    if grep -q "mde-mcp-common.sh" "$dest"; then
      install -m 0755 "$src" "$dest"
      return 0
    fi
    echo "skipping unmanaged wrapper: $dest" >&2
    return 0
  fi

  install -m 0755 "$src" "$dest"
}

ensure_zprofile_include() {
  local zprofile="$HOME/.zprofile"

  if [[ -f "$zprofile" ]] && grep -q "macos-dev-env.zsh" "$zprofile"; then
    return 0
  fi

  cat <<'EOF' >> "$zprofile"

# Managed by macos-development-environment
if [ -f "$HOME/.zprofile.d/macos-dev-env.zsh" ]; then
  . "$HOME/.zprofile.d/macos-dev-env.zsh"
fi
EOF
}

sync_file "$TEMPLATE_DIR/oh-my-zsh/macos-env.zsh" \
  "$HOME/.oh-my-zsh/custom/macos-env.zsh"
sync_file "$TEMPLATE_DIR/oh-my-zsh/aliases.zsh" \
  "$HOME/.oh-my-zsh/custom/aliases.zsh"
sync_file "$TEMPLATE_DIR/oh-my-zsh/llvm.zsh" \
  "$HOME/.oh-my-zsh/custom/llvm.zsh"
sync_file "$TEMPLATE_DIR/tmux.conf" "$HOME/.tmux.conf"
sync_file "$TEMPLATE_DIR/zprofile/macos-dev-env.zsh" \
  "$HOME/.zprofile.d/macos-dev-env.zsh"

sync_exec "$REPO_ROOT/scripts/claude-wrapper.sh" \
  "$HOME/.local/bin/claude"

sync_exec "$REPO_ROOT/scripts/gemini-wrapper.sh" \
  "$HOME/.local/bin/gemini"

sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh" \
  "$HOME/.local/bin/langsmith-fetch"

sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh" \
  "$HOME/.local/bin/langsmith-migrator"

sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh"   "$HOME/.local/bin/langsmith-mcp-server"

fabric_dest="$HOME/.local/bin/fabric"
fabric_bin_dir="${MDE_FABRIC_BIN_DIR:-$HOME/.local/share/mde/bin}"

if [[ -f "$fabric_dest" && ! -L "$fabric_dest" ]]; then
  if ! grep -q "$MANAGED_MARKER" "$fabric_dest" 2>/dev/null; then
    mkdir -p "$fabric_bin_dir"
    if [[ ! -f "$fabric_bin_dir/fabric" ]]; then
      mv "$fabric_dest" "$fabric_bin_dir/fabric" 2>/dev/null || true
    fi
  fi
fi

sync_exec "$REPO_ROOT/scripts/fabric-wrapper.sh" \
  "$fabric_dest"

ensure_zprofile_include

echo "Managed configs synced."
