#!/usr/bin/env zsh
# Managed by macos-development-environment.

_mde_resolve_repo() {
  local candidate

  if [[ -n "${MDE_REPO:-}" && -d "${MDE_REPO}/scripts" ]]; then
    printf '%s' "$MDE_REPO"
    return 0
  fi

  for candidate in \
    "$HOME/dev/github/ray-manaloto/macos-development-environment" \
    "/workspaces/macos-development-environment" \
    "$PWD"; do
    if [[ -x "$candidate/scripts/mde-verify" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done

  if command -v git >/dev/null 2>&1; then
    candidate="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "$candidate" && -x "$candidate/scripts/mde-verify" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  fi

  printf '%s' "$HOME/dev/github/ray-manaloto/macos-development-environment"
}

export MDE_REPO="$(_mde_resolve_repo)"

mde_run_task() {
  local task_name="$1"
  shift || true

  if ! command -v mise >/dev/null 2>&1; then
    echo "mise is required for managed mde tasks" >&2
    return 1
  fi

  (
    cd "$MDE_REPO"
    mise run "$task_name" -- "$@"
  )
}

mde() {
  local cmd="${1:-}"
  shift || true
  local subcmd=""

  case "$cmd" in
    agent)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        preflight)
          mde_run_task "mde:agent:preflight" "$@"
          ;;
        verify)
          mde_run_task "mde:agent:verify" "$@"
          ;;
        report)
          mde_run_task "mde:agent:report" "$@"
          ;;
        *)
          echo "Usage: mde agent <preflight|verify|report>" >&2
          return 1
          ;;
      esac
      ;;
    update)
      mde_run_task "mde:update" "$@"
      ;;
    update-fast)
      mde_run_task "mde:update:fast" "$@"
      ;;
    verify)
      mde_run_task "mde:verify" "$@"
      ;;
    drift)
      mde_run_task "mde:drift" "$@"
      ;;
    migrate)
      if [[ "${1:-}" == "global-tools" ]]; then
        shift || true
      fi
      mde_run_task "mde:migrate:global-tools" "$@"
      ;;
    research)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        autoimprove)
          mde_run_task "mde:research:autoimprove" "$@"
          ;;
        *)
          echo "Usage: mde research <autoimprove>" >&2
          return 1
          ;;
      esac
      ;;
    status)
      mde_run_task "mde:status" "$@"
      ;;
    sync-dotfiles)
      mde_run_task "mde:sync-dotfiles" "$@"
      ;;
    mcp-sync)
      mde_run_task "mde:mcp:sync" "$@"
      ;;
    agents-review)
      mde_run_task "mde:agents:review" "$@"
      ;;
    prune)
      mde_run_task "mde:prune" "$@"
      ;;
    validate)
      mde_run_task "mde:validate" "$@"
      ;;
    doctor)
      mde_run_task "mde:doctor" "$@"
      ;;
    remediate)
      mde_run_task "mde:remediate" "$@"
      ;;
    secrets)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        refresh)
          mde_run_task "mde:secrets:refresh" "$@"
          ;;
        smoke)
          "$MDE_REPO/scripts/secrets-smoke-test.sh" "$@"
          ;;
        *)
          echo "Usage: mde secrets <refresh|smoke>" >&2
          return 1
          ;;
      esac
      ;;
    test)
      mde_run_task "mde:test" "$@"
      ;;
    learn)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        init)
          mde_run_task "mde:learn:init" "$@"
          ;;
        search)
          mde_run_task "mde:learn:search" "$@"
          ;;
        store)
          mde_run_task "mde:learn:store" "$@"
          ;;
        consolidate)
          mde_run_task "mde:learn:consolidate" "$@"
          ;;
        status)
          mde_run_task "mde:learn:status" "$@"
          ;;
        verify)
          mde_run_task "mde:learn:verify" "$@"
          ;;
        *)
          echo "Usage: mde learn <init|search|store|consolidate|status|verify>" >&2
          return 1
          ;;
      esac
      ;;
    team)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        claude-flow-learning)
          mde_run_task "mde:team:claude-flow-learning" "$@"
          ;;
        *)
          echo "Usage: mde team <claude-flow-learning>" >&2
          return 1
          ;;
      esac
      ;;
    refs)
      subcmd="${1:-}"
      shift || true
      case "$subcmd" in
        clone-frameworks)
          mde_run_task "mde:refs:clone-frameworks" "$@"
          ;;
        refresh)
          mde_run_task "mde:refs:refresh" "$@"
          ;;
        verify)
          mde_run_task "mde:refs:verify" "$@"
          ;;
        *)
          echo "Usage: mde refs <clone-frameworks|refresh|verify>" >&2
          return 1
          ;;
      esac
      ;;
    *)
      echo "Usage: mde <agent|update|update-fast|verify|drift|migrate|research|status|sync-dotfiles|mcp-sync|agents-review|prune|validate|doctor|remediate|secrets|test|learn|team|refs>" >&2
      return 1
      ;;
  esac
}

alias mde-agent-preflight='mde agent preflight'
alias mde-agent-verify='mde agent verify'
alias mde-agent-report='mde agent report'
alias mde-update='mde update'
alias mde-update-fast='mde update-fast'
alias mde-verify='mde verify'
alias mde-drift='mde drift'
alias mde-migrate='mde migrate'
alias mde-research-autoimprove='mde research autoimprove'
alias mde-status='mde status'
alias mde-sync-dotfiles='mde sync-dotfiles'
alias mde-mcp-sync='mde mcp-sync'
alias mde-agents-review='mde agents-review'
alias mde-prune='mde prune'
alias mde-validate='mde validate'
alias mde-doctor='mde doctor'
alias mde-test='mde test'
alias mde-learn-status='mde learn status'
alias mde-learn-verify='mde learn verify'
alias mde-remediate='mde remediate'
alias mde-secrets-refresh='mde secrets refresh'

# Cloud workflow (SkyPilot)
alias cloud-run='sky launch -d -c agent-cluster agent_cloud.yaml'
alias cloud-status="$MDE_REPO/scripts/sky-status.sh"
alias sky-status="$MDE_REPO/scripts/sky-status.sh"
alias cloud-ssh='ssh agent-cluster'
alias cloud-view='ssh -L 8123:localhost:8123 agent-cluster'
alias cloud-stop='sky down agent-cluster'

# Agent HUD helper
alias agent-hud="$MDE_REPO/scripts/agent-hud"
alias mde-secrets-check="$MDE_REPO/scripts/secrets-smoke-test.sh"

# OpenLIT telemetry
alias openlit="$MDE_REPO/scripts/openlit-control.sh"
alias openlit-status="$MDE_REPO/scripts/openlit-control.sh status"
alias openlit-deploy="$MDE_REPO/scripts/openlit-control.sh deploy"

# Preserve compatibility only if user has no existing firebase alias.
if ! alias firebase >/dev/null 2>&1; then
  alias firebase="$MDE_REPO/scripts/firebase-wrapper.sh"
fi
