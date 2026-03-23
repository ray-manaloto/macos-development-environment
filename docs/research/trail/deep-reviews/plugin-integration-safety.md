# Plugin Integration Safety Review

**Date**: 2026-03-23
**Reviewer**: Research Agent (Adversarial)
**Status**: BLOCKERS IDENTIFIED
**Spec Under Review**: docs/superpowers/specs/2026-03-23-honcho-memory-design.md

## Executive Summary

The honcho-memory design spec is **technically sound** but has a **critical unresolved blocker**: Claude Code's hook execution order when multiple plugins register the same hook event (SessionStart). The spec documents plugin integration and Docker infrastructure correctly, but doesn't account for the conflict between mde's existing SessionStart hook and the claude-honcho plugin's SessionStart hook.

**Decision**: Do NOT merge PR B until hook conflict is resolved.

## Vectors Passed

### 1. Endpoint Configuration ✅
- Plugin correctly targets `http://localhost:8000/v3` (verified in config.ts)
- Spec's compose.yaml correctly binds port 8000 on 127.0.0.1
- Plugin detects `endpoint.environment="local"` and constructs correct base URL
- **Status**: No issue

### 2. SDK Version Compatibility ✅
- Plugin uses `@honcho-ai/sdk@^2.0.0`
- Honcho server v3.0.3 was released alongside SDK v2.0.1
- Both developed and released by Plastic Labs (coordinated versioning)
- SDK v2 API (fluent async/await) aligns with server v3 REST endpoints
- **Status**: No issue

### 3. Bun Availability ✅
- claude-honcho plugin requires Bun for hook execution
- Bun 1.3.10 is already in mise config (.devcontainer/mise.toml)
- Plugin hooks are TypeScript and use Bun's stdin/stdout APIs
- **Status**: No issue

### 4. Workspace Handling ✅
- Plugin uses workspace NAMES (string), not IDs
- Spec uses workspace names: "claude_code", "cursor", "obsidian"
- Honcho server API accepts both (internally resolves names to IDs)
- Plugin config supports per-host workspace switching
- **Status**: No issue

### 5. API Key Handling ✅
- Spec sets AUTH_USE_AUTH=false for localhost development
- Honcho server skips JWT validation when auth is disabled
- Plugin docs confirm: apiKey can be any value for local endpoint
- Spec comment correctly states this behavior
- **Status**: No issue

## Critical Blocker: Hook Execution Order

### The Problem
```json
// .claude/settings.json - EXISTING hook
{
  "SessionStart": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "uv run mde-py hooks session-start"
        }
      ]
    }
  ]
}
```

When `claude-honcho` plugin is installed, it will register its own SessionStart hook. **The spec does not document what happens when two plugins register hooks for the same event.**

### Three Possible Outcomes

#### Scenario A: Sequential (mde then plugin)
```
1. mde:session-start runs
   - Validates environment
   - Guards against corrupted install
   - Sets up logging
2. plugin:session-start runs
   - Loads Honcho memory
   - Displays context
```
**Issue**: Plugin doesn't see guard checks. If environment is corrupted, plugin runs with stale/invalid state.

#### Scenario B: Sequential (plugin then mde)
```
1. plugin:session-start runs
   - Loads Honcho memory
   - Queries Honcho API (might fail if environment broken)
2. mde:session-start runs
   - Guards install (too late, plugin already executed)
```
**Issue**: Memory load might fail due to network issues that guard-install would have caught.

#### Scenario C: One overrides the other
```
- Only one hook executes
- The other is silently dropped
```
**Issue**: Either guard-checks never run, or memory never loads.

#### Scenario D: Parallel (expected behavior in async systems)
```
1. Both hooks run concurrently
   - Race condition: mde cleanup vs plugin API calls
   - Potential deadlock if both try to acquire same resource
```
**Issue**: Unpredictable interleaving of side effects.

### Why This Matters
- **guard-install** validates environment before any tool execution
- **SessionStart (plugin)** makes HTTP calls to Honcho API
- If mde's guard runs AFTER plugin's SessionStart, the plugin has already executed with an unvalidated environment
- If plugin's SessionStart runs AFTER mde's guard, the guard might report issues that plugin could have worked around

## Unresolved Questions

1. **Official documentation**: Does Claude Code document hook multiplicity semantics?
   - Checked: .claude/settings.json schema is not published
   - Workaround: Spec should test behavior or ask Plastic Labs for clarification

2. **Session strategy not specified**: Plugin supports per-directory, git-branch, chat-instance
   - Spec assumes "default" behavior but doesn't recommend which one
   - Worktrees (mde's use case) need stable per-directory sessions, not dynamic per-branch
   - **Recommendation**: Document `sessionStrategy: "per-directory"` in spec

3. **Plugin marketplace command not verified**: Is `/plugin marketplace add` a real Claude Code command?
   - README examples show this syntax
   - Spec includes this command
   - **Risk**: If command doesn't exist, users can't install plugin (installation will fail at step 1)

4. **MCP server bundling**: Does plugin's MCP server start on a specific port?
   - Plugin has /mcp/ directory
   - Spec doesn't document if it binds to a port or uses stdio
   - **Risk**: Port conflict with observability stack or existing services

## Recommendations

### BLOCKING CHANGES (Required for PR B merge)

1. **Resolve hook conflict**. Choose ONE:

   **Option A: Declare hook priority in mde hooks**
   ```json
   "SessionStart": [
     {
       "matcher": "",
       "hooks": [
         {
           "type": "command",
           "command": "uv run mde-py hooks session-start",
           "priority": "first"  // Or some documented priority system
         }
       ]
     }
   ]
   ```
   Then document in spec: "mde's SessionStart runs first to guard install, plugin's SessionStart runs second to load memory."

   **Option B: Refactor guard-install out of SessionStart**
   Move guard-install logic to PreToolUse hook (runs before each tool, not just at session start). This way:
   - plugin:SessionStart loads memory safely
   - mde:PreToolUse validates before user runs tools

   **Option C: Disable mde's SessionStart when plugin is present**
   Spec could document: "After installing plugin, disable mde's SessionStart hook in .claude/settings.json if hook conflicts occur. Plugin's SessionStart will handle session initialization."

2. **Test hook execution behavior** with the actual plugin installed:
   ```bash
   # In a fresh Claude Code session with both mde and plugin configured:
   1. Start a session
   2. Check stdout for order of messages (mde output first or plugin output first?)
   3. Check .claude/logs/ for hook execution timestamps
   4. Document findings in spec
   ```

### DOCUMENTATION IMPROVEMENTS (Medium priority)

1. **Session strategy recommendation**:
   ```markdown
   ## Session Strategy for Worktrees

   The plugin supports three session strategies:
   - `per-directory`: Stable sessions per project directory (recommended for mde)
   - `git-branch`: Dynamic sessions per git branch (breaks on branch switch)
   - `chat-instance`: Per-chat sessions (breaks on reconnect)

   **Recommendation for mde**: Use `per-directory` because:
   - Worktrees are long-lived per feature branch
   - Memory should persist for the entire feature development
   - Branch switches create new directories (.worktrees/), so dynamic strategies would fragment memory
   ```

2. **LLM API key management**:
   - Document whether LLM keys are fnox-managed or manual
   - Add instructions for setting up Anthropic/OpenAI keys for deriver
   - Explain why deriver needs multiple LLM providers (embeddings vs reasoning)

3. **Plugin marketplace verification**:
   - Test `/plugin marketplace add plastic-labs/claude-honcho` command
   - If syntax differs, update spec installation steps
   - Document expected output (success/failure messages)

### OPTIONAL (Low priority)

1. **MCP server port documentation**: Clarify how plugin's MCP server communicates with Claude Code (stdio vs TCP)

2. **Diagnostics guide**: Add troubleshooting section for:
   - "Memory not loading at session start"
   - "Plugin marketplace add command not found"
   - "Hook conflicts between mde and plugin"

## Test Plan for PR B

Before merging PR B, author must:

1. **Create test environment**:
   ```bash
   # Fresh Docker compose stack
   docker compose -f docker/compose.yaml up -d
   uv run mde-py memory verify    # Confirm stack health
   ```

2. **Install plugin**:
   ```bash
   # In Claude Code session
   /plugin marketplace add plastic-labs/claude-honcho
   /plugin install honcho@honcho
   # Restart Claude Code
   ```

3. **Verify hook execution**:
   ```bash
   # Start a new session in the repo
   # Check that BOTH:
   # - mde output appears (guard-install message)
   # - plugin output appears (Honcho Memory Loaded message)
   # - Both appear in sensible order
   ```

4. **Document findings**:
   ```bash
   # Add section to PR description or spec:
   # "Hook Execution Test Results"
   # - Tested on: Claude Code v[version]
   # - Bun version: [version]
   # - Hook order: [mde first | plugin first | parallel | conflict]
   # - Behavior: [description of what happened]
   ```

## Conclusion

The honcho-memory design is **architecturally sound** but has a **critical gap** around hook multiplicity that must be resolved before merge. The gap is not a design flaw but an **external dependency** (Claude Code's hook system) that lacks public documentation.

**Recommendation**: Contact Plastic Labs (claude-honcho maintainers) or Claude Code team to clarify hook execution semantics, then update spec with findings.

**Status**: BLOCKED pending hook conflict resolution.
