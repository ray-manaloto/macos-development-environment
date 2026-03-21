# LSP Enablement in Claude Code: Step-by-Step Guide

**Source**: Reddit r/ClaudeCode (Feb 2026) + karanbansal.in blog post
**Performance Improvement**: 30-60 seconds → 50ms (600x faster, 100% accuracy)
**Setup Time**: ~2 minutes

## Executive Summary

LSP (Language Server Protocol) is a hidden feature in Claude Code that gives it IDE-like code intelligence: go-to-definition, find-references, type checking, and real-time error diagnostics. It's **not enabled by default** as of February 2026, but enabling it requires only a settings.json flag and installing language servers.

The most common failure point is **plugins being installed but disabled**, which causes the "0 LSP servers loaded" message even when everything appears to be set up correctly.

---

## Prerequisites

- Claude Code version 2.0.74 or later (`claude --version`)
- Language server binary for your language(s) installed and in `$PATH`
- A full restart (not just /reload-plugins) after configuration

---

## Step-by-Step Setup

### Step 1: Enable LSP Tool Flag

Add this to `~/.claude/settings.json`:

```json
{
  "env": {
    "ENABLE_LSP_TOOL": "1"
  }
}
```

Also add as a shell fallback in `~/.zshrc` or `~/.bashrc`:

```bash
export ENABLE_LSP_TOOL=1
```

**Status**: This flag is **not officially documented** as of February 2026. Discovered via GitHub Issue #15619. May change in future versions.

### Step 2: Install Language Server Binaries

Install the LSP server for each language you work with. These are the same servers your IDE uses:

| Language | Command |
|----------|---------|
| Python | `npm i -g pyright` |
| TypeScript/JavaScript | `npm i -g typescript-language-server typescript` |
| Go | `go install golang.org/x/tools/gopls@latest` |
| Rust | `rustup component add rust-analyzer` |
| Java | `brew install jdtls` |
| C/C++ | `brew install llvm` |
| C# | `dotnet tool install -g csharp-ls` |
| PHP | `npm i -g intelephense` |
| Kotlin | GitHub releases (see official docs) |
| Swift | Included with Xcode |
| Lua | GitHub releases |

Verify installation by running the command and checking it's in `$PATH`:

```bash
which pyright
which gopls
which typescript-language-server
```

### Step 3: Install and Enable Plugins

Update the marketplace:

```bash
claude plugin marketplace update claude-plugins-official
```

Install plugins for your languages:

```bash
claude plugin install pyright-lsp                    # Python
claude plugin install typescript-lsp                 # TypeScript/JS
claude plugin install gopls-lsp                      # Go
claude plugin install rust-analyzer-lsp              # Rust
claude plugin install jdtls-lsp                      # Java
claude plugin install clangd-lsp                     # C/C++
claude plugin install csharp-lsp                     # C#
claude plugin install php-lsp                        # PHP
claude plugin install kotlin-lsp                     # Kotlin
claude plugin install swift-lsp                      # Swift
claude plugin install lua-lsp                        # Lua
```

Verify all plugins are installed AND enabled:

```bash
claude plugin list
```

**CRITICAL GOTCHA**: A plugin can be **installed but disabled**. This is why you see "0 LSP servers" even after everything appears to be set up.

Check output for `Status: enabled` (not `disabled`). If any show `disabled`:

```bash
claude plugin enable <plugin-name>
```

To be safe, explicitly set them in `~/.claude/settings.json`:

```json
{
  "env": {
    "ENABLE_LSP_TOOL": "1"
  },
  "enabledPlugins": {
    "pyright-lsp@claude-plugins-official": true,
    "typescript-lsp@claude-plugins-official": true,
    "gopls-lsp@claude-plugins-official": true,
    "rust-analyzer-lsp@claude-plugins-official": true,
    "jdtls-lsp@claude-plugins-official": true,
    "clangd-lsp@claude-plugins-official": true,
    "csharp-lsp@claude-plugins-official": true,
    "php-lsp@claude-plugins-official": true,
    "kotlin-lsp@claude-plugins-official": true,
    "swift-lsp@claude-plugins-official": true,
    "lua-lsp@claude-plugins-official": true
  }
}
```

### Step 4: Restart Claude Code

**IMPORTANT**: Use a full restart, not just `/reload-plugins`. LSP servers initialize at startup and won't load without a complete restart.

---

## Verification

After restarting, verify LSP is working:

1. Ask Claude Code: "What type is [some variable in your code]?"
2. If LSP is enabled, Claude Code will use the `hover` LSP operation to get the exact type signature without reading the file
3. Check debug logs:

```bash
ls ~/.claude/debug/
# Look for LSP_MANAGER logs showing successful initialization
```

Expected output in logs:

```
[LSP MANAGER] Starting async initialization
Total LSP servers loaded: N
pyright initialized          (+0.6s)
typescript initialized       (+0.5s)
gopls initialized            (+0.5s)
jdtls initialized            (+8.6s)  # Java takes longer due to JVM warmup
Index is warm — all LSP operations now ~50ms
```

---

## Troubleshooting: "0 LSP Servers Loaded"

If you see "0 LSP servers loaded" after setup, follow this checklist:

### Checklist

1. **Check ENABLE_LSP_TOOL is set**
   ```bash
   echo $ENABLE_LSP_TOOL  # Should print: 1
   cat ~/.claude/settings.json | grep ENABLE_LSP_TOOL
   ```

2. **Check plugins are ENABLED (not just installed)**
   ```bash
   claude plugin list
   # Look for Status: enabled, not disabled
   # If disabled, run: claude plugin enable <name>
   ```

3. **Check plugin enablement in settings.json**
   ```bash
   cat ~/.claude/settings.json | grep -A 20 enabledPlugins
   # Should show true for each plugin
   ```

4. **Check language server binaries are in PATH**
   ```bash
   which pyright
   which gopls
   which typescript-language-server
   # All should return paths, not "not found"
   ```

5. **Check versions match**
   ```bash
   claude --version  # Should be 2.0.74+
   pyright --version
   ```

6. **Check for plugin conflicts**
   If multiple LSP plugins are installed, they may conflict. Uninstall unused ones:
   ```bash
   claude plugin uninstall <conflicting-plugin>
   ```

7. **Full restart (not reload)**
   - Quit Claude Code completely
   - Wait 5 seconds
   - Reopen Claude Code
   - Do NOT use /reload-plugins — this doesn't initialize LSP servers

### Most Common Root Cause

**Plugins are installed but disabled.** This accounts for ~80% of "LSP isn't working" issues.

Command to diagnose:

```bash
claude plugin list | grep -i lsp
```

If you see `Status: disabled`, run:

```bash
claude plugin enable <exact-plugin-name>
```

Then restart Claude Code fully.

---

## What LSP Actually Does

### Automatic (Passive) Benefits

After every file edit, LSP language servers push diagnostics automatically:
- Type errors
- Missing imports
- Undefined variables
- Function signature mismatches

Claude Code sees these errors **immediately** in the same turn and fixes them before you see the result.

**Example workflow**:
1. You ask: "Add email parameter to createUser()"
2. Claude edits the function signature
3. LSP detects 3 type errors at call sites
4. Claude finds and fixes all 3 call sites
5. You get result with 0 errors ✓

All in one turn, no manual iteration needed.

### On-Demand (Active) Benefits

Claude Code can explicitly query the language server:

| Operation | Query | Response | Time |
|-----------|-------|----------|------|
| `goToDefinition` | "Where is processOrder defined?" | File + exact line | 50ms |
| `findReferences` | "Find all calls to validateUser" | Every call site with location | 50ms |
| `hover` | "What type is config?" | Full type signature + docs | 50ms |
| `documentSymbol` | "List all functions in this file" | Every symbol with location | 50ms |
| `workspaceSymbol` | "Find the PaymentService class" | Search across entire project | 50ms |
| `goToImplementation` | "What classes implement AuthProvider?" | Concrete implementations | 50ms |
| `incomingCalls` | "What calls processPayment?" | Call hierarchy trace | 50ms |

---

## Performance Numbers

From debug logs (real session, Feb 23, 2026):

```
Without LSP
- grep -r "User"
- 847 matches across 203 files
- Manual filtering and reading each file
- ~30-60 seconds
- Frequently wrong result

With LSP
- goToDefinition for "User"
- Direct answer: user-service.ts line 42
- ~50 milliseconds
- 100% accuracy
- Zero false positives
```

**Context window efficiency win**: When running 6+ Claude Code agents in parallel, LSP reduces token waste from agents piecing together what symbols mean. The compounding effect across multiple agents is significant.

---

## Important Caveats

### Claude Code Still Defaults to Grep

Even with LSP enabled, Claude Code may still default to grep/read for navigation. One user reported:

> "Even having LSP enabled doesn't mean Claude is going to default to grep. I additionally push him in global Claude.md"

**Workaround**: Add to your global `Claude.md`:

```markdown
## Code Intelligence

Prefer LSP over Grep/Read for code navigation:
- `workspaceSymbol` to find where something is defined
- `findReferences` to see all usages across the codebase
- `goToDefinition` / `goToImplementation` to jump to source
- `hover` for type info without reading the file

Use Grep only when LSP isn't available or for text/pattern searches.
```

### Language Server Memory Usage

Pyright in particular can consume 2-4GB of RAM on large Python monorepos while indexing. On first query after startup, expect 10-15 seconds while the type graph builds. Subsequent queries are instant.

**Workaround**: Set pyright's `python.analysis.indexing` to false to rely on workspace symbols only (loses deep type inference but keeps sub-100ms navigation).

### Java Server Startup Time

JVM-based servers like jdtls take ~8-10 seconds to initialize due to JVM warmup. This is normal and expected, not a bug.

---

## Recent Changes (Feb 2026)

One Reddit comment claims:

> "LSP is enabled by default in newer Claude Code versions, no need to manually set ENABLE_LSP_TOOL anymore."

**Status**: Unverified. The February 2026 blog post still recommends setting ENABLE_LSP_TOOL explicitly. If you're on a newer version, you may not need this flag, but setting it is harmless.

---

## Debug Logs Location

LSP manager logs are written to `~/.claude/debug/` after each session. Look for:

```
[LSP MANAGER] Starting async initialization
Total LSP servers loaded: <N>
<language> initialized (+<time>)
```

If `Total LSP servers loaded: 0`, check:
1. Plugin enable status
2. Language server binary availability
3. settings.json `enabledPlugins` configuration
4. Full restart was performed

---

## Recommended Reading

- Original blog post: https://karanbansal.in/blog/claude-code-lsp/ (full setup for 11 languages)
- Reddit thread: https://www.reddit.com/r/ClaudeCode/comments/1rh5pcm/enable_lsp_in_claude_code_code_navigation_goes/
- LSP Specification: https://microsoft.github.io/language-server-protocol/

---

## Quick Checklist

- [ ] Claude Code version 2.0.74+
- [ ] `ENABLE_LSP_TOOL=1` in `~/.claude/settings.json`
- [ ] Language servers installed and in `$PATH`
- [ ] Plugins installed via `claude plugin install <name>`
- [ ] Plugins are **enabled** (check with `claude plugin list`)
- [ ] `enabledPlugins` section in `~/.claude/settings.json` set to true
- [ ] Full restart completed (not just /reload-plugins)
- [ ] Verified with debug logs in `~/.claude/debug/`
- [ ] Added LSP guidance to global `Claude.md` to prevent grep default

