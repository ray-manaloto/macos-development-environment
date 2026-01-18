# macOS Development Environment - Setup Notes

This document tracks the macOS development environment automation for this
machine. It focuses on launchd-driven updates for Homebrew and related
toolchains (Bun, Node, uv), plus how to verify and troubleshoot runs.

## Launchd Auto-Updates

### Job definition
- Label: `com.github.domt4.homebrew-autoupdate`
- Plist: `~/Library/LaunchAgents/com.github.domt4.homebrew-autoupdate.plist`
- Script: `~/Library/Application Support/com.github.domt4.homebrew-autoupdate/brew_autoupdate`
- Interval: 43200 seconds (12 hours)
- Logs: `~/Library/Logs/com.github.domt4.homebrew-autoupdate/com.github.domt4.homebrew-autoupdate.out`

### Script behavior (current)
- Homebrew:
  - `brew update`
  - `brew upgrade --formula -v`
  - `brew upgrade --cask -v` for all outdated casks except `osquery`
- Bun (if installed):
  - `bun upgrade`
  - `bun update -g --latest`
- uv (if installed outside Homebrew):
  - `uv self update`
  - Homebrew-installed uv is updated by `brew upgrade --formula`
- Node toolchain:
  - Volta (if installed): `volta install node@lts npm@latest`
  - NVM (if installed):
    - Uses Homebrew curl (`/opt/homebrew/opt/curl/bin/curl`) for downloads
    - Temporarily removes the Homebrew curl shim from `PATH` before sourcing NVM
    - `nvm install --lts --latest-npm` then `npm update -g`
  - Fallback: `npm update -g` if npm is available without NVM

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

## Observability and Manual Runs
- Start the job now:
  - `launchctl start com.github.domt4.homebrew-autoupdate`
- Check if it is loaded:
  - `launchctl list | rg com.github.domt4.homebrew-autoupdate`
- Tail logs:
  - `tail -n 200 ~/Library/Logs/com.github.domt4.homebrew-autoupdate/com.github.domt4.homebrew-autoupdate.out`
- Run the script directly:
  - `~/Library/Application Support/com.github.domt4.homebrew-autoupdate/brew_autoupdate`

## Shell Configuration Notes
- Homebrew curl is preferred in shell config when needed:
  - `export PATH="/opt/homebrew/opt/curl/bin:$PATH"`
- Oh My Zsh updates are separate from launchd (they run within the shell).

## LangChain CLI Tooling
- Inventory: `docs/langchain-cli-tools.md`
- Install/update script: `scripts/install-langchain-cli-tools.sh`
