# mise-First macOS Dev Environment Modernization: Implementation Spec v2

Date: 2026-02-28
Status: Decision-Complete
Audience: AI coding agent implementing all changes in this repository
Supersedes: `2026-02-28-mise-modernization-implementation-spec.md`, `2026-02-28-macos-toolchain-modernization-consolidated-spec.md`

This spec is self-contained. An implementing agent needs only this document plus access to the repository.

---

## 1. Version Policy Decisions

### 1.1 Global mise config.toml

File: `~/.config/mise/config.toml` (user global config, NOT in this repo)

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
uv = "latest"
pixi = "latest"

[env]
UV_PYTHON_DOWNLOADS = "never"
UV_CACHE_DIR = "{{env.HOME}}/Library/Caches/uv"
GOBIN = "{{env.HOME}}/.local/bin"
```

### 1.2 Rationale for Each Version Choice

| Runtime | Specifier | Why |
|---------|-----------|-----|
| python | `latest` | Pinned by `mise.lock`; `latest` keeps flexibility for upgrade cycles |
| node | `lts` | LTS is safer than `latest` for tooling stability; mise core backend |
| bun | `latest` | Primary JS runtime; bun moves fast, `latest` is appropriate |
| go | `latest` | Stable release cadence; pinned by lockfile |
| rust | `latest` | Stable release cadence; pinned by lockfile |
| uv | `latest` | Installed via `aqua:astral-sh/uv`; self-update delegated to mise |
| pixi | `latest` | Installed via `aqua:prefix-dev/pixi`; self-update delegated to mise |

### 1.3 Lockfile Strategy

- `lockfile = true` in global config generates `~/.config/mise/mise.lock`
- Do NOT enable `locked = true` in development (only in CI for strict enforcement)
- `mise.lock` is NOT committed to this repo (this is a config repo, not a software project)
- `yes = true` enables non-interactive operation for launchd and automation

---

## 2. Backend Selection Table

| Tool | Owner | Backend | mise Declaration | Notes |
|------|-------|---------|-----------------|-------|
| python | mise | `core:python` | `python = "latest"` | Primary runtime; core backend for env var support |
| node | mise | `core:node` | `node = "lts"` | Core backend; LTS channel for stability |
| bun | mise | `core:bun` | `bun = "latest"` | Core backend; primary JS runtime |
| go | mise | `core:go` | `go = "latest"` | Core backend |
| rust | mise | `core:rust` | `rust = "latest"` | Core backend |
| uv | mise | `aqua:astral-sh/uv` | `uv = "latest"` | Python tool manager; aqua has checksums+attestation |
| pixi | mise | `aqua:prefix-dev/pixi` | `pixi = "latest"` | Conda-forge tool manager |
| langchain-cli | uv tool | N/A | `uv tool install langchain-cli` | Pure-Python CLI |
| langgraph-cli | uv tool | N/A | `uv tool install langgraph-cli` | Pure-Python CLI |
| skypilot | uv tool | N/A | `uv tool install "skypilot[aws]"` | Pure-Python CLI |
| aider-chat | uv tool | N/A | `uv tool install aider-chat` | Pure-Python CLI |
| claude-code | bun -g | N/A | `bun add -g @anthropic-ai/claude-code` | Node CLI tool |
| codex | bun -g | N/A | `bun add -g @openai/codex` | Node CLI tool |
| gemini-cli | bun -g | N/A | `bun add -g @google/gemini-cli` | Node CLI tool |
| opencode | go install | N/A | `go install github.com/opencode-ai/opencode@latest` | Go CLI tool |
| gnupg | brew | N/A | `brew install gnupg` | OS-level crypto tool |
| curl | brew | N/A | `brew install curl` | System networking tool |
| llvm | brew | N/A | `brew install llvm` | Compiler toolchain |
| ripgrep | brew | N/A | `brew install ripgrep` | Search tool (system-level) |
| tmux | brew | N/A | `brew install tmux` | Terminal multiplexer |
| git | brew | N/A | `brew install git` | Version control |
| osquery | brew cask | N/A | `cask "osquery"` | System monitoring (sudo-required .pkg) |

### 2.1 Ownership Rule

No tool binary shall be installed by more than one manager. If `which -a <cmd>` shows paths from multiple managers (excluding wrappers), it is a policy violation flagged by the drift checker.

---

## 3. Script-by-Script Change Log

### 3.1 `scripts/macos-dev-maintenance.sh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 4 | Migrate env var name | `UV_NO_MANAGED_PYTHON` is undocumented; `UV_PYTHON_DOWNLOADS` is official | `export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` |
| 173 | Sync PATH with macos-env.zsh | Missing `~/.amp/bin`, `~/.antigravity/antigravity/bin`, `~/.oh-my-zsh/custom/bin`, `/opt/google-cloud-sdk/bin` | `export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"` | `export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:$home/.amp/bin:$home/.antigravity/antigravity/bin:$home/.oh-my-zsh/custom/bin:/opt/google-cloud-sdk/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"` |
| 342 | Add `--yes` to `mise self-update` | Prevents hang in launchd (non-interactive) context | `mise self-update \|\| return 1` | `mise self-update --yes \|\| return 1` |
| 391-397 | Add mise-managed path guard to `update_uv()` | `uv self update` fails silently when uv is mise-managed | `case "$uv_path" in /opt/homebrew/*\|/usr/local/*) ;; *) uv self update \|\| return 1 ;; esac` | `case "$uv_path" in "$HOME/.local/share/mise/installs/"*\|"$HOME/.local/share/mise/shims/"*) log "uv is mise-managed; skipping uv self update." ;; /opt/homebrew/*\|/usr/local/*) log "uv is Homebrew-managed; skipping uv self update." ;; *) uv self update \|\| return 1 ;; esac` |
| 419 | Add guard to `pixi self-update` | `pixi self-update` may be disabled in packaged builds | `pixi self-update \|\| return 1` | `if ! pixi self-update 2>/dev/null; then log "pixi self-update unavailable; skipping."; fi` |
| 496-497 | Remove duplicate `cleanup_gemini_cli` call | Line 489 already calls it; line 497 is a duplicate outside the `if` block | Lines 496-497: `cleanup_gemini_cli \|\| failures=1` (extra) + misaligned `fi` | Remove line 497 (`cleanup_gemini_cli \|\| failures=1`), fix indentation of `fi` on line 498 to align with `if` on line 493 |

**Test command:** `MDE_AUTOFIX=0 bash scripts/macos-dev-maintenance.sh` (exits 0 with no hangs)

### 3.2 `scripts/install-agent-stack.sh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 4 | Migrate env var name | Forward compatibility with uv | `export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` |
| 63 | Add `rust@latest` to `mise use -g` | Maintenance script includes rust but agent stack does not | `mise use -g python@latest node@latest bun@latest go@latest` | `mise use -g python@latest node@latest bun@latest go@latest rust@latest` |
| 67-77 | Add mise-managed guard to `ensure_uv()` | `uv self update` fails when uv is mise-managed | `uv self update >/dev/null 2>&1 \|\| true` | `local uv_path; uv_path="$(command -v uv)"; case "$uv_path" in "$HOME/.local/share/mise/installs/"*\|"$HOME/.local/share/mise/shims/"*\|/opt/homebrew/*\|/usr/local/*) ;; *) uv self update >/dev/null 2>&1 \|\| true ;; esac` |
| 79-89 | Add guard to `ensure_pixi()` | `pixi self-update` may be disabled | `pixi self-update >/dev/null 2>&1 \|\| true` | `pixi self-update >/dev/null 2>&1 \|\| true` (already has `\|\| true`, no change needed) |

**Test command:** `bash scripts/install-agent-stack.sh` (exits 0, all tools installed)

### 3.3 `scripts/install-langchain-cli-tools.sh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 4 | Migrate env var name | Forward compatibility | `export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` |
| 51-65 | Add mise-managed guard to `ensure_bun()` | `bun upgrade` causes version tracking drift when bun is mise-managed (R2 finding 5) | `bun upgrade \|\| true` (unconditional) | `local bun_path; bun_path="$(command -v bun)"; case "$bun_path" in "$HOME/.local/share/mise/installs/bun/"*) ;; *) bun upgrade \|\| true ;; esac` |

**Test command:** `bash scripts/install-langchain-cli-tools.sh` (exits 0, no `bun upgrade` when mise-managed)

### 3.4 `scripts/verify-tooling.sh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 32-39 | Replace `setup-skypilot-aws.sh` call with read-only check | `setup-skypilot-aws.sh` writes credentials, restarts services -- violates read-only verification (R5 finding 4) | `"$SCRIPT_DIR/setup-skypilot-aws.sh"` | `"$SCRIPT_DIR/verify-skypilot-aws.sh"` (new script, see section 3.10) |

**Test command:** `bash scripts/verify-tooling.sh` (exits 0, performs no writes)

### 3.5 `scripts/sky-status.sh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 60-71 | Gate `kill_stale_api_server` behind flag | A verification/status script should not kill processes (R5 finding 5) | `kill_stale_api_server` runs unconditionally at top of script | Add `MDE_SKY_KILL_STALE="${MDE_SKY_KILL_STALE:-0}"` at top; wrap body of `kill_stale_api_server()` in `[[ "$MDE_SKY_KILL_STALE" == "1" ]] \|\| return 0` |

**Test command:** `bash scripts/sky-status.sh --no-aws --strict` (no processes killed)

### 3.6 `templates/oh-my-zsh/macos-env.zsh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| 28 | Migrate env var name | Forward compatibility | `export UV_NO_MANAGED_PYTHON=1` | `export UV_PYTHON_DOWNLOADS=never` |
| 17-19 | Move bun completions to fpath | Sourcing 37KB completion file at every startup costs 5-15ms (R4 finding 9) | `source "$BUN_INSTALL/_bun"` | Remove the `source` block. Add comment: `# Bun completions: symlink ~/.bun/_bun to ~/.oh-my-zsh/custom/completions/_bun` |

**Test command:** Open new terminal; `type mde-status` resolves; `bun <tab>` shows completions

### 3.7 `templates/oh-my-zsh/aliases.zsh`

| Line(s) | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| EOF | Add 6 missing aliases | Required by consolidated spec section 7 (R4 finding 7) | File ends after openlit aliases | Append the 6 aliases defined in section 7 of this spec |

New aliases to append:

```zsh
# MDE lifecycle
alias mde-update="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
alias mde-update-fast="MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 $HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
alias mde-verify="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/verify-all.sh"
alias mde-drift="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-drift-check.sh"
alias mde-migrate="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-migrate-to-mise.sh"
alias mde-agents-review="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-agents-review.sh"
```

**Test command:** `source templates/oh-my-zsh/aliases.zsh && type mde-update` (resolves to maintenance script)

### 3.8 `docs/toolchain-precedence.md`

| Section | Change | Why | Before | After |
|---------|--------|-----|--------|-------|
| uv section | Document mise-managed guard | R2 finding 1: uv self-update fails when mise-managed | Only mentions Homebrew guard | Add: "When uv is mise-managed (`~/.local/share/mise/installs/uv/`), skip `uv self update` -- use `mise upgrade` instead." |
| bun section | Document mise-managed guard | R2 finding 5: bun upgrade causes drift | Not mentioned | Add: "When bun is mise-managed, skip `bun upgrade` -- use `mise upgrade` instead." |
| pixi section | Document pixi self-update guard | R2 finding 7: pixi self-update may be disabled | Not mentioned | Add: "pixi self-update may be disabled in externally-packaged builds. Guard with `2>/dev/null` fallback." |

**Test command:** `cat docs/toolchain-precedence.md | grep -c "mise-managed"` (returns >= 2)

### 3.9 New: `scripts/verify-skypilot-aws.sh`

A new read-only script that replaces the `setup-skypilot-aws.sh` call in `verify-tooling.sh`.

```bash
#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

status=0

# Check AWS credentials file exists
if [[ -f "$HOME/.aws/credentials" ]]; then
  log "AWS credentials file: present"
else
  log "AWS credentials file: MISSING"
  status=1
fi

# Check AWS config file exists
if [[ -f "$HOME/.aws/config" ]]; then
  log "AWS config file: present"
else
  log "AWS config file: MISSING"
  status=1
fi

# Check sky CLI present
if command -v sky >/dev/null 2>&1; then
  log "SkyPilot CLI: present ($(sky --version 2>/dev/null || echo unknown))"
  # sky check is read-only (validates credentials, does not write)
  if sky check aws 2>/dev/null; then
    log "SkyPilot AWS check: passed"
  else
    log "SkyPilot AWS check: failed"
    status=1
  fi
else
  log "SkyPilot CLI: not found"
  status=1
fi

exit "$status"
```

**Test command:** `bash scripts/verify-skypilot-aws.sh` (exits 0, no files written)

### 3.10 New: `scripts/mde-drift-check.sh`

Detects policy violations: brew-owned runtimes, duplicate tool ownership, PATH ordering.

```bash
#!/usr/bin/env bash
set -euo pipefail

MDE_DRIFT_ENFORCE="${MDE_DRIFT_ENFORCE:-0}"
BREW="$(command -v brew 2>/dev/null || echo "")"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

warnings=0
errors=0

# Check: brew should not own runtimes
check_brew_runtimes() {
  if [[ -z "$BREW" ]]; then
    return 0
  fi
  local formula
  for formula in node go rust python; do
    if "$BREW" list --formula "$formula" >/dev/null 2>&1; then
      log "DRIFT: brew owns runtime '$formula' (should be mise-managed)"
      warnings=$((warnings + 1))
    fi
  done
  # Check python@* variants
  while IFS= read -r formula; do
    [[ -z "$formula" ]] && continue
    log "DRIFT: brew owns runtime '$formula' (should be mise-managed)"
    warnings=$((warnings + 1))
  done < <("$BREW" list --formula 2>/dev/null | grep -E '^python@' || true)
}

# Check: mise should manage core runtimes
check_mise_runtimes() {
  if ! command -v mise >/dev/null 2>&1; then
    log "DRIFT: mise not found on PATH"
    errors=$((errors + 1))
    return 1
  fi
  local tool
  for tool in python node bun go rust; do
    if ! mise ls "$tool" 2>/dev/null | grep -q "$tool"; then
      log "DRIFT: mise does not manage '$tool'"
      warnings=$((warnings + 1))
    fi
  done
}

# Check: PATH ordering (mise shims should be first)
check_path_ordering() {
  local first_path_entry
  first_path_entry="$(echo "$PATH" | cut -d: -f1)"
  if [[ "$first_path_entry" != "$HOME/.local/share/mise/shims" ]]; then
    log "DRIFT: mise shims not first in PATH (first entry: $first_path_entry)"
    warnings=$((warnings + 1))
  fi
}

# Check: no conflicting runtime managers
check_conflicting_managers() {
  local mgr dir
  for mgr in nvm volta asdf pyenv; do
    dir="$HOME/.$mgr"
    if [[ -d "$dir" ]]; then
      log "DRIFT: conflicting manager directory found: $dir"
      warnings=$((warnings + 1))
    fi
  done
}

# Check: duplicate binaries
check_duplicate_ownership() {
  local cmd paths
  for cmd in python node bun go rustc uv pixi; do
    paths="$(which -a "$cmd" 2>/dev/null | grep -v '/shims/' | wc -l | tr -d ' ')"
    if [[ "$paths" -gt 1 ]]; then
      log "DRIFT: '$cmd' found at multiple non-shim locations:"
      which -a "$cmd" 2>/dev/null | grep -v '/shims/' | while read -r p; do
        log "  $p"
      done
      warnings=$((warnings + 1))
    fi
  done
}

log "Running drift check..."
check_brew_runtimes
check_mise_runtimes
check_path_ordering
check_conflicting_managers
check_duplicate_ownership

if [[ "$errors" -gt 0 ]]; then
  log "Drift check: $errors errors, $warnings warnings -- FAILED"
  exit 1
fi

if [[ "$warnings" -gt 0 ]]; then
  log "Drift check: $warnings warnings found"
  if [[ "$MDE_DRIFT_ENFORCE" == "1" ]]; then
    log "Enforcement mode: exiting non-zero on warnings"
    exit 1
  fi
  exit 0
fi

log "Drift check: clean (no policy violations)"
exit 0
```

**Test command:** `bash scripts/mde-drift-check.sh` (exits 0 if clean, lists violations otherwise)

### 3.11 New: `scripts/mde-migrate-to-mise.sh`

Dry-run/apply migration helper for moving tools from brew to mise.

```bash
#!/usr/bin/env bash
set -euo pipefail

DRY_RUN="${MDE_MIGRATE_DRY_RUN:-1}"
BREW="$(command -v brew 2>/dev/null || echo "")"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

migrate_runtime() {
  local formula="$1"
  local mise_tool="$2"

  if [[ -z "$BREW" ]]; then
    return 0
  fi

  if ! "$BREW" list --formula "$formula" >/dev/null 2>&1; then
    log "SKIP: brew '$formula' not installed"
    return 0
  fi

  if ! command -v mise >/dev/null 2>&1; then
    log "ERROR: mise not found; cannot migrate"
    return 1
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    log "DRY-RUN: would uninstall brew '$formula' and ensure mise '$mise_tool'"
    return 0
  fi

  log "Ensuring mise manages $mise_tool..."
  mise use -g --yes "${mise_tool}@latest" || return 1
  mise reshim || true

  log "Removing brew formula: $formula"
  "$BREW" uninstall "$formula" || return 1
  log "Migrated $formula from brew to mise"
}

log "Migration mode: $([ "$DRY_RUN" == "1" ] && echo "DRY RUN" || echo "APPLY")"

migrate_runtime "node" "node"
migrate_runtime "go" "go"
migrate_runtime "rust" "rust"
# python guarded: llvm may depend on it
if [[ -n "$BREW" ]] && "$BREW" list --formula llvm >/dev/null 2>&1; then
  log "SKIP: python migration blocked (llvm depends on brew python)"
else
  migrate_runtime "python" "python"
fi

log "Migration complete."
if [[ "$DRY_RUN" == "1" ]]; then
  log "To apply: MDE_MIGRATE_DRY_RUN=0 bash scripts/mde-migrate-to-mise.sh"
fi
```

**Test command:** `bash scripts/mde-migrate-to-mise.sh` (dry-run by default, shows what would change)

### 3.12 New: `scripts/mde-agents-review.sh`

Stub script for orchestrating document review agent teams.

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if [[ -x "$REPO_ROOT/scripts/run-multi-agent" ]]; then
  exec "$REPO_ROOT/scripts/run-multi-agent" "$@"
fi

log "Agent review orchestrator not found at scripts/run-multi-agent"
log "Usage: mde-agents-review [review-target]"
exit 1
```

**Test command:** `bash scripts/mde-agents-review.sh --help` (shows usage or delegates to run-multi-agent)

---

## 4. Safe Update Sequence with Guard Conditions

### 4.1 Universal Self-Update Guard Pattern

Every tool's self-update must be guarded against the case where the tool is managed by an external package manager.

#### uv self-update guard (use in all scripts)

```bash
update_uv_binary() {
  if ! command -v uv >/dev/null 2>&1; then
    return 0
  fi
  local uv_path
  uv_path="$(command -v uv)"
  case "$uv_path" in
    "$HOME/.local/share/mise/installs/"*|"$HOME/.local/share/mise/shims/"*)
      log "uv is mise-managed; skipping uv self update (use mise upgrade)."
      ;;
    /opt/homebrew/*|/usr/local/*)
      log "uv is Homebrew-managed; skipping uv self update (use brew upgrade uv)."
      ;;
    "$HOME/.local/bin/uv"|"$HOME/.cargo/bin/uv")
      uv self update || return 1
      ;;
    *)
      uv self update || true
      ;;
  esac
}
```

#### bun upgrade guard (use in all scripts)

```bash
upgrade_bun_binary() {
  if ! command -v bun >/dev/null 2>&1; then
    return 0
  fi
  local bun_path
  bun_path="$(command -v bun)"
  case "$bun_path" in
    "$HOME/.local/share/mise/installs/bun/"*)
      log "bun is mise-managed; skipping bun upgrade (use mise upgrade)."
      ;;
    *)
      bun upgrade || return 1
      ;;
  esac
}
```

#### pixi self-update guard (use in all scripts)

```bash
update_pixi_binary() {
  if ! command -v pixi >/dev/null 2>&1; then
    return 0
  fi
  if ! pixi self-update 2>/dev/null; then
    log "pixi self-update unavailable (likely externally managed); skipping."
  fi
}
```

#### mise self-update guard (non-interactive)

```bash
update_mise_binary() {
  if ! command -v mise >/dev/null 2>&1; then
    return 0
  fi
  mise self-update --yes || return 1
  mise upgrade --yes || return 1
  mise reshim || true
}
```

### 4.2 Maintenance Execution Order

The `main()` function in `macos-dev-maintenance.sh` should execute in this sequence:

1. Acquire lock (`mkdir $LOCK_DIR`)
2. `setup_path` -- establish PATH for non-interactive context
3. `load_env_file_secrets` -- load from `secrets.env`
4. `load_1password_secrets` -- load from 1Password (partial failure OK)
5. `load_keychain_secrets` -- load from Keychain
6. `update_brew` -- Homebrew formulae and casks
7. `update_mise` -- mise self-update + upgrade (with `--yes`)
8. `update_bun` -- bun upgrade (with mise guard)
9. `cleanup_claude_cli` -- remove duplicate bun claude binary
10. `cleanup_gemini_cli` -- remove duplicate bun gemini binary (ONCE, not twice)
11. `update_uv` -- uv self-update (with mise/brew guard) + `uv tool upgrade --all`
12. `prune_uv_cache` -- optional cache pruning
13. `update_pixi` -- pixi self-update (with guard) + `pixi global update`
14. `update_agent_tools` -- agent stack + langchain CLI tools (gated by `MDE_UPDATE_AGENT_TOOLS`)
15. `update_mcp_servers` -- MCP server sync (gated by `MDE_UPDATE_MCP`)
16. `update_oh_my_zsh` -- oh-my-zsh pull (gated by `MDE_UPDATE_OMZ`)
17. Autofix phase (gated by `MDE_AUTOFIX`): ensure mise global, remove conflicting managers, sync configs
18. Strict phase (gated by `MDE_AUTOFIX_STRICT`): remove brew runtimes

---

## 5. Read-Only Verification Pattern with JSON Output

### 5.1 JSON Output Functions

These functions produce the required JSON verification schema with zero external dependencies (no `jq` needed).

```bash
#!/usr/bin/env bash
# Source this in any verify-*.sh script

_json_esc() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

declare -a _MDE_CHECKS=()

mde_add_check() {
  local name="$1" status="$2" severity="$3" details="$4"
  _MDE_CHECKS+=("$(printf '{"name":"%s","status":"%s","severity":"%s","details":"%s"}' \
    "$(_json_esc "$name")" "$status" "$severity" "$(_json_esc "$details")")")
}

mde_emit_json() {
  local overall="pass"
  local c
  for c in "${_MDE_CHECKS[@]}"; do
    if [[ "$c" == *'"status":"fail"'*'"severity":"hard"'* ]]; then
      overall="fail"
      break
    elif [[ "$c" == *'"status":"fail"'* || "$c" == *'"status":"warn"'* ]]; then
      overall="warn"
    fi
  done

  printf '{"timestamp":"%s","overall":"%s","checks":[%s]}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "$overall" \
    "$(IFS=,; printf '%s' "${_MDE_CHECKS[*]}")"
}
```

### 5.2 Usage in verify-all.sh

Add `--json` flag support to `scripts/verify-all.sh`:

```bash
JSON_MODE=0
for arg in "$@"; do
  [[ "$arg" == "--json" ]] && JSON_MODE=1
done

if [[ "$JSON_MODE" == "1" ]]; then
  source "$SCRIPT_DIR/lib/mde-json.sh"  # the functions from 5.1
  # Run each verification and capture results via mde_add_check
  # ...
  mde_emit_json
  exit 0
fi
```

### 5.3 JSON Schema (for reference)

```json
{
  "timestamp": "2026-02-28T16:00:00Z",
  "overall": "pass|fail|warn",
  "checks": [
    {
      "name": "mise",
      "status": "pass|fail|warn|skip",
      "severity": "hard|soft",
      "details": "mise 2026.2.23 installed via core backend"
    }
  ]
}
```

---

## 6. Optional Component Gate Pattern

### 6.1 Environment Variable Gating

Every optional component uses an env var defaulting to `1` (enabled). Setting to `0` disables the component without failing the overall verification.

```bash
# At top of verify script or maintenance script:
MDE_VERIFY_SKYPILOT="${MDE_VERIFY_SKYPILOT:-1}"
MDE_VERIFY_OPENLIT="${MDE_VERIFY_OPENLIT:-1}"
MDE_VERIFY_LANGCHAIN="${MDE_VERIFY_LANGCHAIN:-1}"
MDE_VERIFY_AWS_K8S="${MDE_VERIFY_AWS_K8S:-1}"
```

### 6.2 Soft vs Hard Failure Semantics

```bash
run_optional_check() {
  local name="$1"
  local gate_var="$2"
  local script="$3"

  local gate_val="${!gate_var:-1}"
  if [[ "$gate_val" != "1" ]]; then
    log "SKIP: $name (disabled via $gate_var=0)"
    [[ "$JSON_MODE" == "1" ]] && mde_add_check "$name" "skip" "soft" "disabled via $gate_var"
    return 0
  fi

  if [[ ! -x "$script" ]]; then
    log "SKIP: $name (script not found: $script)"
    [[ "$JSON_MODE" == "1" ]] && mde_add_check "$name" "skip" "soft" "script not found"
    return 0
  fi

  if "$script"; then
    [[ "$JSON_MODE" == "1" ]] && mde_add_check "$name" "pass" "soft" "check passed"
    return 0
  else
    log "WARN: $name check failed (soft failure)"
    [[ "$JSON_MODE" == "1" ]] && mde_add_check "$name" "warn" "soft" "check failed"
    return 0  # soft failure: does not fail overall
  fi
}
```

### 6.3 Strict Mode Override

When `MDE_VERIFY_STRICT_OPTIONAL=1`, optional component failures become hard failures:

```bash
MDE_VERIFY_STRICT_OPTIONAL="${MDE_VERIFY_STRICT_OPTIONAL:-0}"

run_optional_check_strict() {
  local name="$1" gate_var="$2" script="$3"

  run_optional_check "$name" "$gate_var" "$script"
  local result=$?

  if [[ "$MDE_VERIFY_STRICT_OPTIONAL" == "1" && "$result" -ne 0 ]]; then
    return 1  # promote to hard failure
  fi
  return "$result"
}
```

---

## 7. Alias Contract Additions

### 7.1 Exact zsh Syntax

Add to `templates/oh-my-zsh/aliases.zsh` after the existing openlit aliases:

```zsh
# MDE lifecycle
alias mde-update="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
alias mde-update-fast="MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 $HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
alias mde-verify="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/verify-all.sh"
alias mde-drift="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-drift-check.sh"
alias mde-migrate="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-migrate-to-mise.sh"
alias mde-agents-review="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-agents-review.sh"
```

### 7.2 Complete Alias Contract (all aliases)

| Alias | Target | Category | New? |
|-------|--------|----------|------|
| `mde-status` | `scripts/status-dashboard.sh` | Read-only status | Existing |
| `mde-secrets-check` | `scripts/secrets-smoke-test.sh` | Read-only check | Existing |
| `mde-mcp-sync` | `scripts/setup-mcp-servers.sh` | Mutating | Existing |
| `mde-update` | `scripts/macos-dev-maintenance.sh` | Mutating | NEW |
| `mde-update-fast` | `MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 scripts/macos-dev-maintenance.sh` | Mutating (subset) | NEW |
| `mde-verify` | `scripts/verify-all.sh` | Read-only | NEW |
| `mde-drift` | `scripts/mde-drift-check.sh` | Read-only | NEW |
| `mde-migrate` | `scripts/mde-migrate-to-mise.sh` | Mutating (dry-run default) | NEW |
| `mde-agents-review` | `scripts/mde-agents-review.sh` | Orchestration | NEW |

---

## 8. launchd Compatibility Notes

### 8.1 Non-Interactive Constraints

launchd jobs:
- Do NOT source any shell profile (`~/.zprofile`, `~/.zshrc`, `~/.bashrc`)
- Must set PATH explicitly via `EnvironmentVariables` in plist or `setup_path()` in script
- Cannot display interactive prompts (all CLI flags must include `--yes`, `--non-interactive`, etc.)
- stdout/stderr go to files specified by `StandardOutPath`/`StandardErrorPath`

### 8.2 PATH Propagation

launchd passes `EnvironmentVariables` to the direct child process only. The maintenance wrapper script must call `setup_path()` to set the full PATH including mise shims, local bin, bun, pixi, brew paths.

Recommended minimal PATH in plist `EnvironmentVariables` (safety net):

```xml
<key>PATH</key>
<string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
```

The script's `setup_path()` overrides this with the full PATH.

### 8.3 Deprecated launchctl Commands

| Deprecated | Replacement |
|-----------|-------------|
| `launchctl load <plist>` | `launchctl bootstrap gui/$UID <plist>` |
| `launchctl unload <plist>` | `launchctl bootout gui/$UID/<label>` |

The `scripts/install-validation-launchd.sh` currently uses `launchctl load/unload`. Migration pattern:

```bash
# Before:
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

# After:
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST"
```

### 8.4 StartInterval vs KeepAlive

- Use `StartInterval` for periodic tasks (e.g., 43200 seconds = 12 hours)
- Use `RunAtLoad` to also run on first load
- Do NOT use `KeepAlive` with `StartInterval` -- `KeepAlive` overrides interval scheduling and restarts the process immediately on exit

### 8.5 mise in launchd Context

`eval "$(mise activate bash)"` requires an interactive shell. For launchd wrapper scripts, use the shim PATH approach instead:

```bash
setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:..."
}
```

This gives access to all mise-managed tools without needing `mise activate`.

---

## 9. Phased Implementation Plan

### Phase 1: Policy Foundation (Low Risk)

**Changes:**
1. Add `--yes` flag to `mise self-update` in `macos-dev-maintenance.sh:342`
2. Add mise-managed path guard to `update_uv()` in `macos-dev-maintenance.sh:391-397`
3. Add pixi self-update guard in `macos-dev-maintenance.sh:419`
4. Fix duplicate `cleanup_gemini_cli` call in `macos-dev-maintenance.sh:496-497`
5. Add `rust@latest` to `mise use -g` in `install-agent-stack.sh:63`
6. Add mise-managed guard to `ensure_bun()` in `install-langchain-cli-tools.sh:51-65`
7. Add mise-managed guard to `ensure_uv()` in `install-agent-stack.sh:67-77`

**Files:** `scripts/macos-dev-maintenance.sh`, `scripts/install-agent-stack.sh`, `scripts/install-langchain-cli-tools.sh`

**Acceptance Criteria:**
- `bash scripts/macos-dev-maintenance.sh` exits 0 with no interactive prompts
- No `uv self update` warning when uv is mise-managed
- No `bun upgrade` when bun is mise-managed
- `cleanup_gemini_cli` called exactly once per run

**Test Commands:**
```bash
bash scripts/macos-dev-maintenance.sh
echo $?  # expect 0
```

### Phase 2: Verification Hardening (Low Risk)

**Changes:**
1. Create `scripts/verify-skypilot-aws.sh` (new, read-only)
2. Update `scripts/verify-tooling.sh:32-39` to call `verify-skypilot-aws.sh` instead of `setup-skypilot-aws.sh`
3. Gate `kill_stale_api_server` in `scripts/sky-status.sh` behind `MDE_SKY_KILL_STALE` flag
4. Create `scripts/lib/mde-json.sh` with JSON output functions
5. Add `--json` support to `scripts/verify-all.sh`

**Files:** `scripts/verify-tooling.sh`, `scripts/sky-status.sh`, `scripts/verify-skypilot-aws.sh` (new), `scripts/lib/mde-json.sh` (new), `scripts/verify-all.sh`

**Acceptance Criteria:**
- `bash scripts/verify-tooling.sh` performs zero file writes and kills no processes
- `bash scripts/verify-all.sh --json` produces valid JSON matching the schema
- `bash scripts/sky-status.sh --no-aws --strict` does not kill processes

**Test Commands:**
```bash
bash scripts/verify-tooling.sh
echo $?  # expect 0

bash scripts/verify-all.sh --json | python3 -m json.tool
# expect valid JSON with "overall", "timestamp", "checks" keys

MDE_SKY_KILL_STALE=0 bash scripts/sky-status.sh --no-aws --strict
```

### Phase 3: Drift Detection and Migration (Medium Risk)

**Changes:**
1. Create `scripts/mde-drift-check.sh` (new)
2. Create `scripts/mde-migrate-to-mise.sh` (new, dry-run default)
3. Create `scripts/mde-agents-review.sh` (new, stub)
4. Migrate `UV_NO_MANAGED_PYTHON` to `UV_PYTHON_DOWNLOADS=never` in all 3 scripts + macos-env.zsh
5. Add 6 missing aliases to `templates/oh-my-zsh/aliases.zsh`
6. Update `docs/toolchain-precedence.md` with mise-managed guards

**Files:** `scripts/mde-drift-check.sh` (new), `scripts/mde-migrate-to-mise.sh` (new), `scripts/mde-agents-review.sh` (new), `templates/oh-my-zsh/aliases.zsh`, `templates/oh-my-zsh/macos-env.zsh`, `scripts/macos-dev-maintenance.sh`, `scripts/install-agent-stack.sh`, `scripts/install-langchain-cli-tools.sh`, `docs/toolchain-precedence.md`

**Acceptance Criteria:**
- `bash scripts/mde-drift-check.sh` exits 0 on a clean machine
- `bash scripts/mde-migrate-to-mise.sh` shows dry-run output without modifying anything
- All 6 new aliases resolve to executable scripts
- `UV_PYTHON_DOWNLOADS=never` present in all scripts; `UV_NO_MANAGED_PYTHON` removed

**Test Commands:**
```bash
bash scripts/mde-drift-check.sh
echo $?  # expect 0

bash scripts/mde-migrate-to-mise.sh
# expect "DRY RUN" output, no changes

source templates/oh-my-zsh/aliases.zsh
type mde-update mde-verify mde-drift  # all resolve

grep -r 'UV_NO_MANAGED_PYTHON' scripts/ templates/
# expect: no matches

grep -r 'UV_PYTHON_DOWNLOADS' scripts/ templates/
# expect: matches in all relevant files
```

### Phase 4: Shell Optimization (Low Risk)

**Changes:**
1. Move bun completions from `source` to fpath symlink in `macos-env.zsh`
2. Sync `setup_path()` in maintenance script with macos-env.zsh PATH list
3. Document the duplicate `mise activate zsh` issue in `~/.zshrc` line 89 (user must manually remove)

**Files:** `templates/oh-my-zsh/macos-env.zsh`, `scripts/macos-dev-maintenance.sh`

**Acceptance Criteria:**
- Opening a new terminal completes in <300ms (measure with `time zsh -i -c exit`)
- Bun tab completions still work
- All mise-managed tools accessible from PATH in both interactive shells and launchd scripts

**Test Commands:**
```bash
time zsh -i -c exit
# expect: real < 0.300s

# In new terminal:
bun <tab>  # should show completions
which python node bun go  # all resolve to mise shim or install paths
```

---

## 10. Test Matrix

Run these commands in order after completing all phases. Every command must produce the expected output.

| # | Command | Expected Output | Phase |
|---|---------|----------------|-------|
| 1 | `mise doctor --json 2>/dev/null \| head -1` | Valid JSON with no critical warnings | P1 |
| 2 | `mise ls python node bun go rust` | All 5 runtimes listed with versions | P1 |
| 3 | `bash scripts/macos-dev-maintenance.sh; echo $?` | `0` (no hangs, no interactive prompts) | P1 |
| 4 | `uv tool list \| head -5` | Lists installed Python CLI tools | P1 |
| 5 | `bun pm ls -g 2>/dev/null \| head -5` | Lists installed Node CLI tools | P1 |
| 6 | `bash scripts/verify-tooling.sh; echo $?` | `0` (no files written, no processes killed) | P2 |
| 7 | `bash scripts/verify-all.sh --json \| python3 -m json.tool > /dev/null; echo $?` | `0` (valid JSON) | P2 |
| 8 | `bash scripts/verify-skypilot-aws.sh; echo $?` | `0` (read-only check passes) | P2 |
| 9 | `bash scripts/mde-drift-check.sh; echo $?` | `0` (or warnings without enforce) | P3 |
| 10 | `MDE_MIGRATE_DRY_RUN=1 bash scripts/mde-migrate-to-mise.sh` | "DRY RUN" output, no mutations | P3 |
| 11 | `source templates/oh-my-zsh/aliases.zsh && type mde-update` | Resolves to maintenance script path | P3 |
| 12 | `source templates/oh-my-zsh/aliases.zsh && type mde-verify` | Resolves to verify-all.sh path | P3 |
| 13 | `source templates/oh-my-zsh/aliases.zsh && type mde-drift` | Resolves to mde-drift-check.sh path | P3 |
| 14 | `grep -c 'UV_PYTHON_DOWNLOADS' scripts/macos-dev-maintenance.sh` | `>= 1` | P3 |
| 15 | `grep -c 'UV_NO_MANAGED_PYTHON' scripts/macos-dev-maintenance.sh` | `0` | P3 |
| 16 | `time zsh -i -c exit 2>&1 \| grep real` | `< 0.300s` | P4 |
| 17 | `brew outdated --formula && brew outdated --cask` | Lists any outdated packages (informational) | P1 |
| 18 | `mise outdated \|\| true` | Lists any outdated mise tools (informational) | P1 |

---

## Appendix A: Environment Variables Reference

| Variable | Default | Purpose | Used By |
|----------|---------|---------|---------|
| `MDE_AUTOFIX` | `0` | Enable autofix phase in maintenance | `macos-dev-maintenance.sh` |
| `MDE_AUTOFIX_STRICT` | `0` | Enable strict brew runtime removal | `macos-dev-maintenance.sh` |
| `MDE_UPDATE_AGENT_TOOLS` | `1` | Enable agent tool updates | `macos-dev-maintenance.sh` |
| `MDE_UPDATE_MCP` | `1` | Enable MCP server sync | `macos-dev-maintenance.sh` |
| `MDE_UPDATE_OMZ` | `0` | Enable oh-my-zsh update | `macos-dev-maintenance.sh` |
| `MDE_UV_CACHE_PRUNE` | `0` | Enable uv cache pruning | `macos-dev-maintenance.sh` |
| `MDE_DRIFT_ENFORCE` | `0` | Fail on drift warnings | `mde-drift-check.sh` |
| `MDE_MIGRATE_DRY_RUN` | `1` | Dry-run mode for migration | `mde-migrate-to-mise.sh` |
| `MDE_SKY_KILL_STALE` | `0` | Allow killing stale SkyPilot API processes | `sky-status.sh` |
| `MDE_VERIFY_SKYPILOT` | `1` | Enable SkyPilot verification | `verify-tooling.sh` |
| `MDE_VERIFY_OPENLIT` | `1` | Enable OpenLIT verification | `verify-tooling.sh` |
| `MDE_VERIFY_LANGCHAIN` | `1` | Enable LangChain verification | `verify-tooling.sh` |
| `MDE_VERIFY_AWS_K8S` | `1` | Enable AWS/K8s verification | `verify-tooling.sh` |
| `MDE_VERIFY_STRICT_OPTIONAL` | `0` | Promote optional failures to hard failures | `verify-all.sh` |
| `MDE_ENV_FILE` | `~/.config/macos-development-environment/secrets.env` | Secret env file path | Multiple |
| `MDE_ENV_AUTOLOAD` | `1` | Auto-load env file | Multiple |
| `MDE_SECRET_OVERRIDE` | `1` | Allow secret sources to overwrite existing vars | Multiple |
| `MDE_AUTOLOAD_SECRETS` | `1` | Auto-load keychain secrets in shell startup | `macos-env.zsh` |
| `UV_PYTHON_DOWNLOADS` | `never` | Prevent uv from downloading Python | Multiple |
| `UV_CACHE_DIR` | `$HOME/Library/Caches/uv` | uv cache directory (macOS convention) | Multiple |
| `GOBIN` | `$HOME/.local/bin` | Go binary install directory | Multiple |
| `MDE_TOOL_OWNERSHIP_FILE` | `docs/toolchain-precedence.md` | Tool ownership documentation | `mde-drift-check.sh` |

## Appendix B: File Inventory

### Existing Files Modified

| File | Phase |
|------|-------|
| `scripts/macos-dev-maintenance.sh` | P1, P3, P4 |
| `scripts/install-agent-stack.sh` | P1, P3 |
| `scripts/install-langchain-cli-tools.sh` | P1, P3 |
| `scripts/verify-tooling.sh` | P2 |
| `scripts/sky-status.sh` | P2 |
| `scripts/verify-all.sh` | P2 |
| `templates/oh-my-zsh/aliases.zsh` | P3 |
| `templates/oh-my-zsh/macos-env.zsh` | P3, P4 |
| `docs/toolchain-precedence.md` | P3 |

### New Files Created

| File | Phase | Purpose |
|------|-------|---------|
| `scripts/verify-skypilot-aws.sh` | P2 | Read-only SkyPilot/AWS verification |
| `scripts/lib/mde-json.sh` | P2 | Shared JSON output functions |
| `scripts/mde-drift-check.sh` | P3 | Policy drift detection |
| `scripts/mde-migrate-to-mise.sh` | P3 | brew-to-mise migration helper |
| `scripts/mde-agents-review.sh` | P3 | Agent review orchestration stub |

## Appendix C: Known Bugs Fixed by This Spec

| Bug | Location | Finding Source | Fix |
|-----|----------|---------------|-----|
| `mise self-update` hangs in launchd | `macos-dev-maintenance.sh:342` | R1 finding 8, R1 finding 14 | Add `--yes` flag |
| `uv self update` fails when mise-managed | `macos-dev-maintenance.sh:394` | R2 finding 1 | Add mise path guard |
| `bun upgrade` causes version drift when mise-managed | `install-langchain-cli-tools.sh:53` | R2 finding 5 | Add mise path guard |
| Duplicate `cleanup_gemini_cli` call | `macos-dev-maintenance.sh:489,497` | R4 script audit | Remove duplicate |
| `verify-tooling.sh` calls mutating `setup-skypilot-aws.sh` | `verify-tooling.sh:32-39` | R5 finding 4 | Replace with read-only `verify-skypilot-aws.sh` |
| `sky-status.sh` kills processes unconditionally | `sky-status.sh:60-71` | R5 finding 5 | Gate behind `MDE_SKY_KILL_STALE` |
| `rust@latest` missing from `install-agent-stack.sh` | `install-agent-stack.sh:63` | R1 script audit | Add `rust@latest` to `mise use -g` |
| `UV_NO_MANAGED_PYTHON` is undocumented uv env var | Multiple scripts | R2 finding 4 | Migrate to `UV_PYTHON_DOWNLOADS=never` |
| `setup_path()` in maintenance script missing paths | `macos-dev-maintenance.sh:173` | R4 script audit | Sync with `macos-env.zsh` PATH list |
