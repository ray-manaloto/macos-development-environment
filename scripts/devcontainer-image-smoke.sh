#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_TAG="${MDE_DEVCONTAINER_TEST_TAG:-mde-devcontainer:local}"
RUN_PLATFORM="${MDE_DEVCONTAINER_RUN_PLATFORM:-linux/amd64}"

docker run --rm \
  --platform "$RUN_PLATFORM" \
  --user vscode \
  -e HOME=/home/vscode \
  "$IMAGE_TAG" \
  bash -lc '
    set -euo pipefail
    for tool in bash zsh curl git jq rg mise; do
      command -v "$tool" >/dev/null
    done
    [[ "$(whoami)" == "vscode" ]]
    [[ -x "$HOME/.local/bin/mise" || -x "$HOME/.local/share/mise/bin/mise" ]]
    [[ -d "$HOME/.oh-my-zsh/custom" ]]
    [[ -d "$HOME/.oh-my-zsh/custom/completions" ]]
    mise --version >/dev/null
  '
