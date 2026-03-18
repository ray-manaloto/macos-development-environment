#!/usr/bin/env zsh
# Managed by macos-development-environment.
# Platform-specific overlays only. Secrets load through mise + fnox.

if [[ "$MDE_PLATFORM" == "devcontainer" || "$MDE_PLATFORM" == "linux" ]]; then
  export MDE_REMOTE_ENV="${MDE_REMOTE_ENV:-1}"
fi

if [[ "$MDE_PLATFORM" == "devcontainer" ]]; then
  export ZSH_DISABLE_COMPFIX="${ZSH_DISABLE_COMPFIX:-true}"
fi
