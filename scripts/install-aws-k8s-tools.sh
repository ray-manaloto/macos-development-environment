#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: install-aws-k8s-tools.sh [--no-brew] [--optional=0|1] [--allow-sudo]

Installs core AWS + Kubernetes CLI tools. Prefers mise, falls back to Homebrew.

Options:
  --no-brew     Disable Homebrew fallback installs.
  --optional    Enable optional tools (default: 1).
  --allow-sudo Allow sudo-required installs when cached credentials exist.
USAGE
}

use_brew=1
include_optional=1
allow_sudo=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-brew)
      use_brew=0
      ;;
    --optional=0)
      include_optional=0
      ;;
    --optional=1)
      include_optional=1
      ;;
    --allow-sudo)
      allow_sudo=1
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

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

install_with_mise() {
  local tool="$1"

  if ! command -v mise >/dev/null 2>&1; then
    return 1
  fi

  if mise install -q "${tool}@latest" >/dev/null 2>&1; then
    mise use -g "${tool}@latest" >/dev/null 2>&1 || true
    mise reshim >/dev/null 2>&1 || true
    return 0
  fi

  return 1
}

install_with_brew() {
  local formula="$1"

  if [[ "$use_brew" -ne 1 ]]; then
    return 1
  fi
  if ! command -v brew >/dev/null 2>&1; then
    return 1
  fi

  if brew list --formula "$formula" >/dev/null 2>&1; then
    return 0
  fi

  brew install "$formula"
}

sudo_ready() {
  if [[ "$allow_sudo" -ne 1 ]]; then
    return 1
  fi
  if sudo -n true 2>/dev/null; then
    return 0
  fi
  return 1
}

install_tool() {
  local tool="$1"
  local cmd="$2"
  local brew_formula="$3"
  local requires_sudo="${4:-0}"

  if [[ "$requires_sudo" == "1" && "$allow_sudo" -ne 1 ]]; then
    log "skip: $tool requires sudo (use --allow-sudo after caching credentials)"
    return 0
  fi

  if [[ "$requires_sudo" == "1" && ! sudo_ready ]]; then
    log "skip: $tool requires sudo but no cached credentials"
    return 0
  fi

  if command -v "$cmd" >/dev/null 2>&1; then
    log "ok: $cmd already installed"
    return 0
  fi

  if install_with_mise "$tool"; then
    if command -v "$cmd" >/dev/null 2>&1; then
      log "ok: installed $tool via mise"
      return 0
    fi
  fi

  if install_with_brew "$brew_formula"; then
    if command -v "$cmd" >/dev/null 2>&1; then
      log "ok: installed $tool via brew"
      return 0
    fi
  fi

  log "failed: $tool ($cmd)"
  return 1
}

setup_path

required=()
optional=()

required+=("awscli:aws:awscli")
required+=("kubectl:kubectl:kubernetes-cli")
required+=("helm:helm:helm")

optional+=("eksctl:eksctl:eksctl")
optional+=("k9s:k9s:k9s")
optional+=("kubectx:kubectx:kubectx")
optional+=("kubens:kubens:kubectx")
optional+=("stern:stern:stern")
optional+=("session-manager-plugin:session-manager-plugin:session-manager-plugin:1")

failures=0

log "Installing required AWS/Kubernetes tools."
for entry in "${required[@]}"; do
  IFS=':' read -r tool cmd brew_formula <<< "$entry"
  if ! install_tool "$tool" "$cmd" "$brew_formula"; then
    failures=1
  fi
done

if [[ "$include_optional" -eq 1 ]]; then
  log "Installing optional AWS/Kubernetes tools."
  for entry in "${optional[@]}"; do
    IFS=':' read -r tool cmd brew_formula requires_sudo <<< "$entry"
    if ! install_tool "$tool" "$cmd" "$brew_formula" "${requires_sudo:-0}"; then
      log "optional: $tool missing"
    fi
  done
fi

if [[ "$failures" -ne 0 ]]; then
  log "Install completed with failures."
  exit 1
fi

log "AWS/Kubernetes tools installed."
