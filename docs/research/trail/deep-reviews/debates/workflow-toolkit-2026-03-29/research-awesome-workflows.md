# Awesome Claude Code Workflows — Research Summary

**Source**: https://github.com/ithiria894/awesome-claude-code-workflows
**Fetched**: 2026-03-29
**Agent**: researcher (claude-sonnet-4-6)

> A curated list of Claude Code workflow recipes that chain hooks, MCP servers, skills, agents, and CLAUDE.md to automate real development tasks. Explicitly not a tool catalog — it's a "cookbook."

---

## 1. Virtual Engineering Teams

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| gstack | 25 skills: CEO/design/eng review, QA, ship, canary deploy, freeze/guard safety hooks, browser testing | — |
| Superpowers | Composable plugin: TDD, brainstorming, plan-then-execute, parallel dispatch, code review loops; session-start + verification hooks | 20K |
| Solopreneur Plugin | 6 agents, 16 skills, 1 hooks.json, 2 .mcp.json configs, CLAUDE.md; full lifecycle discover→spec→backlog→design→build→review→ship | — |
| OneRedOak/claude-code-workflows | Battle-tested from AI-native startup daily use | 3,734 |
| claude-forge | oh-my-zsh-inspired framework: 11 agents, 36 commands, 15 skills, 6-layer security hooks | 593 |

**SDLC phases covered**: All (discover → define → develop → deliver)

**Agent coordination**: Yes — multiple specialist agents with defined roles, debate-before-build patterns, and lifecycle handoffs between phases.

**Key patterns worth adopting:**
- Solopreneur Plugin's "decision journal + observer protocol" for autonomous agent accountability
- gstack's role separation (CEO/design/eng reviews as distinct skills) maps cleanly to the existing autoplan skill
- claude-forge's 6-layer security hooks is the most architecturally strict model seen here

---

## 2. Plan-Build-Review Pipelines

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| gstack autoplan | Chains CEO → design → eng review in single pipeline; each phase has checklist + acceptance criteria | — |
| Superpowers plan-execute | /write-plan → /execute-plan with verification gates between steps | — |
| Spec-Flow | Spec-driven dev: quality gates, token budgets, auditable artifacts | 73 |
| Solopreneur sprint | Parallel feature branches, auto-checkpoints after each skill, team kickoff debates | — |
| gmickel-claude-marketplace | Flow-Next, Ralph autonomous overnight mode, multi-model review gates, re-anchoring, receipt-based gating | 548 |
| shinpr/claude-code-workflows | Frontend plugin with React-specific agents, component architecture, Testing Library, TypeScript-first QA | — |

**SDLC phases covered**: Define → Develop (strong); handoff to Deliver via gstack

**Agent coordination**: Yes — gstack uses sequential chained skills; Solopreneur uses parallel branch workers with a kickoff meeting

**Key patterns worth adopting:**
- **Receipt-based gating** (gmickel): only proceed to next phase when prior phase emits a machine-readable receipt artifact — prevents silent skips
- **Re-anchoring** to prevent drift when overnight autonomous coding sessions run long
- **Token budget enforcement** (Spec-Flow) as a quality gate primitive

---

## 3. Multi-Agent Orchestration

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| ruflo | Multi-agent swarms with distributed intelligence, RAG integration, native Claude Code + Codex integration | 22,810 |
| multi-agent-shogun | tmux-based shogun→karo→ashigaru hierarchy, parallel tasks | 1,096 |
| Superpowers parallel dispatch | Dispatch subagents in parallel, collect + merge results | — |
| Founder OS queue system | Queue-based: /queue:add → /queue:work → /founder:review; dependency + blocked_by ordering | — |
| catlog22 | JSON-driven multi-agent cadence-team dev with CLI orchestration (Gemini/Qwen/Codex) | 1,555 |
| agent-council | Claude + Codex CLI + Gemini CLI for diverse perspectives on same task | 118 |
| Solopreneur kickoff | 6 specialists debate approach before building | — |
| wshobson/agents | Specialized agent roles with coordinated task execution | — |

**SDLC phases covered**: Develop (primary); orchestration spans all phases in Founder OS

**Agent coordination**: Yes — this entire category is about coordination. Key patterns:
- Hierarchical (shogun model): clear command chain
- Queue-based (Founder OS): async, dependency-aware
- Debate-first (Solopreneur, agent-council): adversarial review before execution

**Key patterns worth adopting:**
- **Founder OS queue with blocked_by** is the closest to a formal dependency graph for agent tasks — worth evaluating for the dream pipeline
- **agent-council's cross-LLM debate** (Claude + Codex + Gemini) maps directly to the existing `mde debate` library
- tmux-based shogun model is a low-infrastructure alternative to Agent SDK teams for long-running parallel work

---

## 4. Context and Memory Management

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| claude-mem | Auto-captures all Claude activity, compresses via Agent SDK, injects relevant context into future sessions | 39,615 |
| Continuous Claude v3 | Hooks-based state via ledgers and handoffs; MCP execution without context pollution; isolated context windows | 3,619 |
| arscontexta | Generates individualized knowledge system from conversation — second brain as markdown files | 2,824 |
| Claude Code Development Kit | Context at scale via hooks + MCP + subagents | 1,330 |
| runesleo | Memory management, context engineering, task routing from 3 months of daily use | 521 |
| cartographer | Maps codebases of any size using parallel subagents | 522 |
| vinicius91carvalho/.claude | Drop-in .claude/ with structured context management for any project | — |

**SDLC phases covered**: Cross-cutting — memory management is a meta-concern spanning all phases

**Agent coordination**: Mixed — claude-mem and arscontexta are solo patterns; Continuous Claude v3 and cartographer use subagents

**Key patterns worth adopting:**
- **Ledger-based handoffs** (Continuous Claude v3): explicit state files that persist between context windows — more reliable than remember.md lifecycle
- **Context pollution prevention** via MCP execution: running tools through MCP keeps tool output out of the main context window
- **cartographer's parallel codebase mapping** is a candidate for the research pipeline when needing full repo orientation

---

## 5. TDD and Code Quality

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Superpowers TDD | Full red-green-refactor loop; auto-triggers verification before marking task complete | — |
| Everything Claude Code TDD | TDD with autonomous loop — agent keeps cycling until all tests pass | — |
| gstack QA | Browser-based QA with Playwright: real pages, screenshots, acceptance criteria validation | — |
| Superpowers code review loop | /requesting-code-review + /receiving-code-review combo with dedicated code-reviewer agent | — |
| claude-pipeline | Portable multi-agent pipeline with quality gates | 97 |
| glebis/claude-skills TDD | Multi-agent TDD: context isolation via Task tool; interactive (pauses at RED) + autonomous (runs all slices) modes | — |

**SDLC phases covered**: Develop (primary)

**Agent coordination**: Yes — Superpowers review loop uses a dedicated reviewer agent; glebis TDD uses context-isolated Task tool subagents

**Key patterns worth adopting:**
- **Mandatory verification before task completion** (Superpowers): the hook fires before any "task complete" marker, not as a separate step
- **Interactive vs autonomous TDD modes** (glebis): pausing at RED checkpoints for human review vs. full end-to-end autonomous — this dual-mode pattern is worth adding to the tester agent
- **Acceptance-criteria-driven QA** (gstack): structured criteria as input to the QA skill, not just "does it run"

---

## 6. Git and PR Automation

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Superpowers git worktrees | Parallel workstreams via git worktrees — each agent in its own isolated repo copy | — |
| gstack ship pipeline | Chains /ship → /land-and-deploy → /canary for full deploy loop | — |
| Autoresearch branch-per-run | New git branch per autonomous experiment; tracks results in results.tsv; keep/discard based on evaluation | — |

**SDLC phases covered**: Develop → Deliver

**Agent coordination**: Superpowers uses per-agent worktrees (strong isolation); Autoresearch uses branch-per-run for experiment tracking

**Key patterns worth adopting:**
- **Branch-per-run experiment tracking** (Autoresearch): results.tsv as lightweight audit trail for autonomous agent decisions — directly applicable to the dream pipeline's tiered autonomy model
- **Worktree isolation per agent** is already policy in this repo (worktree-pr-workflow.md) — confirming this is the community standard

---

## 7. Ship and Deploy

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| gstack canary deploy | Post-deploy monitoring loop: deploy → monitor → rollback-if-needed | — |

**SDLC phases covered**: Deliver

**Agent coordination**: Sequential pipeline with conditional rollback

**Key patterns worth adopting:**
- **Conditional rollback as a first-class workflow step** — not a manual recovery procedure but a named skill in the pipeline
- gstack's canary is the most complete deliver-phase workflow in the list; others focus on develop

---

## 8. Cross-LLM Collaboration

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| claude-review-loop | Claude codes, Codex reviews, iterate until approved | 603 |
| codex-orchestrator | Delegate tasks to OpenAI Codex agents via tmux | 249 |
| agent-council | Claude + Codex CLI + Gemini CLI for diverse perspectives | 118 |
| gstack codex second opinion | Multi-AI second opinion via Codex during code review | — |

**SDLC phases covered**: Develop (code review phase primarily)

**Agent coordination**: Yes — all use at least two models; agent-council uses three

**Key patterns worth adopting:**
- **Iterate-until-approved loop** (claude-review-loop): machine-readable approval signal from Codex triggers exit, not a fixed number of review rounds — more robust than fixed-round patterns
- This entire category validates the existing `mde debate` library as the right abstraction

---

## 9. Research and Discovery

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Everything Claude Code search-first | Research before coding: codebase + docs + web before any code | — |
| Autoresearch autonomous loop | Karpathy's experiment loop: modify → train 5 min → evaluate → keep/discard → repeat; program.md is 114 lines | — |
| Everything Claude Code continuous learning | Auto-extracts patterns from coding sessions into reusable skills | — |
| glebis/claude-skills deep-research | OpenAI + Firecrawl + web scraping with structured output; insight-extractor parses /insights into markdown | — |

**SDLC phases covered**: Discover (primary); continuous learning spans Discover → Develop

**Agent coordination**: Autoresearch is solo-agent; glebis uses multi-tool orchestration

**Key patterns worth adopting:**
- **Search-first enforcement** before any code is written — a hook pattern rather than a guideline
- **Auto-extract patterns from sessions** (continuous learning): the dream pipeline already does this via dream-extract; confirming the pattern is widely validated
- **Autoresearch's minimalism** (10 files, 114-line program.md) is a design principle: intention over infrastructure

---

## 10. Browser and Testing

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| gstack browser QA | Playwright: real pages, screenshots, acceptance criteria validation | — |
| UI Annotator + Claude Code | Hover to label UI components with real names; then describe changes using component names; works with any framework | — |
| Pagecast demo recording | AI reads codebase → writes demo script → browser records with tooltip zoom overlays → exports to GIF/MP4/Shorts | — |

**SDLC phases covered**: Develop (UI iteration) + Deliver (demo creation)

**Agent coordination**: Pagecast is a sequential MCP pipeline (record_page → interact_page → stop_recording → export)

**Key patterns worth adopting:**
- **UI Annotator's component labeling** solves a concrete pain point (AI can't identify UI elements by sight) — worth evaluating if browser QA is added to the stack
- **Pagecast's schema** (record → interact → stop → export) is a clean MCP pipeline template

---

## 11. Autonomous Loops

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Everything Claude Code autonomous loops | /loop-start, /loop-status; runs until goal met | — |
| Autoresearch experiment loop | Autonomous modify → run → evaluate → repeat; no human in loop during runs | — |

**SDLC phases covered**: Develop (continuous; human sets goal, agent executes)

**Agent coordination**: Single-agent continuous loop; no coordination mechanism needed by design

**Key patterns worth adopting:**
- **Goal-met exit condition** (not fixed iteration count): the loop terminates on objective evaluation, not on a hardcoded number of attempts
- **Status observability** (/loop-status): even autonomous loops need an observable state endpoint so a human can check in without interrupting execution

---

## 12. Scope and Config Management

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Claude Code Organizer | Web dashboard + MCP: scans ~/.claude/, shows Global→Workspace→Project hierarchy, drag-and-drop config between scopes | — |
| gstack freeze/guard/unfreeze | File protection via PreToolUse hooks in SKILL.md frontmatter; enforcement only in Claude Code (advisory in Codex) | — |
| agent-skill-manager (asm) | CLI/TUI for skills across 17 providers; security scan, duplicate detection, 2,800+ skill catalog | — |
| claude-code-skill-factory | Builds production-ready skills/agents/commands; 7 hook event types, safety validation | — |

**SDLC phases covered**: Cross-cutting (configuration management)

**Agent coordination**: asm manages skills across agent providers — cross-agent config sync

**Key patterns worth adopting:**
- **Scope hierarchy visualization** (Claude Code Organizer): understanding Global vs Workspace vs Project scope resolution is difficult without tooling — this fills a gap
- **gstack freeze enforcement note**: hooks only fire in Claude Code, not Codex — important constraint when multi-LLM workflows are used; advisory prose is not enforcement

---

## 13. Monitoring and Dashboards

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| claude-hud | Real-time overlay: context usage, active tools, running agents, todo progress | 11,537 |
| cc-context-stats | MI score in status bar calibrated from MRCR benchmark; ASCII dashboard tracking context growth + MI degradation; 5 color-coded zones | — |
| ccproxy | Proxy for Claude Code requests: model routing, request/response modification, LangFuse tracking | 189 |

**SDLC phases covered**: Cross-cutting (observability)

**Agent coordination**: ccproxy is the only one that sits in the request path and can affect routing

**Key patterns worth adopting:**
- **MI (Model Intelligence) score zones** (cc-context-stats): plan / code-only / start-fresh decision points based on measured context degradation — more rigorous than the current "context budget" heuristic
- **LangFuse integration** (ccproxy): structured tracing of all Claude Code requests is the observability primitive needed for retrospectives and drift detection

---

## 14. Comprehensive Frameworks

**What is listed:**

| Workflow | Description | Stars |
|---|---|---|
| Everything Claude Code | 28 agents, 59 commands, 116 skills, 26 hook entries / 7 event groups, 13 language rules, autonomous loop mgmt | 17K |
| claude-code-infrastructure-showcase | Skill auto-activation, hooks, agents as integrated system | 9,315 |
| ChrisWiles/claude-code-showcase | Hooks + skills + agents + commands + GitHub Actions workflows | 5,571 |
| claude-code-plugins-plus-skills | 340 plugins + 1,367 agent skills, CCPI package manager, tutorials, orchestration patterns | 1,689 |
| CloudAI-X/claude-workflow-v2 | Universal Claude Code workflow plugin: agents + skills + hooks + commands in one package | 1,301 |
| shanraisshan/claude-code-best-practice | Command → Agent → Skill orchestration pattern; chain commands into multi-step workflows | trending Mar 2026 |
| luongnv89/claude-howto | Visual 10-module guide: slash commands + hooks + skills + subagents + MCP into end-to-end workflows; CI/CD, security audit templates | — |

**SDLC phases covered**: All phases

**Agent coordination**: Everything Claude Code is the most complete coordination framework; all others bundle coordination primitives

**Key patterns worth adopting:**
- **Command → Agent → Skill pattern** (shanraisshan) is the canonical composition unit worth documenting as a formal abstraction in this repo's agent definitions
- **CCPI package manager** (claude-code-plugins-plus-skills): a package manager for skills/plugins is the natural evolution of the current rsm-subagents marketplace
- **Everything Claude Code's 7 event group hook coverage** is the most complete hook architecture seen — 26 hook entries across 27 scripts as a reference implementation

---

## Cross-Cutting Observations

### Patterns that appear across multiple categories (high confidence)

1. **Debate-before-build**: agent-council, Solopreneur kickoff, gstack autoplan all mandate multi-agent discussion before implementation. This is the community standard for avoiding premature convergence.

2. **Machine-readable exit conditions**: claude-review-loop, Everything Claude Code autonomous loops, and Autoresearch all use evaluated objectives (not iteration counts) to exit loops. Fixed-round loops are an anti-pattern.

3. **Worktree isolation per agent**: Superpowers, Solopreneur sprint, and Autoresearch all use branch/worktree isolation for parallel work. Already policy in this repo — confirmed as community standard.

4. **Receipt-based gating**: gmickel and Spec-Flow require machine-readable artifacts as gate signals. Prevents silent phase skips that bypass quality checks.

5. **Context pollution prevention**: Continuous Claude v3 runs tools through MCP to keep output out of the main context window. A concrete implementation of the context budget policy.

### Gaps in the current mde stack (based on this survey)

| Gap | Evidence | Priority |
|---|---|---|
| No goal-met exit condition for autonomous loops | Everything Claude Code, Autoresearch | HIGH |
| No MI score tracking for context degradation | cc-context-stats | MEDIUM |
| No receipt artifacts from quality gate phases | gmickel, Spec-Flow | MEDIUM |
| No branch-per-run tracking for dream pipeline | Autoresearch | MEDIUM |
| No scope hierarchy visualization | Claude Code Organizer | LOW |

### Relation to existing mde primitives

| Awesome list entry | Existing mde equivalent | Gap |
|---|---|---|
| agent-council / agent-council | `mde debate` library | Debate exists; cross-LLM integration confirmed |
| Superpowers TDD | tester agent | Missing interactive/autonomous mode selection |
| gstack autoplan | `/autoplan` skill | Exists; could add receipt artifacts |
| claude-mem / arscontexta | remember plugin + dream pipeline | Dream pipeline covers pattern extraction; session context injection is weaker |
| Autoresearch experiment loop | dream pipeline promote ladder | Ladder is for code quality; not experiment tracking |
| Everything Claude Code hooks | 17 hooks in `src/mde/hooks/` | Hook count comparable; event coverage similar |

---

## Source Catalog Entries

- https://github.com/ithiria894/awesome-claude-code-workflows — PRIMARY SOURCE (HIGH)
- https://github.com/ruflo/ruflo — Multi-agent orchestration, 22,810 stars (HIGH)
- https://github.com/Everything-Claude-Code — Comprehensive framework, 17K stars (HIGH)
- https://github.com/claude-hud — Context monitoring dashboard, 11,537 stars (HIGH)
- https://github.com/claude-mem — Auto-capture + compress + inject context, 39,615 stars (HIGH)
- https://github.com/ithiria894/awesome-claude-code — Related: tool catalog (MEDIUM)
- https://github.com/multi-agent-shogun — tmux-based hierarchy, 1,096 stars (MEDIUM)
- https://github.com/Autoresearch — Karpathy experiment loop (MEDIUM)
- https://github.com/agent-council — Cross-LLM collaboration, 118 stars (MEDIUM)
- https://github.com/claude-review-loop — Codex review loop, 603 stars (MEDIUM)
- https://github.com/Spec-Flow — Spec-driven dev, 73 stars (MEDIUM)
- https://github.com/cc-context-stats — MI score tracking (MEDIUM)
- https://github.com/ccproxy — LangFuse proxy, 189 stars (MEDIUM)
- https://github.com/Claude-Code-Organizer — Scope management dashboard (LOW)
- https://github.com/claude-code-skill-factory — Skill factory with 7 hook types (LOW)
