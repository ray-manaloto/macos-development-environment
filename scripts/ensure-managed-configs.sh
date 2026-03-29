#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/templates"
CHEZMOI_SOURCE="${MDE_CHEZMOI_SOURCE:-$REPO_ROOT/home}"
MANAGED_MARKER="Managed by macos-development-environment"
MODE="apply"
USE_CHEZMOI="${MDE_USE_CHEZMOI:-1}"
DRIFT=0

chezmoi_fallback_error() {
  local err_file="$1"
  grep -Eqi "not trusted|error parsing config file|source state.+not initialized|run.*chezmoi init|config file.+not found" "$err_file"
}

usage() {
  cat <<'USAGE'
Usage: ensure-managed-configs.sh [--check|--diff] [--no-chezmoi] [--legacy]

  --check, --diff  Show drift only; no file writes.
  --no-chezmoi     Skip chezmoi and use legacy sync.
  --legacy         Force legacy sync mode.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --check|--diff)
      MODE="check"
      ;;
    --no-chezmoi|--legacy)
      USE_CHEZMOI="0"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 1
      ;;
  esac
done

sync_file() {
  local src="$1"
  local dest="$2"
  local dest_dir

  if [[ ! -f "$src" ]]; then
    echo "template missing: $src" >&2
    return 1
  fi

  if [[ "$MODE" == "check" ]]; then
    if [[ ! -f "$dest" ]]; then
      echo "drift: missing file $dest" >&2
      DRIFT=1
      return 0
    fi
    if ! diff -q "$src" "$dest" >/dev/null 2>&1; then
      echo "drift: file differs $dest" >&2
      DRIFT=1
    fi
    return 0
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

  if [[ "$MODE" == "check" ]]; then
    if [[ ! -f "$dest" ]]; then
      echo "drift: missing wrapper $dest" >&2
      DRIFT=1
      return 0
    fi
    return 0
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

  if [[ "$MODE" == "check" ]]; then
    if [[ -f "$zprofile" ]] && grep -q "macos-dev-env.zsh" "$zprofile"; then
      return 0
    fi
    echo "drift: ~/.zprofile missing include for macos-dev-env.zsh" >&2
    DRIFT=1
    return 0
  fi

  if [[ -f "$zprofile" ]] && grep -q "macos-dev-env.zsh" "$zprofile"; then
    return 0
  fi

  cat <<'EOT' >> "$zprofile"

# Managed by macos-development-environment
if [ -f "$HOME/.zprofile.d/macos-dev-env.zsh" ]; then
  . "$HOME/.zprofile.d/macos-dev-env.zsh"
fi
EOT
}

sync_bun_completion() {
  local bun_comp_dir="$HOME/.oh-my-zsh/custom/completions"
  local bun_comp_src="$HOME/.bun/_bun"

  if [[ ! -f "$bun_comp_src" ]]; then
    return 0
  fi

  if [[ "$MODE" == "check" ]]; then
    if [[ ! -L "$bun_comp_dir/_bun" ]]; then
      echo "drift: missing bun completion symlink at $bun_comp_dir/_bun" >&2
      DRIFT=1
    fi
    return 0
  fi

  mkdir -p "$bun_comp_dir"
  ln -sfn "$bun_comp_src" "$bun_comp_dir/_bun"
}

sync_local_override() {
  local src="$1"
  local dest="$2"
  local dest_dir

  if [[ ! -f "$src" ]]; then
    echo "template missing: $src" >&2
    return 1
  fi

  if [[ "$MODE" == "check" ]]; then
    if [[ ! -f "$dest" ]]; then
      echo "drift: missing local override file $dest" >&2
      DRIFT=1
    fi
    return 0
  fi

  if [[ -f "$dest" ]]; then
    return 0
  fi

  dest_dir="$(dirname "$dest")"
  mkdir -p "$dest_dir"
  cp "$src" "$dest"
}

run_chezmoi() {
  if [[ "$USE_CHEZMOI" != "1" ]]; then
    return 1
  fi

  if ! command -v chezmoi >/dev/null 2>&1; then
    echo "chezmoi not found; falling back to legacy sync." >&2
    return 1
  fi

  if [[ ! -d "$CHEZMOI_SOURCE" ]]; then
    echo "chezmoi source not found: $CHEZMOI_SOURCE; falling back to legacy sync." >&2
    return 1
  fi

  if [[ "$MODE" == "check" ]]; then
    local diff_out diff_err
    diff_out="$(mktemp)"
    diff_err="$(mktemp)"
    if chezmoi diff --source "$CHEZMOI_SOURCE" >"$diff_out" 2>"$diff_err"; then
      rm -f "$diff_out" "$diff_err"
      echo "chezmoi drift: clean"
      return 0
    fi
    if chezmoi_fallback_error "$diff_err"; then
      rm -f "$diff_out" "$diff_err"
      echo "chezmoi unavailable in check mode; falling back to legacy sync check." >&2
      return 1
    fi
    rm -f "$diff_out" "$diff_err"
    echo "chezmoi drift: changes detected" >&2
    DRIFT=1
    return 0
  fi

  local apply_err
  apply_err="$(mktemp)"
  if chezmoi apply --force --no-tty --source "$CHEZMOI_SOURCE" 2>"$apply_err"; then
    rm -f "$apply_err"
    return 0
  fi

  if chezmoi_fallback_error "$apply_err"; then
    rm -f "$apply_err"
    echo "chezmoi unavailable in apply mode; falling back to legacy sync apply." >&2
    return 1
  fi

  cat "$apply_err" >&2
  rm -f "$apply_err"
  echo "chezmoi apply failed with non-fallback error." >&2
  exit 1
}

legacy_sync() {
  sync_file "$TEMPLATE_DIR/oh-my-zsh/10-mde-core.zsh" \
    "$HOME/.oh-my-zsh/custom/10-mde-core.zsh"
  sync_file "$TEMPLATE_DIR/oh-my-zsh/15-mde-platform.zsh" \
    "$HOME/.oh-my-zsh/custom/15-mde-platform.zsh"
  sync_file "$TEMPLATE_DIR/oh-my-zsh/20-mde-aliases.zsh" \
    "$HOME/.oh-my-zsh/custom/20-mde-aliases.zsh"
  sync_file "$TEMPLATE_DIR/oh-my-zsh/90-starship.zsh" \
    "$HOME/.oh-my-zsh/custom/90-starship.zsh"
  sync_local_override "$TEMPLATE_DIR/oh-my-zsh/99-local.zsh" \
    "$HOME/.oh-my-zsh/custom/99-local.zsh"

  # Backward compatibility wrappers.
  sync_file "$TEMPLATE_DIR/oh-my-zsh/macos-env.zsh" \
    "$HOME/.oh-my-zsh/custom/macos-env.zsh"
  sync_file "$TEMPLATE_DIR/oh-my-zsh/aliases.zsh" \
    "$HOME/.oh-my-zsh/custom/aliases.zsh"
  sync_file "$TEMPLATE_DIR/oh-my-zsh/llvm.zsh" \
    "$HOME/.oh-my-zsh/custom/llvm.zsh"

  sync_file "$TEMPLATE_DIR/tmux.conf" "$HOME/.tmux.conf"
  sync_file "$TEMPLATE_DIR/zprofile/macos-dev-env.zsh" \
    "$HOME/.zprofile.d/macos-dev-env.zsh"

  if [[ "$MODE" != "check" ]]; then
    local legacy_claude_wrapper="$HOME/.local/bin/claude"
    if [[ -f "$legacy_claude_wrapper" ]] && grep -q "$MANAGED_MARKER" "$legacy_claude_wrapper"; then
      rm -f "$legacy_claude_wrapper"
    fi

    local legacy_gemini_wrapper="$HOME/.local/bin/gemini"
    if [[ -f "$legacy_gemini_wrapper" ]]; then
      if grep -q "$MANAGED_MARKER" "$legacy_gemini_wrapper" \
        || grep -q "@google/gemini-cli/dist/index.js" "$legacy_gemini_wrapper"; then
        rm -f "$legacy_gemini_wrapper"
      fi
    fi
  fi

}

post_sync() {
  sync_local_override "$TEMPLATE_DIR/oh-my-zsh/99-local.zsh" \
    "$HOME/.oh-my-zsh/custom/99-local.zsh"
  sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh" \
    "$HOME/.local/bin/langsmith-fetch"
  sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh" \
    "$HOME/.local/bin/langsmith-migrator"
  sync_exec "$REPO_ROOT/scripts/langsmith-wrapper.sh" \
    "$HOME/.local/bin/langsmith-mcp-server"
  sync_exec "$REPO_ROOT/scripts/fabric-wrapper.sh" \
    "$HOME/.local/bin/fabric"
  sync_bun_completion
  ensure_zprofile_include
}

if run_chezmoi; then
  :
else
  legacy_sync
fi
post_sync

if [[ "$MODE" == "check" ]]; then
  if [[ "$DRIFT" -eq 0 ]]; then
    echo "Managed configs: clean"
    exit 0
  fi
  echo "Managed configs: drift detected" >&2
  exit 1
fi

echo "Managed configs synced."
