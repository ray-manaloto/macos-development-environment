# macos-development-environment

This repository documents the macOS development environment setup and
automation used on this machine. The focus is on launchd-driven updates for
Homebrew and runtime/tool managers (mise, bun, pixi, uv), plus how to verify
and troubleshoot runs.

## Quickstart
- Trust project tasks before first `mise run`:
  - `mise trust`
- Run deterministic remediation when host state is drifted:
  - `mise run mde:remediate`
- Review `docs/setup-notes.md` for the launchd job, tool updates, and log paths.
- Configure global secrets through `fnox` with `mise` integration.
  - Global authorities: `~/.config/mise/config.toml` and `~/.config/fnox/config.toml`
  - Shared repo overlays: `fnox.toml` and optional gitignored `fnox.local.toml`
- Run the job manually if needed:
  - `launchctl start com.ray-manaloto.macos-dev-maintenance`
- Tail logs:
  - `tail -n 200 ~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`

## Cross-Platform Profiles (`macOS` + `devcontainer`)
- `MDE_PLATFORM` is auto-detected:
  - macOS host => `macos`
  - `DEVCONTAINER` or `CODESPACES` => `devcontainer`
  - plain `/.dockerenv` => `linux` (container, not necessarily devcontainer)
  - other Linux => `linux`
- Override explicitly when needed:
  - `MDE_PLATFORM=devcontainer scripts/mde-verify`
- Shell bootstrap is ordered under `~/.oh-my-zsh/custom`:
  - `10-mde-core.zsh`
  - `15-mde-platform.zsh`
  - `20-mde-aliases.zsh`
  - `90-starship.zsh`
  - `99-local.zsh`
- Dotfile sync is `chezmoi`-first with legacy fallback:
  - Apply: `scripts/ensure-managed-configs.sh`
  - Drift check: `scripts/ensure-managed-configs.sh --check`
  - Maintenance always runs config sync (`scripts/macos-dev-maintenance.sh`).
- Recovery/repair path:
  - `scripts/mde-remediate.sh` (`--check`, `--runtime-plan`, `--runtime-apply`)
- Platform log roots:
  - macOS: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance`
  - devcontainer/Linux: `~/.local/state/macos-dev-maintenance`

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
- fnox: secrets authority loaded through `mise-env-fnox` with `MISE_ENV_CACHE=1`
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
- `docs/launchd-automation-runbook.md`
- `docs/skypilot-aws-setup.md`
- `docs/toolchain-precedence.md`
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
- `docs/terminal-startup-profiling.md`
- `docs/decision-log.md`
- `docs/operational-checklist.md`
- `docs/quality-playbook.md`
- `docs/multi-agent-runner.md`

## Scripts
- `scripts/install-langchain-cli-tools.sh`
- `scripts/install-agent-stack.sh`
- `scripts/install-ai-research-skills.sh`
- `scripts/macos-dev-maintenance.sh`
- `scripts/ensure-managed-configs.sh`
- ~~`scripts/optimize-tmux.sh`~~ → migrated to `uv run mde-py install tmux`
- `scripts/status-dashboard.sh`
- `scripts/health-check.sh`
- `scripts/verify-tmux-setup.sh`
- `scripts/mde-verify`
- `scripts/verify-all.sh`
- `scripts/mde-drift-check.sh`
- `scripts/verify-openai-key.py`
- `scripts/verify-openai-key-cli.py`
- `scripts/verify-anthropic-key.py`
- `scripts/set-keychain-secret.py`
- `scripts/setup-skypilot-aws.sh`
- `scripts/sky-status.sh`
- `scripts/openlit-control.sh`
- `scripts/verify-openlit.sh`
- ~~`scripts/install-aws-k8s-tools.sh`~~ → migrated to `uv run mde-py install aws-k8s`
- `scripts/verify-aws-k8s-tools.sh`
- `scripts/verify-ai-research-skills.sh`
- `scripts/post-setup-run.sh`
- `scripts/install-validation-launchd.sh`
- `scripts/setup-sudo-all.sh`
- `scripts/setup-newsyslog-rotation.sh`
- `scripts/agent-hud`
- `scripts/quality-checks.sh`
- `scripts/run-multi-agent.sh`
