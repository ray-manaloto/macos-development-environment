#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=scripts/lib/mde-platform.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mde-platform.sh"

mde_default_cache_root() {
  if mde_is_macos; then
    printf '%s/Library/Caches/com.ray-manaloto.mde' "$HOME"
  else
    printf '%s/.cache/mde' "$HOME"
  fi
}

mde_default_uv_cache_dir() {
  if mde_is_macos; then
    printf '%s/Library/Caches/uv' "$HOME"
  else
    printf '%s/.cache/uv' "$HOME"
  fi
}

mde_default_pipx_home() {
  printf '%s/.local/pipx' "$HOME"
}

mde_default_pipx_bin_dir() {
  printf '%s/.local/bin' "$HOME"
}

mde_default_bun_install_dir() {
  printf '%s/.bun' "$HOME"
}

mde_default_go_cache_dir() {
  if mde_is_macos; then
    printf '%s/Library/Caches/go-build' "$HOME"
  else
    printf '%s/.cache/go-build' "$HOME"
  fi
}

mde_default_go_mod_cache_dir() {
  printf '%s/go/pkg/mod' "$HOME"
}

mde_default_cargo_home() {
  printf '%s/.cargo' "$HOME"
}

mde_default_rustup_home() {
  printf '%s/.rustup' "$HOME"
}

mde_default_cache_dirs() {
  printf '%s\n' \
    "$(mde_default_cache_root)" \
    "$(mde_default_uv_cache_dir)" \
    "$(mde_default_pipx_home)" \
    "$(mde_default_pipx_bin_dir)" \
    "$(mde_default_bun_install_dir)" \
    "$(mde_default_go_cache_dir)" \
    "$(mde_default_go_mod_cache_dir)" \
    "$(mde_default_cargo_home)" \
    "$(mde_default_rustup_home)"
}

mde_export_cache_policy_env() {
  export MDE_CACHE_ROOT="${MDE_CACHE_ROOT:-$(mde_default_cache_root)}"
  export UV_CACHE_DIR="${UV_CACHE_DIR:-$(mde_default_uv_cache_dir)}"
  export PIPX_HOME="${PIPX_HOME:-$(mde_default_pipx_home)}"
  export PIPX_BIN_DIR="${PIPX_BIN_DIR:-$(mde_default_pipx_bin_dir)}"
  export BUN_INSTALL="${BUN_INSTALL:-$(mde_default_bun_install_dir)}"
  export GOCACHE="${GOCACHE:-$(mde_default_go_cache_dir)}"
  export GOMODCACHE="${GOMODCACHE:-$(mde_default_go_mod_cache_dir)}"
  export CARGO_HOME="${CARGO_HOME:-$(mde_default_cargo_home)}"
  export RUSTUP_HOME="${RUSTUP_HOME:-$(mde_default_rustup_home)}"
}

mde_prepare_cache_dirs() {
  local dir
  mde_export_cache_policy_env
  while IFS= read -r dir; do
    [[ -n "$dir" ]] || continue
    mkdir -p "$dir" 2>/dev/null || true
  done < <(mde_default_cache_dirs)
}

mde_cache_policy_env_report() {
  mde_export_cache_policy_env
  cat <<EOF
MDE_CACHE_ROOT=$MDE_CACHE_ROOT
UV_CACHE_DIR=$UV_CACHE_DIR
PIPX_HOME=$PIPX_HOME
PIPX_BIN_DIR=$PIPX_BIN_DIR
BUN_INSTALL=$BUN_INSTALL
GOCACHE=$GOCACHE
GOMODCACHE=$GOMODCACHE
CARGO_HOME=$CARGO_HOME
RUSTUP_HOME=$RUSTUP_HOME
EOF
}
