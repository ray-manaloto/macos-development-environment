#!/usr/bin/env bash
# Managed by macos-development-environment.
set -euo pipefail

profile="${MDE_FABRIC_PROFILE:-anthropic}"
config_dir="${MDE_FABRIC_CONFIG_DIR:-$HOME/.config/fabric}"
bin_dir="${MDE_FABRIC_BIN_DIR:-$HOME/.local/share/mde/bin}"

self_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

link_profile() {
  if [[ -z "$profile" ]]; then
    return 0
  fi

  case "$profile" in
    default|main|base)
      return 0
      ;;
  esac

  local profile_env="$config_dir/.env.$profile"
  if [[ -f "$profile_env" ]]; then
    ln -sfn "$profile_env" "$config_dir/.env"
  fi
}

resolve_fabric() {
  if [[ -n "${MDE_FABRIC_BIN:-}" && -x "${MDE_FABRIC_BIN}" ]]; then
    printf '%s\n' "$MDE_FABRIC_BIN"
    return 0
  fi

  if [[ -x "$bin_dir/fabric" ]]; then
    printf '%s\n' "$bin_dir/fabric"
    return 0
  fi

  local entry=""
  local candidate=""
  IFS=':' read -r -a entries <<< "$PATH"
  for entry in "${entries[@]}"; do
    candidate="$entry/fabric"
    if [[ "$candidate" == "$self_path" ]]; then
      continue
    fi
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

link_profile

if [[ "$profile" == "anthropic" ]]; then
  unset OPENAI_API_KEY
fi

fabric_bin="$(resolve_fabric || true)"
if [[ -z "$fabric_bin" ]]; then
  echo "fabric CLI not found. Install via scripts/install-agent-stack.sh." >&2
  exit 1
fi

exec "$fabric_bin" "$@"
