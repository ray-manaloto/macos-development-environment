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

## GitHub Repos — Reference Dotfiles

| Status | Repo | URL | Verdict | In NB |
|--------|------|-----|---------|-------|
| [~] | martinemde/dotfiles | https://github.com/martinemde/dotfiles | REFERENCE — AI-first dotfiles w/ chezmoi | Yes |

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
