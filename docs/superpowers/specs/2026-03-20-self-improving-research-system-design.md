# Self-Improving Research System — Design Spec

**Created:** 2026-03-20
**Status:** Draft
**Scope:** Autonomous research, knowledge synthesis, and self-improvement loop for macos-development-environment

---

## 1. Problem Statement

The macos-development-environment project has significant infrastructure (mise, chezmoi, claude-flow hooks, AI research skills, autoresearch teams) but suffers from:

1. **Institutional memory loss** — agents discover things, fix things, have ideas, then context evaporates between sessions
2. **Tool underutilization** — chezmoi/mise/dotfiles setup not fully leveraging how tools should work together
3. **Stale configurations** — mise lockfiles for wrong CPU architectures, duplicate installs between brew/node/bun/gem/rust not managed by chezmoi/mise
4. **Non-reproducibility** — chezmoi project likely not reproducible on a clean machine
5. **Missing automation** — devcontainer not set up, GitHub automation not happening
6. **Agent drift** — skills not triggered properly, agent/subagent descriptions incorrect, superpowers workflow not followed
7. **No improvement measurement** — no way to quantify if the project is getting better over time
8. **Research without continuity** — no tracking of what was researched, when, on what tool versions, or what was applied

## 2. Goals

- Build a **self-improving system** where autonomous agents research, synthesize, and apply improvements
- **Full autonomy with guardrails** — agents can make any change but must validate before/after and create revertible commits
- **Quantify "better"** with a measurable improvement score that trends over time
- **Storage-agnostic tracking** — don't commit to GitHub Issues vs Obsidian vs something else; use an adapter
- The **agent orchestrator itself evolves** — the system discovers better agents, tools, and techniques and applies them
- Run on-demand and on a schedule via `/loop`

## 3. Architecture

### 3.1 Four-Layer System

```
┌─────────────────────────────────────────────────────┐
│  META LAYER — Agent Evolution Engine                │
│  Discovers better orchestration patterns,           │
│  creates/retires/improves agents & skills           │
├─────────────────────────────────────────────────────┤
│  LAYER 3 — Self-Improvement Engine                  │
│  Applies changes, validates, measures "better"      │
├─────────────────────────────────────────────────────┤
│  LAYER 2 — Knowledge Synthesis                      │
│  NotebookLM notebooks, gap analysis, consolidation  │
├─────────────────────────────────────────────────────┤
│  LAYER 1 — Research Agents                          │
│  YouTube, Reddit, X, GitHub, Docs crawlers          │
└─────────────────────────────────────────────────────┘
```

- **Layer 1** discovers information from external sources
- **Layer 2** synthesizes findings into actionable knowledge with confidence scoring
- **Layer 3** applies confirmed improvements with validation gates
- **Meta Layer** evolves the agents, skills, and orchestration itself

### 3.2 Core Abstractions

#### Agent Registry (mutable, versioned)

Every agent has: name, purpose, trigger conditions, performance metrics, version, creation date. The registry lives in a config file so agents can edit it.

```yaml
# configs/agent-registry.yaml
version: 3
last_updated: "2026-03-20"
agents:
  youtube-researcher:
    purpose: "Monitor YouTube channels for tutorials on chezmoi/mise/Claude Code/Obsidian"
    type: research
    sources: [youtube]
    schedule: daily
    performance:
      findings_per_run: null
      actionable_rate: null
      last_run: null
    status: new
    created: "2026-03-20"
    version: 1
```

#### Trail Adapter (pluggable storage)

Interface: `record_finding()`, `record_action()`, `query_trail()`, `get_metrics()`

- **Initial backend:** markdown files in `docs/research/trail/`
- **Swappable to:** GitHub Issues, Obsidian vault, database, Linear, whatever research reveals
- Every record includes: timestamp, source, tool versions, agent that produced it

#### Provenance Record

Every finding and action gets a provenance record:

```yaml
id: "finding-2026-03-20-001"
timestamp: "2026-03-20T14:30:00Z"
source: "https://www.youtube.com/watch?v=..."
tool_versions:
  claude_code: "1.0.34"
  mise: "2025.3.8"
  chezmoi: "2.58.0"
agent: "youtube-researcher"
finding_type: technique  # technique | tool | config_change | architecture | metric
status: discovered       # discovered | synthesized | applied | reverted | superseded
confidence: confirmed    # confirmed | probable | speculative
evidence: "Video demonstrates mise aqua backend for Ruby, replacing ruby-build"
```

#### Improvement Score

Weighted composite (0–1) calculated per cycle:

```
score = (
  validation_pass_rate * 0.20 +
  (1 - brew_mise_duplicates/total_tools) * 0.15 +
  chezmoi_reproducible * 0.15 +
  test_coverage * 0.10 +
  (1 - lint_violations/100) * 0.05 +
  (1 - stale_sources/total_sources) * 0.10 +
  findings_actionable_rate * 0.10 +
  agent_trigger_accuracy * 0.10 +
  (1 - token_cost_normalized) * 0.05
)
```

Weights and metrics are configurable and themselves evolve via research.

## 4. Layer 1 — Research Pipeline

### 4.1 Source Categories

| Category | Sources | Agent Behavior | Frequency |
|----------|---------|----------------|-----------|
| YouTube Channels | 14 known channels + discovered ones | Monitor for new uploads, transcribe via yt-dlp, add to NotebookLM | Daily/on-demand |
| Official Docs | chezmoi, mise, Claude Code (code.claude.com + SDK + plugins + cookbooks), Obsidian, Anthropic engineering blog | Crawl every page, diff against last crawl, flag changes | Weekly + on version bump |
| Claude Code Releases | anthropics/claude-code, claude-agent-sdk-python, claude-plugins-official, claude.com/blog | Detect version bumps, new features, breaking changes, new skills/plugins | On release |
| Reddit | r/chezmoi, r/dotfiles, r/ObsidianMD, r/ClaudeAI, r/LocalLLaMA | Scan hot/new posts, extract actionable patterns | Daily |
| X/Twitter | Key accounts + hashtags | Monitor for tool announcements, technique shares | Daily |
| GitHub | Awesome lists, trending repos, specific reference repos | Star count trends, new repos, README analysis | Daily |
| Tool Releases | Claude Code changelog, mise releases, chezmoi releases | Detect version bumps, extract breaking changes + new features | On release |

#### Known YouTube Channels

- @GithubAwesome
- @ArtemXTech
- @intheworldofai
- @indydevdan
- @betterstack
- @Chase-H-AI
- @ManuAGI
- @ColeMedin
- @AILABS-393
- @owainlewis
- @GregIsenberg

#### Official Anthropic/Claude Code Sources (Exhaustive Coverage)

These are foundational — every page should be crawled and diffed on each Claude Code release:

- https://code.claude.com/docs/en/overview — Claude Code official documentation (all pages)
- https://github.com/anthropics/claude-code — Claude Code source/issues/releases
- https://github.com/anthropics/claude-agent-sdk-python — Agent SDK for building custom agents
- https://github.com/anthropics/claude-plugins-official — Official plugin repository
- https://github.com/anthropics/claude-cookbooks — Anthropic cookbooks and examples
- https://github.com/anthropics/skills — Official skills repository
- https://claude.com/blog — Claude blog (product announcements, capabilities)
- https://www.anthropic.com/engineering — Anthropic engineering blog (technical deep-dives)
- https://platform.claude.com/cookbook/ — Platform cookbook recipes

#### Known Reference Repos

- martinemde/dotfiles
- ArtemXTech/personal-os-skills
- ComposioHQ/agent-orchestrator
- wanshuiyin/Auto-claude-code-research-in-sleep
- ruvnet/claude-flow, ruflo, RuView, RuVector, agentic-flow

### 4.2 Research Cycle

```
1. TRIGGER (schedule or on-demand)
2. SPAWN research agents per category (parallel)
   Each agent:
   ├─ Searches its sources
   ├─ Filters for relevance (keywords, recency, engagement)
   ├─ Creates a Provenance Record per finding
   └─ Adds high-value sources to NotebookLM notebook
3. COLLECT all Provenance Records
4. DEDUPLICATE across agents (same URL found by Reddit + YouTube)
5. PASS to Layer 2 for synthesis
```

### 4.3 Version Tracking

Every research cycle stamps tool versions:

```yaml
cycle_id: "2026-03-20-001"
tool_versions:
  claude_code: "1.0.34"
  mise: "2025.3.8"
  chezmoi: "2.58.0"
  obsidian: "1.8.9"
  notebooklm_cli: "0.3.4"
  python: "3.14.0"
agent_versions:
  registry_hash: "sha256:abc..."
```

## 5. Layer 2 — Knowledge Synthesis

### 5.1 NotebookLM Notebook Strategy

Theme-based notebooks that split when approaching capacity:

| Notebook | Purpose | Source Types |
|----------|---------|-------------|
| Research Stack (existing) | Claude Code + Obsidian + NotebookLM integration | YouTube, blogs, GitHub repos |
| Dotfiles & Dev Env | chezmoi, mise, shell config, reproducibility | Docs, tutorials, reference repos |
| Agent Orchestration | Multi-agent patterns, self-improvement, MCP | Framework repos, papers, tutorials |
| Tool Updates | Version-specific changelogs, breaking changes | Release notes, GitHub releases |
| Community Intel | Reddit/X/HN discussions, trending repos | Social sources |

#### Source Limit Configuration

```yaml
# configs/research-config.yaml
notebooklm:
  source_limit: 50           # configurable per plan tier
  split_threshold: 0.8       # create new notebook at 80% capacity
  naming_convention: "{theme}-{date}"
  plan_tier: "standard"      # standard|plus|pro|ultra
```

When a notebook reaches `split_threshold * source_limit`, the system creates a continuation notebook. Cross-notebook queries use NotebookLM's `cross_notebook_query` MCP tool.

### 5.2 Synthesis Cycle

```
1. Research agents add sources to appropriate notebook(s)
2. Query each notebook: "What's new since last cycle?
   What contradicts existing knowledge? What gaps remain?"
3. CONFIDENCE CHECK
   Score each finding: confirmed | probable | speculative
   - confirmed → proceeds to Layer 3 automatically
   - probable → flagged for human review
   - speculative → stays in notebook for future validation
4. GAP ANALYSIS
   Compare findings against current project state:
   - What does research say we should have?
   - What do we actually have?
   - Delta = improvement backlog
5. COMPOUND STEP
   Extract learnings into structured format:
   - Pattern name, when to apply, evidence, confidence
   - Store in docs/knowledge/ (human-inspectable)
   - Also index in memory system (agent-searchable)
6. PASS confirmed improvements to Layer 3
```

### 5.3 Cross-Model Adversarial Review

For high-stakes synthesis (architecture changes, tool migrations):

- Agent A produces a recommendation
- Agent B (different model or different prompt) critiques it
- Only recommendations that survive critique proceed

Prevents the self-play quality ceiling where a single model validates its own bad ideas. Adopted from ARIS (Auto-claude-code-research-in-sleep) pattern.

### 5.4 Source Staleness Detection

```yaml
source_health:
  url: "https://github.com/chezmoi/chezmoi"
  notebook_id: "abc-123"
  added_date: "2026-03-20"
  last_verified: "2026-03-20"
  source_type: github_repo
  staleness_rules:
    github_repo: 30 days
    youtube: 90 days
    docs: 14 days
    reddit: 7 days
    blog: 60 days
  status: fresh  # fresh | stale | expired | replaced
```

Staleness cycle (runs as part of `/loop 7d full-audit`):

1. For each source in each notebook, check if source has changed since `last_verified`
2. GitHub repos: check latest commit/release date
3. Docs pages: fetch and diff against cached version
4. YouTube channels: check for new videos on same topic
5. Stale sources get flagged → agent decides: refresh, replace, or archive
6. Expired sources (>2x staleness threshold) get removed and replaced

### 5.5 NotebookLM ↔ Obsidian Bidirectional Sync

```
NotebookLM notebooks          Obsidian vault
┌──────────────────┐          ┌──────────────────┐
│ Research Stack   │◄────────►│ 03-Resources/    │
│ Dotfiles & Dev   │  sync    │   NotebookLM/    │
│ Agent Orch.      │  layer   │     indexes/     │
│ Tool Updates     │          │     findings/    │
│ Community Intel  │          │     stale/       │
└──────────────────┘          └──────────────────┘
```

The sync layer tracks: which notebook has which sources, when each was added, source freshness, and cross-notebook links.

## 6. Layer 3 — Self-Improvement Engine

### 6.1 Improvement Cycle

```
FINDING arrives from Layer 2 (confidence: confirmed)

1. CLASSIFY the improvement type:
   ├─ config_change (.mise.toml, chezmoi, Brewfile)
   ├─ code_change (src/mde/, tests/)
   ├─ docs_change (CLAUDE.md, skills, agent descriptions)
   ├─ agent_evolution (new agent, modified prompt, retired agent)
   └─ architecture (new skill, new domain, new integration)

2. PRE-VALIDATE
   ├─ Snapshot current improvement score
   ├─ Run `uv run mde-py validate --all`
   ├─ Record tool versions
   └─ For agent_evolution: check agent registry integrity

3. APPLY (in worktree for isolation)
   ├─ Create feature branch
   ├─ Make changes
   ├─ For docs_change: update CLAUDE.md, skill descriptions
   ├─ For agent_evolution: update agent registry + descriptions
   └─ Commit with provenance metadata in message

4. POST-VALIDATE
   ├─ Run `uv run mde-py validate --all` again
   ├─ Run tests: `uv run pytest`
   ├─ Run lint: `uv run ruff check`
   ├─ Compare improvement score: better, same, or worse?
   └─ For config_change: `chezmoi apply --dry-run` in devcontainer

5. DECIDE
   ├─ Score improved → merge automatically, log evidence
   ├─ Score unchanged → merge if no regressions, flag for review
   ├─ Score worse → revert, create GitHub issue with findings
   └─ Validation failed → revert, create GitHub issue

6. COMPOUND (from compound-knowledge pattern)
   ├─ Extract what worked/didn't into docs/knowledge/
   ├─ Update improvement score baseline
   └─ Feed back to Layer 1 (what to research next based on gaps)
```

### 6.2 Improvement Score — Metrics

| Metric | How to Measure | Weight |
|--------|----------------|--------|
| Validation pass rate | `uv run mde-py validate --all` exit code + warning count | 0.20 |
| Brew/mise duplicate count | Cross-reference Brewfile vs .mise.toml | 0.15 |
| Chezmoi reproducibility | `chezmoi apply --dry-run` in clean devcontainer | 0.15 |
| Test coverage | `uv run pytest --cov` | 0.10 |
| Lint cleanliness | `uv run ruff check` violation count | 0.05 |
| Source freshness | Ratio of fresh to total sources across notebooks | 0.10 |
| Actionable findings rate | Ratio of applied findings to total discoveries | 0.10 |
| Agent trigger accuracy | Do agents fire when they should? | 0.10 |
| Token cost efficiency | Cost per finding, trending down | 0.05 |

### 6.3 Score Card

Every cycle produces a versioned score card:

```yaml
# docs/research/trail/scorecards/2026-03-20-001.yaml
cycle_id: "2026-03-20-001"
timestamp: "2026-03-20T14:30:00Z"
tool_versions: { ... }
metrics:
  validation_pass_rate: 0.87
  validation_warning_count: 12
  brew_mise_duplicates: 3
  chezmoi_reproducible: false
  test_coverage: 0.64
  lint_violations: 8
  total_sources: 127
  stale_sources: 14
  notebooks_active: 5
  findings_this_cycle: 7
  findings_actionable: 3
  findings_applied: 2
  findings_reverted: 0
  agents_active: 8
  agents_triggered_correctly: 6
  avg_findings_per_agent: 4.2
  token_cost_this_cycle: 0.47
  cycle_duration_minutes: 34
  score_trend: improving
  consecutive_improving_cycles: 3
  biggest_gap: "chezmoi_reproducible"
delta_from_last:
  validation_pass_rate: +0.03
  brew_mise_duplicates: -1
  stale_sources: +2
  token_cost_this_cycle: -0.12
improvement_score: 0.72
previous_score: 0.68
```

## 7. Meta Layer — Agent Evolution Engine

### 7.1 Evolution Protocol

```
1. DISCOVERY
   Layer 1 agents research orchestration tools/patterns

2. EVALUATION
   Compare against current agent setup:
   ├─ Does this solve a problem we have?
   ├─ Confidence check: confirmed/probable/speculative?
   ├─ Token cost impact?
   └─ Complexity vs. benefit?

3. INTEGRATION (one of):
   ├─ CREATE new agent → add to registry, write description
   ├─ MODIFY existing agent → update prompt, tools, schedule
   ├─ RETIRE agent → mark deprecated, keep in registry for history
   ├─ CREATE skill → new .md file in skills directory
   ├─ INSTALL tool → add to .mise.toml or plugin config
   └─ ADOPT pattern → update CLAUDE.md rules, workflow docs

4. MEASUREMENT
   After N cycles with the change:
   ├─ Did actionable_rate improve?
   ├─ Did improvement score increase?
   ├─ Did token costs decrease?
   └─ Did cycle time improve?

5. REGISTRY UPDATE
   ├─ Update agent performance metrics
   ├─ Bump version on modified agents
   ├─ Archive retired agents
   └─ Log evolution decision in docs/knowledge/
```

### 7.2 Self-Improving Agent Descriptions

After each agent run, compare what the agent was asked to do vs. what it actually did well:

- If there's drift, update the agent's description to match its actual strengths
- Track trigger accuracy: was this agent invoked when it should have been?
- Use the prompt-master pattern (9-dimension intent extraction) as a quality check on agent prompts

## 8. Obsidian Integration

### 8.1 Access Priority

1. **Obsidian CLI** (built-in, 95 commands, token-efficient) — primary agent interface
2. **Local REST API** plugin — fallback for programmatic batch operations
3. **Direct filesystem** — last resort

### 8.2 Recommended Plugin Stack

| Tier | Plugin | Role |
|------|--------|------|
| Core | Obsidian CLI | Agent-vault interface (95 commands) |
| Core | Local REST API | HTTP CRUD for batch operations |
| Core | Dataview | SQL-like queries, dynamic dashboards |
| Core | Obsidian Git | Version-control the knowledge base |
| Core | Templater + QuickAdd | Standardized note creation |
| AI | Smart Connections | Semantic discovery of related notes |
| AI | Obsidian Copilot | In-vault Claude chat |
| Research | Readwise | Automated highlight ingestion |
| Research | Omnisearch | Full-text fuzzy search via HTTP |
| Structure | Metadata Extractor | JSON export for NotebookLM ingestion |

### 8.3 Agent ↔ Vault Interaction

```
Agent finds a useful pattern
  → Obsidian CLI creates note from template
  → Dataview auto-indexes it
  → Smart Connections surfaces related existing notes
  → Obsidian Git auto-commits
  → Metadata Extractor can export for NotebookLM ingestion
```

## 9. Token Optimization

### 9.1 Token Savings Stack

| Tool | Savings | Install | Role |
|------|---------|---------|------|
| mcp2cli | 96-99% MCP schema savings | `uv tool install mcp2cli` | Convert MCP servers to CLI commands |
| CLI-Anything | Structured CLI replaces verbose API calls | `pip install -e .` (generate once) | Wrap desktop tools as CLIs |
| claude-mem pattern | ~10x on memory lookups | Adopt 3-layer retrieval design | Compact indices, full content on demand |
| TOON encoding | 40-60% vs JSON | Built into mcp2cli | Large data serialization between agents |

### 9.2 Bake Pattern for Swarm

```bash
# One-time setup: bake MCP connections as CLI commands
mcp2cli bake notebooklm --save @nlm
mcp2cli bake github --save @gh
mcp2cli bake claude-flow --save @cf

# Any agent can call without loading full MCP schema:
mcp2cli @nlm notebook-query --notebook-id abc --query "what's new"
```

### 9.3 Token Budget Tracking

```yaml
metrics:
  token_cost_this_cycle: 0.47
  token_cost_per_finding: 0.067
  mcp_schema_tokens_saved: 45000
```

## 10. Scheduling & Continuity

### 10.1 Loop Integration

```
/loop 6h research-cycle
  ├─ Layer 1: Spawn research agents (YouTube, Reddit, GitHub, docs)
  ├─ Layer 2: Synthesize new findings via NotebookLM queries
  ├─ Layer 3: Apply confirmed improvements
  └─ Meta: Evaluate agent performance, evolve registry

/loop 24h deep-research
  ├─ ARIS-style overnight autonomous deep dive
  ├─ Cross-model adversarial review on findings
  └─ Full improvement score recalculation

/loop 7d full-audit
  ├─ Chezmoi reproducibility test (devcontainer)
  ├─ Brew/mise duplicate detection
  ├─ Agent registry health check
  ├─ Stale docs detection
  └─ NotebookLM notebook health (approaching source limits?)
```

### 10.2 Continuity Guarantees

| Problem | Solution |
|---------|----------|
| Agent sessions expire after 3 days | Task renewer pattern auto-reschedules |
| Knowledge lost between sessions | Trail adapter persists all findings; agents search before starting |
| Ideas dropped mid-conversation | Every finding gets a Provenance Record immediately |
| Tool versions change under us | Version-stamped cycles; research agents monitor release feeds |
| Research already done gets repeated | Dedup against Trail: "was this URL already researched?" |
| Changes break things | Worktree isolation + pre/post validation + automatic revert |

## 11. Skill Strategy

| Skill | Purpose | Create or Adopt? |
|-------|---------|------------------|
| `research-cycle` | Orchestrate a full Layer 1→2→3 research cycle | Create |
| `source-health` | Check NotebookLM source freshness, refresh stale | Create |
| `notebook-sync` | Bidirectional NotebookLM ↔ Obsidian sync | Create |
| `improvement-score` | Calculate and track the quantified improvement metrics | Create |
| `agent-evolve` | Evaluate and update agent registry based on performance | Create |
| `compound-learn` | Extract and persist learnings after each cycle | Adopt from compound-knowledge |
| `overnight-research` | ARIS-style autonomous overnight deep dive | Adopt from ARIS |
| `vault-review` | Compare vault state against current session | Adopt (community pattern) |

The skill roster is mutable — research may discover better existing skills or reveal that a skill should be split/merged.

## 12. Research Findings — Tools Evaluated

### 12.1 Agent Orchestration

| Tool | Verdict | Key Adoption |
|------|---------|-------------|
| ComposioHQ/agent-orchestrator | STRONG CONSIDER | Worktree isolation + CI feedback loop |
| knowsuchagency/mcp2cli | STRONG CONSIDER | 96-99% token savings, MCP-to-CLI bridge |
| ComposioHQ/composio (Rube MCP) | CONSIDER | Single-auth gateway to 500+ services |
| VoltAgent awesome lists | MINE PERIODICALLY | Skill/subagent discovery catalog |
| NousResearch/hermes-agent | INSPIRATION | Closed learning loop, agentskills.io standard |
| msitarzewski/agency-agents | SKIP | Prompt library, not a framework |

### 12.2 Auto-Research & Memory

| Tool | Verdict | Key Adoption |
|------|---------|-------------|
| wanshuiyin/Auto-claude-code-research-in-sleep (ARIS) | VERY HIGH | Overnight autonomous loop, cross-model review, markdown-skill composability |
| thedotmack/claude-mem | HIGH | 3-layer token-efficient retrieval, automatic observation hooks |
| rysweet/amplihack | HIGH | L1-L12 progressive eval, investigation workflow, knowledge graph persistence |
| nidhinjs/prompt-master | MODERATE | 9-dimension intent extraction for agent prompts |

### 12.3 Claude Code Plugins & Skills

| Tool | Verdict | Key Adoption |
|------|---------|-------------|
| EveryInc/compound-engineering-plugin | HIGH | Brainstorm-plan-work-review-compound cycle |
| EveryInc/compound-knowledge-plugin | HIGH | Confidence assessment, docs/knowledge/ persistence |
| ComposioHQ/awesome-claude-plugins | HIGH | skill-creator, audit-project, connect-apps |
| ComposioHQ/awesome-claude-skills | HIGH | kaizen, subagent-driven-development, root-cause-tracing |
| ArtemXTech/personal-os-skills | MEDIUM | recall, sync-claude-sessions, notebooklm import |
| amanaiproduct/amans-skills | MEDIUM | ralph-loop, plugin-dashboard observability |
| paullarionov/claude-certified-architect | LOW | Study reference only |

### 12.4 Obsidian Plugins (Top 18 evaluated)

**Core:** Obsidian CLI, Local REST API, Dataview, Obsidian Git, Templater, QuickAdd
**AI:** Smart Connections, Obsidian Copilot, Text Generator
**Research:** Readwise, Citation Plugin, Omnisearch
**Automation:** Advanced URI, Shell Commands
**Structure:** Excalidraw, Kanban, Note Refactor, Metadata Extractor

### 12.5 Token Optimization

| Tool | Verdict | Key Adoption |
|------|---------|-------------|
| HKUDS/CLI-Anything | CONSIDER | Generate CLIs for desktop apps (Obsidian) |
| knowsuchagency/mcp2cli | STRONG CONSIDER | 96-99% token savings, bake MCP as CLI |

### 12.6 ruvnet Ecosystem

| Tool | What It Is | Verdict |
|------|-----------|---------|
| ruvnet/ruflo | Enterprise multi-agent orchestration — upstream source of claude-flow CLI, 135 skills, Queen-led swarms, Agent Booster (352x speedup) | ALREADY INTEGRATED (via claude-flow) |
| ruvnet/RuVector | Self-learning vector DB in Rust — SONA engine, HNSW search (150x-12,500x faster), Cognitive Containers (.rvf snapshots) | ENGINE UNDERNEATH claude-flow memory |
| ruvnet/agentic-flow | Production deployment framework — 66 self-learning agents, 213 MCP tools, ReasoningBank, GNN Query Refinement (+12.4% recall) | SDK LAYER for claude-flow |
| ruvnet/RuView | Edge AI perception (WiFi → pose estimation) — unrelated IoT project sharing infrastructure | SKIP — not applicable |

**Critical gap discovered:** CLAUDE.md references SONA, ReasoningBank, neural training, and HNSW but the corresponding skills are NOT installed. The auto-learning protocol described in CLAUDE.md cannot actually execute.

**Skills to install immediately (activate capabilities already described in CLAUDE.md):**

| Skill | Why |
|-------|-----|
| `reasoningbank-intelligence` | Persistent cross-session pattern learning — CLAUDE.md's auto-learning protocol depends on this |
| `agentdb-memory-patterns` | Memory pattern optimization for `memory store/search` commands |
| `agentdb-vector-search` | Semantic vector search backing for `memory search --query` |
| `agent-sona-learning-optimizer` | Activates SONA self-optimizing neural architecture referenced in CLAUDE.md |
| `neural-training` | Enables `neural train` commands referenced in CLAUDE.md |

**Skills for autonomous research (new capabilities):**

| Skill | Why |
|-------|-----|
| `agent-goal-planner` | Self-directed goal decomposition for autonomous research loops |
| `agent-scout-explorer` | Exploration agent for discovering patterns and dependencies |
| `agent-topology-optimizer` | Dynamic swarm topology optimization (replaces static `--topology hierarchical`) |

**Key insight:** The four repos (ruflo, RuVector, agentic-flow, RuView) are layers of the same stack. RuVector is the database engine, agentic-flow is the SDK layer, ruflo/claude-flow is the orchestration CLI. The project has the orchestration layer but is missing the self-learning and memory persistence skills that would make the auto-learning protocol functional.

## 13. Existing NotebookLM Knowledge Base

Notebook: "The Claude Code, NotebookLM, and Obsidian Research Stack"
ID: `a9be3bc0-6152-4c4e-86e6-f364f1df6721`
Sources: 14 (YouTube videos, Medium articles, GitHub repos)

Key patterns already documented:
- Research to Knowledge Graph Pipeline (YouTube → NotebookLM → Obsidian wikilinks)
- Automated Inbox Triage & GTD Routing
- Self-Improving Memory Loop via CLAUDE.md
- Autonomous Scheduled Agents via `/loop` + cmux/tmux
- SessionStart hooks for automatic inbox checking
- vault-review and tlddr skills for maintenance
- yt-dlp for YouTube transcript extraction

Known limitations from notebook:
- Citation accuracy ~60% strong, 31% partial, 10-15% weak
- Sessions auto-expire after 3 days (need task renewer)
- Token costs need management for continuous agents
- Machine must stay awake for scheduled tasks
- Source ceiling per notebook (configurable, currently 50 for standard tier)

## 14. Success Criteria

The system is working when:

1. **Improvement score trends upward** over consecutive cycles
2. **Stale source count trends downward** — notebooks stay fresh
3. **Agent registry evolves** — new agents appear, underperforming ones retire
4. **Token cost per finding decreases** — efficiency improves
5. **Known issues decrease** — brew/mise duplicates, chezmoi reproducibility, lint violations
6. **Skills and CLAUDE.md stay current** — updated within days of tool version changes
7. **The system discovers improvements humans didn't anticipate** — the true test of autonomy

## 15. Parallel Workstreams

Per the agreed approach (Approach C, parallel tracks):

**Track A — Fix Known Issues** (immediate)
- Resolve mise lockfile CPU architecture mismatches
- Identify and eliminate brew/mise/node/bun duplicate installs
- Set up devcontainer for chezmoi reproducibility testing
- Fix agent/subagent description accuracy
- Enable GitHub automation

**Track B — Build Research Pipeline** (concurrent)
- Implement Layer 1 research agents
- Set up NotebookLM notebook strategy with source management
- Build Trail Adapter (initial: markdown files)
- Create improvement score calculation
- Wire up `/loop` scheduling

**Both tracks converge** when research starts informing fixes and the self-improvement loop closes.

## 16. Open Questions

1. **Best storage backend for Trail Adapter** — research should determine this, not premature decision
2. **Cross-model review implementation** — which model pairs work best for adversarial review?
3. **Obsidian CLI vs REST API vs filesystem** — need to evaluate CLI capabilities for our specific use cases
4. **agentskills.io standard** — worth adopting for skill interoperability?
5. **Composio Rube MCP** — worth the dependency for 500+ service integrations?
