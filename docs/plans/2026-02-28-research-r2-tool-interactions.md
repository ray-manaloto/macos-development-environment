# Research Report R2: Tool Manager Interactions (uv, bun, pixi)

## Sources Consulted

- [uv Tools documentation](https://docs.astral.sh/uv/concepts/tools/) -- tool upgrade pinning behavior
- [uv Storage reference](https://docs.astral.sh/uv/reference/storage/) -- cache dir defaults
- [uv Settings reference](https://docs.astral.sh/uv/reference/settings/) -- python-downloads values
- [uv self update warning issue #13221](https://github.com/astral-sh/uv/issues/13221) -- exact error text
- [uv cache dir macOS issue #8626](https://github.com/astral-sh/uv/issues/8626) -- XDG switch confirmation
- [uv Caching concepts](https://docs.astral.sh/uv/concepts/cache/) -- cache behavior
- [Bun installation docs](https://bun.sh/docs/installation) -- upgrade and global install behavior
- [Bun lang page in mise docs](https://mise.jdx.dev/lang/bun.html) -- mise-managed bun warnings
- [bun upgrade failure issue #11523](https://github.com/oven-sh/bun/issues/11523) -- upgrade failure patterns
- [Pixi self-update reference](https://pixi.prefix.dev/latest/reference/cli/pixi/self-update/) -- self-update options
- [Pixi global install reference](https://pixi.prefix.dev/latest/reference/cli/pixi/global/install/) -- -e flag semantics
- [Pixi packaging page](https://prefix-dev.github.io/pixi/v0.33.0/packaging/) -- PIXI_SELF_UPDATE_DISABLED_MESSAGE
- [Pixi self-update discussion #2071](https://github.com/prefix-dev/pixi/discussions/2071) -- external management behavior
- [mise aqua backend docs](https://mise.jdx.dev/dev-tools/backends/aqua.html) -- aqua registry compilation
- [mise registry](https://mise.jdx.dev/registry.html) -- tool backend lookup
- [mise Python cookbook](https://mise.jdx.dev/mise-cookbook/python.html) -- uv integration
- [mise pipx backend](https://mise.jdx.dev/dev-tools/backends/pipx.html) -- uvx fallback
- [mise pixi global backend discussion #4650](https://github.com/jdx/mise/discussions/4650) -- feature request
- [uv + mise pipx backend discussion #4377](https://github.com/jdx/mise/discussions/4377) -- integration patterns
- [pixi vs uv comparison (Jacob Tomlinson, 2025)](https://jacobtomlinson.dev/posts/2025/python-package-managers-uv-vs-pixi/) -- tool positioning
- [Adopting uv in pixi (prefix.dev blog)](https://prefix.dev/blog/uv_in_pixi) -- pixi using uv internally
- Local scripts: `scripts/macos-dev-maintenance.sh`, `scripts/install-agent-stack.sh`, `scripts/install-langchain-cli-tools.sh`
- Local doc: `docs/toolchain-precedence.md`

---

## Key Findings (Numbered)

### 1. uv self update failure under mise-managed path -- exact error and detection

**Exact error message:**
```
warning: Self-update is only available for uv binaries installed via the standalone installation scripts.
If you installed uv with pip, brew, or another package manager, update uv with `pip install --upgrade`, `brew upgrade`, or similar.
```

**Detection mechanism:** uv checks whether the running binary was installed via its own standalone installer script (`curl -LsSf https://astral.sh/uv/install.sh | sh`). The detection is compiled into the binary -- it checks its install location against known standalone paths (typically `~/.local/bin/uv` or `~/.cargo/bin/uv`). When the binary path falls outside those expected locations (e.g., inside `~/.local/share/mise/installs/uv/...`), `uv self update` emits the warning and exits without updating.

**Important nuance:** This is labeled a "warning" but is functionally an error (issue #13221). The command does nothing and exits. Scripts should treat the exit code as a failure indicator.

**Current script behavior:** `macos-dev-maintenance.sh` guards `uv self update` based on path prefix:
```bash
case "$uv_path" in
  /opt/homebrew/*|/usr/local/*)
    ;;  # skip self-update for Homebrew-installed uv
  *)
    uv self update || return 1
    ;;
esac
```
This guard does NOT detect mise-managed uv. If uv is at `~/.local/share/mise/installs/uv/*/bin/uv`, the script calls `uv self update`, which fails with the warning above.

### 2. Reliable detection of whether uv is mise-managed vs standalone

**Recommended detection pattern:**
```bash
uv_path="$(command -v uv)"
case "$uv_path" in
  "$HOME/.local/share/mise/installs/uv/"*|"$HOME/.local/share/mise/shims/"*)
    # mise-managed: skip uv self update, use mise upgrade instead
    ;;
  /opt/homebrew/*|/usr/local/*)
    # Homebrew-managed: use brew upgrade uv
    ;;
  "$HOME/.local/bin/uv"|"$HOME/.cargo/bin/uv")
    # standalone installer: uv self update is safe
    uv self update
    ;;
  *)
    # unknown: attempt self-update, ignore failure
    uv self update || true
    ;;
esac
```

**Alternative (more robust):** Check if mise is aware of uv as a managed tool:
```bash
if mise ls uv 2>/dev/null | grep -q '^uv'; then
  # mise-managed
fi
```

### 3. uv tool upgrade --all pinning behavior

`uv tool upgrade --all` upgrades every installed tool to the latest version that **satisfies the original version constraints** from the `uv tool install` command.

- If a tool was installed with `uv tool install black >=23,<24`, then `uv tool upgrade --all` upgrades Black within `>=23,<24`.
- If a tool was installed without constraints (e.g., `uv tool install black`), it upgrades to the absolute latest.
- Settings from the install command are retained: `--prerelease allow`, `--python`, etc.
- To change constraints, you must `uv tool install` again (reinstall, not upgrade).

**Implication for scripts:** The current `uv tool upgrade --all` call at line 399 of `macos-dev-maintenance.sh` is correct and safe. It will not break pinned tools.

### 4. UV_NO_MANAGED_PYTHON documentation and correct values

**Setting name:** `python-downloads` (config file) / `UV_PYTHON_DOWNLOADS` (env var)

The env var `UV_NO_MANAGED_PYTHON` is an **older, unofficial shorthand** that is not part of uv's documented API. The official mechanism is:

| Config key | Env var | Values |
|---|---|---|
| `python-downloads` | `UV_PYTHON_DOWNLOADS` | `"automatic"` (default), `"manual"`, `"never"` |

However, the scripts in this repo use `UV_NO_MANAGED_PYTHON=1`, which works because uv treats any truthy `UV_NO_MANAGED_PYTHON` value as equivalent to `python-downloads = "never"`. This is a **legacy compatibility shim** -- uv continues to honor it but it is undocumented.

**Recommendation:** Migrate to `UV_PYTHON_DOWNLOADS=never` for forward compatibility. The current `UV_NO_MANAGED_PYTHON=1` may stop working in a future uv release.

### 5. bun upgrade failure under mise-managed path

**Behavior:** When bun is managed by mise (binary lives at `~/.local/share/mise/installs/bun/<version>/bin/bun`), `bun upgrade` attempts to replace the binary in-place. This fails because:
1. mise installs each bun version in its own directory
2. `bun upgrade` downloads a new binary and tries to write to the same location
3. The write may succeed but mise's shim still points at the old version directory
4. mise is unaware of the change, causing version tracking drift

**mise docs explicitly warn:** "Avoid using `bun upgrade` to upgrade bun as mise will not be aware of the change."

**Current script behavior:** `macos-dev-maintenance.sh` lines 349-364 correctly guard against this:
```bash
bun_path="$(command -v bun)"
case "$bun_path" in
  "$HOME/.local/share/mise/installs/bun/"*)
    ;;  # skip bun upgrade for mise-managed bun
  *)
    bun upgrade || return 1
    ;;
esac
```
This is correct. However, `install-langchain-cli-tools.sh` line 53 calls `bun upgrade || true` unconditionally in `ensure_bun()`, which is a bug when bun is mise-managed.

### 6. bun add -g install location when bun is mise-managed

**Default behavior:** `bun add -g` installs packages to `~/.bun/install/global/node_modules/` and creates executable symlinks in `~/.bun/bin/`.

**When bun is mise-managed:** The `bun` binary is at `~/.local/share/mise/installs/bun/<version>/bin/bun`, but `bun add -g` still installs to `~/.bun/install/global/`. This means:
- Global packages are NOT version-isolated per bun version
- `~/.bun/bin` must be on PATH (the current `setup_path()` includes `$HOME/.bun/bin`)
- Switching bun versions via mise does NOT affect globally installed packages
- This is actually desirable: global CLI tools persist across bun version switches

**Risk:** If `~/.bun/bin` is not on PATH or comes after mise shims, globally installed bun tools may not be found.

### 7. pixi self-update behavior when pixi is mise-managed

**Pixi self-update** is a compile-time feature flag. When pixi is packaged by an external package manager (e.g., brew, conda, mise), the packager typically builds pixi with self-update **disabled**.

When self-update is disabled and a user runs `pixi self-update`:
- An error message is displayed
- The message can be customized at build time via the `PIXI_SELF_UPDATE_DISABLED_MESSAGE` env var

**When pixi is installed via the standalone installer** (`curl -fsSL https://pixi.sh/install.sh | bash`), self-update works normally. This is the most common case in this repo's scripts.

**Current script behavior:** `macos-dev-maintenance.sh` line 419 calls `pixi self-update || return 1` unconditionally. If pixi was installed standalone (typical case via `ensure_pixi()`), this works. If pixi came from conda or brew, it would fail and halt the maintenance script.

Similarly, `install-agent-stack.sh` line 83 calls `pixi self-update` unconditionally in `ensure_pixi()`.

**Detection pattern:**
```bash
if pixi self-update --dry-run 2>&1 | grep -qi "disabled\|not available"; then
  # self-update is disabled (packager-built pixi)
else
  pixi self-update
fi
```

### 8. pixi global install -e environment flag semantics

The `-e` / `--environment <ENVIRONMENT>` flag groups packages into a named global environment. Key semantics:

- **Without -e:** Each package gets its own isolated environment
- **With -e my-env:** All packages share one environment named `my-env`, allowing them to see each other's dependencies
- The environment persists at `~/.pixi/envs/<environment-name>/`
- `--pinning-strategy` values: `semver`, `minor`, `major`, `latest-up`, `exact-version`, `no-pin`

**Current script usage:** Both `install-agent-stack.sh` and `install-langchain-cli-tools.sh` use `-e "$PIXI_ENV"` (defaulting to `agent-stack` and `langchain-cli-tools` respectively), with `--pinning-strategy no-pin`. This is correct for tools that should always resolve to latest.

### 9. Stable mise backends for uv and pixi

**uv in mise registry:**
- Backend: `aqua:astral-sh/uv` (the aqua registry is compiled into mise at release time)
- Install: `mise use -g uv@latest` or `mise install uv@<version>`
- Known issue: attestation failures for some versions (e.g., uv 0.9.11 reported in astral-sh/uv#16871)
- The aqua backend downloads the prebuilt binary from GitHub Releases

**pixi in mise registry:**
- Backend: `aqua:prefix-dev/pixi` (also via aqua registry)
- Install: `mise use -g pixi@latest`
- No dedicated `pixi global` backend in mise (feature requested in jdx/mise#4650)

**Note:** When uv or pixi are mise-managed, their `self update` commands should be skipped (use `mise upgrade` instead).

### 10. pixi as intermediary installer pattern: still recommended or superseded by uv?

**Current status (2025):** pixi and uv serve different niches and are converging rather than one superseding the other.

| Dimension | uv | pixi |
|---|---|---|
| **Best for** | Pure Python packages (PyPI) | Conda-forge + PyPI hybrid |
| **Global tools** | `uv tool install` | `pixi global install` |
| **Task runner** | Not built-in | Built-in `pixi run` |
| **PyPI backend** | Native | Uses uv internally since 2024 |
| **Speed** | Extremely fast | Fast (uses uv for pip) |

**For this repo's use case** (installing Python CLI tools globally):
- `uv tool install` is the preferred path for pure-Python tools
- `pixi global install -e` remains useful as a fallback or for packages with compiled conda dependencies
- The current `install_python_tool()` cascade (pixi first, then uv, then pip) in `install-agent-stack.sh` could be inverted to try uv first for speed, falling back to pixi for packages that need conda deps

**pixi is NOT superseded.** It remains the right choice when conda-forge packages are needed (e.g., compiled scientific packages). For pure-Python CLI tools, uv is faster and simpler.

### 11. UV_CACHE_DIR default on macOS

**Documented default:** `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv` on macOS and Linux.

**History:** uv originally used `$HOME/Library/Caches/uv` on macOS (the Apple convention). In PR #5806 they switched to XDG conventions (`$HOME/.cache/uv`) for cross-platform consistency. The documentation was updated (issue #8626).

**Current repo behavior:** Both `macos-dev-maintenance.sh` (line 174) and `install-agent-stack.sh` (line 5) set:
```bash
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"
```
This overrides uv's default of `$HOME/.cache/uv` and places the cache in macOS's conventional `Library/Caches/` directory. This is **intentional and correct** for this repo -- it puts caches where macOS users expect them and where macOS cache-cleaning tools can find them.

**Verify with:** `uv cache dir` (shows the active cache directory).

---

## Current Script Audit

| Script | Function/Section | Finding | Action Needed |
|---|---|---|---|
| `macos-dev-maintenance.sh` | `update_uv()` L384-401 | Guards `uv self update` against Homebrew paths only; does NOT guard against mise-managed uv | Add mise path detection: `"$HOME/.local/share/mise/installs/uv/"*` |
| `macos-dev-maintenance.sh` | `update_bun()` L349-365 | Correctly skips `bun upgrade` for mise-managed bun | No change needed |
| `macos-dev-maintenance.sh` | `update_pixi()` L415-422 | Calls `pixi self-update` unconditionally; fails if pixi was externally packaged | Add guard or `|| true` fallback |
| `macos-dev-maintenance.sh` | `UV_NO_MANAGED_PYTHON` L4 | Uses undocumented env var name | Migrate to `UV_PYTHON_DOWNLOADS=never` |
| `macos-dev-maintenance.sh` | `UV_CACHE_DIR` L174 | Sets to `$HOME/Library/Caches/uv` (macOS convention, overriding uv default of `$HOME/.cache/uv`) | Intentional; document the override reason |
| `install-agent-stack.sh` | `ensure_uv()` L67-77 | Calls `uv self update` unconditionally; fails if mise-managed | Add path guard similar to `update_bun()` |
| `install-agent-stack.sh` | `ensure_pixi()` L79-89 | Calls `pixi self-update` unconditionally | Add guard or `|| true` fallback |
| `install-agent-stack.sh` | `install_python_tool()` L104-134 | Tries pixi first, then uv, then pip; pixi may be slower for pure-Python packages | Consider inverting to uv-first for speed |
| `install-langchain-cli-tools.sh` | `ensure_bun()` L51-65 | Calls `bun upgrade` unconditionally; breaks when bun is mise-managed | Add mise path guard matching `macos-dev-maintenance.sh` pattern |
| `install-langchain-cli-tools.sh` | `UV_NO_MANAGED_PYTHON` L1 | Uses undocumented env var | Migrate to `UV_PYTHON_DOWNLOADS=never` |
| `docs/toolchain-precedence.md` | uv section | States "`uv self update` (only if not Homebrew installed)" but does not mention mise-managed guard needed | Update doc to list mise-managed as also needing guard |

---

## Recommended Patterns

### Pattern 1: Universal uv self-update guard

```bash
update_uv() {
  if ! have_cmd uv; then
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
    *)
      uv self update || return 1
      ;;
  esac

  uv tool upgrade --all || return 1
  return 0
}
```

### Pattern 2: Universal bun upgrade guard

```bash
ensure_bun_current() {
  if ! have_cmd bun; then
    return 1
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

### Pattern 3: pixi self-update with fallback

```bash
update_pixi() {
  if ! have_cmd pixi; then
    return 0
  fi

  # pixi self-update is a compile-time feature; may be disabled in packaged builds
  if ! pixi self-update 2>/dev/null; then
    log "pixi self-update unavailable (likely externally managed); skipping."
  fi

  pixi global update || return 1
  return 0
}
```

### Pattern 4: UV_PYTHON_DOWNLOADS migration

```bash
# Replace this:
export UV_NO_MANAGED_PYTHON="${UV_NO_MANAGED_PYTHON:-1}"

# With this:
export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"
```

### Pattern 5: Tool install cascade (uv-first)

```bash
install_python_tool() {
  local pkg="$1"

  # Try uv first (fastest for pure-Python packages)
  if command -v uv >/dev/null 2>&1; then
    if uv tool install --upgrade "$pkg" 2>/dev/null; then
      return 0
    fi
  fi

  # Fall back to pixi for conda-forge packages
  if command -v pixi >/dev/null 2>&1; then
    if pixi global install -e "$PIXI_ENV" --pinning-strategy no-pin "$pkg" 2>/dev/null; then
      return 0
    fi
  fi

  # Last resort: pip
  if command -v pip >/dev/null 2>&1; then
    pip install --upgrade "$pkg"
    return $?
  fi

  return 1
}
```

---

## Implementation-Ready Decisions

1. **Add mise-managed path guard to `update_uv()`** in `macos-dev-maintenance.sh`. The case pattern needs `"$HOME/.local/share/mise/installs/uv/"*` alongside the existing Homebrew guard.

2. **Fix `ensure_bun()` in `install-langchain-cli-tools.sh`** to match the guard pattern already used in `macos-dev-maintenance.sh`'s `update_bun()`.

3. **Add `|| true` fallback to `pixi self-update`** calls in both `macos-dev-maintenance.sh` and `install-agent-stack.sh`, or use the `2>/dev/null` pattern.

4. **Migrate `UV_NO_MANAGED_PYTHON=1` to `UV_PYTHON_DOWNLOADS=never`** across all three scripts. The old env var is undocumented and may be removed in a future uv release.

5. **Keep `UV_CACHE_DIR=$HOME/Library/Caches/uv`** as the explicit override. This is intentional -- it places caches where macOS expects them. Add a comment explaining the override.

6. **Do NOT change the pixi-then-uv cascade in `install-agent-stack.sh`** without testing. The pixi-first approach ensures conda-compiled packages work. If speed is a concern, the cascade can be inverted for tools known to be pure-Python.

7. **Update `docs/toolchain-precedence.md`** to document the mise-managed uv/pixi/bun guards.

---

## Open Questions / Caveats

1. **uv self-update detection mechanism is undocumented.** The exact heuristic uv uses to determine "standalone installer" vs "external" is not in the official docs. It appears to be a compiled-in path check but could change in a future release.

2. **UV_NO_MANAGED_PYTHON longevity.** The env var works today but is not in uv's official environment variable reference. Migration to `UV_PYTHON_DOWNLOADS=never` should be tested to confirm identical behavior before deploying.

3. **pixi self-update compile flag.** If pixi is installed via `curl -fsSL https://pixi.sh/install.sh | bash` (as in `ensure_pixi()`), self-update should be enabled. But if a user later installs pixi via `brew install pixi` or `mise install pixi`, the replacement binary may have self-update disabled. The script cannot know which build it is running without attempting `pixi self-update`.

4. **mise-managed uv attestation failures.** When mise installs uv via the aqua backend, recent uv versions (e.g., 0.9.11) have triggered GitHub attestation verification failures. This is a transient issue in the uv release process, not a mise bug.

5. **bun global install persistence.** Global packages in `~/.bun/install/global/` are NOT tied to a specific bun version. Upgrading bun via mise to a new major version could theoretically break global packages compiled against the old bun version. In practice, pure-JS packages are unaffected.

6. **pixi global backend for mise.** A feature request exists (jdx/mise#4650) to add `pixi global` as a mise backend. If implemented, this would allow mise to manage pixi-installed tools, adding another layer to the precedence model.

---

## Cross-References

- **R1 (mise core):** This report's findings about mise-managed path detection directly feed into the mise config.toml backend configuration decisions.
- **R3 (reference repos):** The dotfiles repos should be checked for how they handle the same uv/bun/pixi self-update conflicts.
- **R4 (shell/secrets):** PATH ordering in `setup_path()` determines which binary wins when multiple install methods coexist.
- **R5 (brew boundary):** The Homebrew guards in `update_uv()` relate to the brew boundary hardening work.
- **toolchain-precedence.md:** This doc needs updates to reflect the mise-managed guards documented here.
- **Team A spec (mise core):** The `UV_PYTHON_DOWNLOADS` migration is a cross-cutting concern that should be part of the modernization rollout.
