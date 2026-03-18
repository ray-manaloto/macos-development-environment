# Oh-My-Zsh Configuration Audit Report

Generated: 2026-02-28

---

## 1. Overview

This repository manages macOS shell configuration through oh-my-zsh custom files.
Templates live in `templates/oh-my-zsh/` and are deployed to
`~/.oh-my-zsh/custom/` via `scripts/ensure-managed-configs.sh`. The deployment
uses a file-copy strategy with a managed-file marker to avoid overwriting
user-created files.

A **template-deploy sync gap** was found: the deployed `aliases.zsh` and
`macos-env.zsh` files are stale compared to the templates in the repository
working tree. This gap is the root cause of the reported alias bug -- newly
added `mde-*` lifecycle aliases exist in the template but are absent from the
deployed file that zsh actually loads.

---

## 2. Template Files

Three oh-my-zsh templates are managed by this repository:

| Template | Deployed To | Purpose |
|----------|-------------|---------|
| `templates/oh-my-zsh/aliases.zsh` | `~/.oh-my-zsh/custom/aliases.zsh` | Shell aliases for cloud, agent, telemetry, and MDE lifecycle commands |
| `templates/oh-my-zsh/macos-env.zsh` | `~/.oh-my-zsh/custom/macos-env.zsh` | PATH ordering, env vars, mise activation, secrets loading |
| `templates/oh-my-zsh/llvm.zsh` | `~/.oh-my-zsh/custom/llvm.zsh` | Opt-in LLVM/Clang toolchain config (MDE_USE_LLVM flag) |

Additional templates deployed by the same script (not oh-my-zsh):

| Template | Deployed To | Purpose |
|----------|-------------|---------|
| `templates/tmux.conf` | `~/.tmux.conf` | Tmux configuration |
| `templates/zprofile/macos-dev-env.zsh` | `~/.zprofile.d/macos-dev-env.zsh` | Login-shell PATH bootstrap (mise shims, GOBIN, UV_CACHE_DIR) |

---

## 3. Deployment Mechanism (`ensure-managed-configs.sh`)

**File:** `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/ensure-managed-configs.sh`

### How It Works

The script defines two core functions:

**`sync_file(src, dest)`** -- For configuration files:
1. Checks that the source template exists.
2. Creates the destination directory if needed.
3. If the destination file exists AND does NOT contain the marker string
   `"Managed by macos-development-environment"`, it **skips** the file
   (protects user-created files from being overwritten).
4. Otherwise, copies (`cp`) the source to the destination.

**`sync_exec(src, dest)`** -- For executable wrappers (e.g., claude, gemini):
1. Same marker check, but uses `install -m 0755` instead of `cp`.
2. Special case: if the destination references `mde-mcp-common.sh`, it
   overwrites even without the managed marker (legacy migration path).

**`ensure_zprofile_include()`** -- Appends a source line to `~/.zprofile`
pointing to `~/.zprofile.d/macos-dev-env.zsh` (idempotent, checks for
existing include).

### Strategy Details

- **Copy, not symlink**: Files are copied, not symlinked. This means changes
  to templates in the repo do NOT automatically propagate to the deployed
  files. A re-run of `ensure-managed-configs.sh` is required.
- **No backup on overwrite**: When the managed marker is present, the script
  overwrites without creating a backup of the previous version. This is safe
  because the template is the source of truth, but makes it impossible to
  recover intermediate manual edits.
- **Idempotent**: Safe to re-run. Will overwrite managed files and skip
  unmanaged ones. Creates directories as needed.
- **No diff or checksum check**: The script always copies, even when the
  source and destination are identical. Not harmful, just unnecessary I/O.

### Files Synced

```
sync_file: templates/oh-my-zsh/macos-env.zsh -> ~/.oh-my-zsh/custom/macos-env.zsh
sync_file: templates/oh-my-zsh/aliases.zsh   -> ~/.oh-my-zsh/custom/aliases.zsh
sync_file: templates/oh-my-zsh/llvm.zsh      -> ~/.oh-my-zsh/custom/llvm.zsh
sync_file: templates/tmux.conf               -> ~/.tmux.conf
sync_file: templates/zprofile/macos-dev-env.zsh -> ~/.zprofile.d/macos-dev-env.zsh
sync_exec: scripts/claude-wrapper.sh         -> ~/.local/bin/claude
sync_exec: scripts/gemini-wrapper.sh         -> ~/.local/bin/gemini
sync_exec: scripts/langsmith-wrapper.sh      -> ~/.local/bin/langsmith-fetch
sync_exec: scripts/langsmith-wrapper.sh      -> ~/.local/bin/langsmith-migrator
sync_exec: scripts/langsmith-wrapper.sh      -> ~/.local/bin/langsmith-mcp-server
sync_exec: scripts/fabric-wrapper.sh         -> ~/.local/bin/fabric
```

### What Triggers It

The script is called from `macos-dev-maintenance.sh` in the `sync_managed_configs()`
function, BUT **only when `MDE_AUTOFIX=1`** is set:

```bash
# macos-dev-maintenance.sh, line 507-528
if [[ "$MDE_AUTOFIX" == "1" ]]; then
    ...
    sync_managed_configs   # <-- line 520
    ...
fi
```

**`MDE_AUTOFIX` defaults to `0`** (line 6 of `macos-dev-maintenance.sh`).

This means:
- The launchd job that runs every 12 hours does **NOT** sync configs by default.
- The `mde-update` alias runs `macos-dev-maintenance.sh` without `MDE_AUTOFIX=1`.
- Config sync only happens when a user explicitly runs with `MDE_AUTOFIX=1` or
  runs `scripts/ensure-managed-configs.sh` directly.

This is the **root cause** of the sync gap.

---

## 4. Shell Startup Flow

### How oh-my-zsh Loads Custom Files

Oh-my-zsh automatically sources all `*.zsh` files in `$ZSH_CUSTOM/` (which
defaults to `~/.oh-my-zsh/custom/`) during shell initialization. The load
order is alphabetical by filename.

The loading sequence for a new interactive zsh shell:

```
1. /etc/zshenv (system)
2. ~/.zshenv (if exists)
3. /etc/zprofile (system, login shells only)
4. ~/.zprofile (login shells only)
   -> sources ~/.zprofile.d/macos-dev-env.zsh (PATH bootstrap)
5. /etc/zshrc (system)
6. ~/.zshrc
   -> sources $ZSH/oh-my-zsh.sh (oh-my-zsh framework)
      -> sources ~/.oh-my-zsh/custom/*.zsh (alphabetical):
         a. aliases.zsh     -- aliases
         b. claude-env.zsh  -- GITHUB_PERSONAL_ACCESS_TOKEN alias
         c. codex.zsh       -- dangerous-mode helper functions
         d. example.zsh     -- oh-my-zsh example (no-op)
         e. launchd.zsh     -- brewautoupdate aliases
         f. llvm.zsh        -- LLVM PATH/flags
         g. macos-env.zsh   -- mise, PATH ordering, secrets
         h. medan-sky.zsh   -- SkyPilot tunnel helper
```

**Important ordering note:** `aliases.zsh` loads **before** `macos-env.zsh`
(alphabetical). The aliases use `$HOME` expansion which works fine, but if
any alias depended on env vars set by `macos-env.zsh`, they would fail
because `macos-env.zsh` loads later. Currently this is not a problem because
aliases use absolute paths with `$HOME`, not custom env vars.

### Managed vs Unmanaged Files

Files managed by this repo (contain "Managed by macos-development-environment"):
- `aliases.zsh`
- `macos-env.zsh`
- `llvm.zsh`

Unmanaged files (user-created, will NOT be overwritten by ensure-managed-configs.sh):
- `claude-env.zsh` -- GitHub token aliasing for Claude plugins
- `codex.zsh` -- Dangerous-mode helper functions for codex/claude/gemini
- `example.zsh` -- Default oh-my-zsh example file
- `launchd.zsh` -- Homebrew autoupdate launchd helpers
- `medan-sky.zsh` -- SkyPilot SSH tunnel proxy function

---

## 5. Current Sync Gap

### aliases.zsh Diff

The template (`templates/oh-my-zsh/aliases.zsh`) contains 8 lines that are
**missing** from the deployed file (`~/.oh-my-zsh/custom/aliases.zsh`):

```diff
  # After the openlit aliases block, the template has:
+
+ # MDE lifecycle
+ alias mde-update="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
+ alias mde-update-fast="MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 $HOME/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh"
+ alias mde-verify="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/verify-all.sh"
+ alias mde-drift="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-drift-check.sh"
+ alias mde-migrate="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-migrate-to-mise.sh"
+ alias mde-agents-review="$HOME/dev/github/ray-manaloto/macos-development-environment/scripts/mde-agents-review.sh"
```

**The deployed file is missing the entire "MDE lifecycle" alias block.** This
is the direct cause of the alias bug -- typing `mde-update`, `mde-verify`,
`mde-drift`, `mde-migrate`, or `mde-agents-review` in a shell produces
"command not found".

### macos-env.zsh Diff

Three differences between the template and deployed versions:

| Area | Template (new) | Deployed (stale) |
|------|---------------|------------------|
| **mise note** | Has comment about duplicate `mise activate zsh` adding ~5ms | Missing the comment |
| **Bun completions** | Comment-only: suggests fpath-based `_bun` completion loading | Sources `$BUN_INSTALL/_bun` directly (37KB on every shell startup) |
| **Python downloads** | `UV_PYTHON_DOWNLOADS=never` | `UV_NO_MANAGED_PYTHON=1` (deprecated env var) |

The bun completion change is a performance optimization (avoids sourcing 37KB
on every shell startup). The UV env var change aligns with the current uv API
(`UV_PYTHON_DOWNLOADS=never` replaced the older `UV_NO_MANAGED_PYTHON=1`).

### llvm.zsh

No diff. The deployed `llvm.zsh` matches the template exactly.

### Deployed File Timestamps

```
~/.oh-my-zsh/custom/aliases.zsh   -- 2026-02-28 17:11:42
~/.oh-my-zsh/custom/macos-env.zsh -- 2026-02-28 17:11:42
~/.oh-my-zsh/custom/llvm.zsh      -- 2026-02-28 17:11:42
```

Template timestamps (working tree, uncommitted changes):
```
templates/oh-my-zsh/aliases.zsh   -- 2026-02-28 18:35:48
templates/oh-my-zsh/macos-env.zsh -- 2026-02-28 18:37:45
```

The templates were modified ~80 minutes after the last deploy. The deploy at
17:11 captured the old versions; the templates were updated at ~18:35 but
`ensure-managed-configs.sh` was not re-run.

---

## 6. All Aliases (Categorized)

### Cloud / SkyPilot Aliases (in template)
| Alias | Target | Status |
|-------|--------|--------|
| `cloud-run` | `sky launch -d -c agent-cluster agent_cloud.yaml` | Deployed |
| `cloud-status` | `scripts/sky-status.sh` | Deployed |
| `sky-status` | `scripts/sky-status.sh` | Deployed |
| `cloud-ssh` | `ssh agent-cluster` | Deployed |
| `cloud-view` | `ssh -L 8123:localhost:8123 agent-cluster` | Deployed |
| `cloud-stop` | `sky down agent-cluster` | Deployed |

### Agent / Dashboard Aliases (in template)
| Alias | Target | Status |
|-------|--------|--------|
| `agent-hud` | `scripts/agent-hud` | Deployed |
| `mde-status` | `scripts/status-dashboard.sh` | Deployed |
| `mde-secrets-check` | `scripts/secrets-smoke-test.sh` | Deployed |
| `mde-mcp-sync` | `scripts/setup-mcp-servers.sh` | Deployed |
| `firebase` | `scripts/firebase-wrapper.sh` | Deployed |
| `claude` | `scripts/claude-wrapper.sh` | Deployed |

### OpenLIT Telemetry Aliases (in template)
| Alias | Target | Status |
|-------|--------|--------|
| `openlit` | `scripts/openlit-control.sh` | Deployed |
| `openlit-status` | `scripts/openlit-control.sh status` | Deployed |
| `openlit-deploy` | `scripts/openlit-control.sh deploy` | Deployed |

### MDE Lifecycle Aliases (in template, NOT deployed)
| Alias | Target | Status |
|-------|--------|--------|
| `mde-update` | `scripts/macos-dev-maintenance.sh` | **NOT DEPLOYED** |
| `mde-update-fast` | `MDE_UPDATE_AGENT_TOOLS=0 MDE_UPDATE_MCP=0 scripts/macos-dev-maintenance.sh` | **NOT DEPLOYED** |
| `mde-verify` | `scripts/verify-all.sh` | **NOT DEPLOYED** |
| `mde-drift` | `scripts/mde-drift-check.sh` | **NOT DEPLOYED** |
| `mde-migrate` | `scripts/mde-migrate-to-mise.sh` | **NOT DEPLOYED** |
| `mde-agents-review` | `scripts/mde-agents-review.sh` | **NOT DEPLOYED** |

### Aliases in Unmanaged Files (user-created, deployed manually)
| Alias/Function | File | Purpose |
|----------------|------|---------|
| `brewautoupdate-start` | `launchd.zsh` | Start Homebrew autoupdate launchd job |
| `brewautoupdate-status` | `launchd.zsh` | Show launchd job status |
| `brewautoupdate-log` | `launchd.zsh` | Tail autoupdate log |
| `brewautoupdate-tail` | `launchd.zsh` | Follow autoupdate log |
| `skyobs-proxy` / `medan_sky_proxy()` | `medan-sky.zsh` | SSH tunnel to SkyPilot observability cluster |
| `codex_dangerous()` | `codex.zsh` | Run codex with --dangerously-bypass-approvals-and-sandbox |
| `claude_dangerous()` | `codex.zsh` | Run claude with --dangerously-skip-permissions |
| `gemini_dangerous()` | `codex.zsh` | Run gemini with --yolo |

---

## 7. Environment Variables Set

### From `macos-env.zsh` (template version)

| Variable | Value / Source | Purpose |
|----------|---------------|---------|
| `BUN_INSTALL` | `$HOME/.bun` | Bun installation directory |
| `UV_CACHE_DIR` | `$HOME/Library/Caches/uv` | uv package cache location |
| `GOBIN` | `$HOME/.local/bin` | Go binary install target |
| `UV_PYTHON_DOWNLOADS` | `never` | Prevent uv from downloading Python runtimes |
| `MDE_ENV_FILE` | `$HOME/.config/macos-development-environment/secrets.env` | Path to plaintext secrets env file |
| `MDE_SECRET_OVERRIDE` | `0` (set after env file load) | Controls whether keychain overrides env file |

### Secrets Loaded (from Keychain, when `MDE_AUTOLOAD_SECRETS=1`)

| Keychain Label | Environment Variable |
|---------------|---------------------|
| `mde-openai-api-key` | `OPENAI_API_KEY` |
| `mde-anthropic-api-key` | `ANTHROPIC_API_KEY` |
| `mde-gemini-api-key` | `GEMINI_API_KEY` |
| `mde-langsmith-api-key` | `LANGSMITH_API_KEY` |
| `mde-langsmith-workspace-id` | `LANGSMITH_WORKSPACE_ID` |
| `mde-github-token` | `GITHUB_TOKEN` |
| `mde-github-mcp-pat` | `GITHUB_MCP_PAT` |

### From `llvm.zsh` (when `MDE_USE_LLVM=1`, the default)

| Variable | Value |
|----------|-------|
| `PATH` | Prepends `/opt/homebrew/opt/llvm/bin` |
| `LDFLAGS` | `-L/opt/homebrew/opt/llvm/lib` |
| `CPPFLAGS` | `-I/opt/homebrew/opt/llvm/include` |
| `PKG_CONFIG_PATH` | `/opt/homebrew/opt/llvm/lib/pkgconfig` |
| `CC` | `clang` |
| `CXX` | `clang++` |

### From `claude-env.zsh` (unmanaged)

| Variable | Value | Purpose |
|----------|-------|---------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Copied from `GITHUB_TOKEN` | Required by GitHub MCP server plugin |

### PATH Order (from `macos-env.zsh`, highest priority first)

```
1. ~/.local/share/mise/shims       (mise runtime shims)
2. ~/.local/share/mise/bin          (mise binaries)
3. ~/.local/bin                     (local wrappers: claude, gemini, etc.)
4. ~/.bun/bin                       (bun global installs)
5. ~/.pixi/bin                      (pixi tools)
6. ~/.amp/bin                       (amp tool)
7. ~/.antigravity/antigravity/bin   (antigravity tool)
8. ~/.oh-my-zsh/custom/bin          (custom bin directory)
9. /opt/google-cloud-sdk/bin        (gcloud SDK)
10. /opt/homebrew/opt/curl/bin      (Homebrew curl)
11. (remaining system PATH entries)
```

---

## 8. Known Issues and Gaps

### Issue 1: Template-Deploy Sync Gap (ROOT CAUSE OF ALIAS BUG)

**Severity: High**

The `MDE lifecycle` alias block (6 aliases) exists in the template
`templates/oh-my-zsh/aliases.zsh` but is absent from the deployed file
`~/.oh-my-zsh/custom/aliases.zsh`. Running `mde-update`, `mde-verify`,
`mde-drift`, `mde-migrate`, or `mde-agents-review` in a shell produces
"command not found".

**Fix:** Run `scripts/ensure-managed-configs.sh` to copy the updated
template to the deployed location. Alternatively, run
`MDE_AUTOFIX=1 scripts/macos-dev-maintenance.sh`.

### Issue 2: Config Sync Not Part of Default Maintenance

**Severity: Medium**

`ensure-managed-configs.sh` is only invoked when `MDE_AUTOFIX=1`, which
defaults to `0`. The 12-hour launchd maintenance job and the `mde-update`
alias both run without `MDE_AUTOFIX=1`, meaning template changes never
automatically propagate to `~/.oh-my-zsh/custom/`.

**Impact:** Every time a template is updated in the repo, the developer must
remember to manually run `ensure-managed-configs.sh` or set `MDE_AUTOFIX=1`.
This is error-prone and is the direct cause of the current sync gap.

**Recommendation:** Either (a) make config sync part of the default
maintenance flow (not gated behind `MDE_AUTOFIX`), or (b) always run
`ensure-managed-configs.sh` at the end of `macos-dev-maintenance.sh`
regardless of `MDE_AUTOFIX` setting.

### Issue 3: Deprecated UV Environment Variable in Deployed File

**Severity: Low**

The deployed `macos-env.zsh` uses `UV_NO_MANAGED_PYTHON=1` which is the old
env var. The template has been updated to `UV_PYTHON_DOWNLOADS=never` which
is the current uv API. The stale deployed file still works (uv still honors
the old var) but should be updated.

### Issue 4: Bun Completion Performance

**Severity: Low**

The deployed `macos-env.zsh` sources `$BUN_INSTALL/_bun` on every shell
startup (~37KB). The template has been updated to remove this and instead
suggests fpath-based completion loading via a symlink, which is faster.

### Issue 5: Copy-Based Deployment Without Checksums

**Severity: Low**

The `sync_file` function always copies, never checks if the source and
destination are already identical. For correctness this is fine, but it means
there is no way to detect drift without running a manual diff.

**Recommendation:** Add a `--check` or `--dry-run` mode to
`ensure-managed-configs.sh` that reports which files are out of sync without
modifying them. The existing `mde-drift-check.sh` script may already address
this partially, but it is one of the aliases that is currently not deployed.

### Issue 6: Unmanaged Custom Files Not Tracked

**Severity: Low**

Four files in `~/.oh-my-zsh/custom/` are not managed by this repository:
`claude-env.zsh`, `codex.zsh`, `launchd.zsh`, `medan-sky.zsh`. If these
files are important to the development environment, they should be promoted
to templates. If they are intentionally local-only, this is fine but should
be documented.

### Issue 7: No Notification on Sync Gap

**Severity: Medium**

There is no mechanism to alert the user when deployed configs are stale.
A shell startup check (e.g., a checksum comparison in `macos-env.zsh`) could
warn the user that templates have changed and `ensure-managed-configs.sh`
needs to be re-run.

---

## Summary of Key File Paths

| Purpose | Absolute Path |
|---------|---------------|
| Alias template | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/aliases.zsh` |
| Env template | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/macos-env.zsh` |
| LLVM template | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/llvm.zsh` |
| Deployment script | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/ensure-managed-configs.sh` |
| Maintenance script | `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh` |
| Deployed aliases | `/Users/rmanaloto/.oh-my-zsh/custom/aliases.zsh` |
| Deployed env | `/Users/rmanaloto/.oh-my-zsh/custom/macos-env.zsh` |
| Deployed llvm | `/Users/rmanaloto/.oh-my-zsh/custom/llvm.zsh` |
