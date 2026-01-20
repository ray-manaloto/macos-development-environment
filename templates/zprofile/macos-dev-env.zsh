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

if [ -d "$HOME/.local/share/mise/bin" ]; then
  add_path_front "$HOME/.local/share/mise/bin"
fi

if [ -d "$HOME/.local/share/mise/shims" ]; then
  add_path_front "$HOME/.local/share/mise/shims"
fi

if [ -z "${UV_CACHE_DIR:-}" ]; then
  UV_CACHE_DIR="$HOME/Library/Caches/uv"
fi
export UV_CACHE_DIR

if [ -z "${GOBIN:-}" ]; then
  GOBIN="$HOME/.local/bin"
fi
export GOBIN

export PATH
