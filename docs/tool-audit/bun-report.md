# Bun Tool Audit Report

Generated: 2026-02-28

## 1. Overview

Bun serves as the preferred JavaScript tooling runtime in this macOS development
environment. It is used primarily as a **package manager** for installing global
Node/JS CLI tools (via `bun add -g`), and mise is configured to use bun as its
npm backend (`package_manager = "bun"` in mise settings). Bun is not used as a
general-purpose application runtime in this repo -- there are no project-level
`bun run` or `bun build` invocations.

Bun sits at position #2 in the toolchain precedence model (after mise shims,
before pixi and uv).

## 2. Installation Method

**Dual installation detected -- mise-managed is the active runtime.**

| Install Location | Type | Version | Active in PATH |
|---|---|---|---|
| `~/.local/share/mise/installs/bun/1.3.10/bin/bun` | mise-managed | 1.3.10 | Yes (via mise shims) |
| `~/.bun/bin/bun` | Standalone (original installer) | older binary (Jan 12 build) | Shadowed by mise |

The mise global config (`~/.config/mise/config.toml`) declares `bun = "latest"`,
making mise the authoritative version manager. The `which bun` resolves to
`~/.local/share/mise/installs/bun/1.3.10/bin/bun` because mise shims appear
earlier in PATH than `~/.bun/bin`.

The standalone `~/.bun/bin/bun` binary (57 MB, Mach-O arm64, dated Jan 12) is a
leftover from bun's own installer. It is still present on disk but shadowed. The
`~/.bun/bin` directory is included in PATH (position 4) for the global packages
it hosts, not for the bun binary itself.

Mise also has an older version (1.3.8) still installed alongside 1.3.10.

## 3. Global Packages

All global JS/Node packages are installed into `~/.bun/install/global/` and
symlinked into `~/.bun/bin/`. There are 25 global packages (2609 transitive
dependencies):

### Installed via `scripts/install-agent-stack.sh`

| Package | Version | Description |
|---|---|---|
| `@anthropic-ai/claude-code` | 2.1.63 | Claude Code CLI |
| `@openai/codex` | 0.106.0 | OpenAI Codex CLI |
| `@google/gemini-cli` | 0.31.0 | Google Gemini CLI |
| `openwork` | 0.2.0 | OpenWork CLI |
| `create-agent-chat-app` | 0.1.6 | LangChain chat app scaffold |
| `@modelcontextprotocol/inspector` | 0.21.1 | MCP Inspector |

### Installed via `scripts/install-langchain-cli-tools.sh`

| Package | Version | Description |
|---|---|---|
| `create-langchain-integration` | 0.0.12 | LangChain integration scaffold |
| `create-langgraph` | 1.1.5 | LangGraph project scaffold |
| `@langchain/langgraph-checkpoint-validation` | 1.0.9 | Checkpoint validation |
| `@langchain/langgraph-cli` | 1.1.14 | LangGraph JS CLI |
| `@langchain/langgraph-ui` | 1.1.14 | LangGraph UI CLI |
| `deepagents-cli` | 0.0.16 | DeepAgents CLI |

### Installed manually or by other means

| Package | Version | Description |
|---|---|---|
| `@claude-flow/cli` | 3.0.2 | Claude Flow orchestration |
| `claude-flow` | 3.0.0-alpha.152 | Claude Flow (alpha) |
| `@augmentcode/auggie` | 0.15.0 | Augment Code CLI |
| `@playwright/cli` | 0.1.0 | Playwright CLI |
| `@tauri-apps/cli` | 2.10.0 | Tauri desktop app CLI |
| `agent-browser` | 0.9.1 | Agent Browser |
| `awesome-ai` | 0.1.0-beta.7 | Awesome AI CLI |
| `opencode-ai` | 1.1.53 | OpenCode AI |
| `opencode` | (git) | OpenCode (git install) |
| `pyright` | 1.1.408 | Python type checker |
| `typescript` | 5.9.3 | TypeScript compiler |
| `typescript-language-server` | 5.1.3 | TS LSP server |
| `yaml-cli` | 1.1.8 | YAML CLI tool |

### Cleanup note

The `claude` and `gemini` symlinks in `~/.bun/bin/` are explicitly removed by
cleanup functions in both `install-agent-stack.sh` and
`macos-dev-maintenance.sh` to prevent conflicts with wrapper scripts in
`~/.oh-my-zsh/custom/bin/` and `~/.local/bin/`.

## 4. Completions Strategy

**Current state: old approach still in place; new fpath approach not yet wired.**

| Item | Status |
|---|---|
| `~/.bun/_bun` (completions file) | Exists, 37 KB |
| `~/.oh-my-zsh/custom/completions/_bun` (fpath symlink) | Missing |
| `source "$BUN_INSTALL/_bun"` in shell config | Not present (removed) |

The `macos-env.zsh` template contains a comment documenting the intended new
approach:

```
# Bun completions: symlink ~/.bun/_bun to ~/.oh-my-zsh/custom/completions/_bun
# (fpath-based loading avoids sourcing 37KB on every shell startup)
```

However, neither the old `source` line nor the new `_bun` symlink is in place.
The `~/.oh-my-zsh/custom/completions/` directory exists but contains only
`_openspec` entries. **Bun shell completions are effectively disabled.**

### Recommended fix

```bash
ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun
```

This would enable fpath-based autoloading via oh-my-zsh without the 37 KB
`source` penalty on every shell startup.

## 5. Environment Variables

### BUN_INSTALL

Set in `templates/oh-my-zsh/macos-env.zsh`:

```zsh
export BUN_INSTALL="$HOME/.bun"
```

This variable is **not used for PATH resolution** (PATH is constructed
explicitly). It exists so that bun's own tooling and global package resolution
can locate `~/.bun/install/global/`.

### PATH entries involving bun

From `macos-env.zsh` (PATH position 4 of 10):

```
$HOME/.bun/bin
```

Full precedence order:
1. `~/.local/share/mise/shims`
2. `~/.local/share/mise/bin`
3. `~/.local/bin`
4. `~/.bun/bin`  <-- global packages resolve here
5. `~/.pixi/bin`
6. (remaining entries)

### Mise npm backend setting

In `~/.config/mise/config.toml`:

```toml
[settings.npm]
package_manager = "bun"
```

This tells mise to use bun (instead of npm) when installing tools from the npm
backend, giving approximately 3x faster installs.

## 6. Update / Maintenance Flow

The `update_bun()` function in `scripts/macos-dev-maintenance.sh` (lines
348-365) implements a two-phase update:

### Phase 1: Binary upgrade (conditional)

```bash
bun_path="$(command -v bun)"
case "$bun_path" in
  "$HOME/.local/share/mise/installs/bun/"*)
    ;;  # Skip -- mise manages the binary
  *)
    bun upgrade || return 1
    ;;
esac
```

When bun is mise-managed (current state), `bun upgrade` is **skipped**. The
binary is upgraded via `mise upgrade --yes` instead (called separately in the
maintenance flow).

### Phase 2: Global packages upgrade (always)

```bash
bun update -g --latest || return 1
```

This updates all globally installed packages regardless of how the bun binary
is managed.

### Full maintenance call order

1. `update_brew` -- Homebrew formulae and casks
2. `update_mise` -- `mise self-update` + `mise upgrade --yes` + `mise reshim`
   (this upgrades the bun runtime)
3. `update_bun` -- skips binary upgrade (mise-managed), runs `bun update -g --latest`
4. `update_uv` / `update_pixi` -- other tool managers

### ensure_bun() in install-langchain-cli-tools.sh

The `ensure_bun()` function (lines 51-73) mirrors the same pattern: if bun is
mise-managed, skip `bun upgrade`; otherwise run it. If bun is missing entirely,
it falls back to `mise install -q bun@latest && mise use -g bun@latest`.

## 7. Integration Points

### With mise

- Mise is the **runtime version manager** for bun (`bun = "latest"` in mise
  global config).
- Mise shims shadow the standalone `~/.bun/bin/bun` binary.
- Mise uses bun as its npm backend for tool installation (`package_manager = "bun"`).
- `mise reshim` is called after runtime upgrades to keep shims current.

### With node

- Both `bun` and `node` are managed by mise (`node = "latest"`).
- Bun is preferred over node for JS tooling. The `install_node_tool()` function
  in both `install-agent-stack.sh` and `install-langchain-cli-tools.sh` uses
  `bun add -g` (not `npm install -g`).
- Node remains installed for compatibility (some CLIs require node's module
  resolution) and because mise's npm backend needs node for version resolution
  even when using bun for installs.

### With uv

- No direct integration. They manage separate ecosystems (JS vs Python).
- Both are installed and version-managed by mise.

### With pixi

- No direct integration. Pixi handles conda-forge packages.

### Cleanup scripts

- `cleanup_claude_cli()` removes `~/.bun/bin/claude` to prevent conflicts with
  the `claude` alias pointing to `scripts/claude-wrapper.sh`.
- `cleanup_gemini_cli()` removes `~/.bun/bin/gemini` for the same reason.

## 8. Known Issues or Gaps

### Issue 1: Bun completions are disabled

The old `source "$BUN_INSTALL/_bun"` line was removed but the new fpath symlink
was never created. Bun tab completions do not work in the current shell.

**Fix:** `ln -sfn ~/.bun/_bun ~/.oh-my-zsh/custom/completions/_bun`

### Issue 2: Stale standalone bun binary in ~/.bun/bin/bun

A 57 MB standalone bun binary (v1.x, Jan 12 build) exists at `~/.bun/bin/bun`
alongside the mise-managed version at
`~/.local/share/mise/installs/bun/1.3.10/bin/bun`. While PATH ordering ensures
the mise version wins, the standalone binary wastes disk space and could cause
confusion.

**Fix:** Remove the standalone binary: `rm ~/.bun/bin/bun ~/.bun/bin/bunx`

**Risk:** This would break `bun add -g` if mise is ever uninstalled or if
`~/.bun/bin/bun` is referenced directly. Low risk given current architecture.

### Issue 3: Stale mise bun version 1.3.8

`mise ls bun` shows both 1.3.8 and 1.3.10 installed. The older version is
unused.

**Fix:** `mise uninstall bun@1.3.8`

### Issue 4: No bun verification in verify-tooling.sh

The `scripts/verify-tooling.sh` file contains no bun-specific checks. The
`scripts/verify-all.sh` only references `~/.bun/bin` in its PATH setup but does
not verify bun health.

**Fix:** Add bun version and global package checks to the verification suite.

### Issue 5: Global packages installed to standalone bun location

All global packages live under `~/.bun/install/global/` (the standalone bun's
global directory), not under the mise-managed bun install tree. This works
because `~/.bun/bin` is on PATH, but it creates an implicit dependency on the
`~/.bun` directory structure even though the bun binary itself comes from mise.

This is by design (BUN_INSTALL=$HOME/.bun controls this) and is not a bug, but
it means the `~/.bun` directory cannot be fully removed without losing all
global packages.
