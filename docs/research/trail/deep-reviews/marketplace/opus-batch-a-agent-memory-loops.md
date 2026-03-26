# Opus Deep Review: opus-batch-a-agent-memory-loops

**Date**: 2026-03-26
**Model**: claude-opus-4.6
**Agent ID**: ae790336

---

I now have comprehensive knowledge of all five plugins. Let me compile the deep review.

---

## Plugin Deep Review Results

### 1. evolve-loop
**VERDICT: EXTRACT**
**CONFIDENCE: 0.85**
**GOALS: agent-improvement, self-updating, code-modernization**
**COMPONENTS: skills=1 (with 15 sub-files), agents=4, cmds=0, hooks=none (no hooks.json)**
**POLICY_VIOLATIONS:**
- `install.sh`, `uninstall.sh`, `status.sh` (3 .sh files in repo root) -- HARD violation of no-shell-scripts policy
- `scripts/phase-gate.sh`, `scripts/context-budget.sh`, `scripts/eval-quality-check.sh`, `scripts/verify-eval.sh`, `scripts/cycle-health-check.sh` (5 .sh files in scripts/) -- HARD violation; these are core operational scripts, not just install helpers
- The entire pipeline assumes the orchestrator runs bash scripts (`bash scripts/phase-gate.sh`) at every phase transition -- fundamental architecture conflict with our Python-only policy
- Scout agent requests WebSearch/WebFetch tools directly (line 7 of evolve-scout.md) -- conflicts with our agent-fetch-only policy

**OVERLAP:**
- Massive overlap with research-review-toolkit (research pipeline, eval gates), codebase-quality (quality checks), challenger (adversarial review), safety-net (safety guards), and our custom reviewd + consensus.py autonomous review system
- Agent roles (Scout/Builder/Auditor/Operator) parallel our researcher/coder/tester/reviewer subagent architecture

**RATIONALE:** This is an exceptionally well-designed autonomous improvement pipeline with sophisticated anti-cheating mechanisms (challenge tokens, hash chains, canary files, eval quality classifiers, forgery detection). The compound discovery loop, research ledger, instinct system, and multi-dimensional fitness scoring are genuinely novel patterns not present in our stack. However, it requires 8 bash scripts as core infrastructure, making it incompatible with our no-shell-scripts policy. The pipeline would need a full rewrite to Python (src/mde/) to be installable. The anti-cheating patterns, budget-aware agent behavior, and compound discovery loop are high-value extraction targets.

**EXTRACTABLE:**
- Challenge token + hash chain pattern for ledger integrity (adapt for our reviewd consensus system)
- Eval quality classifier (Level 0-4 rigor classification) -- port to Python for our quality gate
- Budget-aware agent behavior with pressure levels (low/medium/high) -- apply to our subagent dispatch
- Compound discovery loop (hypothesize -> discover -> propose -> select) -- integrate into research pipeline
- Anti-forgery artifact substance checks (word count, file refs, freshness) -- port to Python hooks
- Adaptive audit strictness with consecutive-clean streaks

---

### 2. superpowers-optimized
**VERDICT: EXTRACT**
**CONFIDENCE: 0.90**
**GOALS: agent-improvement, memory, prompt-optimization**
**COMPONENTS: skills=21, agents=2 (code-reviewer, red-team), cmds=0, hooks=8 node.js hooks (context-engine, skill-activator, block-dangerous-commands, protect-secrets, subagent-guard, track-edits, track-session-stats, stop-reminders) + 1 session-start shell script**
**POLICY_VIOLATIONS:**
- `hooks/session-start` (shell script without .sh extension) -- HARD violation
- 23 .sh files in tests/ directory -- test infrastructure, not operational, but still violates policy
- `skills/systematic-debugging/find-polluter.sh` -- HARD violation (.sh file in skill)
- Node.js hooks are acceptable per policy ("Node.js hooks -- note but acceptable for guards")
- Writes `context-snapshot.json`, `project-map.md`, `session-log.md`, `state.md` to project root -- conflicts with our file organization policy (never save working files to root)
- The `using-superpowers` skill mandates itself as a BLOCKING REQUIREMENT before any work -- conflicts with our existing workflow guide and skills-first policy
- Context-engine modifies `.gitignore` automatically -- side effect that could conflict with our hk.pkl hooks

**OVERLAP:**
- Heavy overlap with `engineering` (workflow routing), `guide` (step announcements), `safety-net` (dangerous command blocking), `codebase-quality` (review), `challenger` (adversarial), `token-saver` (token efficiency)
- `finishing-a-development-branch` duplicates our worktree-pr-workflow policy
- `self-consistency-reasoner` is novel -- no equivalent in our stack
- `block-dangerous-commands.js` and `protect-secrets.js` overlap with our safety-net plugin but are more comprehensive (40+ patterns vs typical 10-15)

**RATIONALE:** This is the most polished plugin in the batch with battle-tested safety hooks, comprehensive secret protection (file paths + bash commands + content scanning for 13 hardcoded secret patterns), and a well-designed skill activation system. The self-consistency reasoner (Wang et al. majority-vote technique) is a genuinely novel reasoning pattern we lack. However, installing it would create massive overlap with 6+ of our 18 enabled plugins, and its opinionated workflow routing (`using-superpowers` as mandatory entry point) would fight with our existing workflow guide. The safety hooks are the highest-value extraction targets -- they are more thorough than anything in our stack.

**EXTRACTABLE:**
- `protect-secrets.js` patterns -- 56 sensitive file patterns + 13 hardcoded secret patterns with env variable hints; port to Python for our hooks
- `block-dangerous-commands.js` patterns -- 30+ dangerous command patterns with severity levels; port to Python
- Self-consistency reasoner technique (5-path majority vote for high-stakes reasoning) -- add as a skill to our research-review-toolkit
- Subagent guard pattern (detect skill leakage in subagent output) -- port to Python PostToolUse hook
- Micro-task detection (skip workflow routing for trivial changes) -- adopt the heuristic in our workflow guide
- Session statistics tracking (skill invocation counts, edit tracking) -- port to Python hooks

---

### 3. engram
**VERDICT: REJECT**
**CONFIDENCE: 0.95**
**GOALS: memory-research, agent-improvement**
**COMPONENTS: skills=4, agents=0, cmds=4, hooks=none, MCP server=1**
**POLICY_VIOLATIONS:**
- `.mcp.json` present -- HARD violation (we use CLI wrappers only, never MCP tool schemas in context)
- Requires `npx -y engram-sdk@latest mcp` -- downloads external npm package at runtime; no mise config
- License is "Proprietary" -- not MIT/Apache, potential legal concern
- Skills reference MCP tools directly (`engram_remember`, `engram_recall`, `engram_consolidate`, `engram_briefing`) -- fundamentally requires MCP server
- The `engram-sdk` is a cloud service dependency (engram.fyi) -- likely requires API key or account

**OVERLAP:**
- Overlaps with `remember` plugin (already enabled) which provides persistent memory
- Overlaps with our 4-layer memory architecture (hot/warm/cool/cold) documented in CLAUDE.md
- Overlaps with our NotebookLM-based second-brain integration
- Our existing auto-memory (MEMORY.md) + YAML provenance records + NotebookLM cover all the use cases engram targets

**RATIONALE:** Engram is a proprietary MCP-dependent memory system that requires an external npm package and likely a cloud service. It has three hard policy violations (.mcp.json, non-mise dependency, proprietary license). Our existing memory stack (auto-memory + remember plugin + YAML provenance + NotebookLM) already covers persistent recall, consolidation, and session briefing. The knowledge graph and bi-temporal tracking features are interesting conceptually but not worth the policy violations or vendor lock-in.

**EXTRACTABLE:** None worth extracting -- our existing memory architecture is more aligned with our policies.

---

### 4. hipocampus
**VERDICT: EXTRACT**
**CONFIDENCE: 0.75**
**GOALS: memory-research**
**COMPONENTS: skills=4 (core, compaction, flush, search) + 2 platform variants, agents=0, cmds=0, hooks=1 bash (session-start.sh) + 2 node (PreCompact, TaskCompleted via npx)**
**POLICY_VIOLATIONS:**
- `hooks/session-start.sh` -- HARD violation (bash hook)
- Hooks call `npx hipocampus compact` -- requires npm package, not in mise config
- Hooks call `qmd update` / `qmd embed` -- requires qmd tool, not in mise config
- Creates multiple files in project root (SCRATCHPAD.md, WORKING.md, TASK-QUEUE.md, hipocampus.config.json) -- violates file organization policy
- Session-start hook mandates "FIRST RESPONSE RULE" that overrides user requests -- conflicts with our workflow guide priority
- The shell hook creates directories and files automatically (`mkdir -p memory/daily memory/weekly memory/monthly`) -- side effects in project root

**OVERLAP:**
- 3-tier hot/warm/cold directly mirrors our existing Memory Architecture (hot=session, warm=project, cool=synthesis, cold=knowledge) documented in CLAUDE.md
- Compaction tree concept overlaps with our NotebookLM consolidation flow
- Session checkpoint protocol overlaps with our agent-notes policy (write findings to disk IMMEDIATELY)
- Search via ROOT.md overlaps with our progressive disclosure (3-layer index -> context -> full detail)

**RATIONALE:** Hipocampus has a thoughtful compaction tree architecture (Raw -> Daily -> Weekly -> Monthly -> Root) with fixed/tentative lifecycle management and BM25+vector search. The 5-level compaction tree is more sophisticated than our current flat memory approach. However, it requires bash hooks, npm packages (hipocampus, qmd), and pollutes the project root with 5+ files. The core architectural insight -- a compaction tree that progressively summarizes raw logs into a small auto-loaded index -- is valuable and could enhance our existing memory architecture without the plugin's baggage.

**EXTRACTABLE:**
- 5-level compaction tree pattern (Raw -> Daily -> Weekly -> Monthly -> Root) with fixed/tentative lifecycle -- design pattern for enhancing our warm-layer provenance records
- ROOT.md as "what I know I know" index -- the O(1) topic lookup concept could improve our progressive disclosure search
- Keyword-dense BM25-optimized compaction format -- technique for our research trail findings
- Cooldown-gated maintenance dispatch pattern -- useful for any periodic background task

---

### 5. claude-workflow
**VERDICT: REJECT**
**CONFIDENCE: 0.85**
**GOALS: agent-improvement, sdlc-orchestration**
**COMPONENTS: skills=9 (in templates/skills/), agents=0, cmds=0, hooks=2 bash hooks (workflow-start.sh, workflow-cleanup.sh), MCP server=1 (node build/index.js), TypeScript engine**
**POLICY_VIOLATIONS:**
- `.mcp.json` present -- HARD violation (MCP tool schemas in context)
- 2 bash hooks (`workflow-start.sh`, `workflow-cleanup.sh`) -- HARD violation
- `workflow-start.sh` copies skills to `~/.claude/skills/` automatically -- modifies global Claude config as side effect
- Requires `npm run build` (TypeScript compilation) -- build step not in mise config
- Requires `jq` in hooks (not in mise config)
- `hooks/workflow-start.sh` has `STOP. Call mcp__plugin_workflow_wf__start` as mandatory first action -- directly conflicts with our workflow guide and CLI wrappers policy
- The plugin installs its own skills globally into `~/.claude/skills/` via the session-start hook -- invasive side effect

**OVERLAP:**
- YAML state machines overlap with our existing workflow guide (docs/superpowers/workflow-guide.md)
- Sub-workflow stacking overlaps with our subagent dispatch and agent-teams-lifecycle policy
- `coding.yaml` workflow (think -> write -> review -> verify) duplicates our existing quality gate flow
- `file-review.yaml` / `code-review.yaml` overlap with research-review-toolkit
- Skills like `lang-python`, `architecture`, `preferences` overlap with our existing specialized agents

**RATIONALE:** Claude-workflow is an ambitious finite-state machine engine for workflow orchestration, but it has four hard policy violations (MCP server, 2 bash hooks, global skill installation). The FSM approach is interesting for complex multi-step workflows, but our existing workflow guide + skills + hooks already provide structured orchestration. The TypeScript engine requires npm build, and the MCP server adds persistent process overhead. The invasive session-start hook that copies skills globally and demands MCP tool calls as the first action is incompatible with our architecture. The exec/fetch action state pattern (run shell commands or HTTP requests as state transitions) is novel but adds complexity without clear value over our Python-based approach.

**EXTRACTABLE:** The YAML state machine schema is an interesting design pattern but not worth extracting given our existing Python-based orchestration.

---

## Summary Table

| Plugin | Verdict | Confidence | Hard Violations | Key Value |
|--------|---------|------------|-----------------|-----------|
| evolve-loop | EXTRACT | 0.85 | 8 .sh files | Anti-cheating patterns, compound discovery, eval quality classifier |
| superpowers-optimized | EXTRACT | 0.90 | 1 .sh hook | Secret protection (56+13 patterns), self-consistency reasoner, subagent guard |
| engram | REJECT | 0.95 | .mcp.json, proprietary license | None -- existing stack covers all use cases |
| hipocampus | EXTRACT | 0.75 | 1 .sh hook, npm deps | 5-level compaction tree, ROOT.md index pattern |
| claude-workflow | REJECT | 0.85 | .mcp.json, 2 .sh hooks, global skill install | FSM pattern interesting but not worth extracting |

**Priority extraction order:**
1. superpowers-optimized secret protection patterns (highest immediate safety value)
2. evolve-loop eval quality classifier + anti-cheating patterns (highest research pipeline value)
3. superpowers-optimized self-consistency reasoner (novel reasoning technique)
4. hipocampus compaction tree design (long-term memory architecture improvement)
5. evolve-loop compound discovery loop (research pipeline enhancement)
