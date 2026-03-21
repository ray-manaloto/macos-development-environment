# Everything Claude Code Agent Patterns

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://github.com/affaan-m/everything-claude-code (88.5k stars)
- README.md, CLAUDE.md, AGENTS.md, CONTRIBUTING.md
- All 28 agent definition files
- .claude-plugin/plugin.json, hooks/hooks.json
- rules/common/agents.md, rules/common/performance.md, rules/common/hooks.md
- schemas/plugin.schema.json
- skills/team-builder/SKILL.md, skills/autonomous-loops/SKILL.md
- commands/orchestrate.md, commands/multi-plan.md
- the-shortform-guide.md

---

## 1. Agent Definition Format (YAML Frontmatter)

Every agent is a markdown file in `agents/` with this exact frontmatter:

```yaml
---
name: lowercase-hyphenated
description: Detailed description including WHEN to invoke. Critical for routing accuracy.
tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
model: haiku | sonnet | opus
color: optional-color-name  # e.g., "orange", "teal"
---
```

The project contains **28 agents**, **116 skills**, and **59 commands**.

---

## 2. Model Routing Strategy

| Model | Use Case | Agents |
|-------|----------|--------|
| **haiku** | Simple tasks, documentation | doc-updater |
| **sonnet** | Most coding agents | code-reviewer, tdd-guide, build-error-resolver, security-reviewer, all language reviewers, e2e-runner, refactor-cleaner, loop-operator, harness-optimizer, docs-lookup |
| **opus** | Deep reasoning | planner, architect, chief-of-staff |

---

## 3. Tool Permission Patterns

| Pattern | Tools | Agents |
|---------|-------|--------|
| Read-only | `["Read", "Grep", "Glob"]` | planner, architect |
| Review with bash | `["Read", "Grep", "Glob", "Bash"]` | code-reviewer, python-reviewer, rust-reviewer |
| Full-access | `["Read", "Write", "Edit", "Bash", "Grep", "Glob"]` | build-error-resolver, security-reviewer, e2e-runner, refactor-cleaner, chief-of-staff |
| MCP tool agents | `["Read", "Grep", "mcp__context7__resolve-library-id", "mcp__context7__query-docs"]` | docs-lookup |

---

## 4. Description Pattern for Trigger Accuracy

The `description` field is the primary routing signal. Best descriptions:

- State the role explicitly
- Include "Use PROACTIVELY when..." trigger conditions
- Include "MUST BE USED for..." mandatory conditions
- List specific scenarios (e.g., "when build fails", "before commits")

Example:
> "Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code. MUST BE USED for all code changes."

---

## 5. Team Composition Patterns

From AGENTS.md and rules/common/agents.md:

| Workflow | Agent Sequence |
|----------|---------------|
| **Feature** | planner -> tdd-guide -> code-reviewer -> security-reviewer |
| **Bugfix** | planner -> tdd-guide -> code-reviewer |
| **Refactor** | architect -> code-reviewer -> tdd-guide |
| **Security** | security-reviewer -> code-reviewer -> architect |
| **Parallel analysis** | code-reviewer + security-reviewer + architect (independent checks) |
| **Multi-perspective** | factual reviewer + senior engineer + security expert + consistency reviewer + redundancy checker |

---

## 6. Autonomous Loop Patterns (6 patterns)

1. **Sequential Pipeline** (`claude -p` chain) -- pipe output of one Claude session into next
2. **NanoClaw REPL** (persistent session) -- long-running interactive session with checkpoints
3. **Infinite Agentic Loop** (parallel sub-agents for spec-driven generation) -- continuous generation from specifications
4. **Continuous Claude PR Loop** (PR creation + CI + auto-merge) -- autonomous PR lifecycle
5. **De-Sloppify Pattern** (cleanup pass after implementation) -- post-implementation quality sweep
6. **Ralphinho RFC-Driven DAG** (research -> plan -> implement -> test -> review per work unit) -- structured work unit progression

---

## 7. No SDK/Generator -- Pure Markdown Convention

The project does NOT have a code generator for agents. Everything is markdown files following the conventions in CONTRIBUTING.md. The `/skill-create` command generates skills from git history but not agents. The GitHub App (ecc-tools) does analysis but agents are hand-authored.

### Contributing Templates

**Agent template** (from CONTRIBUTING.md):
```yaml
---
name: agent-name
description: Clear description of when this agent should be used.
  Include trigger conditions and mandatory usage scenarios.
tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
model: sonnet
---
```

**Skill template:**
```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

---

## 8. Hooks System Architecture

### Configuration

- JSON-based (`hooks.json`)
- 6 hook types: PreToolUse, PostToolUse, PreCompact, SessionStart, Stop, SessionEnd, PostToolUseFailure
- Matchers: tool name patterns ("Bash", "Edit|Write", "*")

### Runtime Profiles

| Profile | Description |
|---------|-------------|
| `ECC_HOOK_PROFILE=minimal` | Minimum hooks for fast iteration |
| `ECC_HOOK_PROFILE=standard` | Default hook set |
| `ECC_HOOK_PROFILE=strict` | All hooks enabled, strictest validation |

### Hook Disabling

`ECC_DISABLED_HOOKS=comma,separated,ids` -- disable specific hooks by ID without editing hooks.json.

---

## Complete Agent Inventory (28 agents)

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| planner | opus | Read-only | Task planning and decomposition |
| architect | opus | Read-only | System architecture design |
| chief-of-staff | opus | Full | Executive coordination |
| code-reviewer | sonnet | Review+bash | Code quality review |
| security-reviewer | sonnet | Full | Security analysis |
| tdd-guide | sonnet | Review+bash | Test-driven development guidance |
| build-error-resolver | sonnet | Full | Build failure diagnosis and fix |
| e2e-runner | sonnet | Full | End-to-end test execution |
| refactor-cleaner | sonnet | Full | Code refactoring |
| doc-updater | haiku | Full | Documentation updates |
| docs-lookup | sonnet | Read+MCP | Documentation search via context7 |
| loop-operator | sonnet | Full | Autonomous loop management |
| harness-optimizer | sonnet | Full | Test harness optimization |
| python-reviewer | sonnet | Review+bash | Python-specific code review |
| rust-reviewer | sonnet | Review+bash | Rust-specific code review |
| flutter-reviewer | sonnet | Review+bash | Flutter-specific code review |

(Plus additional language-specific and specialized agents totaling 28.)

---

## Key Takeaways for Our Project

1. **Model routing is explicit**: Every agent declares its model. No "inherit" defaults -- forces conscious routing decisions.
2. **Description is the routing signal**: Invest heavily in description quality with trigger conditions.
3. **Tool restrictions are meaningful**: Read-only for planners/architects prevents accidental mutations.
4. **MCP tools in frontmatter**: The docs-lookup agent shows how to grant specific MCP tools.
5. **Hooks are profile-gated**: Environment variables control hook strictness -- good pattern for development vs. CI.
6. **No agent generator exists**: Hand-authored markdown is the norm even at 28 agents and 116 skills.
