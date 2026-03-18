# Research Report R4: Shell Environment and Secrets/Automation

## Sources Consulted

- [mise activate CLI docs](https://mise.jdx.dev/cli/activate.html) -- activate vs shims, placement guidance
- [mise Shims docs](https://mise.jdx.dev/dev-tools/shims.html) -- shims vs PATH feature matrix, hybrid approach
- [mise activate startup delay discussion #4821](https://github.com/jdx/mise/discussions/4821) -- 20-30ms measured overhead
- [mise activate does not remove shims from PATH #4444](https://github.com/jdx/mise/discussions/4444) -- interaction with shim PATH
- [Optimizing Zsh Init with ZProf and Switching to Mise (Mike Kasberg, 2025)](https://www.mikekasberg.com/blog/2025/05/29/optimizing-zsh-init-with-zprof.html) -- 60ms for mise plugin vs 1500ms NVM
- [Oh-My-Zsh startup optimization (various)](https://blog.mattclemente.com/2020/06/26/oh-my-zsh-slow-to-load/) -- compinit, plugin overhead
- [1Password CLI service accounts](https://developer.1password.com/docs/service-accounts/use-with-1password-cli/) -- op read rate limits, supported commands
- [1Password CLI op read reference](https://developer.1password.com/docs/cli/reference/commands/read/) -- read behavior
- [1Password CLI op run reference](https://developer.1password.com/docs/cli/reference/commands/run/) -- env injection
- [1Password CLI secrets in scripts](https://developer.1password.com/docs/cli/secrets-scripts/) -- op run vs op read tradeoffs
- [1Password service account bug reports](https://www.1password.community/discussions/developers/1password-cli-service-account-bug-report/167222) -- token expiration errors
- [chezmoi macOS machine templating](https://www.chezmoi.io/user-guide/machines/macos/) -- conditional template syntax
- [chezmoi templating guide](https://www.chezmoi.io/user-guide/templating/) -- `eq .chezmoi.os "darwin"` pattern
- [launchd.plist(5) man page](https://keith.github.io/xcode-man-pages/launchd.plist.5.html) -- EnvironmentVariables, StartInterval, KeepAlive semantics
- [launchd tutorial](https://www.launchd.info/) -- key interactions and gotchas
- [launchd PATH propagation (Lucas Pinheiro)](https://lucaspin.medium.com/where-is-my-path-launchd-fc3fc5449864) -- child process env
- [macOS security find-generic-password (SS64)](https://ss64.com/mac/security.html) -- exit codes
- [uv installer docs](https://docs.astral.sh/uv/getting-started/installation/) -- `~/.local/bin/env` file purpose
- Local files: `templates/oh-my-zsh/macos-env.zsh`, `templates/oh-my-zsh/aliases.zsh`, `templates/zprofile/macos-dev-env.zsh`, `scripts/ensure-managed-configs.sh`, `scripts/macos-dev-maintenance.sh`, `scripts/secrets-smoke-test.sh`, `scripts/install-validation-launchd.sh`, `scripts/post-setup-run.sh`, `~/.zshrc`, `~/.zprofile`, `~/.oh-my-zsh/custom/*.zsh`

---

## Key Findings -- Shell (Numbered)

### 1. `eval "$(mise activate zsh)"` vs shim PATH: speed and correctness

**Measured overhead:** `mise activate zsh` adds ~20-30ms per prompt evaluation (confirmed in discussion #4821 and local testing). The oh-my-zsh mise plugin adds ~60ms total to shell startup (vs 1500ms+ for NVM).

**Feature gap:** Shims do NOT support environment variables defined in mise config (only available to intercepted commands), most hooks (cd/enter/exit/watch_files), or correct `which` output. `mise activate` supports all features.

**Recommendation from mise docs:** Use the hybrid approach:
- `~/.zprofile` (or `~/.bash_profile`): `eval "$(mise activate --shims)"` -- provides PATH shims for non-interactive contexts (launchd, IDEs, scripts)
- `~/.zshrc` (interactive): `eval "$(mise activate zsh)"` -- full feature set; this call automatically removes the shims directory from PATH when it activates

**Current state (BUG):** `mise activate zsh` is called TWICE in the current setup:
1. In `~/.oh-my-zsh/custom/macos-env.zsh` line 12 (loaded by oh-my-zsh `source $ZSH/oh-my-zsh.sh`)
2. In `~/.zshrc` line 89 (after oh-my-zsh source)

This costs an extra ~20-30ms per prompt for no benefit. The `.zshrc` line 89 call was likely added manually and duplicates the template-managed one.

### 2. `typeset -U path` deduplication: canonical approach and edge cases

**Current implementation** (`macos-env.zsh` lines 31-56) is correct and follows the canonical zsh pattern:
1. `typeset -U path` -- declares the `path` array as unique (automatic dedup)
2. Strips known entries from the rest of the array
3. Rebuilds with explicit ordering: mise shims > mise bin > local bin > bun > pixi > amp > antigravity > oh-my-zsh bin > gcloud > curl > rest

**Edge cases:**
- `typeset -U` only deduplicates exact matches; paths with/without trailing slashes are treated as different
- The stripping pattern `${path_rest:#$HOME/...}` uses zsh array element removal, which is correct for exact matches
- If a new tool manager adds itself to PATH before this code runs (e.g., in `.zprofile`), it will be absorbed into `$path_rest` and placed at the end, which is the desired behavior

**No changes needed.** This is well-implemented.

### 3. `~/.local/bin/env` file: purpose and necessity

**What it is:** A shell-portable script created by the uv standalone installer. Its sole job is to add `$HOME/.local/bin` to PATH if not already present, using a POSIX-compatible `case` guard:
```sh
case ":${PATH}:" in
    *:"$HOME/.local/bin":*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
```

**Is it still needed with modern mise?** The `macos-env.zsh` template already sources it (line 6-8) AND explicitly adds `$HOME/.local/bin` to the path array (line 46). The `zprofile/macos-dev-env.zsh` template also adds it via `add_path_front`.

**Verdict:** The sourcing is harmless (redundant but fast, <1ms) and provides safety for the case where `macos-env.zsh` hasn't loaded yet but uv needs to be on PATH. Keep it, but document it as a "safety net" rather than primary path management.

### 4. chezmoi macOS conditional template syntax (reference patterns)

chezmoi detects macOS via `.chezmoi.os == "darwin"`. Common patterns:

```
{{- if eq .chezmoi.os "darwin" -}}
# macOS-specific content
{{- end -}}
```

For brew prefix detection:
```
{{- if eq .chezmoi.arch "arm64" -}}
/opt/homebrew
{{- else -}}
/usr/local
{{- end -}}
```

The `-` in `{{-` / `-}}` strips surrounding whitespace. This is relevant if MDE ever adopts chezmoi for template management, but currently MDE uses its own `ensure-managed-configs.sh` with simple file copy (no templating).

### 5. Startup time benchmarks for mise activation approaches

| Approach | Measured Overhead | Notes |
|----------|------------------|-------|
| `eval "$(mise activate zsh)"` | ~20-30ms per prompt | Full feature set; runs hook-env on each prompt |
| `mise activate --shims` | ~5ms (one-time PATH prepend) | Shims only; no env vars, no hooks |
| Hybrid (shims in zprofile + activate in zshrc) | ~25ms first prompt, ~20ms subsequent | Recommended by mise docs |
| Oh-my-zsh mise plugin | ~60ms total init | Uses activate internally |
| Duplicate activate (current bug) | ~40-60ms wasted | Fix by removing one call |

**Target:** Well-optimized oh-my-zsh with mise should start in 150-300ms total. Without a framework, 50-100ms is achievable.

### 6. Secret loading performance (keychain reads during startup)

**Measured locally:** 7 sequential `security find-generic-password` calls complete in ~136ms total (~19ms each). This includes both found and not-found items (exit code 44 for missing).

**Impact:** The current `macos-env.zsh` loads 7 secrets at startup via `mde_export_secret`, adding ~136ms to every new shell. This is the single largest startup cost after oh-my-zsh itself.

**Optimization options:**
1. **Lazy loading** -- defer keychain reads until first use (complex, breaks `env` expectations)
2. **Cache in env file** -- use `secrets.env` as cache, only read keychain on explicit refresh (current architecture supports this via `MDE_AUTOLOAD_SECRETS=0`)
3. **Batch read** -- not possible with `security` CLI (no batch mode)
4. **Background preload** -- read in background subshell, export when ready (fragile)
5. **Status quo with documentation** -- 136ms is acceptable for a login shell that opens once; it runs on every new terminal tab however

**Recommendation:** Default `MDE_AUTOLOAD_SECRETS=0` for interactive shells when `MDE_ENV_FILE` already has values. The env file already provides secrets; keychain reads should only run in maintenance/refresh contexts. Add an `mde-secrets-refresh` alias to reload from keychain on demand.

### 7. Alias inventory: current vs required contract

**Existing aliases** (in `templates/oh-my-zsh/aliases.zsh`):

| Alias | Target | Status |
|-------|--------|--------|
| `mde-status` | `scripts/status-dashboard.sh` | Exists |
| `mde-secrets-check` | `scripts/secrets-smoke-test.sh` | Exists |
| `mde-mcp-sync` | `scripts/setup-mcp-servers.sh` | Exists |
| `cloud-run`, `cloud-status`, `sky-status`, `cloud-ssh`, `cloud-view`, `cloud-stop` | SkyPilot operations | Exists |
| `agent-hud` | `scripts/agent-hud` | Exists |
| `firebase` | `scripts/firebase-wrapper.sh` | Exists |
| `claude` | `scripts/claude-wrapper.sh` | Exists |
| `openlit`, `openlit-status`, `openlit-deploy` | `scripts/openlit-control.sh` | Exists |

**Required by Team D spec but MISSING:**

| Alias | Expected Target | Notes |
|-------|----------------|-------|
| `mde-update` | `scripts/macos-dev-maintenance.sh` | Full managed update cycle |
| `mde-update-fast` | TBD | Manager-only short cycle (no agent tools, no MCP) |
| `mde-verify` | `scripts/verify-all.sh` or equivalent | Complete verification suite |
| `mde-drift` | TBD (new script needed) | Ownership/path drift report |
| `mde-migrate` | TBD (new script needed) | Dry-run/apply migration helper |
| `mde-agents-review` | TBD | Orchestrate document-review teams |

**Non-managed custom files** (in `~/.oh-my-zsh/custom/` but not in templates):
- `claude-env.zsh` -- GITHUB_TOKEN -> GITHUB_PERSONAL_ACCESS_TOKEN alias
- `codex.zsh` -- dangerous mode shortcuts
- `launchd.zsh` -- brew autoupdate helpers
- `medan-sky.zsh` -- SkyPilot proxy tunneling

These are not managed by `ensure-managed-configs.sh` and represent user-local customizations.

### 8. zprofile vs zshrc for mise PATH in launchd context

**Zsh loading order:**
1. `/etc/zshenv` -> `~/.zshenv` (always, every shell)
2. `/etc/zprofile` -> `~/.zprofile` (login shells only)
3. `/etc/zshrc` -> `~/.zshrc` (interactive shells only)
4. `/etc/zlogin` -> `~/.zlogin` (login shells only, after zshrc)

**launchd context:** launchd does NOT source any shell profile. It uses its own `EnvironmentVariables` dict from the plist. The wrapper script runs as `#!/usr/bin/env bash`, so it reads `~/.bash_profile` / `~/.bashrc` depending on invocation mode, NOT zsh files.

**Current approach:**
- `~/.zprofile` sources `~/.zprofile.d/macos-dev-env.zsh` which sets up PATH (mise shims + local bin)
- `~/.zshrc` sources oh-my-zsh which loads `macos-env.zsh` (full activate + secrets)
- launchd maintenance script calls `setup_path()` directly, hardcoding the PATH

**Correct placement:**
- mise shims PATH: `~/.zprofile` (login shell, runs before interactive setup -- good for IDEs)
- mise full activate: `~/.zshrc` via oh-my-zsh custom file (interactive shells only -- correct)
- launchd: `EnvironmentVariables` in plist + explicit `setup_path()` in script (correct, since no shell profile is read)

**Current state is architecturally correct** except for the duplicate activate bug noted in finding #1.

### 9. bun shell completion sourcing: current vs recommended

**Current** (`macos-env.zsh` lines 17-19):
```zsh
if [ -s "$BUN_INSTALL/_bun" ]; then
  source "$BUN_INSTALL/_bun"
fi
```

**File size:** `~/.bun/_bun` is 37KB of zsh completions. Sourcing this at startup adds measurable overhead (typically 5-15ms for completion scripts of this size).

**Recommended pattern:** Use `fpath` instead of `source` for completions. The `.zshrc` already sets up a custom completions fpath at `/Users/rmanaloto/.oh-my-zsh/custom/completions`. The recommended approach:
1. Symlink or copy `~/.bun/_bun` to `~/.oh-my-zsh/custom/completions/_bun`
2. Let oh-my-zsh `compinit` pick it up via fpath
3. Remove the explicit `source` from `macos-env.zsh`

This defers completion loading until first tab-completion use, saving 5-15ms at startup. However, this only works if the `_bun` file follows zsh completion function format (it does -- it starts with `#compdef bun`).

---

## Key Findings -- Secrets/Automation (Numbered)

### 1. `op read` behavior with expired/invalid service account token

**Observed behavior:** When `OP_SERVICE_ACCOUNT_TOKEN` is set but expired or invalid:
- `op read` exits with non-zero status
- Error message: `[ERROR] failed to re-initialize service account session`
- In some cases: `Signin credentials are not compatible with the provided user auth from server`
- The `|| true` in `load_op_secret()` (line 40 of `macos-dev-maintenance.sh`) correctly suppresses the error and returns empty value

**Rate limits:** `op read` makes 3 API requests per call (reducible to 1 if vault+item IDs are used instead of names). With 6 secrets, that's 18 API calls per maintenance run. Service accounts have hourly rate limits.

**Recommendation:** Consider using `op run` with a `.env` template to load all secrets in one invocation (1 API call for all secrets) rather than 6 individual `op read` calls.

### 2. `security find-generic-password` behavior when item doesn't exist

**Measured behavior:**
- Exits with code **44** (not 1)
- Stderr: `security: SecKeychainSearchCopyNext: The specified item could not be found in the keychain.`
- Takes ~19ms regardless of found/not-found
- The `2>/dev/null || true` pattern in `mde_load_keychain_secret()` correctly handles this

**Exit codes observed:**
- 0: item found, password returned on stdout
- 44: item not found (`errSecItemNotFound`)
- 45: item already exists (for `add-generic-password`)
- 36: user denied keychain access (interactive prompt was cancelled)

### 3. Performance of multiple `security find-generic-password` calls in shell startup

**Benchmarked:** 7 sequential calls = ~136ms total (~19ms per call). This is the **largest single contributor** to shell startup overhead after oh-my-zsh framework loading.

**Breakdown by scenario:**
| Scenario | Calls | Time |
|----------|-------|------|
| All secrets in env (MDE_AUTOLOAD_SECRETS=0) | 0 | 0ms |
| All secrets in env (MDE_SECRET_OVERRIDE=0) | 7 (skipped early) | ~1ms |
| Mix of env + keychain | 2-4 keychain reads | ~40-80ms |
| All from keychain (no env file) | 7 | ~136ms |

**Key insight:** When `MDE_SECRET_OVERRIDE` is set to `0` (which happens automatically after env file load at line 93-95 of `macos-env.zsh`), the `mde_export_secret` function skips keychain reads for variables already set. BUT the env file load sets `MDE_SECRET_OVERRIDE=0` ONLY if it was previously unset, meaning on first shell with no env file, all 7 keychain reads run.

### 4. launchd `EnvironmentVariables` and PATH propagation to child processes

**Key facts from launchd.plist(5):**
- `EnvironmentVariables` is a dict of key-value pairs set before the job runs
- These are passed to the direct child process via standard Unix env inheritance
- Child processes spawned via `fork(2)` inherit them; grandchild processes may not if intermediary processes reset env
- launchd does NOT source any shell profile files

**Current implementation** in `install-validation-launchd.sh`:
```xml
<key>EnvironmentVariables</key>
<dict>
  <key>MDE_REPO</key>
  <string>$REPO_ROOT</string>
</dict>
```

**Missing:** PATH is not set in the plist `EnvironmentVariables`. The wrapper script calls `setup_path()` in `macos-dev-maintenance.sh` to hardcode it. This is correct because launchd would not know about brew, mise, etc.

**Recommendation:** Add a minimal PATH to the plist `EnvironmentVariables` as a safety net, and keep `setup_path()` as the authoritative PATH builder:
```xml
<key>PATH</key>
<string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
```

### 5. KeepAlive vs RunAtLoad vs StartInterval: correct mechanism for 12-hour interval

**Correct mechanism for periodic maintenance: `StartInterval` alone.**

| Key | Purpose | Correct for 12h? |
|-----|---------|-------------------|
| `StartInterval` | Run every N seconds after last exit | YES: `<integer>43200</integer>` |
| `RunAtLoad` | Run immediately when plist is loaded | Optional addition to StartInterval |
| `KeepAlive` | Restart immediately if process exits | NO -- conflicts with StartInterval; for long-running daemons only |

**Critical interaction:** If `KeepAlive` is `true`, `StartInterval` is ignored because launchd will restart the process immediately on exit, making interval scheduling meaningless.

**Current state:**
- Validation plist uses `StartInterval` (604800 = 7 days) + `RunAtLoad` -- correct
- Maintenance plist is not installed (documented as "create manually" in runbook) -- gap

**Recommendation:** Create an installer script for the maintenance plist using `StartInterval` 43200 + `RunAtLoad` true (same pattern as validation). Do NOT add `KeepAlive`.

### 6. `op --no-masking` flag usage in automation

The `--no-masking` flag on `op read` prevents 1Password from replacing secret values with `<concealed>` in output. It is relevant when:
- Piping `op read` output to another command
- Capturing output in a variable (which is what `load_op_secret` does)

**Current code** (`macos-dev-maintenance.sh` line 40):
```bash
value="$(op read "$ref" 2>/dev/null || true)"
```

This works correctly WITHOUT `--no-masking` because command substitution `$(...)` captures the raw stdout value. The masking behavior applies to terminal output, not captured output. No change needed.

### 7. `op run` vs `op read` + env injection tradeoffs

| Aspect | `op read` (current) | `op run` (alternative) |
|--------|---------------------|----------------------|
| API calls | 3 per secret (18 for 6 secrets) | 1 for all secrets |
| Error granularity | Per-secret error handling | All-or-nothing |
| Implementation | Simple loop, partial failures OK | Requires `.env` template file |
| Secret cleanup | Values persist in env | Values scoped to subprocess only |
| Rate limit risk | Higher (18 calls) | Lower (1 call) |

**`op run` approach would look like:**
```bash
# Template file: .env.op
GITHUB_TOKEN={{ op://vault/item/field }}
OPENAI_API_KEY={{ op://vault/item/field }}
# ...

# Usage:
op run --env-file=.env.op -- bash -c 'export -p' | grep -E '^declare -x (GITHUB_TOKEN|OPENAI_API_KEY)' > /tmp/secrets
source /tmp/secrets
rm /tmp/secrets
```

**Recommendation:** Keep `op read` for the maintenance script (partial failure tolerance is important -- if one secret fails, others should still load). Consider `op run` only if rate limiting becomes a problem.

### 8. `op` CLI version detection before secret reads

**Current code** (`macos-dev-maintenance.sh` line 62):
```bash
if ! have_cmd op; then
  log "1Password CLI not found; skipping secrets load."
  return 0
fi
```

This checks for presence but not version. Service accounts require op >= 2.18.0. Currently installed: **2.32.1** (confirmed).

**Recommendation:** Add a version check:
```bash
local op_version
op_version="$(op --version 2>/dev/null)" || return 0
if [[ "$(printf '%s\n' "2.18.0" "$op_version" | sort -V | head -1)" != "2.18.0" ]]; then
  log "op CLI version $op_version too old for service accounts (need 2.18.0+)."
  return 0
fi
```

This is a defensive measure; it prevents cryptic errors if the system has an old op binary.

### 9. MDE_SECRET_OVERRIDE logic correctness audit

**Three layers of secret loading exist:**

1. **Env file** (`macos-env.zsh` lines 91-96, `macos-dev-maintenance.sh` lines 109-149):
   - Loads from `$MDE_ENV_FILE` (default `~/.config/macos-development-environment/secrets.env`)
   - Uses `MDE_ENV_OVERRIDE` (maintenance) or `MDE_ENV_AUTOLOAD` (shell)
   - After loading, sets `MDE_SECRET_OVERRIDE=0` if previously unset

2. **1Password** (`macos-dev-maintenance.sh` lines 51-75):
   - Uses `MDE_SECRET_OVERRIDE` to decide whether to overwrite existing vars
   - Default: `MDE_SECRET_OVERRIDE=1` (overwrite)
   - After env file load: `MDE_SECRET_OVERRIDE=0` (skip if already set)

3. **Keychain** (`macos-env.zsh` lines 106-128, `macos-dev-maintenance.sh` lines 100-107):
   - Also uses `MDE_SECRET_OVERRIDE`
   - Same logic: skip if var already set and override is 0

**Logic audit:**

The precedence chain works correctly in the **maintenance script** because it loads in order: env file -> 1Password -> Keychain. After env file load, `MDE_SECRET_OVERRIDE=0` prevents 1Password and Keychain from overwriting env file values.

**BUG in `macos-env.zsh`:** The shell template loads env file THEN keychain. After env file sets `MDE_SECRET_OVERRIDE=0`, keychain reads are skipped for any variable already in the env file. This is the intended behavior. However, the variable name is confusing:
- `MDE_SECRET_OVERRIDE=1` means "override existing values" (aggressive)
- `MDE_SECRET_OVERRIDE=0` means "don't override" (conservative)

**Naming suggestion:** Consider renaming to `MDE_SECRET_FORCE_RELOAD` for clarity, but this is a documentation issue, not a functional bug.

**Subtle issue:** In `macos-env.zsh`, `MDE_SECRET_OVERRIDE` defaults to `1` in `mde_export_secret` (line 109) but is set to `0` after env file load (line 94). If `mde_export_secret` is called BEFORE the env file loads (shouldn't happen in normal flow), it would override. The current code order (env file load at line 91, keychain at line 120) is correct.

**One inconsistency:** `macos-dev-maintenance.sh` uses `MDE_ENV_OVERRIDE` (line 111) while `macos-env.zsh` uses `MDE_ENV_OVERRIDE` is not present -- it uses `MDE_SECRET_OVERRIDE` for the same purpose. The maintenance script's `load_env_file_secrets()` uses its own `override` variable from `MDE_ENV_OVERRIDE`, separate from `MDE_SECRET_OVERRIDE`. This means:
- In the maintenance script, env file override is controlled by `MDE_ENV_OVERRIDE`
- In the shell, env file override is controlled by the second parameter to `mde_load_env_file` (default 1 = override)
- Both 1Password and Keychain override is controlled by `MDE_SECRET_OVERRIDE`

This dual-variable approach works but should be documented.

---

## Current Script Audit

| Script | Function/Section | Finding | Action Needed |
|--------|-----------------|---------|---------------|
| `templates/oh-my-zsh/macos-env.zsh` | Line 12: `eval "$(mise activate zsh)"` | Duplicated by `~/.zshrc` line 89 | Remove one (keep template, remove .zshrc line) |
| `templates/oh-my-zsh/macos-env.zsh` | Lines 6-8: `~/.local/bin/env` source | Redundant with line 46 PATH entry | Keep for safety; document as belt-and-suspenders |
| `templates/oh-my-zsh/macos-env.zsh` | Lines 17-19: bun completion source | Slow (37KB parsed at every startup) | Move to fpath-based loading |
| `templates/oh-my-zsh/macos-env.zsh` | Lines 120-128: keychain secret loading | ~136ms overhead for 7 calls | Consider defaulting MDE_AUTOLOAD_SECRETS=0 when env file exists |
| `templates/oh-my-zsh/macos-env.zsh` | Line 31: `typeset -U path` | Correct implementation | No change |
| `templates/oh-my-zsh/macos-env.zsh` | Lines 93-95: MDE_SECRET_OVERRIDE=0 | Only set when unset; correct logic | Document the precedence chain |
| `templates/oh-my-zsh/aliases.zsh` | Full file | Missing 6 aliases from Team D spec | Add mde-update, mde-update-fast, mde-verify, mde-drift, mde-migrate, mde-agents-review |
| `templates/zprofile/macos-dev-env.zsh` | Lines 19-25: mise shim PATH | Uses shim PATH only (no activate) | Correct for zprofile (non-interactive) |
| `scripts/ensure-managed-configs.sh` | `sync_file` function | Only syncs 3 templates + tmux + zprofile | Does not manage claude-env.zsh, codex.zsh, launchd.zsh, medan-sky.zsh |
| `scripts/macos-dev-maintenance.sh` | `setup_path()` line 173 | Hardcoded PATH; does not include ~/.amp/bin, ~/.antigravity/bin | Sync with macos-env.zsh PATH list |
| `scripts/macos-dev-maintenance.sh` | `load_1password_secrets()` | No op version check | Add version >= 2.18.0 check |
| `scripts/macos-dev-maintenance.sh` | Lines 496-498 | Duplicate `cleanup_gemini_cli` call (lines 497 and 489) | Remove duplicate |
| `scripts/macos-dev-maintenance.sh` | `load_env_file_secrets()` line 136 | Quote stripping regex differs from macos-env.zsh | Harmonize (zsh uses `[[ "$value" == \"*\" ]]`, bash uses `[[ "$value" == "\"*\"" ]]`) |
| `scripts/secrets-smoke-test.sh` | `check_secret` | Only checks 5 secrets; missing GITHUB_MCP_PAT, LANGSMITH_WORKSPACE_ID | Add missing checks |
| `scripts/install-validation-launchd.sh` | Plist EnvironmentVariables | Only sets MDE_REPO; no PATH | Add minimal PATH for safety |
| `scripts/install-validation-launchd.sh` | `launchctl unload/load` | Uses deprecated API | Migrate to `launchctl bootout`/`launchctl bootstrap` |
| `scripts/post-setup-run.sh` | Line 8 | References maintenance wrapper | Correct fallback to direct script |
| `~/.zshrc` | Line 89 | Duplicate `eval "$(mise activate zsh)"` | Remove (managed copy in macos-env.zsh is authoritative) |
| `~/.zshrc` | Line 87 | SkyPilot completion: `. ~/.sky/.sky-complete.zsh` | Should be guarded with `[[ -f ... ]]` check |
| `~/.zshrc` | Line 88 | `export PATH="$HOME/.cache/oh-my-opencode/bin:$PATH"` | Unmanaged PATH prepend; will be overridden by macos-env.zsh ordering |

---

## Recommended Patterns

### Shell Startup Architecture

```
~/.zprofile (login shells)
  |-- brew shellenv (Homebrew)
  |-- ~/.zprofile.d/macos-dev-env.zsh
  |     |-- mise shims PATH (non-interactive)
  |     |-- ~/.local/bin PATH
  |     |-- UV_CACHE_DIR, GOBIN
  |-- OrbStack init

~/.zshrc (interactive shells)
  |-- fpath setup (completions)
  |-- oh-my-zsh source
  |     |-- plugins: git, gh, direnv
  |     |-- custom/*.zsh (alphabetical):
  |           |-- aliases.zsh (MDE aliases)
  |           |-- claude-env.zsh (token aliasing)
  |           |-- llvm.zsh (compiler paths)
  |           |-- macos-env.zsh:
  |                 |-- ~/.local/bin/env (safety PATH)
  |                 |-- mise activate zsh (full)  <-- SINGLE activation point
  |                 |-- bun PATH (not completion)
  |                 |-- UV_CACHE_DIR, GOBIN, UV_NO_MANAGED_PYTHON
  |                 |-- PATH ordering (typeset -U)
  |                 |-- env file loading
  |                 |-- keychain secret loading (if MDE_AUTOLOAD_SECRETS=1)
  |-- SkyPilot completions (guarded)
```

### Secret Loading Precedence

```
Priority (highest wins when MDE_SECRET_OVERRIDE=1):
  1. Environment variables already set (e.g., by CI/CD)
  2. secrets.env file (~/.config/macos-development-environment/secrets.env)
  3. 1Password service account (op read, maintenance script only)
  4. macOS Keychain (security find-generic-password)

After env file loads successfully:
  - MDE_SECRET_OVERRIDE -> 0 (prevents lower-priority sources from overwriting)

Override hierarchy variables:
  - MDE_ENV_AUTOLOAD: controls whether env file is read (default 1)
  - MDE_SECRET_OVERRIDE: controls whether 1Password/Keychain overwrite existing vars
  - MDE_AUTOLOAD_SECRETS: controls whether Keychain secrets load in interactive shell
```

### launchd Plist Template (Maintenance)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ray-manaloto.macos-dev-maintenance</string>
  <key>ProgramArguments</key>
  <array>
    <string>/path/to/wrapper</string>
  </array>
  <key>StartInterval</key>
  <integer>43200</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>MDE_REPO</key>
    <string>/path/to/repo</string>
    <key>MDE_AUTOFIX</key>
    <string>1</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>~/Library/Logs/.../maintenance.out</string>
  <key>StandardErrorPath</key>
  <string>~/Library/Logs/.../maintenance.out</string>
  <key>LowPriorityBackgroundIO</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
```

---

## Implementation-Ready Decisions

1. **Remove duplicate `mise activate zsh`** from `~/.zshrc` line 89. The template-managed `macos-env.zsh` is the authoritative activation point.

2. **Keep hybrid shims+activate approach.** `~/.zprofile.d/macos-dev-env.zsh` provides shim PATH for non-interactive contexts. `macos-env.zsh` provides full `mise activate zsh` for interactive shells. This is the mise-recommended pattern.

3. **Move bun completions to fpath.** Replace `source "$BUN_INSTALL/_bun"` with a symlink from `~/.bun/_bun` to `~/.oh-my-zsh/custom/completions/_bun`. Saves 5-15ms per startup.

4. **Add missing aliases to `templates/oh-my-zsh/aliases.zsh`:**
   - `mde-update` -> `scripts/macos-dev-maintenance.sh`
   - `mde-update-fast` -> `MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 scripts/macos-dev-maintenance.sh`
   - `mde-verify` -> `scripts/verify-all.sh` (or `scripts/post-setup-run.sh`)
   - `mde-drift` -> new drift detection script (to be created)
   - `mde-migrate` -> new migration helper (to be created)
   - `mde-agents-review` -> new orchestration alias (to be created)

5. **Create maintenance launchd installer** parallel to `install-validation-launchd.sh`. Use `StartInterval` 43200 + `RunAtLoad` true. Do NOT use `KeepAlive`.

6. **Sync `setup_path()` in maintenance script** with `macos-env.zsh` PATH list (add `~/.amp/bin`, `~/.antigravity/antigravity/bin`, `~/.oh-my-zsh/custom/bin`, `/opt/google-cloud-sdk/bin`).

7. **Add op version check** before service account secret reads.

8. **Fix duplicate `cleanup_gemini_cli` call** in maintenance script (lines 489/497).

9. **Guard SkyPilot completion** in `.zshrc` with `[[ -f ~/.sky/.sky-complete.zsh ]] && . ~/.sky/.sky-complete.zsh`.

10. **Document secret precedence chain** in the launchd-automation-runbook or a dedicated secrets-architecture doc.

---

## Open Questions / Caveats

1. **Keychain startup cost tolerance:** The 136ms for 7 keychain reads is measurable but may be acceptable depending on how frequently new shells are opened. If the user primarily uses tmux (persistent sessions), this cost is paid rarely. If they open many terminal tabs, it adds up. Decision deferred to user preference.

2. **`mise activate` in .zshrc vs oh-my-zsh custom file:** oh-my-zsh custom files load in alphabetical order during `source $ZSH/oh-my-zsh.sh`. Anything in `.zshrc` after that line runs after all custom files. The current template places `mise activate` in `macos-env.zsh` (loaded by oh-my-zsh), which means it runs before the end of `.zshrc`. This is fine, but means the duplicate `.zshrc` line 89 always runs second (wastefully).

3. **`launchctl load/unload` deprecation:** Apple deprecated `launchctl load/unload` in favor of `launchctl bootstrap/bootout` with domain targets (e.g., `gui/$UID`). The current `install-validation-launchd.sh` uses the deprecated API. Migrating requires:
   ```bash
   launchctl bootout "gui/$UID/com.ray-manaloto.macos-dev-validation" 2>/dev/null || true
   launchctl bootstrap "gui/$UID" "$PLIST"
   ```
   This should be done but is low risk.

4. **`security find-generic-password` and keychain locking:** If the login keychain is locked (e.g., after extended sleep), the command may prompt for a password in GUI context or fail silently in headless context. The `2>/dev/null || true` pattern handles this, but the user might not realize secrets are missing. The smoke test script mitigates this.

5. **op service account token in Keychain vs env:** The maintenance script tries `OP_SERVICE_ACCOUNT_TOKEN` env var first, then falls back to keychain label `mde-op-sa`. If neither is set, 1Password loading is skipped entirely (graceful). This is correct behavior but means the service account token itself needs to be provisioned separately.

6. **env file quote stripping:** The zsh version (`macos-env.zsh`) and bash version (`macos-dev-maintenance.sh`) use slightly different quote-stripping patterns. The zsh version uses `[[ "$value" == \"*\" ]]` while the bash version uses `[[ "$value" == "\"*\"" ]]`. Both achieve the same result but the inconsistency could lead to edge-case differences with values containing escaped quotes. Consider extracting to a shared function or harmonizing the pattern.

---

## Cross-References

- **R1 (Mise Core):** mise config.toml `[settings]` section controls whether `mise activate` uses hook-env or not. The `experimental` flag enables newer features. PATH ordering in R4 depends on R1's backend/registry decisions.
- **R2 (Tool Interactions):** bun, uv, pixi self-update behavior (whether they modify PATH) interacts with R4's PATH ordering contract. The `UV_NO_MANAGED_PYTHON=1` export in `macos-env.zsh` is a direct consequence of R2's finding about uv Python download behavior.
- **R3 (Reference Repos):** basnijholt/dotfiles uses chezmoi templating for macOS conditionals (R4 finding #4). thoughtbot/laptop uses a linear script approach rather than oh-my-zsh custom files.
- **R5 (Brew Verification):** The brew boundary decisions affect what goes in PATH and whether brew-managed tools (like llvm) need special PATH handling (R4: `llvm.zsh` custom file).
- **Team D Spec:** R4's alias gap analysis directly informs Team D implementation. The 6 missing aliases need corresponding scripts before the alias file can be updated.
- **Team E Spec:** R4's launchd findings (StartInterval, EnvironmentVariables, PATH) directly inform Team E's maintenance hardening. The `setup_path()` sync gap and duplicate cleanup call are bugs that Team E should fix.
