#!/usr/bin/env zsh
# Managed by macos-development-environment.
# LLVM/Clang toolchain is configured declaratively in mise [env]:
#   - PATH, CC, CXX, LDFLAGS, CPPFLAGS all set via mise config.toml
#   - This file only adds PKG_CONFIG_PATH (not supported by mise _.path)
#   - Set MDE_USE_LLVM=0 to disable the interactive-shell PKG_CONFIG_PATH

if [[ "${MDE_USE_LLVM:-1}" != "1" ]]; then
  return 0
fi

if [[ "${MDE_PLATFORM:-}" != "macos" ]]; then
  return 0
fi

# PKG_CONFIG_PATH is the only env var not handled by mise [env]
export PKG_CONFIG_PATH="/opt/homebrew/opt/llvm/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
