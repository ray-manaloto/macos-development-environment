# mise Audit Report

Audited: 2026-02-28
Scope: How mise is configured, activated, and maintained across the macos-development-environment repository.

---

## 1. Overview

mise is the **primary runtime version manager** for this macOS development environment. It replaces nvm, volta, asdf, and pyenv as the single source of truth for language runtimes (Python, Node, Bun, Go, Rust) and a growing list of CLI tools. The toolchain precedence is:

```
mise shims > ~/.local/bin > bun > pixi > uv > Homebrew
```

mise is installed via `curl https://mise.run | sh` (see `ensure_mise_global()` in `scripts/macos-dev-maintenance.sh`). It is not Homebrew-managed.

---

## 2. Shell Activation

### Primary activation point

File: `templates/oh-my-zsh/macos-env.zsh` (line 12)

```zsh
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate zsh)"
fi
```

This file is loaded by oh-my-zsh as a custom config file. The activation guard (`command -v mise`) prevents errors if mise is not yet installed.

### Known duplicate activation

A duplicate `eval "$(mise activate zsh)"` exists in `~/.zshrc` (approximately line 89). The template file documents this:

```
# NOTE: If ~/.zshrc also calls `mise activate zsh`, the activation runs twice.
# This is harmless but adds ~5ms. Remove the duplicate from ~/.zshrc if present.
```

### PATH ordering

`macos-env.zsh` (lines 44-56) enforces a strict PATH order using zsh array manipulation:

```
1. ~/.local/share/mise/shims      (mise shim directory)
2. ~/.local/share/mise/bin         (mise binary directory)
3. ~/.local/bin                    (uv/pip tools, Go binaries)
4. ~/.bun/bin                      (bun global installs)
5. ~/.pixi/bin                     (pixi global installs)
6. ~/.amp/bin
7. ~/.antigravity/antigravity/bin
8. ~/.oh-my-zsh/custom/bin
9. /opt/google-cloud-sdk/bin
10. /opt/homebrew/opt/curl/bin
11. (everything else)
```

Mise shims are always first on PATH. The `typeset -U path` ensures no duplicates.

### Non-interactive / script contexts

`scripts/macos-dev-maintenance.sh` does NOT use `eval "$(mise activate bash)"`. Instead, it manually constructs PATH with mise shims first (line 173):

```bash
export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:..."
```

This is the correct approach for launchd jobs and non-interactive scripts.

`scripts/install-agent-stack.sh` uses `eval "$(mise activate bash)"` (line 58), which is appropriate because it runs interactively.

---

## 3. Managed Runtimes

### Core runtimes (from global config and scripts)

| Runtime | Version Spec | Set By |
|---------|-------------|--------|
| python | `latest` | `~/.config/mise/config.toml` `[tools]` |
| node | `latest` | `~/.config/mise/config.toml` `[tools]` |
| bun | `latest` | `~/.config/mise/config.toml` `[tools]` |
| go | `latest` | `~/.config/mise/config.toml` `[tools]` |
| rust | `latest` | `~/.config/mise/config.toml` `[tools]` |
| uv | `latest` | `~/.config/mise/config.toml` `[tools]` |
| pixi | `latest` | `~/.config/mise/config.toml` `[tools]` |

### Additional tools managed by mise (from global config)

**Modern Rust-based CLI tools:**
starship, ripgrep, fd, zoxide, bat, eza, fzf, delta, lsd, hyperfine, glow, atuin, ast-grep

**Data processing:** jq, yq

**Code quality:** shellcheck, hadolint, pre-commit (pipx backend), mgrep (pipx backend)

**Infrastructure:** 1password-cli, aws-cli (with `symlink_bins = true`), azure-cli

**Development:** chezmoi, usage, pkl, pitchfork, lefthook, github-cli

**Container tools:** devpod (aqua backend)

**Security:** age (aqua backend)

**Testing:** bats (npm backend), gum (ubi backend)

**AI agents (npm backend):** gemini-cli, ralph-cli, claude-code, codex, opencode-ai, mermaid-cli, jscpd, openspec, biome

### Supplemental Python version

`scripts/install-agent-stack.sh` and `scripts/install-langchain-cli-tools.sh` use `TOOL_PYTHON_VERSION=3.12` as a secondary pinned Python for tool isolation. This is installed alongside `python@latest` via `mise install -q python@${TOOL_PYTHON_VERSION}`.

---

## 4. Configuration Files

| Path | Purpose | Notes |
|------|---------|-------|
| `~/.config/mise/config.toml` | **Global config (source of truth)** | Contains `[settings]`, `[tools]`, `[tasks]`, `[env]` |
| `docs/mise-config.md` (repo) | Minimal example/documentation | Shows recommended `[tools]` and `[env]` structure |
| No `.mise.toml` in repo root | -- | This repo does not use a project-level mise config |
| No `.tool-versions` in repo root | -- | Not using the legacy format |

### Global config settings

```toml
[settings]
experimental = true
not_found_auto_install = true
status = { missing_tools = "if_other_versions_installed" }

[settings.npm]
package_manager = "bun"       # Uses bun for npm backend installs (3x faster)

[settings.python]
uv_venv_auto = true           # Auto-creates venvs with uv

[env]
EDITOR = "zed --wait"
```

### Key settings details

- `experimental = true`: Enables newer mise features (backends, tasks, etc.)
- `not_found_auto_install = true`: Automatically installs tools when a command is not found
- `package_manager = "bun"`: npm-backend tools (claude-code, codex, etc.) are installed via bun instead of npm
- `uv_venv_auto = true`: Python virtualenvs are automatically created using uv

### Lockfile / trust strategy

No explicit `trusted_config_paths` is set in the global config. Scripts that run non-interactively (e.g., `install-agent-stack.sh`) pass `--yes` flags to mise commands to bypass interactive trust prompts. There is no `mise.lock` file in the repository.

---

## 5. Update / Maintenance Flow

### Automated maintenance (launchd, every 12 hours)

The `scripts/macos-dev-maintenance.sh` script runs the `update_mise()` function (lines 336-346):

```bash
update_mise() {
  mise self-update --yes || return 1    # Update mise itself
  mise upgrade --yes || return 1        # Upgrade all installed tool versions
  mise reshim || true                   # Rebuild shims
}
```

This runs in sequence after `update_brew` and before `update_bun`, `update_uv`, and `update_pixi`.

### Full maintenance order

1. `update_brew` -- Homebrew formula and cask upgrades
2. **`update_mise`** -- Self-update, tool upgrades, reshim
3. `update_bun` -- Bun globals (skips `bun upgrade` if mise-managed)
4. `update_uv` -- uv self-update (skips if mise-managed or Homebrew-managed), `uv tool upgrade --all`
5. `update_pixi` -- pixi self-update + global update
6. `update_agent_tools` -- Runs `install-agent-stack.sh` and `install-langchain-cli-tools.sh`

### Autofix mode

When `MDE_AUTOFIX=1`, the maintenance script additionally:

1. Calls `ensure_mise_global()` which runs `mise use -g --yes python@latest node@latest bun@latest go@latest rust@latest`
2. Removes conflicting managers (nvm, volta, asdf, pyenv)
3. Syncs managed configs

When `MDE_AUTOFIX_STRICT=1`, it also removes brew-managed runtimes (node, python, go, rust) in favor of mise.

### Bun upgrade guard

`update_bun()` detects if bun is mise-managed by checking its path:

```bash
case "$bun_path" in
  "$HOME/.local/share/mise/installs/bun/"*)
    ;;  # Skip bun upgrade; mise handles it
  *)
    bun upgrade || return 1
    ;;
esac
```

The same guard pattern exists for uv in `update_uv()`.

---

## 6. Integration Points

### With bun

- mise manages the bun runtime version
- mise's npm backend uses bun as the package manager (`package_manager = "bun"` in settings)
- `install-agent-stack.sh` installs Node tools via `bun add -g`
- `bun upgrade` is skipped when bun is mise-managed to avoid version conflicts

### With uv

- mise manages the uv binary version
- `UV_PYTHON_DOWNLOADS=never` is set in `macos-env.zsh` and all install scripts to prevent uv from downloading its own Python -- mise owns Python runtimes
- uv is used as a tool installer (`uv tool install --upgrade`) with `UV_PYTHON` pointed at the mise-managed Python
- `uv self update` is skipped when uv is mise-managed or Homebrew-managed

### With pixi

- mise manages the pixi binary version
- pixi is used for global conda-forge environments (e.g., `agent-stack`, `langchain-cli-tools`)
- pixi is a fallback installer for Python tools before uv

### With Homebrew

- Homebrew is the lowest-priority tool source
- Strict cleanup mode removes brew-managed runtimes that overlap with mise
- Some brew formulas are kept when they have dependents (e.g., python is kept if llvm depends on it)

### With the migration script

`scripts/mde-migrate-to-mise.sh` migrates individual runtimes from Homebrew to mise:

```bash
migrate_runtime "node" "node"
migrate_runtime "go" "go"
migrate_runtime "rust" "rust"
# python guarded: llvm may depend on it
```

It runs in dry-run mode by default (`MDE_MIGRATE_DRY_RUN=1`). Each migration calls `mise use -g --yes "${mise_tool}@latest"` then `brew uninstall`. An alias `mde-migrate` is defined in `templates/oh-my-zsh/aliases.zsh`.

### With mise tasks

The global config defines extensive `[tasks]` for cloud operations:

- `mise run dashboard` -- Launch TUI
- `mise run validate` -- Environment health check
- `mise run lint` -- Shellcheck all scripts
- `mise run agent:check/up/down/status/stop/start` -- SkyPilot cluster management
- `mise run auth:claude/codex/gemini/opencode` -- CLI authentication helpers
- `mise run env:status` -- Environment status dashboard
- Various `setup:*` and `aws:*` tasks

---

## 7. Known Issues or Gaps

### Duplicate `mise activate zsh`

`eval "$(mise activate zsh)"` runs twice per interactive shell (once in `macos-env.zsh`, once in `~/.zshrc`). This wastes approximately 5ms per prompt. The fix is to remove the `~/.zshrc` line, keeping the template-managed copy as authoritative.

### No project-level mise config

This repository has no `.mise.toml` or `mise.toml`. All tool versions are pinned globally. This means contributors cannot `git clone` and immediately get the right tool versions -- they must set up the global config manually.

### All versions pinned to `latest`

Every tool in the global config uses `version = "latest"`. This means `mise upgrade` can introduce breaking changes. There are no lockfiles (`mise.lock`) to pin resolved versions.

### No `trusted_config_paths` in global settings

The global config does not set `trusted_config_paths`. Scripts work around this by passing `--yes` flags, but new project-level `.mise.toml` files require manual `mise trust` approval.

### Python migration blocked by llvm

The migration script guards against removing brew-managed Python when llvm depends on it. This is documented but means Python migration is incomplete on machines with llvm installed.

### Missing `mise activate --shims` in `.zprofile`

The mise documentation recommends placing `eval "$(mise activate --shims)"` in `~/.zprofile` for non-interactive contexts (IDE terminals, launchd jobs). The current setup uses manual PATH construction instead, which works but requires maintenance when mise's shim directory changes.

### `UV_PYTHON_DOWNLOADS` vs `UV_NO_MANAGED_PYTHON`

The codebase uses `UV_PYTHON_DOWNLOADS=never` (newer uv flag), but `docs/mise-config.md` shows `UV_NO_MANAGED_PYTHON=1` (older flag). These are functionally equivalent but the documentation is inconsistent.
