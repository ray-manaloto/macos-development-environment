# Tool Audit Integration Report

Date: 2026-02-28
Status: PASS (4 warnings, 6 drift items)

---

## 1. Executive Summary

The macOS development environment is **healthy and functional**. All 5 language runtimes (Python 3.14.3, Node 25.7.0, Bun 1.3.10, Go 1.26.0, Rust 1.93.1) resolve correctly through mise shims. All 9 key binaries resolve via mise direct installs. Homebrew v5.0.15, Bun v1.3.10 (2609 global packages), and uv v0.10.7 are operational.

The audit surfaced one systemic issue and several cosmetic concerns:

- **Systemic issue:** The template-to-deploy sync pipeline is gated behind `MDE_AUTOFIX=1` (defaults to 0), meaning template changes in the repository never auto-propagate to `~/.oh-my-zsh/custom/`. This caused the 6 `mde-*` lifecycle aliases to be missing from the live shell. The alias-fixer agent resolved this by running `ensure-managed-configs.sh` directly.

- **Cosmetic concerns:** Duplicate binaries for bun, uv, and pixi coexist across mise installs and standalone install paths. Homebrew still owns `python` and `python@3.14` formulas (blocked by llvm dependency). These are shadowed by mise in PATH and do not cause functional problems.

No critical (P0) issues were found. The environment is production-ready with recommended improvements listed in Section 7.

---

## 2. Tool Integration Map

### PATH Resolution Order (highest priority first)

```
Position  Directory                           Owner     Purpose
--------  ----------------------------------  --------  --------------------------------
1         ~/.local/share/mise/shims           mise      Runtime shims (python, node, bun, go, rust)
2         ~/.local/share/mise/bin             mise      mise binary itself
3         ~/.local/bin                        mixed     Go binaries (GOBIN), uv/pip tools, wrapper scripts
4         ~/.bun/bin                          bun       Global JS packages (bun add -g)
5         ~/.pixi/bin                         pixi      Global conda-forge packages
6         ~/.amp/bin                          amp       Amp tool
7         ~/.antigravity/antigravity/bin      misc      Antigravity tool
8         ~/.oh-my-zsh/custom/bin             oh-my-zsh Custom shell scripts
9         /opt/google-cloud-sdk/bin           gcloud    Google Cloud SDK
10        /opt/homebrew/opt/curl/bin          brew      Keg-only curl (newer TLS)
11        /opt/homebrew/bin                   brew      Homebrew formulas
12        /opt/homebrew/sbin                  brew      Homebrew system binaries
13        /usr/local/bin                      system    macOS system binaries
```

### Data Flow Between Tools

```
mise (runtime manager)
  |
  +---> Python runtimes ---> uv (tool installer, UV_PYTHON_DOWNLOADS=never)
  |                    \---> pixi (fallback tool installer)
  |
  +---> Node runtime -----> bun (preferred JS package manager)
  |                    \---> npm (compatibility fallback)
  |
  +---> Bun runtime ------> bun add -g (global JS tools)
  |                    \---> mise npm backend (package_manager = "bun")
  |
  +---> Go runtime
  +---> Rust runtime
  +---> CLI tools (starship, ripgrep, fd, jq, etc.)
  |
  +---> uv binary (aqua backend)
  +---> pixi binary

Homebrew (OS-level packages only)
  +---> gnupg, tmux, llvm, curl, git
  +---> Fallback for AWS/K8s tools (mise-first, brew-fallback)
```

### Update Pipeline Order

```
1. brew update + brew upgrade (formulas, non-sudo casks)
2. mise self-update -> mise upgrade --yes -> mise reshim
3. bun update -g --latest (skip bun upgrade when mise-managed)
4. uv self update (skip when mise/brew-managed) + uv tool upgrade --all
5. pixi self-update + pixi global update
6. Agent tools (install-agent-stack.sh, install-langchain-cli-tools.sh)
7. Config sync (only when MDE_AUTOFIX=1)
```

---

## 3. Validation Results

### Runtime Checks

| Check | Result | Details |
|-------|--------|---------|
| Python 3.14.3 | PASS | Resolves via mise shim |
| Node 25.7.0 | PASS | Resolves via mise shim |
| Bun 1.3.10 | PASS | Resolves via mise shim |
| Go 1.26.0 | PASS | Resolves via mise shim |
| Rust 1.93.1 | PASS | Resolves via mise shim |

### Binary Resolution Checks

| Check | Result | Details |
|-------|--------|---------|
| All 9 key binaries | PASS | Resolve via mise direct installs |
| Homebrew v5.0.15 | PASS | Operational |
| Bun v1.3.10 (2609 packages) | PASS | Global packages functional |
| uv v0.10.7 | PASS | Tool installer operational |

### Alias Checks

| Check | Result | Details |
|-------|--------|---------|
| 5 mde-* aliases resolve | PASS | After alias-fixer sync |
| mde-agents-review alias | PASS | After alias-fixer sync |
| Templates match deployed files | PASS | After alias-fixer sync |

### Warnings

| # | Warning | Severity | Details |
|---|---------|----------|---------|
| W1 | Multiple claude binaries | Low | mise shim and direct install coexist (cosmetic) |
| W2 | Brew owns python/python@3.14 | Medium | Homebrew formula present alongside mise-managed Python |
| W3 | Duplicate bun/uv/pixi binaries | Low | mise install paths coexist with standalone install paths |
| W4 | Bun completions symlink missing | Low | `~/.bun/_bun` exists but not symlinked to fpath |

---

## 4. Cross-Tool Issues

### 4.1 Dual Python Ownership (mise + Homebrew)

**Tools involved:** mise, Homebrew

Homebrew still owns `python` and `python@3.14` formulas because `llvm` depends on them. The mise-managed Python (also 3.14.3) takes precedence via PATH ordering, but the brew Python continues to exist at `/opt/homebrew/bin/python3`. This is correctly guarded in both `mde-migrate-to-mise.sh` and `macos-dev-maintenance.sh` -- Python migration is skipped when llvm is installed.

**Risk:** Low. PATH ordering ensures mise Python wins. The brew Python could cause confusion if a user runs `/opt/homebrew/bin/python3` directly.

### 4.2 Triple Binary Locations (bun, uv, pixi)

**Tools involved:** mise, standalone installers

Each of bun, uv, and pixi has binaries at two locations:

| Tool | mise path | Standalone path |
|------|-----------|-----------------|
| bun | `~/.local/share/mise/installs/bun/1.3.10/bin/bun` | `~/.bun/bin/bun` |
| uv | `~/.local/share/mise/installs/uv/*/bin/uv` | `~/.local/bin/uv` (if standalone-installed) |
| pixi | `~/.local/share/mise/installs/pixi/*/bin/pixi` | `~/.pixi/bin/pixi` |

In all cases, mise shims resolve first in PATH. The standalone binaries are shadowed but present on disk.

**Risk:** Low. Wastes disk space (~60 MB for standalone bun). Could cause confusion during debugging.

### 4.3 Template-Deploy Pipeline Gap Across All Tools

**Tools involved:** oh-my-zsh, mise, uv, bun

The `ensure-managed-configs.sh` deployment script is gated behind `MDE_AUTOFIX=1`. This means changes to `macos-env.zsh` (which sets `UV_PYTHON_DOWNLOADS`, `BUN_INSTALL`, mise activation, and PATH ordering) do not propagate automatically. Any template change affecting any tool's configuration requires manual intervention.

Specific stale configurations found in the deployed files before the alias-fixer ran:
- `UV_NO_MANAGED_PYTHON=1` instead of `UV_PYTHON_DOWNLOADS=never`
- Bun completion `source` line instead of fpath-based loading
- Missing `mde-*` lifecycle aliases

### 4.4 Bun as mise npm Backend Creates Circular Dependency

**Tools involved:** mise, bun

mise uses bun as its npm backend (`package_manager = "bun"`), but mise also manages the bun runtime version. This creates a bootstrap dependency: mise needs bun to install npm-backend tools, but bun itself is installed by mise. In practice this works because mise installs bun first (as a direct tool), then uses it for npm-backend installs. But if the bun installation fails, all npm-backend tools (claude-code, codex, gemini-cli, etc.) become uninstallable.

**Risk:** Low. The bootstrap order is correct. Would only matter if bun installation fails.

### 4.5 No Unified Verification Pipeline

**Tools involved:** All

Verification is fragmented across multiple scripts:
- `verify-tooling.sh` -- delegates to sub-scripts but has no bun-specific checks
- `verify-all.sh` -- orchestrates verification but does not verify brew formula state
- `mde-drift-check.sh` -- checks for runtime ownership drift but not config drift
- `verify-langchain-tools.sh` -- checks uv tools but not pixi-installed tools

No single command validates the entire toolchain end-to-end.

---

## 5. Root Cause Analysis: Template-Deploy Sync Gap

### What happened

The 6 `mde-*` lifecycle aliases (`mde-update`, `mde-update-fast`, `mde-verify`, `mde-drift`, `mde-migrate`, `mde-agents-review`) were added to the template file `templates/oh-my-zsh/aliases.zsh` but never deployed to `~/.oh-my-zsh/custom/aliases.zsh`. Running any of these aliases produced "command not found".

### Why it happened

The deployment pipeline (`ensure-managed-configs.sh`) uses a **copy strategy** (not symlinks). Templates are copied from the repo to `~/.oh-my-zsh/custom/` only when the script runs. The script is called from `macos-dev-maintenance.sh`, but only inside an `MDE_AUTOFIX=1` guard block.

```
MDE_AUTOFIX defaults to 0
  -> macos-dev-maintenance.sh skips sync_managed_configs()
    -> ensure-managed-configs.sh never runs
      -> template changes never propagate to deployed files
```

The 12-hour launchd job runs `macos-dev-maintenance.sh` without `MDE_AUTOFIX=1`. The `mde-update` alias (once it works) also runs without `MDE_AUTOFIX=1`. There is no mechanism to detect or alert when deployed configs are stale.

### Contributing factors

1. **Copy, not symlink:** If symlinks were used, template changes would propagate instantly.
2. **No checksum comparison:** The deployment script always copies but never checks if files differ. There is no `--check` or `--dry-run` mode.
3. **No shell startup warning:** The shell does not check if deployed configs are stale relative to templates.
4. **Autofix is conservative by design:** `MDE_AUTOFIX=0` is intentional to avoid unexpected changes during routine maintenance. However, config sync is non-destructive and could safely run unconditionally.

### How it was fixed

The alias-fixer agent ran `ensure-managed-configs.sh` directly, which copied the updated templates to `~/.oh-my-zsh/custom/`. All 6 aliases now resolve correctly.

### Recommended permanent fix

Move `sync_managed_configs()` outside the `MDE_AUTOFIX` guard in `macos-dev-maintenance.sh`, or add a separate always-on config sync step. Config file syncing is idempotent and non-destructive (it only overwrites files containing the managed marker), so running it unconditionally is safe.

---

## 6. Drift Inventory

| # | Drift Warning | Severity | Tool Pair | Remediation |
|---|---------------|----------|-----------|-------------|
| D1 | brew owns runtime `python` | Medium | brew + mise | Blocked by llvm dependency. No action unless llvm is removed. Run `MDE_AUTOFIX_STRICT=1` after uninstalling llvm to clean up. |
| D2 | brew owns runtime `python@3.14` | Medium | brew + mise | Same root cause as D1 (llvm dependency). |
| D3 | mise shims not first in PATH (oh-my-opencode at #1) | Low (benign) | mise + oh-my-zsh | An oh-my-zsh plugin prepends its path before mise shims. Benign because oh-my-opencode does not shadow any runtime binaries. No action needed. |
| D4 | bun found at multiple locations | Low | mise + standalone | Remove `~/.bun/bin/bun` and `~/.bun/bin/bunx` (keep `~/.bun/bin/` for global packages). |
| D5 | uv found at multiple locations | Low | mise + standalone | Remove standalone uv if present outside mise paths. Verify with `which -a uv`. |
| D6 | pixi found at multiple locations | Low | mise + standalone | Remove standalone pixi at `~/.pixi/bin/pixi` if mise manages pixi. Keep `~/.pixi/bin/` for global packages. |

---

## 7. Actionable Fixes

### P1 -- Should Fix (recommended for next maintenance cycle)

| # | Fix | Impact | Effort | Details |
|---|-----|--------|--------|---------|
| F1 | Move config sync outside MDE_AUTOFIX guard | High | Low | In `scripts/macos-dev-maintenance.sh`, call `sync_managed_configs` unconditionally (not gated by `MDE_AUTOFIX`). This prevents future template-deploy sync gaps. |
| F2 | Create a Brewfile | Medium | Low | Run `brew bundle dump --file=Brewfile` to capture current state. Add `brew bundle check` to verification. Prevents brew package drift. |
| F3 | Update stale docs for UV_PYTHON_DOWNLOADS | Medium | Low | Replace `UV_NO_MANAGED_PYTHON=1` with `UV_PYTHON_DOWNLOADS=never` in `docs/mise-config.md`, `docs/setup-notes.md`, and `docs/decision-log.md`. |
| F4 | Wire bun completions symlink | Low | Trivial | Run: `ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun`. Add this to `ensure-managed-configs.sh`. |
| F5 | Add bun verification to verify-tooling.sh | Medium | Low | Add `bun --version` and global package count check. Currently no bun-specific verification exists. |

### P2 -- Nice to Have (backlog)

| # | Fix | Impact | Effort | Details |
|---|-----|--------|--------|---------|
| F6 | Remove stale standalone bun binary | Low | Trivial | `rm ~/.bun/bin/bun ~/.bun/bin/bunx` -- saves ~57 MB, reduces confusion. |
| F7 | Remove stale mise bun 1.3.8 | Low | Trivial | `mise uninstall bun@1.3.8` -- cleanup unused version. |
| F8 | Remove duplicate mise activate in ~/.zshrc | Low | Trivial | Remove `eval "$(mise activate zsh)"` from `~/.zshrc` (keep the copy in `macos-env.zsh`). Saves ~5ms per shell startup. |
| F9 | Add shell startup drift warning | Medium | Medium | In `macos-env.zsh`, compare template and deployed file checksums on shell startup. Warn if stale. |
| F10 | Add `brew doctor` to health check | Low | Low | Run `brew doctor` in `scripts/health-check.sh` or `scripts/verify-tooling.sh`. |
| F11 | Add `--check` mode to ensure-managed-configs.sh | Medium | Medium | Report which files are out of sync without modifying them. Useful for drift detection. |
| F12 | Consolidate pixi/uv tool overlap | Medium | Medium | Standardize on one installer per tool. Currently pixi-first/uv-fallback means verify scripts may miss pixi-installed tools. |
| F13 | Pin TOOL_PYTHON_VERSION to 3.13+ | Low | Low | Currently pinned to 3.12. Consider upgrading as 3.12 approaches end-of-bugfix. |
| F14 | Add mise shims to .zprofile | Low | Low | Add `eval "$(mise activate --shims)"` to `~/.zprofile` for non-interactive contexts. Currently using manual PATH construction. |

---

## 8. Tool Ownership Matrix

Based on the toolchain precedence model and audit findings.

### Runtime Ownership

| Runtime | Authoritative Owner | Secondary (shadowed) | Notes |
|---------|-------------------|---------------------|-------|
| Python 3.14.x | **mise** | Homebrew (blocked by llvm) | mise shims win via PATH; brew python persists as llvm dependency |
| Node 25.x | **mise** | -- | `MDE_AUTOFIX_STRICT` removes brew node |
| Bun 1.3.x | **mise** | Standalone (`~/.bun/bin/bun`) | mise shims shadow standalone; standalone kept for global package dir |
| Go 1.26.x | **mise** | -- | `MDE_AUTOFIX_STRICT` removes brew go |
| Rust 1.93.x | **mise** | -- | `MDE_AUTOFIX_STRICT` removes brew rust |

### Tool Installer Ownership

| Installer | Owns | Does NOT Own |
|-----------|------|--------------|
| **mise** | Runtime versions, CLI tools (starship, ripgrep, jq, etc.), uv binary, pixi binary, bun binary | OS-level packages |
| **bun** (`bun add -g`) | JS/Node CLI packages (claude-code, codex, gemini-cli, typescript, etc.) | Runtime versions |
| **uv** (`uv tool install`) | Python CLI tools (langchain-cli, skypilot, aider, crewai, etc.) | Python runtimes (`UV_PYTHON_DOWNLOADS=never`) |
| **pixi** (`pixi global install`) | Conda-forge packages, fallback for Python tools | Runtime versions |
| **Homebrew** | OS-level packages (gnupg, tmux, curl, git, llvm), fallback for AWS/K8s tools | Language runtimes (actively migrated away) |

### Configuration Ownership

| Config Domain | Owner | File |
|---------------|-------|------|
| Runtime versions | mise | `~/.config/mise/config.toml` |
| PATH ordering | oh-my-zsh template | `templates/oh-my-zsh/macos-env.zsh` |
| Shell aliases | oh-my-zsh template | `templates/oh-my-zsh/aliases.zsh` |
| Environment variables | oh-my-zsh template | `templates/oh-my-zsh/macos-env.zsh` |
| Secrets | macOS Keychain + env file | `~/.config/macos-development-environment/secrets.env` |
| Automated maintenance | launchd + script | `scripts/macos-dev-maintenance.sh` |
| Config deployment | script | `scripts/ensure-managed-configs.sh` |

### Binary Resolution Examples

| Command | Resolves To | Owner |
|---------|-------------|-------|
| `python3` | `~/.local/share/mise/shims/python3` -> mise Python 3.14.3 | mise |
| `node` | `~/.local/share/mise/shims/node` -> mise Node 25.7.0 | mise |
| `bun` | `~/.local/share/mise/shims/bun` -> mise Bun 1.3.10 | mise |
| `uv` | `~/.local/share/mise/shims/uv` -> mise uv 0.10.7 | mise |
| `claude` | `~/.local/bin/claude` -> `scripts/claude-wrapper.sh` | MDE wrapper |
| `langchain-cli` | `~/.local/bin/langchain-cli` -> uv tool venv | uv |
| `tmux` | `/opt/homebrew/bin/tmux` | Homebrew |
| `gpg` | `/opt/homebrew/bin/gpg` | Homebrew |

---

## Appendix: Source Reports

This report aggregates findings from the following individual audit reports:

1. `docs/tool-audit/mise-report.md` -- mise configuration, activation, managed runtimes, and integration points
2. `docs/tool-audit/homebrew-report.md` -- Homebrew packages, update flow, and brew/mise overlap
3. `docs/tool-audit/oh-my-zsh-report.md` -- Template deployment, shell startup flow, sync gap analysis
4. `docs/tool-audit/bun-report.md` -- Bun installation, global packages, completions, and update flow
5. `docs/tool-audit/uv-report.md` -- uv installation, Python integration, tool inventory, and migration history

Validation data provided by the tool-validator and alias-fixer agents.
