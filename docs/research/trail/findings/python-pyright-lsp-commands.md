# Python LSP Setup — Exact Commands

**For Python development with Claude Code LSP**

## One-Time Setup (2 minutes)

### 1. Enable LSP Tool
```bash
# Edit ~/.claude/settings.json and add:
# "env": { "ENABLE_LSP_TOOL": "1" }

# Also add to shell profile for fallback:
echo 'export ENABLE_LSP_TOOL=1' >> ~/.zshrc  # macOS
# or
echo 'export ENABLE_LSP_TOOL=1' >> ~/.bashrc # Linux
```

### 2. Install Pyright Language Server
```bash
npm i -g pyright
```

Verify:
```bash
which pyright  # Should show path to pyright executable
```

### 3. Install and Enable Plugin
```bash
# Update marketplace
claude plugin marketplace update claude-plugins-official

# Install Python LSP plugin
claude plugin install pyright-lsp

# Enable it (CRITICAL - plugins are installed but disabled by default)
claude plugin enable pyright-lsp
```

### 4. Full Restart Claude Code
```bash
# Close Claude Code completely and reopen it
# Do NOT use /reload-plugins - it won't work
```

### 5. Verify It's Working
```bash
# Check debug logs
cat ~/.claude/debug/latest | grep "Total LSP servers loaded"
# Should show: "Total LSP servers loaded: 1" (or more if you installed other servers)

# Ask Claude: "What type is [variable]?"
# If it uses LSP hover instead of reading the file, you're good
```

## What You Get

| You Ask Claude | LSP Does | Speed |
|---|---|---|
| "Where is getUserById defined?" | `goToDefinition` | ~50ms |
| "Find all usages of UserService" | `findReferences` | ~50ms |
| "What type is the response?" | `hover` | ~50ms |
| "List all functions in auth.py" | `documentSymbol` | ~50ms |
| "Find the PaymentHandler class" | `workspaceSymbol` | ~50ms |

**Without LSP:** Same queries take 30-60 seconds with grep.

## The #1 Gotcha: Installed But Disabled

After running `claude plugin install pyright-lsp`, the plugin is **disabled by default**.

You must run:
```bash
claude plugin enable pyright-lsp
```

If you skip this, you'll see in debug logs:
```
Total LSP servers loaded: 0
```

This is the single most common issue after setup.

## Debug Checklist

If LSP isn't working:

```bash
# 1. Check the binary exists
which pyright

# 2. Check plugin status
claude plugin list | grep pyright-lsp
# Should show: Status: enabled

# 3. Check debug logs
cat ~/.claude/debug/latest | tail -50 | grep -E "LSP|pyright"
# Should show initialization messages

# 4. If all else fails, restart Claude Code
# (full restart, not /reload-plugins)
```

## Make Claude Actually Use LSP

Even with LSP enabled, Claude Code may default to grep. Add this to `.claude/CLAUDE.md`:

```markdown
### Python Code Intelligence

For Python code navigation, prefer LSP operations:
- `goToDefinition` for finding where functions/classes are defined
- `findReferences` to find all usages of a symbol
- `hover` for type information and docstrings
- `documentSymbol` to list all functions and classes in a file
- `workspaceSymbol` to find symbols across the entire project

Use grep only for searching comments, strings, or config values.
```

## Expected Initialization Output

When Claude Code starts with pyright-lsp enabled:

```
05:53:56.216  [LSP MANAGER] Starting async initialization
05:53:56.573  Total LSP servers loaded: 1
05:53:56.819  pyright initialized        (+0.6s)
              Index is warm — all LSP operations now ~50ms
```

Pyright immediately scans and indexes your entire Python project. Fast queries on the first ask.

## Prerequisites

- Claude Code 2.0.74 or later: `claude --version`
- Node.js 14+ installed: `node --version`

## Sources

- Full setup guide: https://karanbansal.in/blog/claude-code-lsp/
- GitHub issue (ENABLE_LSP_TOOL discovery): https://github.com/anthropics/claude-code/issues/15619
- Pyright documentation: https://github.com/microsoft/pyright
