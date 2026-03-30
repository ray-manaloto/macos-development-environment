# Research: wshobson/agents Workflow Plugins

**Date**: 2026-03-29
**Sources**:
- https://github.com/wshobson/agents/tree/main/plugins/agent-teams
- https://github.com/wshobson/agents/tree/main/plugins/agent-orchestration

---

## Plugin 1: agent-teams (v1.0.2)

**Author**: Seth Hobson (seth@major7apps.com)
**License**: MIT
**Install**: `/plugin install agent-teams@claude-code-workflows`
**Requires**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env flag

### Overview

Orchestrates multi-agent teams for parallel code review, hypothesis-driven debugging, and coordinated feature development using Claude Code's experimental Agent Teams API. Teams communicate via `SendMessage`/`TaskUpdate` primitives and are coordinated by a `team-lead` agent.

---

### Agents (4 total)

| Agent | Model | Color | Tool Access | Role |
|---|---|---|---|---|
| `team-lead` | opus | blue | Read, Glob, Grep, Bash | Orchestrator — decomposes work, manages lifecycle, synthesizes results |
| `team-implementer` | opus | yellow | Read, Write, Edit, Glob, Grep, Bash | Parallel builder within strict file ownership boundaries |
| `team-reviewer` | opus | green | Read, Glob, Grep, Bash | Single-dimension code reviewer (security/perf/arch/testing/accessibility) |
| `team-debugger` | opus | red | Read, Glob, Grep, Bash | Hypothesis investigator — confirms or falsifies one assigned hypothesis |

#### team-lead details
- Decomposes before delegating — builds dependency graphs with `blockedBy/blocks`
- Enforces one-file-one-owner policy; when a file needs multi-owner access the lead owns it
- Life cycle: Spawn → Assign → Monitor → Collect → Synthesize → Shutdown → Cleanup
- Communicates via `message` (never structured JSON — uses `TaskUpdate` instead)
- Reads team config from `~/.claude/teams/{team-name}/config.json`
- Refers to teammates by NAME, never UUID

#### team-implementer details
- Strict file ownership: only modifies files listed in task description
- 5-phase workflow: Understand → Plan → Build → Verify → Report
- Interface contracts are immutable without team-lead approval
- Marks completion via `TaskUpdate`, then messages lead with change summary
- Explicitly prohibited from scope creep outside owned files

#### team-reviewer details
- Operates on exactly one dimension per invocation
- Five dimensions available: Security, Performance, Architecture, Testing, Accessibility
- Structured output format: severity rating + file:line citation + evidence + impact + fix
- Security checks: injection, OWASP, credential exposure, auth bypass, rate limiting
- Performance checks: N+1 queries, memory leaks, algorithm complexity, caching
- Architecture checks: SOLID, separation of concerns, circular deps, abstraction levels
- Testing checks: coverage gaps, isolation, determinism, edge cases
- Accessibility checks: WCAG 2.1 AA, ARIA, keyboard nav, screen reader, contrast

#### team-debugger details
- Assigned exactly one hypothesis to investigate
- 7-step protocol: Understand → Evidence Criteria → Primary Evidence → Supporting Evidence → Test → Assess Confidence → Report
- Confidence ratings: High (>80%), Medium (50-80%), Low (<50%)
- Must cite every claim with file:line references
- Must report both confirming AND contradicting evidence
- Scope discipline: reports discoveries outside hypothesis but does not change focus
- Reports falsified hypotheses as valuable findings (not failures)

---

### Commands (7 total)

| Command | Description |
|---|---|
| `/team-spawn` | Spawn a team using presets or custom composition |
| `/team-status` | Display team members, tasks, and progress |
| `/team-shutdown` | Gracefully shut down a team and clean up resources |
| `/team-review` | Multi-reviewer parallel code review |
| `/team-debug` | Competing hypotheses debugging with parallel investigation |
| `/team-feature` | Parallel feature development with file ownership |
| `/team-delegate` | Task delegation dashboard and workload management |

#### /team-spawn preset options

| Preset | Members | Composition | Use case |
|---|---|---|---|
| `review` | 3 | 3x team-reviewer (security, perf, arch) | Code review |
| `debug` | 3 | 3x team-debugger (one hypothesis each) | Bug investigation |
| `feature` | 3 | 1x team-lead + 2x team-implementer | Feature development |
| `fullstack` | 4 | team-lead + frontend/backend/tests implementers | Full stack features |
| `research` | 3 | 3x general-purpose (different questions) | Codebase/web research |
| `security` | 4 | 4x team-reviewer (OWASP, auth, deps, secrets) | Security audit |
| `migration` | 4 | team-lead + 2x implementer + 1x reviewer | Codebase migration |
| `custom` | 2-5 | Interactive configuration | Ad hoc |

#### /team-review workflow (6 phases)
1. **Target Resolution** — resolves file/dir, git diff range, or PR number via `gh pr diff`
2. **Team Spawn** — spawns one `team-reviewer` per dimension, names them `{dimension}-reviewer`
3. **Monitor and Collect** — polls `TaskList`, collects structured findings as reviewers complete
4. **Consolidation** — deduplicates by file:line, resolves conflicts (higher severity wins), groups by Critical/High/Medium/Low
5. **Report** — outputs consolidated report with per-severity counts
6. **Cleanup** — sends `shutdown_request` to all reviewers, calls `Teammate` cleanup

#### /team-debug workflow (6 phases)
1. **Initial Triage** — reads file or searches codebase for related code, recent git changes, tests
2. **Hypothesis Generation** — generates N hypotheses across 6 failure mode categories: Logic Error, Data Issue, State Problem, Integration Failure, Resource Issue, Environment
3. **Investigation** — spawns one `team-debugger` per hypothesis with scope boundaries
4. **Evidence Collection** — monitors for completion, collects reports
5. **Arbitration** — ranks confirmed hypotheses by confidence + causal chain strength, outputs root cause analysis with recommended fix
6. **Cleanup** — sends `shutdown_request`, calls Teammate cleanup

#### /team-feature workflow (7 phases)
1. **Analysis** — explores codebase to find files to modify, patterns, integration points
2. **Decomposition** — breaks into exclusive-ownership work streams with interface contracts and `blockedBy/blocks` dependency graph; optionally presents plan for user approval (`--plan-first`)
3. **Team Spawn** — optionally creates git branch; spawns `team-lead` + `team-implementer` per stream
4. **Task Creation** — `TaskCreate` per stream with owned files + acceptance criteria; `TaskUpdate` for `blockedBy` relationships
5. **Monitor and Coordinate** — checks `TaskList`, unblocks dependent tasks, rebalances workload
6. **Integration Verification** — runs build + test commands via Bash; creates fix tasks if failures found
7. **Cleanup** — reports branch name + file/stream counts; sends `shutdown_request`, calls Teammate cleanup

#### /team-shutdown workflow
- Pre-shutdown: checks for in-progress tasks, warns user if `--force` not set
- Sends structured `shutdown_request` via `SendMessage` (not plain text)
- Supports `--force` (skip waiting) and `--keep-tasks` (preserve task list)
- Reports member shutdown count and task completion stats

---

### Skills (6 total)

| Skill | Content type |
|---|---|
| `team-composition-patterns` | Team sizing heuristics, preset compositions, agent type selection |
| `task-coordination-strategies` | Task decomposition, dependency graphs, workload monitoring |
| `parallel-debugging` | Hypothesis generation, evidence collection, result arbitration |
| `multi-reviewer-patterns` | Review dimension allocation, finding deduplication, severity calibration |
| `parallel-feature-development` | File ownership strategies, conflict avoidance, integration patterns |
| `team-communication-protocols` | Message type selection, plan approval workflow, shutdown protocol |

---

### SDLC Coverage

| Phase | Coverage |
|---|---|
| Planning | `/team-feature --plan-first` shows decomposition for user approval before spawning |
| Implementation | `/team-feature`, `/team-spawn feature/fullstack/migration` |
| Code Review | `/team-review`, `/team-spawn review/security` |
| Debugging | `/team-debug`, `/team-spawn debug` |
| Research | `/team-spawn research` |
| Release/Migration | `/team-spawn migration` |

Missing from this plugin: CI/CD, deployment, monitoring, retrospective phases.

---

### Handoff Mechanisms

1. **TaskUpdate** — agents mark tasks complete, blocked, or in-progress via structured tool call
2. **SendMessage** — direct messaging between teammates (or broadcast for team-wide announcements)
3. **Structured shutdown_request** — JSON message type, not plain text; recipients must respond before terminating
4. **File-system coordination** — team config at `~/.claude/teams/{team-name}/config.json`; task list at `~/.claude/tasks/{team-name}/`
5. **Interface contracts** — defined before work begins, immutable during execution; implementers message lead if contract seems wrong
6. **Result synthesis** — team-lead merges outputs, deduplicates findings, attributes to source teammates

---

### Quality Gates and Enforcement

- `--plan-first` flag on `/team-feature`: requires user approval of decomposition before implementation begins
- One-file-one-owner rule: enforced via agent behavioral instructions (no structural lock enforcement)
- Integration verification phase in `/team-feature`: runs build + test via Bash before declaring feature complete
- Conflict resolution in code review: higher severity wins when reviewers disagree
- Confidence-rated hypothesis arbitration in `/team-debug`: team-lead selects highest-confidence root cause
- Graceful shutdown: warnings displayed if tasks are in-progress, user must confirm

**Notable gap**: No automated quality gate on implementer output (no ruff/ty equivalent wired in). Quality relies on agent behavioral instructions.

---

## Plugin 2: agent-orchestration (v1.2.1)

**Author**: Seth Hobson (seth@major7apps.com)
**License**: MIT

### Overview

Meta-level plugin for optimizing agents themselves and multi-agent systems. Focuses on agent performance analysis, prompt engineering improvement, and context window management. More of a toolbox for AI engineers than a workflow runner.

---

### Agents (1 total)

#### context-manager

- **Model**: inherit (uses calling context's model)
- **Role**: Elite AI context engineering specialist
- **Scope**: Dynamic context assembly, vector databases, knowledge graphs, intelligent memory systems, multi-agent context handoff

Key capabilities:
- Context window optimization and token budget management
- Vector database implementation (Pinecone, Weaviate, Qdrant)
- Knowledge graph construction and semantic query
- RAG implementation (chunking, hybrid search, retrieval ranking)
- Enterprise context governance (multi-tenant, compliance, audit trails)
- Agent-to-agent context handoff and state management
- Context quality metrics and freshness detection

This agent is explicitly tagged as proactive ("Use PROACTIVELY for complex AI orchestration"). It is a specialist advisor, not a workflow runner.

---

### Commands (2 total)

#### /improve-agent

A systematic agent performance improvement workflow spanning 4 phases:

1. **Performance Analysis and Baseline Metrics**
   - Collects 30 days of metrics via `context-manager`: task completion rate, accuracy, tool usage efficiency, token consumption, hallucination incidents
   - Identifies correction patterns, clarification requests, task abandonment points, failure mode classification
   - Produces quantitative baseline: success rate, corrections/task, tool efficiency, satisfaction score, latency, token efficiency ratio

2. **Prompt Engineering Improvements**
   - Chain-of-thought enhancement (explicit reasoning steps + self-verification checkpoints)
   - Few-shot example optimization (positive + negative examples with annotation)
   - Role definition refinement (mission, expertise, behavioral traits, constraints, success criteria)
   - Constitutional AI integration (self-correction principles + critique-and-revise loops)
   - Output format tuning (structured templates, progressive disclosure, markdown optimization)

3. **Testing and Validation**
   - Test categories: golden path, regression (previously failed), edge cases, stress tests, adversarial inputs, cross-domain
   - A/B testing framework: 100 tasks per variant, 95% confidence, Cohen's d effect size
   - Metrics: task completion rate, correctness score, efficiency, hallucination rate, consistency, safety score
   - Human evaluation: blind review, standardized rubric, multiple evaluators, preference ranking

4. **Version Control and Deployment**
   - Semantic versioning for prompt files (MAJOR.MINOR.PATCH)
   - Staged rollout: alpha (5%) → beta (20%) → canary (50%) → full (100%)
   - Rollback triggers: success rate drops >10%, critical errors up >5%, cost up >20%, safety violations
   - 7-day monitoring window post-deployment

**Success criteria**: +15% task success rate, -25% user corrections, no safety regression, <10% latency increase, <5% cost increase.

#### /multi-agent-optimize

A multi-agent performance engineering toolkit. More of a reference document than a runnable workflow:

- **Profiling agents**: Database Performance Agent (query analysis), Application Performance Agent (CPU/memory), Frontend Performance Agent (rendering, Core Web Vitals)
- **Context window optimization**: semantic compression with importance threshold filtering, token budget management
- **Agent coordination efficiency**: parallel execution design, minimal inter-agent communication overhead, fault-tolerant interactions
- **Cost optimization**: token usage tracking, adaptive model selection (haiku for simple tasks, opus for complex), result caching/memoization
- **Latency reduction**: predictive caching, pre-warming contexts, reduced round-trips
- Reference workflows provided for e-commerce platform optimization and enterprise API performance enhancement

---

### SDLC Coverage

| Phase | Coverage |
|---|---|
| Agent design | `/improve-agent` — systematic prompt engineering |
| Agent testing | `/improve-agent` — A/B testing, regression suites |
| Agent deployment | `/improve-agent` — staged rollout, rollback procedures |
| System optimization | `/multi-agent-optimize` — profiling, cost control |

This plugin covers the agent development lifecycle, not the software development lifecycle. It treats AI agents as artifacts that need their own dev cycle.

---

### Handoff Mechanisms

- `/improve-agent` delegates to `context-manager` for historical data collection and performance analytics
- No native team coordination (no TeamCreate/SendMessage primitives used directly)
- Handoff is sequential: analysis → engineering → testing → deployment

---

### Quality Gates and Enforcement

- Explicit rollback triggers with quantitative thresholds (not vague heuristics)
- A/B test minimum sample sizes enforced (100 tasks, p < 0.05)
- Staged rollout prevents full deployment of unvalidated improvements
- Constitutional AI principles integrated into improved agents as self-check loops

---

## Cross-Plugin Comparison

| Dimension | agent-teams | agent-orchestration |
|---|---|---|
| Focus | Runtime workflow orchestration | Agent improvement meta-tooling |
| SDLC phases | Implementation, review, debugging, research, migration | Agent development lifecycle |
| Agent types | team-lead, team-reviewer, team-debugger, team-implementer | context-manager |
| Coordination model | Parallel with explicit file ownership + messaging | Sequential (analysis → engineering → test → deploy) |
| Quality gates | Plan approval, integration verification, shutdown protocol | A/B testing, rollback triggers, staged rollout |
| Requires experimental API | Yes (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1) | No |
| Strongest use case | Feature dev, code review, bug investigation | Improving underperforming agents |

---

## Gaps and Observations

1. **No CI enforcement hook**: `/team-feature` runs build + test via Bash but does not wire in a pre-commit hook or quality gate command. Implementers must pass tests but there is no ruff/ty/mypy equivalent wired in.

2. **Behavioral-only ownership enforcement**: File ownership is enforced through agent behavioral instructions, not OS-level locks or git worktree isolation. A confused implementer could violate boundaries.

3. **No persistent task state**: Tasks and team configs live in `~/.claude/` which is not version-controlled. Team state is lost if Claude Code is restarted mid-task.

4. **agent-orchestration has no README**: Unlike agent-teams, the orchestration plugin has no README.md in its directory. The command files are self-documenting but there is no top-level orientation.

5. **Experimental flag dependency**: agent-teams requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. The `/team-spawn` command does a pre-flight check and halts if not set — good fail-fast behavior but limits portability.

6. **context-manager is model-agnostic**: Uses `model: inherit` — takes whatever model the calling context uses. This is notable vs. all agent-teams agents which hard-code `opus`.

7. **No dream/self-improvement integration**: Neither plugin integrates with the mde dream pipeline or `.generated/learnings/` output pattern used in this repo.

---

## URLs Logged for Source Catalog

- https://github.com/wshobson/agents/tree/main/plugins/agent-teams
- https://github.com/wshobson/agents/tree/main/plugins/agent-orchestration
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/README.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/.claude-plugin/plugin.json
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/agents/team-lead.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/agents/team-implementer.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/agents/team-reviewer.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/agents/team-debugger.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/commands/team-spawn.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/commands/team-feature.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/commands/team-review.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/commands/team-debug.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-teams/commands/team-shutdown.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-orchestration/.claude-plugin/plugin.json
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-orchestration/agents/context-manager.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-orchestration/commands/improve-agent.md
- https://raw.githubusercontent.com/wshobson/agents/main/plugins/agent-orchestration/commands/multi-agent-optimize.md
