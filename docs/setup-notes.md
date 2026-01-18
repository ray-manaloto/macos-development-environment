# macOS Development Environment - Setup Notes

This document tracks the macOS development environment automation for this
machine. It focuses on launchd-driven maintenance and auto-fix routines for
our preferred toolchain order (mise > pixi > uv > pip; bun > node).

## Launchd Auto-Updates

### Job definition
- Label: `com.ray-manaloto.macos-dev-maintenance`
- Plist: `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-maintenance.plist`
- Script: `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance`
- Interval: 43200 seconds (12 hours)
- Logs: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`

### Script behavior (current)
- Homebrew:
  - `brew update`
  - `brew upgrade --formula -v`
  - `brew upgrade --cask -v` for all outdated casks except `osquery`
- mise (if installed):
  - `mise self-update`
  - `mise upgrade --yes`
  - `mise reshim`
- bun (if installed):
  - `bun update -g --latest`
  - `bun upgrade` only when Bun is not mise-managed
- pixi (if installed):
  - `pixi self-update`
  - `pixi global update`
- uv (if installed outside Homebrew):
  - `uv self update`
  - `uv tool upgrade --all`

### Known exception: sudo-required casks
- Some casks (notably `osquery`) require `sudo` for upgrade and will fail
  under launchd (no TTY). The script skips these casks.
- Manual update example:
  - `brew upgrade --cask osquery`

## Bun Global Trust (Lifecycle Scripts)
Some Bun global packages run lifecycle scripts. To allow those scripts in
non-interactive updates:
- Global project: `~/.bun/install/global`
- Configure trusted dependencies in:
  - `~/.bun/install/global/package.json` under `trustedDependencies`
- Check status:
  - `bun pm -g untrusted`
- Grant trust:
  - `bun pm -g trust <package>`

## Auto-Fix Policy
Auto-fix behavior is controlled via environment variables in the launchd
plist.

- `MDE_REPO`: repo path used by the wrapper script.
- `MDE_AUTOFIX=1`: enable config syncing + tool cleanup.
- `MDE_AUTOFIX_STRICT=1`: additionally remove brew-managed runtimes (node,
  python, go, rust) when mise is present.
- `MDE_UPDATE_OMZ=1`: update oh-my-zsh from git.

Defaults in the plist: `MDE_AUTOFIX=1`, `MDE_AUTOFIX_STRICT=0`,
`MDE_UPDATE_OMZ=0`.

Auto-fix actions:
- Ensure global mise versions (python/node/bun/go/rust).
- Remove conflicting managers (nvm, volta, asdf, pyenv) with backups (only if
  mise is available).
- Sync managed configs (`~/.oh-my-zsh/custom/*` and `~/.tmux.conf`).
- Ensure tmux plugin manager (TPM) is installed.

## Observability and Manual Runs
- Start the job now:
  - `launchctl start com.ray-manaloto.macos-dev-maintenance`
- Check if it is loaded:
  - `launchctl list | rg com.ray-manaloto.macos-dev-maintenance`
- Tail logs:
  - `tail -n 200 ~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`
- Run the script directly:
  - `~/Library/Application Support/com.ray-manaloto.macos-dev-maintenance/macos_dev_maintenance`
  - Repo source: `scripts/macos-dev-maintenance.sh`
- Notifications are log-only by default (no UI toast).

## Shell Configuration Notes
- Homebrew curl is preferred in shell config when needed:
  - `export PATH="/opt/homebrew/opt/curl/bin:$PATH"`
- Managed oh-my-zsh custom files live under `templates/oh-my-zsh`.
  - Sync them with `scripts/ensure-managed-configs.sh`.

## Modern Best Practices (extra)
- Keep Homebrew limited to OS-level packages; use mise for runtimes.
- Install `gpg` so mise can verify downloads (auto-fix installs `gnupg` via brew).
- Use `direnv` or per-repo `.env` files instead of global secrets.
- Store managed dotfile overrides in `~/.oh-my-zsh/custom` to avoid merge
  conflicts during updates.
- Prefer `shellcheck` on scripts and run `scripts/quality-checks.sh` after edits.

## LangChain CLI Tooling
- Inventory: `docs/langchain-cli-tools.md`
- Install/update script: `scripts/install-langchain-cli-tools.sh`

## AI Agent Stack
- Overview: `docs/agent-stack.md`
- Install/update script: `scripts/install-agent-stack.sh`
- mise guidance: `docs/mise-config.md`

## Tmux + Cloud Workflow
- Overview: `docs/tmux-cloud-workflow.md`
- Install/update script: `scripts/optimize-tmux.sh`
- Layout helper: `scripts/agent-hud`

## Decision Log
- Summary of key choices: `docs/decision-log.md`

## Quality + Multi-Agent
- Playbook: `docs/quality-playbook.md`
- Runner config: `docs/multi-agent-runner.md`
