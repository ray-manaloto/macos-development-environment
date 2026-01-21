# macos-development-environment

This repository documents the macOS development environment setup and
automation used on this machine. The focus is on launchd-driven updates for
Homebrew and runtime/tool managers (mise, bun, pixi, uv), plus how to verify
and troubleshoot runs.

## Quickstart
- Review `docs/setup-notes.md` for the launchd job, tool updates, and log paths.
- Configure secrets in `~/.config/macos-development-environment/secrets.env` (template: `templates/secrets.env.example`).
  - Helper: `scripts/setup-secrets-env.sh --open`
- Run the job manually if needed:
  - `launchctl start com.ray-manaloto.macos-dev-maintenance`
- Tail logs:
  - `tail -n 200 ~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`

## Golden Path (One-Time Setup)
- Run all sudo-required setup steps (gcloud migration + log rotation):
  - `sudo scripts/setup-sudo-all.sh`
- Install the weekly validation job:
  - `scripts/install-validation-launchd.sh`
- Start the maintenance job now:
  - `launchctl start com.ray-manaloto.macos-dev-maintenance`
- Run the post-setup validation once:
  - `scripts/post-setup-run.sh`
- Confirm health:
  - `scripts/health-check.sh`
- Initialize SkyPilot AWS config (optional):
  - `scripts/setup-skypilot-aws.sh --init-config`

## Automation Overview
- Launchd job:
  - `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-maintenance.plist`
- Script:
  - `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance`
- Update cadence:
  - Every 12 hours via `StartInterval` (43200 seconds)

## Toolchain Coverage
- Homebrew: formula and cask upgrades (casks skip sudo-required ones like
  `osquery`)
- mise: runtime upgrades and shim refresh
- bun: `bun update -g --latest` (skip `bun upgrade` if mise-managed)
- pixi: `pixi self-update` + `pixi global update`
- uv: `uv self update` when installed outside Homebrew + `uv tool upgrade --all`

## Troubleshooting
- `osquery` upgrades require `sudo` and will fail under launchd (no TTY).
  Upgrade it manually:
  - `brew upgrade --cask osquery`
- If you enable strict auto-fix, brew-managed runtimes are removed in favor of
  mise-managed versions.

## Docs
- `docs/setup-notes.md`
- `docs/langchain-cli-tools.md`
- `docs/ai-agent-langchain-langsmith.md`
- `docs/ai-agent-langchain-langsmith-cheatsheet.md`
- `docs/langchain-langsmith-workflow-optimization.md`
- `docs/agent-playbook.md`
- `docs/langchain-langsmith-weekly-checklist.md`
- `docs/agent-stack.md`
- `docs/ai-research-skills.md`
- `docs/mise-config.md`
- `docs/ide-integrations.md`
- `docs/tmux-cloud-workflow.md`
- `docs/openlit-telemetry.md`
- `docs/decision-log.md`
- `docs/quality-playbook.md`
- `docs/multi-agent-runner.md`

## Scripts
- `scripts/install-langchain-cli-tools.sh`
- `scripts/install-agent-stack.sh`
- `scripts/install-ai-research-skills.sh`
- `scripts/macos-dev-maintenance.sh`
- `scripts/ensure-managed-configs.sh`
- `scripts/optimize-tmux.sh`
- `scripts/status-dashboard.sh`
- `scripts/health-check.sh`
- `scripts/verify-tmux-setup.sh`
- `scripts/verify-all.sh`
- `scripts/verify-openai-key.py`
- `scripts/verify-openai-key-cli.py`
- `scripts/verify-anthropic-key.py`
- `scripts/set-keychain-secret.py`
- `scripts/setup-secrets-env.sh`
- `scripts/setup-skypilot-aws.sh`
- `scripts/sky-status.sh`
- `scripts/openlit-control.sh`
- `scripts/verify-openlit.sh`
- `scripts/install-aws-k8s-tools.sh`
- `scripts/verify-aws-k8s-tools.sh`
- `scripts/verify-ai-research-skills.sh`
- `scripts/post-setup-run.sh`
- `scripts/install-validation-launchd.sh`
- `scripts/setup-sudo-all.sh`
- `scripts/setup-newsyslog-rotation.sh`
- `scripts/agent-hud`
- `scripts/quality-checks.sh`
- `scripts/run-multi-agent.sh`
