# Research Source Catalog

**Created:** 2026-03-20
**Purpose:** Track all sources provided during brainstorming, their research status, and NotebookLM ingestion status.
**Spec:** `docs/superpowers/specs/2026-03-20-self-improving-research-system-design.md`
**NotebookLM Notebook:** `a9be3bc0-6152-4c4e-86e6-f364f1df6721` ("The Claude Code, NotebookLM, and Obsidian Research Stack")

## Status Legend

- [ ] **Not reviewed** — URL provided but not yet researched
- [~] **Skim only** — README/summary read via WebFetch (truncated), needs deep review with `agent-fetch`
- [x] **Full review** — Complete content analyzed with `agent-fetch` or equivalent
- NB: In NotebookLM notebook

---

## Blog Articles — Claude Code & Dev Tools

| Status | Article | URL | Verdict | In NB |
|--------|---------|-----|---------|-------|
| [x] | Karan Bansal: The 2-Minute Claude Code Upgrade You're Probably Missing: LSP | https://karanbansal.in/blog/claude-code-lsp/ | STRONG — Exact LSP setup steps, ENABLE_LSP_TOOL flag, plugin installation gotchas, debug verification | No |

---

## YouTube Channels

| Status | Channel | URL | Notes |
|--------|---------|-----|-------|
| [~] | @GithubAwesome | https://www.youtube.com/@GithubAwesome | Trending repos, AI tools |
| [~] | @ArtemXTech | https://www.youtube.com/@ArtemXTech | Claude Code + Obsidian skills, lab sessions |
| [ ] | @intheworldofai | https://www.youtube.com/@intheworldofai | AI tutorials |
| [ ] | @indydevdan | https://www.youtube.com/@indydevdan | Dev tooling |
| [ ] | @betterstack | https://www.youtube.com/@betterstack | DevOps, monitoring |
| [ ] | @Chase-H-AI | https://www.youtube.com/@Chase-H-AI | AI workflows, Claude Code pipelines |
| [ ] | @ManuAGI | https://www.youtube.com/@ManuAGI | AI agents |
| [ ] | @ColeMedin | https://www.youtube.com/@ColeMedin | AI development |
| [ ] | @AILABS-393 | https://www.youtube.com/@AILABS-393 | AI labs |
| [ ] | @owainlewis | https://www.youtube.com/@owainlewis | AI/Claude Code |
| [ ] | @GregIsenberg | https://www.youtube.com/@GregIsenberg | Tech/startup |

### Specific Videos

| Status | Video | URL | In NB |
|--------|-------|-----|-------|
| [ ] | Unknown (provided by user) | https://www.youtube.com/watch?v=Jvl_MOBPRXI&t=835s | No |

---

## GitHub Repos — Agent Orchestration

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | msitarzewski/agency-agents | https://github.com/msitarzewski/agency-agents | SKIP — prompt library | No |
| [~] | VoltAgent (org) | https://github.com/orgs/VoltAgent/repositories | MINE PERIODICALLY | No |
| [~] | ComposioHQ/composio | https://github.com/ComposioHQ/composio | CONSIDER — 500+ integrations | No |
| [x] | ComposioHQ/agent-orchestrator | https://github.com/ComposioHQ/agent-orchestrator | STRONG CONSIDER — worktree + CI feedback, escalation thresholds | Yes |
| [~] | NousResearch/hermes-agent | https://github.com/NousResearch/hermes-agent | CONSIDER — closed learning loop | No |
| [x] | knowsuchagency/mcp2cli | https://github.com/knowsuchagency/mcp2cli | STRONG CONSIDER — runtime CLI gen, bake pattern, TOON output, fnox-compatible | Yes |

## GitHub Repos — Claude Code Skills & Plugins

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | ArtemXTech/personal-os-skills | https://github.com/ArtemXTech/personal-os-skills | MEDIUM — recall, sync-sessions | No |
| [~] | amanaiproduct/amans-skills | https://github.com/amanaiproduct/amans-skills | MEDIUM — ralph-loop, dashboard | No |
| [x] | EveryInc/compound-engineering-plugin | https://github.com/EveryInc/compound-engineering-plugin | HIGH — skill chaining, 5-subagent compound extraction, docs/solutions/ | Yes |
| [x] | EveryInc/compound-knowledge-plugin | https://github.com/EveryInc/compound-knowledge-plugin | HIGH — prose confidence assessment, learning taxonomy, grep retrieval | Yes |
| [~] | ComposioHQ/awesome-claude-plugins | https://github.com/ComposioHQ/awesome-claude-plugins | HIGH — skill-creator, connect-apps | No |
| [~] | ComposioHQ/awesome-claude-skills | https://github.com/ComposioHQ/awesome-claude-skills | HIGH — kaizen, subagent-driven-dev | No |
| [~] | paullarionov/claude-certified-architect | https://github.com/paullarionov/claude-certified-architect | LOW — study reference | No |

## GitHub Repos — Auto-Research & Memory

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [x] | wanshuiyin/Auto-claude-code-research-in-sleep | https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep | VERY HIGH — checkpoint state, AUTO_PROCEED, 31 composable skills | Yes |
| [x] | thedotmack/claude-mem | https://github.com/thedotmack/claude-mem | HIGH — 3-layer progressive disclosure ~10x savings (AGPL, adopt pattern only) | Yes |
| [x] | rysweet/amplihack | https://github.com/rysweet/amplihack | HIGH — L1-L12 eval ladder, 10-failure taxonomy, self-improvement loop | No |
| [~] | nidhinjs/prompt-master | https://github.com/nidhinjs/prompt-master | MODERATE — intent extraction | No |

## GitHub Repos — ruvnet Ecosystem

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | ruvnet/ruflo | https://github.com/ruvnet/ruflo | ALREADY INTEGRATED via claude-flow | Yes |
| [~] | ruvnet/RuView | https://github.com/ruvnet/RuView | SKIP — IoT, not applicable | No |
| [~] | ruvnet/RuVector | https://github.com/ruvnet/RuVector | ENGINE underneath claude-flow | No |
| [~] | ruvnet/agentic-flow | https://github.com/ruvnet/agentic-flow | SDK LAYER for claude-flow | No |

## GitHub Repos — Reference Dotfiles & Agent Patterns

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | martinemde/dotfiles | https://github.com/martinemde/dotfiles | REFERENCE — AI-first dotfiles w/ chezmoi | Yes |
| [x] | pelted/.dotfiles | https://github.com/pelted/.dotfiles | STRONG — chezmoi + 1Password + mise + bootstrap, agent-focused | No |
| [x] | jalexandercarr/dotfiles | https://github.com/jalexandercarr/dotfiles | STRONG — aide CLI, template-based agent config, symlink strategy | No |
| [x] | barnabasJ/dotfiles | https://github.com/barnabasJ/dotfiles | STRONG — agents/ folder pattern, symlink to ~/.claude/commands/ (solves chezmoi conflicts) | No |
| [x] | guaje/dotfiles | https://github.com/guaje/dotfiles | MEDIUM — chezmoi + age encryption + fnox, Android/Termux | No |
| [x] | Aristoddle/beppe-dotfiles-docs | https://github.com/Aristoddle/beppe-dotfiles-docs | VERY HIGH — Phase 6 research: 9 agents + 8 skills, parallel execution, chezmoi integration | No |
| [x] | JeremiahChurch/dotfiles-template | https://github.com/JeremiahChurch/dotfiles-template | REFERENCE — Claude Code + chezmoi starter template | No |
| [x] | lev-os/leviathan | https://github.com/lev-os/leviathan | ADVANCED — multi-machine sync, source-side intent resolution, ops dashboard | No |

## GitHub Repos — Token Optimization

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | HKUDS/CLI-Anything | https://github.com/HKUDS/CLI-Anything | CONSIDER — desktop app → CLI | Yes |

## skills.sh Pages

| Status | Skill | URL | Notes |
|--------|-------|-----|-------|
| [~] | ruvnet/claude-flow | https://skills.sh/ruvnet/claude-flow | 136 skills, 4.6K installs |
| [~] | ruvnet/ruflo | https://skills.sh/ruvnet/ruflo | 135 skills, same ecosystem |
| [~] | ruvnet/ruview | https://skills.sh/ruvnet/ruview | 30 skills, subset |
| [~] | ruvnet/agentic-flow | https://skills.sh/ruvnet/agentic-flow | 35 skills, subset |
| [~] | hkuds/cli-anything | https://skills.sh/hkuds/cli-anything/cli-anything | CLI generation skill |
| [~] | knowsuchagency/mcp2cli | https://skills.sh/knowsuchagency/mcp2cli/mcp2cli | MCP-to-CLI bridge |
| [x] | teng-lin/notebooklm-py | https://skills.sh/teng-lin/notebooklm-py/notebooklm | Installed, auth working |
| [x] | microsoft/playwright-cli | https://skills.sh/microsoft/playwright-cli/playwright-cli | Installed |

## Websites & Services

| Status | Site | URL | Notes |
|--------|------|-----|-------|
| [~] | agen.cy | https://www.agen.cy/ | Consulting firm, not a tool |
| [ ] | Obsidian plugins | https://obsidian.md/plugins | 18 plugins evaluated (skim) |

---

## Anthropic Official Sources

| Status | Source | URL | In NB |
|--------|--------|-----|-------|
| [x] | Claude Code docs | https://code.claude.com/docs/en/overview | Full review: subagents, agent teams, 28 hooks, auto memory, /batch |
| [~] | Claude Code repo | https://github.com/anthropics/claude-code | No |
| [~] | Agent SDK | https://github.com/anthropics/claude-agent-sdk-python | Yes |
| [~] | Official plugins | https://github.com/anthropics/claude-plugins-official | Yes |
| [ ] | Cookbooks | https://github.com/anthropics/claude-cookbooks | No |
| [~] | Official skills | https://github.com/anthropics/skills | Yes |
| [ ] | Claude blog | https://claude.com/blog | No |
| [~] | Engineering blog | https://www.anthropic.com/engineering | No |
| [ ] | Platform cookbook | https://platform.claude.com/cookbook/ | No |

### Anthropic Blog Posts (individually evaluated)

| Status | Post | URL | In NB |
|--------|------|-----|-------|
| [~] | Building effective agents | https://www.anthropic.com/engineering/building-effective-agents | Yes |
| [~] | Building C compiler w/ parallel Claudes | https://www.anthropic.com/engineering/building-c-compiler | Yes |
| [~] | Effective harnesses for long-running agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | Yes |
| [x] | How Anthropic teams use Claude Code | https://claude.com/blog/how-anthropic-teams-use-claude-code | Full review via research-claude-docs agent |

---

## NotebookLM Notebook Sources (27 total)

The notebook `a9be3bc0-6152-4c4e-86e6-f364f1df6721` contains these sources that were provided by the user or added during this session. Sources marked with "pre-existing" were already in the notebook before this conversation.

### Pre-existing (14 sources — YouTube/Medium/GitHub)
1. /loop: 3 Agents Running Inside My Obsidian Vault on a Timer
2. Build Your AI Second Brain with Obsidian + Claude Code (Free Setup)
3. Build Your Second Brain With Claude Code & Obsidian
4. Claude Code + NotebookLM + Obsidian = GOD MODE
5. Claude Code + NotebookLM + Obsidian: The Research Stack Nobody's Using (x2 — possible duplicate)
6. Claude Code Turned Obsidian Into My Dream Second Brain (x2 — possible duplicate)
7. GitHub - ArtemXTech/personal-os-skills
8. GitHub - sean-esk/second-brain-gtd
9. How to Use Notebook LM with Claude Code for Free Research
10. Medium: my-claude-code-now-has-its-own-second-brain-in-obsidian
11. Medium: i-built-an-ai-powered-second-brain-with-obsidian-claude-code (possible duplicate)

### Added during this session (13 sources)
12. Building Effective AI Agents (Anthropic)
13. Building a C compiler with a team of parallel Claudes (Anthropic)
14. Effective harnesses for long-running agents (Anthropic)
15. GitHub - ComposioHQ/agent-orchestrator
16. GitHub - EveryInc/compound-engineering-plugin
17. GitHub - EveryInc/compound-knowledge-plugin
18. GitHub - HKUDS/CLI-Anything
19. GitHub - anthropics/claude-agent-sdk-python
20. GitHub - anthropics/claude-plugins-official
21. GitHub - anthropics/skills
22. GitHub - knowsuchagency/mcp2cli
23. GitHub - martinemde/dotfiles
24. GitHub - ruvnet/ruflo
25. GitHub - thedotmack/claude-mem
26. GitHub - wanshuiyin/Auto-claude-code-research-in-sleep (ARIS)

### Potential duplicates to clean up
- "Claude Code + NotebookLM + Obsidian: The Research Stack Nobody's Using" appears twice
- "Claude Code Turned Obsidian Into My Dream Second Brain" appears twice
- Medium article by sonnyhuynhb may appear twice

---

## Sources NOT Yet Added to NotebookLM

These were researched but not ingested into the notebook:

| URL | Why not added |
|-----|--------------|
| https://github.com/ComposioHQ/composio | Lower priority |
| https://github.com/NousResearch/hermes-agent | Architectural inspiration only |
| https://github.com/rysweet/amplihack | Not yet added |
| https://github.com/nidhinjs/prompt-master | Moderate priority |
| https://github.com/ruvnet/RuVector | Engine layer, not directly useful as source |
| https://github.com/ruvnet/agentic-flow | SDK layer, subset of ruflo |
| https://github.com/amanaiproduct/amans-skills | Medium priority |
| https://github.com/ComposioHQ/awesome-claude-plugins | Not yet added |
| https://github.com/ComposioHQ/awesome-claude-skills | Not yet added |
| https://code.claude.com/docs/en/overview | Should add docs index |
| https://claude.com/blog/how-anthropic-teams-use-claude-code | Should add |

---

## GitHub Repos — Agent Frameworks & Adversarial Review

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [ ] | open-gitagent/gitagent | https://github.com/open-gitagent/gitagent | HIGH — agent creation framework, evaluate for Claude Code compatibility | No |

## Docs & APIs — Adversarial Review Tools

| Status | Source | URL | Notes |
|--------|--------|-----|-------|
| [ ] | Codex non-interactive mode | https://developers.openai.com/codex/noninteractive | Cross-model adversarial reviewer — preferred, no GUI |
| [ ] | Gemini CLI non-interactive | https://github.com/google-gemini/gemini-cli/blob/52250c162d10f97cafc12f0fdd57cea88997b36d/README.md#non-interactive-mode-for-scripts | Fallback cross-model reviewer, already in mise |

## GitHub Repos — Dev Environment Stacks

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [x] | garrytan/gstack | https://github.com/garrytan/gstack | COMPLEMENTARY — 21-skill Claude Code pack (16K+ stars), NOT a dev env tool. Adopt skill chaining pattern. | No |

## Websites — Dev Environment Stacks

| Status | Site | URL | Notes |
|--------|------|-----|-------|
| [x] | gstacks.org | https://gstacks.org/ | Docs for gstack skill pack. Full review confirmed: browser automation, sprint workflow skills. | No |

## GitHub Repos — Auto-Research Frameworks

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [x] | karpathy/autoresearch | https://github.com/karpathy/autoresearch | Autonomous experiment runner, NOT research grading. Binary keep/discard + results.tsv audit trail. | No |

## Unified Skill Manager & Marketplace

| Status | Tool | URL | Type | Size | Notes |
|--------|------|-----|------|------|-------|
| [x] | skillfish CLI | https://github.com/knoxgraeme/skillfish | npm pkg (v1.0.30) | 126⭐ / 10🍴 | Universal skill manager for 32 agents; search/install/sync via mcpmarket.com API; AGPL-3.0; created 2026-01-21 |
| [~] | skill.fish website | https://www.skill.fish | Marketplace SPA | ~31K-33K skills | Vercel Astro SPA (requires JS rendering); inaccessible via direct HTML fetch |
| [ ] | mcpmarket.com | https://mcpmarket.com | Marketplace API | 31K-33K skills | Backend API for skillfish CLI search; returns 403 to direct browser requests |

**skillfish Discovery Commands:**
- `skillfish search <query>` — Search mcpmarket.com registry
- `skillfish add owner/repo` — Install from GitHub (auto-discovers SKILL.md)
- `skillfish submit owner/repo` — Submit skills to skill.fish for indexing
- `skillfish bundle` — Create skillfish.json manifest for team sync
- `skillfish install` — Sync team skills from manifest

**Supported Agents (32 total):** Claude Code · Cursor · Windsurf · Codex · GitHub Copilot · Gemini CLI · OpenCode · Goose · Amp · Roo Code · Kiro CLI · Kilo Code · Trae · Cline · Antigravity · Droid · Augment · OpenClaw · CodeBuddy · Command Code · Crush · Kode · Mistral Vibe · Mux · OpenClaude IDE · OpenHands · Qoder · Qwen Code · Replit · Trae CN · Neovate · AdaL

**Strategic Note:** skillfish is a unified marketplace for ALL agent ecosystems, not Claude Code specific.

---

## URLs Discovered During Cycle 1 (2026-03-20)

Sources found by research agents during deep review. Logged per Source Discovery Protocol (Section 4.4).

| Status | Source | URL | Priority | Discovered by | Via |
|--------|--------|-----|----------|---------------|-----|
| [ ] | mcp2cli blog (token benchmarks) | https://www.orangecountyai.com/blog/mcp2cli-one-cli-for-every-api-zero-wasted-tokens | HIGH | research-mcp2cli-amplihack | mcp2cli README |
| [ ] | CLIHub concept origin | https://kanyilmaz.me/2026/02/23/cli-vs-mcp.html | MEDIUM | research-mcp2cli-amplihack | mcp2cli README |
| [ ] | amplihack docs site | https://rysweet.github.io/amplihack/ | MEDIUM | research-mcp2cli-amplihack | amplihack README |
| [ ] | amplihack standalone eval | https://github.com/rysweet/amplihack-agent-eval | MEDIUM | research-mcp2cli-amplihack | amplihack README |
| [ ] | azlin (Azure VM fleet) | https://github.com/rysweet/azlin | LOW | research-mcp2cli-amplihack | amplihack README |
| [ ] | RustyClawd (Rust Claude Code) | https://github.com/rysweet/RustyClawd | LOW | research-mcp2cli-amplihack | amplihack README |
| [ ] | Conductor (parallel sprints) | https://conductor.build | MEDIUM | research-gstack | gstack README |
| [ ] | Greptile (PR review AI) | https://greptile.com | MEDIUM | research-gstack | gstack README |
| [ ] | Claude Code subagents docs | https://code.claude.com/docs/en/sub-agents | HIGH | research-claude-docs | docs crawl |
| [ ] | Claude Code agent teams docs | https://code.claude.com/docs/en/agent-teams | HIGH | research-claude-docs | docs crawl |
| [ ] | Claude Code hooks docs | https://code.claude.com/docs/en/hooks | HIGH | research-claude-docs | docs crawl |
| [ ] | Claude Code memory docs | https://code.claude.com/docs/en/memory | HIGH | research-claude-docs | docs crawl |
| [ ] | Claude Code skills docs | https://code.claude.com/docs/en/skills | HIGH | research-claude-docs | docs crawl |
| [ ] | Claude Code CLI reference | https://code.claude.com/docs/en/cli-reference | MEDIUM | research-claude-docs | docs crawl |

## Web-Based Skill Marketplaces (Cycle 2 Discovery — 2026-03-21)

**NEW MARKETPLACES DISCOVERED:** 8 active platforms + 10+ GitHub template implementations

| Status | Marketplace | URL | Size | Type | Install Method | Verdict |
|--------|-------------|-----|------|------|-----------------|---------|
| [x] | SkillsMP | https://skillsmp.com | 546,932+ skills | Web marketplace | GitHub clone or browse | CONFIRMED — primary skills marketplace, SKILL.md standard |
| [x] | Awesome Claude | https://awesomeclaude.ai | Curated resources | Directory | Web links | Resource aggregator for tools, extensions, workflows |
| [x] | Skill.Fish | https://skill.fish | ~31K-33K | Marketplace SPA | npm CLI or web | Web-based skill manager with interactive browser |
| [x] | LobeHub Skills | https://lobehub.com/skills | 229,095+ skills | Marketplace | LobeHub CLI or web | Major marketplace, versioned skills, "most installed" ranking |
| [x] | SkillsLLM | https://skillsllm.com | Significant | Marketplace | Web interface | Enterprise-focused with trending/authors views |
| [x] | Agent Skills | https://agentskills.in | 175,000+ skills | Universal PM | npm: `agent-skills-cli` | EMERGING STANDARD — 42+ AI agent platforms (Claude, Cursor, Copilot, Windsurf, Cline, etc.) |
| [x] | ClawHub | https://clawhub.ai | Growing | Decentralized registry | npx clawhub@latest | NEW — Vector search, "non-suspicious" signal filtering, rollback-ready versions |
| [x] | Smithery | https://smithery.ai | 5,411+ MCPs | Hybrid (MCP + skills) | Web + Smithery CLI | PRIMARY MCP HUB expanding to SKILL.md workflows; 63K-66K installs for Anthropic skills |

**Strategic Assessment:**
- **Agent Skills** (agentskills.in) emerging as "npm for agents" — 42+ platform support, cross-platform focus
- **LobeHub** maintains largest skill count (229K+), strong version control
- **SkillsMP** historical standard, foundational indexing
- **Smithery** represents convergence: MCP servers + skills in single discovery platform
- **ClawHub** represents "decentralized future" with vector search quality signal

**GitHub-based Marketplace Implementations (10 repos):**
- diegomarino/claude-toolshed (45 ⭐) — pre-packaged skill bundles
- cased/claude-code-plugins (5 ⭐) — skills + MCP servers + hooks
- shopwareLabs/ai-coding-tools (13 ⭐) — Shopware-specific development marketplace
- ulasbilgen/mcp-skills-plugins (3 ⭐) — MCP server skills wrapper
- trancong12102/ccc (3 ⭐, archived) — curated plugin marketplace template
- Emasoft/claude-plugins-validation (2 ⭐) — validation suite
- ehudhal/claude-code-marketplace (2 ⭐) — template starter
- seansoreilly/claude-code-marketplace (0 ⭐) — marketplace template
- mkelk/claude-marketplace (0 ⭐) — skills/commands/hooks
- Helms-AI/claude-marketplace (1 ⭐) — enterprise marketplace

## Deep Review Queue (Priority Order)

**Cycle 1 COMPLETED — all 12 sources below fully reviewed on 2026-03-20.**

~~0. https://github.com/garrytan/gstack + https://gstacks.org/~~ — DONE: Skill pack, not dev env tool
~~0b. https://github.com/karpathy/autoresearch~~ — DONE: Experiment runner, not research grading
~~1. https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep~~ — DONE: Checkpoint state pattern
~~2. https://github.com/EveryInc/compound-engineering-plugin~~ — DONE: Skill chaining, compound extraction
~~3. https://github.com/EveryInc/compound-knowledge-plugin~~ — DONE: Prose confidence, learning taxonomy
~~4. https://github.com/thedotmack/claude-mem~~ — DONE: 3-layer retrieval (adopt pattern, not tool)
~~5. https://github.com/ComposioHQ/agent-orchestrator~~ — DONE: CI feedback, escalation thresholds
~~6. https://github.com/knowsuchagency/mcp2cli~~ — DONE: Bake pattern, TOON output
~~7. https://github.com/HKUDS/CLI-Anything~~ — Not reviewed this cycle (CONSIDER priority)
~~8. https://github.com/martinemde/dotfiles~~ — Not reviewed this cycle (REFERENCE priority)
~~9. https://github.com/rysweet/amplihack~~ — DONE: L1-L12 eval, error taxonomy
~~10. https://code.claude.com/docs/en/overview~~ — DONE: Native features replace ~80% of claude-flow

### Cycle 2 Queue (next session)

1. https://github.com/HKUDS/CLI-Anything — CLI generation (CONSIDER)
2. https://github.com/martinemde/dotfiles — reference dotfiles (REFERENCE)
3. https://www.orangecountyai.com/blog/mcp2cli-one-cli-for-every-api-zero-wasted-tokens — Token benchmarks (HIGH)
4. https://github.com/rysweet/amplihack-agent-eval — Standalone eval package (MEDIUM)
5. https://code.claude.com/docs/en/sub-agents — Native subagent docs (HIGH)
6. https://code.claude.com/docs/en/agent-teams — Agent teams docs (HIGH)

---

## Sources Discovered During Cycle 2 (2026-03-20, agent architecture research)

### GitHub Repos — Agent Collections & Frameworks

| Status | Repo | URL | Stars | Priority | Discovered by |
|--------|------|-----|-------|----------|---------------|
| [x] | affaan-m/everything-claude-code | https://github.com/affaan-m/everything-claude-code | 78.8K | HIGH | research-everything-claude |
| [x] | wshobson/agents | https://github.com/wshobson/agents | 31.7K | HIGH | research-wshobson-agents |
| [x] | VoltAgent/awesome-claude-code-subagents | https://github.com/VoltAgent/awesome-claude-code-subagents | 14.4K | HIGH | research-agent-marketplaces |
| [~] | eyaltoledano/claude-task-master | https://github.com/eyaltoledano/claude-task-master | 25.9K | MEDIUM | research-awesomeclaude |
| [~] | SuperClaude-Org/SuperClaude_Framework | https://github.com/SuperClaude-Org/SuperClaude_Framework | 21.5K | MEDIUM | research-awesomeclaude |
| [~] | hesreallyhim/awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | 28.5K | MEDIUM | research-skills-inventory |
| [~] | travisvn/awesome-claude-skills | https://github.com/travisvn/awesome-claude-skills | 8.9K | MEDIUM | research-skills-inventory |
| [~] | BehiSecc/awesome-claude-skills | https://github.com/BehiSecc/awesome-claude-skills | 7.5K | LOW | research-skills-inventory |
| [~] | vijaythecoder/awesome-claude-agents | https://github.com/vijaythecoder/awesome-claude-agents | 4.0K | LOW | research-skills-inventory |

### Websites — Agent Directories

| Status | Site | URL | Notes |
|--------|------|-----|-------|
| [x] | awesomeclaude.ai | https://awesomeclaude.ai | Curated directory, NOT marketplace. 200+ tools cataloged. |
| [~] | skills.sh | https://skills.sh | 89K+ installs, main marketplace |
| [~] | SkillsMP | https://skillsmp.com | Agent Skills Marketplace |
| [~] | awesome-skills.com | https://awesome-skills.com | 125+ curated skills (ComposioHQ) |

### Anthropic Official — Monitoring & Telemetry

| Status | Source | URL | Notes |
|--------|--------|-----|-------|
| [x] | Claude Code monitoring docs | https://code.claude.com/docs/en/monitoring-usage | Full OTel reference, 8 metrics, 5 events |
| [x] | claude-code-monitoring-guide | https://github.com/anthropics/claude-code-monitoring-guide | Docker Compose stack: Prometheus + OTel + Grafana |
| [x] | Claude platform tool types | https://platform.claude.com/docs/en/docs/build-with-claude/tool-use | 11 tool types documented |

### LSP Integration

| Status | Source | URL | Notes |
|--------|--------|-----|-------|
| [x] | Piebald-AI/claude-code-lsps | https://github.com/Piebald-AI/claude-code-lsps | Production LSP marketplace with .lsp.json for 24+ languages. Use instead of claude-plugins-official stubs. |
| [x] | Claude Code LSP blog (Karan Bansal) | https://karanbansal.in/blog/claude-code-lsp/ | ENABLE_LSP_TOOL=1 env var discovery, setup guide, performance benchmarks (50ms vs 30-60s) |
| [x] | Claude Code plugins-reference LSP section | https://code.claude.com/docs/en/plugins-reference#lsp-servers | Official .lsp.json schema docs |

### Skill/Plugin Marketplaces (Comprehensive Inventory — 60+ sources)

**Deep Review:** See `docs/research/trail/findings/finding-all-skill-marketplaces.yaml` for complete inventory.

| Tier | Source | URL | Type | Size | Stars | Status |
|------|--------|-----|------|------|-------|--------|
| **1** | skills.sh (Vercel Labs) | https://github.com/vercel-labs/skills | Official CLI | Universal | 11.1K | [x] ACTIVE |
| **1** | awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | Curated list | Variable | 29.4K | [x] ACTIVE |
| **1** | claude-code-plugins-plus-skills | https://github.com/jeremylongshore/claude-code-plugins-plus-skills | Marketplace + CCPI | 1367 skills | 1.67K | [x] ACTIVE |
| **2** | skillkit | https://github.com/rohitg00/skillkit | Universal installer | 40+ tools | 617 | [x] ACTIVE |
| **2** | claude-skills-marketplace (Hattingpete) | https://github.com/mhattingpete/claude-skills-marketplace | Domain marketplace | SWE | 478 | [x] ACTIVE |
| **2** | gmickel-claude-marketplace | https://github.com/gmickel/gmickel-claude-marketplace | Specialized (Flow-Next) | 40+ | 547 | [x] ACTIVE |
| **2** | awesome-llm-skills | https://github.com/Prat011/awesome-llm-skills | Curated list | Variable | 1.02K | [x] ACTIVE |
| **2** | anthropics/skills | https://github.com/anthropics/skills | Official Anthropic | Variable | — | [x] ACTIVE |
| **2** | anthropics/life-sciences | https://github.com/anthropics/life-sciences | Official domain marketplace | Life Sci | 271 | [x] ACTIVE |
| **2** | skillfile | https://github.com/eljulians/skillfile | Installer + search | 110K+ | 79 | [x] ACTIVE |
| **2** | agent-skills-cli | https://github.com/Karanjot786/agent-skills-cli | Universal CLI | 40K+ | 58 | [x] ACTIVE |
| **2** | flins | https://github.com/powroom/flins | Universal installer | Multi | 34 | [x] ACTIVE |
| **3** | claudemarketplaces.com | https://github.com/mertbuilds/claudemarketplaces.com | Marketplace directory | 12+ | 72 | [x] ACTIVE |
| **3** | SkillX.sh | https://github.com/nextlevelbuilder/skillx | Marketplace + search | Variable | 36 | [x] ACTIVE |
| **3** | Dev-GOM/claude-code-marketplace | https://github.com/Dev-GOM/claude-code-marketplace | Marketplace | Multi | 77 | [x] ACTIVE |
| **3** | claude-emporium | https://github.com/Vvkmnn/claude-emporium | Marketplace (WIP) | — | 145 | [~] BUILDING |
| **3** | sap-skills | https://github.com/secondsky/sap-skills | Domain marketplace | 35 SAP | 155 | [x] ACTIVE |
| **3** | claude-code-elixir | https://github.com/georgeguimaraes/claude-code-elixir | Domain marketplace | Elixir | 130 | [x] ACTIVE |
| **3** | ai-coding-tools (Shopware) | https://github.com/shopwareLabs/ai-coding-tools | Domain marketplace | Shopware | 13 | [x] ACTIVE |
| **3** | dagster-io/skills | https://github.com/dagster-io/skills | Domain marketplace | Dagster | 87 | [x] ACTIVE |
| **3** | smalltalk-dev-plugin | https://github.com/mumez/smalltalk-dev-plugin | Domain marketplace | Smalltalk | 8 | [x] ACTIVE |
| **3** | cpython-skills | https://github.com/gpshead/cpython-skills | Domain marketplace | CPython | 12 | [x] ACTIVE |
| **3** | luxor-claude-marketplace | https://github.com/manutej/luxor-claude-marketplace | Professional marketplace | 140 tools | 44 | [x] ACTIVE |
| **3** | glincker/claude-code-marketplace | https://github.com/glincker/claude-code-marketplace | Community marketplace | 100+ APIs | 18 | [x] ACTIVE |
| **3** | awesome-claude-plugins | https://github.com/Chat2AnyLLM/awesome-claude-plugins | Curated list | Variable | 67 | [x] ACTIVE |
| **3** | cc-thingz | https://github.com/umputun/cc-thingz | General marketplace | Variable | 191 | [x] ACTIVE |
| **3** | audio-plugin-dev-skills | https://github.com/iPlug3/audio-plugin-dev-skills | Domain marketplace | Audio | 47 | [x] ACTIVE |
| **3** | devsforge/marketplace | https://github.com/devsforge/marketplace | Marketplace | Multi | 44 | [x] ACTIVE |
| **3** | skillsforge-marketplace | https://github.com/rawveg/skillsforge-marketplace | Marketplace | Multi | 27 | [x] ACTIVE |
| **3** | netresearch/claude-code-marketplace | https://github.com/netresearch/claude-code-marketplace | Curated marketplace | Variable | 23 | [x] ACTIVE |
| **3** | mwguerra/claude-code-plugins | https://github.com/mwguerra/claude-code-plugins | Marketplace | Multi | 23 | [x] ACTIVE |
| **3** | cc-skills | https://github.com/terrylica/cc-skills | Domain marketplace | DevOps/CH | 22 | [x] ACTIVE |
| **3** | artemnovichkov/skills | https://github.com/artemnovichkov/skills | Marketplace | Multi | 20 | [x] ACTIVE |
| **3** | swe-marketplace | https://github.com/andisab/swe-marketplace | Domain marketplace | SWE | 17 | [x] ACTIVE |
| **3** | awesome-design-skills | https://github.com/bergside/awesome-design-skills | Curated list | Design | 15 | [x] ACTIVE |
| **3** | notion-skills | https://github.com/tommy-ca/notion-skills | Domain marketplace | Notion | 14 | [x] ACTIVE |
| **3** | photon | https://github.com/portel-dev/photon | Intent framework | Multi | 14 | [x] ACTIVE |
| **3** | The-Focus-AI/claude-marketplace | https://github.com/The-Focus-AI/claude-marketplace | Integration marketplace | Multi | 10 | [x] ACTIVE |
| **3** | casper-marketplace | https://github.com/Casper-Studios/casper-marketplace | Marketplace | Multi | 10 | [x] ACTIVE |
| **3** | takahirom-claude-code-marketplace | https://github.com/takahirom/takahirom-claude-code-marketplace | Marketplace | Multi | 10 | [x] ACTIVE |
| **3** | vibekit-claude-plugins | https://github.com/shrwnsan/vibekit-claude-plugins | Domain marketplace | Productivity | 7 | [x] ACTIVE |
| **3** | lazyclaude | https://github.com/NikiforovAll/lazyclaude | TUI visualizer | Viz | 28 | [x] ACTIVE |
| **3** | plum | https://github.com/itsdevcoffee/plum | Multi-marketplace TUI | 750+ plugins | 11 | [x] ACTIVE |
| **4** | mcpbundler-agent-skills | https://github.com/eugenepyvovarov/mcpbundler-agent-skills-marketplace | Multi-tool marketplace | Variable | 10 | [x] ACTIVE |
| **4** | DiversioTeam/agent-skills-marketplace | https://github.com/DiversioTeam/agent-skills-marketplace | Decentralized marketplace | Variable | 2 | [x] ACTIVE |
| **4** | squidbay | https://github.com/squidbay/squidbay | Bitcoin Lightning marketplace | Variable | 2 | [x] EXPERIMENTAL |
| **5** | claude-code-registry | https://github.com/AnobleSCM/claude-code-registry | Community registry | Multi | 0 | [x] ACTIVE |
| **5** | claude-plugins-registry | https://github.com/biggora/claude-plugins-registry | CLI marketplace | Multi | 1 | [x] ACTIVE |
| **5** | awesome-rosetta-skills | https://github.com/xjtulyc/awesome-rosetta-skills | Curated list | Academic | 8 | [x] ACTIVE |
| **6** | adrianpuiu/claude-skills-marketplace | https://github.com/adrianpuiu/claude-skills-marketplace | Marketplace | Arch | 86 | [x] ACTIVE |
| **6** | openclaw-skills-marketplace | https://github.com/dvcrn/openclaw-skills-marketplace | Converted marketplace | OpenClaw | 2 | [x] ACTIVE |
| **6** | awesome-skills (vivy-yi) | https://github.com/vivy-yi/awesome-skills | Curated list | 230+ repos | — | [x] ACTIVE |
| **6** | awesome-agent-skills | https://github.com/megalor1/Awesome-Agent-Skills | Curated list | Variable | — | [x] ACTIVE |
| **6** | awesome-agent4edu | https://github.com/xdelin/awesome-agent4edu | Curated list | Education | — | [x] ACTIVE |
| **npm** | @teng-lin/agent-fetch | https://npm.im/@teng-lin/agent-fetch | Scraping tool | Web scraper | — | [x] ACTIVE |
| **npm** | @elizaos/plugin-agent-skills | https://npm.im/@elizaos/plugin-agent-skills | elizaOS plugin | Plugin | — | [x] ACTIVE |

**Additional 15+ personal/niche marketplaces** with <50 stars each (see full inventory for details)

### Open Standards

| Status | Standard | URL | Notes |
|--------|----------|-----|-------|
| [x] | Agent Skills (agentskills.io) | https://agentskills.io/specification | Adopted by 33+ tools including Claude Code |
| [~] | GitAgent | https://www.gitagent.sh | Git-native agent standard, export to Claude Code |
| [~] | JSON Agents | https://github.com/JSON-Agents/Standard | v1.0.0 Draft |
| [~] | Oracle Agent Spec | https://github.com/oracle/agent-spec | Framework-agnostic |

## Investigation Sources (2026-03-20)

### Plugin Configuration & Context Budget
- https://github.com/anthropic-ai/claude-code-sdk/blob/main/docs/settings-schema.md (enabledPlugins spec)
- Internal: .claude/settings.json (project plugin config)
- Internal: ~/.claude/settings.json (user plugin config, 79 enabled)
- Internal: migration spec Section 7.1 (plugin disable rationale)
- Internal: migration spec Section 10.1 (why claude-flow removed)
- Internal: docs/superpowers/specs/2026-03-20-native-claude-code-migration-design.md (full spec)

## LSP & IDE Integration Sources (2026-03-21)

| Status | Source | URL | Classification | In NB |
|--------|--------|-----|-----------------|-------|
| [x] | Reddit: Complete Guide V3 LSP + CLAUDE.md | https://www.reddit.com/r/ClaudeAI/comments/1qe239d/the_complete_guide_to_claude_code_v3_lsp_claudemd/ | Community guide, high-quality spec | No |
| [x] | tweakcc: Claude Code LSP Patcher | https://github.com/tweakcc/tweakcc | Patches Claude Code, customizes system prompts, enables LSP support | No |
| [x] | DevelopersIO: Local Marketplace LSP Setup | https://dev.classmethod.jp/en/articles/claude-code-lsp-from-local-marketplace/ | Step-by-step local marketplace configuration, marketplace.json structure, strict:false mode, file extension mapping | No |
| [x] | Reddit: Enable LSP in Claude Code (r/ClaudeCode) | https://www.reddit.com/r/ClaudeCode/comments/1rh5pcm/enable_lsp_in_claude_code_code_navigation_goes/ | 65+ upvote thread with LSP setup guide link, "0 LSP servers" root cause analysis (plugins disabled), performance verification (50ms vs 30-60s), plugin architecture gotchas | No |

## Skills.sh Marketplace Discovery (2026-03-21)

**Chezmoi Skills Marketplace Search Results**

| Status | Skill | URL | Installs | Category | Notes |
|--------|-------|-----|----------|----------|-------|
| [~] | terrylica/cc-skills@chezmoi-workflows | https://skills.sh/terrylica/cc-skills/chezmoi-workflows | 85 | chezmoi | HIGHEST ADOPTION — most-installed chezmoi skill, tested workflows |
| [~] | faintghost/skills@chezmoi-config | https://skills.sh/faintghost/skills/chezmoi-config | 28 | chezmoi | CURRENTLY INSTALLED in mde project |
| [~] | fonnesbeck/shay-mwa@chezmoi-chef | https://skills.sh/fonnesbeck/shay-mwa/chezmoi-chef | 26 | chezmoi | Chezmoi workflow patterns |
| [~] | gwenwindflower/.charmschool@chezmoi | https://skills.sh/gwenwindflower/.charmschool/chezmoi | 17 | chezmoi | Charm school educational approach |

**Mise Skills Marketplace Search Results**

| Status | Skill | URL | Installs | Category | Notes |
|--------|-------|-----|----------|----------|-------|
| [~] | terrylica/cc-skills@mise-tasks | https://skills.sh/terrylica/cc-skills/mise-tasks | 114 | mise | PEAK ADOPTION — same author as chezmoi-workflows |
| [~] | samhvw8/dotfiles@mise-expert | https://skills.sh/samhvw8/dotfiles/mise-expert | 98 | mise | High adoption, specialist expertise |
| [~] | terrylica/cc-skills@mise-configuration | https://skills.sh/terrylica/cc-skills/mise-configuration | 63 | mise | Project-level mise config |

**Dev Environment Skills Marketplace Search Results**

| Status | Skill | URL | Installs | Category | Notes |
|--------|-------|-----|----------|----------|-------|
| [~] | patricio0312rev/skills@dev-environment-bootstrapper | https://skills.sh/patricio0312rev/skills/dev-environment-bootstrapper | 36 | dev-env | Full environment setup orchestration |
| [~] | miles990/claude-software-skills@development-environment | https://skills.sh/miles990/claude-software-skills/development-environment | 18 | dev-env | General dev environment |
| [~] | panaversity/agentfactory@python-dev-environment | https://skills.sh/panaversity/agentfactory/python-dev-environment | 17 | dev-env | Python-specific environment |

**Homebrew Skills Marketplace Search Results**

| Status | Skill | URL | Installs | Category | Notes |
|--------|-------|-----|----------|----------|-------|
| [~] | bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance | https://skills.sh/bobmatnyc/claude-mpm-skills/homebrew-formula-maintenance | 84 | homebrew | High adoption formula management |
| [~] | connorads/dotfiles@homebrew-cask-authoring | https://skills.sh/connorads/dotfiles/homebrew-cask-authoring | 68 | homebrew | Cask and formula authoring |
| [~] | arustydev/ai@pkgmgr-homebrew-formula-dev | https://skills.sh/arustydev/ai/pkgmgr-homebrew-formula-dev | 14 | homebrew | Package manager formula development |

**Unified Platform: terrylica/cc-skills Ecosystem**

| Status | Plugin | URL | Focus | Notes |
|--------|--------|-----|-------|-------|
| [~] | dotfiles-tools | https://github.com/terrylica/cc-skills/tree/main/plugins/dotfiles-tools | Chezmoi automation | Natural language dotfile workflows |
| [~] | devops-tools | https://github.com/terrylica/cc-skills/tree/main/plugins/devops-tools | Doppler, MLOps, credentials | Devops automation suite |
| [~] | plugin-dev | https://github.com/terrylica/cc-skills/tree/main/plugins/plugin-dev | Skill architecture | Skill validation and audit |
| [~] | itp | https://github.com/terrylica/cc-skills/tree/main/plugins/itp | ADR-driven 4-phase dev | Implement-The-Plan workflow |
| [~] | gh-tools | https://github.com/terrylica/cc-skills/tree/main/plugins/gh-tools | GitHub automation | GFM link validation for PRs |

**GitHub Code Search (SKILL.md files) — Key Discoveries**

| Status | Source | File | Keywords | Notes |
|--------|--------|------|----------|-------|
| [x] | majiayu000/claude-skill-registry | skills/data/chezmoi/SKILL.md | chezmoi, dotfile-management | Official chezmoi expertise skill |
| [x] | rmullin7286/dotfiles | dot_claude/skills/chezmoi-sync/SKILL.md | chezmoi-sync, re-add, git | Dotfiles sync patterns |
| [x] | terrylica/cc-skills | plugins/dotfiles-tools/skills/chezmoi-sync/SKILL.md | chezmoi sync, drift check, guard | Interactive chezmoi drift detection |
| [x] | ssiumha/dots | prompts/skills/mise-config/SKILL.md | mise.toml, project-config | Project-level mise configuration |
| [x] | btuckerc/boilerplate | home/dot_config/opencode/skills/install-tools/SKILL.md | chezmoi + mise coordination | Integrated setup workflow |

**Finishing-a-Development-Branch Skill Verification**

| Status | Skill | URL | Installs | Location |
|--------|-------|-----|----------|----------|
| [x] | obra/superpowers@finishing-a-development-branch | https://skills.sh/obra/superpowers/finishing-a-development-branch | 19K | PRIMARY (referenced in .claude/rules/worktree-pr-workflow.md) |

**Alternative Ecosystem: Nix-based Configuration**

| Status | Skill | URL | Installs | Notes |
|--------|-------|-----|----------|-------|
| [~] | 0xbigboss/claude-code@nix-best-practices | https://skills.sh/0xbigboss/claude-code/nix-best-practices | 181 | NixOS alternative (NOT recommended for current project) |
| [~] | greenheadhq/nixos-config@managing-macos | https://skills.sh/greenheadhq/nixos-config/managing-macos | 10 | Nix on macOS (NOT recommended for current project) |

---

## Skills & Plugin Management CLIs (2026-03-20, plugin-marketplace research)

### Official Claude Code Plugin System

| Status | Component | URL | Type | Notes |
|--------|-----------|-----|------|-------|
| [x] | Claude Code plugin command | N/A (built-in) | CLI | `claude plugins install/enable/disable/marketplace add/update` |
| [x] | Marketplace schema | https://anthropic.com/claude-code/marketplace.schema.json | Schema | Official marketplace.json validator |
| [x] | Anthropic official plugins | https://github.com/anthropics/claude-plugins-official | GitHub | Pre-configured marketplace, OTel + tool integrations |

### Specialized Skill/Plugin CLI Tools (14 discovered, Feb-Mar 2026)

| Status | Tool | URL | Latest | Purpose | Source |
|--------|------|-----|--------|---------|--------|
| [x] | @spardutti/claude-skills | https://www.npmjs.com/package/@spardutti/claude-skills | v1.10.0 (Mar 2026) | Interactive skill installer | npm |
| [x] | @agent-nexus/csreg | https://www.npmjs.com/package/@agent-nexus/csreg | v0.1.16 (Feb 2026) | Claude Skills Registry CLI (publish, search, pull) | npm |
| [x] | @mammals-at-work/yacs | https://www.npmjs.com/package/@mammals-at-work/yacs | v0.10.0 (Mar 2026) | Yet Another Claude Skills installer, multi-CLI support | npm |
| [x] | vibeindex | https://www.npmjs.com/package/vibeindex | v0.1.1 (Mar 2026) | Install Claude Code skills from GitHub repos | npm |
| [x] | @talisikai/claude-skills | https://www.npmjs.com/package/@talisikai/claude-skills | v1.2.0 (Mar 2026) | Talisikai-branded skill installer | npm |
| [x] | @dayinxisheng/skillctl | https://www.npmjs.com/package/@dayinxisheng/skillctl | v1.1.1 (Mar 2026) | Skill activation & project archive management | npm |
| [x] | @lavelle/lint-agent | https://www.npmjs.com/package/@lavelle/lint-agent | v0.0.8 (Feb 2026) | Linter for .claude/skills/ (filenames, frontmatter) | npm |
| [x] | mcp-to-skill-with-headers | https://www.npmjs.com/package/mcp-to-skill-with-headers | v0.2.2 (Mar 2026) | Convert MCP servers to Claude Skills | npm |
| [x] | claude-skills | https://www.npmjs.com/package/claude-skills | v1.0.2 (Dec 2025) | Claude Code skills collection | npm |
| [x] | claude-skills-frontend | https://www.npmjs.com/package/claude-skills-frontend | v1.4.0 (Feb 2026) | Frontend-focused skills + MCP auto-config | npm |
| [x] | @vibe-agent-toolkit/runtime-claude-skills | https://www.npmjs.com/package/@vibe-agent-toolkit/runtime-claude-skills | v0.1.3 (Feb 2026) | VAT-to-Claude Skills runtime | npm |
| [x] | @loom-node/skills | https://www.npmjs.com/package/@loom-node/skills | v0.1.16 (Mar 2026) | Progressive disclosure architecture for skills | npm |
| [x] | skillshub | https://github.com/ComeOnOliver/skillshub | — | Agent Skills Registry, 5,000+ skills from 500+ repos | GitHub |
| [x] | agent-skills (tech-leads-club) | https://github.com/tech-leads-club/agent-skills | — | Secure, validated skill registry for Claude Code/Cursor/Copilot | GitHub |

### Marketplace Discovery & Aggregation Repos

| Status | Repo | URL | Stars | Purpose |
|--------|------|-----|-------|---------|
| [x] | Kamalnrf/claude-plugins | https://github.com/Kamalnrf/claude-plugins | 482 | Lightweight registry to discover/install Claude plugins |
| [x] | ComposioHQ/awesome-claude-skills | https://github.com/ComposioHQ/awesome-claude-skills | 46,445 | Largest awesome-list for Claude skills |
| [x] | hesreallyhim/awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | 29,439 | Curated awesome-list for Claude Code |
| [x] | VoltAgent/awesome-claude-code-subagents | https://github.com/VoltAgent/awesome-claude-code-subagents | 14,555 | Subagent-focused awesome-list |
| [x] | travisvn/awesome-claude-skills | https://github.com/travisvn/awesome-claude-skills | 9,353 | Curated skills catalog |

### Pre-Configured Marketplaces

| Status | Marketplace | Location | Owner | Plugins | Version |
|--------|-----------|----------|-------|---------|---------|
| [x] | claude-code-workflows | ~/.claude/plugins/marketplaces/claude-code-workflows/ | Seth Hobson (wshobson) | 72 | v1.5.6 |
| [x] | claude-plugins-official | ~/.claude/plugins/marketplaces/claude-plugins-official/ | Anthropic | 500+ | Latest |
| [x] | docker | ~/.claude/plugins/marketplaces/docker/ | Docker Inc. | 2 (MCP Toolkit + Beta) | v1.0.0 |

### Official Anthropic Standards & References

| Status | Source | URL | Type | Relevance |
|--------|--------|-----|------|-----------|
| [x] | Agent Skills standard | https://agentskills.io/specification | Open Standard | Adopted by 33+ tools including Claude Code |
| [x] | Claude Code plugins-reference | https://code.claude.com/docs/en/plugins-reference | Docs | .lsp.json schema, plugin lifecycle |
| [x] | Claude Code monitoring docs | https://code.claude.com/docs/en/monitoring-usage | Docs | OTel events for plugin installation/enable/disable |

---

## Non-Obvious Skill Sources: Tier-1 Comprehensive Collections (2026-03-21)

**Research Phase:** Systematic GitHub topic search + skills.sh marketplace discovery
**Method:** `gh search repos --topic claude-code-*`, marketplace rankings, SKILL.md pattern analysis
**Result:** 45+ new high-value sources identified across 3 distribution tiers

### TIER-1: Comprehensive Ecosystem Repos (10K+ stars, aggregators of 1000s of skills)

| Status | Repo | URL | Stars | Type | Description | New? |
|--------|------|-----|-------|------|-------------|------|
| [ ] | affaan-m/everything-claude-code | https://github.com/affaan-m/everything-claude-code | 90.8K | Awesome | Agent harness optimization: skills, instincts, memory, security, research-first dev | YES |
| [ ] | anthropics/skills | https://github.com/anthropics/skills | 98.6K | Official | OFFICIAL Anthropic agent skills registry (public, open-source) | — |
| [ ] | wshobson/agents | https://github.com/wshobson/agents | 31.8K | Awesome | Multi-agent orchestration for Claude Code | YES |
| [ ] | ComposioHQ/awesome-claude-skills | https://github.com/ComposioHQ/awesome-claude-skills | 46.4K | Awesome | Curated awesome list, highest adoption in Tier-1 | YES |
| [ ] | hesreallyhim/awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | 29.4K | Awesome | Comprehensive: skills, hooks, commands, orchestrators, plugins | YES |
| [ ] | sickn33/antigravity-awesome-skills | https://github.com/sickn33/antigravity-awesome-skills | 26.2K | Awesome | 1,273+ agentic skills, installer CLI, bundles, multi-platform (Claude Code + Cursor + Codex + Gemini CLI) | YES |
| [ ] | VoltAgent/awesome-openclaw-skills | https://github.com/VoltAgent/awesome-openclaw-skills | 40.1K | Awesome | 5,400+ OpenClaw skills (cross-platform foundation) | YES |
| [ ] | VoltAgent/awesome-agent-skills | https://github.com/VoltAgent/awesome-agent-skills | 12.1K | Awesome | 500+ agent skills from official dev teams and community | YES |
| [ ] | VoltAgent/awesome-claude-code-subagents | https://github.com/VoltAgent/awesome-claude-code-subagents | 14.4K | Awesome | Subagent-specific collection | YES |

### TIER-2: Specialized Collections (3K-12K stars, domain/framework/platform focus)

#### Domain & Role-Specific (PM, Marketing, Engineering, Finance)

| Status | Repo | URL | Stars | Focus | New? |
|--------|------|-----|-------|-------|------|
| [ ] | phuryn/pm-skills | https://github.com/phuryn/pm-skills | 7.8K | Product/Marketing (100+ skills: discovery, strategy, execution, launch, growth) | YES |
| [ ] | alirezarezvani/claude-skills | https://github.com/alirezarezvani/claude-skills | 6.1K | Multi-domain (192+ skills: engineering, marketing, product, compliance, C-level advisory) | YES |
| [ ] | travisvn/awesome-claude-skills | https://github.com/travisvn/awesome-claude-skills | 8.9K | Curated skills inventory | YES |
| [ ] | BehiSecc/awesome-claude-skills | https://github.com/BehiSecc/awesome-claude-skills | 7.5K | Curated skills inventory | YES |
| [ ] | vijaythecoder/awesome-claude-agents | https://github.com/vijaythecoder/awesome-claude-agents | 4.0K | Agent-focused collection | YES |

#### Language/Framework-Specific (iOS, Java, Python, etc.)

| Status | Repo | URL | Stars | Focus | New? |
|--------|------|-----|-------|-------|------|
| [ ] | keskinonur/claude-code-ios-dev-guide | https://github.com/keskinonur/claude-code-ios-dev-guide | 488 | Swift/SwiftUI iOS (PRD-driven, extended thinking, planning modes) | YES |
| [ ] | jabrena/cursor-rules-java | https://github.com/jabrena/cursor-rules-java | 329 | Java enterprise patterns (cross-platform: Cursor, Claude Code) | YES |
| [ ] | decebals/claude-code-java | https://github.com/decebals/claude-code-java | 417 | Java development infrastructure | YES |

#### Architecture & Infrastructure

| Status | Repo | URL | Stars | Focus | New? |
|--------|------|-----|-------|-------|------|
| [ ] | athola/claude-night-market | https://github.com/athola/claude-night-market | 221 | 17 production-ready plugins: git workflows, code review, spec-driven dev, architecture patterns, resource optimization | YES |
| [ ] | parcadei/Continuous-Claude-v3 | https://github.com/parcadei/Continuous-Claude-v3 | 3.6K | Context management via hooks, MCP execution without context pollution | YES |
| [ ] | zebbern/claude-code-guide | https://github.com/zebbern/claude-code-guide | 3.7K | Setup, commands, workflows, agents, skills, tips-n-tricks (beginner to power user) | YES |
| [ ] | KhazP/vibe-coding-prompt-template | https://github.com/KhazP/vibe-coding-prompt-template | 2.0K | PRD/Tech Design/MVP generation templates | YES |
| [ ] | NikiforovAll/claude-code-rules | https://github.com/NikiforovAll/claude-code-rules | 104 | Practical enhancement techniques | YES |

#### Specialized/Niche Use Cases

| Status | Repo | URL | Stars | Focus | New? |
|--------|------|-----|-------|-------|------|
| [ ] | a5c-ai/babysitter | https://github.com/a5c-ai/babysitter | 482 | Task complexity enforcement, hallucination-free orchestration for complex workflows | YES |
| [ ] | ljagiello/ctf-skills | https://github.com/ljagiello/ctf-skills | 469 | CTF challenge solutions (web exploitation, binary pwn, crypto, reverse eng, forensics, OSINT) | YES |
| [ ] | opslane/verify | https://github.com/opslane/verify | 90 | Production verification layer for Claude Code | YES |
| [ ] | ivan-magda/claude-code-plugin-template | https://github.com/ivan-magda/claude-code-plugin-template | 44 | Plugin marketplace scaffolding (ready-to-use toolkit for teams) | YES |

### TIER-3: Personal Ecosystem (skills.sh top performers by install count)

#### High-Adoption Skills (100+ installs — Framework-Specific)

| Status | Skill | URL | Installs | Category | Author | Pattern | New? |
|--------|-------|-----|----------|----------|--------|---------|------|
| [ ] | terrylica/cc-skills@mise-tasks | https://skills.sh/terrylica/cc-skills/mise-tasks | 114 | mise | terrylica (NEXUS) | Multi-plugin ecosystem | YES |
| [ ] | 0xbigboss/claude-code@nix-best-practices | https://skills.sh/0xbigboss/claude-code/nix-best-practices | 181 | nixos | 0xbigboss | NixOS alternative | YES |
| [ ] | samhvw8/dotfiles@mise-expert | https://skills.sh/samhvw8/dotfiles/mise-expert | 98 | mise | samhvw8 | Specialist expertise | YES |
| [ ] | bobmatnyc/claude-mpm-skills@homebrew-formula-maintenance | https://skills.sh/bobmatnyc/claude-mpm-skills/homebrew-formula-maintenance | 84 | homebrew | bobmatnyc | Formula management | YES |
| [ ] | terrylica/cc-skills@chezmoi-workflows | https://skills.sh/terrylica/cc-skills/chezmoi-workflows | 85 | chezmoi | terrylica (NEXUS) | Workflow patterns | YES |
| [ ] | connorads/dotfiles@homebrew-cask-authoring | https://skills.sh/connorads/dotfiles/homebrew-cask-authoring | 68 | homebrew | connorads | Cask + formula authoring | YES |
| [ ] | terrylica/cc-skills@mise-configuration | https://skills.sh/terrylica/cc-skills/mise-configuration | 63 | mise | terrylica (NEXUS) | Project-level config | YES |

#### NEXUS ECOSYSTEM: terrylica/cc-skills (Multi-Plugin Platform)

| Status | Plugin | URL | Focus | Installs (est.) |
|--------|--------|-----|-------|-----------------|
| [ ] | mise-tasks | https://skills.sh/terrylica/cc-skills/mise-tasks | mise automation | 114 |
| [ ] | chezmoi-workflows | https://skills.sh/terrylica/cc-skills/chezmoi-workflows | chezmoi drift management | 85 |
| [ ] | mise-configuration | https://skills.sh/terrylica/cc-skills/mise-configuration | Project-level mise | 63 |
| [ ] | dotfiles-tools (GitHub) | https://github.com/terrylica/cc-skills/tree/main/plugins/dotfiles-tools | Natural language dotfile workflows | — |
| [ ] | devops-tools (GitHub) | https://github.com/terrylica/cc-skills/tree/main/plugins/devops-tools | Doppler, MLOps, credentials automation | — |
| [ ] | plugin-dev (GitHub) | https://github.com/terrylica/cc-skills/tree/main/plugins/plugin-dev | Skill validation and audit | — |
| [ ] | itp (GitHub) | https://github.com/terrylica/cc-skills/tree/main/plugins/itp | ADR-driven 4-phase dev (Implement-The-Plan) | — |
| [ ] | gh-tools (GitHub) | https://github.com/terrylica/cc-skills/tree/main/plugins/gh-tools | GitHub automation (GFM link validation) | — |

**Strategic Value:** terrylica is a "nexus author"—monitor all repos and plugins for emerging patterns.

### TIER-3B: SKILL.md Pattern Discovery (Personal Dotfiles Repos)

GitHub code search reveals 45+ personal dotfiles repos encoding framework expertise in SKILL.md files (undocumented patterns):

| Status | Source | File | Skill Pattern | Framework | Notes |
|--------|--------|------|----------------|-----------|-------|
| [x] | majiayu000/claude-skill-registry | skills/data/chezmoi/SKILL.md | chezmoi-management | chezmoi | Official expertise skill |
| [x] | rmullin7286/dotfiles | dot_claude/skills/chezmoi-sync/SKILL.md | chezmoi-sync, re-add, git | chezmoi | Dotfiles sync patterns |
| [x] | terrylica/cc-skills | plugins/dotfiles-tools/skills/chezmoi-sync/SKILL.md | chezmoi sync, drift check, guard | chezmoi (NEXUS) | Interactive drift detection |
| [x] | ssiumha/dots | prompts/skills/mise-config/SKILL.md | mise.toml, project-config | mise | Project-level mise configuration |
| [x] | btuckerc/boilerplate | home/dot_config/opencode/skills/install-tools/SKILL.md | chezmoi + mise coordination | multi | Integrated setup workflow |

---

## PHASE B: SkillsMP Marketplace Analysis (2026-03-21)

### Primary Source: SkillsMP.com

| Source | URL | Status | Details |
|--------|-----|--------|---------|
| Official Website | https://skillsmp.com | [x] BLOCKED | Cloudflare JS challenge - use API instead |
| API v1 Base | https://skillsmp.com/api/v1 | [x] CONFIRMED | Requires API key; supports keyword + semantic search |
| Official GitHub Repo | https://github.com/yan-labs/skillsmp | [x] REVIEWED | Minimal (v0.0.1, "Coming Soon" in code) - npm package placeholder |

### SkillsMP Size & Aggregation

| Platform | Total Skills | Source | Last Updated |
|----------|-------------|--------|--------------|
| SkillsMP | ~161K | skilldb aggregation | 2026-02-27 |
| skills.sh | ~22K | skilldb aggregation | 2026-02-27 |
| ClawHub | ~11K | skilldb aggregation | 2026-02-27 |
| **Total Deduplicated** | **~180K+** | AmazingAng/skilldb | 2026-02-27 |

**Key Finding:** SkillsMP is 7-8x larger than competitors; contains bulk of AI agent skills ecosystem.

### MCP Server Implementations (Bridges)

| Repo | Stars | Package | Latest Version | Status | Focus |
|------|-------|---------|-----------------|--------|-------|
| anilcancakir/skillsmp-mcp-server | 3 | skillsmp-mcp-server | 1.0.0 | Stable | Full-featured; supports Claude Code, Cursor, Copilot, Antigravity |
| boyonglin/skillsmp-mcp-lite | 0 | skillsmp-mcp-lite | 2.4.1 | Active | Lightweight; added Cisco Skill Scanner; auto-setup |
| luckybalabalaya/skillsmp-mcp-server | — | @luckybalabalaya/skillsmp-mcp-server | 1.6.4 | Latest | Intelligent tiering + auto-discovery |
| kefjbo/skillsmp-mcp | — | @kefjbo/skillsmp-mcp | 0.1.0 | Active | Minimal wrapper |
| clancylllin/skillsmp-mcp-lite | — | skillsmp-mcp-lite | 2.4.1 | Latest | Official maintainer (via GitHub Actions) |

### CLI Tools for SkillsMP

| Repo | Stars | Package | Latest | Description |
|------|-------|---------|--------|-------------|
| Karanjot786/agent-skills-cli | 58 | agent-skills-cli | Latest | Universal CLI; accesses 40K+ skills from SkillsMP + others |
| tarangchokshi/claude-skills-cli | — | @tarangchokshi/claude-skills-cli | 1.1.0 | Install agent skills from SkillsMP; targets Claude Code, Cursor, Codex, Windsurf |
| yan-labs/skillsmp | 7 | skillsmp | 0.0.1 | Official npm package (placeholder) |

### SkillsMP API Features (Confirmed via MCP Implementations)

#### Search Tools
- **skillsmp_search**: Keyword search with pagination, sorting (stars/recent)
- **skillsmp_ai_search**: Semantic search via Cloudflare AI

#### Content & Installation
- **skillsmp_get_skill_content**: Fetch skill files from GitHub via REST (no `git clone`)
- **skillsmp_list_repo_skills**: List skills in a repository
- **skillsmp_install_skill**: Install skills to agents

#### Security
- **skillsmp_read_skill**: With optional Cisco Skill Scanner (three-layer limits: 100 files, 500KB/file, 5MB total)

### Integration Points with Our Stack

**Potential Gaps vs. Our Solutions:**
| Need | SkillsMP | skills.sh | Our Status |
|------|----------|-----------|-----------|
| chezmoi skills | Likely exists | Likely exists | Need to catalog |
| mise integration | Likely exists | Likely exists | Need to catalog |
| dotfiles workflows | Very likely | Likely | Need to catalog |
| LSP setup | Unknown | Unknown | Candidate for new skill? |
| Python dev setup | Unknown | Unknown | Candidate for new skill? |

### Data Location & Access Methods

- **Full Skilldb**: 160MB Git LFS file at https://github.com/AmazingAng/skilldb/blob/main/skilldb.json (deduplicated, 180K+ skills)
- **API Access**: https://skillsmp.com/api/v1 (requires API key from skillsmp.com/docs/api)
- **MCP Servers**: Multiple npm packages for one-command integration

### Next Steps for Integration

1. Get SkillsMP API key from https://skillsmp.com/docs/api
2. Test skillsmp-mcp-lite (`npx skillsmp-mcp-lite --setup` for auto-config)
3. Query for chezmoi, mise, dotfiles, LSP skills
4. Consider publishing new skills if gaps found (publication method TBD)
5. Monitor skilldb updates for competitor intel (skillsh.com, clawhub.ai)

---
