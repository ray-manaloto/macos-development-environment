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

## Strict Cleanup (MDE_AUTOFIX_STRICT=1)
Strict cleanup removes brew-managed runtimes (node, python, go, rust) once
mise is available. Enable it only after confirming mise is installed and
active.

Pros:
- Single runtime source of truth (mise) with consistent PATH resolution.
- Fewer duplicate installs and version conflicts.
- Centralized runtime upgrades via one tool.

Cons:
- Breaks scripts that hardcode brew runtime paths.
- Removes brew-provided runtimes and their global packages.
- `brew uninstall` may refuse if other formulae depend on those runtimes.

Gotchas:
- Verify `which node`, `which python`, `which go`, `which rustc` resolve to mise
  shims before enabling strict cleanup.
- Expect large downloads; run on reliable network/power.
- Start a new shell session after cleanup to refresh PATH.

Possible issues:
- Brew upgrades can reintroduce runtimes as dependencies later.
- CI or scripts that expect `/opt/homebrew/bin/*` will fail until updated.
- If brew refuses uninstall due to dependencies, strict cleanup will be partial.

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
- Prefer the official Google Cloud SDK installer for `gcloud` and install
  it under `/opt/google-cloud-sdk` (PATH managed via oh-my-zsh templates).
- `gsutil` is legacy; use `gcloud storage` commands instead.
- If you need the SDK-managed Python, run
  `sudo gcloud components update-macos-python --quiet` once. Avoid setting
  `CLOUDSDK_PYTHON` unless you need an override.
- Migration from `~/google-cloud-sdk` (if present):
  - `sudo mv ~/google-cloud-sdk /opt/google-cloud-sdk`
  - `sudo chown -R "$USER":staff /opt/google-cloud-sdk`
  - `/opt/google-cloud-sdk/install.sh --quiet --path-update false --command-completion false`
- Use `direnv` or per-repo `.env` files instead of global secrets.
- Store managed dotfile overrides in `~/.oh-my-zsh/custom` to avoid merge
  conflicts during updates.
- Prefer `shellcheck` on scripts and run `scripts/quality-checks.sh` after edits.


## Python Versioning (Best Practices)
- Runtime owner: use mise for all Python versions (single source of truth).
- Install multiple versions with mise:
  - `mise install python@3.10 python@3.11 python@3.12`
- Set a global default (stable or latest):
  - `mise use -g python@3.12` or `mise use -g python@latest`
- Pin per-project versions in `mise.toml` (recommended for reproducibility).
- Use `uv` or `pixi` for tools/venvs; avoid global `pip install --user`.
- Prevent uv-managed Python duplicates:
  - `export UV_NO_MANAGED_PYTHON=1`
- If Homebrew Python is required by other formulae, keep it installed but
  ensure mise shims are first in `PATH`. Optionally `brew unlink python@3.x`.

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
