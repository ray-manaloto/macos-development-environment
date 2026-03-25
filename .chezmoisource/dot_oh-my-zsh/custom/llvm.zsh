#!/usr/bin/env zsh
# Managed by macos-development-environment.
# Homebrew LLVM toolchain setup for interactive shells.
#
# mise [env] sets CC, CXX, LDFLAGS, CPPFLAGS, PKG_CONFIG_PATH — but mise
# --shims mode does NOT apply _.path to the interactive shell PATH.
# This file handles PATH prepend so `which clang` resolves to brew's LLVM.
#
# Set MDE_USE_LLVM=0 to disable.

if [[ "${MDE_USE_LLVM:-1}" != "1" ]]; then
  return 0
fi

if [[ "${MDE_PLATFORM:-}" != "macos" ]]; then
  return 0
fi

# Prepend brew LLVM to PATH (required because mise --shims doesn't apply _.path)
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
