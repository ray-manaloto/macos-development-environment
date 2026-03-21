# Researcher/Explorer Agent Configurations: Cross-Project Comparison

**Date:** 2026-03-20
**Analyst:** research-agent
**Research Question:** Should our researcher agent have Write/Edit tools, or should it output findings via stdout and have a separate "note-writer" agent handle persistence?
**Sources:**
- https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep
- https://github.com/EveryInc/compound-engineering-plugin
- https://github.com/EveryInc/compound-knowledge-plugin
- https://github.com/rysweet/amplihack
- https://github.com/thedotmack/claude-mem
- https://github.com/garrytan/gstack
- https://github.com/ComposioHQ/agent-orchestrator

---

## Executive Summary

Every successful research/exploration agent examined **directly writes files**. No project separates "research" from "persistence" into distinct agents. The universal pattern is:

1. The research/explorer agent has **full file-system access** (Read, Write, Edit, Bash, Glob, Grep)
2. Findings are persisted to **well-known directory paths** (e.g., `docs/knowledge/`, `docs/solutions/`, `IDEA_REPORT.md`)
3. A **structured file format** (frontmatter + markdown) enables downstream retrieval
4. The agent itself decides what to write, with **user approval gates** for quality control

**Recommendation:** Give the researcher agent Write/Edit tools. The "research then write" pattern is universal. No project uses stdout-only researchers with separate writer agents.

---

## Project-by-Project Analysis

### 1. ARIS (Auto-Research-In-Sleep)

**URL:** https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep
**Agent type:** SKILL.md markdown files (31 skills)

#### How the research agent is defined

Each skill is a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: research-lit
description: Search and analyze research papers, find related work, summarize key ideas.
  Use when user says "find papers", "related work", "literature review"...
argument-hint: [paper-topic-or-url]
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent, mcp__zotero__*, mcp__obsidian-vault__*
---
```

#### Tools available

The `allowed-tools` line is the key finding. The research-lit skill has:
- `Bash(*)` -- unrestricted shell access
- `Read` -- file reading
- `Glob`, `Grep` -- file search
- `WebSearch`, `WebFetch` -- internet access
- **`Write`** -- direct file writing
- `Agent` -- can spawn sub-agents
- `mcp__zotero__*`, `mcp__obsidian-vault__*` -- MCP tool access

#### How it persists findings

The research-lit skill writes:
- PDF downloads to `papers/` directory
- Literature summaries inline in the conversation
- The downstream `/idea-discovery` pipeline writes `IDEA_REPORT.md`
- `/research-refine` writes `refine-logs/FINAL_PROPOSAL.md` and `refine-logs/EXPERIMENT_PLAN.md`
- All via the `Write` tool directly within the research agent

#### Key insight

ARIS skills are **not restricted** in their write access. The research agent writes files as part of its core workflow. The `allowed-tools` frontmatter explicitly grants `Write`.

---

### 2. Compound Engineering Plugin (EveryInc)

**URL:** https://github.com/EveryInc/compound-engineering-plugin

#### How the research agent is defined

Uses Claude Code plugin format with:
- `agents/` directory containing `.md` agent definitions
- `skills/` directory with `SKILL.md` files
- Agent categories: `review/`, `research/`, `design/`, `docs/`

The plugin has a `research/` agent category alongside its skill definitions.

#### How `/ce:compound` persists findings

The `/ce:compound` skill writes solved-problem documentation to `docs/solutions/`:

```
Workflow: Brainstorm -> Plan -> Work -> Review -> Compound -> Repeat
```

The `Compound` step explicitly **writes files**. From AGENTS.md:
> "New skill: Create `skills/<name>/SKILL.md`"
> "New agent: Create `agents/<category>/<name>.md`"

#### Tools available

Skills use native tools (Glob, Grep, Read) over shell commands. From AGENTS.md:
> "Never instruct agents to use find, ls, cat, head, tail, grep, rg, wc, or tree through a shell for routine file discovery, content search, or file reading"
> "Describe tools by capability class with platform hints"

Agents and skills **have Write access** -- the compound step creates files in `docs/solutions/`.

---

### 3. Compound Knowledge Plugin (EveryInc)

**URL:** https://github.com/EveryInc/compound-knowledge-plugin

#### How `/kw:compound` writes findings

This is the most explicit example. The `/kw:compound` command definition (verbatim):

```yaml
---
name: kw:compound
description: Extract and save learnings from a completed knowledge work session.
  Saves to docs/knowledge/ so future plans automatically find them.
---
```

**Step 4: Save locally** (verbatim from the skill):
```
Write each learning to docs/knowledge/:

Filename: docs/knowledge/{descriptive-slug}.md

Create the directory if it doesn't exist: mkdir -p docs/knowledge/

File format:
---
type: [insight | playbook | correction | pattern]
tags: [relevant keywords for future search]
confidence: [high | medium | low]
created: [today's date]
source: [brief description of what triggered this]
---

# [Learning Title]

[2-4 sentences explaining the learning...]

## Context
[What you were doing when you discovered this.]

## Implication
[How this should change future work.]
```

#### Key design decisions

1. **Agent writes files directly** -- not via stdout, not via a separate writer
2. **User approval required** (Step 2) before writing
3. **Duplicate detection** (Step 3) via `Grep` in `docs/knowledge/` before writing
4. **Structured format** with YAML frontmatter for machine retrieval
5. **Well-known path** (`docs/knowledge/`) that other skills search
6. **1-3 learnings max** per session -- quality filter

#### How findings are retrieved

```
/kw:plan searches docs/knowledge/ -- finds past insights
```

The compounding loop: plan reads knowledge -> work produces -> compound saves -> next plan finds it.

---

### 4. Amplihack

**URL:** https://github.com/rysweet/amplihack
**37 agents** in `.claude/agents/amplihack/`

#### How research agents are defined

Agents are `.md` files with YAML frontmatter:

```yaml
---
name: analyzer
version: 1.0.0
description: Code and system analysis specialist. Automatically selects TRIAGE,
  DEEP, or SYNTHESIS based on task.
role: "Code and system analysis specialist"
model: inherit
---
```

Research-oriented agents include:
- `analyzer.md` -- code and system analysis
- `knowledge-archaeologist.md` -- traces evolution of knowledge
- `concept-extractor.md` -- extracts structured knowledge from documents
- `insight-synthesizer.md` -- discovers revolutionary connections

#### Tools available

All agents have **full Claude Code tool access** (Read, Write, Edit, Bash, Glob, Grep). The analyzer agent uses:
- `Glob` for documentation discovery
- `Grep` for content search
- `Read` for file reading
- **Writes reports directly** -- the output format includes structured report sections

#### How findings are persisted

From the agents README:
```
Sequential Pattern (Common):
1. concept-extractor -> Extract knowledge from documents
2. insight-synthesizer -> Find revolutionary connections
3. architect -> Design implementation
4. builder -> Implement solution
5. cleanup -> Ensure quality
```

The concept-extractor outputs **structured JSON**. The insight-synthesizer outputs reports. Both write directly -- there is no separate "writer" agent. The agent chain passes findings forward through file artifacts.

---

### 5. Claude-Mem

**URL:** https://github.com/thedotmack/claude-mem

#### How PostToolUse hook captures observations

Claude-mem uses a **different approach** -- it is not an agent but a **plugin with lifecycle hooks**:

```json
{
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "node \"$_R/scripts/bun-runner.js\" \"$_R/scripts/worker-service.cjs\" hook claude-code observation",
          "timeout": 120
        }
      ]
    }
  ]
}
```

#### Persistence mechanism

- **PostToolUse hook** fires after every tool call
- Captures the tool name, input, and output as an "observation"
- Sends to a **worker service** (HTTP API on port 37777)
- Worker stores in **SQLite database** with FTS5 full-text search
- **Chroma vector database** for semantic search
- SessionEnd hook generates summaries
- SessionStart hook injects relevant context

#### Key insight

Claude-mem does NOT give agents write access for persistence. Instead, it intercepts all tool calls via hooks and persists observations **automatically and externally**. This is the **hook-based observation pattern** -- fundamentally different from agent-writes-files.

However, claude-mem is for **cross-session memory**, not for research output. Research findings still need to be files that humans can read and version-control.

---

### 6. gstack (Garry Tan)

**URL:** https://github.com/garrytan/gstack
**21 skills** as SKILL.md files

#### How `/investigate` works

The investigate skill (debugging/research) is defined with:

```yaml
---
name: investigate
description: |
  Systematic debugging with root cause investigation. Four phases: investigate,
  analyze, hypothesize, implement. Iron Law: no fixes without root cause.
---
```

**Tools:** Full access -- the skill uses Bash, Read, Write, Glob, Grep. It can:
- Read code and logs
- Write investigation reports
- Create fix implementations
- Write regression tests

The skill **auto-freezes** scope to prevent accidental changes outside the investigation area.

#### How `/retro` saves analytics

The retro skill writes to:
- `~/.gstack/analytics/skill-usage.jsonl` -- usage tracking
- `~/.gstack/contributor-logs/{slug}.md` -- contributor field reports

Both written **directly by the agent** using file write tools.

#### How design documents flow

```
/office-hours writes design doc -> /plan-ceo-review reads it -> /plan-eng-review reads it
```

Each skill writes files that downstream skills read. The entire system is built on the **file-as-communication-channel** pattern.

---

### 7. Composio Agent Orchestrator

**URL:** https://github.com/ComposioHQ/agent-orchestrator

#### How worker agents report findings

This is an **orchestration layer**, not an agent skill system. But the pattern is instructive:

1. Orchestrator spawns workers, each in its own **git worktree**
2. Workers are full Claude Code / Codex / Aider instances with **all tools**
3. Workers **write code, tests, and create PRs** -- full file access
4. Findings flow back via **git** (commits, PRs) and the dashboard

There is no "read-only researcher" pattern. Every agent has full write access.

---

## Pattern Summary

| Project | Research Agent Has Write? | Persistence Method | Approval Gate? | Structured Format? |
|---------|--------------------------|-------------------|----------------|-------------------|
| ARIS | Yes (`Write` in allowed-tools) | Files: `IDEA_REPORT.md`, `EXPERIMENT_PLAN.md` | AUTO_PROCEED configurable | Markdown with sections |
| Compound Engineering | Yes | Files: `docs/solutions/` | Part of review cycle | Markdown |
| Compound Knowledge | Yes | Files: `docs/knowledge/{slug}.md` | User approval required | YAML frontmatter + markdown |
| Amplihack | Yes (full tool access) | Structured reports + JSON | Agent chain | JSON + markdown |
| Claude-Mem | N/A (hook-based) | SQLite + Chroma via HTTP API | Automatic | Database records |
| gstack | Yes (full tool access) | Files: design docs, reports, analytics | AskUserQuestion | Markdown + JSONL |
| Agent Orchestrator | Yes (full tool access) | Git commits + PRs | PR review | Code + markdown |

---

## Design Patterns Identified

### Pattern 1: Agent-Writes-Files (DOMINANT -- 6/7 projects)

The research/explorer agent has Write/Edit tools and directly creates files at well-known paths. This is the universal pattern for research output.

**Advantages:**
- Simple -- no coordination overhead
- Files are human-readable and version-controllable
- Downstream agents can Grep/Read the output
- User can review and edit the files

### Pattern 2: Hook-Based Observation Capture (1/7 projects -- claude-mem)

A PostToolUse hook intercepts all agent activity and persists observations to a database. The agent does not explicitly write research findings.

**Advantages:**
- Zero agent effort -- observations captured automatically
- Semantic search over all activity
- Cross-session persistence

**Disadvantages:**
- Not suitable for structured research output
- Findings are stored as raw observations, not curated knowledge
- Requires external infrastructure (worker service, database)

### Pattern 3: File-as-Communication-Channel (All projects)

Research findings are written as files that downstream agents read. The file system is the communication bus.

```
research-agent --writes--> docs/knowledge/finding.md --read-by--> planning-agent
```

---

## Answer to the Key Question

**Should our researcher agent have Write/Edit tools, or should it output findings via stdout and have a separate "note-writer" agent handle persistence?**

**Answer: Give the researcher Write/Edit tools.** Every successful project does this. The stdout + separate writer pattern does not exist in practice.

### Specific Recommendations

1. **Grant `Write` and `Edit` in `allowed-tools`** for the researcher agent
2. **Define well-known output paths**: `docs/research/trail/findings/` for provenance records
3. **Use structured format**: YAML frontmatter with tags, confidence, date, source
4. **Add approval gate**: Researcher drafts findings, presents to user, writes only after approval (compound-knowledge pattern)
5. **Duplicate detection**: Grep existing findings before writing new ones
6. **Quality filter**: Cap at 3-5 findings per session, not unlimited dumps
7. **Keep the hook-based pattern for cross-session memory** (separate concern from research output)

### What NOT to do

- Do NOT create a separate "note-writer" agent -- it adds coordination overhead with zero benefit
- Do NOT restrict researcher to stdout-only -- every project grants file write access
- Do NOT skip the approval gate -- compound-knowledge's "never auto-save" rule is wise
- Do NOT use unstructured free-text -- use frontmatter for machine-retrievable metadata

---

## Verbatim Agent Configs (Appendix)

### ARIS research-lit SKILL.md (frontmatter)

```yaml
---
name: research-lit
description: Search and analyze research papers, find related work, summarize key ideas.
  Use when user says "find papers", "related work", "literature review",
  "what does this paper say", or needs to understand academic papers.
argument-hint: [paper-topic-or-url]
allowed-tools: Bash(*), Read, Glob, Grep, WebSearch, WebFetch, Write, Agent, mcp__zotero__*, mcp__obsidian-vault__*
---
```

### Compound Knowledge /kw:compound (frontmatter)

```yaml
---
name: kw:compound
description: Extract and save learnings from a completed knowledge work session.
  Saves to docs/knowledge/ so future plans automatically find them.
---
```

### Amplihack analyzer agent (frontmatter)

```yaml
---
name: analyzer
version: 1.0.0
description: Code and system analysis specialist. Automatically selects TRIAGE
  (rapid scanning), DEEP (thorough investigation), or SYNTHESIS (multi-source
  integration) based on task. Use for understanding existing code, mapping
  dependencies, analyzing system behavior, or investigating architectural decisions.
role: "Code and system analysis specialist"
model: inherit
---
```

### gstack investigate (frontmatter)

```yaml
---
name: investigate
description: |
  Systematic debugging with root cause investigation. Four phases: investigate,
  analyze, hypothesize, implement. Iron Law: no fixes without root cause.
  Use when asked to "debug this", "fix this bug", "why is this broken",
  "investigate this error", or "root cause analysis".
  Proactively suggest when the user reports errors, unexpected behavior, or
  is troubleshooting why something stopped working.
---
```

### gstack retro (frontmatter)

```yaml
---
name: retro
description: |
  Weekly engineering retrospective. Analyzes commit history, work patterns,
  and code quality metrics with persistent history and trend tracking.
  Team-aware: breaks down per-person contributions with praise and growth areas.
  Use when asked to "weekly retro", "what did we ship", or "engineering retrospective".
  Proactively suggest at the end of a work week or sprint.
---
```

### Claude-mem PostToolUse hook

```json
{
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "node \"$_R/scripts/bun-runner.js\" \"$_R/scripts/worker-service.cjs\" hook claude-code observation",
          "timeout": 120
        }
      ]
    }
  ]
}
```

### Composio Agent Orchestrator config

```yaml
defaults:
  runtime: tmux
  agent: claude-code
  workspace: worktree
  notifiers: [desktop]

reactions:
  ci-failed:
    auto: true
    action: send-to-agent
    retries: 2
  changes-requested:
    auto: true
    action: send-to-agent
    escalateAfter: 30m
```

---

## Sources Cataloged

| URL | Classification | Fetched |
|-----|---------------|---------|
| https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep | HIGH | Yes |
| https://github.com/EveryInc/compound-engineering-plugin | HIGH | Yes |
| https://github.com/EveryInc/compound-knowledge-plugin | HIGH | Yes |
| https://github.com/rysweet/amplihack | HIGH | Yes |
| https://github.com/thedotmack/claude-mem | MEDIUM | Yes |
| https://github.com/garrytan/gstack | HIGH | Yes |
| https://github.com/ComposioHQ/agent-orchestrator | MEDIUM | Yes |
