# Claude Code LSP Setup — Verified Working Procedure

**Date:** 2026-03-20
**Status:** VERIFIED — `/reload-plugins` confirmed `1 plugin LSP server`
**Claude Code Version:** 2.1.81
**OS:** macOS Darwin 25.3.0

---

## Background

Claude Code supports Language Server Protocol (LSP) for real-time code intelligence: go-to-definition, find-references, hover types, diagnostics. This replaces grep-based code navigation (~30-60s per query) with semantic queries (~50ms, 100% accurate).

LSP was officially added in Claude Code 2.0.74. The `ENABLE_LSP_TOOL` env var was discovered via [GitHub Issue #15619](https://github.com/anthropics/claude-code/issues/15619).

---

## The Problem We Solved

The official `pyright-lsp@claude-plugins-official` plugin is a **stub** — it ships with only `plugin.json`, `README.md`, and `LICENSE`. It has **no `.lsp.json` file**, which is the configuration that tells Claude Code's LSP Manager how to start the language server.

The marketplace catalog (`marketplace.json`) defines the `lspServers` configuration, but Claude Code's LSP Manager reads `.lsp.json` from each plugin's own directory. Without this file, the plugin loads but the LSP server is never discovered.

### Evidence

**Before fix (debug log):**
```
[LSP MANAGER] Starting async initialization (generation 1)
Total LSP servers loaded: 0
```

**After fix:**
```
/reload-plugins → 1 plugin LSP server
```

---

## Working Setup (4 Components)

### 1. pyright binary via mise (chezmoi-managed)

```toml
# ~/.config/mise/config.toml (chezmoi-managed template)
[tools]
"npm:pyright" = "latest"
```

Then: `chezmoi apply` → `mise install` → `mise reshim`

Verify:
```bash
which pyright-langserver
# → ~/.local/share/mise/installs/npm-pyright/1.1.408/bin/pyright-langserver
```

### 2. ENABLE_LSP_TOOL=1 in settings.json

```json
// .claude/settings.json (project-level, git-tracked)
{
  "env": {
    "ENABLE_LSP_TOOL": "1"
  }
}
```

Also recommended in shell profile as fallback:
```bash
# ~/.zshrc
export ENABLE_LSP_TOOL=1
```

### 3. Plugin enabled in settings.json

```json
// .claude/settings.json
{
  "enabledPlugins": {
    "pyright-lsp@claude-plugins-official": true
  }
}
```

**Critical:** `enabledPlugins: {}` (empty) at project level blocks ALL plugins, including user-level ones. If you want to disable specific plugins while keeping pyright-lsp, you must explicitly list pyright-lsp as `true`.

### 4. `.lsp.json` in plugin cache directory

This is the missing piece that the official plugin doesn't ship. Create it manually:

```bash
cat > ~/.claude/plugins/cache/claude-plugins-official/pyright-lsp/1.0.0/.lsp.json << 'EOF'
{
    "python": {
        "command": "pyright-langserver",
        "args": [
            "--stdio"
        ],
        "extensionToLanguage": {
            ".py": "python",
            ".pyi": "python"
        },
        "transport": "stdio",
        "initializationOptions": {},
        "settings": {},
        "maxRestarts": 3
    }
}
EOF
```

**Location:** `~/.claude/plugins/cache/claude-plugins-official/pyright-lsp/<version>/.lsp.json`

### 5. Full Restart Required

LSP servers initialize at startup, NOT on `/reload-plugins`. After making changes:

1. `/exit` or quit Claude Code
2. Restart Claude Code
3. Verify: `/reload-plugins` shows `N plugin LSP server(s)`

---

## .lsp.json Schema Reference

From [Piebald-AI/claude-code-lsps](https://github.com/Piebald-AI/claude-code-lsps):

```json
{
    "<language-id>": {
        "command": "<binary-name>",
        "args": ["--stdio"],
        "extensionToLanguage": {
            ".<ext>": "<language-id>"
        },
        "transport": "stdio",
        "initializationOptions": {},
        "settings": {},
        "maxRestarts": 3,
        "startupTimeout": 30000
    }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `command` | Yes | LSP server binary (must be on PATH) |
| `args` | Yes | Arguments (typically `["--stdio"]`) |
| `extensionToLanguage` | Yes | Map file extensions to LSP language IDs |
| `transport` | No | `"stdio"` (default) |
| `initializationOptions` | No | LSP initialization options |
| `settings` | No | LSP workspace settings |
| `maxRestarts` | No | Auto-restart count before giving up |
| `startupTimeout` | No | Milliseconds to wait for server init (2.1.50+) |

---

## Troubleshooting Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Claude Code version | `claude --version` | ≥ 2.0.74 |
| ENABLE_LSP_TOOL set | `echo $ENABLE_LSP_TOOL` | `1` |
| pyright-langserver on PATH | `which pyright-langserver` | mise path |
| Plugin enabled | `claude plugins list \| grep pyright` | `Status: ✔ enabled` |
| .lsp.json exists | `cat ~/.claude/plugins/cache/claude-plugins-official/pyright-lsp/1.0.0/.lsp.json` | Valid JSON |
| LSP servers loaded | `/reload-plugins` (after restart) | `1 plugin LSP server` |
| Debug verification | `grep "Total LSP" ~/.claude/debug/latest` | `Total LSP servers loaded: 1` |

### Common Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| 0 LSP servers | Missing `.lsp.json` | Create the file (see Step 4) |
| 0 LSP servers | `enabledPlugins: {}` | Add `pyright-lsp: true` explicitly |
| 0 LSP servers | Plugin disabled | `claude plugin enable pyright-lsp` |
| 0 LSP servers | Only `/reload-plugins` | Full restart required |
| Plugin invalid manifest | `source`, `category`, `strict` keys | Remove those keys from plugin.json |
| pyright not found | Not in PATH | Install via mise: `"npm:pyright" = "latest"` |

---

## Alternative Approaches

### Piebald Marketplace (community, 24+ languages)

```bash
/plugin marketplace add Piebald-AI/claude-code-lsps
# Then install via /plugins → Marketplaces → Browse
```

Piebald plugins include `.lsp.json` files. May require `npx tweakcc --apply` for some features.

### Local Marketplace (custom)

Create a local marketplace with custom LSP configurations per the [classmethod guide](https://dev.classmethod.jp/en/articles/claude-code-lsp-from-local-marketplace/).

### amplihack lsp-setup Skill

Installed at `.agents/skills/lsp-setup/` (symlinked to `.claude/skills/lsp-setup`). Auto-detects project languages and configures LSP. Use `/lsp-setup --status-only` to check current state.

---

## Sources

| Source | URL | Key Finding |
|--------|-----|-------------|
| Karan Bansal blog | https://karanbansal.in/blog/claude-code-lsp/ | 4-step setup, ENABLE_LSP_TOOL discovery, #1 gotcha |
| Piebald-AI/claude-code-lsps | https://github.com/Piebald-AI/claude-code-lsps | .lsp.json schema, 24+ language configs, tweakcc |
| classmethod article | https://dev.classmethod.jp/en/articles/claude-code-lsp-from-local-marketplace/ | Local marketplace with lspServers in marketplace.json |
| Reddit complete guide | https://www.reddit.com/r/ClaudeAI/comments/1qe239d/ | LSP built-in since 2.0.74, zero-config for newer versions |
| Reddit enable LSP thread | https://www.reddit.com/r/ClaudeCode/comments/1rh5pcm/ | "installed but disabled" root cause, 80% of failures |
| amplihack lsp-setup | https://skills.sh/rysweet/amplihack/lsp-setup | Automated LSP setup skill with 16 language support |
| Claude Code plugins-reference | https://code.claude.com/docs/en/plugins-reference#lsp-servers | Official .lsp.json docs |
| GitHub Issue #15619 | https://github.com/anthropics/claude-code/issues/15619 | ENABLE_LSP_TOOL env var origin |
