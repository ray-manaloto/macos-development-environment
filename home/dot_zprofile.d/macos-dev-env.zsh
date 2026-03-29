#!/usr/bin/env sh
# Managed by macos-development-environment.

remove_path() {
  case ":$PATH:" in
    *":$1:"*) PATH=":$PATH:"; PATH="${PATH//:$1:/:}"; PATH="${PATH#:}"; PATH="${PATH%:}" ;;
  esac
}

add_path_front() {
  remove_path "$1"
  PATH="$1:$PATH"
}

if [ -d "$HOME/.local/bin" ]; then
  add_path_front "$HOME/.local/bin"
fi

if [ -d "$HOME/.local/share/mde/bin" ]; then
  add_path_front "$HOME/.local/share/mde/bin"
fi

if [ -d "$HOME/.local/share/mise/bin" ]; then
  add_path_front "$HOME/.local/share/mise/bin"
fi

if [ -d "$HOME/.local/share/mise/shims" ]; then
  add_path_front "$HOME/.local/share/mise/shims"
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

export MISE_ENV_CACHE="${MISE_ENV_CACHE:-1}"
export FNOX_CONFIG_DIR="${FNOX_CONFIG_DIR:-$HOME/.config/fnox}"
export FNOX_AGE_KEY_FILE="${FNOX_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"
export SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$FNOX_AGE_KEY_FILE}"

if [ -z "${MDE_PLATFORM:-}" ]; then
  if [ -n "${DEVCONTAINER:-}" ] || [ -n "${CODESPACES:-}" ]; then
    MDE_PLATFORM="devcontainer"
  elif [ -f /.dockerenv ]; then
    MDE_PLATFORM="linux"
  elif [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
    MDE_PLATFORM="macos"
  else
    MDE_PLATFORM="linux"
  fi
fi
export MDE_PLATFORM

if [ -z "${UV_CACHE_DIR:-}" ]; then
  if [ "$MDE_PLATFORM" = "macos" ]; then
    UV_CACHE_DIR="$HOME/Library/Caches/uv"
  else
    UV_CACHE_DIR="$XDG_CACHE_HOME/uv"
  fi
fi
export UV_CACHE_DIR

if [ -z "${GOBIN:-}" ]; then
  GOBIN="$HOME/.local/bin"
fi
export GOBIN

if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate zsh --shims)"
  export MDE_MISE_ACTIVATED=1
  export MDE_MISE_ACTIVATED_MODE="shims"
fi

export PATH
