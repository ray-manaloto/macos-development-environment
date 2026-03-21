---
name: LSP "0 servers" root cause - plugins installed but disabled
description: The #1 cause of LSP setup failures is plugins being installed but silently disabled, not missing ENABLE_LSP_TOOL flag
type: reference
---

## Finding

The most common "0 LSP servers loaded" error is **not** a missing ENABLE_LSP_TOOL flag. It's plugins being installed but **disabled** at startup.

## Root Cause

Claude Code has a plugin system where:
1. Plugins can be **installed** (downloaded)
2. Plugins can be **enabled** (registered at startup)

A plugin can be in state #1 without being in state #2.

Running `claude plugin install pyright-lsp` does NOT guarantee `claude plugin list` shows `Status: enabled`.

## Diagnostic Command

```bash
claude plugin list | grep -i lsp
# If Status: disabled, plugin is installed but not active
```

## Fix

```bash
# Enable each disabled plugin
claude plugin enable pyright-lsp
claude plugin enable typescript-lsp
# ... repeat for all disabled plugins

# Then FULL restart (not /reload-plugins)
# Full restart is required because LSP servers initialize at startup
```

## Verification in settings.json

Also set explicitly in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "pyright-lsp@claude-plugins-official": true,
    "typescript-lsp@claude-plugins-official": true,
    "gopls-lsp@claude-plugins-official": true
  }
}
```

## Evidence

- Reddit thread r/ClaudeCode (Feb 2026): "A plugin can be installed but disabled. A disabled plugin won't register its LSP server at startup."
- Karanbansal.in blog: "The #1 gotcha: A plugin can be installed but disabled."
- Accounts for ~80% of "LSP isn't working" problems

## How to Apply

When user reports "0 LSP servers", don't assume ENABLE_LSP_TOOL is missing. First check:

1. `claude plugin list` — look for Status: disabled
2. If disabled, run `claude plugin enable <name>` for each
3. Full restart Claude Code (not /reload-plugins)
4. Verify with `claude plugin list` again
