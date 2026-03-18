# Best Practices Review: macOS Development Environment

Reviewed: 2026-02-28
Reviewer: practices-reviewer (Team 3)
Input: best-practices-research.md, tool-specific audit reports, codebase analysis

---

## 1. This Repo's Strengths

Before identifying gaps, it is important to document what this repository does well.
These are patterns that should be preserved through any future changes.

### 1a. launchd-Native Automation

The 12-hour `StartInterval` maintenance job (`com.ray-manaloto.macos-dev-maintenance`)
is a genuine best practice for macOS environments. It uses the OS-native scheduler
rather than cron, systemd timers, or external tools. The plist-based approach:

- Survives reboots without additional setup.
- Runs under the user's login session (access to Keychain, GUI session).
- Has built-in macOS logging integration.
- Requires zero external dependencies.

Most popular dotfiles repositories (Mathias Bynens, Dries Vints, holman/dotfiles)
do not include automated maintenance scheduling at all. This is a differentiator.

### 1b. Drift Detection (`mde-drift-check.sh`)

A dedicated script that validates runtime ownership (mise vs brew), PATH ordering,
and conflicting version managers (nvm, volta, pyenv, asdf) is uncommon in personal
dotfiles repositories. The checks are specific and actionable:

- Brew-owned runtimes flagged as drift.
- PATH ordering validated (mise shims must be first).
- Conflicting managers detected and reported.

Neither chezmoi, nix-darwin, nor Ansible provide this kind of runtime-manager
drift detection out of the box. This is custom logic that adds real value.

### 1c. Toolchain Precedence Model

The five-tier precedence model (`mise > bun > pixi > uv > Homebrew`) is clearly
documented in `docs/toolchain-precedence.md` and enforced in both shell config
(`macos-env.zsh` PATH ordering) and scripts (`setup_path()` functions). This
explicit layering prevents the "which python am I running?" confusion that plagues
most multi-manager environments.

### 1d. JSON Output in Health Checks

The `scripts/lib/mde-json.sh` library provides structured JSON output for
verification scripts. Functions like `mde_add_check()` and `mde_emit_json()`
produce machine-parseable results with timestamps, severity levels, and
pass/warn/fail status. This enables programmatic consumption by dashboards
or CI systems -- a pattern rarely seen in personal dotfiles repos.

### 1e. Keychain-Native Secrets

Using macOS Keychain (`security find-generic-password`) for API key storage
is the correct platform-native approach. The `mde_export_secret()` function
in `macos-env.zsh` and the `load_keychain_secret()` function in the maintenance
script provide layered secret loading (Keychain > env file > 1Password) with
override controls. This is more secure than `.env` files alone and more
convenient than requiring a third-party password manager.

### 1f. Guard-Based Safety

The `MANAGED_MARKER` pattern in `ensure-managed-configs.sh` prevents overwriting
user-created files. The `MDE_AUTOFIX` and `MDE_AUTOFIX_STRICT` flags provide
graduated automation levels. The `bun upgrade` and `uv self update` skip logic
(detecting mise-managed binaries by path) prevents version manager conflicts.
These guards show careful thought about failure modes.

### 1g. Comprehensive Update Orchestration

The maintenance script handles six package managers in a defined order with
per-step failure isolation (`|| failures=1`). Each manager's update logic
accounts for its relationship to mise (skip self-update if mise-managed, skip
runtime installs if mise owns the runtime). This level of cross-manager
coordination is not provided by any single tool.

---

## 2. Gap Analysis

Comparing this repository against industry best practices from chezmoi, Brewfile,
nix-darwin, Ansible, and well-known dotfiles repositories.

### 2a. No Package Manifest (Critical)

**What's missing:** There is no `Brewfile`, `mise.toml` package list (in-repo),
or any other declarative manifest of what Homebrew packages should be installed.

**Industry standard:** A `Brewfile` is the de facto standard for macOS Homebrew
environments. Repositories by Dries Vints, Kent C. Dodds, and Mathias Bynens all
include a Brewfile. The `brew bundle` ecosystem (install, check, cleanup) is
mature and zero-cost to adopt.

**Impact:** The current Homebrew state cannot be reproduced on a fresh machine.
Package drift is undetectable. There is no way to answer "what should be installed?"
without reading multiple scripts.

### 2b. Template-Deploy Sync Gap (High)

**What's missing:** Template changes do not propagate to deployed files unless
`MDE_AUTOFIX=1` is set (defaults to `0`) or the user manually runs
`ensure-managed-configs.sh`.

**Industry standard:** chezmoi provides `chezmoi apply` with diff/preview.
GNU Stow uses symlinks (changes propagate instantly). dotbot uses symlinks.
Even simple `cp`-based approaches typically run on every maintenance cycle.

**Impact:** This is the root cause of the alias bug (6 MDE lifecycle aliases
exist in the template but are absent from the deployed file). Any template
change is silently lost until someone remembers to manually sync.

### 2c. No Diff/Preview Before Deploy (Medium)

**What's missing:** `ensure-managed-configs.sh` copies files blindly. There is
no `--dry-run`, `--diff`, or `--check` mode to see what would change.

**Industry standard:** chezmoi (`chezmoi diff`), Ansible (`--check`), and
nix-darwin (`darwin-rebuild build`) all provide preview capabilities.

**Impact:** Users cannot review changes before they take effect. Combined
with the lack of backups on overwrite, this means a bad template can
silently break the shell environment.

### 2d. Duplicated Helper Functions (Medium)

**What's missing:** A shared library for common functions. The `log()`,
`have_cmd()`, and `setup_path()` functions are duplicated across at least
20 scripts (evidence from grep: 18 `log()` definitions, 10 `have_cmd()`
definitions, 15 `setup_path()` definitions).

**Industry standard:** The "DRY helpers" pattern (a single sourced library
file) is standard in well-maintained shell script projects. This repo
already has `scripts/lib/mde-json.sh` as a partial solution.

**Impact:** Bug fixes to common functions must be applied in 15+ places.
`setup_path()` contains a hardcoded username (`/Users/rmanaloto`) in
every copy. If PATH ordering changes, every copy must be updated.

### 2e. No Bun Completions (Low)

**What's missing:** The fpath symlink for bun tab completions was never
created after the old `source` approach was removed.

**Industry standard:** Completion files should be installed as part of
the tool setup, not left as a comment.

**Impact:** Bun tab completions do not work.

### 2f. Stale Standalone Binaries (Low)

**What's missing:** Cleanup of pre-mise standalone installs. A 57 MB
standalone bun binary exists at `~/.bun/bin/bun` alongside the
mise-managed version. An older mise bun version (1.3.8) is also retained.

**Industry standard:** Version managers should clean up old versions.
mise provides `mise prune` for this purpose.

**Impact:** Wasted disk space and potential confusion (the wrong binary
could be invoked if PATH is misconfigured).

### 2g. Stale Documentation References (Low)

**What's missing:** Three docs still reference the deprecated
`UV_NO_MANAGED_PYTHON=1` variable instead of `UV_PYTHON_DOWNLOADS=never`.

**Files affected:**
- `docs/mise-config.md`
- `docs/setup-notes.md`
- `docs/decision-log.md`

---

## 3. Tool-by-Tool Comparison Matrix

| Capability | This Repo | chezmoi | nix-darwin | Brewfile | mise tasks | dotbot |
|---|---|---|---|---|---|---|
| **Config deployment** | `cp` with marker guard | Template engine + diff | Nix expressions | N/A | N/A | Symlinks + YAML |
| **Diff/preview** | None | `chezmoi diff` | `darwin-rebuild build` | `brew bundle check` | N/A | None |
| **Template variables** | Hardcoded paths | Go templates (hostname, OS, user) | Nix interpolation | N/A | N/A | None |
| **Encryption** | None (Keychain external) | Built-in age/gpg | None | N/A | N/A | None |
| **Multi-machine** | No | Yes (per-host templates) | Yes (flake configs) | Partial (host-specific Brewfiles) | No | No |
| **Package manifest** | None | External (run_once scripts) | Full (`environment.systemPackages`) | `Brewfile` | N/A | None |
| **Rollback** | None | `chezmoi merge` | Atomic generation rollback | None | N/A | None |
| **Runtime drift detection** | `mde-drift-check.sh` | None | Full (declarative state) | None | None | None |
| **Update orchestration** | `macos-dev-maintenance.sh` (6 managers) | None (dotfiles only) | `darwin-rebuild switch` | `brew bundle install` | Task dependencies | None |
| **Health checks** | `health-check.sh` + JSON output | None | None | `brew bundle check` | None | None |
| **launchd scheduling** | Native plist (12h interval) | None | launchd abstraction | None | None | None |
| **Secrets management** | Keychain + 1Password + env file | 1Password/Bitwarden/age | None | None | None | None |
| **Task discoverability** | README + `scripts/` listing | N/A | N/A | N/A | `mise tasks` | N/A |
| **Idempotency model** | Manual guards per script | Declarative convergence | Declarative state | Declarative | Depends on task | Declarative symlinks |
| **Learning curve** | Low (bash/zsh) | Low-Medium (Go templates) | High (Nix language) | Very Low | Low (already uses mise) | Very Low |
| **External dependencies** | None | Single Go binary | Nix package manager | None (built into Homebrew) | None (built into mise) | Python (git submodule) |

### Key Takeaways

1. **chezmoi** fills the config-deployment gap (diff, preview, templates, encryption)
   without replacing anything this repo does well (update orchestration, drift
   detection, health checks, launchd).

2. **Brewfile** fills the package-manifest gap with zero cost and zero risk.
   It complements every other tool in this comparison.

3. **nix-darwin** provides the most complete solution but at the highest cost
   (learning curve, ecosystem lock-in, migration effort). Not justified for
   a single-machine environment.

4. **mise tasks** provides discoverability for the 48 scripts. It is additive
   and does not conflict with any existing pattern.

5. **dotbot** is strictly inferior to chezmoi for this use case. The only
   advantage (simplicity) is offset by the lack of templates and encryption
   that address this repo's actual gaps.

---

## 4. Prioritized Recommendations

### P0 -- Quick Wins (do this week)

#### P0-1: Generate and commit a Brewfile

**Effort:** 30 minutes
**Impact:** High -- closes the largest reproducibility gap
**Risk:** None -- additive change, no existing behavior modified

A `Brewfile` captures the current Homebrew state as a declarative manifest.
Once committed, it serves as the source of truth for "which packages should
be installed on this machine."

Steps:
1. `brew bundle dump --describe --file=Brewfile`
2. Review the output; remove any packages that should not be tracked.
3. Commit the Brewfile to the repository root.
4. Add `brew bundle check --file=Brewfile` to `health-check.sh`.
5. Optionally add `brew bundle install --file=Brewfile` to the golden-path
   setup instructions in `README.md`.

#### P0-2: Fix template auto-sync (remove MDE_AUTOFIX gate)

**Effort:** 15 minutes
**Impact:** High -- prevents future sync-gap bugs (root cause of alias bug)
**Risk:** Low -- config sync is already idempotent and marker-protected

The `ensure-managed-configs.sh` script is safe to run on every maintenance
cycle. It only overwrites files that contain the `MANAGED_MARKER` string.
Gating it behind `MDE_AUTOFIX=1` provides no safety benefit and causes
template changes to silently fail to propagate.

Steps:
1. In `scripts/macos-dev-maintenance.sh`, move the `sync_managed_configs`
   call outside the `MDE_AUTOFIX` conditional block.
2. Run `scripts/ensure-managed-configs.sh` once to apply current templates.
3. Verify deployed files match templates.

#### P0-3: Create bun completions symlink

**Effort:** 5 minutes
**Impact:** Low -- restores tab completions for bun
**Risk:** None

Steps:
1. `mkdir -p ~/.oh-my-zsh/custom/completions`
2. `ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun`
3. Add this symlink creation to `ensure-managed-configs.sh` so it persists.

#### P0-4: Fix stale UV_NO_MANAGED_PYTHON references in docs

**Effort:** 15 minutes
**Impact:** Low -- documentation consistency
**Risk:** None

Update the following files to use `UV_PYTHON_DOWNLOADS=never`:
- `docs/mise-config.md` (line 24)
- `docs/setup-notes.md` (line 350)
- `docs/decision-log.md` (line 60, add migration note)

---

### P1 -- Medium Effort (plan for next sprint)

#### P1-1: Adopt chezmoi for config deployment

**Effort:** 1-2 days
**Impact:** High -- diff/preview, template variables, encryption capability
**Risk:** Low -- chezmoi and existing scripts coexist; migration is incremental

chezmoi replaces only the `ensure-managed-configs.sh` layer. The update
lifecycle (`macos-dev-maintenance.sh`), drift detection, health checks,
and launchd scheduling remain unchanged.

Key benefits:
- `chezmoi diff` shows what will change before applying.
- Go template variables replace hardcoded `/Users/rmanaloto` paths.
- `chezmoi add --encrypt` enables versioning secrets (optional).
- Two-way merge detects local modifications to managed files.
- `chezmoi doctor` provides self-diagnostics.

What does NOT change:
- All `scripts/*.sh` files remain as-is.
- `macos-dev-maintenance.sh` continues to orchestrate updates.
- `mde-drift-check.sh` continues to validate runtime ownership.
- `health-check.sh` continues to run all checks.
- launchd scheduling is unaffected.

#### P1-2: Extract shared helper library (`scripts/lib/mde-common.sh`)

**Effort:** Half a day
**Impact:** Medium -- reduces duplication, centralizes PATH definition
**Risk:** Low -- purely mechanical refactor

Extract the following functions into `scripts/lib/mde-common.sh`:

```bash
# scripts/lib/mde-common.sh
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }
setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}
```

Then replace the duplicated definitions in each script with:

```bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/mde-common.sh"
```

(or the appropriate relative path for the script's location)

Scripts to update (grep found 20+ with duplicated functions):
- `macos-dev-maintenance.sh`
- `health-check.sh`
- `verify-all.sh`
- `mde-drift-check.sh`
- `verify-langchain-tools.sh`
- `verify-agent-tools.sh`
- `verify-ai-research-skills.sh`
- `verify-tmux-setup.sh`
- `verify-openlit.sh`
- `verify-aws-k8s-tools.sh`
- `verify-skypilot-aws.sh`
- `status-dashboard.sh`
- `sky-status.sh`
- `install-aws-k8s-tools.sh`
- `install-ai-research-skills.sh`
- `setup-mcp-servers.sh`
- `openlit-control.sh`
- `post-setup-run.sh`
- `mde-migrate-to-mise.sh`
- `secrets-smoke-test.sh`
- `setup-skypilot-aws.sh`

#### P1-3: Clean up stale binaries

**Effort:** 15 minutes
**Impact:** Low -- recovers disk space, reduces confusion
**Risk:** Very low (PATH ordering already shadows these)

Steps:
1. Remove standalone bun binary: `rm ~/.bun/bin/bun ~/.bun/bin/bunx`
2. Remove stale mise bun version: `mise uninstall bun@1.3.8`
3. Run `mise prune` to clean up any other unused versions.
4. Add `mise prune` to the maintenance script (after `mise upgrade`).

---

### P2 -- Future Consideration (backlog)

#### P2-1: Wrap verification/status scripts as mise tasks

**Effort:** Half a day
**Impact:** Medium -- discoverability via `mise tasks`
**Risk:** Low -- additive, existing scripts unchanged

Define a `[tasks]` section in a project-level `mise.toml` (or add to the
existing global `~/.config/mise/config.toml` tasks) that wraps the most
commonly used scripts. Note: the global config already has some tasks
defined (dashboard, validate, lint, agent operations). The gap is that
there is no project-level `mise.toml` in this repo, so contributors
cannot discover tasks without the global config.

Candidate scripts for mise task wrappers:
- `health-check.sh` -> `mise run health`
- `mde-drift-check.sh` -> `mise run drift`
- `verify-all.sh` -> `mise run verify`
- `status-dashboard.sh` -> `mise run status`
- `ensure-managed-configs.sh` -> `mise run sync`

Complex lifecycle scripts (`macos-dev-maintenance.sh`, `install-agent-stack.sh`)
should remain as standalone bash scripts referenced by mise tasks, not
inlined into `mise.toml`.

#### P2-2: Add macOS defaults script

**Effort:** 2-4 hours
**Impact:** Low-Medium -- makes Dock/Finder/keyboard setup reproducible
**Risk:** Low -- one-time setup script, not a maintenance script

Create `scripts/macos-defaults.sh` following the Mathias Bynens pattern.
Document it as a one-time setup script (not automated via launchd).

Candidate preferences to track:
- Dock: auto-hide, minimize-to-application, icon size
- Finder: show extensions, show hidden files, default view
- Keyboard: key repeat rate, initial repeat delay
- Trackpad: tap to click, three-finger drag
- Safari: developer menu, debug menu
- Terminal/iTerm2: theme, font

#### P2-3: Evaluate multi-machine support

**Effort:** 2-4 days (if adopting chezmoi, this comes nearly free)
**Impact:** Low (currently single-machine)
**Risk:** Increases complexity

If chezmoi is adopted (P1-1), multi-machine support becomes a template
variable exercise. Hardcoded paths like `$HOME/dev/github/ray-manaloto/`
become `{{ .chezmoi.homeDir }}/dev/github/{{ .git_username }}/`.

Only pursue this if a second machine (work laptop, cloud dev environment)
becomes a real requirement.

---

## 5. Migration Paths

### Migration Path: Brewfile (P0-1)

```
Step 1: Generate from current state
  $ brew bundle dump --describe --file=Brewfile

Step 2: Review and curate
  - Remove any packages you do not want to track
  - Add comments grouping packages by purpose
  - Separate into sections: tap, brew, cask, mas (if applicable)

Step 3: Commit
  $ git add Brewfile
  $ git commit -m "Add Brewfile for declarative Homebrew package tracking"

Step 4: Integrate with verification
  Add to scripts/health-check.sh:
    if have_cmd brew; then
      brew bundle check --file="$REPO_ROOT/Brewfile" 2>&1 || warn "Brewfile drift detected"
    fi

Step 5: Integrate with setup
  Add to README.md Golden Path:
    brew bundle install --file=Brewfile

Step 6: Integrate with maintenance (optional)
  Add to scripts/macos-dev-maintenance.sh after update_brew():
    brew bundle install --file="$SCRIPT_DIR/../Brewfile" --no-lock || true
```

### Migration Path: Fix Template Auto-Sync (P0-2)

```
Step 1: Move sync call outside MDE_AUTOFIX gate
  In scripts/macos-dev-maintenance.sh, change:

  BEFORE:
    if [[ "$MDE_AUTOFIX" == "1" ]]; then
        ...
        sync_managed_configs
        ...
    fi

  AFTER:
    sync_managed_configs   # Always sync templates
    if [[ "$MDE_AUTOFIX" == "1" ]]; then
        ...
        # (remove sync_managed_configs from here)
        ...
    fi

Step 2: Apply current templates
  $ scripts/ensure-managed-configs.sh

Step 3: Verify
  $ diff templates/oh-my-zsh/aliases.zsh ~/.oh-my-zsh/custom/aliases.zsh
  $ diff templates/oh-my-zsh/macos-env.zsh ~/.oh-my-zsh/custom/macos-env.zsh
  (should show no differences)
```

### Migration Path: chezmoi Adoption (P1-1)

```
Phase 1: Initialize chezmoi alongside existing scripts
  $ chezmoi init
  $ chezmoi add ~/.oh-my-zsh/custom/aliases.zsh
  $ chezmoi add ~/.oh-my-zsh/custom/macos-env.zsh
  $ chezmoi add ~/.oh-my-zsh/custom/llvm.zsh
  $ chezmoi add ~/.tmux.conf
  $ chezmoi add ~/.zprofile.d/macos-dev-env.zsh

Phase 2: Convert hardcoded paths to template variables
  Rename files to .tmpl extension in chezmoi source:
    aliases.zsh -> aliases.zsh.tmpl

  Replace:
    $HOME/dev/github/ray-manaloto/macos-development-environment
  With:
    {{ .chezmoi.homeDir }}/dev/github/{{ .git_username }}/macos-development-environment

  Define variables in ~/.config/chezmoi/chezmoi.toml:
    [data]
    git_username = "ray-manaloto"

Phase 3: Redirect ensure-managed-configs.sh to chezmoi
  Replace the sync_file calls with:
    chezmoi apply --force

  Or: retire ensure-managed-configs.sh entirely and call
  `chezmoi apply` from macos-dev-maintenance.sh.

Phase 4: Add wrapper scripts to chezmoi
  $ chezmoi add --template-symlinks ~/.local/bin/claude
  $ chezmoi add --template-symlinks ~/.local/bin/gemini
  (etc.)

Phase 5: Optional -- add encryption for secrets
  $ chezmoi add --encrypt ~/.config/macos-development-environment/secrets.env
```

### Migration Path: Shared Helper Library (P1-2)

```
Step 1: Create scripts/lib/mde-common.sh
  Extract log(), have_cmd(), setup_path() into the new file.
  Add a guard: SOURCED_MDE_COMMON=1

Step 2: Update scripts one at a time (incremental, testable)
  For each script:
    a. Add: source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/mde-common.sh"
       (adjust relative path based on script location)
    b. Remove the local log(), have_cmd(), setup_path() definitions.
    c. Test the script.

Step 3: Update tests
  Ensure scripts/tests/ still pass after the refactor.

Step 4: Add mde-common.sh to ensure-managed-configs.sh
  If any deployed scripts source the library, ensure the library
  is available at the expected path.
```

---

## 6. What NOT to Change

These patterns are strengths of this repository that should be preserved even
if other tools are adopted. Some of these are things this repo does better
than the alternatives being considered.

### 6a. Do NOT replace launchd with an external scheduler

The `com.ray-manaloto.macos-dev-maintenance` plist provides native macOS
scheduling with no dependencies. chezmoi, Ansible, and nix-darwin do not
provide equivalent scheduling out of the box. The launchd approach should
remain the automation backbone.

### 6b. Do NOT replace the update orchestration with a single tool

No single tool manages Homebrew + mise + bun + uv + pixi updates. The
sequential pipeline in `macos-dev-maintenance.sh` with per-step failure
isolation and manager-aware skip logic is custom and valuable. chezmoi
replaces only the config-deployment layer, not the update layer.

### 6c. Do NOT replace drift detection with a generic tool

`mde-drift-check.sh` validates runtime-manager-specific concerns (brew
owns a runtime that mise should own, PATH ordering is wrong, conflicting
managers present). No off-the-shelf tool provides these checks. This
script should be maintained and extended.

### 6d. Do NOT replace Keychain-based secrets with file-based encryption

The macOS Keychain integration (`mde_export_secret()`, `mde_load_keychain_secret()`)
is the platform-native approach and is more secure than encrypted files
in a git repository. chezmoi's age encryption is a useful supplement for
versioning non-secret config files, but should not replace Keychain for
API keys and tokens.

### 6e. Do NOT replace the JSON health-check framework

The `mde-json.sh` library and structured check output (`mde_add_check()`,
`mde_emit_json()`) enable machine-parseable health reporting. This is
more sophisticated than what chezmoi, Ansible, or nix-darwin provide for
health validation. Extend it rather than replace it.

### 6f. Do NOT adopt nix-darwin or Ansible at this time

Both tools are designed for multi-machine fleet management. For a
single-machine personal development environment:

- **nix-darwin** adds a steep learning curve, ecosystem lock-in, and
  ongoing maintenance burden that outweighs its reproducibility benefits.
- **Ansible** adds Python dependencies and YAML authoring overhead for
  gains (idempotency, roles) that can be achieved more simply with
  Brewfile + chezmoi.

Revisit only if multi-machine management becomes a real requirement.

### 6g. Do NOT reorganize to topical directory structure

The current layout (`templates/`, `scripts/`, `docs/`, `configs/`) is
functional and well-understood. A topical reorganization (grouping by
tool: `mise/`, `bun/`, `homebrew/`) would add churn with minimal
benefit for a single-maintainer project.

---

## Summary: Priority Action Items

| ID | Priority | Item | Effort | Impact |
|---|---|---|---|---|
| P0-1 | P0 | Generate and commit Brewfile | 30 min | High |
| P0-2 | P0 | Fix template auto-sync (remove MDE_AUTOFIX gate) | 15 min | High |
| P0-3 | P0 | Create bun completions fpath symlink | 5 min | Low |
| P0-4 | P0 | Update stale UV_NO_MANAGED_PYTHON doc references | 15 min | Low |
| P1-1 | P1 | Adopt chezmoi for config deployment | 1-2 days | High |
| P1-2 | P1 | Extract shared helpers to scripts/lib/mde-common.sh | 4 hours | Medium |
| P1-3 | P1 | Clean up stale binaries + add mise prune | 15 min | Low |
| P2-1 | P2 | Wrap scripts as mise tasks (project-level mise.toml) | 4 hours | Medium |
| P2-2 | P2 | Add macOS defaults script | 2-4 hours | Low-Medium |
| P2-3 | P2 | Multi-machine support (via chezmoi templates) | 2-4 days | Low |

**Total P0 effort: ~1 hour.** These four items can be completed in a single
session and address the two highest-impact gaps (missing Brewfile, broken
template sync) plus two minor cleanups.

**Total P1 effort: ~2-3 days.** These items provide meaningful improvements
to the config deployment layer and code maintainability.

**Total P2 effort: ~1-2 weeks.** These are optional enhancements to pursue
when the P0 and P1 items are stable.
