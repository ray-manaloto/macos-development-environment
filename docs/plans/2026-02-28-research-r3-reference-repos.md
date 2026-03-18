# Research Report R3: Reference Repository Analysis

## Sources Consulted

| # | Source | Method | Date Accessed |
|---|--------|--------|---------------|
| 1 | [thoughtbot/laptop](https://github.com/thoughtbot/laptop) README | WebFetch | 2026-02-28 |
| 2 | thoughtbot/laptop `mac` script (raw) | WebFetch | 2026-02-28 |
| 3 | [br3ndonland/dotfiles](https://github.com/br3ndonland/dotfiles) README | WebFetch | 2026-02-28 |
| 4 | br3ndonland/dotfiles `bootstrap.sh` | WebFetch | 2026-02-28 |
| 5 | br3ndonland/dotfiles `Brewfile` | WebFetch | 2026-02-28 |
| 6 | br3ndonland/dotfiles `.config/mise/config.toml` | WebFetch | 2026-02-28 |
| 7 | br3ndonland/dotfiles `scripts/symlink.sh` | WebFetch | 2026-02-28 |
| 8 | [basnijholt/dotfiles](https://github.com/basnijholt/dotfiles) README | WebFetch | 2026-02-28 |
| 9 | basnijholt/dotfiles `install` script | WebFetch | 2026-02-28 |
| 10 | basnijholt/dotfiles `install.conf.yaml` (dotbot) | WebFetch | 2026-02-28 |
| 11 | basnijholt/dotfiles `scripts/` directory listing | WebFetch | 2026-02-28 |
| 12 | basnijholt/dotfiles `configs/shell/main.sh` | WebFetch | 2026-02-28 |
| 13 | basnijholt/dotfiles `scripts/bootstrap.sh` | WebFetch | 2026-02-28 |
| 14 | [rjallais/dotfiles](https://github.com/rjallais/dotfiles) (chezmoi+mise) | WebFetch | 2026-02-28 |
| 15 | [marcus-crane/dotfiles](https://github.com/marcus-crane/dotfiles/blob/main/dot_config/mise/config.toml.tmpl) | WebFetch | 2026-02-28 |
| 16 | GitHub search: "mise config.toml dotfiles" | WebSearch | 2026-02-28 |
| 17 | GitHub search: "dotfiles idempotent bootstrap script pattern" | WebSearch | 2026-02-28 |
| 18 | [dotfiles.github.io/bootstrap](https://dotfiles.github.io/bootstrap/) | WebSearch | 2026-02-28 |

---

## Key Findings (Numbered)

### Finding 1: thoughtbot/laptop Idempotency Mechanism

The `mac` script uses **per-operation guard checks** rather than a single global state file. Each operation independently detects its current state and skips/upgrades accordingly:

- **Homebrew**: `command -v brew` check before installing
- **Shell text appending**: `grep -Fqs` prevents duplicate entries in `.zshrc`
- **asdf plugins**: `asdf plugin list | grep -Fq` before adding
- **Language versions**: `asdf list <lang>` checks before installing
- **Ruby gems**: `gem list --installed` determines install vs. update
- **Rosetta 2**: Architecture detection (`uname -m`) before installing

There is no centralized "already-done" file. Each step is individually idempotent. This is the simplest viable pattern.

### Finding 2: thoughtbot/laptop Logging Pattern

- **`fancy_echo()`**: A `printf`-based wrapper that adds newlines. Used for human-readable progress.
- **Log capture**: `sh mac 2>&1 | tee ~/laptop.log` captures both stdout/stderr to `~/laptop.log`.
- **Error handling**: `set -e` with a `trap` that prints "failed" to stderr on non-zero exit.
- **No dry-run support**. No `--dry-run` flag. No `--verbose` flag. The script either runs or fails.

### Finding 3: thoughtbot/laptop Brew Boundary

The script uses a single `brew bundle --file=-` heredoc that lists ALL formulae and casks inline. There is **no separation** between brew-owned and externally-owned tools -- everything runs through `brew bundle`. The boundary is implicit: runtimes (Ruby, Node) are managed by asdf *after* brew installs asdf itself.

Pattern: **brew provides asdf, asdf provides runtimes**. Brew never owns runtime versions directly.

### Finding 4: br3ndonland/dotfiles mise-en-place Integration

Location: `.config/mise/config.toml`

Structure:
```toml
[settings]
# Aggressive activation, idiomatic version files enabled
# pipx uses uvx, python/ruby use precompiled binaries

[tasks.check]   # Runs prettier, shellcheck, shfmt, tombi checks
[tasks.format]  # Runs formatters

[tools]
# Languages: go@1, node@22, node@24, python@3.12, python@3.13, python@3.14, ruby@3, rust@latest
# Utilities: gh, helm, jq, k9s, kubectl, minikube, opentofu, rclone, ruff, shellcheck, shfmt, uv, yt-dlp
# Via npm: prettier, typescript
# Via pipx: basedpyright, hatch, httpie, tombi
```

Key design choices:
- **Multiple concurrent versions** of Node (22, 24) and Python (3.12, 3.13, 3.14)
- **mise tasks** for code quality (check/format) baked into config.toml
- **`pipx_uvx = true`** setting to use `uvx` instead of `pipx`
- **Precompiled binaries** enabled for Python and Ruby (faster installs)
- **Idiomatic version files** enabled for go, node, python, ruby, terraform

### Finding 5: br3ndonland/dotfiles Bootstrap Variables and Flow

The `bootstrap.sh` uses a strict environment variable contract:

**Required (script exits if unset):**
- `STRAP_GIT_NAME` -- uses `:?` parameter expansion to fail immediately
- `STRAP_GIT_EMAIL` -- same

**Optional with defaults:**
- `STRAP_GITHUB_USER` -- defaults to "br3ndonland"
- `STRAP_DOTFILES_URL` -- defaults to GitHub URL
- `STRAP_DOTFILES_BRANCH` -- defaults to "main"
- `STRAP_CI` -- controls CI-specific behavior
- `STRAP_DEBUG` -- enables verbose output
- `STRAP_INTERACTIVE` -- manages interactive prompts

**10-step execution flow:**
1. System detection (OS, architecture, Homebrew prefix)
2. Privilege escalation (sudo with credential management)
3. Security configuration (macOS defaults)
4. Git setup (first pass for dotfiles cloning)
5. Dotfiles clone (only if `~/.dotfiles` absent)
6. Symlink installation (`scripts/symlink.sh`)
7. Git reconfiguration (second pass, CI-aware)
8. Homebrew installation (if `brew` command absent)
9. Package installation (`brew bundle` with skip rules)
10. Post-setup hook (`scripts/strap-after-setup.sh`)

### Finding 6: br3ndonland/dotfiles Verify/Check Pattern

Uses `brew bundle check` as a pre-flight before `brew bundle install`:

```bash
# Only install if check fails
brew bundle check || brew bundle install
```

Additionally uses **dynamic skip lists** to avoid reinstalling things:
- `HOMEBREW_BUNDLE_BREW_SKIP` -- formulae to skip
- `HOMEBREW_BUNDLE_CASK_SKIP` -- dynamically generated from already-installed casks
- `HOMEBREW_BUNDLE_MAS_SKIP` -- extracted from Brewfile MAS IDs

The Brewfile itself enforces `require_sha: true` for cask integrity verification.

### Finding 7: basnijholt/dotfiles Cross-Machine Reproducibility

Runs across 10+ machines (arm64 macOS, x86_64/aarch64 Ubuntu, Debian, NixOS, Raspberry Pi, etc.).

**Three-layer reproducibility:**

1. **Dotbot** (`install.conf.yaml`): Declarative symlink manifest with `create: true`, `relink: true`, `force: true`. Handles 60+ config files/directories.
2. **dotbins** (`dotbins.yaml`): Platform-specific binary management. Downloads correct architecture binaries automatically.
3. **Nix-darwin** (macOS): Pure functional system configuration via flake. `nixswitch` alias runs `darwin-rebuild switch --flake ~/dotfiles/configs/nix-darwin` for fully reproducible macOS state.

**Machine detection**: Scripts detect OS via `uname`, architecture via `uname -m`, and route to platform-specific logic. The bootstrap script handles Alpine/Debian/Fedora/Arch/macOS with appropriate package managers.

### Finding 8: basnijholt/dotfiles Modular Shell Architecture

Uses **numbered-file sourcing** for predictable initialization order:

```
00_prefer_zsh.sh    # Bash->zsh redirect (bash-only)
05_zsh_completions.sh  # Completion system (zsh-only)
10_aliases.sh       # Command aliases
20_exports.sh       # Environment variables
30_misc.sh          # Miscellaneous configs
40_keychain.sh      # Credential management
50_python.sh        # Python environment
60_slurm.sh         # SLURM cluster config
70_zsh_plugins.sh   # Plugin management (zsh-only)
```

`main.sh` is a thin orchestrator sourced from `.zshrc`/`.bashrc`. Shell-type detection via `$BASH_VERSION`/`$ZSH_VERSION` controls which files load.

### Finding 9: basnijholt/dotfiles Idempotency

- **Dotbot**: Symlink operations are inherently idempotent (relink + force flags)
- **install script**: Thin wrapper delegates to dotbot; dotbot handles state
- **bootstrap.sh**: Checks if target directory exists before cloning; exits rather than overwrites
- **Nix**: Declarative builds are idempotent by design
- **uninstall.py**: Reverse operation exists, implying tracked state

### Finding 10: rjallais/dotfiles -- chezmoi + mise Pattern

This repo demonstrates the cleanest chezmoi-mise integration:

- **chezmoi** manages dotfile templates with `run_onchange_` hooks
- **mise** provides tools on-demand, including the shell itself (Nushell via `aqua:nushell/nushell`)
- `run_onchange_after_50-mise-install.nu.tmpl` runs `mise install` only when config changes
- `dot_config/mise/config.toml` is the declarative tool manifest
- Bootstrap: `mise exec chezmoi@latest -- chezmoi init --apply` (no external deps needed)

---

## Pattern Extraction Table

| Repo | Pattern | Code Example | Applicable To Our Codebase? |
|------|---------|--------------|---------------------------|
| thoughtbot/laptop | Per-operation idempotency guard | `command -v brew` / `grep -Fqs` / `asdf plugin list \| grep -Fq` | **Yes** -- adopt for all install scripts. Our scripts lack consistent guards. |
| thoughtbot/laptop | `fancy_echo()` formatted output | `fancy_echo "Installing Homebrew..."` with `printf` | **Yes** -- standardize logging across all `scripts/*.sh`. |
| thoughtbot/laptop | `set -e` + trap for error handling | `trap 'echo "failed" >&2' EXIT` | **Yes** -- many of our scripts lack `set -e`. |
| thoughtbot/laptop | brew-provides-manager, manager-provides-runtimes | brew installs asdf; asdf installs ruby/node | **Yes** -- directly maps to our brew->mise boundary model. |
| thoughtbot/laptop | Extension hook file | `~/.laptop.local` sourced at end | **Maybe** -- useful for per-machine customization. |
| br3ndonland/dotfiles | Required env vars with `:?` fail-fast | `STRAP_GIT_NAME=${STRAP_GIT_NAME:?}` | **Yes** -- adopt for `mde-migrate-to-mise.sh` and bootstrap scripts. |
| br3ndonland/dotfiles | `brew bundle check` before `brew bundle install` | `brew bundle check \|\| brew bundle install` | **Yes** -- use in `mde-update.sh` to skip unnecessary brew runs. |
| br3ndonland/dotfiles | Dynamic skip lists for brew bundle | `HOMEBREW_BUNDLE_CASK_SKIP` generated from installed casks | **Yes** -- reduces update time significantly. |
| br3ndonland/dotfiles | mise config.toml with tasks | `[tasks.check]` and `[tasks.format]` in config.toml | **Yes** -- use mise tasks for `mde-verify` equivalent. |
| br3ndonland/dotfiles | `require_sha: true` for casks | `cask_args appdir: "/Applications", require_sha: true` | **Yes** -- adopt in our Brewfile for integrity. |
| br3ndonland/dotfiles | Symlink with `ln -nsfF` | Force-relink pattern in symlink.sh | **Maybe** -- depends on template management approach. |
| br3ndonland/dotfiles | Separate scripts for phases | `symlink.sh`, `macos.sh`, `strap-after-setup.sh` | **Yes** -- our scripts should follow phase separation. |
| basnijholt/dotfiles | Numbered-file shell sourcing | `00_prefer_zsh.sh` through `70_zsh_plugins.sh` | **Yes** -- adopt for oh-my-zsh custom directory. |
| basnijholt/dotfiles | Dotbot declarative symlink manifest | `install.conf.yaml` with `create: true, relink: true` | **Maybe** -- we use `ensure-managed-configs.sh` already. |
| basnijholt/dotfiles | Separate sync scripts per tool | `sync-bun.sh`, `sync-uv.sh`, `sync-dotfiles.sh` | **Yes** -- maps to our per-tool update approach. |
| basnijholt/dotfiles | Bootstrap exit-if-exists guard | `if [ -d "$DOTFILES_DIR" ]; then exit` | **Yes** -- prevents accidental overwrites in migration. |
| rjallais/dotfiles | mise provides chezmoi (zero-dep bootstrap) | `mise exec chezmoi@latest -- chezmoi init --apply` | **No** -- over-engineered for our use case. |
| rjallais/dotfiles | `run_onchange_` triggers | Re-run `mise install` only when config.toml changes | **Interesting** -- could inspire launchd watch triggers. |
| marcus-crane/dotfiles | Templated mise config.toml | Go template with env-specific overrides | **No** -- adds unnecessary complexity. |

---

## Recommended Patterns

### Pattern 1: Standardized Script Preamble (from thoughtbot/laptop)
Every script in `scripts/` should start with:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Formatted output helper
mde_log() {
  printf "\n[mde] %s\n" "$1"
}

# Error trap
trap 'mde_log "FAILED: $0" >&2' ERR
```
**Why**: Our scripts currently have inconsistent error handling. `set -e` is missing from several. The `mde_log` function replaces ad-hoc `echo` statements with a consistent prefix.

### Pattern 2: Per-Operation Idempotency Guards (from thoughtbot/laptop + br3ndonland)
Every mutating operation should have a guard:
```bash
# Guard: skip if already done
if command -v mise >/dev/null 2>&1; then
  mde_log "mise already installed, skipping"
else
  mde_log "Installing mise..."
  curl https://mise.jdx.dev/install.sh | sh
fi
```
**Why**: Enables safe re-runs of install and update scripts. Our `install-*.sh` scripts would benefit from this pattern universally.

### Pattern 3: brew bundle check Gate (from br3ndonland/dotfiles)
```bash
if brew bundle check --file="$BREWFILE" --no-upgrade 2>/dev/null; then
  mde_log "All Homebrew packages already installed"
else
  mde_log "Installing missing Homebrew packages..."
  brew bundle install --file="$BREWFILE" --no-upgrade
fi
```
**Why**: Avoids unnecessary brew operations during fast updates. Directly useful for `mde-update-fast`.

### Pattern 4: Required Environment Variable Contract (from br3ndonland/dotfiles)
```bash
# Fail immediately if required vars are unset
: "${MDE_TOOL_OWNERSHIP_FILE:?MDE_TOOL_OWNERSHIP_FILE must be set}"
: "${MDE_MISE_EXCEPTION_ALLOWLIST:?MDE_MISE_EXCEPTION_ALLOWLIST must be set}"
```
**Why**: The consolidated spec defines `MDE_TOOL_OWNERSHIP_FILE`, `MDE_MISE_EXCEPTION_ALLOWLIST`, and `MDE_DRIFT_ENFORCE`. These should use `:?` fail-fast in every script that needs them.

### Pattern 5: Numbered Shell Config Sourcing (from basnijholt/dotfiles)
Adopt for oh-my-zsh custom directory:
```
templates/oh-my-zsh/
  00-path.zsh          # PATH setup (mise shims first)
  10-exports.zsh       # Environment variables
  20-aliases.zsh       # Command aliases (mde-status, mde-update, etc.)
  30-completions.zsh   # Tab completions
  40-integrations.zsh  # Tool integrations (fzf, starship, etc.)
```
**Why**: Deterministic load order prevents race conditions between PATH setup and alias definitions. Currently our templates are loaded in undefined order.

### Pattern 6: Separate Mutating vs. Read-Only Scripts (synthesized from all three)
```
scripts/
  install-*.sh         # Mutating: install new things
  setup-*.sh           # Mutating: configure system settings
  mde-update.sh        # Mutating: update packages
  mde-migrate-*.sh     # Mutating: migration operations
  verify-*.sh          # Read-only: check state, report
  mde-drift-check.sh   # Read-only: detect policy violations
  mde-status.sh        # Read-only: display current state
  health-check.sh      # Read-only: system health
```
**Why**: Our codebase already partially follows this (install-* vs verify-*). Formalizing it matches the consolidated spec's requirements for `mde-verify` (read-only) vs `mde-update` (mutating).

---

## Implementation-Ready Decisions

### Decision 1: Adopt `set -euo pipefail` + trap in all scripts
- **Action**: Add standardized preamble to every script in `scripts/`.
- **Scope**: All existing `.sh` files (40+).
- **Risk**: Low. `set -e` may surface latent bugs (which is desirable).
- **Source**: thoughtbot/laptop pattern.

### Decision 2: Use `brew bundle check` as gate in update flow
- **Action**: In `mde-update.sh`, run `brew bundle check` first. Only run `brew bundle install` if check fails.
- **Scope**: New `mde-update.sh` and `mde-update-fast.sh` scripts.
- **Risk**: None. This is strictly additive.
- **Source**: br3ndonland/dotfiles pattern.

### Decision 3: Structure mise config.toml with tasks section
- **Action**: Include `[tasks.check]` and `[tasks.format]` in our `.config/mise/config.toml` for automated code quality checks on shell scripts.
- **Scope**: New file `.config/mise/config.toml`.
- **Risk**: Low. Mise tasks are opt-in.
- **Source**: br3ndonland/dotfiles `config.toml`.

### Decision 4: Enforce `require_sha: true` in Brewfile
- **Action**: Add `cask_args require_sha: true` to our Brewfile.
- **Scope**: Existing or new `Brewfile`.
- **Risk**: Some casks may not have SHA checksums, requiring exceptions.
- **Source**: br3ndonland/dotfiles Brewfile.

### Decision 5: Number oh-my-zsh custom files for deterministic load order
- **Action**: Rename existing `templates/oh-my-zsh/*.zsh` files with numeric prefixes.
- **Scope**: `templates/oh-my-zsh/` directory.
- **Risk**: Requires updating `ensure-managed-configs.sh` to match new names.
- **Source**: basnijholt/dotfiles numbered-file pattern.

### Decision 6: Use `:?` parameter expansion for required env vars
- **Action**: Every new script that depends on `MDE_*` env vars should use `:?` for fail-fast.
- **Scope**: New scripts defined in consolidated spec.
- **Risk**: None.
- **Source**: br3ndonland/dotfiles `bootstrap.sh`.

---

## Open Questions / Caveats

1. **thoughtbot/laptop uses asdf, not mise**: The patterns transfer directly since mise is a drop-in replacement for asdf with the same plugin model, but specific asdf API calls (`asdf plugin list`, `asdf list all`) need mise equivalents (`mise plugins ls`, `mise ls`).

2. **br3ndonland/dotfiles uses a monorepo for all dotfiles**: Our repo is narrower in scope (macOS dev environment, not full dotfiles). We should not try to replicate the full dotfiles management pattern -- just extract the toolchain governance patterns.

3. **basnijholt/dotfiles uses Nix-darwin for macOS reproducibility**: This is a significantly heavier approach than our mise+brew model. The Nix pattern is informative but not directly adoptable without a major architecture change.

4. **`require_sha: true` may break some casks**: Need to test which casks in our Brewfile (if any) lack SHA checksums and document exceptions.

5. **Numbered file sourcing assumes oh-my-zsh loads `custom/*.zsh` alphabetically**: Need to verify oh-my-zsh custom file loading order. Standard oh-my-zsh sources `$ZSH_CUSTOM/*.zsh` via glob, which is alphabetical in zsh.

6. **No reference repo implements a drift checker**: All three repos implement idempotent *installation* but none implement *drift detection* (checking whether state has diverged from policy). Our `mde-drift-check.sh` is novel and has no direct reference pattern to follow.

7. **`brew bundle check` may have performance issues with large Brewfiles**: Need to benchmark on our actual Brewfile. br3ndonland reports fast execution with ~30 formulae.

---

## Cross-References

- **R1 (mise-core research)**: Finding 4 (br3ndonland mise config.toml structure) directly informs the config.toml design. Settings like `pipx_uvx = true`, `python.compile = false`, and idiomatic version files should be cross-referenced with R1 findings on mise settings.
- **R2 (tool-interactions research)**: Finding 4 shows br3ndonland managing `uv` through mise (`"uv" = "latest"` in tools section). This validates the mise-owns-uv pattern.
- **R4 (shell-secrets research)**: Finding 8 (numbered shell sourcing) directly affects the oh-my-zsh template design. PATH ordering (Finding 5, Pattern 5) intersects with shell environment research.
- **R5 (brew-boundary research)**: Findings 3 and 6 provide concrete brew boundary patterns. The `brew bundle check` gate (Pattern 3) and `require_sha: true` (Decision 4) directly support the brew boundary hardening spec.
- **Consolidated Spec Section 6 (brew boundary)**: Pattern 3 implements the "forbid brew runtime ownership" model. Brew provides mise, mise provides runtimes.
- **Consolidated Spec Section 7 (shell contract)**: Pattern 5 (numbered sourcing) ensures the `mde-*` aliases load after PATH is configured.
- **Consolidated Spec Section 8 (maintenance architecture)**: Pattern 3 (`brew bundle check` gate) directly implements the "bounded updates" step.
