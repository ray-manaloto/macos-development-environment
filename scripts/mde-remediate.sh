#!/usr/bin/env bash
# shellcheck disable=SC2329
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/lib/mde-platform.sh
source "$SCRIPT_DIR/lib/mde-platform.sh"

MDE_PLATFORM="${MDE_PLATFORM:-$(mde_detect_platform)}"
RUNTIME_MODE="${MDE_RUNTIME_REPAIR:-plan}" # off|plan|apply
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --check)
      CHECK_ONLY=1
      ;;
    --runtime-off)
      RUNTIME_MODE="off"
      ;;
    --runtime-plan)
      RUNTIME_MODE="plan"
      ;;
    --runtime-apply)
      RUNTIME_MODE="apply"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: scripts/mde-remediate.sh [--check] [--runtime-off|--runtime-plan|--runtime-apply]" >&2
      exit 1
      ;;
  esac
done

REQ_PASS=0
REQ_FAIL=0
OPT_PASS=0
OPT_FAIL=0

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

required_step() {
  local label="$1"
  shift
  log "[required] $label"
  if "$@"; then
    REQ_PASS=$((REQ_PASS + 1))
    return 0
  fi
  REQ_FAIL=$((REQ_FAIL + 1))
  log "[required] FAILED: $label"
  return 1
}

optional_step() {
  local label="$1"
  shift
  log "[optional] $label"
  if "$@"; then
    OPT_PASS=$((OPT_PASS + 1))
    return 0
  fi
  OPT_FAIL=$((OPT_FAIL + 1))
  log "[optional] WARN: $label"
  return 1
}

na_step() {
  local label="$1"
  log "[n/a] $label (platform=$MDE_PLATFORM)"
}

setup_path() {
  local home="${HOME:-$REPO_ROOT}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}

run_or_check() {
  local label="$1"
  shift
  if (( CHECK_ONLY == 1 )); then
    "$@"
    return 0
  fi
  "$@"
}

ensure_mise_trust() {
  cd "$REPO_ROOT"
  if ! command -v mise >/dev/null 2>&1; then
    echo "mise is required but not found on PATH." >&2
    return 1
  fi
  run_or_check "mise trust" mise trust
}

ensure_config_sync() {
  if (( CHECK_ONLY == 1 )); then
    MDE_PLATFORM="$MDE_PLATFORM" "$SCRIPT_DIR/ensure-managed-configs.sh" --check
  else
    MDE_PLATFORM="$MDE_PLATFORM" MDE_USE_CHEZMOI=1 "$SCRIPT_DIR/ensure-managed-configs.sh"
  fi
}

ensure_mise_install() {
  if ! command -v mise >/dev/null 2>&1; then
    return 1
  fi
  if (( CHECK_ONLY == 1 )); then
    mise ls >/dev/null
  else
    mise install
  fi
}

ensure_validation_launchd() {
  local label="com.ray-manaloto.macos-dev-validation"
  local plist="$HOME/Library/LaunchAgents/${label}.plist"

  if (( CHECK_ONLY == 1 )); then
    [[ -f "$plist" ]]
  else
    mkdir -p "$HOME/Library/LaunchAgents"
    "$SCRIPT_DIR/install-validation-launchd.sh"
    launchctl kickstart -k "gui/$(id -u)/${label}" >/dev/null 2>&1 || true
  fi
}

ensure_maintenance_launchd() {
  local label="com.ray-manaloto.macos-dev-maintenance"
  local app_support="$HOME/Library/Application Support/com.ray-manaloto.macos-dev-maintenance"
  local log_dir="$HOME/Library/Logs/com.ray-manaloto.macos-dev-maintenance"
  local wrapper="$app_support/macos_dev_maintenance"
  local plist="$HOME/Library/LaunchAgents/${label}.plist"

  if (( CHECK_ONLY == 1 )); then
    [[ -f "$plist" ]] && launchctl list | grep -q "$label"
    return
  fi

  mkdir -p "$HOME/Library/LaunchAgents" "$app_support" "$log_dir"

  cat > "$wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$SCRIPT_DIR/macos-dev-maintenance.sh"
EOF
  chmod 755 "$wrapper"

  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$wrapper</string>
  </array>
  <key>StartInterval</key>
  <integer>43200</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$log_dir/macos-dev-maintenance.out</string>
  <key>StandardErrorPath</key>
  <string>$log_dir/macos-dev-maintenance.out</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>MDE_REPO</key>
    <string>$REPO_ROOT</string>
    <key>MDE_AUTOFIX</key>
    <string>1</string>
    <key>MDE_AUTOFIX_STRICT</key>
    <string>0</string>
    <key>MDE_UPDATE_AGENT_TOOLS</key>
    <string>1</string>
    <key>MDE_UPDATE_MCP</key>
    <string>1</string>
    <key>MDE_UPDATE_OMZ</key>
    <string>0</string>
  </dict>
</dict>
</plist>
EOF

  launchctl unload "$plist" >/dev/null 2>&1 || true
  launchctl load "$plist"
  launchctl kickstart -k "gui/$(id -u)/${label}" >/dev/null 2>&1 || true
}

runtime_repair() {
  case "$RUNTIME_MODE" in
    off)
      return 0
      ;;
    plan)
      MDE_MIGRATE_DRY_RUN=1 "$SCRIPT_DIR/mde-migrate-to-mise.sh"
      ;;
    apply)
      MDE_MIGRATE_DRY_RUN=0 "$SCRIPT_DIR/mde-migrate-to-mise.sh"
      ;;
    *)
      echo "invalid runtime mode: $RUNTIME_MODE" >&2
      return 1
      ;;
  esac
}

ensure_secrets_file() {
  # Bootstrap chain health check: age key file mode, fnox DOPPLER_TOKEN,
  # and Doppler/local AGE_PRIVATE_KEY parity. Replaces the deleted
  # scripts/secrets-smoke-test.sh.
  uv run mde-py secrets doctor
}

verify_secrets() {
  # Parity check between Doppler and fnox declarations sourced from Doppler.
  uv run mde-py secrets validate
}

verify_tooling_repair() {
  if "$SCRIPT_DIR/verify-tooling.sh"; then
    return 0
  fi
  if (( CHECK_ONLY == 1 )); then
    return 1
  fi
  log "tooling verification failed; routing repair through mise migration workflow"
  "$SCRIPT_DIR/mde-migrate-to-mise.sh" global-tools --apply
  "$SCRIPT_DIR/verify-tooling.sh"
}

setup_path
log "Starting remediation (platform=$MDE_PLATFORM, check_only=$CHECK_ONLY, runtime_mode=$RUNTIME_MODE)."

required_step "trust repository with mise" ensure_mise_trust || true
required_step "sync managed configs (chezmoi-first)" ensure_config_sync || true
required_step "install/refresh mise runtimes" ensure_mise_install || true
required_step "verify mirrored reference bundles" "$SCRIPT_DIR/mde-refs-verify.sh" || true
required_step "verify preset bundles" "$SCRIPT_DIR/mde-preset-verify.sh" || true
required_step "verify domain delegation contract" "$SCRIPT_DIR/mde-domain-verify.sh" || true
required_step "verify learning writeback contract" "$SCRIPT_DIR/mde-learn-verify.sh" || true

if mde_is_macos; then
  required_step "install/load maintenance launchd job" ensure_maintenance_launchd || true
  required_step "install/load validation launchd job" ensure_validation_launchd || true
  required_step "runtime ownership correction path" runtime_repair || true
  required_step "fnox secret readiness" ensure_secrets_file || true
  required_step "secrets verification" verify_secrets || true
else
  na_step "launchd remediation"
  na_step "runtime ownership correction path"
  na_step "keychain/secrets host checks"
fi

required_step "tooling verification and repair path" verify_tooling_repair || true
optional_step "drift check (enforced)" bash -c 'MDE_DRIFT_ENFORCE=1 "'"$SCRIPT_DIR"'/mde-drift-check.sh"' || true

log "Remediation summary: required(pass=$REQ_PASS fail=$REQ_FAIL) optional(pass=$OPT_PASS fail=$OPT_FAIL)"
if (( REQ_FAIL > 0 )); then
  exit 1
fi
exit 0
