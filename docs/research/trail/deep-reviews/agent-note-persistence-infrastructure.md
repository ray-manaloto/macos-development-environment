# Agent Note-Taking and Persistence Infrastructure

Deep review: how agents should persist notes so nothing is lost between sessions.

**Date:** 2026-03-20
**Sources fetched:**
- https://code.claude.com/docs/en/memory (Claude Code memory docs)
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool (Memory tool API)
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Context engineering)
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents (Long-running agent harnesses)
- Existing project: `docs/research/trail/findings/`, `~/.claude/projects/*/memory/`

---

## 1. How agents should write notes that survive session death and context compaction

### The core problem

From Anthropic's "Effective harnesses for long-running agents":

> "The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before."

Two failure modes destroy agent notes:
1. **Context compaction** -- Claude Code summarizes the conversation when nearing the context limit. The compaction summary "preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs or messages" but critical nuance can be lost.
2. **Session death** -- when a session ends (user closes terminal, timeout, crash), anything only in the context window is gone forever.

### Anthropic's recommended techniques (from context engineering article)

Three techniques address context limitations, in order of preference:

1. **Structured note-taking (agentic memory)** -- "a technique where the agent regularly writes notes persisted to memory outside of the context window. These notes get pulled back into the context window at later times." This is the primary pattern. The example given: "Like Claude Code creating a to-do list, or your custom agent maintaining a NOTES.md file."

2. **Compaction** -- automatic summarization. Claude Code "preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs." After compaction, "the agent can then continue with this compressed context plus the five most recently accessed files."

3. **Sub-agent architectures** -- "specialized sub-agents can handle focused tasks with clean context windows. The main agent coordinates with a high-level plan while subagents perform deep technical work. Each subagent might explore extensively, using tens of thousands of tokens or more, but returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)."

### The write-early, write-often principle

From the long-running agents article, Anthropic's solution requires that each agent session "leaves clear artifacts for the next session." Specifically:

- A **progress file** (`claude-progress.txt`) that agents read at session start and update at session end
- **Git commits** with descriptive messages after each feature completion
- A **feature list** in structured JSON format that persists task state

The critical insight: **write to disk immediately, not at the end.** If a session dies mid-work, anything only in context is lost. Agents must write notes to files proactively during work, not just as a cleanup step.

### Recommended note-writing cadence

Based on the sources, agents should write notes:

1. **At session start** -- read existing notes, record "starting work on X"
2. **After each discovery** -- write the finding immediately to a file
3. **Before any risky operation** -- checkpoint current understanding
4. **At every natural breakpoint** -- completed a sub-task, switching focus
5. **Before context compaction** -- if the agent detects it's approaching limits, force a write

---

## 2. Recommended pattern for agent-to-NotebookLM ingestion

### Available CLI commands

The `notebooklm` CLI (teng-lin/notebooklm-py, v0.1.x) provides:

```bash
# Authentication
notebooklm login                          # Browser-based OAuth, stores at $NOTEBOOKLM_HOME

# Notebook management
notebooklm list                           # List all notebooks
notebooklm create "Notebook Name"         # Create new notebook
notebooklm use <notebook-id>              # Set active notebook (supports partial IDs)
notebooklm status                         # Show current context
notebooklm summary                        # AI-generated notebook summary
notebooklm delete <notebook-id>           # Delete notebook

# Source management (critical for ingestion)
notebooklm source add <path-or-url>       # Add file or URL as source
notebooklm source add-research "<query>"  # Add web research as a source
notebooklm source list                    # List sources in current notebook
notebooklm source get <source-id>         # Get source details
notebooklm source fulltext <source-id>    # Get full extracted text
notebooklm source guide <source-id>       # Get AI study guide for a source
notebooklm source rename <id> "name"      # Rename source
notebooklm source delete <id>             # Delete source
notebooklm source stale                   # Find stale sources
notebooklm source refresh <id>            # Refresh source content
notebooklm source wait <id>               # Wait for source processing

# Chat (Q&A against notebook)
notebooklm ask "question"                 # Ask the notebook a question
notebooklm ask "question" --citations     # Include source citations
notebooklm history                        # Get conversation history
notebooklm history --save-as-note         # Save conversation as a note in notebook

# Configuration
notebooklm configure                      # Set persona and response settings
```

### Recommended notebook strategy

Create one notebook per research domain, not per session:

```bash
# Project-level notebooks (long-lived)
notebooklm create "MDE Research Pipeline"
notebooklm create "Agent Infrastructure Patterns"
notebooklm create "Tool Evaluation Library"

# NOT this (session-scoped, creates sprawl)
notebooklm create "Session 2026-03-20 Morning"  # BAD
```

### Agent-to-NotebookLM ingestion workflow

Step 1: Agent writes findings to repo files (YAML provenance records or markdown deep reviews).

Step 2: A consolidation step ingests those files into NotebookLM:

```bash
# Set active notebook
notebooklm use <notebook-id>

# Add the deep review as a source
notebooklm source add docs/research/trail/deep-reviews/agent-note-persistence-infrastructure.md

# Add individual findings
notebooklm source add docs/research/trail/findings/finding-claude-mem-3layer.yaml

# Add external URLs for cross-referencing
notebooklm source add "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"

# Wait for processing
notebooklm source wait <source-id>

# Generate synthesis
notebooklm ask "What are the key patterns for agent note persistence across all sources?"
notebooklm history --save-as-note
```

Step 3: Use `notebooklm ask` for cross-source Q&A that no single document could answer:

```bash
# Cross-source synthesis queries
notebooklm ask "Compare the 3-layer progressive disclosure pattern from claude-mem with Anthropic's structured note-taking recommendation. Are they compatible?"
notebooklm ask "What file formats does each source recommend and why?"
```

### What NotebookLM provides that file-based persistence does not

- **Cross-source synthesis** -- it can answer questions that span multiple documents
- **AI-generated study guides** -- `notebooklm source guide <id>` produces structured summaries
- **Citation tracking** -- `notebooklm ask "..." --citations` traces answers to specific sources
- **Stale detection** -- `notebooklm source stale` identifies outdated sources
- **Research ingestion** -- `notebooklm source add-research "query"` adds web results as sources

---

## 3. How agents should use the second-brain skill for capture/processing

### The second-brain stack (from auto memory `feedback_second_brain_memory.md`)

The project has established this as the canonical memory stack:

| Layer | Tool | Purpose | Scope |
|-------|------|---------|-------|
| Hot (session) | Claude Code auto memory | Session learnings, corrections, preferences | Per working tree |
| Warm (project) | File-based persistence | Findings, progress, provenance records | Git-tracked, shared |
| Cool (synthesis) | NotebookLM | Cross-source Q&A, research synthesis | Per-notebook, cloud |
| Cold (knowledge) | Obsidian vault | GTD/Zettelkasten/PARA knowledge graph | Local vault, long-term |

### Second-brain skill operations

The second-brain skill (`/second-brain`) provides these GTD-style operations:

1. **Capture** -- quick inbox entry for raw ideas and discoveries
2. **Process inbox** -- triage captured items into projects, references, or actions
3. **Daily plan** -- generate a prioritized task list from open items
4. **Closeout** -- end-of-day review, archive completed items

### How agents should use it

**During research sessions:**

```
# Capture each finding immediately (do not batch)
/second-brain capture "Found that Anthropic recommends JSON over markdown for structured agent state because models are less likely to corrupt JSON files"

# At session end
/second-brain closeout
```

**During development sessions:**

```
# At session start
/second-brain daily-plan

# After completing a task
/second-brain capture "Implemented 3-layer progressive disclosure for findings search. Token savings confirmed: 3K vs 35K."
```

**Consolidation (weekly or on-demand):**

```
# Process accumulated inbox items
/second-brain process-inbox

# Items get routed to:
# - Obsidian vault notes (knowledge)
# - GitHub Issues (actions)
# - Auto memory entries (preferences/learnings)
# - NotebookLM sources (research)
```

---

## 4. File formats and locations for persistent findings

### Anthropic's recommendation: JSON for structured state, markdown for prose

From the long-running agents article, Anthropic explicitly recommends JSON for structured task tracking:

> "After some experimentation, we landed on using JSON for this, as **the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files.**"

This was specifically about feature lists and progress tracking. The key finding is that LLMs treat JSON as more "sacred" -- they are less likely to accidentally modify or corrupt structured JSON than they are to rewrite markdown.

### Recommended format matrix

| Content Type | Format | Location | Rationale |
|-------------|--------|----------|-----------|
| Research findings (provenance) | YAML | `docs/research/trail/findings/*.yaml` | Structured but human-readable, already established |
| Deep reviews (analysis) | Markdown | `docs/research/trail/deep-reviews/*.md` | Prose-heavy, benefits from headers/links |
| Task/feature state | JSON | `docs/research/trail/scorecards/*.yaml` | But JSON preferred per Anthropic for machine state |
| Source catalog | Markdown | `docs/research/source-catalog.md` | Discovery log, append-only |
| Session learnings | Markdown | `~/.claude/projects/*/memory/*.md` | Auto memory format, Claude Code native |
| Progress tracking | Plain text | `claude-progress.txt` (if using SDK pattern) | Anthropic's recommended pattern |

### Why YAML works for this project despite Anthropic's JSON recommendation

The project already uses YAML for provenance records (`docs/research/trail/findings/*.yaml`). YAML is appropriate here because:

1. These records are written once and rarely modified (append-only pattern)
2. They are human-reviewed as part of the research pipeline
3. YAML supports comments, which are useful for provenance annotation
4. The schema is simple and stable (id, timestamp, source, confidence, etc.)

However, for anything that agents modify repeatedly (task lists, progress tracking, feature completion), JSON should be preferred per Anthropic's finding.

### The 200-line limit for CLAUDE.md and auto memory

From the Claude Code memory docs:

> Auto memory loads "Every session (first 200 lines)."
> CLAUDE.md: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."

This means:
- Auto memory MEMORY.md should remain a concise index (currently 24 lines, well within limit)
- Individual memory files should be focused and brief (current ones range 700-2700 bytes, appropriate)
- Deep research content must NOT go into auto memory -- it goes into repo files

### File location hierarchy

```
# AUTO MEMORY (session-scoped, loaded every conversation)
~/.claude/projects/<project>/memory/
  MEMORY.md                              # Index file, <200 lines
  feedback_*.md                          # User corrections
  project_*.md                           # Project facts
  reference_*.md                         # Technical references
  user_*.md                              # User preferences

# REPO PERSISTENCE (git-tracked, shared, permanent)
docs/research/
  source-catalog.md                      # All discovered URLs
  trail/
    findings/*.yaml                      # Individual provenance records
    deep-reviews/*.md                    # Comprehensive analysis documents
    scorecards/*.yaml                    # Quantified improvement metrics

# OBSIDIAN VAULT (local, knowledge graph)
~/Obsidian/                              # Or configured vault location
  Inbox/                                 # Second-brain capture target
  Projects/                              # Active project notes
  References/                            # Permanent reference material

# NOTEBOOKLM (cloud, cross-source synthesis)
# Not file-based -- accessed via CLI
notebooklm use <id>
notebooklm source add <file-or-url>
```

---

## 5. How the consolidation step should work

### The problem: scattered notes need synthesis

Agents write notes in many places during a session:
- Auto memory files
- YAML provenance records
- Progress tracking files
- Git commit messages
- Inline code comments

Without consolidation, knowledge remains fragmented and future agents cannot efficiently retrieve it.

### Three-phase consolidation model

**Phase 1: Intra-session (continuous, automatic)**

Each agent writes findings to the appropriate tier immediately:
- Quick learnings -> auto memory
- Research findings -> YAML provenance in `docs/research/trail/findings/`
- Detailed analysis -> markdown deep review in `docs/research/trail/deep-reviews/`

**Phase 2: Cross-session (on-demand, human-triggered)**

A consolidation agent (or the user via `/second-brain process-inbox`) reads all accumulated notes and:

1. **Deduplicates** -- identifies findings that multiple agents discovered independently
2. **Cross-references** -- links related findings (e.g., "finding X confirms finding Y")
3. **Updates source catalog** -- ensures all discovered URLs are in `docs/research/source-catalog.md`
4. **Ingests into NotebookLM** -- adds new deep reviews and key findings as sources
5. **Generates synthesis** -- asks NotebookLM cross-source questions to find patterns

```bash
# Example consolidation workflow
cd /Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment

# 1. Find new findings since last consolidation
git log --oneline --since="2026-03-19" -- docs/research/trail/

# 2. Ingest new findings into NotebookLM
notebooklm use <research-notebook-id>
for f in docs/research/trail/findings/finding-*.yaml; do
  notebooklm source add "$f"
done
notebooklm source add docs/research/trail/deep-reviews/agent-note-persistence-infrastructure.md

# 3. Generate cross-source synthesis
notebooklm ask "What are the top 5 actionable patterns across all recent findings?" --citations
notebooklm history --save-as-note

# 4. Update improvement score
uv run mde-py research score
```

**Phase 3: Periodic deep review (weekly/milestone)**

A human or orchestrator agent:

1. Reads the NotebookLM synthesis notes
2. Reviews the improvement score trend
3. Updates `.claude/rules/` if new patterns are established
4. Archives completed research into Obsidian vault
5. Prunes stale auto memory entries

### Who does consolidation

| Phase | Actor | Trigger |
|-------|-------|---------|
| Intra-session | Working agent | Continuous during work |
| Cross-session | Consolidation agent or user | `uv run mde-py research status` shows new unprocessed findings |
| Deep review | User + NotebookLM | Weekly, or after research cycle completes |

---

## 6. Tools and services we should be using but aren't

### Already in use (confirmed working)

| Tool | Status | Purpose |
|------|--------|---------|
| Claude Code auto memory | Active | `~/.claude/projects/*/memory/` |
| NotebookLM CLI | Installed | `notebooklm` via mise |
| agent-fetch | Installed | Full URL fetching for research |
| YAML provenance records | Active | `docs/research/trail/findings/` |
| `.claude/rules/` | Active | Persistent project instructions |

### Not yet using but should adopt

**1. Claude Developer Platform Memory Tool (`memory_20250818`)**

The memory tool API enables agents built on the Claude API (not just Claude Code) to have persistent file-based memory. Key features:

- **Commands**: `view`, `create`, `str_replace`, `insert`, `delete`, `rename`
- **Client-side execution**: you control the storage backend
- **Automatic checking**: Claude checks `/memories` directory before starting tasks
- **Supported on**: Opus 4.6, Opus 4.5, Opus 4.1, Opus 4, Sonnet 4.6, Sonnet 4.5, Sonnet 4, Haiku 4.5

This matters for any custom agent built with the Claude SDK. The API exposes the same pattern Claude Code uses internally but makes it programmable.

**Adoption path:** If building custom agents via the Claude Agent SDK, enable the memory tool:
```json
{
  "tools": [{
    "type": "memory_20250818",
    "name": "memory"
  }]
}
```

**2. Claude Code native subagent memory**

From the Claude Code docs: "Subagents can also maintain their own auto memory." This means research subagents can persist what they learn across sessions without coordination from the parent agent.

**Adoption path:** Create `.claude/agents/researcher.md` with `persistent_memory: true` to enable subagent-specific memory.

**3. NotebookLM `source add-research` for automated web research**

```bash
notebooklm source add-research "agent memory persistence patterns 2025"
```

This automatically searches the web and adds the results as a notebook source. We are currently using `agent-fetch` for URL content but not leveraging NotebookLM's built-in research ingestion.

**Adoption path:** Use `add-research` for broad topic surveys, `agent-fetch` + `source add` for specific known URLs.

**4. NotebookLM `source guide` for automatic study guides**

```bash
notebooklm source guide <source-id>
```

Generates a structured study guide from any source. This could automate the creation of deep reviews from raw sources.

**5. Anthropic's `claude-progress.txt` + `feature_list.json` pattern**

From the long-running agents article, this two-file pattern solved the "agent declares victory early" and "agent doesn't know what happened" problems:

- `claude-progress.txt` -- plain text log of what each agent session accomplished
- `feature_list.json` -- structured JSON with feature descriptions and pass/fail status

**Adoption path for research:** Adapt this as `docs/research/research-progress.txt` (session log) + improve the existing scorecard YAML to include per-finding pass/fail tracking.

**6. Compaction-aware note-taking hooks**

Claude Code fires hooks before compaction. A pre-compaction hook could automatically:
1. Write all in-context findings to disk
2. Update the progress file
3. Ensure no knowledge exists only in the context window

From the Claude Code docs, the relevant hook events include `SubagentStart`, `SubagentStop`, `TaskCompleted`. A `PreCompaction` hook would need to be implemented or simulated.

**7. Git history as implicit memory**

The long-running agents article emphasizes git as a memory mechanism:

> "we found that the best way to elicit this behavior was to ask the model to commit its progress to git with descriptive commit messages and to write summaries of its progress in a progress file."

Agents should read `git log --oneline -20` at session start and write descriptive commits at each milestone. We do this for code but not systematically for research.

---

## 7. Architectural patterns: putting it all together

### The just-in-time retrieval pattern (from context engineering)

From Anthropic:

> "Rather than pre-processing all relevant data up front, agents built with the 'just in time' approach maintain lightweight identifiers (file paths, stored queries, web links, etc.) and use these references to dynamically load data into context at runtime using tools."

This means auto memory should be an **index of pointers**, not a store of content. The MEMORY.md file already follows this pattern -- it's a list of links to individual files, not a monolithic knowledge dump.

### The 3-layer progressive disclosure pattern (from finding-claude-mem-3layer)

Adapted from the claude-mem analysis:

| Layer | Token Cost | What It Contains |
|-------|-----------|-----------------|
| Index | ~100 tokens/result | File paths, titles, confidence levels, tags |
| Context | ~500 tokens | Finding summary, implication, status |
| Full detail | ~500-1000 tokens | Complete provenance record with evidence |

Agents should search the index first, load context for relevant hits, and only read full details when needed. This achieves ~10x token savings vs loading everything.

**Implementation for this project:**

```
# Layer 1: Index (always loaded via auto memory MEMORY.md)
~/.claude/projects/*/memory/MEMORY.md     # ~24 lines, links to details

# Layer 2: Context (loaded on demand by file path)
docs/research/trail/findings/*.yaml       # ~10-15 lines each, structured
~/.claude/projects/*/memory/*.md           # ~10-30 lines each

# Layer 3: Full detail (loaded only when needed)
docs/research/trail/deep-reviews/*.md      # 100-500+ lines, comprehensive
docs/research/source-catalog.md            # Full URL catalog
```

### The initializer/worker agent pattern (from long-running agents)

Anthropic recommends two distinct agent roles:

1. **Initializer agent** -- runs once to set up the environment:
   - Creates the progress file
   - Generates the feature/task list
   - Makes an initial git commit
   - Writes `init.sh` for environment setup

2. **Worker agent** -- runs in every subsequent session:
   - Reads progress file and git log at start
   - Picks one task from the list
   - Works on it incrementally
   - Commits progress and updates progress file
   - Leaves environment in a clean state

**Adapted for research:**

1. **Research initializer** -- creates the research plan, populates the source catalog, creates the NotebookLM notebook
2. **Research worker** -- picks one source or question, investigates it, writes findings to YAML, updates the source catalog

### The hybrid retrieval pattern (from context engineering)

> "Claude Code is an agent that employs this hybrid model: CLAUDE.md files are naively dropped into context up front, while primitives like glob and grep allow it to navigate its environment and retrieve files just-in-time."

For agent note persistence, this means:

- **Up-front** (always loaded): MEMORY.md index, `.claude/rules/` policy files
- **Just-in-time** (loaded when relevant): Individual findings YAML, deep reviews, source catalog
- **On-demand synthesis** (queried when needed): NotebookLM cross-source Q&A

---

## 8. Specific configuration and command reference

### Claude Code auto memory configuration

Auto memory is enabled by default. Configuration via settings:

```bash
# Check current auto memory state
cat ~/.claude/projects/<project-hash>/memory/MEMORY.md

# Auto memory writes are triggered by:
# 1. User corrections ("actually, do it this way...")
# 2. Explicit "remember this" instructions
# 3. Pattern discovery during work
```

Key constraints:
- First 200 lines of MEMORY.md loaded every session
- Individual files loaded via the index links in MEMORY.md
- Scope is per working tree (git worktrees get separate memory)
- Files are plain markdown with YAML frontmatter

### NotebookLM CLI full reference

```bash
# Setup
notebooklm login
notebooklm --storage ~/.notebooklm/storage_state.json

# Create project notebook
notebooklm create "MDE Agent Infrastructure Research"
notebooklm use <id>

# Ingest sources
notebooklm source add docs/research/trail/deep-reviews/agent-note-persistence-infrastructure.md
notebooklm source add "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"
notebooklm source add-research "agent memory patterns structured note-taking"
notebooklm source wait <source-id>

# Query across sources
notebooklm ask "What file format does Anthropic recommend for agent state and why?" --citations
notebooklm ask "Compare all note persistence patterns discovered so far"

# Maintain
notebooklm source stale                 # Find outdated sources
notebooklm source refresh <id>          # Re-fetch URL sources
notebooklm summary                      # Get notebook overview

# Export
notebooklm history --save-as-note       # Save Q&A as notebook note
```

### Provenance YAML template

```yaml
id: finding-<descriptive-slug>
timestamp: "2026-03-20T20:00:00Z"
source: <url-or-file-path>
agent: <agent-id-that-discovered-this>
finding_type: technique|architecture|tool|pattern|anti-pattern
confidence: confirmed|likely|speculative
confident_about: "<one-paragraph summary of what was confirmed>"
gaps: "<what remains unknown or unverified>"
evidence: "<specific quotes or data points supporting the finding>"
implication: "<what this means for the project, actionable next steps>"
status: discovered|validated|implemented|superseded
tags:
  - tag1
  - tag2
coverage_assessment: full_review|partial_review|title_only
```

### Git-as-memory commands (for agent session protocol)

```bash
# At session start
git log --oneline -20                    # Understand recent work
cat docs/research/trail/findings/ | wc -l  # Count findings

# At each milestone
git add docs/research/trail/findings/finding-<name>.yaml
git commit -m "research: discover <finding-name> from <source>"

# At session end
git add docs/research/
git commit -m "research: session summary -- <what was accomplished>"
```

---

## 9. Anti-patterns to avoid

### 1. Using opaque key-value stores for memory

From `feedback_second_brain_memory.md`:
> "Do NOT use `npx @claude-flow/cli@latest memory store/search/retrieve` for memory operations."

Why: opaque CLI stores don't integrate with the knowledge ecosystem, aren't human-readable, and don't survive tool changes.

### 2. Writing notes only at session end

If the session dies mid-work, everything in context is lost. Write findings to files as they are discovered, not as a batch at the end.

### 3. Putting research content in auto memory

Auto memory has a 200-line budget and is loaded every session. Deep research content wastes this budget. Use auto memory for pointers and preferences, repo files for content.

### 4. One notebook per session in NotebookLM

Creates sprawl and prevents cross-session synthesis. Use one notebook per research domain, add sources incrementally.

### 5. Markdown for structured agent state that gets modified repeatedly

From Anthropic: "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files." Use JSON for pass/fail tracking, task lists, and any state that agents modify in-place.

### 6. Loading all findings into context at once

The 3-layer progressive disclosure pattern (index -> context -> full) achieves ~10x token savings. Never load all findings into context; search the index first.

---

## 10. Implementation checklist

For a future agent implementing this system:

- [ ] Auto memory MEMORY.md serves as a pointer index (<200 lines)
- [ ] Research findings go to `docs/research/trail/findings/*.yaml` immediately upon discovery
- [ ] Deep reviews go to `docs/research/trail/deep-reviews/*.md`
- [ ] All discovered URLs logged in `docs/research/source-catalog.md`
- [ ] NotebookLM notebook exists per research domain (not per session)
- [ ] New findings ingested into NotebookLM via `notebooklm source add`
- [ ] Cross-source synthesis queries via `notebooklm ask --citations`
- [ ] Git commits at each research milestone with descriptive messages
- [ ] JSON used for any structured state that agents modify repeatedly
- [ ] YAML used for append-only provenance records
- [ ] Second-brain skill used for capture/process/closeout workflow
- [ ] Pre-compaction writes implemented (write to disk before context fills)
- [ ] 3-layer progressive disclosure: index -> context -> full detail
- [ ] Agent reads `git log --oneline -20` at session start
- [ ] No opaque key-value stores; all memory is file-based and human-readable
