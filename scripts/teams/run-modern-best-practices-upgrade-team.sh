#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$REPO_ROOT/scripts/lib/mde-agent-policy.sh"

mde_policy_init
mde_setup_managed_path
mde_disable_mise_auto_install
"$REPO_ROOT/scripts/mde-agent-preflight.sh" --quiet >/dev/null
export MDE_AGENT_PREFLIGHT_PASSED=1
export MDE_AGENT_CONTEXT=1
mde_prepare_guard_dir >/dev/null

DATE_STAMP="${MDE_MODERN_BEST_PRACTICES_DATE:-$(date +%F)}"
TRIGGER_CONTEXT="${MDE_MODERN_BEST_PRACTICES_TRIGGER:-modern-best-practices}"
OUT_DIR="${MDE_MODERN_BEST_PRACTICES_OUT_DIR:-reports/modern-best-practices/$DATE_STAMP}"
SUMMARY_FILE="$OUT_DIR/summary.md"
DOMAIN_RUNNER="${MDE_MODERN_BEST_PRACTICES_DOMAIN_RUNNER:-$REPO_ROOT/scripts/teams/run-mde-domain-team.sh}"
DEVCONTAINER_RUNNER="${MDE_MODERN_BEST_PRACTICES_DEVCONTAINER_RUNNER:-$REPO_ROOT/scripts/teams/run-devcontainer-setup-sdlc-team.sh}"

if [[ ! -x "$DOMAIN_RUNNER" ]]; then
  echo "Domain runner is not executable: $DOMAIN_RUNNER" >&2
  exit 1
fi

if [[ ! -x "$DEVCONTAINER_RUNNER" ]]; then
  echo "Devcontainer runner is not executable: $DEVCONTAINER_RUNNER" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

IFS=',' read -r -a DOMAINS <<< "${MDE_MODERN_BEST_PRACTICES_DOMAINS:-mise-core,shell-editor}"

echo "[modern-best-practices] date=$DATE_STAMP trigger=$TRIGGER_CONTEXT"
echo "[modern-best-practices] output_dir=$OUT_DIR"
echo "[modern-best-practices] domains=${DOMAINS[*]}"
echo "[modern-best-practices] runner_mode=${MDE_AGENT_RUNNER_MODE:-real}"

for domain in "${DOMAINS[@]}"; do
  [[ -n "$domain" ]] || continue
  echo "[modern-best-practices] running domain team: $domain"
  MDE_DOMAIN_DATE="$DATE_STAMP" \
  MDE_DOMAIN_OUT_DIR="$OUT_DIR/domains/$domain" \
  "$DOMAIN_RUNNER" --domain "$domain" --trigger "$TRIGGER_CONTEXT"
done

echo "[modern-best-practices] running devcontainer SDLC team"
DEVCONTAINER_SDLC_DATE="$DATE_STAMP" \
DEVCONTAINER_SDLC_OUT_DIR="$OUT_DIR/devcontainer" \
"$DEVCONTAINER_RUNNER"

{
  printf '# Modern Best Practices Upgrade Team\n\n'
  printf -- '- Date: `%s`\n' "$DATE_STAMP"
  printf -- '- Trigger: `%s`\n' "$TRIGGER_CONTEXT"
  printf -- '- Runner mode: `%s`\n' "${MDE_AGENT_RUNNER_MODE:-real}"
  printf -- '- Domains: `%s`\n\n' "$(IFS=,; printf '%s' "${DOMAINS[*]}")"
  printf '## Outputs\n'
  for domain in "${DOMAINS[@]}"; do
    [[ -n "$domain" ]] || continue
    printf -- '- Domain `%s`: `%s`\n' "$domain" "$OUT_DIR/domains/$domain"
  done
  printf -- '- Devcontainer SDLC: `%s`\n\n' "$OUT_DIR/devcontainer"
  printf '## Recommended Execution Order\n'
  printf -- '- Review domain authority outputs first to scope accepted modernization work.\n'
  printf -- '- Review devcontainer SDLC outputs next for implementation, QA, security, and release sequencing.\n'
  printf -- '- Feed accepted findings into implementation work and learning writeback before repo-wide rollout.\n'
} >"$SUMMARY_FILE"

echo "[modern-best-practices] wrote $SUMMARY_FILE"
