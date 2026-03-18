# Homebrew Audit Report

Generated: 2026-02-28

## 1. Overview

Homebrew is the **lowest-priority package manager** in this environment's
five-tier precedence model:

```
mise (shims) > bun > pixi > uv > Homebrew
```

Homebrew is reserved for **OS-level system packages** that do not have a
runtime-version dimension (i.e., you never need "tmux 3.4 for project A and
tmux 3.5 for project B"). Language runtimes (Python, Node, Go, Rust) are
explicitly owned by mise; the environment actively removes brew-managed
runtimes when strict cleanup mode is enabled.

Homebrew is installed at `/opt/homebrew` (Apple Silicon) and its `bin`/`sbin`
directories appear **after** all other managers' paths in `PATH`.

---

## 2. Installed Packages (Formulas and Casks Found in Scripts)

### 2.1 Formulas Explicitly Installed or Referenced

| Formula | Install Context | Source File(s) |
|---------|----------------|----------------|
| `gnupg` | Auto-fix installs if `gpg` is missing | `scripts/macos-dev-maintenance.sh` (line 329) |
| `tmux` | Installed by optimize-tmux script; brew is default, pixi is fallback | `scripts/optimize-tmux.sh` (line 24) |
| `llvm` | Opt-in; documented but not auto-installed | `docs/setup-notes.md` (line 215) |
| `curl` | PATH entry for `/opt/homebrew/opt/curl/bin` present; not auto-installed | `templates/oh-my-zsh/macos-env.zsh` (line 54) |
| `ripgrep` (`rg`) | Required by health-check; assumed pre-installed | `scripts/health-check.sh` (line 219), `docs/plans/` |
| `git` | System tool; assumed pre-installed via brew | `docs/plans/` |
| `awscli` | Fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` (formula: `awscli`) |
| `kubernetes-cli` | Fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` (formula: `kubernetes-cli`) |
| `helm` | Fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` (formula: `helm`) |
| `eksctl` | Optional; fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` |
| `k9s` | Optional; fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` |
| `kubectx` | Optional; fallback if mise install fails (provides `kubectx` + `kubens`) | `scripts/install-aws-k8s-tools.sh` |
| `stern` | Optional; fallback if mise install fails | `scripts/install-aws-k8s-tools.sh` |
| `session-manager-plugin` | Optional; requires sudo | `scripts/install-aws-k8s-tools.sh` |

### 2.2 Casks Referenced

| Cask | Notes | Source |
|------|-------|--------|
| `osquery` | Requires sudo for upgrade; explicitly skipped by launchd maintenance | `scripts/macos-dev-maintenance.sh` (line 313), `README.md` |

### 2.3 Runtimes Explicitly Removed by Strict Cleanup

When `MDE_AUTOFIX_STRICT=1`, the maintenance script uninstalls:

- `node`
- `go`
- `rust`
- `python` / `python@*` (guarded: kept if `llvm` depends on it)

These are migrated to mise. See `scripts/mde-migrate-to-mise.sh` and
`scripts/mde-drift-check.sh` for the migration and drift-detection tooling.

---

## 3. Package Management (Brewfile Status)

### 3.1 No Brewfile Exists

A glob search for `**/Brewfile*` returned **no results**. There is no
declarative Brewfile anywhere in the repository.

### 3.2 Current Tracking Method

Brew packages are tracked **imperatively** across multiple scripts:

| Script | What It Tracks |
|--------|---------------|
| `scripts/macos-dev-maintenance.sh` | `brew update` + `brew upgrade` (all formulas + non-sudo casks) |
| `scripts/install-aws-k8s-tools.sh` | Specific brew formulas as mise fallback |
| `scripts/optimize-tmux.sh` | `brew install tmux` |
| `scripts/tools-inventory.sh` | `brew list --formula` + `brew list --cask` (discovery, not installation) |
| `scripts/status-dashboard.sh` | `brew list --formula` + `brew list --cask` (JSON inventory) |
| `docs/plans/2026-02-28-mise-implementation-spec-v2.md` | Canonical ownership table listing brew-owned tools |

There is no single source of truth for "which brew packages should be installed."
The implementation spec document (plans directory) comes closest to a declarative
list but is a planning document, not an executable manifest.

---

## 4. Update/Maintenance Flow

### 4.1 Automated Updates via Launchd

The maintenance job runs every **12 hours** via `StartInterval 43200`:

- Label: `com.ray-manaloto.macos-dev-maintenance`
- Plist: `~/Library/LaunchAgents/com.ray-manaloto.macos-dev-maintenance.plist`
- Script: `scripts/macos-dev-maintenance.sh`

### 4.2 Brew Update Sequence

The `update_brew()` function in `scripts/macos-dev-maintenance.sh` performs:

1. `brew update` -- refresh tap metadata
2. `brew upgrade --formula -v` -- upgrade all installed formulas (verbose)
3. `brew outdated --cask` -- enumerate outdated casks
4. `brew upgrade --cask -v <list>` -- upgrade casks, **excluding** `osquery`

Environment variables set during brew operations:

```
HOMEBREW_NO_BOTTLE_SOURCE_FALLBACK=1
HOMEBREW_NO_INSTALL_CLEANUP=1
HOMEBREW_CACHE=$HOME/Library/Caches/Homebrew
HOMEBREW_LOGS=$HOME/Library/Logs/Homebrew
```

### 4.3 Brew in the Overall Update Order

Brew runs **first** in the maintenance sequence, before all other managers:

1. **Homebrew** (formulas + casks)
2. mise (self-update, upgrade, reshim)
3. bun (global updates)
4. Claude/Gemini CLI cleanup
5. uv (self update + tool upgrade)
6. pixi (self-update + global update)
7. Agent tools (if enabled)
8. MCP servers (if enabled)
9. oh-my-zsh (if enabled)
10. Auto-fix / strict cleanup (if enabled)

### 4.4 Failure Handling

- Each step uses `|| failures=1` so a brew failure does not block subsequent
  managers.
- Brew failures are captured in launchd log output at
  `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance/macos-dev-maintenance.out`.
- The overall script exits non-zero if any step failed.

---

## 5. Integration Points (with mise, PATH Ordering)

### 5.1 PATH Ordering

Defined in `templates/oh-my-zsh/macos-env.zsh` and duplicated in shell scripts
(`setup_path()` in health-check, verify-agent-tools, maintenance, etc.):

```
$HOME/.local/share/mise/shims        # 1st - mise shims (wins for runtimes)
$HOME/.local/share/mise/bin           # 2nd - mise binaries
$HOME/.local/bin                      # 3rd - local wrappers (claude, gemini)
$HOME/.bun/bin                        # 4th - bun globals
$HOME/.pixi/bin                       # 5th - pixi globals
$HOME/.amp/bin                        # 6th - amp
$HOME/.antigravity/antigravity/bin    # 7th - antigravity
$HOME/.oh-my-zsh/custom/bin           # 8th - custom scripts
/opt/google-cloud-sdk/bin             # 9th - gcloud
/opt/homebrew/opt/curl/bin            # 10th - brew curl (keg-only)
/opt/homebrew/bin                     # 11th - brew formulas
/opt/homebrew/sbin                    # 12th - brew system binaries
/usr/local/bin                        # 13th - system
...
```

Brew is intentionally positioned **after** all other tool managers so that
mise-managed runtimes always shadow brew-installed equivalents.

### 5.2 Brew + mise Runtime Overlap

The environment enforces a single-owner rule for runtimes:

- **mise owns**: python, node, bun, go, rust (and their version variants)
- **brew owns**: OS-level tools only (gnupg, tmux, llvm, ripgrep, git, curl)
- **Overlap detection**: `scripts/mde-drift-check.sh` checks whether brew still
  owns any of `node`, `go`, `rust`, `python`, `python@*` and flags them as drift.
- **Migration tool**: `scripts/mde-migrate-to-mise.sh` automates the transition
  (dry-run by default).
- **Guard**: Python migration is blocked when `llvm` is installed via brew because
  llvm depends on brew's python.

### 5.3 Brew curl (Keg-Only)

`/opt/homebrew/opt/curl/bin` is placed in PATH before `/opt/homebrew/bin` to
ensure the keg-only brew curl (with newer TLS/HTTP features) takes precedence
over the macOS system curl, while still sitting below mise shims.

### 5.4 uv and brew Interaction

The maintenance script detects whether `uv` itself is brew-managed:

```bash
case "$uv_path" in
  /opt/homebrew/*|/usr/local/*)
    log "uv is Homebrew-managed; skipping uv self update."
    ;;
esac
```

If uv is installed via brew, `uv self update` is skipped to avoid conflicts
with brew's ownership of the binary. `uv tool upgrade --all` still runs
regardless.

### 5.5 AWS/K8s Tools: Mise-First, Brew-Fallback

`scripts/install-aws-k8s-tools.sh` tries `mise install` first for each tool,
then falls back to `brew install` only if mise fails. The `--no-brew` flag
disables the fallback entirely.

---

## 6. Known Issues and Gaps

### 6.1 No Brewfile for Declarative Package Tracking

**Impact: Medium-High**

There is no `Brewfile` or equivalent declarative manifest. Brew packages are
scattered across multiple scripts and docs. This means:

- There is no single command to reproduce the expected brew state on a fresh
  machine.
- Package drift (unexpected installs/removals) cannot be detected
  programmatically.
- `brew bundle dump` would capture the current state but nothing enforces it
  going forward.

**Recommendation**: Create a `Brewfile` listing the expected formulas and casks.
Use `brew bundle check` in verification scripts and `brew bundle install` in
setup scripts.

### 6.2 No Brew Package Verification in Health Check

**Impact: Medium**

`scripts/health-check.sh` checks that `brew` is present (`check_cmd brew 0`)
but does not verify that specific expected formulas (gnupg, tmux, ripgrep, etc.)
are installed. The `rg` command is listed as required but there is no check that
it came from brew specifically.

`scripts/verify-tooling.sh` delegates to sub-scripts (agent tools, langchain
tools, skypilot, aws/k8s, openlit) but none of these explicitly verify brew
formula state.

### 6.3 osquery Upgrade Requires Manual Intervention

**Impact: Low**

The `osquery` cask requires sudo for upgrade and is explicitly skipped by the
automated maintenance. It must be upgraded manually:
```
brew upgrade --cask osquery
```

This is documented in `README.md` and `docs/setup-notes.md`.

### 6.4 llvm Blocks Python Migration

**Impact: Low**

When `llvm` is installed via brew, python cannot be migrated from brew to mise
because llvm depends on brew's python. This is correctly guarded in both
`scripts/macos-dev-maintenance.sh` and `scripts/mde-migrate-to-mise.sh`, but
it means the environment may have a persistent brew-owned python that could
shadow or conflict with the mise-managed python if PATH ordering is disrupted.

### 6.5 brew upgrade Can Reintroduce Runtimes

**Impact: Medium**

`brew upgrade --formula` runs unconditionally and may install new runtime
dependencies (e.g., a formula update pulls in `python@3.13` as a dependency).
This would re-introduce a brew-owned runtime that the drift checker would flag,
but the cleanup only runs when `MDE_AUTOFIX_STRICT=1` (which defaults to off
in the script, on only if set in the plist).

### 6.6 HOMEBREW_NO_INSTALL_CLEANUP Prevents Disk Reclamation

**Impact: Low**

The maintenance script sets `HOMEBREW_NO_INSTALL_CLEANUP=1`, which prevents
brew from automatically removing old versions after upgrade. This avoids
unexpected disk space issues during automated runs but means old versions
accumulate until `brew cleanup` is run manually.

### 6.7 No brew doctor in Automated Checks

**Impact: Low**

`brew doctor` is not run by any automated script. Health issues in the
Homebrew installation (broken symlinks, outdated Xcode CLT, etc.) would go
undetected until they cause a visible failure.

**Recommendation**: Consider adding `brew doctor` to the health check or
validation pipeline.
