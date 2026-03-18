# uv Tool Audit Report

Date: 2026-02-28
Scope: How uv (Astral) is installed, configured, and used across the macos-development-environment repository.

## 1. Overview

uv is used exclusively as a **Python tool manager** (via `uv tool install`) and virtual environment creator. It is explicitly prevented from managing Python runtimes -- that responsibility belongs to mise. In the toolchain precedence model, uv sits at tier 4: `mise > bun > pixi > uv > Homebrew`.

uv manages approximately 20+ Python CLI tools, including the full LangChain/LangGraph/LangSmith CLI suite, SkyPilot, aider-chat, crewAI, and open-interpreter. It does not manage any runtimes or language versions.

## 2. Installation Method

uv can be installed through **three different paths**, with detection logic that adapts maintenance behavior accordingly:

| Install path | Detection pattern | Self-update behavior |
|---|---|---|
| **mise (aqua backend)** | `$HOME/.local/share/mise/installs/uv/*` or `$HOME/.local/share/mise/shims/*` | Skip `uv self update`; use `mise upgrade` instead |
| **Homebrew** | `/opt/homebrew/*` or `/usr/local/*` | Skip `uv self update`; use `brew upgrade uv` instead |
| **Standalone installer** | Any other path | `uv self update` is safe to call |

The mise aqua backend (`aqua:astral-sh/uv`) is the recommended path. The standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`) is used as a fallback in `scripts/install-agent-stack.sh` when uv is not already present.

Relevant code from `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/install-agent-stack.sh` (lines 67-85):

```bash
ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    local uv_path
    uv_path="$(command -v uv)"
    case "$uv_path" in
      "$HOME/.local/share/mise/installs/"*|"$HOME/.local/share/mise/shims/"*|/opt/homebrew/*|/usr/local/*)
        ;;
      *)
        uv self update >/dev/null 2>&1 || true
        ;;
    esac
    return 0
  fi
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    return 0
  fi
  return 1
}
```

## 3. Configuration

### 3.1 UV_PYTHON_DOWNLOADS=never

Set in every script and shell environment file that invokes uv:

| File | Line |
|---|---|
| `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/macos-env.zsh` | `export UV_PYTHON_DOWNLOADS=never` (line 29) |
| `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/install-langchain-cli-tools.sh` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` (line 4) |
| `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/install-agent-stack.sh` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` (line 4) |
| `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh` | `export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"` (line 4) |

**Purpose:** Prevents uv from downloading its own Python interpreters. Forces uv to use the Python versions already installed by mise. This eliminates duplicate Python installs and keeps mise as the single source of truth for runtimes.

### 3.2 UV_CACHE_DIR

```bash
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/Library/Caches/uv}"
```

Set in `macos-env.zsh` (line 23), `install-langchain-cli-tools.sh` (line 5), `install-agent-stack.sh` (line 5), `verify-langchain-tools.sh` (line 11), and `macos-dev-maintenance.sh` (line 174).

This follows macOS conventions (`~/Library/Caches/`) rather than the XDG default (`~/.cache/uv`). Each script also runs `mkdir -p "$UV_CACHE_DIR"` to ensure the directory exists.

### 3.3 PYO3_USE_ABI3_FORWARD_COMPATIBILITY

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY="${PYO3_USE_ABI3_FORWARD_COMPATIBILITY:-1}"
```

Set in `install-langchain-cli-tools.sh` (line 8) and `install-agent-stack.sh` (line 10). Ensures PyO3-based Rust extensions (used by some LangChain tools) compile against a stable Python ABI, preventing version mismatches when mise upgrades Python.

### 3.4 UV_TOOL_FORCE and UV_TOOL_TIMEOUT_SECONDS

Set in `install-langchain-cli-tools.sh`:
- `UV_TOOL_FORCE="${UV_TOOL_FORCE:-1}"` -- forces reinstall of specific tools (currently `langchain-cli` and `langc`).
- `UV_TOOL_TIMEOUT_SECONDS="${UV_TOOL_TIMEOUT_SECONDS:-600}"` -- caps long-running installs (notably `docs-monorepo`) at 10 minutes.

### 3.5 MDE_UV_CACHE_PRUNE

Set in `macos-dev-maintenance.sh` (line 10). When `MDE_UV_CACHE_PRUNE=1`, the maintenance script runs `uv cache prune` to remove unreferenced cache entries. Defaults to `0` (disabled).

## 4. Installed Tools

### 4.1 Agent stack tools (via `scripts/install-agent-stack.sh`)

Installed with `uv tool install --upgrade`:

| Tool | Notes |
|---|---|
| langchain-cli | Also in LangChain tools script |
| langgraph-cli | Also in LangChain tools script |
| langsmith-fetch | Also in LangChain tools script |
| skypilot[aws] | AWS extras included |
| aider-chat | AI coding assistant |
| open-interpreter | AI assistant |
| crewai | Multi-agent framework |

### 4.2 LangChain CLI tools (via `scripts/install-langchain-cli-tools.sh`)

Installed with `uv tool install --upgrade`, many from Git repositories:

| Tool | Source | Install method |
|---|---|---|
| langchain-cli | `langchain-ai/langchain` (libs/cli) | PyPI or git fallback |
| langchain-model-profiles | `langchain-ai/langchain` (libs/model-profiles) | PyPI or git fallback |
| langgraph-cli | `langchain-ai/langgraph` (libs/cli) | PyPI or git fallback |
| langgraph-gen | `langchain-ai/langgraph-gen-py` | PyPI or git fallback |
| langgraph-engineer | `langchain-ai/langgraph-engineer` | PyPI or git fallback |
| langsmith-fetch | `langchain-ai/langsmith-fetch` | PyPI or git fallback |
| langsmith-data-migration-tool | `langchain-ai/langsmith-data-migration-tool` | PyPI or git fallback |
| langsmith-mcp-server | `langchain-ai/langsmith-mcp-server` | PyPI or git fallback |
| mcpdoc | `langchain-ai/mcpdoc` | PyPI or git fallback |
| deepagents-cli | `langchain-ai/deepagents` (libs/deepagents-cli) | PyPI or git fallback |
| pylon-data-extractor | `langchain-ai/pylon_data_extractor` | PyPI or git fallback |

Internal/optional tools (when `INCLUDE_INTERNAL=1`):

| Tool | Source | Install method |
|---|---|---|
| langc | `langchain-ai/cli` | Custom git clone + patching |
| docs-monorepo | `langchain-ai/docs` | Custom git clone + patching (timeout-guarded) |
| langchain-plugin | `langchain-ai/langchain-aiplugin` | PyPI or git fallback |
| learning-langchain | `langchain-ai/learning-langchain` | Custom git clone + patching |
| mcp-simple-streamablehttp-stateless | `langchain-ai/langchain-mcp-adapters` (subdirectory) | PyPI or git fallback |

### 4.3 Python target version for tools

All tool installs target `TOOL_PYTHON_VERSION="${TOOL_PYTHON_VERSION:-3.12}"`. The `tool_python_path()` function resolves this to a mise-managed Python binary via `mise where python@3.12`, and passes it to uv as `UV_PYTHON="$path"`.

## 5. Python Integration (Interaction with mise-managed Python)

The integration between uv and mise follows a strict ownership model:

1. **mise owns Python runtimes.** All Python versions are installed via `mise install python@X.Y` and managed via `mise use -g python@latest`.

2. **uv consumes mise-managed Python.** Every `uv tool install` call resolves the Python interpreter through `tool_python_path()`:

   ```bash
   tool_python_path() {
     local version="${1:-$TOOL_PYTHON_VERSION}"
     if command -v mise >/dev/null 2>&1; then
       local base=""
       base="$(mise where python@${version} 2>/dev/null || true)"
       if [[ -n "$base" && -x "$base/bin/python3" ]]; then
         printf '%s' "$base/bin/python3"
         return 0
       fi
     fi
     return 1
   }
   ```

   The resolved path is passed as `UV_PYTHON="$uv_python"` to each `uv tool install` invocation.

3. **UV_PYTHON_DOWNLOADS=never** prevents uv from ever downloading its own Python, even if the mise-managed Python is missing or incompatible. If mise cannot provide a suitable Python, the uv install fails explicitly rather than silently fetching a duplicate runtime.

4. **uv tool virtualenvs** live in `~/.local/share/uv/tools/<tool-name>/`. Each tool gets its own isolated venv with a `bin/python` symlink pointing to the mise-managed interpreter. Verification scripts (e.g., `verify-langchain-tools.sh`) use this path to run smoke tests:

   ```bash
   tool_python() {
     local name="$1"
     local python="$HOME/.local/share/uv/tools/$name/bin/python"
     if [[ -x "$python" ]]; then
       printf '%s' "$python"
       return 0
     fi
     return 1
   }
   ```

5. **pixi** is used as an alternative/fallback for some tools. The install scripts try `pixi global install` first, then fall back to `uv tool install` if pixi fails. Both pixi and uv are prevented from managing Python runtimes.

## 6. Update/Maintenance Flow

The maintenance script (`/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh`) handles uv updates in two stages:

### Stage 1: uv binary update (`update_uv()`, lines 384-405)

```bash
update_uv() {
  local uv_path
  uv_path="$(command -v uv)"
  case "$uv_path" in
    "$HOME/.local/share/mise/installs/"*|"$HOME/.local/share/mise/shims/"*)
      log "uv is mise-managed; skipping uv self update."
      ;;
    /opt/homebrew/*|/usr/local/*)
      log "uv is Homebrew-managed; skipping uv self update."
      ;;
    *)
      uv self update || return 1
      ;;
  esac

  uv tool upgrade --all || return 1
  return 0
}
```

- If uv is mise-managed: skip `uv self update`, rely on `mise upgrade` (run earlier in the pipeline).
- If uv is Homebrew-managed: skip `uv self update`, rely on `brew upgrade` (run earlier in the pipeline).
- Otherwise (standalone install): run `uv self update`.

### Stage 2: uv cache pruning (`prune_uv_cache()`, lines 407-417)

Optional, controlled by `MDE_UV_CACHE_PRUNE=1`. Runs `uv cache prune` to reclaim disk space.

### Stage 3: tool-level updates

After `update_uv()`, the maintenance script optionally runs `install-agent-stack.sh` and `install-langchain-cli-tools.sh`, which call `uv tool install --upgrade` for each tool. Then `uv tool upgrade --all` (from Stage 1) catches anything not covered by the install scripts.

### Execution order in maintenance pipeline

1. `update_brew` -- Homebrew formula/cask upgrades
2. `update_mise` -- `mise self-update` + `mise upgrade --yes` + `mise reshim`
3. `update_bun` -- bun global updates
4. `update_uv` -- uv self-update (guarded) + `uv tool upgrade --all`
5. `prune_uv_cache` -- optional cache cleanup
6. `update_pixi` -- pixi self-update + global update
7. `update_agent_tools` -- runs install-agent-stack.sh and install-langchain-cli-tools.sh

## 7. Migration History (UV_NO_MANAGED_PYTHON to UV_PYTHON_DOWNLOADS)

### Original approach (2026-01)

The repository originally used `UV_NO_MANAGED_PYTHON=1` to prevent uv from downloading Python runtimes. This was set in:

- `templates/oh-my-zsh/macos-env.zsh`
- `scripts/macos-dev-maintenance.sh`
- `scripts/install-langchain-cli-tools.sh`
- `scripts/install-agent-stack.sh`
- `~/.config/mise/config.toml` (in `[env]` section)
- `docs/setup-notes.md`

The decision was logged in `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/decision-log.md` under "2026-01 - Python runtime ownership".

### Discovery of the issue

Research round R2 (documented in `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/plans/2026-02-28-research-r2-tool-interactions.md`, finding 4) discovered that `UV_NO_MANAGED_PYTHON` is an **undocumented legacy environment variable**. It is not part of uv's official API. The official mechanism is:

- Environment variable: `UV_PYTHON_DOWNLOADS=never`
- Config file: `python-downloads = "never"` (in `uv.toml` or `pyproject.toml`)

uv continues to honor `UV_NO_MANAGED_PYTHON=1` as a backward-compatibility shim, treating any truthy value as equivalent to `python-downloads = "never"`. However, this is not guaranteed in future releases.

### Migration (2026-02-28)

All scripts were migrated from `UV_NO_MANAGED_PYTHON=1` to `UV_PYTHON_DOWNLOADS=never` as part of the mise modernization implementation (Phase 3 in the consolidation spec). The migration was applied to:

- `templates/oh-my-zsh/macos-env.zsh` (line 29)
- `scripts/macos-dev-maintenance.sh` (line 4)
- `scripts/install-langchain-cli-tools.sh` (line 4)
- `scripts/install-agent-stack.sh` (line 4)

### Not yet migrated

- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/mise-config.md` (line 24) still shows `UV_NO_MANAGED_PYTHON = "1"` in the example `config.toml`. This should be updated to `UV_PYTHON_DOWNLOADS = "never"`.
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/setup-notes.md` (line 350) still references `export UV_NO_MANAGED_PYTHON=1`. This should be updated.
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/decision-log.md` (line 60) references the old variable name in the impact statement. Consider adding a new decision entry documenting the migration.

## 8. Known Issues or Gaps

### 8.1 Stale documentation references to UV_NO_MANAGED_PYTHON

As noted in Section 7, `docs/mise-config.md`, `docs/setup-notes.md`, and `docs/decision-log.md` still reference the old `UV_NO_MANAGED_PYTHON=1` variable. These should be updated for consistency.

### 8.2 No mise config.toml [env] migration

The `[env]` section in the example `~/.config/mise/config.toml` (documented in `docs/mise-config.md`) still sets `UV_NO_MANAGED_PYTHON = "1"`. If the user's actual config.toml mirrors this example, they have a stale env var. The config should be updated to `UV_PYTHON_DOWNLOADS = "never"`.

### 8.3 uv cache location not enforced by mise

The `UV_CACHE_DIR` is set to `~/Library/Caches/uv` by shell exports in multiple files, but this is not enforced via `~/.config/mise/config.toml` `[env]`. If a script runs before the shell environment is loaded, it may use uv's default cache location (`~/.cache/uv` or platform default). Each script defensively re-exports this variable, which is correct but duplicative.

### 8.4 pixi/uv tool ownership overlap

Both pixi (`pixi global install`) and uv (`uv tool install`) are used for Python CLI tool installation. The install scripts try pixi first and fall back to uv. This means some tools may be installed by pixi on one run and uv on another, depending on pixi availability. The `verify-langchain-tools.sh` script only checks `uv tool list`, so pixi-installed tools would appear as "missing" in verification even if they are functional.

### 8.5 No `uv tool list` in the maintenance verification step

The maintenance script (`macos-dev-maintenance.sh`) runs `uv tool upgrade --all` but does not verify that the upgrade succeeded or log the current tool inventory. A post-upgrade `uv tool list` would help with auditability.

### 8.6 TOOL_PYTHON_VERSION pinned to 3.12

The default `TOOL_PYTHON_VERSION=3.12` is hardcoded across install scripts. When mise upgrades the global Python to 3.13+, tool venvs will still target 3.12 unless the variable is explicitly overridden. This is intentional (stability over bleeding-edge) but worth noting as Python 3.12 approaches end-of-bugfix status.
