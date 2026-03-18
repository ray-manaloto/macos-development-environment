#!/usr/bin/env bash
set -euo pipefail
# Tools migrated to mise declarative config (~/.config/mise/config.toml).
# This script now only syncs langsmith wrapper scripts.

export GIT_TERMINAL_PROMPT=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"
# shellcheck source=scripts/lib/mde-cache-policy.sh
source "$SCRIPT_DIR/lib/mde-cache-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
mde_prepare_cache_dirs
mde_block_legacy_installer_in_agent_context "$(basename "$0")" "mise run mde:migrate:global-tools -- --dry-run"

sync_langsmith_wrappers() {
  local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local repo_root="$(cd "$script_dir/.." && pwd)"
  local wrapper="$repo_root/scripts/langsmith-wrapper.sh"
  local dest_dir="$HOME/.local/bin"

  if [[ ! -f "$wrapper" ]]; then
    echo "langsmith wrapper missing: $wrapper" >&2
    return 1
  fi

  mkdir -p "$dest_dir"
  install -m 0755 "$wrapper" "$dest_dir/langsmith-fetch"
  install -m 0755 "$wrapper" "$dest_dir/langsmith-migrator"
  install -m 0755 "$wrapper" "$dest_dir/langsmith-mcp-server"
}

sync_langsmith_wrappers
printf "\nLangsmith wrappers synced.\n"
