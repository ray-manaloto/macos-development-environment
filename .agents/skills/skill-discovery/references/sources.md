# Skill Discovery Source Registry

Last verified: 2026-03-21

## CLI Search Tools (npm-verified)

| Tool | npm Package | Install | Search Command | Index Size |
|------|------------|---------|---------------|-----------|
| skills.sh | `skills` | `mise use npm:skills` | `npx skills search "<q>"` | 22K+ skills, 89K+ installs tracked |
| skillkit | `skillkit` | `mise use npm:skillkit` | `npx skillkit search "<q>"` | 13+ AI tools supported |
| agent-skills-cli | `agent-skills-cli` | `mise use npm:agent-skills-cli` | `npx agent-skills search "<q>"` | 175K+ skills, 42+ AI agents |
| skillfish | `skillfish` | `mise use npm:skillfish` | `npx skillfish search "<q>"` | 31-33K skills, 32 AI agents (search currently broken) |
| add-skill | `skills` (same pkg) | included with skills | `npx skills add <owner/repo> --skill <name>` | N/A (installer) |

### MCP-Based Search (for SkillsMP 546K+ catalog)

| Tool | npm Package | Setup | Capability |
|------|------------|-------|-----------|
| skillsmp-mcp-lite | `skillsmp-mcp-lite` | `npx skillsmp-mcp-lite --setup` | Search + install from SkillsMP (546K+ skills) |
| anilcancakir/skillsmp-mcp | GitHub | MCP server | Full SkillsMP API access |

### Discarded CLIs (404 on npm, do not use)
- `@itsdevcoffee/plum` — 404 on npm and GitHub
- `skillfile` — 404 on npm and GitHub

## Web Marketplaces (by catalog size)

| Marketplace | URL | Skills | Search Method | Notes |
|------------|-----|--------|--------------|-------|
| **SkillsMP** | https://skillsmp.com | 546K+ | REST API v1 (key required) + MCP servers | Largest. Cloudflare-protected web UI. |
| **LobeHub** | https://lobehub.com/skills | 229K+ | Web UI only | Major marketplace with versioning |
| **Agent Skills** | https://agentskills.in | 175K+ | `agent-skills-cli` | Emerging universal standard, 42 platforms |
| **Skill.Fish** | https://skill.fish | 31-33K | `skillfish` CLI (broken search) | SPA, backed by mcpmarket.com API |
| **skills.sh** | https://skills.sh | 22K+ | `npx skills search` | Official Vercel CLI, install count rankings |
| **ClawHub** | https://clawhub.ai | NEW | Vector search | Decentralized, quality-first |
| **Smithery** | https://smithery.ai | 5.4K+ MCPs | Web + MCP | MCP hub expanding to skills |
| **awesomeclaude.ai** | https://awesomeclaude.ai/awesome-claude-skills | Directory | Web (curated links) | Curated list, not a registry |
| **awesome-skills.com** | https://awesome-skills.com | 125+ | Web (ComposioHQ) | Curated directory |
| **claudemarketplaces.com** | https://claudemarketplaces.com | Unknown | Web | Plugin marketplace |
| **skillsllm.com** | https://skillsllm.com | Unknown | Web | Enterprise-focused |

## Curated GitHub Collections

| Collection | URL | Stars | Size | Search Method |
|-----------|-----|-------|------|--------------|
| anthropics/skills | github.com/anthropics/skills | 98.6K | Official skills | `gh api repos/anthropics/skills/git/trees/main` |
| affaan-m/everything-claude-code | github.com/affaan-m/everything-claude-code | 90.8K | 116+ skills, 28 agents | `gh api` tree search |
| ComposioHQ/awesome-claude-skills | github.com/ComposioHQ/awesome-claude-skills | 46.4K | 125+ skills | `gh api` tree search |
| wshobson/agents | github.com/wshobson/agents | 31.8K | 146 skills, 112 agents | `gh api` tree search |
| hesreallyhim/awesome-claude-code | github.com/hesreallyhim/awesome-claude-code | 29.4K | Comprehensive list | README grep |
| VoltAgent/awesome-claude-code-subagents | github.com/VoltAgent/awesome-claude-code-subagents | 14.4K | 127+ subagents | `gh api` tree search |
| travisvn/awesome-claude-skills | github.com/travisvn/awesome-claude-skills | 8.9K | Curated list | README grep |
| BehiSecc/awesome-claude-skills | github.com/BehiSecc/awesome-claude-skills | 7.5K | 108 skills | README grep |

## GitHub Search Patterns

```bash
# Find SKILL.md files mentioning a topic
gh search code "<topic>" --filename "SKILL.md" --limit 20

# Find repos with claude-code topic
gh search repos "<topic>" --topic claude-code --sort stars --limit 20 \
  --json fullName,stargazersCount,description

# Find marketplace.json files (custom marketplaces)
gh search code "lspServers" --filename "marketplace.json" --limit 10
```

## Installed Marketplaces (this machine)

| Marketplace | Location | Plugins |
|------------|----------|---------|
| claude-code-workflows | ~/.claude/plugins/marketplaces/claude-code-workflows | 72 plugins |
| claude-plugins-official | ~/.claude/plugins/marketplaces/claude-plugins-official | 500+ plugins |
| docker | ~/.claude/plugins/marketplaces/docker | MCP tools |

## High-Adoption Skill Authors

| Author | Repos | Top Skill (installs) | Speciality |
|--------|-------|---------------------|-----------|
| terrylica | cc-skills (20 plugins) | mise-tasks (114) | DevOps, dotfiles, GitHub |
| samhvw8 | dotfiles | mise-expert (98) | mise workflows |
| bobmatnyc | claude-mpm-skills | homebrew-formula-maintenance (84) | Package management |
| faintghost | skills | chezmoi-config (28) | Chezmoi configuration |
| obra | superpowers | test-driven-development (N/A) | SDLC workflow |

## Recommended Search Priority

When searching for a skill, query sources in this order (largest → smallest, fastest → slowest):

1. **Local inventory** — already installed? `find .claude/skills .agents/skills -name SKILL.md | xargs grep -li "<q>"`
2. **skills.sh CLI** — fastest, has adoption metrics: `npx skills search "<q>"`
3. **agent-skills-cli** — 175K+ index: `npx agent-skills search "<q>"`
4. **skillkit** — cross-platform: `npx skillkit search "<q>"`
5. **GitHub code search** — deepest: `gh search code "<q>" --filename SKILL.md`
6. **GitHub collections** — curated quality: `gh api repos/<collection>/git/trees/main`
7. **SkillsMP MCP** — 546K+ if MCP installed: search via MCP tool
8. **skillfish** — 31K+: `npx skillfish search "<q>"` (when search is fixed)

## Open Standards

| Standard | URL | Adoption |
|----------|-----|----------|
| Agent Skills (agentskills.io) | https://agentskills.io/specification | 33+ tools (Claude, Cursor, Codex, etc.) |
