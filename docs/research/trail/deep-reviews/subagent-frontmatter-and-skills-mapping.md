# Subagent Frontmatter and Skills Mapping

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://code.claude.com/docs/en/sub-agents (full page)
- https://code.claude.com/docs/en/skills (full page)
- Local project: `.claude/agents/` (15 agent files)
- Local project: `.claude/skills/skills/` (75+ skill directories)

---

## Frontmatter Fields (14 total)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | YES | -- | Unique ID, lowercase + hyphens only |
| `description` | string | YES | -- | When Claude should delegate; used for routing |
| `tools` | string (CSV) | No | inherit all | Comma-separated tool names |
| `disallowedTools` | string (CSV) | No | none | Tools to deny |
| `model` | string | No | `inherit` | `sonnet`, `opus`, `haiku`, full model ID, or `inherit` |
| `permissionMode` | string | No | `default` | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | integer | No | unlimited | Max agentic turns before stopping |
| `skills` | list of strings | No | none | Skill names to preload into context |
| `mcpServers` | list | No | none | Inline MCP defs or string refs |
| `hooks` | object | No | none | Lifecycle hooks |
| `memory` | string | No | none | `user`, `project`, or `local` |
| `background` | boolean | No | `false` | Always run as background task |
| `effort` | string | No | inherit | `low`, `medium`, `high`, `max` |
| `isolation` | string | No | none | `worktree` for isolated git worktree |

---

## Critical Discovery: `skills` Field Behavior

- Full skill content is **INJECTED at startup**, not just made available on-demand
- Subagents do **NOT inherit skills from parent conversation**
- Must list skills **explicitly per agent** in the `skills:` frontmatter field
- Skills consume context window space -- be selective about which skills to preload
- Only skills installed in the project or user scope can be referenced

---

## Bundled Skills (5)

These ship with Claude Code and are always available:

| Skill | Purpose |
|-------|---------|
| `/batch` | Batch processing operations |
| `/claude-api` | Claude API usage patterns |
| `/debug` | Debugging assistance |
| `/loop` | Autonomous loop execution |
| `/simplify` | Code simplification |

---

## Project Skills Inventory (75+)

### Python

| Skill | Purpose |
|-------|---------|
| python-code-review | Python code review patterns |
| pytest-code-review | pytest-specific review |
| pydantic-ai-* (6 skills) | Pydantic AI framework patterns |
| fastapi-code-review | FastAPI review |
| sqlalchemy-code-review | SQLAlchemy review |

### Testing

| Skill | Purpose |
|-------|---------|
| test-driven-development | TDD workflow |
| vitest-testing | Vitest test patterns |

### Workflow

| Skill | Purpose |
|-------|---------|
| subagent-driven-development | Multi-agent development |
| dispatching-parallel-agents | Parallel agent coordination |
| executing-plans | Plan execution workflow |
| writing-plans | Plan creation workflow |
| brainstorming | Idea generation |

### Review

| Skill | Purpose |
|-------|---------|
| requesting-code-review | How to request reviews |
| receiving-code-review | How to process reviews |
| review-verification-protocol | Review quality checks |
| review-skill-improver | Meta: improving review skills |

### Debugging

| Skill | Purpose |
|-------|---------|
| systematic-debugging | Structured debugging methodology |

### Git

| Skill | Purpose |
|-------|---------|
| using-git-worktrees | Git worktree patterns |
| finishing-a-development-branch | Branch completion workflow |

### Meta

| Skill | Purpose |
|-------|---------|
| writing-skills | How to write new skills |
| using-superpowers | Superpowers framework usage |
| verification-before-completion | Final verification checklist |

### ADR

| Skill | Purpose |
|-------|---------|
| adr-writing | Architecture Decision Record creation |
| adr-decision-extraction | Extract decisions from conversations |

### Go

| Skill | Purpose |
|-------|---------|
| go-code-review | Go code review |
| go-testing-code-review | Go test review |

### Swift

| Skill | Purpose |
|-------|---------|
| swift-code-review | Swift code review |
| swiftui-code-review | SwiftUI review |
| swiftdata-code-review | SwiftData review |
| swift-testing-code-review | Swift testing review |

---

## Skills-to-Agent Mapping

This mapping shows which skills should be preloaded (via `skills:` frontmatter) for each agent type in our project.

### Researcher Agent

```yaml
skills:
  - brainstorming
  - writing-plans
```

**Rationale:** Researcher needs idea generation and plan creation. Does not need code review or testing skills.

### Coder Agent

```yaml
skills:
  - test-driven-development
  - systematic-debugging
  - finishing-a-development-branch
  - using-git-worktrees
  - verification-before-completion
  - python-code-review
  - executing-plans
```

**Rationale:** Full development lifecycle skills. Python-specific since our project is Python.

### Tester Agent

```yaml
skills:
  - test-driven-development
  - verification-before-completion
  - pytest-code-review
```

**Rationale:** Focused on testing patterns and verification.

### Reviewer Agent

```yaml
skills:
  - requesting-code-review
  - receiving-code-review
  - review-verification-protocol
  - python-code-review
```

**Rationale:** Review workflow and Python-specific review patterns.

### Planner Agent

```yaml
skills:
  - subagent-driven-development
  - dispatching-parallel-agents
  - writing-plans
  - writing-skills
  - adr-writing
  - adr-decision-extraction
```

**Rationale:** Orchestration and planning skills. ADR skills for documenting architectural decisions.

### Security Reviewer Agent

```yaml
skills:
  - python-code-review
  - systematic-debugging
```

**Rationale:** Minimal skills -- security review is primarily about the agent's system prompt and expertise, not preloaded skill content.

---

## Context Window Budget Considerations

Each preloaded skill consumes context window space. Recommendations:

1. **Limit to 3-7 skills per agent** -- more than this wastes context on instructions rather than working memory
2. **Prioritize workflow skills** (TDD, debugging) over reference skills (language-specific review)
3. **Use `model: haiku` agents for simple tasks** -- they have smaller context windows, so fewer skills
4. **Test skill combinations** -- some skills overlap and the redundancy wastes tokens
5. **Monitor via `/doctor`** -- check if agents are loading correctly with their skill sets

---

## Unmapped Skills (available but not assigned)

These project skills exist but are not recommended for any current agent:

| Skill | Reason Not Mapped |
|-------|-------------------|
| vitest-testing | Project uses pytest, not vitest |
| go-code-review, go-testing-code-review | Project is Python, not Go |
| swift-*, swiftui-*, swiftdata-* | Project is Python, not Swift |
| pydantic-ai-* | Not currently using pydantic-ai framework |
| fastapi-code-review | Not currently using FastAPI |
| sqlalchemy-code-review | Not currently using SQLAlchemy |
| review-skill-improver | Meta-skill for skill improvement, not needed in agent context |
