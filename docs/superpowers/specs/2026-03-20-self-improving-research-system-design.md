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

## 2. Primary Mandate: Assemble, Don't Build

**The AI/LLM ecosystem in 2026 has tools for nearly everything.** Building new code when a tool, skill, plugin, or CLI already exists is an anti-pattern. The research system's first job is to FIND what exists, not to BUILD replacements.

**Priority order for every capability needed:**
1. **Use an existing installed tool/skill/plugin** — check what's already in mise, .claude/skills/, plugins
2. **Install an existing tool** — search skills.sh, npm, PyPI, GitHub, awesome-lists
3. **Compose existing tools** — chain 2-3 tools together via skills or CLI pipelines
4. **Extend an existing tool** — fork, PR, or wrap an existing tool with minimal glue
5. **Build new code** — LAST RESORT, only when 1-4 are genuinely exhausted

**This applies to everything:** research agents, note-taking, consolidation, scheduling, scoring, tracking. Before writing a single line of Python in `src/mde/`, the agent MUST document what it searched for, what it found, and why nothing existing works.

**Anti-patterns this mandate prevents:**
- Writing a custom "trail adapter" when Obsidian + Dataview already does this
- Building a custom "improvement score" calculator when existing validation tools + a Python module suffice
- Creating custom agent definitions when skills.sh has 4,600+ skills
- Writing a NotebookLM wrapper when `notebooklm-py` already provides full CLI access
- Building a scheduling system when ARIS + launchd already solve the problem

**The research system IS the tool that finds better tools.** If it builds code instead of finding tools, it has failed at its primary purpose.

**No shell scripts.** Per project policy, ALL automation and hook logic MUST be Python modules in `src/mde/`. Claude Code hooks MUST call `uv run mde-py <subcommand>`, never `.sh` files. Any new automation for this system (research cycle orchestration, score calculation, source health checks, trail adapter) MUST be implemented as `mde-py` subcommands, not standalone scripts.

## 3. Goals

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

#### Source Access Methods (Phase 1 vs Phase 2)

| Source | Access Method | Credentials | Phase |
|--------|--------------|-------------|-------|
| GitHub repos/releases | `gh` CLI (already in mise) | `GITHUB_TOKEN` (in fnox) | 1 |
| Official docs | WebFetch / `agent-fetch` skill | None | 1 |
| YouTube transcripts | `yt-dlp` (needs adding to mise) | None | 1 |
| NotebookLM sources | `notebooklm source add` CLI | `storage_state.json` | 1 |
| Reddit | WebFetch on `.json` endpoints or Reddit API | API key (if rate limited) | 2 |
| X/Twitter | `bird` CLI for content fetch | None (uses browser rendering) | 2 |
| Awesome lists | GitHub API via `gh` | `GITHUB_TOKEN` | 1 |

Phase 1 focuses on GitHub + official docs + YouTube + NotebookLM (all have well-defined access). Social sources (Reddit, X) are Phase 2.

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

### 4.3 Agent Research Toolkit (MANDATORY for all research agents)

Every research agent MUST use these tools — not WebFetch (which truncates) or ad-hoc file writes.

#### Fetching Content

| Tool | When to Use | Why |
|------|------------|-----|
| `agent-fetch` (`npx agent-fetch "<url>" --json`) | **Primary** — any URL that needs full text | Returns complete article with structure, 7 extraction strategies, browser impersonation. WebFetch truncates. |
| `agent-fetch crawl "<url>" --json` | Documentation sites — crawl all pages | Follows links, depth control, same-origin safety |
| `notebooklm source add "<url>"` | Adding to NotebookLM for synthesis | NotebookLM indexes full content for cited Q&A |
| `notebooklm source add-research "query" --mode deep` | Discovery — find sources on a topic | NotebookLM searches web, returns relevant sources |
| `yt-dlp` (needs adding to mise) | YouTube transcripts | Extracts captions for full video content |

**Anti-pattern:** Never use WebFetch for research content extraction. It summarizes and truncates, losing the detail that makes findings actionable.

#### Taking Notes (Provenance Records + Second Brain)

Research agents MUST capture findings in TWO forms:

1. **Provenance Records** (machine-readable, for the improvement engine):
   - Written to `docs/research/trail/findings/` as YAML
   - Include: source URL, timestamp, tool versions, confidence, finding type
   - These feed Layer 2 synthesis and Layer 3 improvement scoring

2. **Second Brain capture** (human-readable, for knowledge persistence):
   - Use the second-brain skill's capture workflow: findings go to the Obsidian vault inbox
   - Agent calls: "capture this: [finding summary with source URL]"
   - Processed during inbox triage into Projects/Areas/Resources/Permanent Notes
   - This ensures findings survive even if the trail adapter backend changes

#### Consolidation Pattern

The consolidation agent receives all findings from a research cycle and:

```
1. LOAD all new Provenance Records from docs/research/trail/findings/
2. QUERY NotebookLM notebooks for cross-source synthesis:
   notebooklm ask "What patterns emerge across these new sources?
   What contradicts existing knowledge?" --json
3. CONFIDENCE SCORE each finding (confirmed/probable/speculative)
4. GAP ANALYSIS: Compare findings against current project state
   (run `uv run mde-py validate --all` to get current baseline)
5. SAVE consolidated findings:
   - Machine-readable: docs/research/trail/synthesis/YYYY-MM-DD.yaml
   - Human-readable: second-brain capture to vault
   - NotebookLM: notebooklm ask "..." --save-as-note
6. PASS confirmed improvements to Layer 3
```

#### Deep Review Protocol (ensuring full coverage, not skimming)

For sources that need thorough review (not just a README skim):

```
1. FETCH full content: npx agent-fetch "<url>" --json
2. CHECK completeness: Does the JSON output contain the full article?
   If textContent length < 1000 chars for a substantial source → re-fetch with --preset
3. For GitHub repos: Also fetch key files individually
   - README.md (already in initial fetch)
   - SKILL.md or CLAUDE.md (agent-fetch the raw URL)
   - docs/ directory (agent-fetch crawl "<repo-url>/tree/main/docs")
4. For YouTube: Extract transcript via yt-dlp, add full transcript to NotebookLM
5. SUMMARIZE with explicit coverage checklist:
   - What does it do? (confirmed via actual content, not inferred)
   - Key features relevant to our use case? (cited from source text)
   - What we should adopt? (with specific evidence from the content)
   - What we're missing? (gaps identified by reading, not assumed)
6. FLAG if content was truncated or incomplete — create a follow-up task
```

**Quality gate:** Each research agent must include a `coverage_assessment` in its output:
- `full_review`: Read complete content, all key sections analyzed
- `partial_review`: Some sections skipped (list which and why)
- `skim_only`: Only README/summary — needs deep review follow-up

### 4.4 Source Discovery Protocol (MANDATORY for all agents)

When an agent encounters ANY new URL during research (linked from a README, mentioned in a video transcript, referenced in a blog post, discovered via GitHub trending), it MUST:

```
1. LOG IMMEDIATELY — append to docs/research/source-catalog.md:
   | [ ] | <short description> | <url> | <category> | Discovered by <agent-name> via <parent-source> |

2. CLASSIFY priority:
   - HIGH: Directly relevant to current research domain + actively maintained
   - MEDIUM: Tangentially relevant or relevant to a different domain
   - LOW: Interesting but not clearly actionable
   - SKIP: Irrelevant (log with reason, don't investigate further)

3. For HIGH priority: Add to the Deep Review Queue at bottom of catalog
4. For MEDIUM: Log only — future research cycles will pick it up
5. For LOW/SKIP: Log with reason — never silently discard

NEVER skip logging because "it's probably not relevant" or "I'll come
back to it." The whole point is that future agents can re-evaluate
what this agent thought was low priority.
```

**Why this matters:** In this brainstorming session, research agents skimmed 19 repos and found links to dozens more (VoltAgent's awesome-lists alone reference 500+ skills). Without a protocol, those disappear. With it, each research cycle expands the catalog — and the catalog IS the memory of what the system knows about.

**Anti-patterns:**
- "I found 12 interesting links but only reported 3" — log all 12
- "This repo links to 5 dependencies but they're just libraries" — log them, classify as LOW
- "I already evaluated a similar tool" — log it anyway with "see also: <similar tool>"
- "The video mentioned a tool but I couldn't find the URL" — log the tool name with `[ ] <tool-name> | URL unknown — mentioned in <video-title> at ~<timestamp> | needs-url`

### 4.5 Version Tracking

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
| Dotfiles & Dev Env | chezmoi, mise, zsh config, reproducibility | Docs, tutorials, reference repos |
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

### 5.3 Cross-Model Adversarial Review (Phase 2)

**Not in initial implementation.** Deferred until the basic research pipeline is running and producing findings.

When implemented, the pattern is:
- Agent A produces a recommendation
- Agent B is prompted: "Find flaws in this recommendation: [recommendation]. List specific risks with severity (LOW/MEDIUM/HIGH)."
- If Agent B identifies any HIGH severity risks, the recommendation is blocked and flagged for human review
- LOW/MEDIUM risks are logged in the trail but don't block

Prevents the self-play quality ceiling where a single model validates its own bad ideas. Adopted from ARIS pattern.

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

### 5.5 NotebookLM → Obsidian Export (Phase 1) / Bidirectional Sync (Phase 2)

**Phase 1:** Unidirectional export only — NotebookLM findings are exported to Obsidian vault notes via `notebooklm ask "..." --save-as-note` and CLI output parsing. No sync back from Obsidian to NotebookLM.

**Phase 2 (future):** Bidirectional sync with conflict resolution, data format mapping, and trigger mechanisms. This is a significant engineering effort deferred until the basic pipeline is proven.

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
   ├─ Score improved → create PR via /finishing-a-development-branch, flag as auto-approved
   ├─ Score unchanged → create PR if no regressions, flag for human review
   ├─ Score worse → revert, create GitHub issue with findings
   └─ Validation failed → revert, create GitHub issue

6. COMPOUND (from compound-knowledge pattern)
   ├─ Extract what worked/didn't into docs/knowledge/
   ├─ Update improvement score baseline
   └─ Feed back to Layer 1 (what to research next based on gaps)
```

### 6.2 Improvement Scoring — Dual Model

Inspired by karpathy/autoresearch: improvements need both a **binary gate** (did it get better at all?) and a **magnitude score** (by how much?). This prevents accepting trivially small improvements that aren't worth the complexity.

#### Binary Gates (pass/fail — must ALL pass for a change to be accepted)

| Gate | Pass Condition | How to Measure |
|------|---------------|----------------|
| No regressions | No metric got worse by > 5% | Compare pre/post scorecard |
| Validation clean | Zero new errors introduced | `uv run mde-py validate --all` |
| Tests pass | No test failures | `uv run pytest` exit code |
| Lint clean | No new violations | `uv run ruff check` violation delta |
| Builds work | No broken imports or syntax | Python import check |

If ANY binary gate fails → revert, no exceptions.

#### Magnitude Metrics (scientific scoring — how much better?)

| Metric | How to Measure | Direction | Unit |
|--------|----------------|-----------|------|
| Code speed | `uv run pytest --benchmark` or `hyperfine` on key operations | Lower is better | ms |
| Token usage | Tokens consumed per research cycle | Lower is better | tokens |
| Context efficiency | Findings produced per 1K tokens consumed | Higher is better | findings/1K tokens |
| Rewrite rate | Files modified more than once in a cycle (wasted work) | Lower is better | count |
| Build time | `time uv run mde-py validate --all` | Lower is better | seconds |
| Validation pass rate | `uv run mde-py validate --all` warning count | Lower is better | count |
| Brew/mise duplicates | Cross-reference Brewfile vs .mise.toml | Lower is better | count |
| Chezmoi reproducibility | `chezmoi apply --dry-run` in clean devcontainer | Binary (pass/fail) | bool |
| Test coverage | `uv run pytest --cov` | Higher is better | % |
| Source freshness | Ratio of fresh to total sources | Higher is better | % |
| Agent trigger accuracy | Invocations producing actionable findings / total invocations | Higher is better | % |
| Skill trigger rate | Skills invoked when they should have been / opportunities | Higher is better | % |

#### Composite Score (weighted, for trend tracking)

```
score = (
  validation_pass_rate * 0.15 +
  (1 - brew_mise_duplicates/total_tools) * 0.10 +
  chezmoi_reproducible * 0.15 +
  test_coverage * 0.10 +
  (1 - lint_violations/100) * 0.05 +
  (1 - stale_sources/total_sources) * 0.10 +
  findings_actionable_rate * 0.10 +
  agent_trigger_accuracy * 0.10 +
  context_efficiency_normalized * 0.10 +
  (1 - rewrite_rate_normalized) * 0.05
)
```

**Reference framework:** Study karpathy/autoresearch for how automated research scoring should work. The system should be able to answer: "Is the project measurably better today than it was last week?" with a concrete number, not a feeling.

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

### 7.2 Phase Boundary

**Phase 1 (initial implementation):** The agent registry is human-editable only. Agents produce _recommendations_ for registry changes (stored in the trail) but do NOT modify the registry autonomously. Maximum registry size: 20 agents. Human approval required for agent creation or retirement.

**Phase 2 (after improvement score demonstrates upward trend over 10+ cycles):** Agents may modify the registry autonomously with these guardrails:
- `max_agents` cap of 30
- New agents require post-validation (must produce at least 1 actionable finding in first 3 cycles or auto-retire)
- Retired agents are archived, not deleted, with a 30-day restore window
- Registry changes go through the same PR workflow as code changes

### 7.3 Self-Improving Agent Descriptions

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

### 10.1 Scheduling Architecture: `/loop` + ARIS + Outer Scheduler

**Three scheduling layers, each for what it does best:**

| Layer | Tool | Purpose | Session Survival |
|-------|------|---------|-----------------|
| **Outer** | launchd / GitHub Actions | Start new Claude sessions on schedule | Yes (OS-level) |
| **Pipeline** | ARIS skills | Autonomous multi-round research with state persistence | Yes (file-based `REVIEW_STATE.json`) |
| **Monitor** | `/loop` | Intra-session polling and status checks | No (session-scoped, 3-day max) |

**Why not `/loop` alone?** `/loop` dies when the terminal closes or session expires. It cannot run overnight autonomously. ARIS was designed for exactly this — file-based state persistence, cross-model adversarial review, and resume-from-checkpoint after session death.

**Why not ARIS alone?** ARIS has no scheduler — it runs as a long pipeline within a session. An outer scheduler (launchd, GitHub Actions) starts the session; ARIS handles the pipeline; `/loop` monitors within the session.

```
[Outer Scheduler: launchd / GitHub Actions]
    │
    ▼
[Claude Code Session (ephemeral)]
    │
    ├── ARIS pipeline (autonomous research, state persisted to filesystem)
    │     ├── REVIEW_STATE.json (survives session death)
    │     ├── AUTO_REVIEW.md (cumulative research log)
    │     └── Cross-model review via Codex MCP (Claude executor + GPT reviewer)
    │
    └── /loop (intra-session monitoring only)
          ├── "check ARIS pipeline status every 15m"
          └── "alert if pipeline stalled (state timestamp > 1h old)"
```

### 10.2 Scheduled Cycles

**Every 6 hours (outer scheduler starts session → ARIS pipeline runs):**
- Layer 1: Research agents scan GitHub, YouTube, official docs
- Layer 2: Synthesize via NotebookLM CLI queries
- Layer 3: Apply confirmed improvements via PR workflow
- ARIS state files track progress; session death is recoverable

**Every 24 hours (overnight deep research):**
- ARIS `AUTO_PROCEED: true` for full autonomy
- Cross-model adversarial review on high-stakes findings
- Full improvement score recalculation
- Cumulative log written to `AUTO_REVIEW.md`

**Every 7 days (full audit — can run as `/loop` within active session):**
- Chezmoi reproducibility test (devcontainer)
- Brew/mise duplicate detection
- Agent registry health check
- Stale docs detection
- NotebookLM notebook health (approaching source limits?)

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

**Coverage note:** The research rounds in this brainstorming session used WebFetch (truncating) and skimmed READMEs. A deep review round using `agent-fetch` + `notebooklm source add` should be run for all high-priority sources before implementation begins. Each source should be re-evaluated with `coverage_assessment: full_review`.

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
**Automation:** Advanced URI, Obsidian CLI
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

### Phase 1 Targets (after 10 research cycles)

1. **Improvement score >= 0.05 above initial baseline** measured at cycle 10
2. **Stale source ratio < 20%** across all notebooks
3. **At least 3 actionable findings applied** that improved the improvement score
4. **Token cost per actionable finding < $0.50** averaged over cycles 5-10
5. **brew/mise duplicate count reduced by >= 1** from initial state
6. **CLAUDE.md updated within 7 days** of any Claude Code version bump

### Long-term Indicators (Phase 2+)

7. **Agent registry has been modified** — at least 1 agent added or retired based on performance data
8. **At least 1 finding per 5 cycles classified as "novel"** by human review (not on the known-issues list at cycle start)
9. **chezmoi `apply --dry-run` succeeds** in a clean devcontainer

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

## 16. NotebookLM Integration Issues & Remediation

### 16.1 Current State (Resolved)

**Single tool: `notebooklm-py` (teng-lin) v0.3.4**

| Property | Value |
|----------|-------|
| Package | `notebooklm-py` with `extras = "browser"` |
| Auth location | `~/.notebooklm/storage_state.json` |
| Auth method | Playwright browser login (`notebooklm login`) |
| Auth TTL | 2-4 weeks (Google cookie expiry), auto CSRF refresh |
| Installed via | mise pipx backend, declared in global config |
| CLI binary | `notebooklm` |
| Env var | `NOTEBOOKLM_HOME=~/.notebooklm` (set in mise `[env]`) |

**Previous confusion:** A second package (`notebooklm-mcp-cli` by jacob-bd) was also installed, providing `nlm` CLI and `notebooklm-mcp` MCP server with a separate auth store. This has been **removed** — all NotebookLM access goes through `notebooklm` CLI.

### 16.2 Issues Found and Resolved

| Issue | Root Cause | Resolution |
|-------|-----------|------------|
| Two tools with separate auth | `notebooklm-mcp-cli` installed alongside `notebooklm-py` | Removed `notebooklm-mcp-cli` entirely |
| CLI Playwright missing | `extras = "browser"` not set in mise config | Added `extras = "browser"` to pipx config |
| MCP auth expired rapidly | `notebooklm-mcp-cli` used Chrome DevTools with short-lived cookies | N/A — removed package |
| Not project-owned | Tools not in mise config | Added to global mise config via chezmoi |
| No status check | No way to verify auth | Added `mde:notebooklm:status` mise task |

### 16.3 Access Pattern for Research System

- **All NotebookLM operations** use `notebooklm` CLI (invoked via `uv run` or direct CLI call)
- **Auth refresh:** `mise run mde:notebooklm:login` (interactive, every 2-4 weeks)
- **Status check:** `mise run mde:notebooklm:status`
- **Parallel safety:** Always pass notebook IDs explicitly, never rely on `context.json`
- **Rate limits:** Use `--retry 3` on generate commands
- **Automation parsing:** Use `--json` output consistently
- **Token optimization:** `mcp2cli` available for future MCP bridge if needed

### 16.4 Features We Should Be Using But Aren't

| Feature | Command/Tool | Why It Matters |
|---------|-------------|----------------|
| Web research | `notebooklm source add-research "query" --mode deep` | Discover sources without manually finding URLs |
| Cross-notebook query | `mcp__notebooklm__cross_notebook_query` | Search across all themed notebooks at once |
| Save Q&A as notes | `notebooklm ask "..." --save-as-note` | Persist synthesis results inside notebooks |
| Conversation history | `notebooklm history --save` | Archive research conversations |
| Source fulltext | `notebooklm source fulltext <id>` | Get indexed content for vault sync |
| Mind map generation | `notebooklm generate mind-map` | Export hierarchical JSON for Obsidian |
| Report generation | `notebooklm generate report --format study-guide` | Structured summaries |
| Retry on rate limit | `--retry N` on generate commands | Automatic exponential backoff |
| Debug logging | `NOTEBOOKLM_LOG_LEVEL=DEBUG` | Diagnose silent failures |
| Source waiting | `notebooklm source wait <id>` | Confirm sources are indexed before querying |

### 16.5 NotebookLM Skill Audit

The skill is installed at `.claude/skills/notebooklm` → `.agents/skills/notebooklm` (from `teng-lin/notebooklm-py`).

**What the skill provides that we loaded correctly:**
- SKILL.md with full CLI reference (loaded at conversation start via `/notebooklm`)
- Autonomy rules (what to run automatically vs. ask first)
- Parallel safety warnings about shared context.json
- Subagent patterns for background artifact waiting

**What needs improvement:**
- The skill references CLI commands but our CLI auth is broken — need to specify MCP as primary interface
- The skill's subagent patterns for `artifact wait` and `source wait` should use explicit `-n <notebook_id>` flags for parallel safety
- X/Twitter content requires `bird` CLI pre-fetch (documented in troubleshooting but not in main skill)
- The skill should document the CLI vs MCP auth disconnect for this project

## 17. Claude Code Native Capabilities Gap Analysis

### 17.1 Critical Finding

Anthropic's official docs and engineering blog reveal that Claude Code now has **native equivalents** for many claude-flow features. The canonical guidance from "Building effective agents" (anthropic.com/engineering): "Most successful implementations use simple, composable patterns rather than frameworks."

### 17.2 Native Features We Should Evaluate Against claude-flow

| Capability | claude-flow | Native Claude Code | Status |
|-----------|------------|-------------------|--------|
| Multi-agent coordination | Swarm init + topology | Agent Teams (experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | Need to evaluate |
| Parallel work decomposition | Task orchestrate | `/batch` skill (auto-decomposes into 5-30 units, worktree isolation) | Not using |
| Persistent agent memory | Memory store/search CLI | Native subagent `memory` field (`user`/`project`/`local` scope) → `~/.claude/agent-memory/<name>/` | Not using |
| Agent lifecycle hooks | Hooks CLI | Native `settings.json` hooks (20+ events including `TaskCompleted`, `SubagentStart/Stop`, `TeammateIdle`) | Partially using |
| Task locking for parallel agents | Swarm coordination | File-based task locking (from "Building a C compiler" pattern) | Not using |
| Progress tracking | Swarm status | `claude-progress.txt` pattern (from "Effective harnesses" blog) | Not using |

### 17.3 Official Plugins We Should Install

| Plugin | Source | What It Provides |
|--------|--------|-----------------|
| `claude-code-setup` | anthropics/claude-plugins-official | `claude-automation-recommender` skill — analyzes codebase and recommends automations |
| `claude-md-management` | anthropics/claude-plugins-official | `claude-md-improver` skill, `/revise-claude-md` command |
| `pyright-lsp` | anthropics/claude-plugins-official | Python type intelligence via LSP |
| `context7` | anthropics/claude-plugins-official | Library documentation lookup |

### 17.4 Official Marketplaces to Register

```bash
/plugin marketplace add anthropics/skills
/plugin marketplace add anthropics/claude-plugins-official
```

### 17.5 Agent Skills Standard (agentskills.io)

The official `anthropics/skills` repo follows the Agent Skills open standard. Our custom skills should adopt this standard for interoperability. Key requirements:
- `SKILL.md` with `name` and `description` frontmatter
- Keep SKILL.md under 500 lines; use supporting files for reference
- Skills support `context: fork`, `agent`, `model`, `allowed-tools` frontmatter

### 17.6 Python Agent SDK Capabilities We're Not Using

| Feature | What It Enables |
|---------|----------------|
| `@tool` decorator + `create_sdk_mcp_server()` | In-process Python tools as MCP servers (no subprocess overhead) |
| Python hooks via `HookMatcher` | PreToolUse/PostToolUse validation in Python |
| `permission_mode="plan"` | Review-before-execute workflows |
| `setting_sources=["project", "local"]` | Load filesystem settings in SDK |
| Custom `system_prompt` per agent | Specialized agent behavior |

### 17.7 Engineering Blog Patterns to Adopt

| Pattern | Source | What to Do |
|---------|--------|-----------|
| File-based task locking | "Building a C compiler with parallel Claudes" | Agents claim tasks via lock files, git handles conflicts |
| `claude-progress.txt` | "Effective harnesses for long-running agents" | Work history file prevents premature completion claims |
| One-feature-per-session | Same | Focus discipline for agent sessions |
| Simple composable patterns | "Building effective agents" | Evaluate if native features can replace claude-flow complexity |
| Poka-yoke tool design | "Writing effective tools" | Design tools that prevent misuse |

### 17.8 NotebookLM Sources to Add from This Research

| Source | Priority | URL |
|--------|----------|-----|
| Claude Code docs index | High | `https://code.claude.com/docs/llms.txt` |
| Building effective agents | High | `https://www.anthropic.com/engineering/building-effective-agents` |
| Building C compiler with parallel Claudes | High | `https://www.anthropic.com/engineering/building-c-compiler` |
| Effective harnesses for long-running agents | High | `https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents` |
| Agent SDK README | Medium | `https://github.com/anthropics/claude-agent-sdk-python` |
| Claude plugins official README | Medium | `https://github.com/anthropics/claude-plugins-official` |
| Skills repo README + spec | Medium | `https://github.com/anthropics/skills` |
| How Anthropic teams use Claude Code | Medium | `https://claude.com/blog/how-anthropic-teams-use-claude-code` |

### 17.9 Architecture Decision Required

**Open question:** Should the self-improving research system use:

**A) claude-flow** — More features (swarm topologies, neural training, HNSW search), but adds framework complexity and many referenced capabilities (SONA, ReasoningBank) have missing skills

**B) Native Claude Code features** — Agent teams + `/batch` + native subagent memory + hooks. Simpler, officially supported, follows Anthropic's own "simple composable patterns" guidance

**C) Hybrid** — Use native features for orchestration (agent teams, hooks, memory), claude-flow for specialized capabilities (vector search, embeddings, advanced routing)

This decision should itself be a research output of the system — Layer 1 should continuously evaluate both approaches as both evolve.

**Blast radius if option B (native) is chosen:** Sections 3.1 (swarm topology references), 7 (Meta Layer orchestration), 9.2 (mcp2cli bake pattern), 10 (loop scheduling via claude-flow), and all claude-flow CLI references would need revision. The following designs are **orchestration-agnostic** and survive any choice: Trail Adapter, Provenance Record, Improvement Score, NotebookLM notebook strategy, source staleness detection, and the research source catalog.

## 18. Open Questions

1. **Best storage backend for Trail Adapter** — research should determine this, not premature decision
2. **Cross-model review implementation** — which model pairs work best for adversarial review?
3. **Obsidian CLI vs REST API vs filesystem** — need to evaluate CLI capabilities for our specific use cases
4. **agentskills.io standard** — worth adopting for skill interoperability?
5. **Composio Rube MCP** — worth the dependency for 500+ service integrations?
6. **claude-flow vs native Claude Code features** — which orchestration approach is better for this project?
7. **Agent teams (experimental)** — stable enough for production use?
