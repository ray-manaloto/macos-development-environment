#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MDE_ZSH_BENCH_REPO_URL:-https://github.com/romkatv/zsh-bench.git}"
INSTALL_DIR="${MDE_ZSH_BENCH_INSTALL_DIR:-$HOME/.local/share/mde/tools/zsh-bench}"
REF="${MDE_ZSH_BENCH_REF:-}"

usage() {
  cat <<'EOF'
Usage: scripts/install-zsh-bench.sh [options]

Options:
  --repo-url <url>      Clone/fetch source repository.
  --install-dir <dir>   Managed checkout directory.
  --ref <ref>           Optional git ref to checkout after install/update.
  -h, --help            Show this help text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$INSTALL_DIR")"

if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" fetch --tags origin
else
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

if [[ -n "$REF" ]]; then
  git -C "$INSTALL_DIR" checkout "$REF"
else
  git -C "$INSTALL_DIR" pull --ff-only >/dev/null 2>&1 || true
fi

[[ -x "$INSTALL_DIR/zsh-bench" ]] || {
  printf 'error: expected executable at %s/zsh-bench\n' "$INSTALL_DIR" >&2
  exit 1
}

printf 'installed=%s\n' "$INSTALL_DIR"
printf 'binary=%s\n' "$INSTALL_DIR/zsh-bench"
if [[ -x "$INSTALL_DIR/dbg/timeline" ]]; then
  printf 'timeline=%s\n' "$INSTALL_DIR/dbg/timeline"
fi
