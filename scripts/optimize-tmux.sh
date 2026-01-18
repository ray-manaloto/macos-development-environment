#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_CONF="$SCRIPT_DIR/../templates/tmux.conf"
TMUX_FORCE_CONF="${TMUX_FORCE_CONF:-0}"
MANAGED_MARKER="Managed by macos-development-environment"

TMUX_INSTALL="${TMUX_INSTALL:-auto}"

install_tmux() {
  if [[ "$TMUX_INSTALL" == "pixi" ]]; then
    if command -v pixi >/dev/null 2>&1; then
      pixi global install tmux
      return 0
    fi
    echo "pixi not found; cannot install tmux via pixi" >&2
    return 1
  fi

  if command -v brew >/dev/null 2>&1; then
    brew install tmux
    return 0
  fi

  if command -v pixi >/dev/null 2>&1; then
    pixi global install tmux
    return 0
  fi

  echo "tmux install failed: brew or pixi required" >&2
  return 1
}

install_skypilot() {
  if ! command -v uv >/dev/null 2>&1; then
    if command -v curl >/dev/null 2>&1; then
      curl -LsSf https://astral.sh/uv/install.sh | sh
      export PATH="$HOME/.local/bin:$PATH"
    fi
  fi

  if command -v uv >/dev/null 2>&1; then
    uv tool install --upgrade "skypilot[aws]"
    return 0
  fi
  if command -v pip >/dev/null 2>&1; then
    pip install --upgrade "skypilot[aws]"
    return 0
  fi
  echo "skypilot install failed: uv or pip required" >&2
  return 1
}

install_tpm() {
  local tpm_dir="$HOME/.tmux/plugins/tpm"
  if [ ! -d "$tpm_dir" ]; then
    git clone https://github.com/tmux-plugins/tpm "$tpm_dir"
  fi
}

write_tmux_conf() {
  local conf="$HOME/.tmux.conf"
  local backup
  backup="${conf}.bak.$(date +%Y%m%d%H%M%S)"
  if [ -f "$conf" ]; then
    if [[ "$TMUX_FORCE_CONF" != "1" ]] && \
      ! grep -q "$MANAGED_MARKER" "$conf"; then
      echo "tmux.conf exists and is not managed; skipping (set TMUX_FORCE_CONF=1 to override)" >&2
      return 0
    fi
    cp "$conf" "$backup"
  fi

  if [[ -f "$TEMPLATE_CONF" ]]; then
    cp "$TEMPLATE_CONF" "$conf"
    return 0
  fi

  echo "tmux template not found at $TEMPLATE_CONF" >&2
  return 1
}

install_tmux
install_skypilot
install_tpm
write_tmux_conf

echo "tmux + skypilot setup complete."
echo "Open tmux and press prefix + I to install plugins."
