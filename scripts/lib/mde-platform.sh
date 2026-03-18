#!/usr/bin/env bash
set -euo pipefail

mde_detect_platform() {
  local explicit="${MDE_PLATFORM:-}"
  if [[ -n "$explicit" ]]; then
    case "${explicit,,}" in
      macos|darwin)
        printf 'macos'
        return 0
        ;;
      devcontainer)
        printf 'devcontainer'
        return 0
        ;;
      linux|container)
        printf 'linux'
        return 0
        ;;
    esac
  fi

  if [[ -n "${DEVCONTAINER:-}" || -n "${CODESPACES:-}" ]]; then
    printf 'devcontainer'
    return 0
  fi

  if [[ -f /.dockerenv ]]; then
    printf 'linux'
    return 0
  fi

  case "$(uname -s 2>/dev/null || true)" in
    Darwin)
      printf 'macos'
      ;;
    Linux)
      printf 'linux'
      ;;
    *)
      printf 'linux'
      ;;
  esac
}

mde_is_macos() {
  [[ "${MDE_PLATFORM:-$(mde_detect_platform)}" == "macos" ]]
}

mde_is_devcontainer() {
  [[ "${MDE_PLATFORM:-$(mde_detect_platform)}" == "devcontainer" ]]
}

mde_is_linux() {
  local platform="${MDE_PLATFORM:-$(mde_detect_platform)}"
  [[ "$platform" == "linux" || "$platform" == "devcontainer" ]]
}

mde_default_uv_cache_dir() {
  if mde_is_macos; then
    printf '%s/Library/Caches/uv' "$HOME"
  else
    printf '%s/.cache/uv' "$HOME"
  fi
}

mde_default_log_dir() {
  if mde_is_macos; then
    printf '%s/Library/Logs/com.ray-manaloto.macos-dev-maintenance' "$HOME"
  else
    printf '%s/.local/state/macos-dev-maintenance' "$HOME"
  fi
}
