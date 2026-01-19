#!/usr/bin/env zsh
# Managed by macos-development-environment.
# Enable with: MDE_USE_LLVM=1

if [[ "${MDE_USE_LLVM:-0}" != "1" ]]; then
  return 0
fi

export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/llvm/lib/pkgconfig"
export CC=clang
export CXX=clang++
