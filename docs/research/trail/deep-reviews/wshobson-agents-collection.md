# wshobson/agents Collection Deep Review

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://github.com/wshobson/agents (31.8K stars) -- README, architecture.md, agents.md, marketplace.json, example agents
- https://github.com/VoltAgent/awesome-claude-code-subagents (14.5K stars) -- README, CONTRIBUTING.md, example agents

---

## wshobson/agents Structure

### Overview

- **72 plugins**, each self-contained in `plugins/{name}/` with `agents/`, `commands/`, `skills/` subdirs
- **112 agents** across 23 categories
- **146 skills** following Anthropic Agent Skills Spec
- **79 tools** (MCP and custom)
- Agent definitions are `.md` files with YAML frontmatter (3 fields: name, description, model)
- Skills follow Anthropic Agent Skills Spec with 2-field frontmatter (name, description)
- `marketplace.json` catalogs all 72 plugins with name, source, description, version, author, category

### Model Distribution

| Model | Count | Use Cases |
|-------|-------|-----------|
| opus | 42 | Deep reasoning, architecture, complex analysis |
| inherit | 42 | Default/flexible routing |
| sonnet | 51 | Standard coding, review, testing |
| haiku | 18 | Simple tasks, search, documentation |

### Agent Categories (23)

The 112 agents span categories including: code-review, security, testing, architecture, documentation, DevOps, data-engineering, machine-learning, mobile-development, cloud-infrastructure, API-design, performance-optimization, accessibility, internationalization, content-marketing, agent-orchestration, and more.

### Plugin Structure

Each plugin is self-contained:
```
plugins/{name}/
  agents/
    {agent-name}.md
  commands/
    {command-name}.md
  skills/
    {skill-name}/
      SKILL.md
  README.md
```

### Notable Plugins

| Plugin | Description | Agents | Skills |
|--------|-------------|--------|--------|
| conductor | Context-driven development workflow | 3 | 4 |
| agent-teams | Parallel team orchestration | 5 | 2 |
| code-review | Multi-perspective code review | 4 | 3 |
| security-audit | Security analysis pipeline | 3 | 5 |
| python-mastery | Python-specific development | 2 | 6 |
| testing-mastery | Comprehensive testing | 3 | 4 |

---

## VoltAgent/awesome-claude-code-subagents Structure

### Overview

- **127+ subagents** organized in 10 category folders
- Agent definitions are `.md` files with YAML frontmatter (4 fields: name, description, tools, model)
- Key difference from wshobson: VoltAgent includes `tools` field in frontmatter
- Plugin-based installation

### Categories (10)

| Category | Agent Count | Focus |
|----------|-------------|-------|
| code-quality | 15+ | Review, refactoring, testing |
| devops | 12+ | CI/CD, Docker, Kubernetes |
| documentation | 8+ | Technical writing, API docs |
| research | 7+ | Analysis, search, synthesis |
| security | 10+ | Auditing, vulnerability analysis |
| architecture | 8+ | System design, patterns |
| performance | 6+ | Profiling, optimization |
| data | 8+ | Database, ETL, analytics |
| mobile | 5+ | iOS, Android, cross-platform |
| orchestration | 5+ | Multi-agent coordination |

### Tool Assignment Philosophy

| Agent Type | Tools | Rationale |
|------------|-------|-----------|
| Read-only analysts | `["Read", "Grep", "Glob"]` | Cannot accidentally mutate |
| Research agents | `["Read", "Grep", "Glob", "Bash", "WebFetch", "WebSearch"]` | Need internet + shell for discovery |
| Code writers | `["Read", "Write", "Edit", "Bash", "Grep", "Glob"]` | Full filesystem access |
| Documentation agents | `["Read", "Write", "Grep", "Glob"]` | Write access, no Bash needed |

---

## Frontmatter Comparison

| Field | wshobson | VoltAgent | Claude Code Native |
|-------|----------|-----------|-------------------|
| name | yes | yes | yes (required) |
| description | yes (long, detailed) | yes (long, detailed) | yes (required) |
| model | yes (opus/sonnet/haiku) | yes (opus/sonnet/haiku) | yes |
| tools | **NO** | yes (array) | yes |
| version | no | no | no |
| color | no | no | yes (undocumented) |
| permissionMode | no | no | yes |
| maxTurns | no | no | yes |
| skills | no | no | yes |
| mcpServers | no | no | yes |
| hooks | no | no | yes |
| memory | no | no | yes |
| background | no | no | yes |
| effort | no | no | yes |
| isolation | no | no | yes |

**Key observation:** wshobson agents do NOT specify tools in frontmatter, meaning they inherit ALL tools. VoltAgent explicitly restricts tools per agent. Claude Code native supports 14 fields, while both collections use only 3-4.

---

## Research/Explorer Agents Found

### VoltAgent Research Category (7 agents)

| Agent | Model | Tools | Description |
|-------|-------|-------|-------------|
| research-analyst | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Comprehensive research methodology with structured output |
| search-specialist | haiku | Read, Grep, Glob, WebFetch, WebSearch | Fast web search and source discovery |
| data-researcher | haiku | Read, Grep, Glob, Bash | Data analysis and pattern discovery |
| competitive-analyst | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Market and competitor analysis |
| market-researcher | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Market trend research |
| trend-analyst | haiku | Read, Grep, Glob, WebFetch | Trend identification and tracking |
| scientific-literature-researcher | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Academic paper analysis |

### wshobson Research-Adjacent Agents

No dedicated research category exists. Closest agents:
- `search-specialist` (under content-marketing plugin)
- `context-manager` (under agent-orchestration plugin)
- Various analysis agents across domain-specific plugins

---

## Agents Worth Adopting

### From VoltAgent

1. **agent-organizer** -- Multi-agent team assembly and routing. Could improve our swarm coordination.
2. **research-analyst** -- Comprehensive research methodology with structured output format. Good template for our researcher agent.
3. **knowledge-synthesizer** -- Knowledge aggregation and synthesis. Useful for compiling research findings.
4. **multi-agent-coordinator** -- Coordinates parallel agent execution. Reference for orchestration patterns.

### From wshobson

1. **conductor plugin** -- Context-driven development workflow. The conductor pattern (assess context, route to specialist, verify output) is a clean orchestration model.
2. **agent-teams plugin** -- Parallel team orchestration with pre-defined team compositions. Could adopt team presets for common workflows.
3. **code-review plugin** -- Multi-perspective review (4 agents with different review focuses). More thorough than single-agent review.
4. **security-audit plugin** -- Security analysis pipeline with multiple specialized agents. Good reference for our security-reviewer.

---

## Installation Methods

### wshobson/agents

```bash
# Full plugin install
/plugin marketplace add wshobson/agents

# Individual plugin
/plugin install wshobson/agents --plugin conductor
```

### VoltAgent/awesome-claude-code-subagents

```bash
# Full collection
/plugin marketplace add VoltAgent/awesome-claude-code-subagents

# Manual: copy specific agent .md files to .claude/agents/
```

---

## Key Differences Summary

| Aspect | wshobson/agents | VoltAgent/subagents |
|--------|-----------------|---------------------|
| Organization | 72 plugins, each self-contained | 10 category folders |
| Total agents | 112 | 127+ |
| Total skills | 146 | Agents only (no separate skills) |
| Frontmatter | 3 fields (name, desc, model) | 4 fields (name, desc, tools, model) |
| Tool restriction | None (inherit all) | Explicit per-agent |
| Research agents | None dedicated | 7 dedicated |
| Installation | Plugin marketplace | Plugin marketplace or manual copy |
| Stars | 31.8K | 14.5K |
