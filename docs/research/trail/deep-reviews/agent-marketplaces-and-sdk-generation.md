# Agent Marketplaces and SDK Generation Deep Review

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:** 20+ sources including skills.sh, SkillsMP, awesome-skills.com, anthropics/skills, agentskills.io, gitagent.sh, JSON-Agents/Standard, oracle/agent-spec, and numerous GitHub repositories

---

## Executive Summary

The Claude Code agent/skill ecosystem has matured into a multi-layer landscape: 6 marketplaces/registries, 8 curated collections, 7+ SDK tools for generation, 4 open standards for agent definitions, and 33 platforms adopting the Agent Skills standard. This document catalogs every discovered marketplace, registry, SDK tool, JSON schema, and orchestration framework.

---

## 1. Marketplaces and Registries

| Registry | URL | Content |
|----------|-----|---------|
| **skills.sh** | https://skills.sh/ | The Open Agent Skills Directory. Leaderboard of 89,481+ skill installs. Browse/search. Install via `npx skills add <owner>/<repo>` or `npx add-skill <owner>/<repo> --skill "name"` |
| **SkillsMP** | https://skillsmp.com | Agent Skills Marketplace for Claude, Codex, ChatGPT |
| **awesome-skills.com** | https://awesome-skills.com/ | Visual directory of 125+ curated skills and plugins (by ComposioHQ) |
| **LobeHub Skills Marketplace** | https://lobehub.com/skills/ | Claude skills marketplace with per-skill pages |
| **claudemarketplaces.com** | https://claudemarketplaces.com/ | Claude Code Marketplace for plugins |
| **skillsllm.com** | https://skillsllm.com/ | Skills LLM marketplace |

---

## 2. Curated Collections

| Collection | URL | Size |
|------------|-----|------|
| **ComposioHQ/awesome-claude-skills** | https://github.com/ComposioHQ/awesome-claude-skills | 125+ skills, updated 2026-03-19 |
| **ComposioHQ/awesome-claude-plugins** | https://github.com/ComposioHQ/awesome-claude-plugins | Curated plugins with agents, hooks, MCP |
| **VoltAgent/awesome-claude-code-subagents** | https://github.com/VoltAgent/awesome-claude-code-subagents | 127+ subagent .md files in 10 categories, 14.4k stars |
| **VoltAgent/awesome-agent-skills** | https://github.com/VoltAgent/awesome-agent-skills | 200+ agent skills |
| **wshobson/agents** | https://github.com/wshobson/agents | 72 plugins, 112 agents, 146 skills, 79 tools, 31.7k stars |
| **vijaythecoder/awesome-claude-agents** | https://github.com/vijaythecoder/awesome-claude-agents | 24+ orchestrated dev agents |
| **anthropics/skills** | https://github.com/anthropics/skills | Official Anthropic skills (docx, pdf, pptx, xlsx + community), 98.6k stars |
| **travisvn/awesome-claude-skills** | https://github.com/travisvn/awesome-claude-skills | Fork/variant of awesome skills |

---

## 3. SDK Tools for Agent Generation

| Tool | Type | What it does |
|------|------|-------------|
| **@anthropic-ai/claude-agent-sdk** | npm (TS/JS) | Programmatic `AgentDefinition` via `query({ agents: {...} })` |
| **claude_agent_sdk** (Python) | pip | Python SDK with `AgentDefinition` dataclass |
| **`/agents` command** | Built-in CLI | Interactive agent creation wizard in Claude Code |
| **`--agents` CLI flag** | Built-in CLI | Pass JSON agent definitions at session start |
| **SkillForge** | Meta-skill | https://github.com/tripleyak/SkillForge -- generates best-in-class skills |
| **Skill Factory** | Toolkit | https://github.com/alirezarezvani/claude-code-skill-factory -- builds production skills/agents at scale |
| **Agent Skill Creator** | Meta-skill | https://github.com/FrancyJGLisboa/agent-skill-creator -- teaches Claude to create agents |
| **skill-creator** | Official | https://github.com/anthropics/skills/tree/main/skills/skill-creator -- Anthropic's official skill creator |
| **skills-ref** | Validator | https://github.com/agentskills/agentskills/tree/main/skills-ref -- validates SKILL.md |

---

## 4. JSON Schemas and Type Definitions

### A. Claude Code AgentDefinition (TypeScript SDK)

```typescript
type AgentDefinition = {
  description: string;           // Required: when to use this agent
  tools?: string[];              // Optional: allowed tool names
  disallowedTools?: string[];    // Optional: tools to deny
  prompt: string;                // Required: system prompt
  model?: "sonnet" | "opus" | "haiku" | "inherit";
  mcpServers?: AgentMcpServerSpec[];
  skills?: string[];             // Skill names to preload
  maxTurns?: number;
  criticalSystemReminder_EXPERIMENTAL?: string;
};
```

### B. Claude Code .claude/agents/*.md Frontmatter

```yaml
name: string             # Required: lowercase + hyphens
description: string      # Required: when to delegate
tools: string            # Optional: comma-separated tool names
disallowedTools: string  # Optional: tools to deny
model: string            # Optional: sonnet|opus|haiku|inherit|full-model-id
permissionMode: string   # Optional: default|acceptEdits|dontAsk|bypassPermissions|plan
maxTurns: number         # Optional: max agentic turns
skills: list             # Optional: skills to preload
mcpServers: list         # Optional: MCP server configs
hooks: object            # Optional: lifecycle hooks
memory: string           # Optional: user|project|local
background: boolean      # Optional: run as background task
effort: string           # Optional: low|medium|high|max
isolation: string        # Optional: worktree
```

### C. Agent Skills Open Standard (agentskills.io)

```yaml
name: string             # Required: max 64 chars, lowercase+hyphens
description: string      # Required: max 1024 chars
license: string          # Optional
compatibility: string    # Optional: max 500 chars
metadata: map            # Optional: string->string
allowed-tools: string    # Optional: space-delimited (experimental)
```

### D. GitAgent agent.yaml Schema

```yaml
spec_version: "0.1.0"
name: string
version: string
description: string
model:
  preferred: string
compliance: object       # FINRA, SEC, Federal Reserve
segregation_of_duties: object
recordkeeping: object
```

### E. JSON Agents Standard (PAM)

```json
{
  "manifest_version": "1.0",
  "profiles": ["core", "exec", "gov", "graph"],
  "agent": { "id": "ajson://...", "name": "...", "version": "...", "description": "..." },
  "capabilities": ["..."],
  "tools": ["..."],
  "runtime": {},
  "security": {},
  "policies": ["..."],
  "graph": { "nodes": ["..."], "edges": ["..."] }
}
```

### F. Oracle Open Agent Specification

- YAML/JSON serialization
- Components: agents, flows, nodes, tools
- Python SDK: PyAgentSpec
- Spec URL: https://oracle.github.io/agent-spec/language_spec_25_4_0.html

---

## 5. Open Standards for Agent Definitions

| Standard | URL | Status |
|----------|-----|--------|
| **Agent Skills** (agentskills.io) | https://agentskills.io/specification | Production. Adopted by 33+ tools (Claude, Cursor, VS Code, Gemini CLI, OpenAI Codex, etc.) |
| **GitAgent** | https://github.com/open-gitagent/gitagent / https://www.gitagent.sh/ | Active. Git-native agent standard. Export to Claude Code, OpenAI, CrewAI, etc. |
| **JSON Agents** | https://github.com/JSON-Agents/Standard | v1.0.0 Draft. JSON Schema 2020-12. Python validator production-ready |
| **Oracle Agent Spec** | https://github.com/oracle/agent-spec | Active. Framework-agnostic. PyAgentSpec SDK. Adapters for LangGraph, AutoGen, CrewAI |

---

## 6. Platforms Adopting Agent Skills Standard (33 tools)

Claude Code, Claude.ai, Cursor, VS Code (Copilot), GitHub Copilot, Gemini CLI, OpenAI Codex, Roo Code, OpenCode, OpenHands, Goose, Junie (JetBrains), Amp, Letta, Firebender, Mux (Coder), Autohand, TRAE (ByteDance), Spring AI, Mistral Vibe, Command Code, Ona, VT Code, Qodo, Laravel Boost, Emdash, Snowflake Cortex Code, Kiro, Piebald, Factory, pi, Databricks, Agentman

---

## 7. Orchestration Frameworks

| Framework | URL | Stars |
|-----------|-----|-------|
| **Everything Claude Code** | https://github.com/affaan-m/everything-claude-code | 88.5k |
| **Vibe Kanban** | https://github.com/BloopAI/vibe-kanban | 23.5k |
| **Ruflo** | https://github.com/ruvnet/ruflo | 21.9k |
| **SuperClaude Framework** | https://github.com/SuperClaude-Org/SuperClaude_Framework | 21.7k |
| **oh-my-claudecode** | https://github.com/Yeachan-Heo/oh-my-claudecode | 10.5k |
| **claude-squad** | https://github.com/smtg-ai/claude-squad | 6.4k |
| **gstack** | https://github.com/garrytan/gstack | Skill-based, 21 slash commands, Conductor integration |
| **Continuous Claude** | https://github.com/parcadei/Continuous-Claude-v3 | 3.6k |
| **AI Maestro** | https://github.com/23blocks-OS/ai-maestro | 539 |
| **Subtask** | https://github.com/zippoxer/subtask | 320 |

---

## 8. Researcher Agent Patterns

Key patterns for how researcher agents are configured across the ecosystem:

- **Built-in Explore**: model=haiku, tools=Read-only, thoroughness levels (quick/medium/very thorough)
- **Built-in Plan**: model=inherit, tools=Read-only, used in plan mode
- **VoltAgent research category**: 7 agents (research-analyst, search-specialist, trend-analyst, competitive-analyst, market-researcher, data-researcher, scientific-literature-researcher)
- **wshobson agents Research team preset**: parallel multi-agent research
- **Skill with context:fork + agent:Explore**: Run research in isolated read-only subagent
- **Common tools for researchers**: Read, Grep, Glob, Bash (read-only patterns)
- **Agent memory**: `memory: project` or `memory: user` for cross-session learning

---

## Source Catalog

| URL | Type |
|-----|------|
| https://skills.sh/ | Marketplace |
| https://skillsmp.com | Marketplace |
| https://awesome-skills.com/ | Marketplace |
| https://lobehub.com/skills/ | Marketplace |
| https://claudemarketplaces.com/ | Marketplace |
| https://skillsllm.com/ | Marketplace |
| https://github.com/ComposioHQ/awesome-claude-skills | Collection |
| https://github.com/ComposioHQ/awesome-claude-plugins | Collection |
| https://github.com/VoltAgent/awesome-claude-code-subagents | Collection |
| https://github.com/VoltAgent/awesome-agent-skills | Collection |
| https://github.com/wshobson/agents | Collection |
| https://github.com/vijaythecoder/awesome-claude-agents | Collection |
| https://github.com/anthropics/skills | Official |
| https://github.com/travisvn/awesome-claude-skills | Collection |
| https://agentskills.io/specification | Standard |
| https://github.com/open-gitagent/gitagent | Standard |
| https://www.gitagent.sh/ | Standard |
| https://github.com/JSON-Agents/Standard | Standard |
| https://github.com/oracle/agent-spec | Standard |
| https://github.com/tripleyak/SkillForge | SDK Tool |
| https://github.com/alirezarezvani/claude-code-skill-factory | SDK Tool |
| https://github.com/FrancyJGLisboa/agent-skill-creator | SDK Tool |
| https://github.com/anthropics/skills/tree/main/skills/skill-creator | SDK Tool |
| https://github.com/agentskills/agentskills/tree/main/skills-ref | Validator |
| https://github.com/affaan-m/everything-claude-code | Framework |
| https://github.com/BloopAI/vibe-kanban | Framework |
| https://github.com/ruvnet/ruflo | Framework |
| https://github.com/SuperClaude-Org/SuperClaude_Framework | Framework |
| https://github.com/smtg-ai/claude-squad | Framework |
| https://github.com/garrytan/gstack | Framework |
