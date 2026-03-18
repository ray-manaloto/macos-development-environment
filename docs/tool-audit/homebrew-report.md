# Homebrew Audit Report

Generated: 2026-03-18

## 1. Overview

Homebrew is the **lowest-priority package manager** in this environment's
five-tier precedence model:

```
mise (shims) > bun > pixi > uv > Homebrew
```

Homebrew owns **only 3-4 formulae** (gnupg, curl, chafa, tree) plus GUI casks.
All CLI tools are managed by mise. The Brewfile is managed by chezmoi at
`.chezmoisource/Brewfile.tmpl` and applied via `run_onchange_` script.

Homebrew is installed at `/opt/homebrew` (Apple Silicon) and its `bin`/`sbin`
directories appear **after** all other managers' paths in `PATH`.

---

## 2. Brew-Owned Packages

### 2.1 Formulae (no mise backend)

| Formula | Reason |
|---------|--------|
| `gnupg` | OS-level crypto (pinentry, gpg-agent, keychain integration) |
| `curl` | Keg-only with newer TLS/HTTP3 features |
| `chafa` | Terminal image renderer (no mise backend) |
| `tree` | Tiny directory display utility |

### 2.2 Casks (GUI applications)

| Cask | Notes |
|------|-------|
| `gemini` | Disk cleaner |
| `ghostty` | GPU-accelerated terminal |
| `git-credential-manager` | Cross-platform Git credential storage |
| `iterm2` | Terminal emulator |
| `jordanbaird-ice` | Menu bar manager |
| `mactex` | TeX Live distribution |
| `opencode-desktop` | AI coding agent |
| `osquery` | SQL-powered OS instrumentation (requires sudo for upgrade) |
| `sublime-text` | Text editor |
| `swiftbar` | Menu bar customization |
| `wezterm` | GPU-accelerated terminal/multiplexer |

### 2.3 Migrated to Mise (formerly brew)

These were previously brew formulae, now fully mise-managed:

| Former brew formula | Mise entry | Backend |
|--------------------|-----------|---------|
| `glow` | `glow = "latest"` | registry (aqua) |
| `crush` | `"aqua:charmbracelet/crush"` | aqua |
| `cloudflared` | `cloudflared = "latest"` | registry |
| `direnv` | `direnv = "latest"` | registry |
| `pandoc` | `pandoc = "latest"` | registry |
| `tmux` | `tmux = "latest"` | registry |
| `xcodegen` | `xcodegen = "latest"` | registry |
| `llvm` | `clang = "latest"` | registry |
| `docker` | `docker-cli = "latest"` | registry (aqua) |
| `docker-compose` | `docker-compose = "latest"` | registry (aqua) |
| `buildkit` | `"aqua:moby/buildkit" = "latest"` | aqua |
| `cagent` (docker-agent) | `"github:docker/docker-agent" = "latest"` | github |
| `session-manager-plugin` | `"aqua:aws/session-manager-plugin" = "latest"` | aqua |

---

## 3. Declarative Brewfile (chezmoi-managed)

### 3.1 Source of Truth

The Brewfile lives at `.chezmoisource/Brewfile.tmpl` and is applied by chezmoi:
- `chezmoi apply` triggers `run_onchange_before_install-packages-darwin.sh.tmpl`
- The script runs `brew bundle` with the templated Brewfile
- The `run_onchange_` pattern re-runs only when the Brewfile hash changes

### 3.2 Validation

```bash
# Check brew formula inventory against expected set
uv run mde-py validate --brew

# Full validation (includes brew, docker, mise, chezmoi, etc.)
uv run mde-py validate --all
```

---

## 4. Update/Maintenance Flow

### 4.1 Automated Updates via Launchd

The maintenance job runs every **12 hours** via `StartInterval 43200`:

- Label: `com.ray-manaloto.macos-dev-maintenance`
- Script: `scripts/macos-dev-maintenance.sh`

### 4.2 Brew Update Sequence

1. `brew update` -- refresh tap metadata
2. `brew upgrade --formula -v` -- upgrade all installed formulas
3. `brew outdated --cask` -- enumerate outdated casks
4. `brew upgrade --cask -v <list>` -- upgrade casks, **excluding** `osquery`

### 4.3 Periodic Maintenance

```bash
brew cleanup --prune=all    # reclaim disk
brew autoremove             # remove orphaned deps
brew doctor                 # health check
brew leaves                 # should show ~3-4 items only
```

---

## 5. PATH Ordering

```
$HOME/.local/share/mise/shims        # 1st - mise shims (wins for runtimes)
$HOME/.local/share/mise/bin           # 2nd - mise binaries
$HOME/.local/bin                      # 3rd - local wrappers
$HOME/.bun/bin                        # 4th - bun globals
$HOME/.pixi/bin                       # 5th - pixi globals
...
/opt/homebrew/opt/curl/bin            # 10th - brew curl (keg-only)
/opt/homebrew/bin                     # 11th - brew formulas
/opt/homebrew/sbin                    # 12th - brew system binaries
```

Brew is intentionally positioned **after** all other tool managers so that
mise-managed tools always shadow brew-installed equivalents.

---

## 6. Known Issues

### 6.1 osquery Requires Manual Upgrade

The `osquery` cask requires sudo. Upgrade manually: `brew upgrade --cask osquery`.

### 6.2 brew upgrade Can Reintroduce Runtimes

`brew upgrade --formula` may install runtime dependencies. The drift checker
flags these, but cleanup only runs with `MDE_AUTOFIX_STRICT=1`.

### 6.3 brew doctor Now in Validation Pipeline

`uv run mde-py validate --brew` runs `brew doctor` and checks for unexpected
formulae. This is also wired into the `hk` pre-commit hook via `mde-validate`.
