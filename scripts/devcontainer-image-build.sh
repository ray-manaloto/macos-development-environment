#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_TAG="${MDE_DEVCONTAINER_TEST_TAG:-mde-devcontainer:local}"
BUILD_PLATFORM="${MDE_DEVCONTAINER_BUILD_PLATFORM:-linux/amd64}"

"$REPO_ROOT/scripts/devcontainer-cleanup.sh"

docker buildx build \
  --platform "$BUILD_PLATFORM" \
  --file "$REPO_ROOT/.devcontainer/Dockerfile" \
  --tag "$IMAGE_TAG" \
  --load \
  "$REPO_ROOT/.devcontainer"

printf '%s\n' "$IMAGE_TAG"
