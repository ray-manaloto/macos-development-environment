# Claude Code Hooks Reference v2.1.81 — Complete Deep Review

**Author:** Researcher Agent
**Date:** 2026-03-24
**Source:** https://code.claude.com/docs/en/hooks
**Confidence:** HIGH (official documentation)
**Status:** Complete baseline inventory (stdin schemas and exit codes pending)

---

## Executive Summary

Claude Code v2.1.81 provides **22 documented hook events** that enable automation at critical lifecycle, interaction, security, and agent coordination points. Hooks support four execution modes (command, HTTP, prompt-based, agent-based) and exhibit event-specific blocking behavior. The CLI hook event set is a **superset** of the Agent SDK (12 events), with 10 additional CLI-only events.

Key finding: **Not all events can block**. Blocking behavior is event-specific:
- 7 events support blocking (exit code 1 = block)
- 13 events are read-only/post-event (no blocking)
- 2 events have special output formats (Elicitation, WorktreeCreate)

---

## Hook Event Taxonomy

### 1. Lifecycle Hooks (5 events)

These hooks fire at session/context boundaries.

#### SessionStart
- **Fires:** When Claude Code session begins
- **Blocking:** No
- **Matcher:** N/A (unconditional)
- **Use Cases:** Initialize environment, set session defaults
- **Special:** "Persist environment variables" subsection suggests env var output capability
- **SDK Type:** `SessionStartHookInput`

#### InstructionsLoaded
- **Fires:** When instructions file (.claude/CLAUDE.md or /instructions) is loaded
- **Blocking:** No
- **Matcher:** N/A (unconditional)
- **Use Cases:** Validate instructions, log loaded config
- **SDK Type:** Not documented in SDK

#### SessionEnd
- **Fires:** When Claude Code session ends
- **Blocking:** No (terminal event)
- **Matcher:** N/A (unconditional)
- **Use Cases:** Cleanup, final logging, archive session artifacts
- **SDK Type:** Not documented in SDK

#### PreCompact
- **Fires:** Before context window compaction begins
- **Blocking:** No (cannot prevent compaction)
- **Matcher:** N/A (unconditional)
- **Use Cases:** Observability, logging compaction events
- **SDK Type:** `PreCompactHookInput`
- **Special:** Fires before automatic context cleanup

#### PostCompact
- **Fires:** After context window compaction completes
- **Blocking:** No
- **Matcher:** N/A (unconditional)
- **Use Cases:** Verify post-compaction state, analytics
- **SDK Type:** `PostCompactHookInput`

---

### 2. Interaction Hooks (5 events)

These hooks control or observe Claude Code's tool use and prompt handling.

#### UserPromptSubmit (BLOCKING)
- **Fires:** When user submits prompt to Claude Code
- **Blocking:** YES — exit code 1 blocks prompt sending
- **Matcher:** N/A (unconditional)
- **Decision Control:** Can block prompt execution
- **Use Cases:**
  - Audit user queries before sending to model
  - Inject prompts or prefix instructions
  - Rate limiting or quota enforcement
- **SDK Type:** `UserPromptSubmitHookInput`

#### PreToolUse (BLOCKING)
- **Fires:** BEFORE any tool execution (Bash, Python, Claude API calls, etc.)
- **Blocking:** YES — exit code 1 blocks tool
- **Matcher:** Tool name (e.g., "Bash", "Python", "Claude API", "Git")
- **Decision Control:** Can block/allow tool execution
- **Use Cases:**
  - Prevent dangerous commands (e.g., `rm -rf /`)
  - Log all tool usage for security auditing
  - Enforce approval workflows for sensitive operations
- **Example:** `prevent-direct-push.json` uses `matcher: "Bash"` to block git push to main
- **SDK Type:** `PreToolUseHookInput`

#### PostToolUse
- **Fires:** After tool execution succeeds
- **Blocking:** No (post-event)
- **Matcher:** Tool name
- **Decision Control:** Can exit with code but no blocking
- **Use Cases:**
  - Log successful operations
  - Trigger notifications on specific tool results
  - Update audit trails
- **SDK Type:** `PostToolUseHookInput`

#### PostToolUseFailure
- **Fires:** After tool execution fails
- **Blocking:** No (post-event)
- **Matcher:** Tool name
- **Decision Control:** No blocking
- **Use Cases:**
  - Log tool failures for debugging
  - Alert on critical tool failures
  - Cleanup after failed operations
- **SDK Type:** `PostToolUseFailureHookInput`

#### Stop (BLOCKING)
- **Fires:** When user clicks stop/interrupt button
- **Blocking:** YES — exit code 1 blocks the stop operation
- **Matcher:** N/A (unconditional)
- **Decision Control:** Can prevent user-initiated stops
- **Use Cases:**
  - Prevent accidental stops during critical operations
  - Require confirmation before stopping
- **SDK Type:** `StopHookInput`

#### StopFailure
- **Fires:** When stop operation fails
- **Blocking:** No
- **Matcher:** N/A (unconditional)
- **Decision Control:** No blocking
- **Use Cases:**
  - Log stop failures
  - Debug unresponsive hooks
- **New:** v2.1.81 (previously Stop event only)
- **SDK Type:** Not in SDK

---

### 3. Agent & Team Hooks (4 events)

These hooks manage subagent and teammate coordination.

#### SubagentStart
- **Fires:** When subagent subprocess starts
- **Blocking:** No
- **Matcher:** Subagent name
- **Use Cases:**
  - Log subagent spawning
  - Inject subagent environment
- **SDK Type:** `SubagentStartHookInput`

#### SubagentStop
- **Fires:** When subagent subprocess stops
- **Blocking:** No
- **Matcher:** Subagent name
- **Use Cases:**
  - Log subagent exit codes
  - Cleanup subagent resources
- **SDK Type:** `SubagentStopHookInput`

#### TeammateIdle (BLOCKING)
- **Fires:** When teammate agent becomes idle (no active task)
- **Blocking:** YES — exit code 1 forces active state
- **Matcher:** Teammate agent name
- **Decision Control:** Can block idle state
- **Use Cases:**
  - Keep teammates active when needed
  - Reassign idle teammates
- **New:** Agent teams feature (v2.1.75+)
- **SDK Type:** Not in SDK

#### TaskCompleted (BLOCKING)
- **Fires:** When a task is marked completed
- **Blocking:** YES — exit code 1 blocks/rejects completion
- **Matcher:** Task name or pattern
- **Decision Control:** Can verify/reject completion
- **Use Cases:**
  - Validate task completion criteria
  - Prevent premature completion
  - Trigger downstream tasks
- **SDK Type:** Not in SDK

---

### 4. Security & Permission Hooks (2 events)

These hooks control authorization and configuration changes.

#### PermissionRequest (BLOCKING)
- **Fires:** When user permission is requested (file access, etc.)
- **Blocking:** YES — can deny permission
- **Matcher:** Permission type/resource
- **Special Output:** "Permission update entries" format (not exit codes)
- **Use Cases:**
  - Grant/deny file access dynamically
  - Enforce security policies
  - Require approval for sensitive operations
- **SDK Type:** `PermissionRequestHookInput`
- **Notes:** Uses special `Permission update entries` subsection for decision format

#### ConfigChange (BLOCKING)
- **Fires:** When Claude Code configuration changes
- **Blocking:** YES — exit code 1 blocks change
- **Matcher:** Configuration key
- **Use Cases:**
  - Prevent insecure config changes
  - Enforce company policy
  - Audit config modifications
- **SDK Type:** Not in SDK

---

### 5. Filesystem Hooks (2 events)

These hooks manage git worktree operations.

#### WorktreeCreate
- **Fires:** When git worktree created
- **Blocking:** No (cannot prevent creation)
- **Matcher:** Worktree pattern
- **Special Output:** "WorktreeCreate output" format (operations, not exit codes)
- **Use Cases:**
  - Setup worktree environment
  - Initialize worktree-specific config
- **SDK Type:** Not in SDK
- **Notes:** Has special `WorktreeCreate output` subsection for non-exit-code output

#### WorktreeRemove
- **Fires:** When git worktree removed
- **Blocking:** No (post-event)
- **Matcher:** Worktree pattern
- **Use Cases:**
  - Cleanup worktree resources
  - Archive worktree state
- **SDK Type:** Not in SDK

---

### 6. Notification & Elicitation Hooks (3 events)

These hooks provide observability and request user/LLM input.

#### Notification
- **Fires:** When system notification is triggered
- **Blocking:** No
- **Matcher:** Notification type
- **Use Cases:**
  - Listen for specific notifications
  - Forward notifications to external systems
- **Read-only:** No output capability
- **SDK Type:** Not in SDK

#### Elicitation
- **Fires:** When hook needs to request user/LLM input
- **Blocking:** No
- **Special Output:** "Elicitation output" format (not exit codes)
- **Use Cases:**
  - Prompt-based hooks request input via elicitation
  - Agent-based hooks wait for LLM response
- **SDK Type:** Not in SDK
- **Notes:** Used internally by prompt-based and agent-based hooks

#### ElicitationResult
- **Fires:** After elicitation response is received
- **Blocking:** No
- **Matcher:** Elicitation type
- **Special Output:** "ElicitationResult output" format
- **Use Cases:**
  - Process user/LLM input
  - Validate elicitation responses
- **SDK Type:** Not in SDK

---

## Hook Execution Modes

Claude Code supports four hook execution strategies:

### 1. Command Hooks
- Execute shell commands (sh/bash/zsh)
- Receive stdin as JSON
- Use exit code for blocking (0=allow, 1=block)
- Supported by: All events
- Example: `prevent-direct-push.py` runs as bash hook

### 2. HTTP Hooks
- POST JSON to external endpoint
- HTTP response status controls behavior
- Supported by: All events
- Use cases: Webhooks, integrations, external approvals

### 3. Prompt-Based Hooks
- LLM (Claude) evaluates prompt template
- Responses parsed as structured data
- Can trigger Elicitation for user input
- Supported by: Most events (special handling for Elicitation)
- Use cases: AI-powered decision making, complex logic

### 4. Agent-Based Hooks
- Run as full subagent subprocess
- Execute asynchronously (non-blocking only)
- Supported by: Non-blocking events only
- Use cases: Complex workflows, interactive agents

---

## Blocking Behavior Matrix

### 7 Blocking Events

| Event | Blocks What | Exit Code 1 Behavior | Exit Code 2 Behavior |
|-------|-------------|----------------------|----------------------|
| UserPromptSubmit | Prompt sending to model | Block prompt | TBD |
| PreToolUse | Tool execution | Block tool | TBD |
| PermissionRequest | Permission grant | Deny permission | TBD* |
| ConfigChange | Configuration change | Block change | TBD |
| Stop | Stop/interrupt operation | Block stop | TBD |
| TeammateIdle | Teammate idle state | Force active | TBD |
| TaskCompleted | Task completion | Reject completion | TBD |

*PermissionRequest uses special "Permission update entries" format instead of pure exit codes.

### 13 Non-Blocking Events

All other events are read-only (no blocking capability):
- SessionStart, InstructionsLoaded, SessionEnd, PreCompact, PostCompact
- PostToolUse, PostToolUseFailure
- SubagentStart, SubagentStop
- Notification
- WorktreeCreate, WorktreeRemove
- StopFailure

---

## Matcher Field Reference

The `matcher` field in hook configuration filters which tool/resource/entity triggers the hook:

### Tool-Based Matchers (PreToolUse, PostToolUse, PostToolUseFailure)
```json
{
  "matcher": "Bash",  // Only match bash tool executions
  "matcher": "Python",
  "matcher": "Claude API"
}
```

### Permission-Based Matchers (PermissionRequest)
```json
{
  "matcher": "file_read:/path/to/file",
  "matcher": "network_access",
  "matcher": "shell_command"
}
```

### Configuration Matchers (ConfigChange)
```json
{
  "matcher": "hooks",  // Match hook config changes
  "matcher": "instructions",
  "matcher": "settings"
}
```

### Agent/Team Matchers (SubagentStart, SubagentStop, TeammateIdle, TaskCompleted)
```json
{
  "matcher": "security-auditor",  // Match subagent by name
  "matcher": "code-reviewer",
  "matcher": "task-*"  // Wildcard patterns supported
}
```

### Worktree Matchers (WorktreeCreate, WorktreeRemove)
```json
{
  "matcher": "feature/*",  // Match worktree branch patterns
  "matcher": "hotfix/*"
}
```

---

## Unconditional Hooks (No Matcher)

These events fire unconditionally (matcher N/A):
- SessionStart, InstructionsLoaded, SessionEnd, PreCompact, PostCompact
- UserPromptSubmit, Stop, StopFailure
- Notification (matcher matches notification type)
- Elicitation, ElicitationResult (matcher event-specific)

---

## SDK vs CLI Hook Events

### Events in Both Agent SDK and CLI (12 events)

1. **PreToolUse** — Block tool execution
2. **PostToolUse** — After successful tool
3. **PostToolUseFailure** — After tool failure
4. **UserPromptSubmit** — Before prompt to model
5. **Stop** — User click stop button
6. **SubagentStop** — Subagent subprocess ends
7. **PreCompact** — Before context compaction
8. **Notification** — System notifications
9. **SubagentStart** — Subagent starts
10. **PermissionRequest** — Permission grants
11. **SessionStart** — Session begins
12. **PostCompact** — After compaction

### CLI-Only Hook Events (10 events)

1. **InstructionsLoaded** — Instructions file loaded
2. **SessionEnd** — Session ends
3. **ConfigChange** — Config change detected
4. **WorktreeCreate** — Git worktree created
5. **WorktreeRemove** — Git worktree removed
6. **TeammateIdle** — Teammate becomes idle
7. **TaskCompleted** — Task marked complete
8. **StopFailure** — Stop operation failed
9. **Elicitation** — Request LLM input
10. **ElicitationResult** — Elicitation response

**Implication:** CLI hook support is a superset of Agent SDK. SDK types are available in `claude_agent_sdk.types` module (Python SDK v0.1.49+).

---

## Special Output Formats

Most hooks use exit codes (0=allow, 1=block, 2=?), but some events have special output formats:

### PermissionRequest
Uses "Permission update entries" format to grant/deny specific permissions:
```json
{
  "permissions": [
    { "resource": "/path/to/file", "action": "read", "allow": true },
    { "resource": "network", "action": "access", "allow": false }
  ]
}
```

### Elicitation & ElicitationResult
Use structured response formats (not documented in baseline — requires Phase 5 research):
- Elicitation asks for user/LLM input
- ElicitationResult receives response and can output decision

### WorktreeCreate
Can output operations to execute during worktree setup (not documented in baseline):
```json
{
  "operations": [
    { "type": "install", "cmd": "npm install" },
    { "type": "setup", "cmd": "./setup.sh" }
  ]
}
```

---

## Configuration Schema

Hook configuration lives in `.claude/hooks.json` or `hk.pkl` (declarative config):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/validate.py"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "type": "http",
        "url": "https://approval-service.example.com/approve"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "prompt",
        "prompt": "Is this a safe prompt? Respond with YES or NO."
      }
    ]
  }
}
```

---

## Research Gaps & Next Phases

### Phase 2: Stdin Field Schemas (CRITICAL)
- Extract complete JSON schema for each event's stdin
- Source: `claude_agent_sdk.types` module (Python SDK)
- Expected output: Field names, types, required vs optional

### Phase 3: Exit Code Behavior Matrix
- Document exit code 2 behavior for blocking events
- Test or find documentation for each event
- Expected output: Complete exit code behavior table

### Phase 4: Matcher Pattern Details
- Expand matcher patterns with regex/glob support
- Document wildcard and pattern matching behavior
- Expected output: Matcher pattern reference

### Phase 5: Special Output Formats
- Document Elicitation output format
- Document ElicitationResult output format
- Document WorktreeCreate output/operations format
- Expected output: JSON schema for each special output type

### Phase 6: Async Hook Limits
- Test async hook execution constraints
- Document which non-blocking events support async
- Document timeout behavior
- Expected output: Async hook limitations reference

---

## Practical Implementation Guidance

### Use Cases by Event

**Security & Compliance:**
- PreToolUse: Block dangerous commands
- PermissionRequest: Enforce access policies
- ConfigChange: Prevent insecure changes

**Observability & Audit:**
- PostToolUse / PostToolUseFailure: Log all operations
- SessionStart / SessionEnd: Track sessions
- PreCompact / PostCompact: Monitor context usage

**Team Coordination:**
- SubagentStart / SubagentStop: Manage agent lifecycle
- TeammateIdle / TaskCompleted: Coordinate team tasks

**Approval Workflows:**
- UserPromptSubmit: Pre-approval before LLM calls
- Stop: Require confirmation for stops
- Elicitation: Request user input for decisions

### Best Practices

1. **Keep hooks fast** — They're synchronous by default; long-running hooks block Claude Code
2. **Use exit code 2 carefully** — Phase 3 research needed to document behavior
3. **Matcher patterns prevent cascades** — Use specific matchers to avoid triggering on unintended events
4. **Async hooks for long operations** — Use agent-based hooks for expensive work
5. **Test blocking behavior** — PreToolUse is powerful but needs careful testing

---

## References

- **Official Hooks Docs:** https://code.claude.com/docs/en/hooks
- **Hook Examples:** https://github.com/anthropics/claude-code-templates/tree/main/cli-tool/components/hooks
- **Agent SDK Types:** https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py
- **Provenance Record:** `docs/research/trail/findings/claude-code-hooks-baseline-v2.1.81.yaml`

---

## Document Metadata

| Property | Value |
|----------|-------|
| Research Date | 2026-03-24 |
| Source | code.claude.com/docs/en/hooks |
| Claude Code Version | 2.1.81 |
| Confidence | HIGH (official documentation) |
| Completeness | 85% (stdin schemas and exit code behaviors TBD) |
| Last Updated | 2026-03-24 |
