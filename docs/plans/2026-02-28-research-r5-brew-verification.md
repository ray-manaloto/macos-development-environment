# Research Report R5: brew Boundary and Verification Architecture

## Sources Consulted

### Online Documentation
- [Homebrew Manpage (brew(1))](https://docs.brew.sh/Manpage) -- command reference for `list`, `outdated`, `info`, `bundle`
- [Homebrew Bundle and Brewfile](https://docs.brew.sh/Brew-Bundle-and-Brewfile) -- `brew bundle check`, `brew bundle list`
- [Homebrew FAQ](https://docs.brew.sh/FAQ)
- [Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae) -- formula vs cask boundary rules
- [Homebrew JSON API](https://formulae.brew.sh/docs/api/)
- [brew outdated output format issue #20976](https://github.com/Homebrew/brew/issues/20976)
- [brew bundle check verbose issue #401](https://github.com/Homebrew/homebrew-bundle/issues/401)
- [brew bundle check missing output issue #147](https://github.com/Homebrew/homebrew-bundle/issues/147)
- [brew install/upgrade idempotency issue #11393](https://github.com/Homebrew/brew/issues/11393)
- [Cask sudo permissions issue #62739](https://github.com/Homebrew/homebrew-cask/issues/62739)
- [osquery build deps permissions issue #3385](https://github.com/osquery/osquery/issues/3385)
- [json.bash -- shell-native JSON generation](https://github.com/h4l/json.bash)
- [Baeldung: JSON in Shell Scripts](https://www.baeldung.com/linux/json-shell-parse-validate-print)

### Local Files Read
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-tooling.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-agent-tools.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-langchain-tools.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-all.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/health-check.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/status-dashboard.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/sky-status.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/setup-skypilot-aws.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-openlit.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/tools-inventory.sh`

---

## Key Findings (Numbered)

### 1. `brew list --formula` vs `brew ls --versions`: Correct Idempotent Check

**`brew list --formula <name>`** is the correct idempotent check for "is this formula installed?"

- `brew list --formula <name>` exits 0 if installed, non-zero if not. Produces no output when redirected. This is exactly the pattern used by `brew_has()` in `macos-dev-maintenance.sh:194-197`.
- `brew ls --versions <name>` is an alias that prints `<name> <version>` if installed, empty/non-zero if not. Useful when you also need the version string.
- Both are read-only and idempotent. Neither triggers installs or network requests.
- **Recommendation**: Keep the existing `brew_has()` pattern (`brew list --formula "$1" >/dev/null 2>&1`). It is correct. For version-aware checks, use `brew ls --versions "$1"` and parse the output.

```bash
# Current pattern (correct):
brew_has() {
  [[ -n "$BREW" ]] || return 1
  "$BREW" list --formula "$1" >/dev/null 2>&1
}

# Version-aware variant:
brew_has_version() {
  local formula="$1"
  local required_version="$2"
  local installed
  installed="$("$BREW" ls --versions "$formula" 2>/dev/null)" || return 1
  [[ "$installed" == *"$required_version"* ]]
}
```

### 2. `brew bundle check`: Suitability for CI-Style Read-Only Verification

**Suitable, but with caveats.**

- `brew bundle check` verifies all Brewfile dependencies are satisfied. Exit code 0 = all satisfied, non-zero = something missing.
- It does NOT check for outdated packages -- only installation presence. This is a feature, not a bug, for verification purposes.
- With `--verbose`, it lists what is missing.
- **Critical caveat**: The project has **no Brewfile**. To use `brew bundle check`, a Brewfile must first be created.
- `brew bundle check` is strictly read-only. It does not install, upgrade, or modify anything.
- **Recommendation**: If the modernization adopts a Brewfile (recommended), `brew bundle check --verbose` is the ideal CI-style verification. The pattern `brew bundle check || brew bundle install` separates verification from mutation cleanly.

### 3. `brew outdated --formula`: JSON Flag and Machine-Readable Output

**Yes, `--json` flag exists with two versions.**

- `brew outdated --json=v2` produces JSON output for both formulae and casks. v1 is deprecated.
- Structure (v2):
  ```json
  {
    "formulae": [
      {
        "name": "git",
        "installed_versions": ["2.44.0"],
        "current_version": "2.45.0",
        "pinned": false,
        "pinned_version": null
      }
    ],
    "casks": [...]
  }
  ```
- `brew outdated --formula --json=v2` filters to formulae only.
- **Known issue (2025)**: `brew outdated` output format can vary between runs depending on whether brew auto-updates its JSON API cache. The `--json` flag produces consistent structured output regardless.
- **Recommendation**: Use `brew outdated --json=v2` for machine-readable verification. Parse with `jq` if available, or with the existing `json_escape` pattern in `status-dashboard.sh`.

### 4. `verify-tooling.sh` Calls `setup-skypilot-aws.sh` -- Mutation Separation

**This is a significant violation of the read-only verification principle.**

`verify-tooling.sh:32-39` executes `setup-skypilot-aws.sh` directly. Analysis of `setup-skypilot-aws.sh` reveals it performs these **mutating** operations:

| Line(s) | Mutation | Description |
|----------|----------|-------------|
| 73-86 | Writes `~/.aws/credentials` | Overwrites AWS credentials file from env vars |
| 87-97 | Writes `~/.aws/config` | Overwrites AWS config file |
| 100-101 | `chmod 600` | Changes file permissions |
| 183-184 | Runs `patch-skypilot.sh` | Patches SkyPilot installation |
| 187-191 | `sky api stop` / `sky api start` | Restarts the SkyPilot API server |
| 193-198 | `sky check aws` | Validates credentials (read-only, but preceded by mutations) |

**Recommendation**: `verify-tooling.sh` must NOT call `setup-skypilot-aws.sh`. Instead:
- Extract a new `verify-skypilot-aws.sh` that only does read-only checks (credential file exists, `sky check aws` without restart).
- Move `setup-skypilot-aws.sh` calls to the maintenance script only (where mutations are acceptable).

### 5. `sky-status.sh --no-aws --strict`: Read-Only Analysis

**Mostly read-only, but has one side effect.**

`sky-status.sh` with `--no-aws` skips all AWS API calls and cache writes. However:

| Line(s) | Operation | Side Effect? |
|----------|-----------|-------------|
| 60-71 | `kill_stale_api_server()` | **YES** -- kills processes on port 46580 |
| 77-113 | `load_env_file_secrets` | Exports env vars (process-local, not a file mutation) |
| 125-144 | `sky_status` | Read-only (`sky status` is a query) |

The `kill_stale_api_server()` function at line 60 calls `kill $pids` on any SkyPilot API server found listening on port 46580. This is a mutating side effect that runs unconditionally, before even checking `--no-aws`.

**Recommendation**: Gate `kill_stale_api_server` behind an explicit flag (e.g., `--kill-stale`) or move it to maintenance. A verification script should never kill processes.

### 6. Brew Formulae Audit: Runtimes vs OS Tools

Audit of `macos-dev-maintenance.sh` and cross-referencing with `status-dashboard.sh` inventory functions:

**Runtimes (should be managed by mise, NOT brew):**

| Formula | Current Handler | Where Referenced | Notes |
|---------|----------------|------------------|-------|
| `node` | `remove_brew_runtimes()` | maintenance.sh:254 | Correctly targeted for removal |
| `go` | `remove_brew_runtimes()` | maintenance.sh:254 | Correctly targeted for removal |
| `rust` | `remove_brew_runtimes()` | maintenance.sh:254 | Correctly targeted for removal |
| `python` / `python@*` | `remove_brew_runtimes()` | maintenance.sh:267-273 | Conditionally kept if llvm depends on it |

**OS/System Tools (should stay in brew):**

| Formula | Category | Notes |
|---------|----------|-------|
| `gnupg` | Crypto/signing | Installed by `ensure_gpg()` in maintenance.sh:323-333 |
| `curl` | Network | Referenced in PATH at `/opt/homebrew/opt/curl/bin` |
| `llvm` | Compiler toolchain | Noted as dependency blocker for python removal |
| `ripgrep` (`rg`) | Search | health-check.sh marks it as required |

**Observation**: The codebase does not maintain an explicit list of "brew-owned OS tools." The `remove_brew_runtimes()` function knows what to remove, but there is no corresponding "expected brew formulae" list for validation. A Brewfile would solve this.

### 7. Idempotent Pattern for Verifying Tool Presence AND Version

The recommended pattern combines `command -v` (presence) with version parsing (correctness):

```bash
# Pattern: Verify tool present AND version-correct, no installs
verify_tool() {
  local name="$1"
  local min_version="$2"  # optional

  # Step 1: Presence check
  if ! command -v "$name" >/dev/null 2>&1; then
    return 1  # not present
  fi

  # Step 2: Version check (optional)
  if [[ -z "$min_version" ]]; then
    return 0  # present, no version constraint
  fi

  local current
  current="$("$name" --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')" || return 2

  # Compare versions (simple numeric comparison)
  printf '%s\n%s' "$min_version" "$current" | sort -V | head -1 | grep -qx "$min_version"
}
```

For brew-specific tools, combine with `brew_has`:

```bash
verify_brew_tool() {
  local formula="$1"
  local cmd="${2:-$1}"  # command name may differ from formula name

  brew_has "$formula" && command -v "$cmd" >/dev/null 2>&1
}
```

### 8. Minimal Bash JSON Output (Shellcheck-Compatible)

Implementation for the requested schema, using only POSIX-compatible constructs and passing shellcheck:

```bash
#!/usr/bin/env bash
# shellcheck-compatible JSON output for verification results

json_escape_value() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

# Usage: json_check "name" "pass|fail|warn|skip" "hard|soft" "details string"
json_check() {
  printf '{"name":"%s","status":"%s","severity":"%s","details":"%s"}' \
    "$(json_escape_value "$1")" "$2" "$3" "$(json_escape_value "$4")"
}

# Accumulate checks in an array
declare -a CHECKS=()

add_check() {
  CHECKS+=("$(json_check "$@")")
}

emit_json() {
  local overall="$1"
  local timestamp
  timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

  printf '{"timestamp":"%s","overall":"%s","checks":[' "$timestamp" "$overall"
  local i
  for i in "${!CHECKS[@]}"; do
    if [[ "$i" -gt 0 ]]; then
      printf ','
    fi
    printf '%s' "${CHECKS[$i]}"
  done
  printf ']}\n'
}

# Example usage:
# add_check "mise" "pass" "hard" "mise 2025.2.1 installed"
# add_check "node" "fail" "soft" "node not found in PATH"
# emit_json "fail"
```

**Shellcheck notes**:
- Avoids `echo` for JSON (uses `printf`).
- Uses `${s//pattern/replacement}` which is bash-specific but shellcheck-clean.
- No subshell for the array accumulation.
- The `status-dashboard.sh` already has a working `json_escape()` function (line 28-30) using `sed`, which is also valid but spawns a subprocess per call.
- **Recommendation**: Adopt the `printf`-based pattern above for new verification scripts. It avoids `sed` subprocesses and is faster in loops.

### 9. osquery Cask Upgrade Behavior

**Why osquery is skipped in cask upgrades** (`macos-dev-maintenance.sh:313`):

```bash
[[ "$cask" == "osquery" ]] && continue
```

osquery is distributed as a `.pkg` installer cask. This creates two problems:

1. **sudo requirement**: Homebrew casks that use `.pkg` installers unconditionally require `sudo` for installation and upgrade. The `brew upgrade --cask` command will prompt for a password interactively, which breaks unattended/launchd execution.

2. **System-level installation**: osquery installs a system daemon (`osqueryd`) into `/usr/local/bin/osqueryd` and a LaunchDaemon plist. Upgrading it mid-operation could disrupt monitoring.

3. **Known Homebrew limitation**: Per [homebrew-cask issue #62739](https://github.com/Homebrew/homebrew-cask/issues/62739), there is no way to selectively grant sudo for specific casks in an unattended `brew upgrade --cask` run. The workaround is to exclude such casks and handle them separately with explicit `sudo brew upgrade --cask osquery`.

**Recommendation**: Document the exclusion explicitly. Consider a separate `upgrade-sudo-casks.sh` script that runs interactively (not from launchd).

### 10. `brew list --cask` vs `brew outdated --cask` Behavior Differences

| Aspect | `brew list --cask` | `brew outdated --cask` |
|--------|--------------------|------------------------|
| Purpose | Lists all installed casks | Lists casks with newer versions available |
| Output | Cask names, one per line | Cask names with version info |
| Network | No (reads local cellar) | Yes (checks formulae.brew.sh API) |
| `--json` | Not supported for listing | Supported (`--json=v2`) |
| Auto-update casks | N/A (shows all) | Excluded by default; include with `--greedy` |
| `version :latest` casks | Listed | Excluded by default; include with `--greedy-latest` |
| Exit code | 0 if any installed, non-zero if empty | 0 always (even if nothing outdated) |
| Speed | Fast (local) | Slow (network, API cache) |

**Key behavioral note**: `brew outdated --cask` by default does NOT show casks that have `auto_updates true` in their definition (e.g., Chrome, Firefox, VS Code). Use `--greedy-auto-updates` to include them. This means a naive `brew outdated --cask` check will undercount outdated casks.

---

## Current Script Audit

| Script | Function/Section | Finding | Action Needed |
|--------|-----------------|---------|---------------|
| `macos-dev-maintenance.sh` | `brew_has()` (L194-197) | Correct idempotent pattern: `brew list --formula "$1" >/dev/null 2>&1` | None -- keep as-is |
| `macos-dev-maintenance.sh` | `update_brew()` (L295-321) | Mutating: runs `brew update`, `brew upgrade --formula`, `brew upgrade --cask`. Correctly excludes osquery. | None -- mutation is expected in maintenance |
| `macos-dev-maintenance.sh` | `remove_brew_runtimes()` (L250-275) | Mutating: uninstalls node, go, rust, python from brew. Guarded by `MDE_AUTOFIX_STRICT`. | None -- correct placement in maintenance |
| `macos-dev-maintenance.sh` | `remove_conflicting_managers()` (L238-248) | Mutating: uninstalls nvm, volta, asdf, pyenv. Guarded by `MDE_AUTOFIX`. | None -- correct placement in maintenance |
| `verify-tooling.sh` | L32-39 | **VIOLATION**: Calls `setup-skypilot-aws.sh` which writes credentials, restarts API server, patches SkyPilot | Extract read-only `verify-skypilot-aws.sh`; remove `setup-skypilot-aws.sh` call |
| `verify-tooling.sh` | L42-50 | Calls `sky-status.sh --no-aws --strict` which kills stale processes | Gate `kill_stale_api_server` behind flag |
| `verify-all.sh` | L21-29 | Calls `health-check.sh` -- read-only, correct | None |
| `verify-all.sh` | L41-48 | Calls `verify-tooling.sh` -- inherits the mutation problem above | Fix upstream (`verify-tooling.sh`) |
| `verify-all.sh` | L51-58 | Calls `status-dashboard.sh --json` -- read-only | None |
| `verify-agent-tools.sh` | entire file | Pure read-only: `command -v` checks + `uv tool list` | None -- exemplary pattern |
| `verify-langchain-tools.sh` | `smoke_command()` | Runs tools with `--help` arg and timeout. Read-only. | None -- good pattern |
| `verify-langchain-tools.sh` | `langsmith_api_ping()` (L175-243) | Network call to LangSmith API. Read-only (GET request). | None |
| `health-check.sh` | `check_cmd()`, `check_file()`, `check_secret()` | All read-only: `command -v`, `test -f`, `security find-generic-password` | None -- exemplary pattern |
| `health-check.sh` | `check_log_health()` (L182-209) | Reads log files, greps for error patterns. Read-only. | None |
| `status-dashboard.sh` | `output_json()` (L333-401) | Produces structured JSON. Read-only. | Good reference for JSON output pattern |
| `status-dashboard.sh` | `inventory_brew_formula()` (L87-93) | Calls `brew list --formula`. Read-only. | None |
| `sky-status.sh` | `kill_stale_api_server()` (L60-71) | **SIDE EFFECT**: Kills processes on port 46580. Runs unconditionally. | Gate behind `--kill-stale` or move to maintenance |
| `sky-status.sh` | `aws_summary()` (L146-240) | Creates cache files in `~/Library/Caches/`. Minor side effect (cache write). | Acceptable for a status script |
| `setup-skypilot-aws.sh` | `ensure_aws_credentials()` (L59-103) | **MUTATING**: Writes `~/.aws/credentials` and `~/.aws/config` | Must never be called from verify scripts |
| `setup-skypilot-aws.sh` | L183-198 | **MUTATING**: Patches SkyPilot, restarts API server, runs `sky check aws` | Must never be called from verify scripts |
| `tools-inventory.sh` | entire file | Read-only: `mise ls`, `uv tool list`, `brew list --formula`, etc. | None -- exemplary |
| `verify-openlit.sh` | entire file | Read-only: env var check + optional `curl` reachability test | None -- exemplary |

---

## Recommended Patterns

### Pattern 1: Brewfile as Canonical Brew Boundary

Create a `Brewfile` at the repo root that explicitly declares what brew owns:

```ruby
# Brewfile -- canonical list of brew-managed packages
# Runtimes (node, python, go, rust) are NOT here -- managed by mise

# System tools (formula)
brew "gnupg"
brew "curl"
brew "ripgrep"
brew "tmux"
brew "git"

# Compiler toolchain
brew "llvm"

# Casks (GUI applications)
cask "osquery"
# ... other casks
```

Verification becomes: `brew bundle check --verbose --file=Brewfile`

### Pattern 2: Read-Only Verification with JSON Output

```bash
#!/usr/bin/env bash
set -euo pipefail

# Pattern: verification script that produces JSON, has zero side effects

declare -a CHECKS=()

json_esc() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  printf '%s' "$s"
}

add_check() {
  local name="$1" status="$2" severity="$3" details="$4"
  CHECKS+=("$(printf '{"name":"%s","status":"%s","severity":"%s","details":"%s"}' \
    "$(json_esc "$name")" "$status" "$severity" "$(json_esc "$details")")")
}

emit_result() {
  local overall="pass"
  for c in "${CHECKS[@]}"; do
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
    "$(IFS=,; printf '%s' "${CHECKS[*]}")"
}

# ... verification logic using add_check ...
emit_result
```

### Pattern 3: Optional Component Gating

```bash
# Environment variable gating pattern (already used in the codebase)
MDE_VERIFY_SKYPILOT="${MDE_VERIFY_SKYPILOT:-1}"
MDE_VERIFY_OPENLIT="${MDE_VERIFY_OPENLIT:-1}"
MDE_VERIFY_LANGCHAIN="${MDE_VERIFY_LANGCHAIN:-1}"

if [[ "$MDE_VERIFY_SKYPILOT" == "1" ]]; then
  # ... skypilot checks ...
fi
```

This pattern is already partially used (e.g., `MDE_OPENLIT_REQUIRED`, `MDE_LANGCHAIN_SMOKE`). Standardize it across all optional components.

### Pattern 4: Separated Setup vs Verify

```
scripts/
  setup-skypilot-aws.sh    # MUTATING: writes credentials, restarts services
  verify-skypilot-aws.sh   # READ-ONLY: checks credentials exist, sky check passes

  macos-dev-maintenance.sh # MUTATING: runs updates, installs, removes
  verify-tooling.sh        # READ-ONLY: checks tools present and functional
  verify-all.sh            # READ-ONLY: orchestrates all verify-* scripts
  health-check.sh          # READ-ONLY: checks system health
```

---

## Implementation-Ready Decisions

### D1: Create a Brewfile

A `Brewfile` at the repo root should enumerate all brew-managed packages. This becomes the single source of truth for the brew boundary. `brew bundle check --verbose` replaces ad-hoc presence checks for brew-owned tools.

### D2: Extract `verify-skypilot-aws.sh` from `setup-skypilot-aws.sh`

The new script should only:
- Check that `~/.aws/credentials` exists and is non-empty
- Check that `AWS_ACCESS_KEY_ID` is set (env or file)
- Run `sky check aws` (read-only)
- NOT write credentials, restart services, or patch anything

### D3: Gate `kill_stale_api_server` in `sky-status.sh`

Change from unconditional execution to requiring `--kill-stale` flag. The verification path (`verify-tooling.sh` calling `sky-status.sh --no-aws --strict`) should not kill processes.

### D4: Standardize JSON Output for All Verification Scripts

All `verify-*.sh` scripts should support a `--json` flag that produces:
```json
{"timestamp":"...","overall":"pass|fail|warn","checks":[{"name":"...","status":"pass|fail|warn|skip","severity":"hard|soft","details":"..."}]}
```

This allows `verify-all.sh --json` to aggregate results programmatically.

### D5: Use `brew outdated --json=v2` for Staleness Checks

In `status-dashboard.sh`, replace human-readable `brew outdated` with `brew outdated --json=v2` for the JSON output mode. This gives structured data about what needs upgrading.

### D6: Document osquery Exclusion

Add a comment block in `macos-dev-maintenance.sh` explaining why osquery is excluded from `brew upgrade --cask`:
```bash
# osquery is excluded from unattended cask upgrades because:
# 1. Its .pkg installer unconditionally requires sudo (no workaround)
# 2. Upgrading the system daemon mid-operation can disrupt monitoring
# 3. Must be upgraded manually: sudo brew upgrade --cask osquery
```

### D7: No Brewfile Yet -- Use `brew_has()` Pattern Until Migration

If a Brewfile is not created in the near term, the existing `brew_has()` pattern remains the correct idempotent check. Do not switch to `brew bundle check` without first creating the Brewfile.

---

## Open Questions / Caveats

1. **llvm-python dependency**: `remove_brew_runtimes()` skips python removal if llvm is installed. Is llvm still required? If not, this guard can be removed, allowing full brew python cleanup.

2. **No Brewfile exists**: The project has no Brewfile. Creating one requires auditing all currently-installed brew formulae and casks to determine which are intentional vs. incidental dependencies. The `tools-inventory.sh` and `status-dashboard.sh --json` outputs can bootstrap this.

3. **`brew outdated` format instability**: GitHub issue #20976 reports that `brew outdated` output format varies between runs when brew auto-updates its API cache. The `--json=v2` flag appears to produce consistent output but should be tested.

4. **`brew bundle check` does not check versions**: It only checks presence. If the modernization requires version-pinning (e.g., gnupg >= 2.4), additional version-aware checks are needed beyond what `brew bundle check` provides.

5. **Cache writes in `sky-status.sh`**: The `aws_summary()` function writes cache files to `~/Library/Caches/`. This is a minor side effect. Decide whether this is acceptable in a "read-only" verification context or if the cache should be opt-in.

6. **`verify-langchain-tools.sh` uses `eval`**: Lines 100, 116, 284 use `eval "$failures_ref=1"` to set a variable by reference. This is a known shellcheck concern (SC2086). Consider using `declare -n` (bash 4.3+) or returning exit codes instead.

7. **Duplicate `load_env_file_secrets` function**: This function is copy-pasted across `sky-status.sh`, `verify-openlit.sh`, `setup-skypilot-aws.sh`, and `verify-langchain-tools.sh`. A shared library (`lib/mde-common.sh`) would reduce drift.

8. **`setup_path()` duplication**: The PATH setup function is duplicated verbatim in at least 8 scripts. Same recommendation: extract to shared library.

---

## Cross-References

- **R1 (mise-core)**: The brew boundary directly impacts mise scope. Runtimes removed from brew (node, go, rust, python) must have corresponding `mise use -g` entries. See `ensure_mise_global()` in `macos-dev-maintenance.sh:209-224`.
- **R2 (tool-interactions)**: The `remove_brew_runtimes()` function (maintenance.sh:250-275) is the mechanism that enforces the brew-to-mise migration for runtimes. Its guard (`MDE_AUTOFIX_STRICT=1`) should be documented in the interaction matrix.
- **R4 (shell-secrets)**: The `load_env_file_secrets()` duplication across scripts is a shared concern. The brew verification scripts load secrets for AWS/LangSmith validation, creating a coupling between verification and secret management.
- **Team C spec (brew-boundary)**: This research directly supports the `2026-02-28-team-c-brew-boundary-spec.md` deliverables. The Brewfile recommendation and verification JSON schema should feed into that spec.
- **Team E spec (maintenance-validation)**: The separation of mutating setup scripts from read-only verification scripts is a core requirement. The `verify-tooling.sh` mutation problem identified here must be resolved in the Team E implementation.
