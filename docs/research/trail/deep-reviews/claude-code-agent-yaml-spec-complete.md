# Claude Code Agent YAML Spec Complete Reference

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/cli-reference
- https://agentskills.io/specification
- https://github.com/anthropics/skills
- https://platform.claude.com/docs/en/agent-sdk/subagents
- https://github.com/anthropics/claude-agent-sdk-python (types.py)
- GitHub issues #8501, #10504, #22843, #23691, #25380
- `claude agents --help` and `claude --help` (local CLI output)

---

## Q1: EXACT YAML Frontmatter Schema for .claude/agents/*.md

**14 fields total.** Only `name` and `description` are required.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | YES | -- | Unique ID, lowercase + hyphens only |
| `description` | string | YES | -- | When Claude should delegate; used for routing |
| `tools` | string (CSV) | No | inherit all | Comma-separated tool names |
| `disallowedTools` | string (CSV) | No | none | Tools to deny (removed from inherited set) |
| `model` | string | No | `inherit` | `sonnet`, `opus`, `haiku`, full model ID, or `inherit` |
| `permissionMode` | string | No | `default` | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | integer | No | unlimited | Max agentic turns before stopping |
| `skills` | list of strings | No | none | Skill names to preload into context |
| `mcpServers` | list | No | none | Inline MCP defs or string refs to existing servers |
| `hooks` | object | No | none | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |
| `memory` | string | No | none | `user`, `project`, or `local` |
| `background` | boolean | No | `false` | Always run as background task |
| `effort` | string | No | inherit | `low`, `medium`, `high`, `max` (Opus 4.6 only) |
| `isolation` | string | No | none | `worktree` for isolated git worktree |
| `color` | string | No | auto | UNDOCUMENTED. Valid: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |

**Body (after frontmatter):** Markdown content becomes the system prompt. Subagents receive ONLY this prompt + basic env details (cwd), NOT the full Claude Code system prompt.

---

## Q2: Agent Files vs. Skill Files

| Aspect | Agent (.claude/agents/*.md) | Skill (.claude/skills/*/SKILL.md) |
|--------|---------------------------|----------------------------------|
| Purpose | Isolated sub-agent with own context window | Instructions/knowledge injected into current or forked context |
| Context | Fresh context (no parent history) | Runs inline or in forked subagent |
| Invocation | Claude delegates automatically or @-mention | `/skill-name` or Claude auto-invokes |
| Return | Final message returns to parent | Content stays in conversation |
| Required fields | `name`, `description` | `description` (recommended) |
| Unique fields | `maxTurns`, `memory`, `background`, `isolation`, `permissionMode`, `disallowedTools`, `mcpServers` | `argument-hint`, `disable-model-invocation`, `user-invocable`, `context`, `agent` |
| Shared fields | `name`, `description`, `tools`/`allowed-tools`, `model`, `effort`, `hooks` | Same |
| Nesting | Cannot spawn sub-subagents | Can fork into a subagent via `context: fork` |

**When to use which:**
- **Agent:** Task produces verbose output, needs tool restrictions, is self-contained
- **Skill:** Reusable prompts, reference knowledge, workflows in main context

---

## Q3: `claude agents` Subcommands

`claude agents` has NO create/generate/validate subcommands. It ONLY lists configured agents:

```
Usage: claude agents [options]
List configured agents
Options:
  -h, --help                   Display help for command
  --setting-sources <sources>  Comma-separated list of setting sources
```

The `/agents` interactive command (inside a session) DOES have create/edit/delete.

---

## Q4: `/agents` Interactive Command -- "Generate with Claude" Mode

YES, the `/agents` command has a "Generate with Claude" mode:
1. Select "Create new agent" -> Choose Personal or Project
2. Select "Generate with Claude"
3. Describe the agent in natural language
4. Claude generates: identifier, description, system prompt
5. You then select: tools, model, color, memory scope
6. Save immediately or save-and-edit in editor

It produces a complete `.md` file with YAML frontmatter + markdown body.

---

## Q5: Agent SDK AgentDefinition

The Python SDK (`claude-agent-sdk`) has `AgentDefinition` with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | str | Yes (SDK docs say yes) | When to use this agent |
| `prompt` | str | Yes (SDK docs say yes) | System prompt (= markdown body in file-based) |
| `tools` | list[str] | No | Tool names; inherits all if omitted |
| `model` | `'sonnet' | 'opus' | 'haiku' | 'inherit'` | No | Model override |

The SDK `AgentDefinition` is a SUBSET of the file-based schema. It does NOT expose: `disallowedTools`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`.

There is NO function in the SDK to create/generate/validate agent `.md` files. The SDK is for programmatic agent invocation, not file management.

---

## Q6: `--agents` CLI Flag

The `--agents` flag accepts JSON with the SAME fields as file-based frontmatter, PLUS a `prompt` field (equivalent to the markdown body):

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Reviews code",
    "prompt": "You are a code reviewer...",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "disallowedTools": ["Write"],
    "model": "sonnet",
    "permissionMode": "default",
    "mcpServers": [...],
    "hooks": {...},
    "maxTurns": 10,
    "skills": ["api-conventions"],
    "memory": "user",
    "effort": "high",
    "background": false,
    "isolation": "worktree"
  }
}'
```

All 14 frontmatter fields are supported. `prompt` replaces the markdown body.

---

## Q7: Official JSON Schema

**NO official JSON Schema exists** for agent frontmatter. The closest references:
- The docs table at https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields
- The SDK's `AgentDefinition` TypedDict (subset only)
- GitHub issue #8501 requested authoritative schema -- closed NOT_PLANNED
- The `agentskills.io` spec covers SKILL.md only, not agent files

Validation is internal to Claude Code; errors surface as DEBUG logs (issue #22843).

---

## Q8: agentskills.io Standard

The Agent Skills standard (https://agentskills.io/specification) defines:

**SKILL.md fields (agentskills.io standard):**

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, lowercase + hyphens, must match directory name |
| `description` | Yes | 1-1024 chars |
| `license` | No | License name or file reference |
| `compatibility` | No | 1-500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value map |
| `allowed-tools` | No | Space-delimited tool list (experimental) |

**Relationship to Claude Code:**
- Claude Code EXTENDS the standard with: `disable-model-invocation`, `user-invocable`, `argument-hint`, `context`, `agent`, `model`, `effort`, `hooks`
- The agentskills.io standard is SKILL-only; it does NOT define agent files
- OpenAI Codex also adopted the same SKILL.md standard
- Skills can be installed via `anthropics/skills` marketplace

---

## Q9: gitagent Import/Export

No tool called "gitagent" was found in any search. There is no known tool that imports/exports Claude Code agent format. The closest ecosystem tools are:
- VoltAgent/awesome-claude-code-subagents (collection of 100+ agents)
- Various community repos with agent templates
- The `/agents` command's "Generate with Claude" is the only generator

---

## Q10: Validation

**Current validation is MINIMAL and problematic:**

1. **Startup parsing:** Agent files are parsed at session start. Missing `name` field logs a DEBUG-level message but does NOT block startup.
2. **API propagation bug (issue #22843):** Malformed agent files cause API 500 errors on ALL subsequent requests, not clear parse errors.
3. **`/doctor` command:** Shows agent parse errors but must be run manually.
4. **`/agents` command:** Lists all agents; broken ones may not appear.
5. **No `claude agents validate` subcommand exists.**
6. **SKILL.md validator (issue #25380):** Exists but only validates agentskills.io standard fields; rejects Claude Code extended fields as invalid.
7. **`skills-ref validate`:** The agentskills.io reference library can validate SKILL.md files against the standard.

**How to know if an agent file is valid:**
- Run `claude agents` to see if it appears in the list
- Run `/agents` interactively to check for errors
- Run `/doctor` to see parse warnings
- Check debug logs for "Missing required 'name' in frontmatter" messages
