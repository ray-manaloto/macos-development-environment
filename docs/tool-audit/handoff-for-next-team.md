# Tool Integration Audit: Handoff for Next Agent Team

Date: 2026-02-28
Status: Complete (3 teams, 9 agents, 4 waves)
Purpose: Single-source brief for the second Claude Code agent team to perform
research, BDD test planning, code review, QA, and documentation updates.

---

## 1. Executive Summary

### What Was Audited

Five tool managers that compose this macOS development environment:

| Tool | Role | Report |
|------|------|--------|
| **mise** | Primary runtime version manager (Python, Node, Bun, Go, Rust) + CLI tools | `mise-report.md` |
| **Homebrew** | Lowest-priority package manager (OS-level tools only) | `homebrew-report.md` |
| **oh-my-zsh** | Shell configuration framework (templates deployed via copy) | `oh-my-zsh-report.md` |
| **bun** | JS package manager for global CLI tools (`bun add -g`) | `bun-report.md` |
| **uv** | Python tool manager (`uv tool install`), not runtime manager | `uv-report.md` |

### What Was Fixed During the Audit

The alias-fixer agent ran `scripts/ensure-managed-configs.sh` to deploy 6
missing `mde-*` lifecycle aliases (`mde-update`, `mde-update-fast`, `mde-verify`,
`mde-drift`, `mde-migrate`, `mde-agents-review`) from the template to
`~/.oh-my-zsh/custom/aliases.zsh`.

### Validation Result

**PASS** with 4 warnings:

| # | Warning | Severity |
|---|---------|----------|
| W1 | Multiple `claude` binaries (mise shim + direct install) | Low |
| W2 | Homebrew owns `python`/`python@3.14` (blocked by llvm dependency) | Medium |
| W3 | Duplicate bun/uv/pixi binaries (mise + standalone installs) | Low |
| W4 | Bun completions symlink missing (`~/.bun/_bun` not in fpath) | Low |

### Root Cause

The `MDE_AUTOFIX=1` gate in `scripts/macos-dev-maintenance.sh` (line 507)
defaults to `0`, blocking `sync_managed_configs()` from running during the
12-hour launchd maintenance cycle. Template changes in the repo never
auto-propagate to `~/.oh-my-zsh/custom/`. This single gate caused:

- 6 missing shell aliases
- Stale `UV_NO_MANAGED_PYTHON=1` in deployed config (should be `UV_PYTHON_DOWNLOADS=never`)
- Old bun completion strategy still in deployed config

---

## 2. Tool Ownership Matrix

### Toolchain Precedence (5-Tier Model)

```
mise shims > ~/.local/bin > bun > pixi > uv > Homebrew
```

Documented in `docs/toolchain-precedence.md` and enforced by PATH ordering in
`templates/oh-my-zsh/macos-env.zsh`.

### PATH Resolution Order

```
Position  Directory                           Owner     Purpose
--------  ----------------------------------  --------  --------------------------------
1         ~/.local/share/mise/shims           mise      Runtime shims (python, node, bun, go, rust)
2         ~/.local/share/mise/bin             mise      mise binary itself
3         ~/.local/bin                        mixed     Go binaries (GOBIN), uv/pip tools, wrappers
4         ~/.bun/bin                          bun       Global JS packages (bun add -g)
5         ~/.pixi/bin                         pixi      Global conda-forge packages
6-8       ~/.amp/bin, ~/.antigravity/..., ~/.oh-my-zsh/custom/bin
9         /opt/google-cloud-sdk/bin           gcloud    Google Cloud SDK
10        /opt/homebrew/opt/curl/bin          brew      Keg-only curl (newer TLS)
11-12     /opt/homebrew/bin, /opt/homebrew/sbin        brew      Homebrew formulas
13        /usr/local/bin                      system    macOS system binaries
```

### Runtime Ownership

| Runtime | Authoritative Owner | Secondary (shadowed) | Notes |
|---------|-------------------|---------------------|-------|
| Python 3.14.x | **mise** | Homebrew (blocked by llvm) | mise shims win via PATH |
| Node 25.x | **mise** | -- | `MDE_AUTOFIX_STRICT` removes brew node |
| Bun 1.3.x | **mise** | Standalone (`~/.bun/bin/bun`) | Standalone kept for global pkg dir |
| Go 1.26.x | **mise** | -- | |
| Rust 1.93.x | **mise** | -- | |

### Tool Installer Ownership

| Installer | Owns | Does NOT Own |
|-----------|------|--------------|
| **mise** | Runtime versions, CLI tools, uv/pixi/bun binaries | OS-level packages |
| **bun** (`bun add -g`) | JS/Node CLI packages (claude-code, codex, gemini-cli, typescript) | Runtime versions |
| **uv** (`uv tool install`) | Python CLI tools (langchain-cli, skypilot, aider, crewai) | Python runtimes (`UV_PYTHON_DOWNLOADS=never`) |
| **pixi** (`pixi global install`) | Conda-forge packages, fallback for Python tools | Runtime versions |
| **Homebrew** | OS-level packages (gnupg, tmux, curl, git, llvm) | Language runtimes |

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

---

## 3. Prioritized Fixes

### P0 -- Critical (do first, ~1 hour total)

| # | Fix | File(s) | Details |
|---|-----|---------|---------|
| 1 | **Generate and commit a Brewfile** | `Brewfile` (new) | Run `brew bundle dump --describe --file=Brewfile`. No Brewfile exists; Homebrew state is unreproducible. Add `brew bundle check` to `health-check.sh`. |
| 2 | **Remove/change MDE_AUTOFIX=1 gate for config sync** | `scripts/macos-dev-maintenance.sh` (line ~507-528) | Move `sync_managed_configs` call outside the `if [[ "$MDE_AUTOFIX" == "1" ]]` block. Config sync is idempotent and marker-protected; gating provides no safety benefit. This is the **root cause** of all template-deploy sync gaps. |
| 3 | **Create bun completions fpath symlink** | `templates/oh-my-zsh/macos-env.zsh`, `scripts/ensure-managed-configs.sh` | Run: `ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun`. Add this to `ensure-managed-configs.sh` so it persists. The old `source "$BUN_INSTALL/_bun"` was removed but the fpath symlink was never created. |
| 4 | **Update 3 stale docs referencing UV_NO_MANAGED_PYTHON=1** | `docs/mise-config.md` (line 24), `docs/setup-notes.md` (line 350), `docs/decision-log.md` (line 60) | Replace with `UV_PYTHON_DOWNLOADS=never`. All scripts were already migrated; only documentation lags behind. Add a migration entry to `docs/decision-log.md`. |

### P1 -- Important (plan for next sprint, ~2-3 days total)

| # | Fix | File(s) | Details |
|---|-----|---------|---------|
| 5 | **Extract shared helpers into `scripts/lib/mde-common.sh`** | `scripts/lib/mde-common.sh` (new), 20+ scripts | `log()`, `have_cmd()`, `setup_path()` are duplicated across 15-20 scripts. Extract into a shared library sourced by all. `setup_path()` contains hardcoded `/Users/rmanaloto` in every copy. |
| 6 | **Remove stale standalone bun binary (~57MB)** | `~/.bun/bin/bun`, `~/.bun/bin/bunx` | Leftover from bun's own installer. Shadowed by mise-managed bun. Saves disk space, reduces confusion. Also run `mise uninstall bun@1.3.8` for stale mise version. |
| 7 | **Remove duplicate `mise activate zsh` from ~/.zshrc** | `~/.zshrc` (~line 89) | Activation runs twice per shell (~5ms waste). Keep the copy in `macos-env.zsh` as authoritative. |
| 8 | **Add `uv tool list` post-upgrade verification** | `scripts/macos-dev-maintenance.sh` | The `update_uv()` function runs `uv tool upgrade --all` but never verifies success. Add a post-upgrade `uv tool list` for auditability. |
| 9 | **Create idempotent bootstrap script** | `scripts/bootstrap.sh` (new) | Currently no single command reproduces the environment. A bootstrap script would run `brew bundle install`, `mise install`, `bun install -g`, and `ensure-managed-configs.sh`. |

### P2 -- Nice-to-Have (backlog)

| # | Fix | Details |
|---|-----|---------|
| 10 | **Evaluate chezmoi for dotfiles management** | Replace `ensure-managed-configs.sh` with `chezmoi apply`. Gains: diff/preview, template variables (eliminate hardcoded paths), encryption, two-way merge. Migration effort: 1-2 days. Strongly recommended by best-practices research. |
| 11 | **Pin critical mise tools to specific versions** | All tools use `version = "latest"` in global config. No lockfile (`mise.lock`). `mise upgrade` can introduce breaking changes. |
| 12 | **Add UV_PYTHON_DOWNLOADS to mise config.toml [env]** | `~/.config/mise/config.toml` example in `docs/mise-config.md` still shows `UV_NO_MANAGED_PYTHON = "1"`. |
| 13 | **Reconcile pixi/uv tool ownership overlap** | Install scripts try pixi first, uv as fallback. `verify-langchain-tools.sh` only checks `uv tool list`, so pixi-installed tools appear as "missing" even if functional. |
| 14 | **Add Brewfile audit to `mde-drift-check.sh`** | Once Brewfile exists, add `brew bundle check` to drift detection for package-level drift. |

---

## 4. Cross-Tool Issues

### Issue 1: Dual Python Ownership (mise + Homebrew)

Homebrew owns `python` and `python@3.14` because `llvm` depends on them. The
mise-managed Python wins via PATH ordering, but the brew Python persists. Python
migration is guarded in `mde-migrate-to-mise.sh` and `macos-dev-maintenance.sh`.

**Risk:** Low. Would only cause confusion if someone runs `/opt/homebrew/bin/python3` directly.

### Issue 2: Multiple claude Binaries Across PATH

A mise shim and a direct install of `claude` coexist. The `~/.local/bin/claude`
wrapper script takes precedence (PATH position 3 vs mise shims at position 1).
Cleanup functions in `install-agent-stack.sh` and `macos-dev-maintenance.sh`
remove the `~/.bun/bin/claude` symlink to prevent a third conflict.

**Risk:** Low. Cosmetic only; the wrapper script is the intended entrypoint.

### Issue 3: Bun Completions Disabled After Migration

The old `source "$BUN_INSTALL/_bun"` line (37KB sourced on every shell startup)
was removed from `macos-env.zsh`. The replacement (fpath symlink to
`~/.oh-my-zsh/custom/completions/_bun`) was documented as a comment but never
created. Bun tab completions do not work.

**Fix:** `ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun`

### Issue 4: uv Cache Location Not Enforced via mise config

`UV_CACHE_DIR` is set to `~/Library/Caches/uv` by shell exports in 5+ files,
but not in `~/.config/mise/config.toml` `[env]`. Scripts defensively re-export
this variable, which is correct but duplicative.

### Issue 5: pixi/uv Tool Ownership Overlap

Both `pixi global install` and `uv tool install` are used for Python CLI tools.
The install scripts try pixi first and fall back to uv. Verification scripts
(`verify-langchain-tools.sh`) only check `uv tool list`, making pixi-installed
tools appear as "missing" even when functional.

---

## 5. Validation Results

### Runtime Checks (all PASS)

| Check | Version | Resolution |
|-------|---------|------------|
| Python | 3.14.3 | mise shim |
| Node | 25.7.0 | mise shim |
| Bun | 1.3.10 | mise shim |
| Go | 1.26.0 | mise shim |
| Rust | 1.93.1 | mise shim |

### Binary Resolution (all PASS)

- All 9 key binaries resolve via mise direct installs
- Homebrew v5.0.15 operational
- Bun v1.3.10 with 2609 global packages (25 top-level) functional
- uv v0.10.7 operational

### Alias Checks (all PASS after fix)

- 6 `mde-*` aliases resolve after alias-fixer ran `ensure-managed-configs.sh`
- Templates now match deployed files

### Drift Inventory

| # | Warning | Severity | Remediation |
|---|---------|----------|-------------|
| D1 | brew owns `python` | Medium | Blocked by llvm. No action unless llvm removed. |
| D2 | brew owns `python@3.14` | Medium | Same root cause as D1. |
| D3 | mise shims not first in PATH (oh-my-opencode at #1) | Low | Benign; oh-my-opencode does not shadow runtimes. |
| D4 | bun at multiple locations (mise + standalone) | Low | Remove `~/.bun/bin/bun` and `~/.bun/bin/bunx`. |
| D5 | uv at multiple locations | Low | Verify with `which -a uv`. |
| D6 | pixi at multiple locations | Low | Remove standalone if mise manages pixi. |

---

## 6. BDD Test Plan Guidance

Suggested location: `scripts/tests/`

The next team should flesh out these Gherkin-style scenario outlines into
executable tests (bats, shunit2, or plain bash assertions).

### Scenario Group 1: Template Sync

```gherkin
Feature: Template-to-deploy synchronization
  Background:
    Given the repository templates are the source of truth
    And ensure-managed-configs.sh uses the MANAGED_MARKER guard

  Scenario: Templates propagate on maintenance run
    Given macos-dev-maintenance.sh runs without MDE_AUTOFIX
    When sync_managed_configs is invoked
    Then deployed aliases.zsh matches templates/oh-my-zsh/aliases.zsh
    And deployed macos-env.zsh matches templates/oh-my-zsh/macos-env.zsh

  Scenario: Unmanaged files are not overwritten
    Given a file in ~/.oh-my-zsh/custom/ without the MANAGED_MARKER
    When ensure-managed-configs.sh runs
    Then the file is not modified

  Scenario: New template files are deployed
    Given a new template is added to templates/oh-my-zsh/
    When ensure-managed-configs.sh runs
    Then the new file appears in ~/.oh-my-zsh/custom/
```

### Scenario Group 2: Alias Resolution

```gherkin
Feature: MDE lifecycle aliases
  Scenario Outline: All mde-* aliases resolve
    Given aliases.zsh is deployed with the MDE lifecycle block
    When the user runs <alias>
    Then the command resolves to <target>

    Examples:
      | alias              | target                                    |
      | mde-update         | scripts/macos-dev-maintenance.sh          |
      | mde-update-fast    | scripts/macos-dev-maintenance.sh (no agents/MCP) |
      | mde-verify         | scripts/verify-all.sh                     |
      | mde-drift          | scripts/mde-drift-check.sh                |
      | mde-migrate        | scripts/mde-migrate-to-mise.sh            |
      | mde-agents-review  | scripts/mde-agents-review.sh              |
```

### Scenario Group 3: Tool Precedence

```gherkin
Feature: Tool precedence enforcement
  Scenario: mise-managed Python takes precedence over brew
    Given mise manages python@latest
    And brew has python installed (llvm dependency)
    When the user runs "which python3"
    Then the result is under ~/.local/share/mise/

  Scenario: mise-managed bun takes precedence over standalone
    Given mise manages bun@latest
    And ~/.bun/bin/bun exists (standalone)
    When the user runs "which bun"
    Then the result is under ~/.local/share/mise/
```

### Scenario Group 4: Maintenance Lifecycle

```gherkin
Feature: Maintenance update ordering
  Scenario: Update pipeline runs in correct order
    When macos-dev-maintenance.sh runs
    Then brew updates run before mise updates
    And mise updates run before bun updates
    And bun updates run before uv updates
    And bun upgrade is skipped when bun is mise-managed
    And uv self update is skipped when uv is mise-managed
```

### Scenario Group 5: uv/mise Integration

```gherkin
Feature: uv respects mise Python ownership
  Scenario: UV_PYTHON_DOWNLOADS prevents uv from downloading Python
    Given UV_PYTHON_DOWNLOADS=never is set
    When uv tool install runs
    Then uv uses the mise-managed Python
    And uv does not download its own Python interpreter
```

### Scenario Group 6: Drift Detection

```gherkin
Feature: Drift detection
  Scenario: Brew-owned runtimes are flagged
    Given mise should own all language runtimes
    When mde-drift-check.sh runs
    Then any brew-owned node/go/rust is flagged as drift
    And brew-owned python is flagged with llvm caveat

  Scenario: PATH ordering is validated
    Given mise shims should be first in PATH
    When mde-drift-check.sh runs
    Then non-mise entries before mise shims are flagged
```

---

## 7. Code Review Scope

Priority-ordered files for the next team to review. Each entry lists the key
concerns found during the audit.

### Priority 1 (Critical Path)

**`scripts/ensure-managed-configs.sh`**
- `sync_file()`: Copy-based deployment with MANAGED_MARKER guard. No checksum
  comparison (always copies). No backup on overwrite. No `--dry-run` mode.
- Review whether symlinks would be safer than copies.
- Review the marker string detection logic.

**`scripts/macos-dev-maintenance.sh`**
- `MDE_AUTOFIX` gate (line ~507-528): Config sync should run unconditionally.
- Update ordering: brew -> mise -> bun -> uv -> pixi. Verify per-step failure
  isolation (`|| failures=1` pattern) is consistent.
- `update_bun()` / `update_uv()`: Verify mise-managed detection logic
  (path-based `case` statements) covers all edge cases.
- Lock file handling and re-entrant safety.

### Priority 2 (Install Scripts)

**`scripts/install-agent-stack.sh`**
- `ensure_uv()`: Falls back to `curl | sh` if uv is missing. Review security
  implications (uv install script piped to shell).
- `tool_python_path()`: Resolves mise-managed Python for uv. Verify error
  handling when `mise where python@3.12` fails.
- `install_node_tool()`: Uses `bun add -g`. Review error handling for package
  install failures.

**`scripts/install-langchain-cli-tools.sh`**
- `UV_TOOL_FORCE=1`: Forces reinstall of specific tools. Review whether this
  is necessary on every run or only for specific tools.
- `UV_TOOL_TIMEOUT_SECONDS=600`: 10-minute timeout for `docs-monorepo`.
  Review whether this is sufficient and whether timeout failures are handled.
- Git clone + patching for internal tools: Review security of git clone
  operations and patch application.

### Priority 3 (Shell Config)

**`templates/oh-my-zsh/macos-env.zsh`**
- PATH construction: Verify the 10-position PATH matches the precedence model.
- `UV_PYTHON_DOWNLOADS=never`: Confirm this is set before any uv invocation.
- mise activation guard: `command -v mise` check is correct but review the
  duplicate activation note.
- Bun completions: Confirm the fpath approach is documented correctly.
- Secrets loading: Review `mde_export_secret()` and Keychain integration.

**`templates/oh-my-zsh/aliases.zsh`**
- All alias targets use `$HOME` expansion. Verify all target scripts exist.
- MDE lifecycle block: Confirm all 6 aliases are present and correct.
- No alias depends on env vars from `macos-env.zsh` (which loads after
  `aliases.zsh` alphabetically). Currently safe but worth documenting.

---

## 8. Documentation Update Inventory

| File | Current State | Required Update |
|------|--------------|-----------------|
| `AGENTS.md` | SkillPort skill listings only | Add MDE tool management context, reference audit findings |
| `README.md` | Quickstart + golden path | Add `mde-*` aliases section, reference tool audit, add Brewfile install step once Brewfile exists |
| `docs/mise-config.md` | Shows `UV_NO_MANAGED_PYTHON = "1"` (line 24) | Change to `UV_PYTHON_DOWNLOADS = "never"` |
| `docs/setup-notes.md` | Shows `export UV_NO_MANAGED_PYTHON=1` (line 350) | Change to `export UV_PYTHON_DOWNLOADS=never` |
| `docs/decision-log.md` | References old variable name (line 60) | Add new entry documenting UV_PYTHON_DOWNLOADS migration |
| `docs/toolchain-precedence.md` | Accurate but sparse | Add cross-tool issue notes from Section 4 above |

### Note on CLAUDE.md

`/Users/rmanaloto/CLAUDE.md` is a user-level project instructions file for
claude-flow configuration. It is NOT checked into this repository. The next
team should evaluate whether MDE-specific instructions (tool precedence,
maintenance workflow) belong in a repo-level `.claude/CLAUDE.md` or similar.

---

## 9. Source Reports Index

All reports are in `docs/tool-audit/`:

| Report | Lines | Scope |
|--------|-------|-------|
| `mise-report.md` | 295 | mise configuration, activation, managed runtimes, integration points |
| `homebrew-report.md` | 299 | Homebrew packages, update flow, brew/mise overlap, missing Brewfile |
| `oh-my-zsh-report.md` | 447 | Template deployment, shell startup flow, sync gap root cause analysis |
| `bun-report.md` | 291 | Bun installation, global packages, completions, dual binary issue |
| `uv-report.md` | 295 | uv installation, Python integration, UV_NO_MANAGED_PYTHON migration |
| `integration-report.md` | 322 | Cross-tool integration, validation results, ownership matrix, drift |
| `best-practices-research.md` | 421 | chezmoi, nix-darwin, Ansible, Brewfile, mise tasks, dotbot comparison |
| `best-practices-review.md` | 645 | Gap analysis, prioritized recommendations, migration paths, what NOT to change |

**Total: 3,015+ lines across 8 reports.**

---

## 10. Recommended Next Team Composition

### Agent Roles

| Agent | Subagent Type | Scope | Key Deliverables |
|-------|---------------|-------|------------------|
| **doc-updater** | `coder` | Update stale docs (P0-4) and AGENTS.md/README.md | Updated `docs/mise-config.md`, `docs/setup-notes.md`, `docs/decision-log.md`, `README.md` |
| **bdd-planner** | `tester` | Flesh out BDD test plans from Section 6 | Executable test files in `scripts/tests/` |
| **code-reviewer** | `reviewer` | Review critical scripts from Section 7 | Review findings document with severity ratings |
| **fix-implementer** | `coder` | Implement P0 fixes (Brewfile, gate, completions, docs) | Modified `scripts/macos-dev-maintenance.sh`, `scripts/ensure-managed-configs.sh`, new `Brewfile` |
| **qa-validator** | `tester` | Run full verification after all changes | Validation report confirming no regressions |

### Execution Order

```
Wave 1 (parallel):
  - doc-updater: Fix stale UV_NO_MANAGED_PYTHON references (P0-4)
  - code-reviewer: Review scripts from Section 7

Wave 2 (parallel, after Wave 1):
  - fix-implementer: Implement P0-1 (Brewfile), P0-2 (gate fix), P0-3 (completions)
  - bdd-planner: Write test scenarios from Section 6

Wave 3 (sequential, after Wave 2):
  - qa-validator: Run mde-verify, mde-drift, diff templates vs deployed
  - doc-updater: Update README.md and AGENTS.md with audit results
```

### What the Next Team Should NOT Change

These patterns are strengths identified in `best-practices-review.md` Section 6:

1. **Do NOT replace launchd** with an external scheduler (cron, systemd, etc.)
2. **Do NOT replace the update orchestration** -- no single tool manages 6 package managers
3. **Do NOT replace drift detection** -- `mde-drift-check.sh` is custom and valuable
4. **Do NOT replace Keychain secrets** with file-based encryption
5. **Do NOT replace the JSON health-check framework** (`mde-json.sh`)
6. **Do NOT adopt nix-darwin or Ansible** at this time (overkill for single machine)
7. **Do NOT reorganize** to a topical directory structure (current layout is functional)

---

## Quick Reference: Key File Paths

| Purpose | Path |
|---------|------|
| Maintenance script | `scripts/macos-dev-maintenance.sh` |
| Config deployment | `scripts/ensure-managed-configs.sh` |
| Drift detection | `scripts/mde-drift-check.sh` |
| Health check | `scripts/health-check.sh` |
| Verification suite | `scripts/verify-all.sh` |
| Alias template | `templates/oh-my-zsh/aliases.zsh` |
| Env template | `templates/oh-my-zsh/macos-env.zsh` |
| Shared JSON lib | `scripts/lib/mde-json.sh` |
| Agent tools installer | `scripts/install-agent-stack.sh` |
| LangChain tools installer | `scripts/install-langchain-cli-tools.sh` |
| Toolchain precedence doc | `docs/toolchain-precedence.md` |
| Decision log | `docs/decision-log.md` |
| mise config doc | `docs/mise-config.md` |
| Setup notes | `docs/setup-notes.md` |
