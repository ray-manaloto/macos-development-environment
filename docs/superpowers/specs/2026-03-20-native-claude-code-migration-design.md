# Native Claude Code Migration Design Spec

**Date:** 2026-03-20
**Status:** Draft
**Goal:** Clean break from claude-flow to native Claude Code features. Rewrite ~/CLAUDE.md from 711 lines to <100. Remove all claude-flow references. Enforce mcp2cli/cli-anything for MCP access. Use second-brain (NotebookLM + Obsidian) for persistent memory.

---

## 1. New ~/CLAUDE.md (<100 lines)

This is the LITERAL content that replaces the current 711-line file.

```markdown
# MDE Development Environment

## Project
Typed Python package at src/mde/ managing macOS developer tooling.
Entry point: `uv run mde-py <subcommand>`. Tools: ruff, ty, pytest.

## Policies (see .claude/rules/ for details)
- Mise-first: all tools in mise config, not install scripts
- Declarative config: pyproject.toml for Python tools, hk.pkl for git hooks
- No shell scripts: all automation is Python modules in src/mde/
- Library-first: find existing tools before writing code
- Secrets: fnox + macOS Keychain + age encryption
- Worktree PR workflow: verify on feature branch, never merge to main for testing
- Issue tracking: catalog unrelated errors as GitHub Issues via `gh issue create`

## Subagents
Defined in .claude/agents/. Core: researcher (Haiku, writes to docs/research/),
coder (inherit), tester (inherit, pytest/ruff/ty), reviewer (Sonnet, read-only).
Specialists: python-coder, mise-specialist, chezmoi-specialist, brew-specialist,
security-auditor (Sonnet, read-only), claude-code-specialist (Sonnet, platform expert).

## MCP Access
Do NOT use MCP tool schemas in context. Use CLI wrappers instead:
- `mcp2cli @github <tool> [args]` for GitHub operations
- `mcp2cli @docker <tool> [args]` for Docker operations
- `npx agent-fetch "<url>" --json` for full URL content (never WebFetch for research)
- `notebooklm <command>` for NotebookLM operations

## Memory Architecture
- Hot (session): Claude Code auto memory (~/.claude/projects/*/memory/)
- Warm (project): YAML/markdown in docs/research/trail/ (git-tracked)
- Cool (synthesis): NotebookLM notebooks per research domain
- Cold (knowledge): Obsidian vault

## Agent Note-Taking Protocol
Write findings to disk IMMEDIATELY, not at session end:
1. Research findings -> docs/research/trail/findings/*.yaml
2. Deep analysis -> docs/research/trail/deep-reviews/*.md
3. Session learnings -> auto memory (for corrections/preferences only)
4. Task state that agents modify repeatedly -> JSON (not markdown)

## Research Pipeline
- CLI: `uv run mde-py research {catalog,score,status}`
- Source catalog: docs/research/source-catalog.md
- Provenance records: docs/research/trail/findings/*.yaml
- Baseline improvement score: 0.450

## File Organization
Never save working files to the root folder. Use:
- src/ for source code, tests/ for tests, docs/ for documentation
- docs/research/trail/ for research artifacts
- .claude/agents/ for subagent definitions
- .claude/rules/ for project policies
```

**Line count: 47 lines** (well under 100).

---

## 2. New .claude/rules/ Files

### 2.1 Keep Existing Rules (no changes needed)

These 8 files remain as-is -- they are already clean of claude-flow references:

| File | Lines | Content |
|------|-------|---------|
| `declarative-config.md` | 7 | pyproject.toml, hk.pkl policy |
| `issue-tracking.md` | 5 | GitHub Issues via gh CLI |
| `library-first.md` | 12 | Assemble-don't-build policy |
| `mise-first.md` | 6 | mise backend priority |
| `no-shell-scripts.md` | 5 | Python modules only |
| `research-pipeline.md` | 8 | Research CLI and source protocol |
| `secrets-management.md` | 6 | fnox + Keychain + age |
| `worktree-pr-workflow.md` | 6 | Never merge to verify |

### 2.2 New Rule: mcp-access.md

**Scope:** Global (no paths frontmatter)

```markdown
# MCP Access Policy

- NEVER use MCP tool schemas directly in the context window (wastes 96-99% of tokens)
- Use mcp2cli baked tools: `mcp2cli @<name> <tool> [args]`
- Use cli-anything generated CLIs for GUI applications
- For GitHub: `mcp2cli @github <tool> --arg value`
- For Docker: `mcp2cli @docker <tool> --arg value`
- For new MCP servers: `mcp2cli bake create <name> --mcp-stdio "<command>"`
- TOON output format (--toon) for large uniform arrays (40-60% token savings)
- Secret values use `env:` or `file:` prefix, never bare CLI arguments
```

### 2.3 New Rule: agent-notes.md

**Scope:** Global (no paths frontmatter)

```markdown
# Agent Note-Taking Policy

- Write findings to disk IMMEDIATELY upon discovery, not at session end
- If session dies mid-work, anything only in context is LOST
- Research findings: docs/research/trail/findings/*.yaml (append-only provenance)
- Deep analysis: docs/research/trail/deep-reviews/*.md
- Auto memory: ONLY for corrections, preferences, and pointers (<200 lines)
- Task/feature state that agents modify repeatedly: use JSON, not markdown
  (models are less likely to corrupt JSON -- Anthropic recommendation)
- Subagents MUST write findings to files, not just return summaries
- At session start: read `git log --oneline -20` for recent context
- At each milestone: `git commit` with descriptive message
- Before context fills: force-write all in-context findings to disk
```

### 2.4 New Rule: context-budget.md

**Scope:** Global (no paths frontmatter)

```markdown
# Context Budget Policy

- CLAUDE.md must stay under 100 lines (target: 50)
- Auto memory MEMORY.md must stay under 200 lines (first 200 loaded every session)
- Use 3-layer progressive disclosure for findings retrieval:
  Layer 1 (index): file paths, titles, confidence -- ~100 tokens/result
  Layer 2 (context): finding summary, implication -- ~500 tokens
  Layer 3 (full detail): complete provenance record -- ~500-1000 tokens
  Search index FIRST, load context for relevant hits, full detail only when needed
- Never load all research findings into context at once
- Subagents return condensed summaries (1000-2000 tokens), not full explorations
- Disable irrelevant plugins to save skill description budget (2% of context window)
```

### 2.5 New Rule: second-brain.md

**Scope:** Global (no paths frontmatter)

```markdown
# Second-Brain Integration Policy

- NotebookLM: one notebook per research DOMAIN, not per session
  - Use `notebooklm source add <file-or-url>` for ingestion
  - Use `notebooklm ask "question" --citations` for cross-source synthesis
  - Use `notebooklm source add-research "query"` for broad topic surveys
  - Use `notebooklm source stale` to find outdated sources
- Obsidian vault: GTD/Zettelkasten for long-term knowledge
- /second-brain skill: capture -> process-inbox -> daily-plan -> closeout
- Consolidation flow:
  1. Agent writes findings to repo files (YAML provenance or markdown deep reviews)
  2. Consolidation step ingests into NotebookLM: `notebooklm source add <file>`
  3. Cross-source synthesis: `notebooklm ask --citations`
```

---

## 3. New .claude/agents/ Files

Replace all 15 existing agents with 10 roles: 4 core + 6 specialists. The existing agents (api-auditor, config-reviewer, findings-consolidator, hooks-reviewer, etc.) are leftovers from the claude-flow era and should be removed.

**Design decisions (cross-referenced from research):**
- Every successful project gives researchers Write access ([researcher-agent-configurations-comparison.md](../../research/trail/deep-reviews/researcher-agent-configurations-comparison.md))
- Descriptions include "Use PROACTIVELY when..." trigger conditions for routing accuracy ([everything-claude-code-agents.md](../../research/trail/deep-reviews/everything-claude-code-agents.md))
- Model routing: haiku for simple/doc, sonnet for coding/review, opus for architecture ([everything-claude-code-agents.md](../../research/trail/deep-reviews/everything-claude-code-agents.md))
- 4-tier tool permissions: read-only, read+bash, full-write, MCP-specific ([everything-claude-code-agents.md](../../research/trail/deep-reviews/everything-claude-code-agents.md))
- `skills:` field INJECTS full skill content at startup, subagents do NOT inherit from parent ([subagent-frontmatter-and-skills-mapping.md](../../research/trail/deep-reviews/subagent-frontmatter-and-skills-mapping.md))

### 3.1 Core Agents

All 4 core agent definitions are in `.claude/agents/`. See the actual files for full system prompts.

| Agent | Model | Tools | Description |
|-------|-------|-------|-------------|
| **researcher** | haiku | Read, Glob, Grep, Bash, **Write, Edit** + agent-fetch | Research + write findings to docs/research/. **FIX**: original spec had Write/Edit in disallowedTools, but protocol required writing files. Now has Write/Edit per universal pattern. |
| **coder** | inherit | All except WebFetch, WebSearch | General implementation with full tool access |
| **tester** | inherit | Read, Glob, Grep, Bash, Write, Edit | pytest, ruff, ty quality gates |
| **reviewer** | sonnet | Read, Glob, Grep, Bash + agent-fetch | Read-only code review, P1/P2/P3 priority system |

### 3.2 Specialist Agents

| Agent | Model | Tools | Description |
|-------|-------|-------|-------------|
| **python-coder** | inherit | All except WebFetch, WebSearch | Python specialist for src/mde/ with ruff/ty/pytest knowledge |
| **mise-specialist** | haiku | Read, Glob, Grep, Bash | mise config, backend priority, tool management |
| **chezmoi-specialist** | haiku | Read, Glob, Grep, Bash | chezmoi templates, dotfiles, secret injection |
| **brew-specialist** | haiku | Read, Glob, Grep, Bash | Homebrew packages, cask management, mise conflict resolution |
| **security-auditor** | sonnet | Read, Glob, Grep | Read-only security review with OWASP focus |
| **claude-code-specialist** | sonnet | Read, Glob, Grep, Bash | Claude Code platform expert (subagents, hooks, skills, teams, plugins, settings, telemetry, platform tools) |

### 3.3 Key Design Change: Researcher Writes Directly

**Original spec (broken):** `disallowedTools: Write, Edit` but protocol says "Write each finding IMMEDIATELY"

**Fixed spec:** `tools: Read, Glob, Grep, Bash, Write, Edit` with `disallowedTools: Agent, WebFetch, WebSearch`

**Evidence from 7 projects:** Every successful research agent directly writes files. No project separates "research" from "persistence" into distinct agents. See [researcher-agent-configurations-comparison.md](../../research/trail/deep-reviews/researcher-agent-configurations-comparison.md) for the full cross-project analysis.

**Constraint:** Researcher is constrained via system prompt to ONLY write to `docs/research/` paths. This is enforced by convention, not by tool restrictions (no per-path tool scoping exists in Claude Code).

---

## 4. MCP Cleanup

### 4.1 MCP Servers to Remove

Remove these from `.claude/settings.json` (if present as MCP configurations):

| Server | Reason |
|--------|--------|
| `claude-flow` | Entire claude-flow system being removed |
| `ruv-swarm` | claude-flow ecosystem |
| `flow-nexus` | claude-flow ecosystem |

### 4.2 mcp2cli Bake Configurations to Create

```bash
# GitHub (replaces mcp__MCP_DOCKER__* GitHub tools and mcp__plugin_github_github__*)
mcp2cli bake create github --mcp-stdio "npx -y @modelcontextprotocol/server-github" \
  --include "search-*,list-*,get-*,create-*,issue-*,pull-*" \
  --exclude "delete-*"

# Docker (replaces mcp__MCP_DOCKER__docker*)
mcp2cli bake create docker --mcp-stdio "npx -y @modelcontextprotocol/server-docker" \
  --include "docker*,checkRepository*,listRepository*"
```

### 4.3 cli-anything CLIs to Consider

For GUI tools used in the workflow:

| Software | Priority | CLI |
|----------|----------|-----|
| NotebookLM | LOW | Already have `notebooklm` CLI (teng-lin/notebooklm-py) |
| Obsidian | MEDIUM | Could generate via cli-anything for vault management |

**Decision:** Do not generate cli-anything CLIs in the initial migration. The existing `notebooklm` CLI and `agent-fetch` cover our needs. Revisit if we need programmatic Obsidian vault management beyond file writes.

---

## 5. Memory Architecture

### 5.1 Claude Code Auto Memory Configuration

No changes needed. Auto memory is enabled by default. Current configuration:

- Location: `~/.claude/projects/<project-hash>/memory/`
- MEMORY.md: Currently 24 lines (index of pointers) -- well within 200-line limit
- Individual files: feedback_*.md, project_*.md, reference_*.md, user_*.md

**Action:** Review MEMORY.md after migration and remove any claude-flow references.

### 5.2 NotebookLM Notebook Strategy

Create one notebook per research domain (long-lived, not per session):

```bash
# Initial notebooks to create
notebooklm create "MDE Research Pipeline"        # Research findings and methodology
notebooklm create "Agent Infrastructure Patterns" # Agent design patterns
notebooklm create "Tool Evaluation Library"       # Tool evaluation and comparison
```

**CLI commands for agents:**

```bash
# Ingest a finding
notebooklm use <notebook-id>
notebooklm source add docs/research/trail/deep-reviews/<filename>.md
notebooklm source wait <source-id>

# Cross-source synthesis
notebooklm ask "What patterns emerge across all sources?" --citations
notebooklm history --save-as-note

# Broad topic survey
notebooklm source add-research "agent memory persistence patterns 2026"

# Maintenance
notebooklm source stale          # Find outdated sources
notebooklm source refresh <id>   # Re-fetch URL sources
```

### 5.3 Obsidian Second-Brain Integration Points

The `/second-brain` skill provides GTD-style operations:

| Operation | When | What |
|-----------|------|------|
| `capture` | During work, on discovery | Quick inbox entry for raw ideas |
| `process-inbox` | Weekly or on-demand | Triage items into projects/references/actions |
| `daily-plan` | Session start | Generate prioritized task list |
| `closeout` | Session end | Archive completed items |

**File flow:** Agent writes to repo -> consolidation ingests to NotebookLM -> weekly deep review archives to Obsidian vault.

### 5.4 How Agents Write Persistent Notes

**File patterns and locations:**

```
# Immediate writes (during work)
docs/research/trail/findings/finding-<slug>.yaml    # YAML provenance records
docs/research/trail/deep-reviews/<topic>.md          # Comprehensive analysis
docs/research/source-catalog.md                      # URL discovery log (append-only)

# Task state (modified repeatedly -- use JSON)
docs/research/RESEARCH_STATE.json                    # Checkpoint for research loops
docs/research/trail/scorecards/*.yaml                # Improvement metrics

# Session learnings (auto memory -- pointers only)
~/.claude/projects/*/memory/MEMORY.md                # Index, <200 lines
~/.claude/projects/*/memory/*.md                     # Individual topic files
```

**Rule:** If an agent modifies a state file repeatedly during a session, it MUST be JSON. If it writes once and never modifies (append-only), YAML or markdown is fine.

---

## 6. Hooks Configuration

### 6.1 Updated .claude/settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks guard-install"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks log-edit-outcome"
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks log-agent-event"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks log-agent-event"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Did the agent write all findings to files on disk? Check if any research findings, deep reviews, or provenance records were mentioned in the conversation but not written to docs/research/trail/. If findings exist only in context and not on disk, answer NO with the missing items. If all findings are persisted, answer YES.",
            "timeout": 15
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Before compaction, verify: (1) Are there any research findings in the conversation that have NOT been written to docs/research/trail/findings/*.yaml? (2) Are there any decisions or preferences that should be saved to auto memory? List any unpersisted items.",
            "timeout": 15
          }
        ]
      }
    ]
  },
  "enabledPlugins": {}
}
```

### 6.2 Hook Changes Summary

| Hook | Action | Rationale |
|------|--------|-----------|
| `PreToolUse[Bash]` | KEEP | guard-install prevents unauthorized package installs |
| `PostToolUse[Write\|Edit]` | KEEP | log-edit-outcome tracks file changes |
| `SubagentStart` | KEEP | log-agent-event for observability |
| `SubagentStop` | KEEP | log-agent-event for observability |
| `TaskCompleted` | REMOVE | Was for claude-flow task tracking, not needed natively |
| `TeammateIdle` | REMOVE | Agent Teams experimental feature, not in active use |
| `Stop` | ADD (prompt) | Quality gate: verify all findings persisted to disk before session ends |
| `PreCompact` | ADD (prompt) | Catch unpersisted findings before context compaction |

### 6.3 Prompt-Based Hooks for Quality Gates

The two new prompt hooks (Stop and PreCompact) are the critical addition. They implement Anthropic's "write-early, write-often" principle by catching the case where findings exist only in the context window and have not been written to files. This is the single most important anti-pattern to prevent: session death destroying knowledge.

---

## 7. Skills Cleanup

### 7.1 Plugins to Disable at Project Level

Set `enabledPlugins` to empty `{}` in `.claude/settings.json`. The current enabled plugins are:

| Plugin | Action | Reason |
|--------|--------|--------|
| `python-development@claude-code-workflows` | DISABLE | Generic Python advice wastes context; our rules are more specific |
| `shell-scripting@claude-code-workflows` | DISABLE | We have a no-shell-scripts policy |
| `developer-essentials@claude-code-workflows` | DISABLE | Generic; our CLAUDE.md + rules provide better guidance |
| `conductor@claude-code-workflows` | DISABLE | claude-flow ecosystem dependency |

### 7.2 User-Level Skills Irrelevant to This Project

The untracked directories shown in git status (`.agent/skills/`, `.agents/skills/`, `.augment/skills/`, etc.) are skill-sync artifacts for various AI coding tools. These do not consume Claude Code context budget and can be left as-is or cleaned up separately.

### 7.3 Skills to Consider Installing

From the research (anthropic-official-complete.md Section 3):

| Plugin | Priority | Action |
|--------|----------|--------|
| `pyright-lsp@claude-plugins-official` | HIGH | Python type checking integration |
| `skill-creator@claude-plugins-official` | MEDIUM | For creating custom skills |
| `hookify@claude-plugins-official` | MEDIUM | For creating hooks |

**Decision:** Do not install these during initial migration. Evaluate after migration is complete and stable.

---

## 8. Research Pipeline Integration

### 8.1 Connection to New Architecture

The existing research pipeline (`src/mde/research/`) connects to the new architecture at these points:

| Pipeline Component | Connection Point |
|-------------------|-----------------|
| `uv run mde-py research catalog` | Reads/writes `docs/research/source-catalog.md` |
| `uv run mde-py research score` | Reads `docs/research/trail/scorecards/` |
| `uv run mde-py research status` | Reads all `docs/research/trail/` |
| Agent findings | Written to `docs/research/trail/findings/*.yaml` |
| Deep reviews | Written to `docs/research/trail/deep-reviews/*.md` |

No changes needed to the Python pipeline code. The new agent-notes.md rule ensures agents write to the correct locations.

### 8.2 RESEARCH_STATE.json Checkpoint Pattern (from ARIS)

Adopt the ARIS `REVIEW_STATE.json` pattern for any multi-round research loops:

```json
{
  "round": 2,
  "status": "in_progress",
  "last_score": 0.450,
  "last_verdict": "needs_improvement",
  "timestamp": "2026-03-20T20:00:00Z",
  "pending_sources": ["https://example.com/article"],
  "completed_findings": ["finding-agent-note-persistence", "finding-3layer-disclosure"]
}
```

**Recovery logic:**
1. File does not exist: fresh start
2. `status` is `"completed"`: fresh start
3. `status` is `"in_progress"` AND `timestamp` older than 24 hours: fresh start (stale)
4. `status` is `"in_progress"` AND `timestamp` within 24 hours: resume from `round + 1`

**Location:** `docs/research/RESEARCH_STATE.json`

### 8.3 Score History Tracking (from autoresearch)

Adopt the autoresearch `results.tsv` pattern for tracking improvement cycles:

**Location:** `docs/research/trail/score-history.tsv`

```
cycle	score	sources_processed	status	description
2026-03-19-01	0.450	60	baseline	Initial research pipeline baseline
2026-03-20-01	0.000	8	in_progress	Deep review of 8 source categories
```

**Fields:**
- `cycle`: date + sequence number
- `score`: quantified improvement metric (0.0-1.0)
- `sources_processed`: count of sources reviewed
- `status`: `baseline`, `in_progress`, `completed`, `regression`, `abandoned`
- `description`: what the cycle attempted

### 8.4 Provenance Enrichment (from compound)

Extend the existing provenance YAML with fields from compound-engineering and compound-knowledge:

```yaml
# Existing fields (keep)
id: finding-<slug>
timestamp: "<ISO 8601>"
source: <url-or-file-path>
agent: <agent-id>
finding_type: technique|architecture|tool|pattern|anti-pattern
confidence: confirmed|likely|speculative
status: discovered|validated|implemented|superseded

# New fields (from compound)
tags:
  - tag1
  - tag2
implication: "<what this means for the project, actionable next steps>"
confident_about: "<one-paragraph summary of what was confirmed>"
gaps: "<what remains unknown or unverified>"
evidence: "<specific quotes or data points>"
coverage_assessment: full_review|partial_review|title_only
```

The `implication`, `confident_about`, and `gaps` fields come from the compound-knowledge plugin's confidence assessment methodology (kw:confidence). The `tags` field enables grep-based retrieval (compound-knowledge's plan search pattern). The `coverage_assessment` field from our existing schema is retained.

---

## 9. Patterns Adopted (with source attribution)

| # | Pattern | Source | Section | How Adopted |
|---|---------|--------|---------|-------------|
| 1 | 3-layer progressive disclosure (search -> context -> full) | claude-mem-mcp2cli-amplihack-complete.md | Section 1 (claude-mem) | context-budget.md rule; auto memory as index, findings as context, deep reviews as full |
| 2 | mcp2cli bake pattern for CLI wrappers | claude-mem-mcp2cli-amplihack-complete.md | Section 2 (mcp2cli) | mcp-access.md rule; baked tools replace MCP tool schemas |
| 3 | TOON output format for token savings | claude-mem-mcp2cli-amplihack-complete.md | Section 3 (mcp2cli) | mcp-access.md rule; --toon flag for large arrays |
| 4 | env:/file: secret prefixes | claude-mem-mcp2cli-amplihack-complete.md | Section 5 (mcp2cli) | mcp-access.md rule; compatible with fnox |
| 5 | REVIEW_STATE.json checkpoint with 24h staleness | aris-and-compound-complete.md | Section 1.3 | RESEARCH_STATE.json in research pipeline |
| 6 | Subagents return text, orchestrator writes files | aris-and-compound-complete.md | Section 3.6 | reviewer.md writes to docs/reviews/; researcher.md writes to docs/research/ |
| 7 | Provenance enrichment (tags, implication, confidence prose) | aris-and-compound-complete.md | Sections 2.3, 3.3 | Extended provenance YAML template |
| 8 | kw:confidence non-numeric assessment | aris-and-compound-complete.md | Section 3.2 | Adopted as pattern for researcher agent findings |
| 9 | Grep-based retrieval in docs/ directories | aris-and-compound-complete.md | Section 3.4 | Already in use via research pipeline |
| 10 | Skill chaining with artifact handoff | gstack-complete-reference.md | Section 5 | Informed sequential agent workflow (research -> code -> test -> review) |
| 11 | /review two-pass checklist (critical blocks, informational doesn't) | gstack-complete-reference.md | Section 10 | reviewer.md P1/P2/P3 priority system |
| 12 | JSON over Markdown for repeatedly-modified state | anthropic-official-complete.md | Section 6C | agent-notes.md rule; RESEARCH_STATE.json |
| 13 | Initializer + Worker agent pattern | anthropic-official-complete.md | Section 6C | Adapted for research: initializer creates plan, worker picks one source |
| 14 | claude-progress.txt progress file pattern | anthropic-official-complete.md | Section 6C | Adapted as RESEARCH_STATE.json + score-history.tsv |
| 15 | Write-early write-often principle | agent-note-persistence-infrastructure.md | Section 1 | agent-notes.md rule; Stop/PreCompact prompt hooks |
| 16 | 4-tier memory hierarchy (hot/warm/cool/cold) | agent-note-persistence-infrastructure.md | Section 3 | Memory architecture in CLAUDE.md |
| 17 | One notebook per domain, not per session | agent-note-persistence-infrastructure.md | Section 2 | second-brain.md rule |
| 18 | NotebookLM source add-research for broad surveys | agent-note-persistence-infrastructure.md | Section 6 | second-brain.md rule |
| 19 | Git history as implicit memory | agent-note-persistence-infrastructure.md | Section 6 | agent-notes.md: read git log at start, commit at milestones |
| 20 | Just-in-time retrieval with lightweight identifiers | anthropic-official-complete.md | Section 6D | MEMORY.md as pointer index, not content store |
| 21 | Context as finite resource with diminishing returns | anthropic-official-complete.md | Section 6D | context-budget.md rule |
| 22 | Absolute minimum viable complexity | anthropic-official-complete.md | Section 6A | Removing claude-flow entirely; native features only |
| 23 | results.tsv structured experiment tracking | orchestrator-autoresearch-complete.md | Section 2.7 | score-history.tsv for research cycles |
| 24 | Simplicity criterion for changes | orchestrator-autoresearch-complete.md | Section 2.6.3 | Reinforces library-first and minimal-change policies |
| 25 | Prompt-based hooks for quality gates | claude-code-native-complete.md | Section 4 | Stop and PreCompact prompt hooks |
| 26 | Agent frontmatter field reference | claude-code-native-complete.md | Section 2 | All 4 agent files use proper YAML frontmatter |
| 27 | Recall + sync-claude-sessions for Obsidian continuity | skill-plugin-ecosystem-complete.md | Section 3 | Identified for future Obsidian integration |
| 28 | CLI-Anything for generating agent-native CLIs | skill-plugin-ecosystem-complete.md | Section 8 | Listed in mcp-access.md rule as option |
| 29 | Flat metadata files over database | orchestrator-autoresearch-complete.md | Section 1.14 | All state is file-based, no opaque databases |
| 30 | Protected artifacts (never flagged for deletion) | aris-and-compound-complete.md | Section 2.4 | Research trail files are append-only |

---

## 10. What Was Explicitly NOT Adopted (and why)

| # | Pattern/Tool | Source | Reason Not Adopted |
|---|-------------|--------|-------------------|
| 1 | claude-flow CLI (all 26 commands) | Current ~/CLAUDE.md | Opaque key-value memory store, excessive context consumption (711 lines), no integration with knowledge ecosystem, redundant with native Claude Code features |
| 2 | claude-flow swarm orchestration | Current ~/CLAUDE.md | Native Claude Code subagents + Agent Teams provide the same capability without third-party CLI overhead |
| 3 | claude-flow neural/HNSW/RuVector | Current ~/CLAUDE.md | Over-engineered for a developer environment project; native auto memory + file-based persistence is sufficient |
| 4 | claude-flow hooks system | Current ~/CLAUDE.md | Claude Code has its own 22-event hook system; duplicating hook logic in two systems creates confusion |
| 5 | claude-mem worker service | claude-mem-mcp2cli-amplihack-complete.md | AGPL-3.0 license is restrictive; background daemon on port 37777 adds complexity; the 3-layer pattern is adopted conceptually without the tool |
| 6 | claude-mem SQLite + ChromaDB backend | claude-mem-mcp2cli-amplihack-complete.md | We use file-based persistence (YAML/markdown/JSON) for human-readability and git-trackability |
| 7 | amplihack Kuzu graph DB | claude-mem-mcp2cli-amplihack-complete.md | Over-engineered for our scale; file-based + NotebookLM cross-source synthesis covers our needs |
| 8 | amplihack L1-L12 eval framework | claude-mem-mcp2cli-amplihack-complete.md | Fascinating but not applicable -- we're building a developer environment, not evaluating agent memory |
| 9 | amplihack self-improvement loop | claude-mem-mcp2cli-amplihack-complete.md | Too complex for our research pipeline; the simpler ARIS checkpoint + autoresearch results.tsv patterns suffice |
| 10 | ARIS cross-model review (GPT-5.4 via Codex MCP) | aris-and-compound-complete.md | Adds external API dependency; single-model review with structured checklists is sufficient for our use case |
| 11 | ARIS Feishu/Lark integration | aris-and-compound-complete.md | Not relevant -- we don't use Feishu |
| 12 | ARIS MCP servers (claude-review, llm-chat, minimax-chat) | aris-and-compound-complete.md | Additional MCP servers increase context cost; mcp2cli approach preferred |
| 13 | compound-engineering 27+ review agents | aris-and-compound-complete.md | Excessive for our project size; 4 canonical agents with clear roles is sufficient |
| 14 | compound-engineering docs/solutions/ staleness refresh | aris-and-compound-complete.md | Good pattern but premature -- we need to accumulate solutions first |
| 15 | gstack 21-skill pack | gstack-complete-reference.md | Designed for product teams shipping features, not developer environment tooling |
| 16 | gstack /browse browser automation | gstack-complete-reference.md | We don't need browser testing for a CLI tooling project |
| 17 | gstack Conductor (10-15 parallel sessions) | gstack-complete-reference.md | Agent Teams provides this natively; external tool not needed |
| 18 | gstack Greptile integration | gstack-complete-reference.md | Greptile is for async PR review on GitHub; not needed for this project |
| 19 | agent-orchestrator 8-slot plugin architecture | orchestrator-autoresearch-complete.md | Enterprise-grade orchestration; our 4-agent model with native subagents is simpler and sufficient |
| 20 | agent-orchestrator reaction engine YAML | orchestrator-autoresearch-complete.md | We don't have CI/PR automation that needs retry/escalation; native hooks suffice |
| 21 | hermes-agent closed learning loop | skill-plugin-ecosystem-complete.md | Interesting pattern (agents create skills from experience) but requires hermes-agent as runtime; we use Claude Code directly |
| 22 | gitagent compliance framework (FINRA, SEC) | skill-plugin-ecosystem-complete.md | Not in a regulated industry |
| 23 | chezmoi dotfiles management | skill-plugin-ecosystem-complete.md | We use mise-first, not chezmoi-first |
| 24 | Composio 78-app SaaS automation | skill-plugin-ecosystem-complete.md | We don't need SaaS automation |
| 25 | Agent Teams experimental feature | claude-code-native-complete.md | Experimental (requires env flag); standard subagents are stable and sufficient for now |

---

## 11. Migration Checklist

Execute in this order. Each step should be a separate git commit on a feature branch.

### Phase 1: Remove claude-flow (clean break)

- [ ] 1. **DELETE** `~/CLAUDE.md` (the 711-line file)
- [ ] 2. **CREATE** `~/CLAUDE.md` with the 47-line content from Section 1
- [ ] 3. **EDIT** `.claude/settings.json`: remove `enabledPlugins` entries, remove `TaskCompleted` and `TeammateIdle` hooks
- [ ] 4. **VERIFY**: `grep -r "claude-flow\|npx @claude-flow\|ruv-swarm\|flow-nexus" ~/CLAUDE.md .claude/` returns no results

### Phase 2: Add new rules

- [ ] 5. **CREATE** `.claude/rules/mcp-access.md` with content from Section 2.2
- [ ] 6. **CREATE** `.claude/rules/agent-notes.md` with content from Section 2.3
- [ ] 7. **CREATE** `.claude/rules/context-budget.md` with content from Section 2.4
- [ ] 8. **CREATE** `.claude/rules/second-brain.md` with content from Section 2.5

### Phase 3: Replace agents

- [ ] 9. **DELETE** all 15 files in `.claude/agents/` (api-auditor.md, config-reviewer.md, findings-consolidator.md, hooks-reviewer.md, integration-tester.md, learning-hook-writer.md, learning-writer.md, mise-fixer.md, process-reviewer.md, prompt-writer.md, qa-verifier.md, settings-integrator.md, stop-hook-writer.md, team-config-writer.md, type-safety-agent.md)
- [ ] 10. **CREATE** `.claude/agents/researcher.md` -- core, Haiku, **with Write/Edit** (FIX from original spec)
- [ ] 11. **CREATE** `.claude/agents/coder.md` -- core, inherit model
- [ ] 12. **CREATE** `.claude/agents/tester.md` -- core, inherit model
- [ ] 13. **CREATE** `.claude/agents/reviewer.md` -- core, Sonnet, read-only
- [ ] 13a. **CREATE** `.claude/agents/python-coder.md` -- specialist, inherit model
- [ ] 13b. **CREATE** `.claude/agents/mise-specialist.md` -- specialist, Haiku
- [ ] 13c. **CREATE** `.claude/agents/chezmoi-specialist.md` -- specialist, Haiku
- [ ] 13d. **CREATE** `.claude/agents/brew-specialist.md` -- specialist, Haiku
- [ ] 13e. **CREATE** `.claude/agents/security-auditor.md` -- specialist, Sonnet, read-only
- [ ] 13f. **CREATE** `.claude/agents/claude-code-specialist.md` -- specialist, Sonnet, platform expert

### Phase 4: Add hooks

- [ ] 14. **EDIT** `.claude/settings.json`: add `Stop` prompt hook from Section 6.1
- [ ] 15. **EDIT** `.claude/settings.json`: add `PreCompact` prompt hook from Section 6.1
- [ ] 16. **EDIT** `.claude/settings.json`: set `enabledPlugins` to `{}`

### Phase 5: MCP cleanup

- [ ] 17. **RUN** `mcp2cli bake create github --mcp-stdio "npx -y @modelcontextprotocol/server-github"` (if not already baked)
- [ ] 18. **RUN** `mcp2cli bake create docker --mcp-stdio "npx -y @modelcontextprotocol/server-docker"` (if not already baked)
- [ ] 19. **VERIFY**: `claude mcp list` does not show claude-flow, ruv-swarm, or flow-nexus

### Phase 6: Research pipeline integration

- [ ] 20. **CREATE** `docs/research/RESEARCH_STATE.json` with initial state: `{"round": 0, "status": "completed", "timestamp": "2026-03-20T00:00:00Z"}`
- [ ] 21. **CREATE** `docs/research/trail/score-history.tsv` with header row: `cycle\tscore\tsources_processed\tstatus\tdescription`
- [ ] 22. **VERIFY** existing provenance YAML files have not been corrupted

### Phase 7: Auto memory cleanup

- [ ] 23. **REVIEW** `~/.claude/projects/<project>/memory/MEMORY.md` -- remove any claude-flow references
- [ ] 24. **REVIEW** individual memory files -- remove feedback_second_brain_memory.md reference to claude-flow if present

### Phase 8: Validation

- [ ] 25. **RUN** `uv run mde-py validate --all` -- confirm no regressions
- [ ] 26. **RUN** `uv run ruff check src/ tests/` -- confirm clean
- [ ] 27. **RUN** `uv run ty check` -- confirm clean
- [ ] 28. **RUN** `uv run pytest` -- confirm passing
- [ ] 29. **TEST** subagent invocation: spawn researcher agent, verify it writes to correct location
- [ ] 30. **TEST** Stop hook: end a session with an unpersisted finding, verify prompt hook catches it

---

## Appendix A: File Inventory (What Changes)

### Files Created (22)
```
~/CLAUDE.md                                    (rewritten, 47 lines)
.claude/rules/mcp-access.md                    (new)
.claude/rules/agent-notes.md                   (new)
.claude/rules/context-budget.md                (new)
.claude/rules/second-brain.md                  (new)
.claude/agents/researcher.md                   (new, with Write/Edit -- FIX from original spec)
.claude/agents/coder.md                        (new)
.claude/agents/tester.md                       (new)
.claude/agents/reviewer.md                     (new)
.claude/agents/python-coder.md                 (new, specialist)
.claude/agents/mise-specialist.md              (new, specialist)
.claude/agents/chezmoi-specialist.md           (new, specialist)
.claude/agents/brew-specialist.md              (new, specialist)
.claude/agents/security-auditor.md             (new, specialist)
.claude/agents/claude-code-specialist.md       (new, specialist)
.claude/skills/research-team/SKILL.md          (new, team spawn recipe)
.claude/skills/python-dev-team/SKILL.md        (new, team spawn recipe)
.claude/skills/dotfiles-team/SKILL.md          (new, team spawn recipe)
.claude/skills/infra-team/SKILL.md             (new, team spawn recipe)
docs/research/RESEARCH_STATE.json              (new)
docs/research/trail/score-history.tsv          (new)
docs/research/trail/deep-reviews/*.md          (10 new deep review files from research)
```

### Files Modified (1)
```
.claude/settings.json                          (hooks + plugins updated)
```

### Files Deleted (15)
```
.claude/agents/api-auditor.md
.claude/agents/config-reviewer.md
.claude/agents/findings-consolidator.md
.claude/agents/hooks-reviewer.md
.claude/agents/integration-tester.md
.claude/agents/learning-hook-writer.md
.claude/agents/learning-writer.md
.claude/agents/mise-fixer.md
.claude/agents/process-reviewer.md
.claude/agents/prompt-writer.md
.claude/agents/qa-verifier.md
.claude/agents/settings-integrator.md
.claude/agents/stop-hook-writer.md
.claude/agents/team-config-writer.md
.claude/agents/type-safety-agent.md
```

### Files Unchanged (8 rules + all src/ + all docs/research/trail/)
```
.claude/rules/declarative-config.md
.claude/rules/issue-tracking.md
.claude/rules/library-first.md
.claude/rules/mise-first.md
.claude/rules/no-shell-scripts.md
.claude/rules/research-pipeline.md
.claude/rules/secrets-management.md
.claude/rules/worktree-pr-workflow.md
```

---

## 12. Agent File Validation and Schema-Driven Generation

*Derived from: [agent-file-schemas-and-generation.md](../../research/trail/deep-reviews/agent-file-schemas-and-generation.md)*

### 12.1 The Gap: No Official Schema

As of 2026-03-20, Anthropic publishes no JSON Schema for `.claude/agents/*.md` YAML frontmatter. The canonical specification exists only as documentation prose at `code.claude.com/docs/en/sub-agents`. The Agent SDK Python `AgentDefinition` dataclass covers only 7 of the 14 documented fields. There is no `claude agents validate` command.

### 12.2 Derived JSON Schema for Agent Frontmatter

We will maintain a project-local JSON Schema derived from the official documentation. This schema covers all 14 documented frontmatter fields: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`. (Note: an undocumented `color` field also exists but is excluded from the schema to align with official docs.)

**Location:** `docs/schemas/agent-frontmatter.schema.json`

The full schema is documented in the research appendix (Approach A in the deep review). Key constraints:

| Field | Type | Validation |
|-------|------|------------|
| `name` | string | Required, kebab-case pattern `^[a-z][a-z0-9-]*$` |
| `description` | string | Required, non-empty |
| `model` | string | Enum: sonnet, opus, haiku, inherit, or `claude-*` prefix |
| `permissionMode` | string | Enum: default, acceptEdits, dontAsk, bypassPermissions, plan |
| `memory` | string | Enum: user, project, local |
| `effort` | string | Enum: low, medium, high, max |
| `isolation` | string | Enum: worktree |
| `maxTurns` | integer | Minimum 1 |

### 12.3 gitagent as a Portability/Export Tool (NOT a Validator)

**Correction (2026-03-20):** Investigation confirmed that gitagent (`open-gitagent/gitagent`) is a **portability/export bridge**, not a validator for Claude Code agent files. It imports Claude Code agents into gitagent's own multi-file format (`agent.yaml` + `SOUL.md`) and exports to 10+ frameworks (CrewAI, AutoGen, LangChain, etc.). However, `gitagent validate` validates gitagent format, NOT Claude Code `.md` frontmatter format.

```bash
# gitagent is for EXPORT, not validation:
gitagent import --from claude .claude/agents/   # Convert to gitagent format
gitagent export --format crewai                  # Export to CrewAI

# For Claude Code agent VALIDATION, use our custom hook instead:
# uv run mde-py hooks validate-agents (Section 12.4-12.5)
```

**Decision:** Install gitagent via mise for future portability needs. Do NOT use it for agent file validation — use `validate_agents.py` (Section 12.5) instead.

### 12.4 PostToolUse Hook for Real-Time Validation

Add a PostToolUse hook that triggers agent frontmatter validation whenever a Write or Edit targets `.claude/agents/`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks validate-agents"
          }
        ]
      }
    ]
  }
}
```

The `validate-agents` hook reads `tool_input.file_path` from stdin JSON. If the path does not match `.claude/agents/`, it exits 0 immediately (no-op). If it matches, it parses YAML frontmatter and validates against required fields and enum constraints. Exit code 1 blocks the edit with an error message.

**Note:** This extends the existing `PostToolUse[Write|Edit]` matcher from Section 6.1. The existing `log-edit-outcome` hook and this new `validate-agents` hook should be combined into a single dispatcher command: `uv run mde-py hooks post-edit-dispatch`.

### 12.5 Pre-Commit Hook for Frontmatter Validation

Add a Python validation module at `src/mde/hooks/validate_agents.py` (see deep review Section 3.2 for the full implementation). This validates:

- YAML frontmatter is present and parseable
- Required fields (`name`, `description`) exist
- Enum fields have valid values
- `name` matches kebab-case pattern

Register in `hk.pkl` as a pre-commit hook targeting `.claude/agents/*.md` changes.

### 12.6 Weekly Schema Drift Detection

A GitHub Actions workflow checks whether the upstream Claude Code subagent documentation has changed:

```yaml
# .github/workflows/schema-drift-check.yml
name: Check Agent Schema Drift
on:
  schedule:
    - cron: '0 8 * * 1'  # Weekly Monday 8am
  workflow_dispatch:

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch current docs
        run: curl -sL https://code.claude.com/docs/en/sub-agents > /tmp/subagents-docs.html
      - name: Compare with cached version
        run: |
          if ! diff -q docs/research/cache/subagents-docs.html /tmp/subagents-docs.html; then
            echo "::warning::Claude Code subagent docs have changed"
            gh issue create --title "Agent schema drift detected" \
              --body "The subagent docs page has changed. Review for new frontmatter fields." \
              --label "auto:agent-discovered"
          fi
```

Cache the current docs snapshot at `docs/research/cache/subagents-docs.html` during initial setup.

---

## 13. Chezmoi + Mise Dotfiles Skills

*Derived from: [chezmoi-mise-dotfiles-skills.md](../../research/trail/deep-reviews/chezmoi-mise-dotfiles-skills.md)*

### 13.1 Current State

The project has strong mise skills (`mise-enforcement`, `mise-tool-management`) and basic chezmoi validation (`src/mde/validate/chezmoi.py`), but **no dedicated chezmoi skills** and **no dotfiles-lifecycle skills** that tie chezmoi and mise together. Ecosystem search (skills.sh, awesome-claude-skills) returned zero results for chezmoi, mise, or dotfiles skills. These are greenfield skill opportunities.

### 13.2 New Skill: mde-chezmoi-dotfiles

**Priority:** HIGH
**Location:** `.agents/skills/mde-chezmoi-dotfiles/SKILL.md`
**Purpose:** Guide agents through chezmoi dotfiles management workflows.

**When to invoke:**
- Adding/editing shell config, tmux config, zsh plugins, starship config
- Modifying any file under `~/.config/` that is chezmoi-managed
- Setting up a new machine or devcontainer

**Key content to include:**
- NEVER edit deployed files directly; always go through `.chezmoisource/`
- Template authoring: Go template syntax, `chezmoi data` for available variables
- OS-conditional templates: `{{ if eq .chezmoi.os "darwin" }}`
- Workflow: edit source -> `chezmoi diff` -> `chezmoi apply`
- Secret injection: `{{ keychain "item-name" }}` or age-encrypted files
- External sources: `chezmoi externals` for oh-my-zsh, tmux plugins
- `chezmoi doctor` as a health check
- Non-interactive bootstrap via env vars (`GIT_USER_NAME`, `GIT_USER_EMAIL`) for CI/agent contexts (pattern from martinemde/dotfiles)

### 13.3 New Skill: mde-dotfiles-lifecycle

**Priority:** MEDIUM
**Location:** `.agents/skills/mde-dotfiles-lifecycle/SKILL.md`
**Purpose:** Coordinate the full chezmoi + mise lifecycle when adding/removing tools.

**When to invoke:**
- Adding a new tool that needs both mise config and shell config
- Changing environment variables that flow through both systems
- Bootstrap/provision workflows (new machine, devcontainer)

**Key content to include:**
- Full lifecycle: `.chezmoisource/dot_config/mise/config.toml.tmpl` edit -> `chezmoi apply` -> `mise install --yes` -> `mise lock` -> `mise reshim`
- Decision tree: "Does this change need a chezmoi template update, a direct mise config edit, or both?"
- Bootstrap sequence: `chezmoi init` -> `chezmoi apply` -> `mise install` -> verify
- Environment variable coordination: mise `[env]` vs. shell rc files vs. chezmoi templates
- Shell startup performance check: `time zsh -i -c exit` (pattern from martinemde/dotfiles)
- Devcontainer-aware templates: `{{ if .chezmoi.container }}` conditions

### 13.4 Updates to Existing Skills

#### mise-tool-management: Add chezmoi cross-reference

The current step 3 ("Add to `.chezmoisource/dot_config/mise/config.toml.tmpl`") should be expanded to:
- Link to `mde-chezmoi-dotfiles` skill for template syntax guidance
- Document the full lifecycle steps: edit template -> `chezmoi apply` -> `mise install` -> `mise lock` -> `mise reshim`
- Note OS-conditional tool declarations in templates: `{{ if eq .chezmoi.os "darwin" }}`

#### mise-enforcement: Add chezmoi awareness

Add a note: mise config at `~/.config/mise/config.toml` is chezmoi-managed. Changes MUST go through `.chezmoisource/dot_config/mise/config.toml.tmpl`, not direct edits to the deployed file.

### 13.5 Skill Registry Updates

Add to `configs/mde-skill-registry.json`:

```json
{
  "id": "skills/mde-chezmoi-dotfiles",
  "canonical_path": ".agents/skills/mde-chezmoi-dotfiles/SKILL.md",
  "aliases": ["mde-chezmoi-dotfiles", "chezmoi", "dotfiles"]
},
{
  "id": "skills/mde-dotfiles-lifecycle",
  "canonical_path": ".agents/skills/mde-dotfiles-lifecycle/SKILL.md",
  "aliases": ["mde-dotfiles-lifecycle", "dotfiles-lifecycle"]
}
```

### 13.6 martinemde/dotfiles Patterns Adopted

| Pattern | Source | How Adopted |
|---------|--------|-------------|
| Non-interactive bootstrap via env vars | martinemde/dotfiles | Documented in mde-chezmoi-dotfiles skill |
| Shell startup performance benchmarking | martinemde/dotfiles | `time zsh -i -c exit` in mde-dotfiles-lifecycle |
| Devcontainer-aware templates | martinemde/dotfiles | `{{ if .chezmoi.container }}` in mde-dotfiles-lifecycle |
| Pragmatic minimalism (single-purpose tools) | martinemde/dotfiles | Reinforces existing library-first and mise-first policies |

---

## 14. Specialized Agent Teams

*Derived from: [specialized-agent-teams-patterns.md](../../research/trail/deep-reviews/specialized-agent-teams-patterns.md)*

### 14.1 Enabling Agent Teams

Set in `.claude/settings.json` (already done):

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 14.2 Four Team Templates with Spawn Prompts

#### Research Team

**Use case:** Research cycles, source discovery, literature review, knowledge synthesis.

**Composition:** Lead (inherit) + 2 Researchers (Haiku, write directly) + 1 Reviewer (Sonnet, read-only)

**Design change:** Removed "note-writer" agent. Researchers write findings directly, per the universal pattern found across 7 projects (see [researcher-agent-configurations-comparison.md](../../research/trail/deep-reviews/researcher-agent-configurations-comparison.md)). Each researcher writes to non-overlapping file paths to avoid conflicts.

**Spawn prompt:**
```
Create an agent team to research [TOPIC]. Spawn 3 teammates:
1. "researcher-a" -- Fetch and analyze [URL1, URL2, URL3] via agent-fetch. Write findings to docs/research/trail/findings/finding-[topic]-a-*.yaml. Write deep review section to docs/research/trail/deep-reviews/[FILENAME]-part-a.md.
2. "researcher-b" -- Fetch and analyze [URL4, URL5, URL6] via agent-fetch. Write findings to docs/research/trail/findings/finding-[topic]-b-*.yaml. Write deep review section to docs/research/trail/deep-reviews/[FILENAME]-part-b.md.
3. "reviewer" -- After researchers complete, cross-reference all findings, identify contradictions and gaps. Read-only.
Lead synthesizes parts into final document at docs/research/trail/deep-reviews/[FILENAME].md.
Use Sonnet for reviewer, Haiku for researchers.
```

#### Python Development Team

**Use case:** Feature implementation in src/mde/, bug fixes, refactoring.

**Composition:** Lead/Architect (Opus) + 1 Implementer (Sonnet) + 1 Tester (Sonnet) + 1 Reviewer (Sonnet, read-only)

**Spawn prompt:**
```
Create an agent team to implement [FEATURE] in the mde Python package. Spawn 3 teammates:
1. "implementer" -- Implement in src/mde/ following existing patterns. Only modify src/mde/.
2. "tester" -- Write pytest tests under tests/. Only modify tests/.
3. "reviewer" -- Review for quality, security, and convention adherence. Read-only.
Implementer works first. Tester and reviewer begin once initial commits land.
Use Sonnet for all teammates.
```

**File ownership (conflict avoidance):**

| Owner | Owns | Cannot Touch |
|-------|------|-------------|
| Implementer | `src/mde/**/*.py` | `tests/`, `docs/`, `pyproject.toml` |
| Tester | `tests/**/*.py` | `src/mde/`, `docs/` |
| Reviewer | Nothing (read-only) | Everything |
| Lead | `pyproject.toml`, `docs/` | Delegates src/ and tests/ |

#### Dotfiles/Config Team

**Use case:** Changes spanning chezmoi templates, mise config, Brewfile, and system validation.

**Composition:** Lead/Coordinator (Opus) + 1 Mise Specialist (Sonnet) + 1 Chezmoi Specialist (Sonnet) + 1 Validator (Haiku, read-only + Bash)

**Spawn prompt:**
```
Create an agent team to [DESCRIBE CHANGE] across our dotfiles setup. Spawn 3 teammates:
1. "mise-specialist" -- Handle mise.toml changes. Use registry > aqua > github backend priority.
2. "chezmoi-specialist" -- Handle chezmoi template changes under .chezmoisource/.
3. "validator" -- After others finish, run `uv run mde-py validate --all`. Report failures.
Mise-specialist and chezmoi-specialist work in parallel. Validator waits for both.
```

#### Infrastructure Team

**Use case:** Homebrew packages, system setup scripts, security hardening.

**Composition:** Lead/Coordinator (Opus) + 1 Brew Specialist (Sonnet) + 1 Security Auditor (Sonnet, read-only) + 1 Docs Writer (Haiku)

**Spawn prompt:**
```
Create an agent team to [DESCRIBE CHANGE] in our infrastructure. Spawn 3 teammates:
1. "brew-specialist" -- Modify Brewfile, handle cask installations, resolve conflicts with mise.
2. "security-auditor" -- Review all changes for security implications. Read-only.
3. "docs-writer" -- Update relevant documentation to reflect changes. Use Haiku.
```

### 14.3 Team Spawn Recipe Skills

Each team template is a reusable skill under `.claude/skills/<team-name>/SKILL.md` with `context: fork` and `agent:` frontmatter:

| Skill | Location | Purpose |
|-------|----------|---------|
| `research-team` | `.claude/skills/research-team/SKILL.md` | Multi-source research with researcher agents that write directly |
| `python-dev-team` | `.claude/skills/python-dev-team/SKILL.md` | Feature implementation with file ownership rules |
| `dotfiles-team` | `.claude/skills/dotfiles-team/SKILL.md` | Chezmoi + mise coordination, validation gate |
| `infra-team` | `.claude/skills/infra-team/SKILL.md` | Brewfile management, security review |

Skills contain the full spawn prompt, file ownership rules, quality gate criteria, and task decomposition strategy. Each uses `context: fork` to run in a forked subagent context, and `agent:` to specify the default agent type for the lead.

### 14.4 Quality Gate Hooks per Team Type

| Team Type | TeammateIdle Check | TaskCompleted Check |
|-----------|-------------------|---------------------|
| **Python Dev** | `ruff check` + `ty check` + `pytest` | Coverage threshold, type safety, lint clean |
| **Research** | Has produced output file | Source content extracted, URLs cataloged |
| **Dotfiles** | `mde-py validate --all` passes | Validation clean, no new warnings |
| **Infrastructure** | No broken brew packages | Brewfile parseable, no conflicts with mise |

Quality gate logic lives in `src/mde/hooks/` as Python modules (per no-shell-scripts policy). The hooks read `teammate_name` or `task_description` from stdin JSON to determine which gate to apply.

### 14.5 File-Ownership Decomposition Strategies

**Strategy 1: File-Ownership (recommended default)** -- Each teammate owns a disjoint set of files. Two teammates NEVER edit the same file. If they must, make tasks sequential with dependencies.

**Strategy 2: Layer Decomposition** -- Split by architectural layer (models, services, CLI, tests). Each layer owned by one teammate.

**Strategy 3: Feature Slice** -- Each teammate implements a complete vertical slice. Higher autonomy per teammate but risk of shared-utility conflicts.

**Strategy 4: Source-Per-Task (research)** -- One source per task, synthesizer depends on all fetch tasks, writer depends on synthesizer.

### 14.6 When to Use Teams vs Subagents vs /batch

| Situation | Use |
|-----------|-----|
| Quick focused delegation (test run, search, single-file edit) | **Subagent** |
| Collaborative work needing inter-agent discussion | **Agent Team** |
| Debugging with competing hypotheses | **Agent Team** |
| 5+ parallel independent tasks (no coordination needed) | **Subagents** with worktree isolation |
| Batch processing identical tasks on different inputs | **`/batch`** or parallel subagents |
| Complex feature spanning multiple files/layers | **Agent Team** with file ownership |
| Single-file edits, config changes | **Main session** (no delegation) |

---

## 15. Updated Migration Checklist (Supplemental Items)

Add these items to the existing Phase 2-5 checklist from Section 11:

### Phase 2 additions (after step 8)

- [ ] 8a. **CREATE** `docs/schemas/agent-frontmatter.schema.json` with the derived JSON Schema from Section 12.2
- [ ] 8b. **CREATE** `docs/research/cache/subagents-docs.html` by fetching `https://code.claude.com/docs/en/sub-agents`

### Phase 3 additions (after step 13)

- [ ] 13a. **INSTALL** gitagent via mise: `mise use npm:@open-gitagent/gitagent` (portability tool, NOT validator)
- [ ] 13b. ~~**VALIDATE** agent files round-trip~~ **SKIPPED** — gitagent validates its own format, not Claude Code .md frontmatter. Use `validate_agents.py` (step 16b) instead.

### Phase 4 additions (after step 16)

- [ ] 16a. **UPDATE** `PostToolUse[Write|Edit]` hook to use combined dispatcher `uv run mde-py hooks post-edit-dispatch` (handles both `log-edit-outcome` and `validate-agents`)
- [ ] 16b. **CREATE** `src/mde/hooks/validate_agents.py` with frontmatter validation logic from Section 12.5
- [ ] 16c. **ADD** pre-commit hook for agent frontmatter validation in `hk.pkl`

### Phase 5 additions (after step 19)

- [ ] 19a. **CREATE** `.github/workflows/schema-drift-check.yml` from Section 12.6
- [ ] 19b. **VERIFY** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in `.claude/settings.json` env

### New Phase 9: Chezmoi + Mise Dotfiles Skills

- [ ] 31. **CREATE** `.agents/skills/mde-chezmoi-dotfiles/SKILL.md` with content from Section 13.2
- [ ] 32. **CREATE** `.agents/skills/mde-dotfiles-lifecycle/SKILL.md` with content from Section 13.3
- [ ] 33. **UPDATE** `.agents/skills/mise-tool-management/SKILL.md` with chezmoi cross-references from Section 13.4
- [ ] 34. **UPDATE** `.agents/skills/mise-enforcement/SKILL.md` with chezmoi awareness from Section 13.4
- [ ] 35. **UPDATE** `configs/mde-skill-registry.json` with new skill entries from Section 13.5

### New Phase 10: Team Spawn Recipe Skills

- [ ] 36. **CREATE** `.claude/skills/spawn-research-team.md` with content from Section 14.3
- [ ] 37. **CREATE** `.claude/skills/spawn-python-team.md` with content from Section 14.3
- [ ] 38. **CREATE** `.claude/skills/spawn-dotfiles-team.md` with content from Section 14.3
- [ ] 39. **CREATE** `.claude/skills/spawn-infra-team.md` with content from Section 14.3
- [ ] 40. **CREATE** `src/mde/hooks/team_quality_gates.py` with per-team quality gate logic from Section 14.4

### New Phase 11: Validation of Supplemental Items

- [ ] 41. ~~**VERIFY** `gitagent validate`~~ **REPLACED** — verify `uv run mde-py hooks validate-agents` passes for all agent files in `.claude/agents/` (gitagent validates its own format, not Claude Code)
- [ ] 42. **VERIFY** `uv run mde-py hooks validate-agents` correctly validates and rejects malformed frontmatter
- [ ] 43. **TEST** team spawn by invoking one of the recipe skills and confirming teammates spawn correctly
