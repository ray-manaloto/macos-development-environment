# Consolidation Synthesis: macOS Toolchain Modernization

Date: 2026-02-28
Input: Research reports R1-R5, Implementation Spec, Consolidated Spec

---

## 1. Bugs Found

| Bug | Source Report | File:Line | Severity | Fix Description |
|-----|-------------|-----------|----------|-----------------|
| `mise self-update` lacks `--yes` flag; hangs in launchd/non-interactive contexts | R1 #8, #14 | `scripts/macos-dev-maintenance.sh:342` | **HIGH** | Change to `mise self-update --yes --no-plugins` |
| Duplicate `eval "$(mise activate zsh)"` -- called in both `macos-env.zsh` and `~/.zshrc` | R4 Shell #1 | `templates/oh-my-zsh/macos-env.zsh:12`, `~/.zshrc:89` | MEDIUM | Remove the `~/.zshrc:89` line; keep template-managed copy as authoritative |
| `uv self update` guard missing mise-managed path detection | R2 #1, #2 | `scripts/macos-dev-maintenance.sh:384-401` | **HIGH** | Add `"$HOME/.local/share/mise/installs/uv/"*` to the case guard |
| `bun upgrade` called unconditionally in `install-langchain-cli-tools.sh` when bun may be mise-managed | R2 #5 | `scripts/install-langchain-cli-tools.sh:53` | **HIGH** | Add mise path guard matching the pattern in `macos-dev-maintenance.sh:349-364` |
| `pixi self-update` called unconditionally; fails if pixi was externally packaged | R2 #7 | `scripts/macos-dev-maintenance.sh:419`, `scripts/install-agent-stack.sh:83` | MEDIUM | Add `|| true` fallback or `2>/dev/null` guard |
| `verify-tooling.sh` calls mutating `setup-skypilot-aws.sh` (writes credentials, restarts services) | R5 #4 | `scripts/verify-tooling.sh:32-39` | **HIGH** | Extract read-only `verify-skypilot-aws.sh`; remove setup call from verify path |
| `sky-status.sh` kills stale processes unconditionally in `kill_stale_api_server()` | R5 #5 | `scripts/sky-status.sh:60-71` | MEDIUM | Gate behind `--kill-stale` flag; do not run from verification path |
| `rust@latest` missing from `install-agent-stack.sh` `ensure_runtimes()` (present in maintenance script) | R1 Script Audit | `scripts/install-agent-stack.sh:63` | LOW | Add `rust@latest` to `mise use -g` call for consistency |
| Duplicate `cleanup_gemini_cli` call in maintenance script | R4 Script Audit | `scripts/macos-dev-maintenance.sh:489,497` | LOW | Remove duplicate call at line 497 |
| `setup_path()` in maintenance script missing `~/.amp/bin`, `~/.antigravity/bin`, gcloud, oh-my-zsh bin | R4 Shell #8 | `scripts/macos-dev-maintenance.sh:173` | LOW | Sync PATH entries with `templates/oh-my-zsh/macos-env.zsh` |
| `secrets-smoke-test.sh` only checks 5 secrets; missing `GITHUB_MCP_PAT`, `LANGSMITH_WORKSPACE_ID` | R4 Script Audit | `scripts/secrets-smoke-test.sh` | LOW | Add missing secret checks |
| SkyPilot completion in `~/.zshrc` not guarded with file existence check | R4 Script Audit | `~/.zshrc:87` | LOW | Wrap with `[[ -f ~/.sky/.sky-complete.zsh ]] && . ~/.sky/.sky-complete.zsh` |
| `install-validation-launchd.sh` uses deprecated `launchctl load/unload` API | R4 Secrets #3 | `scripts/install-validation-launchd.sh` | LOW | Migrate to `launchctl bootout`/`launchctl bootstrap` with `gui/$UID` domain |
| No `op` CLI version check before service account reads | R4 Secrets #8 | `scripts/macos-dev-maintenance.sh:62` | LOW | Add version >= 2.18.0 check |
| Env file quote stripping differs between zsh and bash versions | R4 Secrets #9 | `macos-env.zsh` vs `macos-dev-maintenance.sh:136` | LOW | Harmonize pattern or extract to shared function |

---

## 2. Migration Items

| Deprecated Pattern | Replacement | Source Report | Files Affected |
|-------------------|-------------|---------------|----------------|
| `UV_NO_MANAGED_PYTHON=1` (undocumented env var) | `UV_PYTHON_DOWNLOADS=never` (official API) | R2 #4 | `scripts/macos-dev-maintenance.sh:4`, `scripts/install-langchain-cli-tools.sh:1`, `scripts/install-agent-stack.sh:5`, `templates/oh-my-zsh/macos-env.zsh` |
| `ubi:owner/repo` backend prefix | `github:owner/repo` | R1 #3 | No current usage (preemptive -- do not introduce `ubi:`) |
| `launchctl load/unload` | `launchctl bootout gui/$UID/...` / `launchctl bootstrap gui/$UID ...` | R4 Secrets #3 | `scripts/install-validation-launchd.sh` |
| `source "$BUN_INSTALL/_bun"` for completions (37KB parsed every startup) | Move `_bun` to `fpath` via `~/.oh-my-zsh/custom/completions/_bun` | R4 Shell #9 | `templates/oh-my-zsh/macos-env.zsh:17-19` |
| Flat `task_*` settings namespace (deprecated before 2026.8.0) | `task.*` namespace | R1 #14 | No current usage (preemptive -- do not introduce flat `task_*`) |
| `python = "latest"` / `node = "latest"` without lockfile | Add `[settings] lockfile = true`; consider `node = "lts"` | R1 #1, #12 | `~/.config/mise/config.toml`, `docs/mise-config.md` |
| `setup_path()` duplicated in 8+ scripts | Extract to `scripts/lib/path-setup.sh` and source | R1 Script Audit, R5 #8 | `macos-dev-maintenance.sh`, `install-agent-stack.sh`, `install-langchain-cli-tools.sh`, `sky-status.sh`, `verify-openlit.sh`, `setup-skypilot-aws.sh`, `verify-langchain-tools.sh`, + others |
| `load_env_file_secrets()` duplicated across 4+ scripts | Extract to `scripts/lib/mde-common.sh` | R5 Open Question #7 | `sky-status.sh`, `verify-openlit.sh`, `setup-skypilot-aws.sh`, `verify-langchain-tools.sh` |
| Pixi-first install cascade for pure-Python tools | uv-first cascade (faster for PyPI packages), pixi fallback for conda deps | R2 #10, Pattern 5 | `scripts/install-agent-stack.sh:104-134` |

---

## 3. New Patterns to Adopt

### Pattern 1: Standardized Script Preamble
**Source:** R3 (thoughtbot/laptop Finding 1, Finding 2)

```bash
#!/usr/bin/env bash
set -euo pipefail

mde_log() {
  printf "\n[mde] %s\n" "$1"
}

trap 'mde_log "FAILED: $0" >&2' ERR
```

**Apply to:** All scripts in `scripts/`. Many currently lack `set -e` or use inconsistent `echo` logging.

---

### Pattern 2: Per-Operation Idempotency Guards
**Source:** R3 (thoughtbot/laptop Finding 1, br3ndonland Finding 6)

```bash
if command -v mise >/dev/null 2>&1; then
  mde_log "mise already installed, skipping"
else
  mde_log "Installing mise..."
  curl https://mise.jdx.dev/install.sh | sh
fi
```

**Apply to:** All `scripts/install-*.sh` files. Guards currently exist for some operations but not consistently.

---

### Pattern 3: `brew bundle check` Gate
**Source:** R3 (br3ndonland Finding 6), R5 (Finding 2)

```bash
if brew bundle check --file="$BREWFILE" --no-upgrade 2>/dev/null; then
  mde_log "All Homebrew packages already installed"
else
  mde_log "Installing missing Homebrew packages..."
  brew bundle install --file="$BREWFILE" --no-upgrade
fi
```

**Apply to:** New `scripts/mde-update.sh`. Requires creating a `Brewfile` first (see Migration Items).

---

### Pattern 4: Required Env Var Contract with `:?` Fail-Fast
**Source:** R3 (br3ndonland Finding 5)

```bash
: "${MDE_TOOL_OWNERSHIP_FILE:?MDE_TOOL_OWNERSHIP_FILE must be set}"
: "${MDE_MISE_EXCEPTION_ALLOWLIST:?MDE_MISE_EXCEPTION_ALLOWLIST must be set}"
```

**Apply to:** All new scripts that depend on `MDE_*` env vars (from Consolidated Spec Section 12).

---

### Pattern 5: Universal Tool Manager Self-Update Guard
**Source:** R2 (Patterns 1-3)

```bash
update_tool() {
  local tool="$1"
  local tool_path
  tool_path="$(command -v "$tool")"
  case "$tool_path" in
    "$HOME/.local/share/mise/installs/"*|"$HOME/.local/share/mise/shims/"*)
      mde_log "$tool is mise-managed; skipping self update (use mise upgrade)."
      return 0
      ;;
    /opt/homebrew/*|/usr/local/*)
      mde_log "$tool is Homebrew-managed; skipping self update."
      return 0
      ;;
  esac
  "$tool" self update || return 1
}
```

**Apply to:** `update_uv()`, `update_bun()`, `update_pixi()` in `scripts/macos-dev-maintenance.sh`; `ensure_uv()`, `ensure_bun()`, `ensure_pixi()` in `scripts/install-agent-stack.sh` and `scripts/install-langchain-cli-tools.sh`.

---

### Pattern 6: Numbered Shell Config Sourcing
**Source:** R3 (basnijholt Finding 8)

```
templates/oh-my-zsh/
  00-path.zsh          # PATH setup (mise shims first)
  10-exports.zsh       # Environment variables
  20-aliases.zsh       # Command aliases
  30-completions.zsh   # Tab completions
  40-integrations.zsh  # Tool integrations
```

**Apply to:** `templates/oh-my-zsh/` directory. Requires updating `scripts/ensure-managed-configs.sh` to match new filenames.

---

### Pattern 7: JSON Verification Output
**Source:** R5 (Finding 8, Pattern 2)

```bash
add_check() {
  local name="$1" status="$2" severity="$3" details="$4"
  CHECKS+=("$(printf '{"name":"%s","status":"%s","severity":"%s","details":"%s"}' \
    "$(json_esc "$name")" "$status" "$severity" "$(json_esc "$details")")")
}
```

**Apply to:** All `scripts/verify-*.sh` scripts via new `--json` flag. Output schema defined in Implementation Spec.

---

### Pattern 8: Shared Script Library
**Source:** R1 Script Audit, R5 Open Question #7-8

```bash
# scripts/lib/mde-common.sh
# Contains: setup_mde_path(), load_env_file_secrets(), mde_log(), json_esc(), have_cmd()
source "${MDE_REPO:-$(cd "$(dirname "$0")/.." && pwd)}/scripts/lib/mde-common.sh"
```

**Apply to:** All scripts that currently duplicate `setup_path()`, `load_env_file_secrets()`, `have_cmd()`, `json_escape()`.

---

### Pattern 9: Brewfile as Canonical Brew Boundary
**Source:** R5 (Pattern 1, Decision D1), R3 (br3ndonland Finding 6)

```ruby
# Brewfile
cask_args require_sha: true
brew "gnupg"
brew "curl"
brew "ripgrep"
brew "tmux"
brew "git"
brew "llvm"
cask "osquery"
```

**Apply to:** New `Brewfile` at repo root. Becomes the single source of truth for brew-owned packages.

---

### Pattern 10: mise Global Config with Lockfile
**Source:** R1 #1, #12, Recommended Patterns

```toml
min_version = "2025.1.0"

[settings]
lockfile = true
yes = true

[tools]
python = "latest"
node = "lts"
bun = "latest"
go = "latest"
rust = "latest"

[env]
UV_PYTHON_DOWNLOADS = "never"
GOBIN = "{{env.HOME}}/.local/bin"
UV_CACHE_DIR = "{{env.HOME}}/Library/Caches/uv"
_.path = ["{{env.HOME}}/.local/bin"]
```

**Apply to:** `~/.config/mise/config.toml`, `docs/mise-config.md`.

---

## 4. Cross-Reference Map

### Phase 1 (P1): Deterministic Version Policy

| Finding | Source | Impact |
|---------|--------|--------|
| R1 #1: `python = "latest"` / `node = "latest"` provides no reproducibility | R1 | Add `lockfile = true` to pin resolved versions; consider `node = "lts"` |
| R1 #12: Lock file format enables per-platform checksums | R1 | Enable `lockfile = true` in global config; commit `mise.lock` for project configs |
| R1 #6: `--bump` rewrites config -- unsafe for automation | R1 | Never use `--bump` in scripts; keep `--yes` only |
| R1 #14: Stricter lockfile enforcement in v2026.2.23 | R1 | Use `lockfile = true` (not `locked = true`) in dev; reserve `locked = true` for CI |
| R2 #3: `uv tool upgrade --all` respects original install constraints | R2 | Safe for automation; pinning is inherited from install command |
| R3 Finding 4: br3ndonland uses multiple concurrent versions + precompiled binaries | R3 | Reference pattern for multi-version Python/Node if needed |

### Phase 2 (P2): Manager Ownership Cleanup

| Finding | Source | Impact |
|---------|--------|--------|
| R1 #4: uv and pixi are NOT mise backends; remain independent installers | R1 | Confirms current architecture: mise manages the uv/pixi binaries, not their ecosystems |
| R1 #5: `mise install` vs `mise use -g` -- correct pattern already used | R1 | Keep current `install` + `use -g` + `reshim` pattern |
| R1 #2: Aqua backend preferred for CLI tools (aws-cli, kubectl, terraform, etc.) | R1 | When adding tools to mise, prefer `aqua:` over `asdf:` for security |
| R2 #9: uv backend = `aqua:astral-sh/uv`, pixi = `aqua:prefix-dev/pixi` | R2 | Both are stable aqua backends; mise can own their binary lifecycle |
| R2 #10: uv-first cascade faster for pure-Python tools; pixi for conda deps | R2 | Consider inverting cascade in `install_python_tool()` |
| R5 #6: Brew formulae audit identifies runtimes vs OS tools | R5 | Runtimes (node, go, rust, python) -> mise; OS tools (gnupg, curl, llvm, rg) -> brew |
| R1 Script Audit: `rust@latest` missing from `install-agent-stack.sh` | R1 | Add `rust@latest` for consistency with maintenance script |

### Phase 3 (P3): Make Verification Read-Only

| Finding | Source | Impact |
|---------|--------|--------|
| R5 #4: `verify-tooling.sh` calls mutating `setup-skypilot-aws.sh` | R5 | Extract `verify-skypilot-aws.sh` (read-only checks only) |
| R5 #5: `sky-status.sh` kills processes unconditionally | R5 | Gate `kill_stale_api_server()` behind `--kill-stale` flag |
| R5 #8: JSON output pattern for verification scripts | R5 | Adopt `printf`-based JSON pattern for all `verify-*.sh --json` |
| R5 #3: `brew outdated --json=v2` for machine-readable output | R5 | Use in `status-dashboard.sh` JSON mode |
| R4 Shell #7: Missing aliases `mde-verify`, `mde-drift` | R4 | Add aliases; requires creating corresponding scripts first |
| R5 Script Audit: `verify-agent-tools.sh` is exemplary read-only pattern | R5 | Use as reference for new verification scripts |

### Phase 4 (P4): Optional Components as Soft Checks

| Finding | Source | Impact |
|---------|--------|--------|
| R5 Pattern 3: Environment variable gating for optional components | R5 | Standardize `MDE_VERIFY_SKYPILOT`, `MDE_VERIFY_OPENLIT`, `MDE_VERIFY_LANGCHAIN` env vars |
| R5 #9: osquery excluded from cask upgrades (sudo requirement) | R5 | Document the exclusion; create separate `upgrade-sudo-casks.sh` for interactive use |
| R5 #10: `brew outdated --cask` excludes auto-update casks by default | R5 | Use `--greedy-auto-updates` if comprehensive staleness check is needed |

### Phase 5 (P5): uv/mise Interaction Hardening

| Finding | Source | Impact |
|---------|--------|--------|
| R2 #1: `uv self update` fails silently when mise-managed | R2 | Add mise path detection to all uv self-update guards |
| R2 #2: Reliable detection pattern for mise-managed tools | R2 | Use `case "$uv_path" in "$HOME/.local/share/mise/installs/"*` pattern |
| R2 #5: `bun upgrade` creates version tracking drift under mise | R2 | Already guarded in maintenance; fix `install-langchain-cli-tools.sh` |
| R2 #7: pixi self-update is a compile-time feature flag | R2 | Add `|| true` or `2>/dev/null` fallback |
| R2 #4: `UV_NO_MANAGED_PYTHON` is undocumented legacy | R2 | Migrate to `UV_PYTHON_DOWNLOADS=never` |
| R1 #7: Hybrid shims+activate is the recommended mise approach | R1 | Keep `~/.zprofile` shims + `~/.zshrc` activate; fix duplicate |
| R1 #10: `MISE_YES=1` or `settings.yes = true` for non-interactive contexts | R1 | Set in global config and/or launchd scripts |

---

## 5. Conflicts Resolved

### Conflict 1: Pixi-first vs uv-first install cascade
- **R2 #10** recommends inverting to uv-first for speed (pure-Python packages).
- **R2 Decision 6** says do NOT change the cascade without testing.
- **Resolution:** Keep pixi-first as default (safe). Add a `--uv-first` flag or per-tool override for known pure-Python packages. The cascade order matters less than correctness.

### Conflict 2: `UV_NO_MANAGED_PYTHON` -- keep vs migrate
- **R1** notes it works and recommends keeping as shell export alongside `[env]`.
- **R2 #4** recommends migrating to `UV_PYTHON_DOWNLOADS=never` because the old name is undocumented.
- **Resolution:** Migrate to `UV_PYTHON_DOWNLOADS=never` everywhere. The old name may be removed in a future uv release. R2 is more current on uv internals.

### Conflict 3: Brewfile location
- **R5 Pattern 1** recommends `Brewfile` at repo root.
- **Consolidated Spec** does not specify Brewfile location.
- **Resolution:** Place at repo root (`Brewfile`) following Homebrew convention. This is the standard path that `brew bundle` discovers automatically.

### Conflict 4: Project-level `mise.toml` vs global config only
- **R1 Decision 9** says do NOT create a project-level `mise.toml` (this is a config repo, not a software project).
- **R3 Finding 4** (br3ndonland) uses a project-level config with tasks.
- **Resolution:** Keep global `~/.config/mise/config.toml` as primary. Do not create `mise.toml` in this repo. Mise tasks (if adopted) go in the global config.

### Conflict 5: Numbered oh-my-zsh files vs current naming
- **R3 Pattern 5** recommends numbered filenames for deterministic load order.
- **R4** confirms oh-my-zsh loads `custom/*.zsh` alphabetically via glob.
- **Resolution:** Adopt numbered filenames. The rename requires updating `scripts/ensure-managed-configs.sh` and is a Phase P1 deliverable. Current `aliases.zsh` and `macos-env.zsh` are already loaded alphabetically (a < m), but numbered prefixes make the intent explicit.

### Conflict 6: `op read` vs `op run` for secret loading
- **R4 Secrets #7** compares both approaches.
- **Resolution:** Keep `op read` (current). Partial failure tolerance is more important than API call reduction. Only switch to `op run` if rate limiting becomes a problem.

### Conflict 7: Keychain startup cost -- optimize or accept
- **R4 Shell #6** documents 136ms overhead for 7 keychain reads.
- **Resolution:** Default `MDE_AUTOLOAD_SECRETS=0` when env file has values. Add `mde-secrets-refresh` alias. The 136ms is acceptable for first-run but unnecessary on subsequent shells when `secrets.env` is populated.

---

## 6. Priority Ordering

Items ranked by: risk (high to low) x impact (high to low) x effort (low to high).

### Tier 1: Critical -- Fix First (high risk, high impact, low effort)

| # | Item | Risk | Impact | Effort | Phase |
|---|------|------|--------|--------|-------|
| 1 | Add `--yes` to `mise self-update` in maintenance script | Launchd hang | Blocks automation | 1 line | P5 |
| 2 | Add mise path guard to `uv self update` | Silent failure | Wrong uv version | 3 lines | P5 |
| 3 | Fix `bun upgrade` guard in `install-langchain-cli-tools.sh` | Version drift | Broken bun shim | 5 lines | P5 |
| 4 | Remove `setup-skypilot-aws.sh` call from `verify-tooling.sh` | Credential overwrite | Verify is mutating | 10 lines | P3 |
| 5 | Gate `kill_stale_api_server()` in `sky-status.sh` | Process kill | Verify kills procs | 5 lines | P3 |

### Tier 2: High -- Fix Soon (medium risk, high impact, moderate effort)

| # | Item | Risk | Impact | Effort | Phase |
|---|------|------|--------|--------|-------|
| 6 | Migrate `UV_NO_MANAGED_PYTHON=1` to `UV_PYTHON_DOWNLOADS=never` | Future breakage | 3 scripts | 4 lines each | P5 |
| 7 | Add `pixi self-update` fallback guard | Script failure | Maintenance halts | 3 lines each | P5 |
| 8 | Remove duplicate `mise activate zsh` in `~/.zshrc` | 20-30ms wasted | Every prompt | 1 line | P1 |
| 9 | Enable `lockfile = true` in mise global config | Reproducibility | Version drift | 2 lines | P1 |
| 10 | Extract shared `setup_path()` into `scripts/lib/path-setup.sh` | Maintenance burden | 8+ scripts | New file + sourcing | P2 |
| 11 | Extract shared `load_env_file_secrets()` into `scripts/lib/mde-common.sh` | Drift between copies | 4+ scripts | New file + sourcing | P2 |

### Tier 3: Medium -- Planned Work (low risk, high impact, higher effort)

| # | Item | Risk | Impact | Effort | Phase |
|---|------|------|--------|--------|-------|
| 12 | Create `Brewfile` for brew boundary | None | Enables `brew bundle check` | Audit + new file | P1 |
| 13 | Add missing `mde-*` aliases to `templates/oh-my-zsh/aliases.zsh` | None | UX contract | 6 aliases | P1 |
| 14 | Create `scripts/mde-drift-check.sh` | None | Drift enforcement | New script | P2 |
| 15 | Create `scripts/mde-migrate-to-mise.sh` with dry-run/apply | None | Migration tooling | New script | P2 |
| 16 | Add `mise doctor` to `health-check.sh` | None | Better diagnostics | 5 lines | P1 |
| 17 | Add `--json` flag to all `verify-*.sh` scripts | None | Machine-readable output | Per-script work | P3 |
| 18 | Standardize script preamble (`set -euo pipefail` + trap) | May surface bugs | Consistency | All scripts | P1 |
| 19 | Create maintenance launchd plist installer (12h interval) | None | Automates maintenance | New script | P3 |
| 20 | Create `docs/tooling/mise-exceptions.yaml` | None | Exception governance | New file | P1 |

### Tier 4: Low -- Nice to Have (low risk, moderate impact, variable effort)

| # | Item | Risk | Impact | Effort | Phase |
|---|------|------|--------|--------|-------|
| 21 | Number oh-my-zsh custom files (00-path.zsh, etc.) | Minor rename churn | Deterministic load | Rename + update | P1 |
| 22 | Move bun completions from `source` to `fpath` | None | 5-15ms startup | Symlink + edit | P1 |
| 23 | Sync maintenance `setup_path()` with `macos-env.zsh` PATH | Minor | Consistent paths | 5 lines | P2 |
| 24 | Remove duplicate `cleanup_gemini_cli` call | None | Clean code | 1 line | P3 |
| 25 | Add `op` version check >= 2.18.0 | None | Better errors | 5 lines | P3 |
| 26 | Fix secrets-smoke-test to check all 7 secrets | None | Coverage | 2 lines | P3 |
| 27 | Guard SkyPilot completion in `~/.zshrc` with file check | None | Clean startup | 1 line | P1 |
| 28 | Migrate `launchctl load/unload` to `bootout/bootstrap` | Deprecated API | Future-proof | 5 lines | P3 |
| 29 | Document osquery cask exclusion reason | None | Clarity | Comment block | P3 |
| 30 | Add `require_sha: true` to Brewfile (when created) | Cask integrity | Security | 1 line | P1 |
| 31 | Consider `node = "lts"` instead of `node = "latest"` | None | Stability | 1 line | P1 |
| 32 | Add `MISE_YES=1` or `settings.yes = true` for automation | None | Non-interactive trust | 1-2 lines | P1 |
| 33 | Default `MDE_AUTOLOAD_SECRETS=0` when env file has values | None | 136ms saved | Logic change | P1 |
| 34 | Document secret precedence chain | None | Clarity | Doc section | P1 |

---

## Appendix: Files Requiring Changes (by frequency of mentions)

| File | Change Count | Primary Phases |
|------|-------------|----------------|
| `scripts/macos-dev-maintenance.sh` | 10 | P3, P5 |
| `templates/oh-my-zsh/macos-env.zsh` | 5 | P1, P5 |
| `scripts/verify-tooling.sh` | 3 | P3, P4 |
| `scripts/install-agent-stack.sh` | 3 | P2, P5 |
| `scripts/install-langchain-cli-tools.sh` | 3 | P2, P5 |
| `templates/oh-my-zsh/aliases.zsh` | 2 | P1 |
| `scripts/sky-status.sh` | 2 | P3 |
| `scripts/health-check.sh` | 1 | P1 |
| `scripts/install-validation-launchd.sh` | 1 | P3 |
| `scripts/secrets-smoke-test.sh` | 1 | P3 |
| `docs/toolchain-precedence.md` | 1 | P2 |
| `~/.config/mise/config.toml` | 1 | P1 |
| `~/.zshrc` | 1 | P1 |
| **New files** | | |
| `scripts/lib/mde-common.sh` (shared library) | -- | P2 |
| `scripts/lib/path-setup.sh` (shared PATH) | -- | P2 |
| `Brewfile` | -- | P1 |
| `scripts/mde-drift-check.sh` | -- | P2 |
| `scripts/mde-migrate-to-mise.sh` | -- | P2 |
| `scripts/verify-skypilot-aws.sh` | -- | P3 |
| `docs/tooling/mise-exceptions.yaml` | -- | P1 |
| `scripts/mde-update.sh` | -- | P3 |
