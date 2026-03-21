# Complete Skills Inventory

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://github.com/anthropics/skills (17 official skills, 98.6k stars)
- https://github.com/anthropics/claude-code/plugins (13 first-party plugins)
- https://github.com/ComposioHQ/awesome-claude-skills (108+ community skills)
- https://github.com/ComposioHQ/awesome-claude-plugins (28+ plugins)
- https://github.com/wshobson/agents (146 skills, 112 agents, 72 plugins)
- https://github.com/affaan-m/everything-claude-code (116+ skills, 28 agents)
- https://github.com/VoltAgent/awesome-claude-code-subagents (127+ subagents)
- https://awesomeclaude.ai/ (directory of all major repos)
- https://github.com/garrytan/gstack (21 skills)
- https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep (31+ skills)
- https://github.com/hesreallyhim/awesome-claude-code (28.5k stars)
- https://github.com/travisvn/awesome-claude-skills (8.9k stars)
- https://github.com/BehiSecc/awesome-claude-skills (108 unique skills)
- https://github.com/vijaythecoder/awesome-claude-agents (24 agents)
- https://github.com/obra/superpowers (15 core SDLC skills)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total unique skills across all sources | ~550+ |
| Total unique agents | ~300+ |
| Total unique plugins | ~100+ |
| Installation methods | 5 (plugin marketplace, git clone, manual copy, npm, skills.sh) |
| Skills relevant to our project (MDE) | ~85 |

---

## Source-by-Source Catalog

### 1. anthropics/skills (Official)

17 official skills including: skill-creator, mcp-builder, webapp-testing, pdf, docx, pptx, xlsx, and community contributions. Install via `/plugin install anthropic/skills`.

### 2. anthropics/claude-code/plugins (First-Party)

13 first-party plugins with embedded skills/agents: security-guidance, code-review, pr-review-toolkit, feature-dev, hookify, plugin-dev, ralph-wiggum, commit-commands, and others.

### 3. ComposioHQ/awesome-claude-skills

108+ community skills + 78 SaaS app skills. Largest curated list with categories spanning development, testing, security, DevOps, documentation, and more.

### 4. ComposioHQ/awesome-claude-plugins

28+ plugins with embedded skills. Includes agent orchestration, CI/CD integration, and workflow automation plugins.

### 5. wshobson/agents

146 skills, 112 agents, 72 plugins. The largest single-repo collection organized as self-contained plugins.

### 6. affaan-m/everything-claude-code

116+ skills, 28 agents, 59 commands. Comprehensive framework with hooks system, plugin schema, and contributing templates.

### 7. VoltAgent/awesome-claude-code-subagents

127+ subagents across 10 categories. Focus on agent definitions rather than standalone skills.

### 8. awesomeclaude.ai

Directory of all major repos + official resources. Not a source of original skills but the best index of where to find them.

### 9. garrytan/gstack

21 skills including: investigate, retro, office-hours, plan-eng-review, review, qa, ship, browse, careful, freeze, and more.

### 10. ARIS (Auto-Research-In-Sleep)

31+ skills focused on academic research: research-lit, novelty-check, research-review, auto-review-loop, arxiv, idea-discovery, research-refine, mermaid-diagram, and more.

### 11-15. Bonus Sources

- hesreallyhim/awesome-claude-code (28.5k stars) -- comprehensive index
- travisvn/awesome-claude-skills (8.9k stars) -- curated list
- BehiSecc/awesome-claude-skills (108 unique skills) -- includes OWASP, VibeSec, sanitize
- vijaythecoder/awesome-claude-agents (24 specialized agents)
- obra/superpowers (15 core SDLC skills) -- already installed in our project

---

## Master Skill Inventory Table (MDE-Relevant Skills)

This is the curated subset of ~550+ total skills, filtered to those relevant to our macOS development environment project (Python, mise, chezmoi, research, security, testing, DevOps).

| Skill Name | Source | Category | Install Method | Relevant Agent(s) | Priority |
|------------|--------|----------|----------------|-------------------|----------|
| **test-driven-development** | obra/superpowers | Testing | `git clone` to `~/.claude/skills/superpowers` | coder, tester | HIGH |
| **systematic-debugging** | obra/superpowers | Debugging | same as above | coder, reviewer | HIGH |
| **root-cause-tracing** | obra/superpowers | Debugging | same as above | coder, reviewer | HIGH |
| **finishing-a-development-branch** | obra/superpowers | Git Workflow | same as above | coder | HIGH (already used) |
| **using-git-worktrees** | obra/superpowers | Git Workflow | same as above | coder | HIGH (already used) |
| **subagent-driven-development** | obra/superpowers | Orchestration | same as above | planner, coder | HIGH |
| **dispatching-parallel-agents** | obra/superpowers | Orchestration | same as above | planner | HIGH |
| **brainstorming** | obra/superpowers | Collaboration | same as above | researcher, planner | MEDIUM |
| **writing-plans** | obra/superpowers | Planning | same as above | planner | MEDIUM |
| **executing-plans** | obra/superpowers | Planning | same as above | coder | MEDIUM |
| **verification-before-completion** | obra/superpowers | Quality | same as above | coder, tester | HIGH |
| **requesting-code-review** | obra/superpowers | Review | same as above | coder | MEDIUM |
| **receiving-code-review** | obra/superpowers | Review | same as above | coder | MEDIUM |
| **writing-skills** | obra/superpowers | Meta | same as above | planner | MEDIUM |
| **defense-in-depth** | obra/superpowers | Security | same as above | security-reviewer | HIGH |
| **skill-creator** | anthropics/skills | Meta | `/plugin install anthropic/skills` | planner | MEDIUM |
| **mcp-builder** | anthropics/skills | Development | `/plugin install anthropic/skills` | coder | LOW |
| **webapp-testing** | anthropics/skills | Testing | `/plugin install anthropic/skills` | tester | MEDIUM |
| **pdf** | anthropics/skills | Document | `/plugin install anthropic/skills` | researcher | LOW |
| **security-guidance** | anthropics/claude-code/plugins | Security | `/plugin install security-guidance` | security-reviewer, coder | HIGH |
| **code-review** | anthropics/claude-code/plugins | Review | `/plugin install code-review` | reviewer | HIGH |
| **pr-review-toolkit** | anthropics/claude-code/plugins | Review | `/plugin install pr-review-toolkit` | reviewer | HIGH |
| **feature-dev** | anthropics/claude-code/plugins | Workflow | `/plugin install feature-dev` | coder | MEDIUM |
| **hookify** | anthropics/claude-code/plugins | Meta | `/plugin install hookify` | planner | LOW |
| **plugin-dev** | anthropics/claude-code/plugins | Meta | `/plugin install plugin-dev` | planner | LOW |
| **ralph-wiggum** | anthropics/claude-code/plugins | Autonomous | `/plugin install ralph-wiggum` | coder (long tasks) | MEDIUM |
| **commit** | anthropics/claude-code/plugins | Git | `/plugin install commit-commands` | coder | MEDIUM |
| **/office-hours** | garrytan/gstack | Product | `git clone` to `~/.claude/skills/gstack` | planner | MEDIUM |
| **/plan-eng-review** | garrytan/gstack | Architecture | same | planner, architect | MEDIUM |
| **/review** | garrytan/gstack | Review | same | reviewer | MEDIUM |
| **/investigate** | garrytan/gstack | Debugging | same | coder | MEDIUM |
| **/qa** | garrytan/gstack | Testing | same | tester | MEDIUM |
| **/ship** | garrytan/gstack | Release | same | coder | LOW |
| **/browse** | garrytan/gstack | Browser | same | tester | LOW |
| **/careful** | garrytan/gstack | Safety | same | coder | MEDIUM |
| **/freeze** | garrytan/gstack | Safety | same | coder | LOW |
| **research-lit** | ARIS | Research | `git clone` to `~/.claude/skills/` | researcher | HIGH |
| **novelty-check** | ARIS | Research | same | researcher | MEDIUM |
| **research-review** | ARIS | Research | same | researcher | MEDIUM |
| **auto-review-loop** | ARIS | Review | same | reviewer | MEDIUM |
| **arxiv** | ARIS | Research | same | researcher | LOW |
| **mermaid-diagram** | ARIS | Visualization | same | planner, researcher | MEDIUM |
| **python-patterns** | everything-claude-code | Python | `/plugin marketplace add affaan-m/everything-claude-code` | coder | HIGH |
| **python-testing** | everything-claude-code | Testing | same | tester | HIGH |
| **python-reviewer** | everything-claude-code | Review | same | reviewer | HIGH |
| **tdd-workflow** | everything-claude-code | Testing | same | tester, coder | HIGH |
| **security-review** | everything-claude-code | Security | same | security-reviewer | HIGH |
| **e2e-testing** | everything-claude-code | Testing | same | tester | MEDIUM |
| **continuous-learning** | everything-claude-code | Meta | same | all agents | MEDIUM |
| **continuous-learning-v2** | everything-claude-code | Meta | same | all agents | MEDIUM |
| **verification-loop** | everything-claude-code | Quality | same | tester | HIGH |
| **eval-harness** | everything-claude-code | Quality | same | tester | MEDIUM |
| **search-first** | everything-claude-code | Research | same | researcher | HIGH |
| **skill-stocktake** | everything-claude-code | Meta | same | planner | MEDIUM |
| **docker-patterns** | everything-claude-code | DevOps | same | coder | LOW |
| **deployment-patterns** | everything-claude-code | DevOps | same | coder | LOW |
| **api-design** | everything-claude-code | Architecture | same | architect, coder | LOW |
| **backend-patterns** | everything-claude-code | Architecture | same | coder | MEDIUM |
| **postgres-patterns** | everything-claude-code | Database | same | coder | LOW |
| **autonomous-loops** | everything-claude-code | Orchestration | same | planner | MEDIUM |
| **python-pro** | VoltAgent/subagents | Python | `/plugin marketplace add VoltAgent/awesome-claude-code-subagents` or manual copy | coder | MEDIUM |
| **security-engineer** | VoltAgent/subagents | Security | same | security-reviewer | MEDIUM |
| **security-auditor** | VoltAgent/subagents | Security | same | security-reviewer | MEDIUM |
| **devops-engineer** | VoltAgent/subagents | DevOps | same | coder | LOW |
| **docker-expert** | VoltAgent/subagents | DevOps | same | coder | LOW |
| **code-reviewer** | VoltAgent/subagents | Review | same | reviewer | MEDIUM |
| **performance-engineer** | VoltAgent/subagents | Performance | same | coder | LOW |
| **research-analyst** | VoltAgent/subagents | Research | same | researcher | MEDIUM |
| **documentation-engineer** | VoltAgent/subagents | Docs | same | researcher | LOW |
| **cli-developer** | VoltAgent/subagents | Development | same | coder | MEDIUM |
| **refactoring-specialist** | VoltAgent/subagents | Quality | same | coder | MEDIUM |
| **kaizen** | ComposioHQ/awesome-claude-skills | Process | manual copy to `~/.config/claude-code/skills/` | planner | MEDIUM |
| **owasp-security** | BehiSecc list | Security | manual copy | security-reviewer | HIGH |
| **VibeSec-Skill** | BehiSecc list | Security | manual copy | security-reviewer | MEDIUM |
| **sanitize** | BehiSecc list | Security | manual copy | security-reviewer | MEDIUM |
| **agnix** | BehiSecc list | Linting | manual copy | reviewer | LOW |
| **kanban-skill** | BehiSecc list | Project Mgmt | manual copy | planner | LOW |
| **recall** | ArtemXTech/personal-os-skills | Memory | `/plugin marketplace add ArtemXTech/personal-os-skills` | researcher | MEDIUM |
| **sync-claude-sessions** | ArtemXTech/personal-os-skills | Memory | same | all agents | MEDIUM |
| **notebooklm** (ArtemXTech) | ArtemXTech/personal-os-skills | Research | same | researcher | HIGH |
| **compound-engineering** | EveryInc | Full Workflow | `/plugin marketplace add EveryInc/compound-engineering-plugin` | all agents | MEDIUM |
| **Trail of Bits Security Skills** | travisvn list | Security | manual copy | security-reviewer | HIGH |
| **claude-scientific-skills** | travisvn list | Research | manual copy | researcher | LOW |

---

## Agent Preloading Recommendations

### researcher agent

```yaml
skills:
  - superpowers/brainstorming
  - superpowers/writing-plans
  - aris/research-lit
  - aris/novelty-check
  - everything-claude-code/search-first
  - personal-os-skills/notebooklm
  - personal-os-skills/recall
```

### coder agent

```yaml
skills:
  - superpowers/test-driven-development
  - superpowers/systematic-debugging
  - superpowers/finishing-a-development-branch
  - superpowers/using-git-worktrees
  - superpowers/verification-before-completion
  - everything-claude-code/python-patterns
  - everything-claude-code/tdd-workflow
  - everything-claude-code/backend-patterns
```

### tester agent

```yaml
skills:
  - superpowers/test-driven-development
  - superpowers/defense-in-depth
  - everything-claude-code/python-testing
  - everything-claude-code/verification-loop
  - everything-claude-code/e2e-testing
  - everything-claude-code/eval-harness
```

### reviewer agent

```yaml
skills:
  - plugins/code-review
  - plugins/pr-review-toolkit
  - plugins/security-guidance
  - everything-claude-code/python-reviewer
  - everything-claude-code/security-review
  - superpowers/root-cause-tracing
```

### security-reviewer agent

```yaml
skills:
  - plugins/security-guidance
  - everything-claude-code/security-review
  - owasp-security
  - trail-of-bits-security-skills
  - superpowers/defense-in-depth
  - VibeSec-Skill
```

### planner agent

```yaml
skills:
  - superpowers/subagent-driven-development
  - superpowers/dispatching-parallel-agents
  - superpowers/writing-plans
  - superpowers/writing-skills
  - everything-claude-code/autonomous-loops
  - everything-claude-code/skill-stocktake
```

---

## Gap Analysis

### Skills That Do NOT Exist Anywhere

These skills were searched across all 15 sources and do not exist in any catalog:

| Missing Skill | Domain | Impact |
|---------------|--------|--------|
| **chezmoi skills** | Dotfiles | No chezmoi-specific skills in any catalog |
| **mise skills** | Tool management | No mise-specific skills in any catalog |
| **dotfiles lifecycle skills** | Dotfiles | No dotfiles management skills exist |
| **fnox/secrets skills** | Secrets | No fnox integration skills exist |
| **hk (git hooks) skills** | Git hooks | No hk-specific skills exist |
| **structlog skills** | Logging | No structured logging skills exist |
| **Pydantic codegen skills** | Code generation | No schema-driven codegen skills exist |

### Skills We Should Build (Greenfield)

Per the existing chezmoi-mise-dotfiles-skills deep review, we need 3-4 new skills:

1. **chezmoi-lifecycle** -- add/edit/apply/verify cycle
2. **mise-tool-sync** -- ensure mise config and chezmoi templates stay in sync
3. **dotfiles-drift-detection** -- detect and remediate drift between source and deployed
4. **secrets-rotation** -- fnox + age + keychain rotation workflow

---

## Note on `agent-fetch`

The npm package `agent-fetch` referenced in the research pipeline rule does not exist on the npm registry (returns E404 Not Found). WebFetch + `gh api` are the correct tools for fetching repository content.
