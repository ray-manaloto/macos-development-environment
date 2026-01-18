# macos-development-environment

This repository documents the macOS development environment setup and
automation used on this machine. The focus is on launchd-driven updates for
Homebrew and common toolchains (Bun, Node, uv), plus how to verify and
troubleshoot runs.

## Quickstart
- Review `docs/setup-notes.md` for the launchd job, tool updates, and log paths.
- Run the job manually if needed:
  - `launchctl start com.github.domt4.homebrew-autoupdate`
- Tail logs:
  - `tail -n 200 ~/Library/Logs/com.github.domt4.homebrew-autoupdate/com.github.domt4.homebrew-autoupdate.out`

## Automation Overview
- Launchd job:
  - `~/Library/LaunchAgents/com.github.domt4.homebrew-autoupdate.plist`
- Script:
  - `~/Library/Application Support/com.github.domt4.homebrew-autoupdate/brew_autoupdate`
- Update cadence:
  - Every 12 hours via `StartInterval` (43200 seconds)

## Toolchain Coverage
- Homebrew: formula and cask upgrades (casks skip sudo-required ones like
  `osquery`)
- Bun: `bun upgrade` and `bun update -g --latest`
- uv: `uv self update` when installed outside Homebrew
- Node: Volta LTS, NVM LTS + `npm update -g`

## Troubleshooting
- `osquery` upgrades require `sudo` and will fail under launchd (no TTY).
  Upgrade it manually:
  - `brew upgrade --cask osquery`
- If NVM downloads fail under launchd, ensure Homebrew curl is available and
  `PATH` is not using the Homebrew curl shim before sourcing NVM.

## Docs
- `docs/setup-notes.md`
- `docs/langchain-cli-tools.md`
- `docs/agent-stack.md`
- `docs/mise-config.md`
- `docs/ide-integrations.md`
- `docs/tmux-cloud-workflow.md`
- `docs/decision-log.md`

## Scripts
- `scripts/install-langchain-cli-tools.sh`
- `scripts/install-agent-stack.sh`
- `scripts/optimize-tmux.sh`
- `scripts/agent-hud`
