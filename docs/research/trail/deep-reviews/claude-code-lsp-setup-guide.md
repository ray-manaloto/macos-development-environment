# Claude Code LSP Setup Guide

**Source:** https://karanbansal.in/blog/claude-code-lsp/
**Author:** Karan Bansal
**Date:** February 2026
**Research Date:** March 21, 2026

## Executive Summary

LSP (Language Server Protocol) enables Claude Code to perform semantic code navigation in ~50ms instead of grep-based text search in 30-60 seconds. Setup takes 2 minutes and requires four steps, plus a critical gotcha about plugins being installed but disabled by default.

## Performance Impact

| Operation | Without LSP | With LSP | Speedup |
|-----------|------------|----------|---------|
| goToDefinition | 30-60 seconds | 50ms | 600-1200x |
| Accuracy | ~80-90% (fuzzy match) | 100% (semantic) | Perfect |

## The 4-Step Setup

### Step 1: Enable LSP Tool (1 min)

Add to `~/.claude/settings.json`:
```json
{
  "env": { "ENABLE_LSP_TOOL": "1" }
}
```

**Also recommended** for shell profile fallback:
```bash
export ENABLE_LSP_TOOL=1
```

**Critical Note:** This flag is **not officially documented** as of Feb 2026. Discovered via [GitHub Issue #15619](https://github.com/anthropics/claude-code/issues/15619). May change in future versions.

### Step 2: Install Language Server Binary (1 min)

Install one or more language servers (same ones your IDE uses):

| Language | Command |
|----------|---------|
| Python | `npm i -g pyright` |
| TypeScript/JS | `npm i -g typescript-language-server typescript` |
| Go | `go install golang.org/x/tools/gopls@latest` |
| Rust | `rustup component add rust-analyzer` |
| Java | `brew install jdtls` |
| C/C++ | `brew install llvm` |
| C# | `dotnet tool install -g csharp-ls` |
| PHP | `npm i -g intelephense` |
| Kotlin | GitHub releases |
| Swift | Included with Xcode |
| Lua | GitHub releases |

Verify installation:
```bash
which pyright     # (or whatever binary you installed)
```

### Step 3: Install and Enable Plugin (~30 sec)

```bash
# Update marketplace catalog
claude plugin marketplace update claude-plugins-official

# Install plugin for your language
claude plugin install pyright-lsp          # Python
# OR typescript-lsp, gopls-lsp, rust-analyzer-lsp, jdtls-lsp,
#    clangd-lsp, csharp-lsp, php-lsp, kotlin-lsp, swift-lsp, lua-lsp

# CRITICAL: Enable the plugin
claude plugin enable pyright-lsp           # Must do this!
```

**THE #1 GOTCHA**: Plugins install as disabled by default. You must explicitly enable them. If you skip this, you'll see "Total LSP servers loaded: 0" in debug logs.

### Step 4: Restart Claude Code

Full restart required. `/reload-plugins` does **not** work. Verify it's working:

1. Restart Claude Code fully
2. Ask Claude: "What type is [some variable]?"
3. If Claude uses LSP `hover` operation instead of reading file, you're good
4. Check debug logs: `cat ~/.claude/debug/latest | grep "Total LSP servers loaded"`
   - Should show: `Total LSP servers loaded: N` where N > 0

## LSP Operations

Claude Code can now use:

| Operation | When Claude Uses It | Example Command |
|-----------|-------------------|-----------------|
| `goToDefinition` | You ask "where is X defined?" | Direct file + line number |
| `findReferences` | You ask "find all usages of X" | Every call site with location |
| `hover` | You ask "what type is X?" | Full type signature + docs |
| `documentSymbol` | You ask "list functions in this file" | All symbols with locations |
| `workspaceSymbol` | You ask "find PaymentService class" | Across entire project |
| `goToImplementation` | You ask "what implements AuthProvider?" | Concrete implementations |
| `incomingCalls` | You ask "what calls processPayment?" | Full call hierarchy |
| `outgoingCalls` | You ask "what does handleOrder call?" | Dependencies of a function |

## Startup Sequence

When Claude Code starts with LSP enabled, all servers initialize simultaneously:

```
05:53:56.216  [LSP MANAGER] Starting async initialization
05:53:56.573  Total LSP servers loaded: 4
05:53:56.757  gopls initialized          (+0.5s)
05:53:56.762  typescript initialized     (+0.5s)
05:53:56.819  pyright initialized        (+0.6s)
05:54:04.791  jdtls initialized          (+8.6s)    # JVM warmup is slow
              Index is warm — all LSP operations now ~50ms
```

Servers immediately scan and index your entire project. By the time you ask your first question, the index is warm and ready.

## Troubleshooting Checklist

| Issue | Cause | Fix |
|-------|-------|-----|
| LSP tool not available | `ENABLE_LSP_TOOL` not set | Add to settings.json + restart |
| "Plugin not found in marketplace" | Stale catalog | `claude plugin marketplace update claude-plugins-official` |
| Plugin installed but disabled | Not enabled after install | `claude plugin enable <name>` + restart |
| "Executable not found" | Binary not in PATH | Install binary + verify with `which <binary>` |
| "Total LSP servers loaded: 0" | All plugins disabled | Enable plugins + restart |
| Race condition during startup | Servers not ready | Restart Claude Code, wait for initialization |

## Making Claude Code Actually Use LSP

Even with LSP fully set up, Claude Code may default to grep/glob. Add this to your project's `.claude/CLAUDE.md` (or global `~/.claude/CLAUDE.md`):

```markdown
### Code Intelligence Preferences

Prefer LSP operations over Grep/Glob/Read for code navigation:
- `goToDefinition` / `goToImplementation` to jump to source
- `findReferences` to see all usages across the codebase
- `workspaceSymbol` to find where something is defined
- `documentSymbol` to list all symbols in a file
- `hover` for type info without reading the file
- `incomingCalls` / `outgoingCalls` for call hierarchy

Before renaming or changing a function signature, use
`findReferences` to find all call sites first.

Use Grep/Glob only for text/pattern searches (comments,
strings, config values) where LSP doesn't help.

After writing or editing code, check LSP diagnostics before
moving on. Fix any type errors or missing imports immediately.
```

Alternatively, use Claude Code's auto-memory: "Remember to always prefer LSP over Grep for code navigation."

## Key Insights

1. **Semantic vs Text Search**: LSP treats code as structured programs with meaning. Grep treats it as text. For "find User" with 847 matches across 203 files, LSP returns the one actual definition you wanted.

2. **Self-Correcting Edits**: After Claude edits code, LSP pushes diagnostics automatically. Claude sees errors (missing imports, type mismatches) and fixes them in the same turn before you see the result.

3. **Index is Warm at Startup**: LSP servers scan your entire project during initialization, not on-demand. The first query is just as fast as the hundredth.

4. **Universal Servers**: These are the exact same language servers VS Code, Vim, and Neovim use. Not custom to Claude Code. Proven, battle-tested implementations.

## Gotchas Summary

1. **ENABLE_LSP_TOOL is undocumented** — Found via GitHub issue, may change
2. **Plugins install disabled** — Must explicitly enable after install
3. **Full restart required** — `/reload-plugins` doesn't work
4. **Binary must be in PATH** — Just installing the language server isn't enough
5. **Claude defaults to grep** — LSP preference requires explicit instruction in CLAUDE.md
6. **Debug logs are truth** — Check `~/.claude/debug/latest` for "Total LSP servers loaded: N"

## Prerequisites

- Claude Code version 2.0.74 or later
- Language server binary(ies) installed and in `$PATH`

## Summary

Two minutes of setup → 600-1200x performance improvement. The payoff is substantial, especially on large codebases where text search becomes the bottleneck.
