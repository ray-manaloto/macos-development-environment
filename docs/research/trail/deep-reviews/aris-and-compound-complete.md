# ARIS and Compound Plugins: Complete Deep Review

**Date:** 2026-03-20
**Sources:**
- https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep (cloned)
- https://github.com/EveryInc/compound-engineering-plugin (cloned)
- https://github.com/EveryInc/compound-knowledge-plugin (cloned)

---

## Part 1: ARIS (Auto-claude-code-Research-In-Sleep)

### 1.1 Philosophy and Architecture

ARIS is a **zero-dependency, plain-Markdown skill system** for autonomous ML research. The entire system is `SKILL.md` files with no framework, no database, no Docker, no daemon. Skills are readable by any LLM and portable across Claude Code, Codex CLI, OpenClaw, Cursor, Trae, Antigravity, and Windsurf.

**Core design thesis:** Cross-model collaboration beats self-play. Claude Code executes research; an external LLM (GPT-5.4 via Codex MCP) acts as adversarial reviewer. The rationale is that a single model reviewing itself falls into local minima (stochastic bandits), while cross-model review is adversarial (probes weaknesses the executor did not anticipate). Two models is the minimum to break blind spots; adding more has diminishing returns.

**Cross-model pattern:** Claude Code calls `mcp__codex__codex` for the first review (returns a `threadId`), then `mcp__codex__codex-reply` with the saved `threadId` for subsequent rounds in the same thread. Always uses `config: {"model_reasoning_effort": "xhigh"}` for maximum reasoning depth. The reviewer model defaults to `gpt-5.4`.

### 1.2 Complete Skill Inventory (31 Skills)

#### Core Research Skills (19)
| # | Skill | Purpose |
|---|-------|---------|
| 1 | `research-lit` | Multi-source literature review (Zotero + Obsidian + local PDFs + arXiv/Scholar) |
| 2 | `idea-creator` | Generate 8-12 research ideas, filter, pilot on GPUs, rank by empirical signal |
| 3 | `novelty-check` | Multi-source + cross-model novelty verification for research ideas |
| 4 | `research-review` | Deep critical review via GPT-5.4 xhigh with iterative dialogue |
| 5 | `research-refine` | Turn vague direction into problem-anchored, frontier-aware method plan (up to 5 rounds, score >= 9) |
| 6 | `experiment-plan` | Claim-driven experiment roadmap with ablations, budgets, run order |
| 7 | `research-refine-pipeline` | One-shot chain: research-refine then experiment-plan |
| 8 | `idea-discovery` | Workflow 1 orchestrator: research-lit -> idea-creator -> novelty-check -> research-review -> research-refine-pipeline |
| 9 | `experiment-bridge` | Workflow 1.5: implement experiment code, GPT-5.4 code review, deploy to GPU, collect results |
| 10 | `run-experiment` | Deploy experiments to local/remote GPU servers via SSH + screen |
| 11 | `monitor-experiment` | Check running experiments, collect screen output, pull W&B metrics |
| 12 | `analyze-results` | Statistical analysis of experiment results, comparison tables |
| 13 | `auto-review-loop` | Workflow 2: 4-round autonomous review->fix->re-review via Codex MCP |
| 14 | `auto-review-loop-llm` | Same as auto-review-loop but using any OpenAI-compatible API via llm-chat MCP |
| 15 | `auto-review-loop-minimax` | Same as auto-review-loop but using MiniMax API |
| 16 | `research-pipeline` | Full pipeline: idea-discovery -> implement -> run-experiment -> auto-review-loop |
| 17 | `paper-plan` | Generate structured paper outline from review conclusions and results |
| 18 | `paper-write` | Draft LaTeX paper section by section, with anti-hallucination DBLP/CrossRef citations |
| 19 | `paper-compile` | Compile LaTeX to PDF, fix errors, verify output |

#### Paper Enhancement Skills (4)
| # | Skill | Purpose |
|---|-------|---------|
| 20 | `paper-figure` | Generate publication-quality matplotlib plots and LaTeX tables |
| 21 | `paper-illustration` | AI-generated architecture diagrams via Claude planning + Gemini rendering |
| 22 | `auto-paper-improvement-loop` | 2-round paper writing quality improvement (4/10 -> 8.5/10) |
| 23 | `paper-writing` | Workflow 3 orchestrator: paper-plan -> paper-figure -> paper-write -> paper-compile -> auto-paper-improvement-loop |

#### Utility and Presentation Skills (5)
| # | Skill | Purpose |
|---|-------|---------|
| 24 | `arxiv` | Search, download, and summarize arXiv papers |
| 25 | `feishu-notify` | Feishu/Lark notifications (off/push/interactive modes) |
| 26 | `mermaid-diagram` | Generate Mermaid diagrams (20+ types) |
| 27 | `pixel-art` | Generate pixel art SVG illustrations |
| 28 | `paper-poster` | Conference poster (tcbposter LaTeX -> A0/A1 PDF + PPTX + SVG) |
| 29 | `paper-slides` | Conference presentation slides (beamer -> PDF + PPTX) with speaker notes |

#### Domain-Specific Skills (3)
| # | Skill | Purpose |
|---|-------|---------|
| 30 | `idea-discovery-robot` | Robotics-specific idea discovery with embodiment/sim2real constraints |
| 31 | `comm-lit-review` | Communications-domain literature review (IEEE/ACM/ScienceDirect priority) |

#### Theory Skills (3 -- included in the 31 count above depending on how you count)
| Skill | Purpose |
|-------|---------|
| `formula-derivation` | Research formula development and verification |
| `proof-writer` | Rigorous theorem/lemma proof drafting |
| `grant-proposal` | Grant proposal drafting for 9 agencies (KAKENHI, NSF, NSFC, ERC, DFG, SNSF, ARC, NWO, generic) |
| `dse-loop` | Autonomous design space exploration for computer architecture/EDA |

### 1.3 REVIEW_STATE.json Schema

This is the state persistence file written after every Phase E of the auto-review loop. It survives context window compaction.

```json
{
  "round": 2,
  "threadId": "019cd392-...",
  "status": "in_progress",
  "last_score": 5.0,
  "last_verdict": "not ready",
  "pending_experiments": ["screen_name_1"],
  "timestamp": "2026-03-13T21:00:00"
}
```

**Fields:**
- `round` (integer): Current round number (1-based)
- `threadId` (string): Codex MCP thread ID for conversation continuity. Saved from the first `mcp__codex__codex` call, used in all subsequent `mcp__codex__codex-reply` calls. Not present in the LLM/MiniMax variants (those use standalone API calls per round).
- `status` (string): `"in_progress"` or `"completed"`
- `last_score` (float): Numeric score 1-10 from the reviewer
- `last_verdict` (string): `"ready"` / `"almost"` / `"not ready"`
- `pending_experiments` (array of strings): Screen session names for experiments still running
- `timestamp` (string): ISO 8601 timestamp of last write

**Recovery logic on initialization:**
1. If file does not exist: **fresh start**
2. If exists AND `status` is `"completed"`: **fresh start** (previous loop finished)
3. If exists AND `status` is `"in_progress"` AND `timestamp` older than 24 hours: **fresh start** (stale state from killed/abandoned run -- delete file and start over)
4. If exists AND `status` is `"in_progress"` AND `timestamp` within 24 hours: **resume**
   - Read state to recover `round`, `threadId`, `last_score`, `pending_experiments`
   - Read `AUTO_REVIEW.md` to restore full context of prior rounds
   - If `pending_experiments` is non-empty, check if screen sessions have completed
   - Resume from `round + 1`
   - Log: "Recovered from context compaction. Resuming at Round N."

**On completion:** Set `"status": "completed"` so future invocations do not accidentally resume.

The `auto-paper-improvement-loop` uses a similar file called `PAPER_IMPROVEMENT_STATE.json` with the same schema minus `pending_experiments` and with field name `current_round` instead of `round`.

### 1.4 AUTO_REVIEW.md Cumulative Log Format

This is the append-only review log, written to the project root.

**Header (created on initialization):**
```markdown
# Auto Review Log
**Topic**: [topic]
**Started**: [timestamp]
**Pipeline**: auto-review-loop
```

**Per-round entry (appended in Phase E):**
```markdown
## Round N (timestamp)

### Assessment (Summary)
- Score: X/10
- Verdict: [ready/almost/not ready]
- Key criticisms: [bullet list]

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

[Paste the COMPLETE raw response from the external reviewer here -- verbatim, unedited.
This is the authoritative record. Do NOT truncate or paraphrase.]

</details>

### Actions Taken
- [what was implemented/changed]

### Results
- [experiment outcomes, if any]

### Status
- [continuing to round N+1 / stopping]
```

**Termination section:**
```markdown
## Method Description
[1-2 paragraph description of the final method, architecture, and data flow.
Serves as input for /paper-illustration in Workflow 3.]
```

**Key rule:** The FULL raw response from the external reviewer must be saved verbatim in a `<details>` block. This is the primary record. Never truncate or paraphrase.

### 1.5 AUTO_PROCEED Gate Logic

The `AUTO_PROCEED` constant (default: `true`) controls behavior at human checkpoints. It is used in `research-pipeline` and `idea-discovery`.

**Gate 1 (After Idea Discovery in research-pipeline):**
- If `AUTO_PROCEED=false`: Wait for explicit user confirmation. The user can approve an idea, pick a different idea, request changes, reject all ideas, or stop.
- If `AUTO_PROCEED=true`: Present the top ideas, wait 10 seconds for user input. If no response, auto-select the #1 ranked idea (highest pilot signal + novelty confirmed) and proceed. Log: `"AUTO_PROCEED: selected Idea 1 -- [title]"`.

**Checkpoints in idea-discovery (at each phase transition):**
- After Phase 1 (Literature Survey): Present landscape summary, ask if scope needs adjusting
- After Phase 2 (Idea Generation): Present ranked ideas, ask which to validate further
- After Phase 4.5 (Method Refinement): Present refined proposal summary
- If `AUTO_PROCEED=true` and no user response: proceed with best option

**HUMAN_CHECKPOINT (separate from AUTO_PROCEED):**
When `HUMAN_CHECKPOINT=true`, the auto-review loops pause after each round's review (Phase B) and present:
```
Round N/MAX_ROUNDS review complete.
Score: X/10 -- [verdict]
Top weaknesses: [list]
Suggested fixes: [list]
Options:
- Reply "go" -> implement all suggested fixes
- Reply with custom instructions -> implement your modifications
- Reply "skip 2" -> skip fix #2, implement the rest
- Reply "stop" -> end the loop
```

### 1.6 Cross-Model Review Pattern

**MCP commands used:**

First review (Round 1):
```
mcp__codex__codex:
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N/MAX_ROUNDS of autonomous review loop]
    [Full research context]
    Please act as a senior ML reviewer (NeurIPS/ICML level).
    1. Score this work 1-10 for a top venue
    2. List remaining critical weaknesses (ranked by severity)
    3. For each weakness, specify the MINIMUM fix
    4. State clearly: is this READY for submission? Yes/No/Almost
```

Subsequent reviews (Round 2+):
```
mcp__codex__codex-reply:
  threadId: [saved from round 1]
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N update]
    Since your last review, we have:
    1. [Action 1]: [result]
    2. [Action 2]: [result]
    Updated results table: [paste metrics]
    Please re-score and re-assess.
```

**ThreadId persistence:** The `threadId` is saved from the first `mcp__codex__codex` call and reused for all subsequent `mcp__codex__codex-reply` calls within the same loop. It is also persisted in `REVIEW_STATE.json` for recovery after context compaction.

**Alternative LLM variant:** The `auto-review-loop-llm` skill uses `mcp__llm-chat__chat` instead, with configurable `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`. Falls back to `curl` if MCP is unavailable. Supports DeepSeek, MiniMax, Kimi, ZhiPu, SiliconFlow, and more.

**Alternative MiniMax variant:** Uses `mcp__minimax-chat__minimax_chat` or direct curl to `https://api.minimax.chat/v1/chat/completions`. Each round is a standalone API call (no thread persistence).

### 1.7 Safety Guardrails

**MAX_ROUNDS:**
- `auto-review-loop`: MAX_ROUNDS = 4
- `auto-paper-improvement-loop`: MAX_ROUNDS = 2
- `research-refine`: MAX_ROUNDS = 5 (score threshold = 9)

**GPU hour limits (idea-discovery):**
- `PILOT_MAX_HOURS = 2` -- skip any pilot estimated > 2 hours per GPU
- `PILOT_TIMEOUT_HOURS = 3` -- hard timeout, kill running pilot after 3 hours
- `MAX_PILOT_IDEAS = 3` -- pilot at most 3 ideas in parallel
- `MAX_TOTAL_GPU_HOURS = 8` -- total GPU budget across all pilots

**Budget awareness (research-pipeline):**
- Track total GPU-hours across the pipeline
- Flag if approaching user-defined limits

**Anti-gaming rules:**
- "Do NOT hide weaknesses to game a positive score"
- "Be honest -- include negative results and failed experiments"
- "Implement fixes BEFORE re-reviewing (don't just promise to fix)"
- "Do not fabricate experimental results"
- "If an experiment takes > 30 minutes, launch it and continue with other fixes while waiting"

**Fix prioritization rules:**
- Skip fixes requiring excessive compute (flag for manual follow-up)
- Skip fixes requiring external data/models not available
- Prefer reframing/analysis over new experiments when both address the concern
- Always implement metric additions (cheap, high impact)

**DSE-loop specific safety:**
- NEVER sudo anything
- NEVER rm -rf or recursive deletion
- NEVER rm files not created in this session
- NEVER overwrite existing source files without reading first
- NEVER git push, git reset --hard, or destructive git operations
- NEVER kill processes not started by the skill

### 1.8 The Four Workflows (Step-by-Step)

#### Workflow 1: Idea Discovery (`/idea-discovery`)

```
/research-lit -> /idea-creator -> /novelty-check -> /research-review -> /research-refine-pipeline
```

**Phase 1 -- Literature Survey (`/research-lit`):**
1. Check Zotero MCP (if available): search by topic, read collections, extract annotations/highlights, export BibTeX
2. Check Obsidian MCP (if available): search vault, check tags, read research notes, follow wikilinks
3. Scan local PDFs: check `papers/` and `literature/` directories, read first 3 pages of relevant papers
4. External search: WebSearch for arXiv, Semantic Scholar, Google Scholar; optionally use `arxiv_fetch.py` for structured API results
5. Optional PDF download: when `ARXIV_DOWNLOAD=true`, download top N papers with 1-second rate limiting
6. Analyze each paper: extract problem, method, results, relevance, source
7. Synthesize: group by approach/theme, identify consensus vs disagreements, find gaps
8. Output: structured literature table + narrative summary

**Checkpoint:** Present landscape summary, ask if scope needs adjusting.

**Phase 2 -- Idea Generation + Filtering + Pilots (`/idea-creator`):**
1. Scan local paper library (first 3 pages of relevant papers)
2. Search recent literature (5+ query formulations, top 10-15 papers)
3. Build landscape map and identify structural gaps
4. Brainstorm 8-12 ideas via GPT-5.4 xhigh (codex MCP with threadId)
5. First-pass filter: feasibility check (GPU-hours, data availability), novelty quick-check (2-3 searches), impact estimation
6. Deep validation: full `/novelty-check` + GPT-5.4 devil's advocate review for survivors
7. Parallel pilot experiments: design minimal experiments (30 min - 2 hours), deploy on different GPUs, collect results
8. Re-rank based on empirical evidence
9. Output: `IDEA_REPORT.md` with ranked ideas, pilot results, eliminated ideas

**Checkpoint:** Present ranked ideas, ask which to validate further.

**Phase 3 -- Deep Novelty Verification (`/novelty-check`):**
1. Extract 3-5 core technical claims
2. Multi-source search: WebSearch (arXiv, Scholar, Semantic Scholar), 3+ query formulations per claim, year filters 2024-2026
3. Cross-model verification: GPT-5.4 xhigh via codex MCP
4. Output: Novelty report with per-claim novelty rating, closest prior work table, overall assessment

**Phase 4 -- External Critical Review (`/research-review`):**
1. Gather research context (narrative docs, memory files, experiment history)
2. Send to GPT-5.4 xhigh: score, weaknesses, missing experiments, narrative weaknesses
3. Iterative dialogue using threadId: respond to criticisms, ask targeted follow-ups
4. Document everything: round-by-round summary, claims matrix, prioritized TODOs

**Phase 4.5 -- Method Refinement + Experiment Planning (`/research-refine-pipeline`):**
1. Freeze Problem Anchor (immutable bottom-line problem, must-solve bottleneck, non-goals, constraints, success condition)
2. Build initial proposal: scan grounding material, identify technical gap, choose sharpest route, concretize method, design minimal claim-driven validation
3. External review via GPT-5.4: score 7 dimensions (Problem Fidelity 15%, Method Specificity 25%, Contribution Quality 25%, Frontier Leverage 15%, Feasibility 10%, Validation Focus 5%, Venue Readiness 5%)
4. Parse feedback, run anchor check + simplicity check, revise method
5. Re-evaluate in same thread, repeat until score >= 9 or 5 rounds
6. Generate experiment plan with claim-driven blocks, run order, milestones

**Checkpoint:** Present refined proposal summary.

**Phase 5 -- Final Report:**
Write `IDEA_REPORT.md` with executive summary, landscape, ranked ideas, refined proposal references, next steps.

#### Workflow 1.5: Experiment Bridge (`/experiment-bridge`)

```
refine-logs/EXPERIMENT_PLAN.md -> implement code -> GPT-5.4 code review -> deploy -> collect results
```

1. Read experiment plan and proposal
2. Implement experiment code following the plan (sanity stage first if `SANITY_FIRST=true`)
3. GPT-5.4 code review before deployment (if `CODE_REVIEW=true`): catches logic bugs before wasting GPU hours
4. Deploy via `/run-experiment` (up to `MAX_PARALLEL_RUNS=4` in parallel)
5. Monitor and collect initial results
6. Update experiment tracker

#### Workflow 2: Auto Review Loop (`/auto-review-loop`)

```
review -> implement fixes -> re-review (up to 4 rounds)
```

**Initialization:**
1. Check REVIEW_STATE.json for recovery (see 1.3 above)
2. Read project narrative, memory files, prior review documents
3. Read recent experiment results
4. Identify current weaknesses and open TODOs
5. Initialize round counter
6. Create/update AUTO_REVIEW.md

**Loop (up to MAX_ROUNDS=4):**

Phase A -- Review: Send comprehensive context to GPT-5.4 xhigh via codex MCP (or codex-reply with threadId for round 2+).

Phase B -- Parse Assessment: Save FULL raw response verbatim. Extract score (1-10), verdict (ready/almost/not ready), action items. Stop if score >= 6 AND verdict contains "ready" or "almost".

Human Checkpoint (if `HUMAN_CHECKPOINT=true`): Present score + weaknesses, wait for user input (go/custom instructions/skip/stop).

Feishu Notification (if configured): Send review_scored notification.

Phase C -- Implement Fixes: For each action item (highest priority first): code changes, run experiments, analysis, documentation. Apply prioritization rules.

Phase D -- Wait for Results: Monitor remote sessions, collect results from output files and logs.

Phase E -- Document Round: Append to AUTO_REVIEW.md (full format in section 1.4). Write REVIEW_STATE.json.

**Termination:**
1. Update REVIEW_STATE.json with `"status": "completed"`
2. Write final summary to AUTO_REVIEW.md
3. Write method/pipeline description (input for paper-illustration)
4. If stopped at max rounds without positive assessment: list remaining blockers, estimate effort, suggest continue vs pivot
5. Feishu pipeline_done notification

#### Workflow 3: Paper Writing (`/paper-writing`)

```
/paper-plan -> /paper-figure -> /paper-write -> /paper-compile -> /auto-paper-improvement-loop
```

**Phase 1 -- Paper Plan (`/paper-plan`):**
1. Extract claims and evidence from narrative documents
2. Build Claims-Evidence Matrix
3. Design figure plan and section plan
4. GPT-5.4 reviews the outline
5. Output: `PAPER_PLAN.md` with section-by-section structure

**Phase 2 -- Paper Figure (`/paper-figure`):**
1. Read figure plan from PAPER_PLAN.md
2. Generate data-driven plots (matplotlib, publication style, 300 DPI PDF)
3. Generate LaTeX comparison tables
4. GPT-5.4 reviews figure quality
5. Output: `figures/*.pdf` + `figures/latex_includes.tex`

**Phase 3 -- Paper Write (`/paper-write`):**
1. Read PAPER_PLAN.md and NARRATIVE_REPORT.md
2. Draft LaTeX section by section using venue-specific templates (ICLR 2026, NeurIPS 2025, ICML 2025)
3. Anti-hallucination citations: fetch real BibTeX from DBLP/CrossRef (default on)
4. GPT-5.4 reviews each section
5. Output: `paper/sections/*.tex` + `paper/references.bib`

**Phase 4 -- Paper Compile (`/paper-compile`):**
1. Verify prerequisites (pdflatex, latexmk, bibtex)
2. Compile with `latexmk -pdf`
3. Fix errors (up to 3 attempts)
4. Verify: 0 undefined references, 0 undefined citations
5. Output: `paper/main.pdf`

**Phase 5 -- Auto Paper Improvement (`/auto-paper-improvement-loop`):**
1. Preserve original as `main_round0_original.pdf`
2. Concatenate all section files
3. Round 1: GPT-5.4 xhigh review (score, strengths, weaknesses with severity), implement fixes (CRITICAL > MAJOR > MINOR), recompile
4. Round 2: GPT-5.4 xhigh re-review in same thread, implement fixes, recompile
5. Format check: page count, overfull hbox, underfull hbox, auto-fix
6. Output: `PAPER_IMPROVEMENT_LOG.md` with score progression table + all raw reviews

**Typical score progression:** Round 0: 4/10 -> Round 1: 6/10 -> Round 2: 7/10 -> Format fix: 8.5/10 (+4.5 points across 3 rounds)

### 1.9 Feishu/Lark Integration

**Configuration:** `~/.claude/feishu.json`
```json
{
  "mode": "push",
  "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID",
  "interactive": {
    "bridge_url": "http://localhost:5000",
    "timeout_seconds": 300
  }
}
```

**Three modes:**
- `"off"` or file absent: nothing happens (zero-impact guarantee)
- `"push"`: send webhook notifications at key events (mobile push, no reply)
- `"interactive"`: full bidirectional via feishu-claude-code bridge

**Notification types:** `experiment_done`, `review_scored`, `checkpoint`, `pipeline_done`, `error`

### 1.10 MCP Servers

ARIS includes 4 MCP servers in `mcp-servers/`:

1. **claude-review**: Local bridge so Codex CLI can use Claude as reviewer (reverse direction)
2. **feishu-bridge**: Bidirectional Feishu/Lark integration
3. **llm-chat**: Generic OpenAI-compatible API wrapper (supports DeepSeek, MiniMax, Kimi, ZhiPu, SiliconFlow, etc.)
4. **minimax-chat**: MiniMax-specific MCP server

---

## Part 2: Compound Engineering Plugin

### 2.1 Architecture Overview

The compound-engineering-plugin is a **multi-target Claude Code plugin** that provides:
- Skills (Claude Code SKILL.md files)
- Agents (reviewer agents as markdown files)
- Commands (slash commands as markdown)
- Converters (sync skills/agents to Codex, Copilot, Cursor, Gemini, Kiro, Windsurf, OpenCode, Droid, Pi, Qwen, OpenClaw)

The plugin is a TypeScript project (`src/`) with Bun as the runtime, plus a `plugins/compound-engineering/` directory containing the actual plugin content.

### 2.2 The Full Compound Cycle

The compound engineering workflow follows this cycle:

```
/ce:brainstorm  ->  Explore requirements, produce requirements doc
/ce:plan        ->  Structure implementation plan from requirements
/ce:work        ->  Execute plan, produce code, create PR
/ce:review      ->  Multi-agent code review with todo creation
/ce:compound    ->  Document solved problem for future reference
```

#### Step 1: Brainstorm (`/ce:brainstorm`)

**Purpose:** Explore requirements and approaches through collaborative dialogue. Produces a requirements document (lightweight PRD).

**Execution Flow:**
1. **Phase 0 -- Resume, Assess, Route:**
   - Check for existing `*-requirements.md` in `docs/brainstorms/`
   - Assess whether brainstorming is needed (clear requirements = skip)
   - Classify scope: Lightweight / Standard / Deep
2. **Phase 1 -- Understand the Idea:**
   - 1.1 Existing Context Scan (check AGENTS.md, CLAUDE.md, search for topic)
   - 1.2 Product Pressure Test (is this the right problem? what if we do nothing?)
   - 1.3 Collaborative Dialogue (one question at a time, prefer multiple choice, single-select)
3. **Phase 2 -- Explore Approaches:**
   - Propose 2-3 concrete approaches with pros/cons/risks
   - Lead with recommendation
   - Optionally include one higher-upside challenger option
4. **Phase 3 -- Capture Requirements:**
   - Write `docs/brainstorms/YYYY-MM-DD-<topic>-requirements.md`
   - YAML frontmatter: `date`, `topic`
   - Sections: Problem Frame, Requirements (with stable IDs R1, R2...), Success Criteria, Scope Boundaries, Key Decisions, Dependencies/Assumptions, Outstanding Questions (Resolve Before Planning / Deferred to Planning)
5. **Phase 4 -- Handoff:**
   - Options: Proceed to planning, Proceed directly to work, Review and refine, Ask more questions, Share to Proof, Done for now

**Key principles:**
- Keep implementation out of requirements doc
- Apply YAGNI to carrying cost, not coding effort
- Ask one question at a time
- Resolve product decisions here; leave technical implementation for planning

#### Step 2: Plan (`/ce:plan`)

**Purpose:** Transform feature descriptions into well-structured plan files following project conventions.

**Execution Flow:**
1. **Step 0 -- Idea Refinement:**
   - Check `docs/brainstorms/` for matching requirements document (within 14 days)
   - If found: read thoroughly, extract ALL decisions/requirements/questions, skip idea refinement
   - If `Resolve Before Planning` has items: STOP, direct user back to brainstorm
   - If not found: run collaborative dialogue to refine idea
2. **Step 1 -- Local Research (parallel):**
   - `repo-research-analyst`: existing patterns, AGENTS.md guidance
   - `learnings-researcher`: search `docs/solutions/` for related patterns
3. **Step 1.5 -- Research Decision:**
   - High-risk topics (security, payments, external APIs): always research externally
   - Strong local context: skip external research
   - Uncertainty: run external research
4. **Step 1.5b -- External Research (conditional, parallel):**
   - `best-practices-researcher`
   - `framework-docs-researcher`
5. **Step 2 -- Issue Planning & Structure:**
   - Draft title, determine type, generate dated filename with sequence number
   - Format: `YYYY-MM-DD-NNN-<type>-<descriptive-name>-plan.md`
6. **Step 3 -- SpecFlow Analysis:**
   - `spec-flow-analyzer` validates and refines the specification
7. **Step 4 -- Choose Detail Level:**
   - MINIMAL: problem statement + acceptance criteria + context
   - MORE: + background, technical considerations, system-wide impact, success metrics, dependencies
   - A LOT: + implementation phases, alternatives considered, risk analysis, resource requirements, future considerations
8. **Step 5 -- Issue Creation & Formatting**
9. **Step 6 -- Final Review & Submission**
   - Cross-check against origin document
   - Write to `docs/plans/YYYY-MM-DD-NNN-<type>-<name>-plan.md`

**Plan YAML frontmatter:**
```yaml
---
title: [Issue Title]
type: [feat|fix|refactor]
status: active
date: YYYY-MM-DD
origin: docs/brainstorms/YYYY-MM-DD-<topic>-requirements.md
---
```

**Post-generation options:** Open in editor, Run /deepen-plan, Review and refine, Share to Proof, Start /ce:work, Start /ce:work on remote, Create Issue

#### Step 3: Work (`/ce:work`)

**Purpose:** Execute work plans efficiently while maintaining quality.

**Execution Flow:**
1. **Phase 1 -- Quick Start:**
   - Read plan completely, treat as decision artifact not execution script
   - Check for `Execution note`, `Deferred to Implementation`, `Scope Boundaries` sections
   - Setup environment (branch or worktree)
   - Create todo list from implementation units
   - Choose execution strategy: Inline (1-2 tasks) / Serial subagents (3+ with dependencies) / Parallel subagents (3+ independent)
2. **Phase 2 -- Execute:**
   - Task execution loop with System-Wide Test Check
   - Incremental commits at logical unit boundaries
   - Follow existing patterns, test continuously, simplify as you go
   - Figma design sync (if applicable)
3. **Phase 3 -- Quality Check:**
   - Run core quality checks (test suite, linting)
   - Optional reviewer agents for complex/risky changes
   - Final validation against plan requirements
   - Prepare Post-Deploy Monitoring & Validation section
4. **Phase 4 -- Ship It:**
   - Create commit with conventional format + attribution
   - Capture screenshots for UI changes (agent-browser + imgup)
   - Create PR with summary, testing, monitoring sections
   - Update plan status to completed

**System-Wide Test Check questions:**
- What fires when this runs? (callbacks, middleware, observers)
- Do my tests exercise the real chain? (not just mocks)
- Can failure leave orphaned state?
- What other interfaces expose this? (API parity)
- Do error strategies align across layers?

**Attribution format:**
```
feat(scope): description of what and why

Generated with [MODEL] via [HARNESS](HARNESS_URL) + Compound Engineering v[VERSION]

Co-Authored-By: [MODEL] ([CONTEXT] context, [THINKING]) <noreply@anthropic.com>
```

#### Step 4: Review (`/ce:review`)

**Purpose:** Exhaustive multi-agent code review.

**Execution Flow:**
1. **Determine Review Target:** PR number, GitHub URL, file path, or current branch
2. **Load Review Agents:** Read from `compound-engineering.local.md` frontmatter (`review_agents`)
3. **Choose Execution Mode:** Parallel (default for <= 5 agents) or Serial (--serial flag or auto for 6+ agents)
4. **Run Agents in Parallel:**
   - Configured review agents (from settings file)
   - Always: `agent-native-reviewer` + `learnings-researcher`
   - Conditional: `schema-drift-detector` + `data-migration-expert` + `deployment-verification-agent` (if PR has migrations)
5. **Ultra-Thinking Deep Dive:**
   - Stakeholder Perspective Analysis (developer, operations, end user, security, business)
   - Scenario Exploration (happy path, invalid inputs, boundaries, concurrent access, scale, network, resource exhaustion, security, data corruption, cascading failures)
6. **Simplification Review:** Run `code-simplicity-reviewer`
7. **Findings Synthesis:** Merge, categorize (P1 CRITICAL / P2 IMPORTANT / P3 NICE-TO-HAVE), create todo files using file-todos skill
8. **Summary Report:** Total findings, created todo files, next steps
9. **Optional End-to-End Testing:** Web (`/test-browser`) or iOS (`/xcode-test`) based on project type

**Available review agents (27+):**
- **Research:** best-practices-researcher, framework-docs-researcher, git-history-analyzer, issue-intelligence-analyst, learnings-researcher, repo-research-analyst
- **Review:** agent-native-reviewer, architecture-strategist, code-simplicity-reviewer, data-integrity-guardian, data-migration-expert, deployment-verification-agent, dhh-rails-reviewer, julik-frontend-races-reviewer, kieran-python-reviewer, kieran-rails-reviewer, kieran-typescript-reviewer, pattern-recognition-specialist, performance-oracle, schema-drift-detector, security-sentinel
- **Design:** design-implementation-reviewer, design-iterator, figma-design-sync
- **Docs:** ankane-readme-writer
- **Workflow:** bug-reproduction-validator, lint, pr-comment-resolver, spec-flow-analyzer

**Protected artifacts (never flagged for deletion):**
- `docs/brainstorms/*-requirements.md`
- `docs/plans/*.md`
- `docs/solutions/*.md`

#### Step 5: Compound (`/ce:compound`)

**Purpose:** Document a recently solved problem to compound team knowledge.

**Execution Strategy (Full Mode):**

**Phase 0.5 -- Auto Memory Scan:**
- Read MEMORY.md from auto memory directory
- Scan for entries related to the problem being documented
- Pass relevant excerpts as supplementary context to Phase 1 subagents

**Phase 1 -- Parallel Research (5 subagents in parallel):**
1. **Context Analyzer:** Extract conversation history, identify problem type/component/symptoms, return YAML frontmatter skeleton
2. **Solution Extractor:** Analyze investigation steps, identify root cause, extract working solution with code examples
3. **Related Docs Finder:** Search `docs/solutions/` for related documentation, find cross-references and GitHub issues, flag stale docs
4. **Prevention Strategist:** Develop prevention strategies, create best practices guidance, generate test cases
5. **Category Classifier:** Determine optimal category, validate against schema, suggest filename

**CRITICAL RULE:** Phase 1 subagents return TEXT DATA only. They must NOT write files. Only the orchestrator (Phase 2) writes files.

**Phase 2 -- Assembly & Write (sequential):**
1. Collect all text results from Phase 1
2. Assemble complete markdown file
3. Validate YAML frontmatter against schema
4. Create directory: `mkdir -p docs/solutions/[category]/`
5. Write single file: `docs/solutions/[category]/[filename].md`

**Phase 2.5 -- Selective Refresh Check:**
Decide whether to invoke `ce:compound-refresh` based on whether the new learning contradicts, supersedes, or invalidates older docs. Not a default follow-up -- only when evidence warrants it.

**Phase 3 -- Optional Enhancement (parallel, based on problem type):**
- `performance_issue` -> `performance-oracle`
- `security_issue` -> `security-sentinel`
- `database_issue` -> `data-integrity-guardian`
- `test_failure` -> `cora-test-reviewer`
- Any code-heavy issue -> `kieran-rails-reviewer` + `code-simplicity-reviewer`

**Compact-Safe Mode:** Single-pass alternative when context budget is tight. Orchestrator does everything in one pass: extract from conversation, classify, write minimal doc, skip Phase 3. No subagents.

**Auto-invoke triggers:** "that worked", "it's fixed", "working now", "problem solved"

### 2.3 docs/solutions/ File Format

**YAML frontmatter (validated against schema):**
```yaml
---
module: Email Processing
date: 2025-11-12
problem_type: performance_issue
component: rails_model
symptoms:
  - "N+1 query when loading email threads"
  - "Brief generation taking >5 seconds"
root_cause: missing_include
rails_version: 7.1.2
resolution_type: code_fix
severity: high
tags: [n-plus-one, eager-loading, performance]
---
```

**Required fields:**
- `module` (string)
- `date` (string, ISO 8601)
- `problem_type` (enum): build_error, test_failure, runtime_error, performance_issue, database_issue, security_issue, ui_bug, integration_issue, logic_error, developer_experience, workflow_issue, best_practice, documentation_gap
- `component` (enum): rails_model, rails_controller, rails_view, service_object, background_job, database, frontend_stimulus, hotwire_turbo, email_processing, brief_system, assistant, authentication, payments, development_workflow, testing_framework, documentation, tooling
- `symptoms` (array, 1-5 items)
- `root_cause` (enum): missing_association, missing_include, missing_index, wrong_api, scope_issue, thread_violation, async_timing, memory_leak, config_error, logic_error, test_isolation, missing_validation, missing_permission, missing_workflow_step, inadequate_documentation, missing_tooling, incomplete_setup
- `resolution_type` (enum): code_fix, migration, config_change, test_fix, dependency_update, environment_setup, workflow_improvement, documentation_update, tooling_addition, seed_data_update
- `severity` (enum): critical, high, medium, low

**Optional fields:** `rails_version`, `tags`

**Category mapping (from problem_type to directory):**
- build_error -> `docs/solutions/build-errors/`
- test_failure -> `docs/solutions/test-failures/`
- runtime_error -> `docs/solutions/runtime-errors/`
- performance_issue -> `docs/solutions/performance-issues/`
- database_issue -> `docs/solutions/database-issues/`
- security_issue -> `docs/solutions/security-issues/`
- ui_bug -> `docs/solutions/ui-bugs/`
- integration_issue -> `docs/solutions/integration-issues/`
- logic_error -> `docs/solutions/logic-errors/`
- developer_experience -> `docs/solutions/developer-experience/`
- workflow_issue -> `docs/solutions/workflow-issues/`
- best_practice -> `docs/solutions/best-practices/`
- documentation_gap -> `docs/solutions/documentation-gaps/`

**File naming:** `[sanitized-symptom]-[module]-[YYYYMMDD].md`

### 2.4 Duplicate Detection Logic

In `ce:compound`, Step 3 of the compound-docs skill handles duplicate detection:

```bash
# Search by error message keywords
grep -r "exact error phrase" docs/solutions/

# Search by symptom category
ls docs/solutions/[category]/
```

If a similar issue is found, present decision options:
1. Create new doc with cross-reference (recommended)
2. Update existing doc (only if same root cause)
3. Other

In `kw:compound` (knowledge plugin), Step 3 checks for duplicates:
```
Grep: [key phrases] in docs/knowledge/
Grep: [key phrases] in docs/solutions/
```
If found: show existing entry, ask "Update existing or save as new?"

### 2.5 Staleness Refresh Pattern (`ce:compound-refresh`)

**Purpose:** Maintain quality of `docs/solutions/` over time by reviewing existing learnings against the current codebase.

**Mode detection:** Check if `$ARGUMENTS` contains `mode:autonomous`. Interactive mode (default) asks user questions; autonomous mode applies all safe actions and marks ambiguous cases as stale.

**Refresh order:**
1. Review individual learning docs first
2. Note which stayed valid, were updated, replaced, or archived
3. Then review pattern docs that depend on those learnings

**Four maintenance outcomes:**
| Outcome | Meaning | Action |
|---------|---------|--------|
| **Keep** | Still accurate and useful | No file edit |
| **Update** | Core solution correct, references drifted | Apply in-place edits (paths, class names, links, code snippets) |
| **Replace** | Old artifact is misleading, known better replacement | Create successor via subagent, archive old with `superseded_by` |
| **Archive** | No longer useful or applicable | Move to `docs/solutions/_archived/` with `archived_date` and `archive_reason` |

**Scope selection strategies (in order):**
1. Directory match (e.g., `performance-issues`)
2. Frontmatter match (module, component, tags)
3. Filename match (partial)
4. Content search (keyword)

**Routing by scope:**
- **Focused** (1-2 files): investigate directly, present recommendation
- **Batch** (up to ~8 docs): investigate first, present grouped recommendations
- **Broad** (9+ docs): triage first, then investigate in batches

**Investigation dimensions for each learning:**
- **References**: do file paths, class names, modules still exist?
- **Recommended solution**: does the fix still match current code?
- **Code examples**: do snippets reflect current implementation?
- **Related docs**: are cross-references still present and consistent?
- **Auto memory**: does auto memory contain notes in the same problem domain?

**Update vs Replace boundary:** If you find yourself rewriting the solution section or changing what the learning recommends, that is Replace, not Update.

**Stale marking (for ambiguous cases in autonomous mode):**
```yaml
status: stale
stale_reason: [what you found]
stale_date: YYYY-MM-DD
```

**Subagent strategy:**
- Investigation subagents: read-only, return evidence + recommendation (can run in parallel)
- Replacement subagents: write a single new learning (run one at a time, sequentially)
- Orchestrator: merges results, detects contradictions, coordinates replacements, handles archival

**Commit handling (autonomous mode):**
- On main: create branch, commit, attempt to open PR
- On feature branch: commit as separate commit
- Stage only modified files, not other dirty files

---

## Part 3: Compound Knowledge Plugin

### 3.1 Overview

The compound-knowledge-plugin provides **6 workflow commands** for knowledge work (non-code): brainstorm, plan, confidence, review, work, compound. It is the knowledge-work equivalent of compound-engineering.

**The compounding loop:**
```
/kw:brainstorm  ->  Brain dump, pull references, find the shape
/kw:plan        ->  Structure into an actionable plan
/kw:confidence  ->  Gut-check what you know vs. don't (callable at any point)
/kw:review      ->  Strategic alignment + data accuracy check
/kw:work        ->  Execute the plan, produce deliverables
/kw:compound    ->  Save learnings for next time
```

Each cycle makes the next one faster. `/kw:plan` searches `docs/knowledge/` for past learnings saved by `/kw:compound`. Knowledge compounds.

**Components:** 6 workflows, 2 review agents (strategic-alignment-reviewer, data-accuracy-reviewer)

**Storage:** `docs/knowledge/` for learnings, `plans/` for plan files. Local-first, no external dependencies.

### 3.2 The Confidence Assessment Methodology

`/kw:confidence` assesses the agent's own epistemic state (what it knows vs doesn't know) at any point in any workflow.

**4 assessment dimensions (evaluated internally, not output as checklist):**
1. **Task understanding** -- Do I know exactly what's being asked?
2. **Information sufficiency** -- Do I have what I need to do this well?
3. **Approach certainty** -- Is this approach proven or am I guessing?
4. **Risk awareness** -- Can I see what could go wrong?

**Output format (mandatory structure):**
```
## Confidence Check

**Confident about:** [What you know and why. Be specific -- name files
read, patterns recognized, experience drawn on.]

**Less confident about:** [What you don't know and why it matters. Name
specific gaps -- missing data, unverified assumptions, unfamiliar territory.]

**My recommendation:** [One of three paths:
- "Proceed." -- confidence is high, no meaningful gaps
- "Proceed, but [caveat]." -- mostly confident, one area to watch
- "Pause for [specific thing]." -- a gap needs resolving first]
```

**Rules:**
- NEVER give a number (no percentages, no 1-10 scales, no letter grades). Write in prose.
- Be specific ("Missing Q4 data" not "some information gaps")
- Don't hedge on what you know (confidence theater is worse than overconfidence)
- Actions must be executable ("Read file X" not "gather more data")
- Non-destructive interrupt (resume exactly where you left off)
- Keep it proportional (high confidence = 2 sentences; mixed = a few paragraphs)

**If high confidence:** Keep it short -- two sentences is fine.

**"Increase confidence" path:** Produce a ranked list of specific, executable actions (biggest confidence gain first). Each action must be specific enough to execute immediately.

### 3.3 The Learning Type Taxonomy

`/kw:compound` classifies learnings into 4 types:

| Type | Signals |
|------|---------|
| **Insight** | "We discovered...", surprising finding, counter-intuitive result |
| **Playbook** | Repeatable process that worked, step-by-step that others could follow |
| **Correction** | Wrong assumption fixed, data source clarified, definition updated |
| **Pattern** | Something that keeps recurring, systemic observation |

**Rules:**
- Extract 1-3 learnings max per session (quality over quantity)
- If nothing is worth saving, say so: "Nothing from this session seems worth saving as a standalone learning."
- Approval required -- never auto-save
- Be specific ("Revenue metrics come from [specific dashboard], not [other source] which overcounts by ~$X")
- Tags are for retrieval -- choose tags that `/kw:plan`'s grep search would match on

### 3.4 How Grep-Based Retrieval Works in `/kw:plan`

Step 2 of `/kw:plan` runs ALL searches in parallel:

**2a. Past plans:**
```
Glob: plans/*.md
Grep: [keywords from description] in plans/
```
Read top 3 most relevant files. Extract: what was decided, what data was used, what worked.

**2b. Knowledge base:**
```
Grep: [keywords] in docs/knowledge/
```
These are insights from past sessions saved by `/kw:compound`.

**2c. Solutions and patterns:**
```
Grep: [keywords] in docs/solutions/
```
Engineering patterns that may contain relevant operational or integration insights.

**2d. Live data:** Pull current metrics if the plan involves data (follow data hierarchy from CLAUDE.md).

**2e. External research:** If the topic would benefit from outside context, search the web.

Results are presented as a "What I Found" context brief before structuring the plan.

### 3.5 docs/knowledge/ File Format

**Filename:** `docs/knowledge/{descriptive-slug}.md`

```markdown
---
type: [insight | playbook | correction | pattern]
tags: [relevant keywords for future search]
confidence: [high | medium | low]
created: [today's date]
source: [brief description of what triggered this]
---

# [Learning Title]

[2-4 sentences explaining the learning. Be specific enough that someone
reading this in 3 months understands what happened and why it matters.]

## Context

[What you were doing when you discovered this.]

## Implication

[How this should change future work. Be concrete: "When doing X, always check Y first."]
```

### 3.6 The 5-Subagent Compound Extraction (Engineering Plugin)

In `ce:compound` (engineering plugin), Phase 1 launches 5 subagents in parallel:

1. **Context Analyzer**: Extracts conversation history, identifies problem type/component/symptoms, validates against schema, returns YAML frontmatter skeleton
2. **Solution Extractor**: Analyzes all investigation steps, identifies root cause, extracts working solution with code examples, returns solution content block
3. **Related Docs Finder**: Searches `docs/solutions/` for related documentation, identifies cross-references and links, finds related GitHub issues, flags stale docs, returns links/relationships/refresh candidates
4. **Prevention Strategist**: Develops prevention strategies, creates best practices guidance, generates test cases if applicable, returns prevention/testing content
5. **Category Classifier**: Determines optimal `docs/solutions/` category, validates category against schema, suggests filename based on slug, returns final path and filename

**Critical constraint:** Subagents return TEXT DATA to the orchestrator. They must NOT use Write, Edit, or create any files. Only the orchestrator (Phase 2) writes the final documentation file.

### 3.7 The Review System (Knowledge Plugin)

`/kw:review` runs 2 automated reviewers in parallel as Task agents:

**Strategic Alignment Reviewer:**
- Pass: full content + business context from CLAUDE.md
- Checks: goal clarity, falsifiable hypothesis, success metrics, scope proportionality, resource awareness, strategic consistency

**Data Accuracy Reviewer:**
- Pass: full content + data context files from CLAUDE.md
- Checks: source citations, comparison baselines, canonical definitions, freshness, caveats, hardcoded numbers

**Severity definitions:**
| Severity | What qualifies |
|----------|---------------|
| P1 Critical | Factual error, wrong data source, missing goal, unfalsifiable hypothesis |
| P2 Important | Missing source citation, stale data, unclear success metric |
| P3 Nice-to-have | Minor framing, additional context, formatting |

**Staleness rules:** Data older than 48 hours gets a freshness warning. Data older than 7 days gets a P2.

### 3.8 Plan Types and Templates

`/kw:plan` auto-detects work type and uses corresponding template:

| Type | Lead Section | Signals |
|------|-------------|---------|
| Strategy | Recommendation (Pyramid Principle) | Roadmap, architecture, long-term, layers, phases |
| Campaign | Timeline | Launch, promotion, timeline, channels, audience |
| Brief | Recommendation + Scope | Directive for someone else, scope, deliverables |
| Research | Key Findings | Investigation, competitive, analysis, synthesis |
| Operations | Trigger + Steps | Playbook, runbook, SOP, recurring process |

All templates share common sections at the bottom: Success Metrics, Open Questions, References.

---

## Part 4: Comparison and Cross-Reference

### 4.1 ARIS vs Compound Engineering -- Conceptual Mapping

| Concept | ARIS | Compound Engineering |
|---------|------|---------------------|
| Domain | ML research (papers, experiments) | Software engineering (features, bugs) |
| Review loop | auto-review-loop (cross-model, GPT-5.4 reviews) | ce:review (multi-agent, same-model subagents) |
| Knowledge capture | AUTO_REVIEW.md (append-only log) | ce:compound -> docs/solutions/ (structured YAML frontmatter) |
| State persistence | REVIEW_STATE.json | Plan YAML frontmatter (status field) |
| Planning | paper-plan, experiment-plan | ce:brainstorm -> ce:plan |
| Execution | run-experiment, experiment-bridge | ce:work |
| Staleness management | None (logs are immutable) | ce:compound-refresh (4 outcomes: Keep/Update/Replace/Archive) |
| External LLM | Required (GPT-5.4 via Codex MCP) | Optional (review agents are same-model subagents) |

### 4.2 Compound Engineering vs Compound Knowledge

| Aspect | Engineering | Knowledge |
|--------|------------|-----------|
| Target user | Software engineers | Knowledge workers (marketing, strategy, ops) |
| Storage | docs/solutions/ (YAML frontmatter, enum-validated) | docs/knowledge/ (simple YAML frontmatter) |
| Plan output | docs/plans/ (dated, sequenced, typed) | plans/ (type-prefixed) |
| Review | Multi-agent code review (27+ agents) | 2-agent review (strategic alignment + data accuracy) |
| Compound | 5-subagent parallel extraction | Simple 1-3 learning extraction with approval |
| Refresh | ce:compound-refresh (full staleness management) | None (knowledge entries are lightweight) |
| Confidence | None | /kw:confidence (prose-based epistemic assessment) |
| Brainstorm | ce:brainstorm (requirements-focused, PRD-like) | kw:brainstorm (brain dump, themes, tensions) |

### 4.3 Key Design Patterns Worth Adopting

1. **ARIS cross-model review:** Using a different model as adversarial reviewer prevents self-play blind spots
2. **ARIS REVIEW_STATE.json:** Simple JSON state file survives context window compaction with 24-hour staleness rule
3. **Compound's 5-subagent extraction:** Parallel subagents return text, orchestrator assembles single file
4. **Compound's staleness refresh:** Systematic maintenance of documentation with 4 clear outcomes
5. **kw:confidence:** Non-destructive interrupt that assesses epistemic state without numbers
6. **Compound's grep-based retrieval:** Simple grep in docs/knowledge/ and docs/solutions/ makes past learnings discoverable in /kw:plan
7. **ARIS's fix prioritization:** Skip excessive compute, prefer reframing over new experiments, always implement cheap metric additions
8. **Compound's protected artifacts:** Review agents never flag brainstorms/plans/solutions for deletion
