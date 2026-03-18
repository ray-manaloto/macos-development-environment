#!/usr/bin/env zsh
# Managed by macos-development-environment.
# Shared shell bootstrap for macOS + devcontainer/linux.

if [[ -n "${MDE_PLATFORM:-}" ]]; then
  case "${MDE_PLATFORM:l}" in
    darwin|macos) export MDE_PLATFORM="macos" ;;
    devcontainer) export MDE_PLATFORM="devcontainer" ;;
    container|linux) export MDE_PLATFORM="linux" ;;
  esac
fi

if [[ -z "${MDE_PLATFORM:-}" ]]; then
  if [[ -n "${DEVCONTAINER:-}" || -n "${CODESPACES:-}" ]]; then
    export MDE_PLATFORM="devcontainer"
  elif [[ -f /.dockerenv ]]; then
    export MDE_PLATFORM="linux"
  elif [[ "$(uname -s 2>/dev/null)" == "Darwin" ]]; then
    export MDE_PLATFORM="macos"
  else
    export MDE_PLATFORM="linux"
  fi
fi

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$HOME/.local/run}"
export ZSH_DATA_DIR="${ZSH_DATA_DIR:-$XDG_DATA_HOME/zsh}"
export ZSH_CACHE_DIR="${ZSH_CACHE_DIR:-$XDG_CACHE_HOME/zsh}"
export ZSH_COMPDUMP="${ZSH_COMPDUMP:-$ZSH_CACHE_DIR/.zcompdump-${ZSH_VERSION:-current}}"
export HISTFILE="${HISTFILE:-$ZSH_DATA_DIR/history}"

mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_RUNTIME_DIR" "$ZSH_DATA_DIR" "$ZSH_CACHE_DIR"

if [ -f "$HOME/.local/bin/env" ]; then
  . "$HOME/.local/bin/env"
fi

export MISE_ENV_CACHE="${MISE_ENV_CACHE:-1}"
export FNOX_CONFIG_DIR="${FNOX_CONFIG_DIR:-$HOME/.config/fnox}"
export FNOX_AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
export SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$FNOX_AGE_KEY_FILE}"

if command -v mise >/dev/null 2>&1 && [[ "${MDE_MISE_ACTIVATED_MODE:-}" != "interactive" ]]; then
  eval "$(mise activate zsh)"
  export MDE_MISE_ACTIVATED=1
  export MDE_MISE_ACTIVATED_MODE="interactive"
fi

export BUN_INSTALL="$HOME/.bun"

if [[ -z "${UV_CACHE_DIR:-}" ]]; then
  if [[ "$MDE_PLATFORM" == "macos" ]]; then
    export UV_CACHE_DIR="$HOME/Library/Caches/uv"
  else
    export UV_CACHE_DIR="$XDG_CACHE_HOME/uv"
  fi
fi

export GOBIN="${GOBIN:-$HOME/.local/bin}"
export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"

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
path_rest=(${path_rest:#/Applications/Codex.app/Contents/Resources})

path=(
  "$HOME/.local/share/mise/shims"
  "$HOME/.local/share/mise/bin"
  "$HOME/.local/bin"
  "$HOME/.bun/bin"
  "$HOME/.pixi/bin"
  "$HOME/.amp/bin"
  "$HOME/.antigravity/antigravity/bin"
  "$HOME/.oh-my-zsh/custom/bin"
)

if [[ "$MDE_PLATFORM" == "macos" ]]; then
  path+=("/opt/google-cloud-sdk/bin" "/opt/homebrew/opt/curl/bin")
fi

path+=($path_rest)
unset path_rest
