# Agent File Schemas, Generation, and Cross-Framework Comparison

> Complete reference for auto-generating Claude Code agent files from schemas/SDKs,
> and comparison of agent definition formats across 6 multi-agent frameworks.
> Sources: code.claude.com/docs, github.com/anthropics/claude-agent-sdk-python,
> agentskills.io, github.com/open-gitagent/gitagent, deep-review corpus.
> Fetched: 2026-03-20.

## Table of Contents

1. [Part 1: Official SDK/Schema Tools for Agent File Generation](#part-1-official-sdkschema-tools-for-agent-file-generation)
2. [Part 2: Cross-Framework Agent Format Comparison](#part-2-cross-framework-agent-format-comparison)
3. [Part 3: Auto-Generation and Drift Prevention](#part-3-auto-generation-and-drift-prevention)
4. [Appendix A: Complete Claude Code Agent Frontmatter Schema](#appendix-a-complete-claude-code-agent-frontmatter-schema)
5. [Appendix B: Complete gitagent agent.yaml Schema](#appendix-b-complete-gitagent-agentyaml-schema)
6. [Appendix C: Complete agentskills.io SKILL.md Schema](#appendix-c-complete-agentskillsio-skillmd-schema)

---

## Part 1: Official SDK/Schema Tools for Agent File Generation

### 1.1 Is There an Official JSON Schema for Agent Frontmatter?

**No.** As of 2026-03-20, there is no published JSON Schema for `.claude/agents/*.md`
YAML frontmatter. The canonical specification exists only as documentation prose at
`code.claude.com/docs/en/sub-agents`.

The closest machine-readable definitions are:

| Source | What It Provides | Limitation |
|--------|-----------------|------------|
| Agent SDK Python `AgentDefinition` dataclass | 7 fields typed in Python | Missing 8+ fields that the CLI supports |
| `--agents` CLI flag JSON format | Same fields as frontmatter | No schema file published; validation is internal |
| `/agents` interactive command | Generates files with all fields | Interactive-only, no programmatic API |
| agentskills.io `skills-ref` library | Validates SKILL.md frontmatter | Skills only, not agents |

### 1.2 Can `claude agents` or `/agents` Generate Agent Files?

**`claude agents`** (CLI command) is read-only -- it lists configured agents grouped by
source and indicates which are overridden. It has no `--create`, `--generate`, or
`--export` subcommand.

```
$ claude agents --help
Usage: claude agents [options]
List configured agents
Options:
  -h, --help                   Display help for command
  --setting-sources <sources>  Comma-separated list of setting sources to load
```

**`/agents`** (interactive slash command) is the only official generation tool:
1. Select "Create new agent"
2. Choose scope: Personal (`~/.claude/agents/`) or Project (`.claude/agents/`)
3. Choose "Generate with Claude" or manual
4. Select tools, model, color, memory scope
5. File is written with full YAML frontmatter

This is interactive-only. There is no `--json` export or programmatic API for
`/agents`.

### 1.3 Does the Agent SDK Provide Programmatic Agent Creation?

The Python Agent SDK (`claude-agent-sdk-python`) defines `AgentDefinition` as a
dataclass:

```python
@dataclass
class AgentDefinition:
    """Agent definition configuration."""
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    skills: list[str] | None = None
    memory: Literal["user", "project", "local"] | None = None
    mcpServers: list[str | dict[str, Any]] | None = None
```

**Important gaps:** The SDK `AgentDefinition` is missing these fields that the
file-based frontmatter supports:

| Frontmatter Field | SDK `AgentDefinition` | Notes |
|-------------------|-----------------------|-------|
| `name` | Not present | Required in files, implicit in `--agents` JSON (key name) |
| `disallowedTools` | Not present | Supported in files and `--agents` JSON |
| `permissionMode` | Not present | Supported in files and `--agents` JSON |
| `maxTurns` | Not present | Supported in files and `--agents` JSON |
| `hooks` | Not present | Supported in files and `--agents` JSON |
| `background` | Not present | Supported in files and `--agents` JSON |
| `effort` | Not present | Supported in files and `--agents` JSON |
| `isolation` | Not present | Supported in files and `--agents` JSON |

The SDK does NOT provide:
- A function to generate `.md` agent files from `AgentDefinition`
- A function to validate agent frontmatter YAML
- A JSON Schema export for agent definitions
- Any template/scaffold utilities

The SDK's primary use case is running agents programmatically via `ClaudeSDKClient`,
passing `AgentDefinition` objects at runtime, not generating persistent agent files.

### 1.4 The `--agents` CLI Flag as Inline Definition

The `--agents` flag accepts JSON with the same fields as file frontmatter. This is
the closest thing to a programmatic agent definition API:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer.",
    "prompt": "You are a senior code reviewer.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet",
    "permissionMode": "default",
    "maxTurns": 50,
    "background": false,
    "effort": "high",
    "isolation": "worktree",
    "memory": "project",
    "skills": ["api-conventions"],
    "mcpServers": ["github"],
    "hooks": {
      "PreToolUse": [{
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "./validate.sh"}]
      }]
    }
  }
}'
```

Session-only; not persisted to disk.

### 1.5 What Validation Tools Exist?

| Tool | What It Validates | How |
|------|-------------------|-----|
| Claude Code internal parser | Agent frontmatter on session start | Errors shown in UI; no CLI access |
| `/agents` UI | Interactive validation during creation | Real-time feedback |
| `skills-ref validate` | SKILL.md frontmatter only | CLI: `skills-ref validate ./my-skill` |
| `gitagent validate` | Full agent repository | CLI: `gitagent validate [--compliance]` |
| None | Claude Code agent `.md` files | No standalone validator exists |

**Key gap:** There is no `claude agents validate` or equivalent CLI command that can
validate `.claude/agents/*.md` files outside of a running session.

### 1.6 Summary of Official Tooling

| Question | Answer |
|----------|--------|
| Official JSON Schema for agent frontmatter? | No |
| `claude agents` can generate files? | No (list-only) |
| `/agents` can generate files? | Yes, interactive-only |
| Agent SDK provides file generation? | No |
| Agent SDK provides validation? | No |
| Standalone frontmatter validator? | No |
| `--agents` JSON matches frontmatter fields? | Yes (use `prompt` instead of markdown body) |

---

## Part 2: Cross-Framework Agent Format Comparison

### 2.1 Format Overview

| Framework | File Format | Required Files | Schema Language | Validation Tool |
|-----------|-------------|----------------|-----------------|-----------------|
| **Claude Code** | `.claude/agents/*.md` (YAML frontmatter + Markdown body) | 1 file per agent | None (docs only) | None (internal parser) |
| **agentskills.io** | `skills/*/SKILL.md` (YAML frontmatter + Markdown body) | 1 file per skill | Python `skills-ref` | `skills-ref validate` |
| **gstack** | `.claude/skills/gstack/*` (SKILL.md per skill) | 1 file per skill | None | None |
| **ARIS** | `SKILL.md` per skill (zero-dependency) | 1 file per skill | None | None |
| **gitagent** | `agent.yaml` + `SOUL.md` + optional files | 2+ files per agent | JSON Schema (10 schemas) | `gitagent validate` |
| **agent-orchestrator** | TypeScript interfaces in `packages/core/src/types.ts` | Code, not config | TypeScript types | TypeScript compiler |

### 2.2 Field-by-Field Comparison

#### Identity Fields

| Field | Claude Code | agentskills.io | gitagent | ARIS | gstack |
|-------|-------------|----------------|----------|------|--------|
| Name/ID | `name` (required, kebab-case) | `name` (required, kebab-case, max 64 chars) | `name` (required, kebab-case) | implicit (filename) | implicit (filename) |
| Description | `description` (required) | `description` (required, max 1024 chars) | `description` (required, one-line) | implicit (first paragraph) | implicit (first paragraph) |
| Version | -- | -- (via `metadata.version`) | `version` (required, semver) | -- | -- |
| Author | -- | -- (via `metadata.author`) | `author` (optional) | -- | -- |
| License | -- | `license` (optional) | `license` (optional, SPDX) | -- | -- |
| Tags | -- | -- (via `metadata`) | `tags` (optional, string[]) | -- | -- |

#### Model Configuration

| Field | Claude Code | agentskills.io | gitagent | agent-orchestrator |
|-------|-------------|----------------|----------|--------------------|
| Model selection | `model` (sonnet/opus/haiku/inherit/full ID) | -- | `model.preferred` (any model ID) | Agent interface `name` field |
| Fallback models | -- | -- | `model.fallback` (string[]) | -- |
| Temperature | -- | -- | `model.constraints.temperature` | -- |
| Max tokens | -- | -- | `model.constraints.max_tokens` | -- |
| Top-p/k | -- | -- | `model.constraints.top_p/top_k` | -- |

#### Capability Control

| Field | Claude Code | agentskills.io | gitagent | agent-orchestrator |
|-------|-------------|----------------|----------|--------------------|
| Tool allowlist | `tools` (comma-separated) | `allowed-tools` (space-delimited) | `tools` (string[]) | `AgentLaunchConfig` |
| Tool denylist | `disallowedTools` | -- | -- | -- |
| Skills injection | `skills` (list) | -- | `skills` (string[]) | -- |
| MCP servers | `mcpServers` (list of names or inline defs) | -- | `tools/*.yaml` (MCP-compatible) | -- |
| Permission mode | `permissionMode` (5 modes) | -- | -- | -- |

#### Execution Control

| Field | Claude Code | agentskills.io | gitagent | agent-orchestrator |
|-------|-------------|----------------|----------|--------------------|
| Max turns | `maxTurns` (integer) | -- | `runtime.max_turns` | -- |
| Background execution | `background` (boolean) | -- | -- | Session lifecycle FSM |
| Effort level | `effort` (low/medium/high/max) | -- | -- | -- |
| Isolation | `isolation` ("worktree") | -- | compliance.segregation_of_duties.isolation | `Workspace` interface |
| Timeout | -- | -- | `runtime.timeout` (seconds) | `readyThresholdMs` |

#### Lifecycle and Hooks

| Field | Claude Code | agentskills.io | gitagent | agent-orchestrator |
|-------|-------------|----------------|----------|--------------------|
| Hooks | `hooks` (PreToolUse, PostToolUse, Stop) | -- | `hooks/hooks.yaml` (on_session_start, pre_tool_use, post_response, on_error) | `ReactionConfig` (event-driven) |
| Memory | `memory` (user/project/local scope) | -- | `memory/memory.yaml` + `MEMORY.md` | -- |
| Compatibility | -- | `compatibility` (max 500 chars) | -- | -- |

#### System Prompt

| Framework | Where the Prompt Lives |
|-----------|-----------------------|
| Claude Code | Markdown body after YAML frontmatter in the `.md` file |
| agentskills.io | Markdown body after YAML frontmatter in `SKILL.md` |
| gstack | Markdown body in `SKILL.md` |
| ARIS | Markdown body in `SKILL.md` |
| gitagent | `SOUL.md` (identity) + `RULES.md` (constraints) + `DUTIES.md` (roles) -- separate files |
| agent-orchestrator | `prompt` field in `AgentLaunchConfig`, or `generatePrompt()` from Tracker |

### 2.3 Structural Comparison

#### Claude Code: Single-File Agent

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep, Bash
disallowedTools: Write, Edit
model: sonnet
permissionMode: default
maxTurns: 50
memory: project
effort: high
background: false
isolation: worktree
skills:
  - api-conventions
  - error-handling-patterns
mcpServers:
  - github
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---

You are a senior code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

**Strengths:** Everything in one file. Immediate discoverability. No build step.
**Weaknesses:** No versioning. No inheritance. No schema validation. No export.

#### agentskills.io: Single-File Skill

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
compatibility: Requires Python 3.14+ and poppler-utils
allowed-tools: Bash(python3:*) Read Write
metadata:
  author: example-org
  version: "1.0"
---

# PDF Processing

## Instructions
1. Use poppler-utils for text extraction
2. Use reportlab for form filling
...
```

**Strengths:** Industry standard (30+ tools). Progressive disclosure. `skills-ref` validator.
**Weaknesses:** Skills only, not agents. No model/permission/hook fields. No execution control.

#### gitagent: Multi-File Agent Repository

```
my-agent/
  agent.yaml       # Required: identity + config + compliance
  SOUL.md           # Required: personality + communication style
  RULES.md          # Optional: hard constraints
  DUTIES.md         # Optional: segregation of duties
  AGENTS.md         # Optional: framework-agnostic fallback
  skills/           # Optional: Agent Skills standard skills
  tools/            # Optional: MCP-compatible tool definitions
  hooks/            # Optional: lifecycle hooks
  workflows/        # Optional: structured workflows
  knowledge/        # Optional: indexed knowledge base
  memory/           # Optional: persistent memory
  agents/           # Optional: sub-agent definitions (recursive)
  compliance/       # Optional: regulatory artifacts
  config/           # Optional: environment-specific config
```

**Strengths:** Most comprehensive schema. JSON Schema validation (10 schemas).
Import from Claude Code/Cursor/CrewAI. Export to 10+ formats. Compliance built-in.
Git-native versioning. Inheritance via `extends`.
**Weaknesses:** Most complex. Requires CLI tooling. Regulatory compliance is overkill
for most use cases.

#### agent-orchestrator: TypeScript Plugin Interfaces

```typescript
interface Agent {
  readonly name: string;
  readonly processName: string;
  readonly promptDelivery?: "inline" | "post-launch";
  getLaunchCommand(config: AgentLaunchConfig): string;
  getEnvironment(config: AgentLaunchConfig): Record<string, string>;
  detectActivity(terminalOutput: string): ActivityState;
  getActivityState(session: Session, readyThresholdMs?: number): Promise<ActivityDetection | null>;
  isProcessRunning(handle: RuntimeHandle): Promise<boolean>;
  getSessionInfo(session: Session): Promise<AgentSessionInfo | null>;
  getRestoreCommand?(session: Session, project: ProjectConfig): Promise<string | null>;
  postLaunchSetup?(session: Session): Promise<void>;
  setupWorkspaceHooks?(workspacePath: string, config: WorkspaceHooksConfig): Promise<void>;
}
```

**Strengths:** Full type safety. Rich lifecycle management. Plugin architecture.
**Weaknesses:** Code-only -- no declarative config files. Requires TypeScript compilation.

#### ARIS: Zero-Dependency SKILL.md

```markdown
---
name: auto-review-loop
description: Cross-model adversarial review loop for ML research papers
---

# Auto Review Loop

Phase A -- Launch Review Session: ...
Phase B -- Execute Experiment Round: ...
Phase C -- Cross-Model Review: send to GPT-5.4 via Codex MCP ...
Phase D -- Wait for Results: ...
Phase E -- Document Round: Append to AUTO_REVIEW.md ...
```

ARIS skills use the agentskills.io `SKILL.md` format but with no optional fields --
just `name` and `description`. All behavioral specification lives in the markdown body.
State is managed via separate JSON files (`REVIEW_STATE.json`, `PAPER_IMPROVEMENT_STATE.json`).

**Strengths:** Zero dependencies. Works on any LLM. Purely portable markdown.
**Weaknesses:** No type safety. No validation. State management is ad-hoc JSON.

#### gstack: Skill Pack Pattern

gstack uses the same `SKILL.md` format as agentskills.io. Each of its 21 skills is a
standalone markdown file with frontmatter containing `name` and `description`. The setup
script creates symlinks for discovery. Skills reference each other by name but have no
formal dependency declaration.

### 2.4 Knowledge Capture Comparison

| Framework | Knowledge Format | Persistence | Cross-Session |
|-----------|-----------------|-------------|---------------|
| Claude Code | `MEMORY.md` in agent-memory dirs (user/project/local scope) | Built-in with `memory` field | Yes |
| ARIS | `AUTO_REVIEW.md` (append-only log) + `REVIEW_STATE.json` | Manual file writes | Yes (file-based) |
| compound-engineering | `docs/solutions/*.md` with validated YAML frontmatter | 5-agent pipeline writes files | Yes (file-based) |
| gitagent | `memory/MEMORY.md` + `memory/archive/` + `memory.yaml` config | Structured with rotation policy | Yes |
| agent-orchestrator | Session JSONL files + `AgentSessionInfo` | Runtime-managed | Via session restore |
| gstack | `/retro` JSON snapshots for trend tracking | Explicit skill invocation | Yes (file-based) |

### 2.5 Agent Portability Matrix

| Source Format | Can Export To | Mechanism |
|---------------|--------------|-----------|
| Claude Code `.claude/agents/*.md` | gitagent | `gitagent import --from claude <path>` |
| gitagent `agent.yaml` + `SOUL.md` | Claude Code, OpenAI, CrewAI, system-prompt, 6+ more | `gitagent export --format <fmt>` |
| SKILL.md (agentskills.io) | Any of 30+ compatible tools | Native loading by each tool |
| Cursor rules | gitagent | `gitagent import --from cursor <path>` |
| CrewAI YAML | gitagent | `gitagent import --from crewai <path>` |
| agent-orchestrator TypeScript | None (code-only) | Manual conversion |

**gitagent is the hub.** It can import from 4 formats and export to 10+, making it the
most practical bridge between frameworks.

---

## Part 3: Auto-Generation and Drift Prevention

### 3.1 Schema-Driven Code Generation Patterns

Since no official JSON Schema exists for Claude Code agent frontmatter, here are
approaches for creating one:

#### Approach A: Derive Schema from Documentation

Extract the field table from `code.claude.com/docs/en/sub-agents` and encode it as
JSON Schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Claude Code Agent Frontmatter",
  "type": "object",
  "required": ["name", "description"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9-]*$",
      "description": "Unique identifier using lowercase letters and hyphens"
    },
    "description": {
      "type": "string",
      "minLength": 1,
      "description": "When Claude should delegate to this subagent"
    },
    "tools": {
      "oneOf": [
        {"type": "string", "description": "Comma-separated tool names"},
        {"type": "array", "items": {"type": "string"}}
      ]
    },
    "disallowedTools": {
      "oneOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}}
      ]
    },
    "model": {
      "type": "string",
      "description": "sonnet, opus, haiku, inherit, or full model ID"
    },
    "permissionMode": {
      "type": "string",
      "enum": ["default", "acceptEdits", "dontAsk", "bypassPermissions", "plan"]
    },
    "maxTurns": {
      "type": "integer",
      "minimum": 1
    },
    "skills": {
      "type": "array",
      "items": {"type": "string"}
    },
    "mcpServers": {
      "type": "array",
      "items": {
        "oneOf": [
          {"type": "string"},
          {
            "type": "object",
            "minProperties": 1,
            "maxProperties": 1,
            "additionalProperties": {
              "type": "object",
              "properties": {
                "type": {"type": "string", "enum": ["stdio", "http", "sse", "ws"]},
                "command": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}}
              }
            }
          }
        ]
      }
    },
    "hooks": {
      "type": "object",
      "properties": {
        "PreToolUse": {"$ref": "#/$defs/hookMatcherArray"},
        "PostToolUse": {"$ref": "#/$defs/hookMatcherArray"},
        "Stop": {"$ref": "#/$defs/hookMatcherArray"}
      },
      "additionalProperties": false
    },
    "memory": {
      "type": "string",
      "enum": ["user", "project", "local"]
    },
    "background": {
      "type": "boolean",
      "default": false
    },
    "effort": {
      "type": "string",
      "enum": ["low", "medium", "high", "max"]
    },
    "isolation": {
      "type": "string",
      "enum": ["worktree"]
    }
  },
  "$defs": {
    "hookMatcherArray": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "matcher": {"type": "string"},
          "hooks": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "command"],
              "properties": {
                "type": {"type": "string", "enum": ["command"]},
                "command": {"type": "string"}
              }
            }
          }
        }
      }
    }
  }
}
```

#### Approach B: Use gitagent as the Source of Truth

Since gitagent already has 10 JSON Schemas in `spec/schemas/`, and can import/export
Claude Code format:

```bash
# Import existing Claude Code agents into gitagent format
gitagent import --from claude .claude/agents/

# Validate with full schema
gitagent validate

# Export back to Claude Code format
gitagent export --format claude-code
```

This provides a round-trip validation pipeline without needing a custom schema.

#### Approach C: Derive Schema from Agent SDK Types

Use the Python `AgentDefinition` dataclass as a starting point and extend it with
missing fields from the documentation. Then use a tool like `datamodel-code-generator`
or `pydantic` to produce a JSON Schema.

### 3.2 File Watchers and Change Detection Hooks

#### Pre-Commit Hook for Agent Validation

```python
# In src/mde/hooks/validate_agents.py
"""Validate .claude/agents/*.md frontmatter on commit."""
import yaml
import sys
from pathlib import Path

REQUIRED_FIELDS = {"name", "description"}
VALID_MODELS = {"sonnet", "opus", "haiku", "inherit"}
VALID_PERMISSIONS = {"default", "acceptEdits", "dontAsk", "bypassPermissions", "plan"}
VALID_MEMORY = {"user", "project", "local"}
VALID_EFFORT = {"low", "medium", "high", "max"}

def validate_agent(path: Path) -> list[str]:
    """Return list of validation errors."""
    errors = []
    text = path.read_text()
    if not text.startswith("---"):
        errors.append(f"{path}: missing YAML frontmatter")
        return errors
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{path}: malformed frontmatter (missing closing ---)")
        return errors
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        errors.append(f"{path}: invalid YAML: {e}")
        return errors
    if not isinstance(fm, dict):
        errors.append(f"{path}: frontmatter is not a mapping")
        return errors
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"{path}: missing required field '{field}'")
    if "model" in fm and fm["model"] not in VALID_MODELS and not fm["model"].startswith("claude-"):
        errors.append(f"{path}: invalid model '{fm['model']}'")
    if "permissionMode" in fm and fm["permissionMode"] not in VALID_PERMISSIONS:
        errors.append(f"{path}: invalid permissionMode '{fm['permissionMode']}'")
    if "memory" in fm and fm["memory"] not in VALID_MEMORY:
        errors.append(f"{path}: invalid memory '{fm['memory']}'")
    if "effort" in fm and fm["effort"] not in VALID_EFFORT:
        errors.append(f"{path}: invalid effort '{fm['effort']}'")
    return errors
```

#### Claude Code Hook for Agent File Changes

In `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import sys, json; inp=json.load(sys.stdin); path=inp.get('tool_input',{}).get('file_path',''); sys.exit(0) if '.claude/agents/' not in path else __import__('subprocess').run(['uv','run','mde-py','hooks','validate-agents']).returncode\""
          }
        ]
      }
    ]
  }
}
```

### 3.3 CI Validation Checks

#### GitHub Actions Workflow

```yaml
name: Validate Agent Files
on:
  pull_request:
    paths:
      - '.claude/agents/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate agent frontmatter
        run: |
          for f in .claude/agents/*.md; do
            python3 -c "
          import yaml, sys
          text = open('$f').read()
          parts = text.split('---', 2)
          fm = yaml.safe_load(parts[1])
          assert 'name' in fm, 'missing name'
          assert 'description' in fm, 'missing description'
          print(f'OK: $f ({fm[\"name\"]})')
          "
          done
```

### 3.4 Auto-Regeneration When the SDK Updates

#### Strategy: Monitor Upstream Changes

1. **Watch the docs page** for frontmatter field additions:
   `https://code.claude.com/docs/en/sub-agents` -- diff the "Supported frontmatter
   fields" table on each release.

2. **Watch the Agent SDK types.py** for `AgentDefinition` changes:
   `https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py`

3. **Watch the agentskills.io spec** for SKILL.md field additions:
   `https://agentskills.io/specification`

#### Dependabot-Style Schema Tracking

```yaml
# .github/workflows/schema-drift-check.yml
name: Check Agent Schema Drift
on:
  schedule:
    - cron: '0 8 * * 1'  # Weekly Monday 8am
  workflow_dispatch:

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch current docs
        run: |
          curl -sL https://code.claude.com/docs/en/sub-agents > /tmp/subagents-docs.html
      - name: Compare with cached version
        run: |
          if ! diff -q docs/research/cache/subagents-docs.html /tmp/subagents-docs.html; then
            echo "::warning::Claude Code subagent docs have changed -- review for new frontmatter fields"
            gh issue create --title "Agent schema drift detected" \
              --body "The subagent docs page has changed. Review for new frontmatter fields." \
              --label "auto:agent-discovered"
          fi
```

### 3.5 Generation Pipeline Design

For this project, the recommended pipeline is:

```
                              Upstream Sources
                    +----------------------------------+
                    | code.claude.com/docs/en/sub-agents|
                    | AgentDefinition (SDK types.py)    |
                    | agentskills.io/specification      |
                    +----------------------------------+
                                    |
                                    v
                    +----------------------------------+
                    |  Derived JSON Schema             |
                    |  (docs/schemas/agent-frontmatter |
                    |   .schema.json)                  |
                    +----------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
        +-------------------+          +-------------------+
        | Validation        |          | Generation        |
        | (CI + pre-commit) |          | (from templates)  |
        +-------------------+          +-------------------+
                    |                               |
                    v                               v
        .claude/agents/*.md              New agent files
```

1. **Schema derivation:** Manually maintained JSON Schema derived from docs + SDK types
2. **Validation:** Pre-commit hook + CI check validates all `.claude/agents/*.md` against schema
3. **Generation:** Template function creates new agent files from schema defaults
4. **Drift detection:** Weekly CI job checks upstream for changes

---

## Appendix A: Complete Claude Code Agent Frontmatter Schema

Every field supported in `.claude/agents/*.md` YAML frontmatter, derived from
`code.claude.com/docs/en/sub-agents` (2026-03-20):

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `name` | Yes | string (kebab-case) | -- | Unique identifier |
| `description` | Yes | string | -- | When Claude should delegate to this subagent |
| `tools` | No | string (comma-sep) or string[] | Inherits all | Tool allowlist |
| `disallowedTools` | No | string (comma-sep) or string[] | None | Tool denylist (applied before `tools`) |
| `model` | No | "sonnet" \| "opus" \| "haiku" \| "inherit" \| full model ID | "inherit" | Model to use |
| `permissionMode` | No | "default" \| "acceptEdits" \| "dontAsk" \| "bypassPermissions" \| "plan" | Inherits | Permission handling mode |
| `maxTurns` | No | integer | -- | Maximum agentic turns |
| `skills` | No | string[] | None | Skills injected into context at startup |
| `mcpServers` | No | (string \| {name: MCPServerConfig})[] | None | MCP servers to connect |
| `hooks` | No | {PreToolUse?: HookMatcher[], PostToolUse?: HookMatcher[], Stop?: HookMatcher[]} | None | Lifecycle hooks scoped to this agent |
| `memory` | No | "user" \| "project" \| "local" | None | Persistent memory scope |
| `background` | No | boolean | false | Always run as background task |
| `effort` | No | "low" \| "medium" \| "high" \| "max" | Inherits | Effort level override |
| `isolation` | No | "worktree" | None | Run in isolated git worktree |

**HookMatcher structure:**
```yaml
- matcher: "ToolName|OtherTool"  # regex pattern matching tool names
  hooks:
    - type: command
      command: "./path/to/script.sh"
```

**MCPServerConfig structure (inline):**
```yaml
- server-name:
    type: stdio|http|sse|ws
    command: "executable"
    args: ["arg1", "arg2"]
```

**Priority order** (highest wins): `--agents` CLI flag > `.claude/agents/` (project) >
`~/.claude/agents/` (user) > plugin `agents/` directory.

**Plugin restrictions:** Plugin-provided agents ignore `hooks`, `mcpServers`, and
`permissionMode` for security.

**Body content:** The markdown after the closing `---` becomes the system prompt.
Agents receive only this prompt plus basic environment details, not the full Claude
Code system prompt.

---

## Appendix B: Complete gitagent agent.yaml Schema

Full schema from `spec/SPECIFICATION.md` v0.1.0:

### Required Fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | `^[a-z][a-z0-9-]*$` (kebab-case) |
| `version` | string | Semantic version `^X.Y.Z[-prerelease][+build]$` |
| `description` | string | One-line summary |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | Target gitagent spec version |
| `author` | string | Name or organization |
| `license` | string | SPDX identifier |
| `model.preferred` | string | Primary model ID |
| `model.fallback` | string[] | Priority-ordered fallback models |
| `model.constraints` | object | temperature, max_tokens, top_p, top_k, stop_sequences, presence_penalty, frequency_penalty |
| `extends` | string | Git URL or local path for inheritance |
| `dependencies` | object[] | Composed agents (name, source, version, mount, vendor_management) |
| `skills` | string[] | Enabled skill names |
| `tools` | string[] | Enabled tool names |
| `agents` | object | Sub-agent configuration |
| `delegation.mode` | "auto" \| "explicit" \| "router" | Delegation strategy |
| `delegation.router` | string | Router agent name |
| `runtime.max_turns` | integer | Conversation turn limit |
| `runtime.temperature` | number | 0.0-2.0 |
| `runtime.timeout` | integer | Seconds |
| `a2a` | object | Agent-to-Agent protocol metadata |
| `compliance` | object | Full regulatory config (see spec) |
| `tags` | string[] | Categorization |
| `metadata` | object | Arbitrary key-value pairs |

### Companion Files

| File | Required | Purpose |
|------|----------|---------|
| `SOUL.md` | Yes | Identity, personality, communication style |
| `RULES.md` | No | Hard constraints, must-always/must-never |
| `DUTIES.md` | No | Segregation of duties, role boundaries |
| `AGENTS.md` | No | Framework-agnostic fallback instructions |

### JSON Schemas (10 files in `spec/schemas/`)

| Schema | Validates |
|--------|-----------|
| `agent-yaml.schema.json` | `agent.yaml` |
| `tool.schema.json` | `tools/*.yaml` |
| `hooks.schema.json` | `hooks/hooks.yaml` |
| `hook-io.schema.json` | Hook script JSON I/O |
| `workflow.schema.json` | `workflows/*.yaml` |
| `memory.schema.json` | `memory/memory.yaml` |
| `skill.schema.json` | Skill YAML frontmatter |
| `marketplace.schema.json` | Skill distribution |
| `knowledge.schema.json` | `knowledge/index.yaml` |
| `config.schema.json` | `config/*.yaml` |

---

## Appendix C: Complete agentskills.io SKILL.md Schema

From `agentskills.io/specification`:

| Field | Required | Type | Constraints |
|-------|----------|------|-------------|
| `name` | Yes | string | 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing/consecutive hyphens, must match parent directory name |
| `description` | Yes | string | 1-1024 chars, non-empty, describes what and when |
| `license` | No | string | License name or bundled file reference |
| `compatibility` | No | string | 1-500 chars, environment requirements |
| `metadata` | No | map\<string, string\> | Arbitrary key-value pairs |
| `allowed-tools` | No | string | Space-delimited tool names (experimental) |

**Adopters (30+ as of 2026-03-20):** Claude Code, Claude.ai, OpenAI Codex, Cursor,
VS Code Copilot, GitHub Copilot, Gemini CLI, Goose, Roo Code, OpenHands, OpenCode,
Junie, Amp, Letta, Firebender, Mux, TRAE, Factory, Kiro, Databricks, Snowflake,
Spring AI, Laravel Boost, Piebald, Autohand, Agentman, Emdash, Qodo, Command Code,
VT Code, Ona, Mistral Vibe.

**Validation:** `skills-ref validate ./my-skill` (Python library at
`github.com/agentskills/agentskills/tree/main/skills-ref`)

**Progressive disclosure:**
1. Metadata (~100 tokens): name + description loaded at startup for all skills
2. Instructions (<5000 tokens recommended): full SKILL.md loaded on activation
3. Resources (as needed): scripts/, references/, assets/ loaded on demand
