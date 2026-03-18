#!/usr/bin/env bash
set -euo pipefail
# Tools migrated to mise declarative config (~/.config/mise/config.toml).
# This script now only handles: fabric install, gh-copilot extension, fabric env config.

export GIT_TERMINAL_PROMPT=0
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY="${PYO3_USE_ABI3_FORWARD_COMPATIBILITY:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"
# shellcheck source=scripts/lib/mde-cache-policy.sh
source "$SCRIPT_DIR/lib/mde-cache-policy.sh"
# shellcheck source=scripts/lib/mde-secrets.sh
source "$SCRIPT_DIR/lib/mde-secrets.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
mde_prepare_cache_dirs
mde_block_legacy_installer_in_agent_context "$(basename "$0")" "mise run mde:migrate:global-tools -- --dry-run"

INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-1}"

set_env_line() {
  local env_file="$1"
  local key="$2"
  local value="$3"
  local overwrite="$4"
  local tmp=""

  if [[ -z "$value" ]]; then
    return 1
  fi

  if [[ "$overwrite" == "1" ]]; then
    tmp="$(mktemp)"
    if [[ -f "$env_file" ]]; then
      grep -v "^${key}=" "$env_file" > "$tmp" || true
    fi
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
    mv "$tmp" "$env_file"
    chmod 600 "$env_file" 2>/dev/null || true
    return 0
  fi

  if grep -q "^${key}=" "$env_file" 2>/dev/null; then
    return 1
  fi

  printf '%s=%s\n' "$key" "$value" >> "$env_file"
  chmod 600 "$env_file" 2>/dev/null || true
  return 0
}

configure_fabric_env() {
  local setup="${MDE_FABRIC_SETUP:-1}"
  local overwrite="${MDE_FABRIC_OVERWRITE:-0}"
  local profile="${MDE_FABRIC_PROFILE:-anthropic}"
  local config_dir="${MDE_FABRIC_CONFIG_DIR:-$HOME/.config/fabric}"
  local env_file="${MDE_FABRIC_ENV_FILE:-}"
  local env_dir=""
  local wrote=0

  if [[ "$setup" != "1" ]]; then
    return 0
  fi

  if [[ -z "$env_file" ]]; then
    case "$profile" in
      ""|default|main|base)
        env_file="$config_dir/.env"
        ;;
      *)
        env_file="$config_dir/.env.$profile"
        ;;
    esac
  fi

  env_dir="$(dirname "$env_file")"
  mkdir -p "$env_dir" 2>/dev/null || true

  if [[ -e "$config_dir/.env" && ! -L "$config_dir/.env" && "$env_file" != "$config_dir/.env" ]]; then
    mv "$config_dir/.env" "$config_dir/.env.all" 2>/dev/null || true
  fi

  if [[ "$env_file" != "$config_dir/.env" ]]; then
    ln -sfn "$env_file" "$config_dir/.env"
  fi

  if [[ ! -f "$env_file" ]]; then
    : > "$env_file"
    chmod 600 "$env_file" 2>/dev/null || true
  fi

  local keys=()
  local value=""
  case "$profile" in
    anthropic)
      keys=(ANTHROPIC_API_KEY ANTHROPIC_USE_OAUTH_LOGIN)
      ;;
    gemini)
      keys=(GEMINI_API_KEY)
      ;;
    openai)
      keys=(OPENAI_API_KEY)
      ;;
    all|full)
      keys=(OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY GROQ_API_KEY MISTRAL_API_KEY DEEPSEEK_API_KEY SILICON_API_KEY GROKAI_API_KEY LM_STUDIO_API_BASE_URL OLLAMA_URL ANTHROPIC_USE_OAUTH_LOGIN)
      ;;
    *)
      keys=(ANTHROPIC_API_KEY)
      ;;
  esac

  for key in "${keys[@]}"; do
    mde_load_secrets
    value="${!key:-}"
    if set_env_line "$env_file" "$key" "$value" "$overwrite"; then
      wrote=1
    fi
  done

  local default_vendor="${MDE_FABRIC_DEFAULT_VENDOR:-}"
  local default_model="${MDE_FABRIC_DEFAULT_MODEL:-}"
  local default_context="${MDE_FABRIC_DEFAULT_MODEL_CONTEXT_LENGTH:-}"

  if set_env_line "$env_file" "DEFAULT_VENDOR" "$default_vendor" "$overwrite"; then
    wrote=1
  fi
  if set_env_line "$env_file" "DEFAULT_MODEL" "$default_model" "$overwrite"; then
    wrote=1
  fi
  if set_env_line "$env_file" "DEFAULT_MODEL_CONTEXT_LENGTH" "$default_context" "$overwrite"; then
    wrote=1
  fi

  if [[ "$wrote" == "1" ]]; then
    echo "[fabric] updated config at $env_file"
  fi
}

install_fabric() {
  if ! command -v curl >/dev/null 2>&1; then
    echo "missing curl for fabric install" >&2
    return 1
  fi
  local bin_dir="${MDE_FABRIC_BIN_DIR:-$HOME/.local/share/mde/bin}"
  local legacy_bin="$HOME/.local/bin/fabric"

  mkdir -p "$bin_dir" 2>/dev/null || true
  export PATH="$bin_dir:$PATH"

  if [[ -f "$legacy_bin" && ! -L "$legacy_bin" ]]; then
    if ! grep -q "Managed by macos-development-environment" "$legacy_bin" 2>/dev/null; then
      if [[ ! -f "$bin_dir/fabric" ]]; then
        mv "$legacy_bin" "$bin_dir/fabric" 2>/dev/null || true
      fi
    fi
  fi

  curl -fsSL https://raw.githubusercontent.com/danielmiessler/fabric/main/scripts/installer/install.sh | \
    INSTALL_DIR="$bin_dir" bash
}

if [[ "$INCLUDE_OPTIONAL" == "1" ]]; then
  if command -v gh >/dev/null 2>&1; then
    gh extension install github/gh-copilot >/dev/null 2>&1 || \
      gh extension upgrade github/gh-copilot >/dev/null 2>&1 || true
  fi
  if install_fabric; then
    configure_fabric_env || true
  fi
fi

printf "\nAgent stack non-declarative installs complete.\n"
