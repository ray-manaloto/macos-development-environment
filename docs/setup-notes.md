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
- `MDE_UPDATE_AGENT_TOOLS=1`: update agent tooling (agent stack + LangChain CLI).
- `MDE_UPDATE_MCP=1`: sync MCP servers for Claude Desktop, Claude Code, and Codex.

Defaults in the plist: `MDE_AUTOFIX=1`, `MDE_AUTOFIX_STRICT=0`,
`MDE_UPDATE_OMZ=0`, `MDE_UPDATE_AGENT_TOOLS=1`, `MDE_UPDATE_MCP=1`.

Auto-fix actions:
- Ensure global mise versions (python/node/bun/go/rust).
- Remove conflicting managers (nvm, volta, asdf, pyenv) with backups (only if
  mise is available).
- Sync managed configs (`~/.oh-my-zsh/custom/*` and `~/.tmux.conf`).
- Ensure tmux plugin manager (TPM) is installed.
- Update agent tooling (agent stack + LangChain CLI inventory).
- Sync MCP servers (Claude Desktop, Claude Code, Codex).

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



## Claude Code Wrapper
- Managed wrapper: `scripts/claude-wrapper.sh` (alias: `claude`).
- Installed to `~/.local/bin/claude` for non-interactive shells.
- Loads `GITHUB_PERSONAL_ACCESS_TOKEN` from the same GitHub token used elsewhere.
- Removes `~/.bun/bin/claude` so there is only one `claude` on PATH.
- Wrapper runs `@anthropic-ai/claude-code` (override with `MDE_CLAUDE_CLI`).
- Use `\claude` to bypass the alias when needed.

## Gemini CLI Wrapper
- Managed wrapper: `scripts/gemini-wrapper.sh` (alias: `gemini`).
- Installed to `~/.local/bin/gemini` for non-interactive shells.
- Loads `GEMINI_API_KEY` from Keychain/1Password when available.
- Loads `GITHUB_MCP_PAT` for GitHub MCP (Keychain `mde-github-mcp-pat` or `mde-github-token`, or `MDE_OP_GITHUB_TOKEN_REF`).
- Removes `~/.bun/bin/gemini` so there is only one `gemini` on PATH.
- Wrapper runs `@google/gemini-cli@latest` via `bunx` to avoid bun global dependency conflicts.
- Wrapper prepends mise shims so extensions that invoke `npx` resolve the managed Node install.
- If no `./tools.yaml` is present, `mcp-toolbox` is skipped to avoid MCP connection errors; set `MDE_GEMINI_ENABLE_MCP_TOOLBOX=1` or pass `--extensions` to override.
- Use `\gemini` to bypass the alias when needed.

## LangSmith CLI Wrappers
- Managed wrapper: `scripts/langsmith-wrapper.sh` (aliases: `langsmith-fetch`, `langsmith-migrator`, `langsmith-mcp-server`).
- Installed to `~/.local/bin` for non-interactive shells.
- Loads `LANGSMITH_API_KEY` from Keychain/1Password when available.
- Use `LANGSMITH_API_KEY=... langsmith-fetch ...` to override when needed.

## Firebase CLI Logs
- Managed wrapper: `scripts/firebase-wrapper.sh` (alias: `firebase`).
- Logs move to `~/Library/Logs/firebase-tools/firebase-debug-YYYYMMDD_HHMMSS.log`.
- Use `\firebase` to bypass the alias when needed.

## Validation and Post-Setup
- Tools inventory (all managers):
  - `scripts/tools-inventory.sh`
- Status dashboard (quick overview):
  - `scripts/status-dashboard.sh`
  - `scripts/status-dashboard.sh --tmux` (tmux status bar)
  - `scripts/status-dashboard.sh --json` (automation; includes tmux verification + tool inventory)
  - `mde-status` (oh-my-zsh alias)
- Health check (no secrets printed):
  - `scripts/health-check.sh`
- Secrets check (no values printed):
  - `scripts/secrets-smoke-test.sh`
  - `mde-secrets-check` (oh-my-zsh alias)
- API key verification (provider API check):
  - `scripts/verify-openai-key.py`
  - `scripts/verify-openai-key-cli.py` (use when env overrides keychain)
  - `scripts/verify-anthropic-key.py`
- Keychain helper (stdin -> Keychain):
  - `scripts/set-keychain-secret.py --service mde-openai-api-key --stdin`
- Tmux verification (plugins + status bar):
  - `scripts/verify-tmux-setup.sh`
- Tooling verification (agent + LangChain):
  - `scripts/verify-tooling.sh`
- Agent tool verification:
  - `scripts/verify-agent-tools.sh`
- LangChain tool verification:
  - `scripts/verify-langchain-tools.sh`
- Verify all (health + tmux + tooling + dashboard JSON):
  - `scripts/verify-all.sh`
- One-time post-setup run with summary log:
  - `scripts/post-setup-run.sh`
  - Summary log: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/post-setup-summary.log`
  - Run log: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/post-setup-run.log`
- Weekly validation via launchd (installs + runs at load):
  - `scripts/install-validation-launchd.sh`
  - Logs: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-validation.out`
- Log rotation (newsyslog, requires sudo):
  - `sudo scripts/setup-newsyslog-rotation.sh`


## MCP Servers (Claude/Codex)
- Setup/sync: `scripts/setup-mcp-servers.sh`
- Alias: `mde-mcp-sync`
- Config file (common `.mcp.json` schema): `configs/mcp-servers.mcp.json`
- Override config path: `MDE_MCP_CONFIG=/path/to/mcp-servers.mcp.json`
- Installs wrapper scripts into `~/.local/bin` and updates:
  - Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Claude Code: `claude mcp add` (scope default: `user`)
  - Codex CLI: `codex mcp add`
- Managed servers (default): `github`, `langsmith`, `notebooklm`, `context7`,
  `brave-search`, `filesystem`, `MCP_DOCKER`.
- Override defaults:
  - `MDE_MCP_SCOPE=user|project|local` (Claude Code scope)
  - `MDE_MCP_FILESYSTEM_ROOTS="$HOME/dev:$HOME/Documents"` (colon-separated)
- Node-based CLIs (`claude`, `codex`) require Node; ensure mise shims are in PATH.

## Shell Configuration Notes
- Login shells (e.g., `zsh -lc`) load `~/.zprofile.d/macos-dev-env.zsh` to keep mise shims on PATH.
- `~/.local/bin` is prepended for managed wrappers (e.g., `claude`).
- `scripts/ensure-managed-configs.sh` keeps the zprofile include in sync.
- Homebrew curl is preferred in shell config when needed:
  - `export PATH="/opt/homebrew/opt/curl/bin:$PATH"`
- Managed oh-my-zsh custom files live under `templates/oh-my-zsh`.
  - Sync them with `scripts/ensure-managed-configs.sh`.
- When a `.env` file is loaded, keychain overrides are disabled by default (`MDE_SECRET_OVERRIDE=0`). Set `MDE_SECRET_OVERRIDE=1` to force keychain/1Password to win.

## LLVM (opt-in)
- Install/upgrade via Homebrew:
  - `brew install llvm` or `brew upgrade llvm`
- Keep Apple clang as default; opt into brewed LLVM per shell/project.
- Enabled by default via oh-my-zsh (managed). Set `MDE_USE_LLVM=0` before
  loading zsh to disable.
- Optional per-project via `direnv`:
  - `export PATH="/opt/homebrew/opt/llvm/bin:$PATH"`
  - `export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"`
  - `export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"`
  - `export PKG_CONFIG_PATH="/opt/homebrew/opt/llvm/lib/pkgconfig"`

## Secrets and Automation (non-interactive)
- Preferred: `.env` file loaded by both shells and launchd runs:
  - Default path: `~/.config/macos-development-environment/secrets.env`
  - Template: `templates/secrets.env.example`
  - Helper: `scripts/setup-secrets-env.sh --open`
  - Lock permissions: `chmod 600 ~/.config/macos-development-environment/secrets.env`
  - AWS (SkyPilot): add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`
  - Override path: `MDE_ENV_FILE=/path/to/secrets.env`
  - Disable autoload: `MDE_ENV_AUTOLOAD=0`
  - Override existing env: `MDE_ENV_OVERRIDE=1` (default)
  - Keychain/1Password override: `MDE_SECRET_OVERRIDE=1` (default is `0` when env file is loaded)
- Use a 1Password service account for unattended runs when available (no login prompts).
- Store the service account token in Keychain:
  - `security add-generic-password -a "$USER" -s mde-op-sa -w`
- Install the 1Password CLI (`op`) and ensure it is on `PATH`.
- Configure secret references in the launchd plist (references are not secrets):
  - `MDE_OP_GITHUB_TOKEN_REF=op://Vault/GitHub/token`
  - `MDE_OP_OPENAI_API_KEY_REF=op://Vault/OpenAI/api_key`
  - `MDE_OP_ANTHROPIC_API_KEY_REF=op://Vault/Anthropic/api_key`
  - `MDE_OP_LANGSMITH_API_KEY_REF=op://Vault/LangSmith/api_key`
  - `MDE_OP_LANGSMITH_WORKSPACE_ID_REF=op://Vault/LangSmith/workspace_id`
  - `MDE_OP_GEMINI_API_KEY_REF=op://Vault/Gemini/api_key`
  - `MDE_OP_BRAVE_API_KEY_REF=op://Vault/Brave/api_key` (optional)
- The maintenance script loads these into the environment when available.
- Gemini CLI reads `GEMINI_API_KEY` for unattended auth.
- Keychain fallback (local-only, no 1Password service account):
  - `security add-generic-password -a "$USER" -s mde-github-token -w`
  - `security add-generic-password -a "$USER" -s mde-openai-api-key -w`
  - `security add-generic-password -a "$USER" -s mde-anthropic-api-key -w` (optional)
  - `security add-generic-password -a "$USER" -s mde-langsmith-api-key -w` (optional)
  - `security add-generic-password -a "$USER" -s mde-langsmith-workspace-id -w` (service keys)
  - `security add-generic-password -a "$USER" -s mde-gemini-api-key -w` (optional)
  - `security add-generic-password -a "$USER" -s mde-brave-api-key -w` (optional)
- Keychain values are used only when `.env` and 1Password do not provide a value.
- For LangSmith personal keys, omit `LANGSMITH_WORKSPACE_ID` (service keys require it).
- `.gitignore` includes `.env` and `secrets.env` to prevent accidental check-in.
- Keep secrets out of `~/.oh-my-zsh/custom/*`; use `op run -- <cmd>` for ad-hoc work.
- For tmux, avoid global exports; prefer `op run -- tmux new-session ...` or per-session `setenv`.

## SkyPilot (AWS)
- Install with `scripts/install-agent-stack.sh` or `scripts/optimize-tmux.sh` (includes `skypilot[aws]`).
- Optional: install AWS CLI for richer status output (`mise use -g awscli@latest`).
- Add AWS keys to `~/.config/macos-development-environment/secrets.env`.

## AWS + Kubernetes Tooling
- Install core AWS + Kubernetes CLIs:
  - `scripts/install-aws-k8s-tools.sh`
- Verification:
  - `scripts/verify-aws-k8s-tools.sh`
- Optional tools include `eksctl`, `k9s`, `kubectx`, `kubens`, `stern`, and `session-manager-plugin`.
- Initialize config + validate access:
  - `scripts/setup-skypilot-aws.sh --init-config`
- Validate later with:
  - `scripts/setup-skypilot-aws.sh`
- Status + AWS details:
  - `scripts/sky-status.sh` (cache TTL via `MDE_SKY_AWS_TTL=120`)
- See `docs/tmux-cloud-workflow.md` for launch/stop workflows.

## UV Cache
- Default cache directory: `~/Library/Caches/uv` (set via `UV_CACHE_DIR`).
- Maintenance prune (optional): set `MDE_UV_CACHE_PRUNE=1` to run `uv cache prune`.
- To clean the old cache after switching: `UV_CACHE_DIR=~/.cache/uv uv cache clean`.
- Do not delete cache files manually; use `uv cache clean` or `uv cache prune`.

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
  - One-shot sudo wrapper (recommended):
    - `sudo scripts/setup-sudo-all.sh`
  - gcloud-only wrapper:
    - `sudo scripts/setup-gcloud-sudo-all.sh`
  - Manual (one-time):
    - `sudo mv ~/google-cloud-sdk /opt/google-cloud-sdk`
    - `sudo chown -R "$USER":staff /opt/google-cloud-sdk`
    - `/opt/google-cloud-sdk/install.sh --quiet --path-update false --command-completion false`
  - Automated (passwordless, least-privilege helper):
    - `sudo scripts/setup-gcloud-sudo-helper.sh`
    - Then maintenance will attempt migration via `/usr/local/sbin/mde-gcloud-migrate`.
    - The helper runs `install.sh` as your user and fixes `~/.config/gcloud`
      ownership if it was created by root.
  - If you see `PermissionError` under `~/.config/gcloud/virtenv`, fix ownership:
    - `sudo chown -R "$USER":staff ~/.config/gcloud`
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
- Agent guide: `docs/ai-agent-langchain-langsmith.md`
- Agent cheat sheet: `docs/ai-agent-langchain-langsmith-cheatsheet.md`
- Workflow optimization: `docs/langchain-langsmith-workflow-optimization.md`
- Agent playbook: `docs/agent-playbook.md`
- Weekly checklist: `docs/langchain-langsmith-weekly-checklist.md`
- Install/update script: `scripts/install-langchain-cli-tools.sh`
- `UV_TOOL_TIMEOUT_SECONDS=600` caps long installs (set to `0` to disable).
- `DOCS_MONOREPO_SUBMODULES=1` controls docs submodule cloning (set `0` to skip).
- `DOCS_MONOREPO_DEPTH=1` controls docs clone depth (set `0` for full history).
- `docs-monorepo` is patched during install to include `pipeline.*` + template data.

## AI Agent Stack
- Overview: `docs/agent-stack.md`
- Install/update script: `scripts/install-agent-stack.sh`
- mise guidance: `docs/mise-config.md`

## AI Research Skills Marketplace
- Overview: `docs/ai-research-skills.md`
- Install/update script: `scripts/install-ai-research-skills.sh`
- Verification script: `scripts/verify-ai-research-skills.sh`
- Set `MDE_AI_RESEARCH_FORCE=1` to reinstall all plugins.

## Tmux + Cloud Workflow
- Overview: `docs/tmux-cloud-workflow.md`
- Install/update script: `scripts/optimize-tmux.sh`
- Layout helper: `scripts/agent-hud`

## Decision Log
- Summary of key choices: `docs/decision-log.md`

## Quality + Multi-Agent
- Playbook: `docs/quality-playbook.md`
- Runner config: `docs/multi-agent-runner.md`
