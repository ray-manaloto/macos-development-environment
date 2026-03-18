# Claude-Flow Learning Pipeline Improvements

Status: Draft
Created: 2026-03-17
Based on: docs/research/agent-self-learning-landscape.md

---

## Prioritized Improvements

| Priority | Improvement | Effort | Impact | Source Framework(s) | Description |
|----------|-------------|--------|--------|---------------------|-------------|
| P0 | Auto-store patterns on successful task completion | Low | High | DSPy, CrewAI | Wire post-task hook to automatically store successful patterns with quality metadata |
| P0 | Auto-search memory before starting any task | Low | High | Letta, LangGraph | Wire pre-task hook to search memory for relevant patterns and inject them into context |
| P1 | Pattern quality scoring + decay | Medium | High | Letta/MemGPT, DSPy | Score patterns by usage frequency, success rate, and age; auto-prune low-value ones |
| P1 | Cross-session knowledge transfer | Medium | Medium | Semantic Kernel | Transfer patterns from project-level to global memory when they generalize |
| P1 | Structured reflection after multi-step tasks | Medium | High | AutoGen, DSPy | After complex tasks, evaluate what worked and what didn't; store meta-patterns |
| P2 | Collaborative learning from swarm agents | High | Medium | CrewAI, AutoGen | When multiple agents work on related tasks, merge their learned patterns |
| P2 | Automatic prompt optimization from memory | High | High | DSPy | Use accumulated patterns to dynamically optimize prompts for specific task types |
| P2 | Tool selection learning | Medium | Medium | LangGraph, Semantic Kernel | Track which tools work best for which task types; auto-suggest optimal toolsets |
| P3 | Graph-based knowledge representation | High | Medium | LangGraph, Letta | Move beyond flat key-value patterns to connected knowledge graphs |
| P3 | Confidence-calibrated predictions | High | Medium | DSPy | Track prediction accuracy over time; calibrate confidence scores |
| P3 | Adversarial self-testing | High | High | OpenHands | Generate edge cases from learned patterns; test against them |

---

## P0: Auto-Store Patterns on Successful Task Completion

### Current state

The post-task hook (`npx @claude-flow/cli@latest hooks post-task --task-id "[id]" --success true --store-results true`) exists and can store results. However, invocation depends entirely on Claude Code remembering to call it after each task. In practice, this is inconsistent — the hook is called in some sessions and forgotten in others. There is no enforcement mechanism, and the stored data lacks structured quality metadata (what approach was used, which tools, how complex the task was).

### Proposed change

Make pattern storage automatic and guaranteed by adding a wrapper that always runs after task completion. Store structured metadata alongside the pattern: task type, tools used, file count, success/failure, duration, and a short summary of the approach.

### Implementation steps

1. Add a shell function `mde_post_task_store` in `scripts/lib/` that wraps the post-task hook with structured metadata collection. It should accept task-id, task-type, success boolean, and a summary string.
2. Update `CLAUDE.md`'s post-task protocol to make the store call non-optional — move it from the "Auto-Learning Protocol" suggestion section into a mandatory step in the task completion flow.
3. Define a standard metadata schema for stored patterns: `{ task_type, tools_used[], file_count, duration_seconds, success, summary, timestamp }`. Store this as the `--value` in JSON format.
4. Add a `--namespace` convention: `task-outcomes` for raw outcomes, `patterns` for distilled reusable patterns (manually or automatically promoted).
5. Validate by running 5 sample tasks and confirming that all 5 produce entries in `task-outcomes` namespace via `memory list --namespace task-outcomes`.

### Success criteria

- Every completed task (success or failure) produces a memory entry within 2 seconds of completion.
- Entries contain structured JSON with all required metadata fields.
- Entries are retrievable via `memory search` with relevant keywords.

### Risks

- **Storage bloat**: Every task produces an entry. Mitigated by P1 (quality scoring + decay) and by using a separate `task-outcomes` namespace that can be pruned aggressively.
- **Inconsistent metadata**: If the wrapper function is not called uniformly, metadata quality varies. Mitigated by making the wrapper the single entry point for task completion reporting.

---

## P0: Auto-Search Memory Before Starting Any Task

### Current state

The pre-task hook (`npx @claude-flow/cli@latest hooks pre-task --description "[task]"`) exists and returns routing recommendations. Memory search (`memory search --query "[keywords]"`) is available. However, these are separate operations, and the memory search step is frequently skipped. When it is performed, the results are not consistently injected into the agent's initial context.

### Proposed change

Combine pre-task routing and memory search into a single mandatory step that runs before any task begins. The combined output should include: routing recommendation, relevant past patterns (top 3-5), and any relevant past failures to avoid.

### Implementation steps

1. Create a `mde_pre_task_context` shell function in `scripts/lib/` that runs both `hooks pre-task` and `memory search` in parallel, merges the output, and formats it as a context block.
2. The function should search across multiple namespaces: `patterns` (reusable approaches), `task-outcomes` (past similar tasks), and `solutions` (known fixes).
3. Update `CLAUDE.md` to include the context injection as the first mandatory step before any task execution — not as a suggestion but as a required protocol step.
4. Format the output as a structured block that agents can parse: `## Relevant Past Patterns`, `## Past Task Outcomes`, `## Routing Recommendation`.
5. Test by starting 3 different task types (bug fix, feature, refactor) and confirming that relevant patterns are surfaced each time.

### Success criteria

- Every task start produces a context block within 3 seconds.
- When relevant patterns exist in memory, they appear in the context block.
- Agents reference retrieved patterns in their approach (verifiable in task logs).

### Risks

- **Irrelevant pattern injection**: If the memory store is noisy, retrieved patterns may confuse rather than help. Mitigated by P1 (quality scoring) and by limiting results to top 3 with a similarity threshold.
- **Latency**: Adding a memory search to every task start adds 1-3 seconds. Acceptable for the value provided.

---

## P1: Pattern Quality Scoring + Decay

### Current state

Stored patterns have no quality metadata beyond what was manually added at storage time. There is no tracking of how often a pattern is retrieved, whether tasks that used it succeeded, or how old it is. The memory store will grow monotonically without pruning.

### Proposed change

Add a scoring system: `quality = (retrieval_count * success_rate) / age_factor`. Patterns below a threshold are flagged for review or auto-pruned. Implement this as a background worker that runs periodically.

### Implementation steps

1. Extend the stored pattern metadata to include `retrieval_count`, `success_after_retrieval_count`, and `created_at` fields.
2. When a pattern is retrieved during pre-task context, increment its `retrieval_count`. When the subsequent task succeeds, increment `success_after_retrieval_count`.
3. Create a `consolidate-patterns` script that calculates quality scores and prunes entries below a configurable threshold (default: score < 0.1 after 30 days).
4. Wire this script to the existing `consolidate` background worker via `hooks worker dispatch --trigger consolidate`.
5. Add a `memory stats --namespace patterns` command variant that reports pattern count, average quality, and age distribution.

### Success criteria

- After 2 weeks of use, the memory store contains scored patterns with non-zero retrieval counts.
- Low-quality patterns (never retrieved, or always followed by failure) are flagged or pruned.
- Memory search results are ranked by quality score, not just semantic similarity.

### Risks

- **Premature pruning**: New patterns have low scores by definition. Mitigated by a grace period (no pruning for patterns less than 7 days old).
- **Cold start**: Initially all patterns have zero retrieval data. The system operates in "accumulate" mode until enough data exists for meaningful scoring.

---

## P1: Cross-Session Knowledge Transfer

### Current state

Memory is per-project. Patterns learned in one project are not available in others. The `hooks transfer` command supports IPFS-based pattern sharing, but it is not integrated into the standard workflow and requires manual invocation.

### Proposed change

When a pattern has been successfully used in 3+ separate sessions within a project, automatically promote it to a `global` namespace. When starting work in any project, search the `global` namespace in addition to project-local namespaces.

### Implementation steps

1. Add a `session_count` field to pattern metadata. Increment it when a pattern is retrieved in a new session (deduplicated by session ID).
2. In the `consolidate-patterns` script, identify patterns with `session_count >= 3` and `success_rate > 0.7`. Copy these to a `global` namespace stored in a shared location (`~/.claude-flow/global-memory/`).
3. Update `mde_pre_task_context` to also search the `global` namespace, appending results under a `## Global Patterns` heading.
4. Add a `memory promote --key "[key]" --to global` command for manual promotion.

### Success criteria

- After 3+ sessions using a pattern, it appears in the global namespace.
- Starting a new project surfaces relevant global patterns in pre-task context.
- Global patterns can be distinguished from project-local patterns in search results.

### Risks

- **Context pollution**: Global patterns may not apply to all projects. Mitigated by tagging patterns with domain/language metadata and filtering on retrieval.
- **Storage location**: The global store location (`~/.claude-flow/`) must exist and be writable. Initialization check needed.

---

## P1: Structured Reflection After Multi-Step Tasks

### Current state

After swarm execution or multi-step tasks, there is no systematic evaluation of what worked and what did not. Task outcomes are stored (if the hook is invoked) but there is no meta-analysis step that identifies reusable patterns from the execution.

### Proposed change

After any task involving 3+ steps or swarm coordination, automatically spawn a reflection step that reviews the task log, identifies what worked well and what failed, and stores distilled meta-patterns.

### Implementation steps

1. Define a reflection prompt template that takes as input: task description, steps taken, tools used, outcomes at each step, and final result. The template asks for: what worked, what failed, what would be done differently, and 1-3 reusable patterns.
2. Add a `mde_reflect_on_task` function that runs after multi-step tasks. It collects the task log, invokes the reflection prompt, and stores the output in the `meta-patterns` namespace.
3. Update the swarm completion protocol in `CLAUDE.md` to include reflection as a mandatory final step after result synthesis.
4. Meta-patterns should reference the source task and include applicability conditions (when should this pattern be used?).
5. Test by running 2 swarm tasks and verifying that reflection entries are created with actionable meta-patterns.

### Success criteria

- Every swarm task or multi-step task (3+ steps) produces a reflection entry.
- Reflection entries contain at least one actionable meta-pattern with applicability conditions.
- Meta-patterns are retrievable via memory search and surfaced in pre-task context for similar future tasks.

### Risks

- **Reflection quality**: The reflection is only as good as the prompt and the task log. Mitigated by using a well-tested reflection template and including structured task metadata.
- **Cost**: An extra LLM call per multi-step task. Mitigated by routing reflection to Haiku (sufficient for meta-analysis) and only triggering for tasks with 3+ steps.

---

## Implementation Sequence

```
Phase 1 (Week 1): P0 items
  - Implement mde_post_task_store wrapper
  - Implement mde_pre_task_context wrapper
  - Update CLAUDE.md protocols
  - Validate with 5 sample tasks

Phase 2 (Week 2-3): P1 items
  - Add quality scoring metadata
  - Implement consolidate-patterns worker
  - Add cross-session promotion logic
  - Implement reflection template and trigger

Phase 3 (Week 4+): P2 items
  - Collaborative swarm learning
  - Prompt optimization prototype
  - Tool selection tracking

Phase 4 (Future): P3 items
  - Graph-based knowledge representation
  - Confidence calibration
  - Adversarial self-testing
```

---

## Dependencies

- claude-flow CLI v3 with memory and hooks commands operational
- SQLite-backed memory store initialized (`memory init`)
- Background worker daemon running (`daemon start`)
- CLAUDE.md protocols adopted by all agent users

## Metrics to Track

| Metric | Baseline | Target (4 weeks) |
|--------|----------|-------------------|
| Tasks with auto-stored outcomes | ~20% | 95%+ |
| Tasks with pre-task memory search | ~10% | 95%+ |
| Patterns with quality scores | 0% | 80%+ |
| Cross-session pattern reuse | None | 5+ patterns promoted |
| Reflection entries per week | 0 | 3-5 per active week |
