#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
export MDE_AGENT_CONTEXT=1
mde_prepare_guard_dir >/dev/null

MODE="incremental"
for arg in "$@"; do
  case "$arg" in
    --incremental) MODE="incremental" ;;
    --full) MODE="full" ;;
    --report) MODE="report" ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

if [[ "$MODE" == "report" ]]; then
  latest_summary="$(find "$MDE_REPO_ROOT/reports/mde-autoresearch" -maxdepth 1 -type f -name '*-summary.md' 2>/dev/null | sort | tail -n 1)"
  if [[ -n "$latest_summary" ]]; then
    cat "$latest_summary"
    exit 0
  fi
  printf 'No autoresearch summary found.\n' >&2
  exit 1
fi

"$SCRIPT_DIR/mde-agent-preflight.sh" --quiet >/dev/null
DOMAIN_HINT="${MDE_DOMAIN:-${MDE_RESEARCH_DOMAIN_HINT:-mde:research:autoimprove}}"
ACTIVE_DOMAIN="$("$SCRIPT_DIR/mde-domain-classify.sh" "$DOMAIN_HINT")"
export MDE_ACTIVE_DOMAIN="$ACTIVE_DOMAIN"
mde_emit_telemetry_event "research.domain.selected" started "MDE autoresearch domain selected" "mode=$MODE" "domain=$ACTIVE_DOMAIN"
"$SCRIPT_DIR/teams/run-mde-domain-team.sh" --domain "$ACTIVE_DOMAIN" --trigger "mde:research:autoimprove"
mde_emit_telemetry_event "research.started" started "MDE autoresearch started" "mode=$MODE" "team=mde-autoresearch"
export MDE_AUTORESEARCH_MODE="$MODE"
"$SCRIPT_DIR/teams/run-mde-autoresearch-team.sh"
mde_emit_telemetry_event "research.completed" passed "MDE autoresearch completed" "mode=$MODE" "team=mde-autoresearch"
