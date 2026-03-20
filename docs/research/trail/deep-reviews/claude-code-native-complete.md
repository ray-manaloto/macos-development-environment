# Claude Code Native Features -- Complete Reference

> Compiled 2026-03-20 from 15 primary sources at code.claude.com/docs and anthropic.com/engineering.
> This document is the definitive reference for all native Claude Code capabilities.

---

## 1. CLAUDE.md Organization

### Recommended Structure and Size

- Target under **200 lines** per CLAUDE.md file
- Longer files consume more context and reduce adherence
- Use markdown headers and bullets to group related instructions
- Write instructions specific enough to verify ("Use 2-space indentation" not "Format code properly")
- If two rules contradict, Claude may pick one arbitrarily

### File Hierarchy (Precedence: Higher Overrides Lower)

| Scope | Location | Purpose | Shared With |
|---|---|---|---|
| **Managed policy** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL: `/etc/claude-code/CLAUDE.md`; Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | Organization-wide instructions managed by IT/DevOps | All users in org |
| **Project instructions** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared instructions for the project | Team via source control |
| **User instructions** | `~/.claude/CLAUDE.md` | Personal preferences for all projects | Just you |

CLAUDE.md files in the directory hierarchy above the working directory are loaded in full at launch. CLAUDE.md files in subdirectories load on demand when Claude reads files in those directories.

### .claude/rules/ with Path-Scoped Frontmatter

Place markdown files in `.claude/rules/` directory. Each file covers one topic. Files are discovered recursively (subdirectories supported).

Rules without `paths` frontmatter are loaded at launch unconditionally. Rules WITH `paths` frontmatter only load when Claude works with matching files:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
...
```

Glob patterns supported:

| Pattern | Matches |
|---|---|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under src/ |
| `*.md` | Markdown files in root |
| `src/components/*.tsx` | React components in specific dir |

Multiple patterns and brace expansion work: `"src/**/*.{ts,tsx}"`.

User-level rules: `~/.claude/rules/` apply to every project. Loaded before project rules (lower priority).

Symlinks are supported and resolved normally.

### @import Syntax

CLAUDE.md files can import additional files using `@path/to/import` syntax:

```text
See @README for project overview and @package.json for available npm commands.
@docs/git-instructions.md
@~/.claude/my-project-instructions.md
```

- Both relative and absolute paths are allowed
- Relative paths resolve relative to the file containing the import
- Imported files can recursively import (max depth: 5 hops)
- First-time external imports show an approval dialog

### claudeMdExcludes

Setting in `.claude/settings.local.json` to skip specific CLAUDE.md files:

```json
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}
```

Patterns match against absolute paths using glob syntax. Configurable at any settings layer. **Managed policy CLAUDE.md files cannot be excluded.**

### Additional Directories

`--add-dir` flag gives Claude access to extra directories. CLAUDE.md files from these dirs are NOT loaded by default. Set `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to also load them.

### Auto Memory vs CLAUDE.md

| | CLAUDE.md files | Auto memory |
|---|---|---|
| **Who writes it** | You | Claude |
| **What it contains** | Instructions and rules | Learnings and patterns |
| **Scope** | Project, user, or org | Per working tree |
| **Loaded into** | Every session (full) | Every session (first 200 lines of MEMORY.md) |
| **Use for** | Coding standards, workflows, architecture | Build commands, debugging insights, preferences |

Auto memory storage: `~/.claude/projects/<project>/memory/` (derived from git repo). Contains `MEMORY.md` (index) plus topic files. Machine-local. All worktrees/subdirs within same git repo share one directory.

Enable/disable: `/memory` command, or `"autoMemoryEnabled": false` in settings, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.

Custom directory: `"autoMemoryDirectory": "~/my-memory-dir"` (not accepted from project settings).

---

## 2. Subagent System

### Overview

Subagents are specialized AI assistants running in their own context window with custom system prompt, specific tool access, and independent permissions. They cannot spawn other subagents.

### Complete Frontmatter Field Reference

| Field | Required | Type | Description |
|---|---|---|---|
| `name` | Yes | string | Unique identifier, lowercase letters and hyphens |
| `description` | Yes | string | When Claude should delegate to this subagent |
| `tools` | No | comma-separated string | Tools the subagent can use (inherits all if omitted) |
| `disallowedTools` | No | comma-separated string | Tools to deny, removed from inherited or specified list |
| `model` | No | string | `sonnet`, `opus`, `haiku`, full model ID (e.g. `claude-opus-4-6`), or `inherit`. Default: `inherit` |
| `permissionMode` | No | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | number | Maximum agentic turns before subagent stops |
| `skills` | No | list | Skills to preload into subagent context at startup |
| `mcpServers` | No | list | MCP servers (inline definitions or string references) |
| `hooks` | No | object | Lifecycle hooks scoped to this subagent |
| `memory` | No | string | `user`, `project`, or `local` -- enables cross-session learning |
| `background` | No | boolean | `true` to always run as background task. Default: `false` |
| `effort` | No | string | `low`, `medium`, `high`, `max` (Opus 4.6 only). Overrides session |
| `isolation` | No | string | `worktree` -- run in temporary git worktree |

### Built-in Subagents

**Explore**: Fast read-only agent for codebase search/analysis.
- Model: Haiku (fast, low-latency)
- Tools: Read-only (denied Write and Edit)
- Thoroughness levels: quick, medium, very thorough

**Plan**: Research agent for plan mode.
- Model: Inherits from main conversation
- Tools: Read-only (denied Write and Edit)
- Used when in plan mode for codebase research

**General-purpose**: Capable agent for complex multi-step tasks.
- Model: Inherits from main conversation
- Tools: All tools
- Used for tasks requiring both exploration and modification

**Other built-in agents**:

| Agent | Model | Purpose |
|---|---|---|
| Bash | Inherits | Running terminal commands in separate context |
| statusline-setup | Sonnet | When running `/statusline` |
| Claude Code Guide | Haiku | Questions about Claude Code features |

### Memory Scopes

| Scope | Location | Use when |
|---|---|---|
| `user` | `~/.claude/agent-memory/<name>/` | Learnings across all projects |
| `project` | `.claude/agent-memory/<name>/` | Project-specific, shareable via VCS |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific, not checked in |

When memory is enabled: system prompt includes read/write instructions; first 200 lines of MEMORY.md included; Read, Write, Edit tools auto-enabled.

### Tool Restrictions: Agent(type) Syntax

When agent runs as main thread with `claude --agent`, restrict spawnable subagents:

```yaml
tools: Agent(worker, researcher), Read, Bash
```

This is an allowlist. `Agent` without parentheses = unrestricted. Omitting `Agent` entirely = cannot spawn subagents.

Note: In v2.1.63, Task tool was renamed to Agent. `Task(...)` still works as alias.

### Scoped MCP Servers

```yaml
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github  # reference existing server
```

Inline servers connected when subagent starts, disconnected when finished.

### Permission Modes

| Mode | Behavior |
|---|---|
| `default` | Standard permission checking |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny prompts (explicitly allowed tools still work) |
| `bypassPermissions` | Skip permission prompts (USE WITH CAUTION) |
| `plan` | Plan mode (read-only exploration) |

If parent uses `bypassPermissions`, it takes precedence and cannot be overridden.

### /agents Command

Interactive interface: view all subagents (built-in, user, project, plugin), create new, edit, delete. `claude agents` (CLI) lists agents without interactive session.

### Subagent Scope Priority

| Location | Priority |
|---|---|
| `--agents` CLI flag | 1 (highest) |
| `.claude/agents/` | 2 |
| `~/.claude/agents/` | 3 |
| Plugin's `agents/` | 4 (lowest) |

### --agent Flag and --agents JSON Flag

`claude --agent code-reviewer` -- run entire session as that subagent (replaces default system prompt).

`claude --agents '{"reviewer":{"description":"...","prompt":"...","tools":["Read"],"model":"sonnet"}}'` -- define session-only subagents via JSON.

### Resume via SendMessage

Each subagent invocation creates fresh context. To continue: ask Claude to resume. Claude uses `SendMessage` tool with agent's ID. Transcripts persist at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.

### Background vs Foreground Execution

- **Foreground**: Blocks main conversation. Permission prompts passed through.
- **Background**: Run concurrently. Pre-approves permissions upfront. Auto-denies anything not pre-approved. Clarifying questions fail silently.

Disable background tasks: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.

Press **Ctrl+B** to background a running task.

---

## 3. Agent Teams

### Architecture

| Component | Role |
|---|---|
| **Team lead** | Main session that creates team, spawns teammates, coordinates |
| **Teammates** | Separate Claude Code instances working on tasks |
| **Task list** | Shared list with states: pending, in progress, completed (supports dependencies) |
| **Mailbox** | Messaging system for inter-agent communication |

### Enable Flag

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Requires Claude Code v2.1.32+.

### Display Modes

- **In-process** (default): All teammates in main terminal. Shift+Down to cycle. Works in any terminal.
- **Split panes** (tmux/iTerm2): Each teammate in own pane. Click to interact. Requires tmux or iTerm2 with `it2` CLI.
- **auto** (default `teammateMode`): Split if already in tmux, in-process otherwise.

```json
{ "teammateMode": "in-process" }
```

CLI flag: `claude --teammate-mode in-process`

### Task Claiming with File Locking

Tasks have three states: pending, in-progress, completed. Dependencies supported (blocked until deps complete). Task claiming uses **file locking** to prevent race conditions. Lead can assign explicitly or teammates self-claim.

Storage:
- Team config: `~/.claude/teams/{team-name}/config.json`
- Task list: `~/.claude/tasks/{team-name}/`

### Plan Approval Workflow

Require teammates to plan before implementing. Teammate works in read-only plan mode, sends plan approval request to lead. Lead approves or rejects with feedback. If rejected, teammate revises and resubmits.

### TeammateIdle and TaskCompleted Hooks

- **TeammateIdle**: Runs when teammate about to go idle. Exit code 2 sends feedback, keeps working.
- **TaskCompleted**: Runs when task being marked complete. Exit code 2 prevents completion, sends feedback.

### All 7 Limitations

1. No session resumption with in-process teammates (`/resume` and `/rewind` don't restore)
2. Task status can lag (teammates sometimes fail to mark tasks completed)
3. Shutdown can be slow (teammates finish current request before stopping)
4. One team per session
5. No nested teams (teammates can't spawn their own teams)
6. Lead is fixed (can't promote teammate or transfer leadership)
7. Permissions set at spawn (all get lead's mode; can change individual after spawning)

Split panes NOT supported in VS Code terminal, Windows Terminal, or Ghostty.

### Recommended Team Size

**3-5 teammates** for most workflows. 5-6 tasks per teammate keeps everyone productive.

---

## 4. Hooks System

### All 22 Hook Events

| Event | When | Can Block | Matcher |
|---|---|---|---|
| `SessionStart` | Session begins/resumes | No | `startup`, `resume`, `clear`, `compact` |
| `SessionEnd` | Session terminates | No | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `UserPromptSubmit` | User submits prompt | Yes (exit 2) | None |
| `PreToolUse` | Before tool executes | Yes (exit 2) | Tool name |
| `PermissionRequest` | Permission dialog appears | Yes (exit 2) | Tool name |
| `PostToolUse` | After tool succeeds | No | Tool name |
| `PostToolUseFailure` | After tool fails | No | Tool name |
| `Notification` | Notification sent | No | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |
| `SubagentStart` | Subagent spawned | No | Agent type |
| `SubagentStop` | Subagent finishes | Yes (exit 2) | Agent type |
| `Stop` | Claude finishes responding | Yes (exit 2) | None |
| `StopFailure` | Turn ends due to API error | No | Error type |
| `TeammateIdle` | Teammate about to go idle | Yes (exit 2) | None |
| `TaskCompleted` | Task marked complete | Yes (exit 2) | None |
| `InstructionsLoaded` | CLAUDE.md/.claude/rules loaded | No | Load reason |
| `ConfigChange` | Config file changes | Yes (exit 2, except policy) | Config source |
| `WorktreeCreate` | Worktree created | Yes (non-zero fails) | None |
| `WorktreeRemove` | Worktree removed | No | None |
| `PreCompact` | Before compaction | No | `manual`, `auto` |
| `PostCompact` | After compaction | No | `manual`, `auto` |
| `Elicitation` | MCP requests user input | Yes (exit 2) | MCP server name |
| `ElicitationResult` | User responds to elicitation | Yes (exit 2) | MCP server name |

### 4 Handler Types

**Command** (`type: "command"`):
```json
{ "type": "command", "command": "shell command", "timeout": 600, "async": false }
```

**HTTP** (`type: "http"`):
```json
{ "type": "http", "url": "http://localhost:8080/endpoint", "headers": {"Authorization": "Bearer $MY_TOKEN"}, "allowedEnvVars": ["MY_TOKEN"] }
```

**Prompt** (`type: "prompt"`): Single-turn LLM evaluation returning yes/no.
```json
{ "type": "prompt", "prompt": "Evaluate this...", "model": "claude-opus-4-1", "timeout": 30 }
```

**Agent** (`type: "agent"`): Multi-turn subagent with tool access.
```json
{ "type": "agent", "prompt": "Verify this...", "timeout": 60 }
```

Common fields (all types): `timeout`, `statusMessage`, `once`.

### Exit Code Semantics

| Exit Code | Behavior |
|---|---|
| **0** | Success. Parse stdout for JSON. |
| **2** | Blocking error. stderr fed to Claude/user. |
| **Other** | Non-blocking error. stderr shown in verbose mode. |

### JSON Output Format

```json
{
  "continue": true,
  "stopReason": "reason when continue=false",
  "suppressOutput": false,
  "systemMessage": "warning to user",
  "decision": "block",
  "reason": "explanation",
  "hookSpecificOutput": { "hookEventName": "EventName", ... }
}
```

#### PreToolUse Decision Control:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "reason",
    "updatedInput": { "command": "modified" },
    "additionalContext": "context for Claude"
  }
}
```

#### PermissionRequest Decision Control:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow|deny",
      "updatedInput": {...},
      "updatedPermissions": [{
        "type": "addRules|replaceRules|removeRules|setMode|addDirectories|removeDirectories",
        "rules": [{"toolName": "Bash", "ruleContent": "npm test"}],
        "behavior": "allow|deny|ask",
        "destination": "session|localSettings|projectSettings|userSettings"
      }],
      "message": "for deny only"
    }
  }
}
```

### Async Hooks

Command hooks support `"async": true` to run without blocking.

### SessionStart CLAUDE_ENV_FILE Pattern

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

### Hooks in Skill/Agent Frontmatter

Hooks defined in subagent or skill frontmatter run only while that component is active:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
```

`Stop` hooks in frontmatter are auto-converted to `SubagentStop` events.

### Hook Locations

| Location | Scope |
|---|---|
| `~/.claude/settings.json` | All projects |
| `.claude/settings.json` | Single project (shareable) |
| `.claude/settings.local.json` | Single project (local) |
| Managed policy settings | Organization-wide |
| Plugin `hooks/hooks.json` | When plugin enabled |
| Skill/agent frontmatter | While active |

### Environment Variables

- `$CLAUDE_PROJECT_DIR` -- project root
- `${CLAUDE_PLUGIN_ROOT}` -- plugin installation dir
- `${CLAUDE_PLUGIN_DATA}` -- plugin persistent data dir
- `$CLAUDE_ENV_FILE` -- SessionStart only
- `$CLAUDE_CODE_REMOTE` -- "true" in remote environments

Disable all hooks: `"disableAllHooks": true`

---

## 5. Skills System

### SKILL.md Format and Frontmatter Reference

```yaml
---
name: my-skill
description: What this skill does
argument-hint: "[issue-number]"
disable-model-invocation: true
user-invocable: false
allowed-tools: Read, Grep, Glob
model: sonnet
effort: high
context: fork
agent: Explore
hooks:
  PreToolUse: [...]
---

Skill instructions in markdown...
```

| Field | Required | Description |
|---|---|---|
| `name` | No | Display name (defaults to directory name). Lowercase, hyphens, max 64 chars |
| `description` | Recommended | What and when. Claude uses this for auto-invocation |
| `argument-hint` | No | Hint during autocomplete (e.g. `[issue-number]`) |
| `disable-model-invocation` | No | `true` = only user can invoke. Default: `false` |
| `user-invocable` | No | `false` = hidden from / menu. Default: `true` |
| `allowed-tools` | No | Tools allowed without permission when skill active |
| `model` | No | Model when skill active |
| `effort` | No | `low`, `medium`, `high`, `max` (Opus 4.6 only) |
| `context` | No | `fork` = run in forked subagent context |
| `agent` | No | Which subagent type when `context: fork` (default: general-purpose) |
| `hooks` | No | Hooks scoped to skill lifecycle |

### Bundled Skills

| Skill | Purpose |
|---|---|
| `/batch <instruction>` | Orchestrate large-scale parallel changes. Researches, decomposes into 5-30 units, spawns background agents in git worktrees |
| `/claude-api` | Load Claude API reference for project language. Auto-activates on anthropic imports |
| `/debug [description]` | Troubleshoot current session by reading debug log |
| `/loop [interval] <prompt>` | Run prompt repeatedly on interval (e.g. `/loop 5m check deploy`) |
| `/simplify [focus]` | Review changed files, spawn 3 review agents in parallel, apply fixes |

### context: fork + agent Field

`context: fork` runs skill in isolated subagent. Skill content becomes the task prompt:

```yaml
context: fork
agent: Explore
```

The `agent` field specifies execution environment: built-in (`Explore`, `Plan`, `general-purpose`) or custom from `.claude/agents/`.

### !`command` Dynamic Injection

Shell commands run before skill content sent to Claude. Output replaces placeholder:

```yaml
## PR Context
- PR diff: !`gh pr diff`
- Changed files: !`gh pr diff --name-only`
```

### String Substitutions

| Variable | Description |
|---|---|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` | Specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing SKILL.md |

### Skill Description Budget

Descriptions loaded into context so Claude knows what's available. Budget scales dynamically at **2% of context window**, fallback 16,000 characters. Override: `SLASH_COMMAND_TOOL_CHAR_BUDGET`.

### Invocation Control

| Frontmatter | You can invoke | Claude can invoke | Context loading |
|---|---|---|---|
| (default) | Yes | Yes | Description always, full on invoke |
| `disable-model-invocation: true` | Yes | No | Not in context |
| `user-invocable: false` | No | Yes | Description always, full on invoke |

### Where Skills Live

| Location | Path | Applies to |
|---|---|---|
| Enterprise | Managed settings | All users |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project only |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin enabled |

Priority: enterprise > personal > project. Plugin skills namespaced (`plugin:skill`).

### Trigger "ultrathink"

Include the word "ultrathink" anywhere in skill content to enable extended thinking.

---

## 6. Anthropic Engineering Patterns

### Building Effective Agents (Core Principles)

1. **Simplicity**: most successful implementations use simple, composable patterns, not complex frameworks
2. **Transparency**: explicitly show planning steps
3. **Agent-Computer Interface (ACI)**: invest as much in tool design as in HCI
4. **Start simple**: optimize single LLM calls first, add agentic complexity only when needed

**Workflow patterns** (prescriptive code paths):
- Prompt chaining (sequential steps with gates)
- Routing (classify input, direct to specialist)
- Parallelization (sectioning or voting)
- Orchestrator-workers (dynamic decomposition)
- Evaluator-optimizer (generate + evaluate loop)

**Agents** (LLMs dynamically directing tool usage in a loop):
- For open-ended problems where steps can't be predicted
- Need ground truth from environment at each step
- Include stopping conditions
- Test extensively in sandboxed environments

**Tool design advice**:
- Give model tokens to "think" before writing itself into a corner
- Keep format close to naturally occurring text
- No formatting overhead (counting lines, escaping JSON)
- Use absolute filepaths (relative paths cause mistakes)
- Treat tool definitions like docstrings for a junior developer
- Poka-yoke: make arguments harder to misuse

### Effective Harnesses for Long-Running Agents

**The problem**: Compaction alone is insufficient. Agents try to one-shot, leave half-implemented features, or declare victory prematurely.

**Two-part solution**:

1. **Initializer agent** (first session): Sets up environment:
   - `init.sh` script to run dev server
   - `claude-progress.txt` -- log of what agents have done
   - `feature_list.json` -- comprehensive feature list (200+ features), all initially "failing"
   - Initial git commit

2. **Coding agent** (every subsequent session): Makes incremental progress:
   - Read progress file and git logs
   - Run basic end-to-end test first
   - Choose ONE feature to work on
   - Implement and test end-to-end (browser automation)
   - Commit with descriptive message
   - Update progress file
   - Only change `passes` field in feature list

**Key insights**:
- **JSON over Markdown** for structured data (model less likely to inappropriately modify JSON)
- **One feature per session** prevents overreach
- **claude-progress.txt** bridges context windows
- **Git history** provides state recovery
- Strongly-worded instructions: "It is unacceptable to remove or edit tests"

### Effective Context Engineering for AI Agents

**Core concept**: Context engineering = curating the optimal set of tokens during LLM inference. Natural progression of prompt engineering.

**Context rot**: As tokens increase, recall accuracy decreases (n^2 pairwise relationships). Treat context as finite resource with diminishing marginal returns.

**System prompts**: Find the "right altitude" -- specific enough to guide behavior, flexible enough for strong heuristics. Use XML tags or Markdown headers for sections.

**Tools**: Self-contained, robust to error, minimal overlap. Bloated tool sets = ambiguous decision points. If a human can't tell which tool to use, neither can the agent.

**Just-in-time retrieval**: Maintain lightweight identifiers (file paths, queries, links), dynamically load at runtime. Claude Code's hybrid model: CLAUDE.md loaded up front, glob/grep for just-in-time navigation.

**Long-horizon techniques**:
1. **Compaction**: Summarize conversation, reinitiate with summary + 5 most recent files. Maximize recall first, then improve precision.
2. **Structured note-taking**: Agent writes persistent notes (NOTES.md, to-do lists) outside context window.
3. **Sub-agent architectures**: Specialized sub-agents explore extensively (tens of thousands of tokens), return condensed 1,000-2,000 token summaries.

**Guiding principle**: Find the smallest set of high-signal tokens that maximize likelihood of desired outcome.

---

## Appendix A: CLI Reference (Key Flags)

| Flag | Description |
|---|---|
| `--agent <name>` | Run session as named subagent |
| `--agents <json>` | Define subagents via JSON |
| `--add-dir <path>` | Add working directories |
| `--allowedTools` | Tools that skip permission prompts |
| `--disallowedTools` | Tools removed from context |
| `--append-system-prompt` | Append to default system prompt |
| `--system-prompt` | Replace entire system prompt |
| `--effort` | `low`, `medium`, `high`, `max` |
| `--model` | Model alias or full ID |
| `--permission-mode` | `default`, `plan`, `acceptEdits`, `dontAsk`, `bypassPermissions` |
| `--worktree`, `-w` | Start in isolated git worktree |
| `--tools` | Restrict available tools |
| `--mcp-config` | Load MCP servers from JSON |
| `--name`, `-n` | Session display name |
| `--resume`, `-r` | Resume session by ID/name |
| `--continue`, `-c` | Continue most recent conversation |
| `--print`, `-p` | Non-interactive mode |
| `--output-format` | `text`, `json`, `stream-json` |
| `--max-turns` | Limit agentic turns (print mode) |
| `--max-budget-usd` | Spending limit (print mode) |
| `--json-schema` | Validated JSON output (print mode) |
| `--debug` | Debug mode with category filtering |
| `--chrome` | Enable Chrome browser integration |
| `--teammate-mode` | `auto`, `in-process`, `tmux` |
| `--from-pr <number>` | Resume sessions linked to PR |
| `--fork-session` | New session ID when resuming |
| `--plugin-dir` | Load plugins from directory |
| `--remote-control` | Enable Remote Control from claude.ai |

## Appendix B: Settings Reference (Key Settings)

| Key | Description |
|---|---|
| `permissions.allow/deny/ask` | Permission rules arrays |
| `permissions.defaultMode` | Default permission mode |
| `hooks` | Hook configuration object |
| `env` | Environment variables for sessions |
| `model` | Override default model |
| `agent` | Run main thread as named subagent |
| `autoMemoryEnabled` | Enable/disable auto memory |
| `autoMemoryDirectory` | Custom memory storage path |
| `claudeMdExcludes` | Glob patterns to skip CLAUDE.md files |
| `enabledPlugins` | Plugin enable/disable map |
| `teammateMode` | Agent team display mode |
| `effortLevel` | Persist effort level across sessions |
| `sandbox.enabled` | Enable bash sandboxing |
| `worktree.symlinkDirectories` | Directories to symlink in worktrees |
| `worktree.sparsePaths` | Sparse checkout paths for worktrees |
| `cleanupPeriodDays` | Session cleanup period (default: 30) |
| `disableAllHooks` | Disable all hooks |
| `outputStyle` | Configure output style |
| `language` | Preferred response language |

Settings precedence: Managed > CLI args > Local > Project > User.

Array settings **merge** across scopes (concatenated and deduplicated).

## Appendix C: Plugin System

### Plugin Structure

```
my-plugin/
  .claude-plugin/
    plugin.json          # Manifest (required)
  skills/                # SKILL.md files
  agents/                # Agent definitions
  commands/              # Legacy commands
  hooks/
    hooks.json           # Hook configuration
  .mcp.json              # MCP servers
  .lsp.json              # LSP servers
  settings.json          # Default settings (currently only `agent` key)
```

### Plugin Manifest (plugin.json)

```json
{
  "name": "my-plugin",
  "description": "Plugin description",
  "version": "1.0.0",
  "author": { "name": "Author" },
  "homepage": "https://...",
  "repository": "https://...",
  "license": "MIT"
}
```

Plugin skills namespaced: `/plugin-name:skill-name`.

Security: Plugin subagents do NOT support `hooks`, `mcpServers`, or `permissionMode` frontmatter.

Test locally: `claude --plugin-dir ./my-plugin`. Reload: `/reload-plugins`.

---

## Sources

1. https://code.claude.com/docs/en/memory
2. https://code.claude.com/docs/en/sub-agents
3. https://code.claude.com/docs/en/agent-teams
4. https://code.claude.com/docs/en/hooks
5. https://code.claude.com/docs/en/hooks-guide
6. https://code.claude.com/docs/en/skills
7. https://code.claude.com/docs/en/cli-reference
8. https://code.claude.com/docs/en/settings
9. https://code.claude.com/docs/en/permissions
10. https://code.claude.com/docs/en/plugins
11. https://code.claude.com/docs/en/common-workflows
12. https://claude.com/blog/how-anthropic-teams-use-claude-code
13. https://www.anthropic.com/engineering/building-effective-agents
14. https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
15. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
