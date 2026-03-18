#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
export MDE_AGENT_CONTEXT="${MDE_AGENT_CONTEXT:-1}"
mde_prepare_guard_dir >/dev/null

SCOPE="${1:-global-tools}"
if [[ "$SCOPE" != "global-tools" ]]; then
  printf 'Usage: %s [global-tools] [--dry-run|--apply|--verify|--report]\n' "$0" >&2
  exit 2
fi
shift || true

MODE="dry-run"
for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE="dry-run" ;;
    --apply) MODE="apply" ;;
    --verify) MODE="verify" ;;
    --report) MODE="report" ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

BREW="$(command -v brew 2>/dev/null || true)"
REPORT_DIR="$MDE_REPO_ROOT/reports/mde-migration"
DATE_STAMP="$(date +%F)"
INVENTORY_FILE="$REPORT_DIR/${DATE_STAMP}-inventory.json"
SUMMARY_FILE="$REPORT_DIR/${DATE_STAMP}-summary.md"

mkdir -p "$REPORT_DIR"

mde_emit_telemetry_event "migration.started" started "Global tool migration started" "mode=$MODE" "scope=$SCOPE"
"$SCRIPT_DIR/mde-agent-preflight.sh" --quiet >/dev/null

collect_inventory() {
  python3 - "$MDE_TOOL_OWNERSHIP_FILE" "$HOME" > "$INVENTORY_FILE" <<'PY'
import json
import os
import shutil
import sys
from pathlib import Path

registry_path, home = sys.argv[1:3]
with open(registry_path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)

managed_wrapper_prefix = '# Managed by macos-development-environment.'

def is_managed_wrapper(path_str: str | None) -> bool:
    if not path_str:
        return False
    path = Path(path_str)
    if not path.is_file():
        return False
    try:
        with path.open('r', encoding='utf-8', errors='ignore') as fh:
            return fh.readline().startswith(managed_wrapper_prefix)
    except OSError:
        return False

def classify_owner(resolved: str | None) -> str:
    if not resolved:
        return 'missing'
    real = os.path.realpath(resolved)
    mise_prefixes = (
        str(Path(home) / '.local/share/mise/shims'),
        str(Path(home) / '.local/share/mise/installs'),
        str(Path(home) / '.local/share/mise/bin'),
    )
    if resolved.startswith(mise_prefixes) or real.startswith(mise_prefixes):
        return 'mise'
    if real.startswith('/Applications/Codex.app/Contents/Resources'):
        return 'app-bundle'
    if real.startswith('/opt/homebrew') or real.startswith('/usr/local/Homebrew'):
        return 'brew'
    if real.startswith(str(Path(home) / '.bun')):
        return 'bun-global'
    if real.startswith(str(Path(home) / '.local/bin')) and is_managed_wrapper(real):
        return 'managed-wrapper'
    if (
        real.startswith(str(Path(home) / '.cargo/bin'))
        or real.startswith(str(Path(home) / 'go/bin'))
        or real.startswith(str(Path(home) / '.local/bin'))
    ):
        return 'local-bin'
    return 'other'

rows = []
for item in data.get('tools', []):
    command = item.get('command', '')
    resolved = shutil.which(command) if command else None
    current_owner = classify_owner(resolved)
    rows.append({
        'id': item.get('id'),
        'command': command,
        'tool_class': item.get('tool_class'),
        'target_owner': item.get('owner'),
        'current_owner': current_owner,
        'resolved_path': resolved,
        'needs_migration': item.get('owner') == 'mise' and current_owner not in ('mise', 'managed-wrapper', 'app-bundle', 'missing')
    })
print(json.dumps(rows, indent=2))
PY
}

write_summary() {
  python3 - "$INVENTORY_FILE" "$SUMMARY_FILE" <<'PY'
import json
import sys
inventory_path, summary_path = sys.argv[1:3]
with open(inventory_path, 'r', encoding='utf-8') as fh:
    items = json.load(fh)
needs = [x for x in items if x.get('needs_migration')]
missing = [x for x in items if x.get('current_owner') == 'missing']
with open(summary_path, 'w', encoding='utf-8') as out:
    out.write('# Global Tool Migration Summary\n\n')
    out.write(f'- total tools: {len(items)}\n')
    out.write(f'- needs migration: {len(needs)}\n')
    out.write(f'- missing commands: {len(missing)}\n\n')
    if needs:
        out.write('## Needs Migration\n\n')
        for item in needs:
            out.write(f"- `{item['command']}`: current owner `{item['current_owner']}` -> target `{item['target_owner']}`\n")
    if missing:
        out.write('\n## Missing Commands\n\n')
        for item in missing:
            out.write(f"- `{item['command']}` is not currently installed\n")
PY
}

migrate_runtime() {
  local formula="$1"
  local mise_tool="$2"
  if [[ -z "$BREW" ]]; then
    return 0
  fi
  if ! "$BREW" list --formula "$formula" >/dev/null 2>&1; then
    return 0
  fi
  printf 'Ensuring mise manages %s before removing brew %s\n' "$mise_tool" "$formula"
  mise use -g --yes "${mise_tool}@latest" >/dev/null 2>&1 || return 1
  mise reshim >/dev/null 2>&1 || true
  "$BREW" uninstall "$formula"
}

collect_inventory
write_summary

case "$MODE" in
  dry-run)
    cat "$SUMMARY_FILE"
    ;;
  apply)
    mise install
    mise reshim >/dev/null 2>&1 || true
    migrate_runtime node node || true
    migrate_runtime go go || true
    migrate_runtime rust rust || true
    if [[ -n "$BREW" ]] && ! "$BREW" list --formula llvm >/dev/null 2>&1; then
      migrate_runtime python python || true
    fi
    collect_inventory
    write_summary
    cat "$SUMMARY_FILE"
    ;;
  verify)
    python3 - "$INVENTORY_FILE" <<'PY'
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    items = json.load(fh)
needs = [x for x in items if x.get('needs_migration')]
if needs:
    for item in needs:
        print(f"migration needed: {item['command']} ({item['current_owner']} -> {item['target_owner']})", file=sys.stderr)
    sys.exit(1)
PY
    cat "$SUMMARY_FILE"
    ;;
  report)
    printf 'inventory: %s\n' "$INVENTORY_FILE"
    printf 'summary: %s\n' "$SUMMARY_FILE"
    cat "$SUMMARY_FILE"
    ;;
esac

mde_emit_telemetry_event "migration.${MODE}" passed "Global tool migration completed" "mode=$MODE" "inventory=$INVENTORY_FILE" "summary=$SUMMARY_FILE"
