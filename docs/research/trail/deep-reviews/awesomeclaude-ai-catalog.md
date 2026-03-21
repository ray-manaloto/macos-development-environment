# awesomeclaude.ai Deep Review

**Date:** 2026-03-20
**Analyst:** research-agent
**Sources:**
- https://awesomeclaude.ai/
- https://awesomeclaude.ai/code-cheatsheet
- https://awesomeclaude.ai/awesome-claude-code
- https://awesomeclaude.ai/vibe-coding-guide
- https://awesomeclaude.ai/how-to
- https://awesomeclaude.ai/ralph-wiggum
- https://github.com/webfuse-com/awesome-claude (backing repo)

---

## What is awesomeclaude.ai?

awesomeclaude.ai is a **curated directory of Claude AI resources** maintained by Webfuse (webfuse.com), backed by the GitHub repo `webfuse-com/awesome-claude`. It is NOT a marketplace or registry with installable packages -- it is a human-curated link directory organized into categories with editorial descriptions and GitHub star counts.

---

## Site Structure (6 active pages)

1. **/** (main) -- Resource directory with 7 major sections: Official Anthropic, Claude Code & MCP, Community Lists, Extensions, Applications, Education, Community
2. **/code-cheatsheet** -- Comprehensive Claude Code 2.0 cheatsheet covering: installation, keyboard shortcuts, config hierarchy, checkpointing, 46+ slash commands, headless mode, skills, plugins, MCP servers, git worktrees, subagents, permissions, hooks
3. **/awesome-claude-code** -- Deep catalog of 200+ tools: agent skills (18), workflows (31), Ralph Wiggum (6), tooling (56), statuslines (5), hooks (11), slash commands (53+), CLAUDE.md examples (20+), orchestrators (10)
4. **/vibe-coding-guide** -- Methodology guide for AI-assisted development with the "Vibe Loop" pattern
5. **/how-to** -- 30 how-to guides for specific integration tasks (databases, email, Slack, Docker, etc.)
6. **/ralph-wiggum** -- Resources for the iterative Ralph loop technique

**404 pages:** /agents, /skills, /plugins, /tools, /resources, /marketplace, /directory, /catalog

---

## Does it have agent definitions we can reference?

**No native agent definitions.** It catalogs 18+ agent skill repos and 10 orchestrators, but does not define agents itself. The most valuable agent-related resources it links to:

- **Everything Claude Code** (78.8K stars) -- github.com/affaan-m/everything-claude-code
- **Superpowers** (87.2K stars) -- github.com/obra/superpowers (already known)
- **Claude Scientific Skills** (15.1K stars) -- github.com/K-Dense-AI/claude-scientific-skills
- **Compound Engineering Plugin** (10.5K stars) -- github.com/EveryInc/compound-engineering-plugin (already in catalog)
- **Claude Code Agents** (72 stars) -- github.com/undeadlist/claude-code-agents
- **AgentSys** (598 stars) -- github.com/avifenesh/agentsys

---

## Does it link to marketplaces/registries we haven't found?

**No new marketplaces.** It links to:
- skills.sh (already in our catalog)
- Claude plugins marketplace (already known)
- awesome-mcp-servers (83.2K stars, already known)
- Various "awesome-*" GitHub lists (most already known)

---

## New Tools/Projects NOT in Our Source Catalog

### HIGH Priority

| Repo | Stars | Why |
|------|-------|-----|
| affaan-m/everything-claude-code | 78.8K | Massive resource collection |
| K-Dense-AI/claude-scientific-skills | 15.1K | Scientific research skills |
| davila7/claude-code-templates | 23.0K | Template collection with UI |
| automazeio/ccpm | 7.6K | Project management workflow |
| diet103/claude-code-infrastructure-showcase | 9.3K | Hooks-based skill selection |
| FlorianBruniaux/claude-code-ultimate-guide | 1.6K | Comprehensive guide |
| NeoLabHQ/context-engineering-kit | 645 | Context engineering techniques |
| frankbria/ralph-claude-code | 7.9K | Ralph framework |
| mikeyobrien/ralph-orchestrator | 2.2K | Ralph orchestration |
| snwfdhmp/awesome-ralph | 803 | Ralph resource list |
| vijaythecoder/awesome-claude-agents | 4.0K | Agent-specific awesome list |
| VoltAgent/awesome-claude-code-subagents | 14.0K | Subagent patterns |
| hesreallyhim/awesome-claude-code | 28.5K | Community curated list |
| travisvn/awesome-claude-skills | 8.9K | Skills list |
| BehiSecc/awesome-claude-skills | 7.5K | Skills list |
| langgptai/awesome-claude-prompts | 4.5K | Prompts list |

### MEDIUM Priority (useful tooling)

| Repo | Stars | Why |
|------|-------|-----|
| ryoppippi/ccusage | 11.6K | Usage monitoring CLI |
| Haleclipse/CCometixLine | 2.2K | Statusline in Rust |
| sirmalloc/ccstatusline | 5.1K | Customizable statusline |
| AndyMik90/Auto-Claude | 13.3K | Multi-agent framework w/ kanban |
| smtg-ai/claude-squad | 6.4K | Terminal multi-agent manager |
| eyaltoledano/claude-task-master | 25.9K | Task management system |
| slopus/happy | 15.3K | Parallel Claude spawner |
| backnotprop/plannotator | 3.2K | Interactive plan review hooks |
| nizos/tdd-guard | 1.8K | TDD enforcement hooks |
| trailofbits/skills | 3.6K | Security audit skills |
| Piebald-AI/claude-code-system-prompts | 5.9K | System prompt extraction |
| shareAI-lab/learn-claude-code | 28.8K | Agent design analysis |

### LOW Priority (niche but notable)

| Repo | Stars | Why |
|------|-------|-----|
| skills-directory/skill-codex | 858 | Cross-agent prompting |
| avifenesh/agentsys | 598 | Workflow automation |
| akin-ozer/cc-devops-skills | 114 | DevOps skills |
| jeffallan/claude-skills | 6.8K | 65 fullstack skills |
| pchalasani/claude-code-tools | 1.6K | Session continuity |
| dagger/container-use | 3.6K | Docker dev environments |
| SuperClaude-Org/SuperClaude_Framework | 21.5K | Config framework |
| Piebald-AI/tweakcc | 1.3K | Styling customization |
| mbailey/voicemode | 895 | Voice integration |
| carlrannaberg/claudekit | 632 | CLI toolkit w/ checkpointing |

---

## Configuration Patterns Documented

The cheatsheet documents several patterns worth noting:

1. **4-tier config hierarchy**: Enterprise > Project Local > Project Shared > User Global
2. **Skill YAML frontmatter**: name, description, allowed-tools fields
3. **Subagent YAML frontmatter**: name, description, tools, model fields
4. **Hook event types**: PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, SubagentStop, PreCompact, SessionStart/End
5. **Permission templates**: Basic, Strict, MCP restrictions
6. **Plugin management**: `/plugin marketplace add <url>`, `/plugin install <name>@<marketplace>`

---

## Recommendations

1. **Add to source catalog**: All HIGH priority repos above should be added to `docs/research/source-catalog.md`
2. **Deep review candidates**: everything-claude-code and claude-scientific-skills deserve their own deep reviews
3. **No new marketplaces discovered**: awesomeclaude.ai links to the same marketplaces already in our catalog
4. **Cheatsheet is valuable reference**: The /code-cheatsheet page is the most comprehensive single-page Claude Code reference found outside official docs
5. **Ralph Wiggum pattern**: Multiple repos implement this autonomous loop pattern -- worth evaluating for our research pipeline
