#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with sudo: sudo $0" >&2
  exit 1
fi

TARGET_USER="${SUDO_USER:-${MDE_TARGET_USER:-}}"
if [[ -z "$TARGET_USER" ]]; then
  echo "SUDO_USER not set. Re-run with sudo or set MDE_TARGET_USER." >&2
  exit 1
fi

HOME_DIR="$(dscl . -read "/Users/$TARGET_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
if [[ -z "$HOME_DIR" ]]; then
  HOME_DIR="/Users/$TARGET_USER"
fi

HELPER_PATH="/usr/local/sbin/mde-gcloud-migrate"
SUDOERS_PATH="/etc/sudoers.d/mde-gcloud-migrate"

install -d -o root -g wheel /usr/local/sbin

cat <<'SCRIPT' > "$HELPER_PATH"
#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

TARGET_USER="${SUDO_USER:-${MDE_TARGET_USER:-}}"
if [[ -z "$TARGET_USER" ]]; then
  echo "SUDO_USER not set. Run via sudo." >&2
  exit 1
fi

HOME_DIR="$(dscl . -read "/Users/$TARGET_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
if [[ -z "$HOME_DIR" ]]; then
  HOME_DIR="/Users/$TARGET_USER"
fi

SRC="$HOME_DIR/google-cloud-sdk"
DST="/opt/google-cloud-sdk"

if [[ ! -d "$SRC" ]]; then
  log "gcloud SDK not found at $SRC."
  exit 0
fi

if [[ -e "$DST" ]]; then
  log "gcloud SDK already at $DST."
  exit 0
fi

mv "$SRC" "$DST"
chown -R "$TARGET_USER":staff "$DST"
"$DST/install.sh" --quiet --path-update false --command-completion false
log "gcloud SDK migrated to $DST."
SCRIPT

chown root:wheel "$HELPER_PATH"
chmod 755 "$HELPER_PATH"

cat <<EOF2 > "$SUDOERS_PATH"
# Managed by macos-development-environment.
$TARGET_USER ALL=(root) NOPASSWD: $HELPER_PATH
EOF2

chmod 440 "$SUDOERS_PATH"
visudo -cf "$SUDOERS_PATH"

log "Installed $HELPER_PATH and sudoers rule for $TARGET_USER."
log "Run: sudo -n $HELPER_PATH"
log "Remove with: sudo rm -f $SUDOERS_PATH $HELPER_PATH"
