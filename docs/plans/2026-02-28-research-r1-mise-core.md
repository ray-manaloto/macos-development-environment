# Research Report R1: mise Core Technology

## Sources Consulted

| Source | What was found |
|--------|----------------|
| [mise.jdx.dev](https://mise.jdx.dev/) | Core identity: polyglot tool version manager, env manager, task runner. Current version 2026.2.23. |
| [mise configuration docs](https://mise.jdx.dev/configuration.html) | Full config.toml format, version pinning syntax, trust model, merge behavior, idiomatic version files |
| [mise registry](https://mise.jdx.dev/registry.html) | Registry architecture, backend priority, aqua-first default, backend override via env vars |
| [mise tips and tricks](https://mise.jdx.dev/tips-and-tricks.html) | Shebang usage, `mise en` for non-interactive, lockfile tips, auto-install hooks |
| [mise aqua backend](https://mise.jdx.dev/dev-tools/backends/aqua.html) | Native Rust reimplementation, aqua registry compiled into binary, security verification (cosign, SLSA, minisign, GitHub attestations), `symlink_bins` |
| [mise ubi backend](https://mise.jdx.dev/dev-tools/backends/ubi.html) | **Deprecated** -- replaced by `github:` backend. Migration: `ubi:owner/repo` -> `github:owner/repo` |
| [mise backends](https://mise.jdx.dev/dev-tools/backends/) | 18 backends total: core, aqua, github, gitlab, asdf, vfox, cargo, go, npm, pipx, http, s3, spm, conda, dotnet, forgejo, gem, ubi |
| [mise.lock docs](https://mise.jdx.dev/dev-tools/mise-lock.html) | TOML format, per-platform checksums/URLs, `lockfile = true` setting, `locked = true` for strict enforcement |
| [mise use CLI](https://mise.jdx.dev/cli/use.html) | `--global`, `--pin`, `--fuzzy`, `--before`, config file targeting logic |
| [mise install CLI](https://mise.jdx.dev/cli/install.html) | Installs only; does NOT modify config files or activate tools |
| [mise upgrade CLI](https://mise.jdx.dev/cli/upgrade.html) | `--yes` skips prompts, `--bump` upgrades across major versions and rewrites config, `--exclude` |
| [mise self-update CLI](https://mise.jdx.dev/cli/self-update.html) | `--yes` for non-interactive, `--no-plugins`, not available when installed via package manager |
| [mise doctor CLI](https://mise.jdx.dev/cli/doctor.html) | Checks installation health, `--json` for machine output, `dr` alias |
| [mise shims docs](https://mise.jdx.dev/dev-tools/shims.html) | Shim directory `~/.local/share/mise/shims`, tradeoffs vs `mise activate`, non-interactive behavior |
| [mise settings](https://mise.jdx.dev/configuration/settings.html) | `trusted_config_paths`, `yes`, `paranoid`, `lockfile`, `locked`, `go.set_gobin`, `disable_backends`, `env_shell_expand` |
| [mise environments](https://mise.jdx.dev/environments/) | `[env]` section, `_.path`, `_.file`, `_.source`, templates, `redact`, `required` |
| [DeepWiki registry analysis](https://deepwiki.com/jdx/mise/6.1-registry-system) | Compile-time registry from TOML files, backend resolution pipeline: env-var override -> type filter -> platform filter -> experimental filter |
| [github.com/jdx/mise](https://github.com/jdx/mise) | 25.1k stars, 749 contributors, 509 releases. Latest: v2026.2.23, stricter lockfile enforcement. |
| `/docs/mise-config.md` (local) | Current config uses `python = "latest"`, `node = "latest"`, etc. `[env]` sets `UV_NO_MANAGED_PYTHON`. pixi/uv installed outside mise. |
| `/docs/toolchain-precedence.md` (local) | Precedence: mise > bun > pixi > uv > Homebrew. `mise upgrade --yes` used in maintenance. |
| `/scripts/install-agent-stack.sh` (local) | Uses `mise install -q`, `mise use -g`, `mise activate bash`, `mise reshim`, `mise where python@${VERSION}` |
| `/scripts/macos-dev-maintenance.sh` (local) | Uses `mise self-update`, `mise upgrade --yes`, `mise reshim`, `mise use -g --yes` |

---

## Key Findings (Numbered)

### 1. Version Pinning Syntax in config.toml

Mise supports multiple version specifiers in `[tools]`:

```toml
[tools]
node = "20.0.0"            # Exact version
node = "20"                 # Fuzzy: latest 20.x.x
node = "latest"             # Latest available
node = "lts"                # LTS channel (Node-specific)
node = "ref:master"         # Compile from VCS ref
node = "prefix:1.19"        # Latest matching prefix
node = "sub-0.1:latest"     # Version arithmetic
python = "path:./cpython"   # Custom compiled location

# Advanced: version + options
node = { version = "22", postinstall = "corepack enable" }
```

The `mise use --pin` flag writes exact versions (e.g., `20.11.1`), while `--fuzzy` writes fuzzy versions (e.g., `20`). Default behavior is fuzzy unless `MISE_PIN=1`.

**Recommendation for this codebase**: The current `python = "latest"`, `node = "latest"` pattern is valid but provides no reproducibility. Consider adding `lockfile = true` to pin resolved versions.

### 2. Aqua Backend

**Declaration syntax:**

```toml
[tools]
# Explicit aqua backend
"aqua:BurntSushi/ripgrep" = "latest"

# Or when the registry defaults to aqua for a tool
aws-cli = "latest"            # resolves to aqua:aws/aws-cli automatically
aws-cli = { version = "latest", symlink_bins = true }  # prevent bundled Python exposure
```

**How it works internally:** The aqua CLI is NOT used. Mise has a native Rust reimplementation that uses the aqua registry (YAML files compiled into the mise binary at build time). Zero external dependencies.

**Security features (native Rust implementations):**
- Cosign signature verification (`aqua.cosign = true`, default)
- SLSA provenance verification (`aqua.slsa = true`, default)
- GitHub Artifact Attestations (`aqua.github_attestations = true`, default)
- Minisign signature verification (`aqua.minisign = true`, default)
- Checksums (SHA256/512/1/MD5, always enabled)

**Settings:**

| Setting | Default | Purpose |
|---------|---------|---------|
| `aqua.baked_registry` | `true` | Use compiled-in registry |
| `aqua.registry_url` | `None` | Custom registry URL |
| `aqua.cosign` | `true` | Cosign verification |
| `aqua.slsa` | `true` | SLSA provenance |
| `aqua.github_attestations` | `true` | GitHub attestations |
| `aqua.minisign` | `true` | Minisign verification |

**Limitations:** Cannot set environment variables; only downloads binaries. Tools needing env vars require asdf/vfox plugins. Package types `cargo` and `go_install` are not supported via aqua.

**Tools in this repo that have aqua entries:** Based on the registry, tools used by this codebase that have aqua backends include: `aws-cli` (aqua:aws/aws-cli), `kubectl` (aqua:kubernetes/kubectl), `helm` (aqua:helm/helm), `terraform` (aqua:hashicorp/terraform), `gh` (aqua:cli/cli), `jq`, `yq`, `ripgrep` (aqua:BurntSushi/ripgrep). Core runtimes (python, node, go, rust) use the `core:` backend.

### 3. UBI Backend

**Status: DEPRECATED.** Replace `ubi:owner/repo` with `github:owner/repo`.

The ubi backend auto-detected binaries from GitHub Releases. The `github:` backend is the successor with the same functionality.

**Declaration syntax (for migration reference):**

```toml
# OLD (deprecated)
"ubi:goreleaser/goreleaser" = "latest"
"ubi:BurntSushi/ripgrep" = { version = "latest", exe = "rg" }

# NEW (recommended)
"github:goreleaser/goreleaser" = "latest"
"github:BurntSushi/ripgrep" = { version = "latest", exe = "rg" }
```

**When to use github: vs aqua:** Prefer `aqua:` whenever the tool exists in the aqua registry (better security, checksums, progress bars). Use `github:` only for tools NOT in the aqua registry.

### 4. Backend Support for uv and pixi

**uv:** There is no dedicated `uv` backend in mise. uv is available as a tool to install via mise (using `aqua:astral-sh/uv` or the registry shorthand `uv`). Mise can install uv as a binary, but does not use uv as a backend for installing other tools. The `pipx` backend handles Python tools.

**pixi:** There is no dedicated `pixi` backend in mise. pixi is installable via mise (`mise use pixi`), but mise does not delegate tool installations to pixi. There was a GitHub discussion (#5620) about custom backend plugins which could theoretically enable a pixi backend, but none exists officially.

**This codebase's approach is correct:** uv and pixi are installed via their own installers (`curl ... | sh`) because mise's role is limited to managing their binary installation, not delegating to them. The `pipx` backend could replace some `uv tool install` calls, but the current approach gives more control.

### 5. `mise install` vs `mise use -g`

| Aspect | `mise install` | `mise use -g` |
|--------|---------------|---------------|
| Downloads tool | Yes | Yes |
| Writes to config file | No | Yes (`~/.config/mise/config.toml`) |
| Activates tool for use | No | Yes (globally) |
| When to use | Pre-populating cache, CI builds | Setting global defaults |

**Current codebase pattern:**

```bash
# install-agent-stack.sh (line 62-64)
mise install -q python@latest python@${TOOL_PYTHON_VERSION} node@latest bun@latest go@latest
mise use -g python@latest node@latest bun@latest go@latest
mise reshim
```

This is correct: `mise install` downloads both versions (including a secondary Python 3.12), then `mise use -g` activates the `latest` versions globally. The `mise install` step for `python@${TOOL_PYTHON_VERSION}` is necessary because `mise use -g` only registers `python@latest`.

### 6. `mise upgrade --yes` vs `--bump`

| Flag | Behavior | Config impact | Safety for automation |
|------|----------|--------------|----------------------|
| `--yes` | Skips confirmation prompts; upgrades within existing version constraints | Does NOT modify mise.toml version specifiers | **Safe** -- respects ranges |
| `--bump` | Upgrades to absolute latest and rewrites config | Changes `node = "20"` to `node = "22"` in mise.toml | **Risky** -- can introduce breaking major version changes |

**Current codebase** uses `mise upgrade --yes` in `macos-dev-maintenance.sh:343`, which is the **correct choice** for automated maintenance. Since the config uses `python = "latest"`, `node = "latest"`, the `--yes` flag is redundant for version ranges but necessary for trust/confirmation prompts.

**Recommendation:** `--bump` should NEVER be used in automated maintenance scripts. It should only be used interactively when you explicitly want to change version constraints.

Additional useful flags:
- `--exclude <TOOL>`: Skip specific tools during upgrade
- `--dry-run`: Preview what would change
- `--before <DATE>`: Only install versions released before a date (useful for stability)

### 7. `mise activate zsh` vs Shim PATH

| Aspect | `mise activate zsh` | Shim PATH (`mise activate --shims`) |
|--------|--------------------|------------------------------------|
| How it works | Updates PATH on every prompt display | Static shims in `~/.local/share/mise/shims` |
| Interactive shells | Full feature set: hooks, env vars, dynamic switching | Limited: no hooks, env vars only for tools |
| Non-interactive shells | Does NOT work (no prompt = no PATH update) | Works correctly |
| IDE integration | Requires IDE-specific setup | Works natively |
| Performance | Slight overhead per prompt (~100-200ms reported) | Zero overhead after initial PATH setup |
| `which` transparency | Shows real executable path | Shows shim path (obscures real binary) |

**Recommended setup for zsh:**

```bash
# ~/.zprofile (non-interactive, login shell)
eval "$(mise activate zsh --shims)"

# ~/.zshrc (interactive)
eval "$(mise activate zsh)"
```

**This codebase's approach:** `macos-dev-maintenance.sh:173` and other scripts manually set PATH with `$home/.local/share/mise/shims` first. This is the **correct approach for non-interactive scripts** -- using the shim directory directly instead of `eval "$(mise activate bash)"`. The `install-agent-stack.sh:58` uses `eval "$(mise activate bash)"` which also works since it's sourced interactively.

### 8. `mise self-update` Non-Interactive Behavior

```bash
mise self-update --yes     # Skip confirmation prompt
mise self-update --yes --no-plugins  # Also skip plugin updates
mise self-update [VERSION]  # Pin to specific version
```

**Critical caveat:** `mise self-update` is **NOT available when mise is installed via a package manager** (Homebrew, apt, etc.). It only works when installed via `curl https://mise.run | sh`.

The current `macos-dev-maintenance.sh:342` calls `mise self-update` without `--yes`. This will hang in non-interactive (launchd) contexts if mise prompts for confirmation.

**Recommendation:** Change to `mise self-update --yes` or `mise self-update --yes --no-plugins` for launchd automation.

### 9. `mise doctor` Checks and Output

`mise doctor` (alias: `mise dr`) performs installation health checks:
- Checks for missing plugins
- Validates configuration file syntax
- Verifies tool installations
- Detects PATH issues
- Identifies version conflicts

**Output options:**
- Default: Human-readable text with warnings
- `--json` / `-J`: Machine-readable JSON output
- `mise doctor path [-f/--full]`: PATH-specific diagnostics

**This codebase does not currently use `mise doctor`.** Adding it to `health-check.sh` would complement existing checks.

### 10. Trust Model for Non-Interactive Plugin Installs

Mise has a trust/untrust system for config files:
- **Trusted plugins** (first-party, mise-plugins org): Auto-install without prompts
- **Untrusted plugins**: Require explicit trust confirmation

**Non-interactive trust mechanisms:**

```toml
# ~/.config/mise/config.toml
[settings]
yes = true                            # Auto-approve all prompts
trusted_config_paths = [
  "~/work/my-projects",               # Auto-trust all configs under this path
  "~/dev/github/ray-manaloto"         # Trust this user's repos
]
```

```bash
# Environment variable
export MISE_YES=1                      # Same as yes = true
export MISE_TRUSTED_CONFIG_PATHS="$HOME/dev:$HOME/work"  # Colon-separated

# Explicit trust command
mise trust /path/to/mise.toml          # Mark a specific config as trusted
mise trust --all                       # Trust all untrusted configs
```

**Recommendation for this codebase:** Set `MISE_YES=1` in scripts that run non-interactively, or add `trusted_config_paths` to global config.

### 11. `[env]` Section: Can It Replace Shell-Level Exports?

**Yes, partially.** The `[env]` section can set `UV_NO_MANAGED_PYTHON`, `GOBIN`, and similar variables:

```toml
[env]
UV_NO_MANAGED_PYTHON = "1"
GOBIN = "{{env.HOME}}/.local/bin"
UV_CACHE_DIR = "{{env.HOME}}/Library/Caches/uv"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"

# PATH extension
_.path = ["{{env.HOME}}/.local/bin"]

# Load from dotenv
_.file = ".env"

# Unset a variable
SOME_OLD_VAR = false
```

**Limitations:**
- `[env]` variables are only active when mise is activated (via `mise activate` or shims). They are NOT available in raw shell contexts without mise.
- When using shims, env vars are "only available to mise tools" -- not to your general shell session.
- For global env vars that must be available everywhere (including before mise loads), shell-level exports in `.zshrc`/`.zprofile` are still needed.

**Conclusion for this codebase:** `UV_NO_MANAGED_PYTHON=1` and `GOBIN` can live in `[env]` for tool-invocation contexts, but should ALSO remain as shell exports for scripts that run before mise is activated (like `macos-dev-maintenance.sh` which sets its own PATH).

### 12. Lock File Format and Reproducibility

**Enabling:**
```toml
[settings]
lockfile = true    # Read/write mise.lock automatically
locked = true      # STRICT: fail if lockfile is incomplete for current platform
```

**File format (TOML):**
```toml
[[tools.node]]
version = "22.11.0"
backend = "core:node"

[tools.node.platforms.macos-arm64]
checksum = "sha256:abc123..."
size = 45678901
url = "https://nodejs.org/dist/v22.11.0/node-v22.11.0-darwin-arm64.tar.xz"

[[tools.python]]
version = "3.12.8"
backend = "core:python"
```

**Backend support levels:**

| Backend | version | checksum | size | url |
|---------|---------|----------|------|-----|
| aqua | Yes | Yes | Yes | Yes |
| http | Yes | Yes | Yes | Yes |
| github | Yes | Yes | Yes | Yes |
| core (some) | Yes | Yes | - | - |
| asdf | Yes | - | - | - |
| npm, cargo, pipx | Yes | - | - | - |

**Workflow:**
1. Lead developer runs `mise install` (generates/updates `mise.lock`)
2. `mise.lock` is committed to Git
3. Team members get exact same versions
4. `mise lock --platform linux-x64,macos-arm64` pre-populates for CI platforms

**Local lockfile:** `mise.local.toml` uses `mise.local.lock` (not committed).

**Recommendation:** Enable `lockfile = true` in global config for reproducibility. Do NOT enable `locked = true` in development (only in CI for strict enforcement).

### 13. Default Registry vs Aqua Registry Lookup Behavior

**Resolution pipeline (in order):**

1. **Environment variable override:** `MISE_BACKENDS_<TOOL>` (SHOUTY_SNAKE_CASE) -- becomes sole backend
2. **Registry lookup:** mise's built-in registry maps short names to backend lists
3. **Backend type filtering:** Removes disabled backends (`disable_backends` setting)
4. **Platform filtering:** Removes backends not supporting current OS/arch
5. **Experimental filtering:** Removes experimental backends unless `experimental = true`
6. **First match wins:** First remaining backend is used

**Backend priority in registry entries (typical order):**
1. `core:` -- Native mise implementations (python, node, go, rust, bun, etc.)
2. `aqua:` -- Aqua registry tools (most CLI tools)
3. `asdf:` -- ASDF plugin fallback
4. `vfox:` -- Vfox plugin system

**Key insight:** Core runtimes (python, node, go, rust, bun) use `core:` backends, which provide the deepest integration (env vars, version detection, post-install hooks). CLI tools (aws-cli, terraform, kubectl) typically use `aqua:` backends.

**The aqua registry is baked into the mise binary at compile time.** When you write `mise use kubectl`, the registry resolves it to `aqua:kubernetes/kubectl` without any network call. Fresh registry data comes with each mise release.

### 14. Current Breaking Changes Relevant to This Codebase

**Active/Upcoming:**

1. **Idiomatic version files default change (2025.10.0+):** mise no longer defaults to reading `.python-version`, `.node-version`, `.ruby-version` files. Must explicitly enable per-tool:
   ```bash
   mise settings add idiomatic_version_file_enable_tools python
   mise settings add idiomatic_version_file_enable_tools node
   ```
   **Impact on this codebase:** Low -- this repo uses `config.toml`, not idiomatic version files.

2. **ubi backend deprecated:** Replace `ubi:` with `github:` prefix. **Impact:** None -- this codebase does not use ubi.

3. **Settings namespace migration (pre-2026.8.0):** Nine flat `task_*` settings moving to `task.*` namespace. Old names work with deprecation warnings until 2026.8.0. **Impact:** Low -- this codebase doesn't use task settings.

4. **`mise self-update` without `--yes`:** In automated contexts, this can hang waiting for confirmation. **Impact:** **HIGH** -- `macos-dev-maintenance.sh:342` runs `mise self-update` without `--yes`.

5. **Lockfile enforcement tightening (v2026.2.23):** "Stricter lockfile enforcement" in latest release. If `lockfile = true` is enabled and `locked = true`, missing platform entries will cause failures. **Impact:** None currently (lockfiles not enabled), but relevant when adopting lockfiles.

---

## Current Script Audit

| Script | Function/Section | Finding | Action Needed |
|--------|-----------------|---------|---------------|
| `macos-dev-maintenance.sh` | `update_mise()` L342 | `mise self-update` lacks `--yes`; will hang in launchd | Add `--yes` flag |
| `macos-dev-maintenance.sh` | `update_mise()` L343 | `mise upgrade --yes` is correct for automation | None |
| `macos-dev-maintenance.sh` | `ensure_mise_global()` L222 | `mise use -g --yes python@latest node@latest bun@latest go@latest rust@latest` -- redundant with upgrade | Consider removing if upgrade handles it |
| `macos-dev-maintenance.sh` | `setup_path()` L173 | Hardcodes mise shim/bin paths -- correct for non-interactive | None |
| `macos-dev-maintenance.sh` | L4 | `UV_NO_MANAGED_PYTHON` set as shell export | Keep; needed before mise activates |
| `install-agent-stack.sh` | `ensure_mise()` L58 | Uses `eval "$(mise activate bash)"` | Correct for interactive scripts |
| `install-agent-stack.sh` | `ensure_runtimes()` L62-64 | `mise install` + `mise use -g` + `mise reshim` pattern | Correct but could use `--yes` for non-interactive |
| `install-agent-stack.sh` | `ensure_runtimes()` L63 | `mise use -g` does not include `rust@latest` (but maintenance script does) | Add `rust@latest` for consistency |
| `install-agent-stack.sh` | L62 | Installs `python@${TOOL_PYTHON_VERSION}` separately via `mise install` | Correct; secondary version for tooling |
| `install-aws-k8s-tools.sh` | `install_with_mise()` L64-66 | `mise install -q` + `mise use -g` + `mise reshim` per tool | Correct but chatty; consider batching |
| `health-check.sh` | `main()` L214 | Checks `mise` command exists but does not run `mise doctor` | Add `mise doctor` check |
| `tools-inventory.sh` | L5-6 | Uses `mise ls --installed` for inventory | Correct |
| Multiple scripts | `setup_path()` | PATH duplicated across 8+ scripts | Extract to shared library |
| `docs/mise-config.md` | Example config | Uses `python = "latest"` without lockfile | Add `[settings] lockfile = true` |
| No script | Missing | No `mise trust` call for global config | Add trust for `~/.config/mise/config.toml` or set `MISE_YES=1` |

---

## Recommended Patterns

### Before: Current global config

```toml
# ~/.config/mise/config.toml
[tools]
python = "latest"
node = "latest"
bun = "latest"
go = "latest"
rust = "latest"

[env]
GITHUB_USER = "your_username"
UV_NO_MANAGED_PYTHON = "1"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"
```

### After: Recommended global config

```toml
# ~/.config/mise/config.toml
min_version = "2025.1.0"

[settings]
lockfile = true                    # Enable lockfile for reproducibility
yes = true                         # Non-interactive (safe for automation)
# locked = false                   # Only enable in CI for strict enforcement

[tools]
python = "latest"                  # Resolved version pinned in mise.lock
node = "lts"                       # LTS is safer than "latest" for tooling
bun = "latest"
go = "latest"
rust = "latest"

# CLI tools via aqua (no plugins needed)
# "aqua:aws/aws-cli" = { version = "latest", symlink_bins = true }

[env]
UV_NO_MANAGED_PYTHON = "1"
GOBIN = "{{env.HOME}}/.local/bin"
UV_CACHE_DIR = "{{env.HOME}}/Library/Caches/uv"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"
_.path = ["{{env.HOME}}/.local/bin"]
```

### Before: Maintenance script mise update

```bash
mise self-update || return 1
mise upgrade --yes || return 1
mise reshim || true
```

### After: Safe non-interactive mise update

```bash
mise self-update --yes --no-plugins || return 1
mise upgrade --yes || return 1
mise reshim || true
```

### Before: Duplicated PATH setup (in 8+ scripts)

```bash
setup_path() {
  local home="${HOME:-/Users/rmanaloto}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:..."
}
```

### After: Shared PATH library

```bash
# scripts/lib/path-setup.sh
setup_mde_path() {
  local home="${HOME:-$(id -un | xargs -I{} echo /Users/{})}"
  export PATH="$home/.local/share/mise/shims:$home/.local/share/mise/bin:$home/.local/bin:$home/.bun/bin:$home/.pixi/bin:/opt/homebrew/opt/curl/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}
```

---

## Implementation-Ready Decisions

1. **Add `--yes` to `mise self-update`** in `macos-dev-maintenance.sh:342` to prevent launchd hangs. This is a one-line fix with zero risk.

2. **Enable lockfile** (`lockfile = true` in global config) to get version pinning without changing any existing workflow. Commit `mise.lock` to this repo if a project-level `mise.toml` is added.

3. **Do NOT adopt `--bump` for automation.** Keep `--yes` only. `--bump` is for intentional manual version migrations.

4. **Keep `UV_NO_MANAGED_PYTHON=1` as both shell export AND `[env]` entry.** Shell export covers pre-mise scripts; `[env]` covers tool-invocation contexts.

5. **Consider `node = "lts"` instead of `node = "latest"`** for global config. LTS is more stable for tooling that depends on Node. bun remains `latest` since it's the preferred JS runtime.

6. **Add `mise doctor` to `health-check.sh`** for comprehensive installation diagnostics. Use `mise doctor --json` for machine-parseable output if needed.

7. **Prefer aqua backend for CLI tools.** When adding new CLI tools to mise management (aws-cli, kubectl, terraform, helm, etc.), prefer `aqua:` over `asdf:` for security and simplicity. Check availability with `mise registry | grep <tool>`.

8. **Extract shared `setup_path()` into `scripts/lib/path-setup.sh`** and source from all scripts. The current duplication across 8+ scripts creates maintenance burden.

9. **Do NOT create a project-level `mise.toml` in this repo yet.** This is a configuration/scripts repo, not a software project. The global `~/.config/mise/config.toml` is the appropriate location.

10. **Set `MISE_YES=1` or `settings.yes = true`** for non-interactive contexts (launchd, CI). This covers trust prompts, plugin installs, and self-update confirmations.

---

## Open Questions / Caveats

- **mise self-update when installed via Homebrew:** If mise is installed via brew, `mise self-update` is unavailable. The maintenance script should detect installation method and skip self-update for brew-installed mise (use `brew upgrade mise` instead).

- **aqua registry freshness:** The aqua registry is baked into the mise binary at compile time. Updating mise itself is required to get new aqua registry entries. This means `mise self-update` frequency affects which tool versions are discoverable via aqua.

- **Shim performance in tight loops:** For scripts that invoke mise-managed tools thousands of times in a loop, shims add per-invocation overhead. Consider `mise exec` or `mise activate` in such scripts.

- **`[env]` and launchd:** Environment variables set in `[env]` require mise activation. launchd jobs that source scripts without activating mise will not see these variables. Shell-level exports in the job script remain necessary.

- **Python dual-version management:** The current pattern of `mise install python@3.12` alongside `mise use -g python@latest` works but the secondary version is only accessible via `mise where python@3.12`. Consider whether `mise use -g python@3.12` as a secondary version would be cleaner (mise supports multiple global versions).

- **Missing `rust@latest` in install-agent-stack.sh:** `ensure_runtimes()` installs python, node, bun, go but not rust. The maintenance script's `ensure_mise_global()` does include rust. This inconsistency should be resolved.

---

## Cross-References

| Finding | Affects Domain |
|---------|---------------|
| #7 (activate vs shims) | Shell/UX team (oh-my-zsh config, .zprofile/.zshrc split) |
| #8 (self-update --yes) | Maintenance/Validation team (launchd job reliability) |
| #11 ([env] section) | Shell/UX team (UV_NO_MANAGED_PYTHON dual-location strategy) |
| #4 (uv/pixi not backends) | Tool Interactions team (confirms uv/pixi remain independent installers) |
| #14 (breaking changes) | Maintenance team (idiomatic version file default, self-update prompts) |
| #12 (lockfile) | All teams (reproducibility strategy affects CI, onboarding, drift detection) |
| Shared PATH extraction | All scripts (maintenance, install, verification, health-check) |
| #6 (upgrade --yes safety) | Maintenance team (validates current approach, warns against --bump) |
| #10 (trust model) | Shell/Secrets team (MISE_YES=1 for non-interactive, trusted_config_paths) |
| #2 (aqua backend for CLI tools) | Brew Boundary team (aqua can replace some brew-installed CLI tools) |
