# Debate — Workflow Toolkit Architecture

**Participant**: Reviewer (claude-sonnet-4-6)
**Date**: 2026-03-29
**Position**: Assemble over Build; Agent Team required for SDLC enforcement

---

## Round 1: Build vs Assemble

**Position: Assemble from existing primitives. Building a custom agent team from scratch is the wrong answer.**

### The evidence against building custom

The research-awesome-workflows.md cataloged 14 categories of community workflows. In almost every category, proven, battle-tested tools already exist that implement the exact patterns the current skill is missing. The gap list is not a case for building — it is a shopping list:

- **Receipt-based gating** is already implemented in gmickel (548 stars) and Spec-Flow (73 stars). Building a custom gate mechanism when two working implementations exist violates the library-first policy and introduces new surface area to debug.
- **Ledger-based handoffs** are already implemented in Continuous Claude v3 (3,619 stars). The Continuous Claude v3 pattern uses explicit state files that persist between context windows — documented as "more reliable than remember.md lifecycle" precisely because it decouples handoff persistence from the one-shot remember.md lifecycle. The current skill's P1 failure — writing to remember.md which gets cleared on SessionStart — would not exist if we assembled from Continuous Claude v3's ledger pattern instead of inventing our own.
- **Goal-met exit conditions** are already validated by Everything Claude Code (17K stars) and Autoresearch. Fixed-round loops are described as an anti-pattern by multiple sources; the community has converged on evaluated objectives.
- **Cross-LLM debate** is already working as `mde debate`. The research confirms agent-council (118 stars), claude-review-loop (603 stars), and the existing `mde debate` library all solve the same problem with the same approach. The debate gate in the skill is advisory and has no enforcement — because enforcing it requires a mechanism we already have.

### The embrace.yaml is not ours to duplicate

The skill-analysis review found that the `next-workflow-step` skill attempts to replicate concepts already formally defined in `~/.claude/plugins/cache/nyldn-plugins/octo/9.15.2/workflows/embrace.yaml`: autonomy modes, per-phase quality gate thresholds, provider availability, on_failure semantics, bridge_config ledger. The skill gets all of these wrong — it drops autonomy mode, loses quality gate thresholds (reducing them to pass/fail), ignores the ledger path entirely.

This is the cost of building: you reimplement someone else's formal schema from memory and introduce divergence. The embrace.yaml already has:
- `bridge_config.ledger_path: "~/.claude-octopus/bridge/task-ledger.json"` with `warm_start: true`
- Per-phase quality thresholds (probe: 0.5, grasp: 0.75, tangle: 0.75, ink: 0.80)
- Three autonomy modes with different `transition_type` values
- `on_failure: halt`, `on_failure: retry`, `on_failure: escalate` semantics per phase

A skill that wraps these should read from them, not re-model them. The correct assembly is: read the ledger, report the schema-defined state, transition according to schema-defined rules. That is six lines of Python, not a SKILL.md that grows to 200 lines and still misses the source of truth.

### The counter-argument fails under inspection

The natural counter to "assemble" is: "these community tools don't fit our exact workflow." Let's test that claim against the P1 bugs:

1. **Handoff write path wrong** — Continuous Claude v3's ledger pattern does not use remember.md at all. Assembling from it eliminates this P1 by design.
2. **Phase detection looks in wrong directory** — The octo plugin owns `~/.claude-octopus/results/`. A wrapper that calls the octo CLI to query state instead of grepping the repo eliminates this P1 by design.
3. **Quality gate populated from memory** — The `tester` agent already exists and runs `uv run mde-py quality`. Delegating to it is assembly, not building.
4. **bridge_config task-ledger ignored** — embrace.yaml declares this as the authoritative state ledger. Reading it is assembly; continuing to ignore it is building a parallel state mechanism that will diverge.

All four P1 bugs are eliminated by composing from existing primitives rather than building a new prose-driven skill.

### What "assemble" concretely means here

Assemble does not mean "write no code." It means:

1. Read `~/.claude-octopus/bridge/task-ledger.json` as the authoritative phase state source (octo already writes this)
2. Write handoff to `now.md` via the `_remember_local.py` infrastructure (already exists, already has error handling, already has boolean return on failure)
3. Delegate quality gate verification to the `tester` agent (already exists)
4. Delegate code review to the `reviewer` agent (already exists)
5. Trigger debate via `mde debate` (already exists)
6. Adopt Continuous Claude v3's ledger pattern for cross-session state (3,619 stars, battle-tested)

The skill becomes: read the ledger, delegate to agents, write to now.md via existing infrastructure, commit. That is the right scope for a skill. Anything larger belongs in a dedicated agent.

---

## Round 2: Skill vs Agent Team

**Position: A skill-only approach is insufficient for SDLC enforcement. An agent team is required, but it must be thin and composed from existing agents — not a new layer of custom coordination logic.**

### The fundamental problem with skill-only enforcement

The skill-analysis review found six categories of enforcement gaps. Every one of them has the same root cause: a skill runs in the caller's context and can only recommend actions; it cannot compel them.

Consider the enforcement requirements that SDLC actually needs:

- Quality gate must have been run on the *current* code, not from memory
- Debate gate must have fired when required, with a machine-readable outcome
- Handoff must have been verified as written, not assumed written
- Agents in flight must be tracked as explicit state, not inferred from conversation context

None of these can be enforced by a skill. A skill is prose. Prose cannot block a transition. The tangle phase has `transition: type: quality_gate` in embrace.yaml — that is a machine-enforced gate. The skill produces a template with a "quality gate: pass/fail" field populated from memory. These are not the same thing.

The adversarial review's finding in §3.1 is damning: "The handoff may claim 'quality gate: pass' based on a gate that was run hours ago with different code." This is not a bug in the skill's implementation — it is a structural limitation of the skill abstraction for enforcement purposes.

### The agent-teams-lifecycle.md policy already defines the correct pattern

The `agent-teams-lifecycle.md` rule (loaded into every session) documents exactly what is needed:
- An orchestrator that coordinates the workflow
- TaskCreate/TaskUpdate with dependencies (addBlockedBy) for cross-agent sequencing
- Shutdown protocol that guarantees agent termination
- Agent types with SendMessage and TaskUpdate

A skill cannot do any of this. A skill cannot TaskCreate. A skill cannot spawn a background tester agent and wait for its exit code. A skill cannot use addBlockedBy to block the handoff until the reviewer agent returns. Only an agent team can do this.

### The case against a heavy custom team

Here is where the "agent team required" argument must be constrained, or it becomes the wrong answer. The research-awesome-workflows.md cataloged multi-agent frameworks with 11 agents (claude-forge), 6 specialists (Solopreneur), 28 agents (Everything Claude Code). These are impressive but they are also maintained systems with update burden. The feedback memory explicitly states "Assemble don't build" and "find existing tools first."

The correct agent team for this project is thin:
- **Orchestrator** role: the existing `researcher` agent, scoped to read the task-ledger, assess phase state, and coordinate delegation
- **Gate-keeper** role: the existing `tester` agent, run against current code, returning machine-readable pass/fail with threshold scores
- **Reviewer** role: the existing `reviewer` agent (already defined at `.claude/agents/reviewer.md`)
- **State manager**: not a new agent — this is the `_remember_local.py` infrastructure plus the octo ledger

The four roles are already filled by existing agents. What is missing is not more agents — it is a thin coordinator that uses TaskCreate/addBlockedBy to sequence them and collects their machine-readable outputs before writing the handoff.

### The gmickel receipt pattern is the minimum viable gate

From research-awesome-workflows.md §2, gmickel's receipt-based gating is described as: "only proceed to next phase when prior phase emits a machine-readable receipt artifact — prevents silent phase skips that bypass quality checks." The receipt artifact is the key concept missing from the current skill.

A receipt is simply: when the tester agent runs `uv run mde-py quality`, it writes a JSON receipt to `.generated/receipts/quality-{timestamp}.json` with the gate result, threshold scores, and test counts. The orchestrator reads this receipt — not memory, not conversation context — before writing the handoff. If no receipt exists or the receipt is stale (older than the most recent commit), the transition is blocked.

This is the minimum viable gate-keeper. It does not require a framework. It requires: a receipt write in the tester agent, a receipt read in the coordinator, and a staleness check. Three changes to existing code. But it cannot be a skill — it requires an agent that calls other agents and evaluates their outputs.

### The skill approach's deepest structural problem

The research-skill-analysis.md §2.4 identifies this precisely: "When phase detection is ambiguous — which it will be frequently — the skill falls back to 'state your best guess with reasoning and ask the user to confirm.' This is not a reliable handoff mechanism — it recreates exactly the problem the skill was designed to solve. The user is asked to remember the phase."

Skills degrade gracefully when context is healthy and degrade catastrophically when context degrades — which is exactly the condition that triggers session boundaries. An agent team with a ledger reader does not degrade with context; it reads state from a file. The ledger is the authoritative source regardless of how much context has been consumed.

The MI score tracking documented in cc-context-stats confirms this: context degradation is measurable, and the degraded state is precisely when handoffs become most critical. A skill that depends on Claude's recall of conversation context for phase detection will fail hardest at the moment it matters most. An agent that reads `~/.claude-octopus/bridge/task-ledger.json` does not degrade.

### Concrete recommendation

Not a full agent team — a minimal coordinator:

1. **Promote the skill to a command** with `allowed-tools` that includes Task delegation
2. **The command spawns three background agents** using the existing agent types: tester (quality gate), reviewer (if code was changed), researcher (updates ledger and provenance)
3. **Receipt artifacts** gated via addBlockedBy: the handoff write is blocked until tester receipt exists and is newer than HEAD
4. **State written to now.md via `_remember_local.py`**, not directly to remember.md
5. **Ledger read at start, ledger write at end** using `~/.claude-octopus/bridge/task-ledger.json` as defined by embrace.yaml

This is assembly from four existing agents plus a thin coordinator command. It is not a custom framework. It eliminates all six P1 bugs. The coordinator is ~50 lines. The receipt format is a 10-line JSON schema.

### Why the current skill structure should not be patched in place

The skill has 6 P1 bugs and 6 P2 issues. The P1 bugs are not implementation errors — they are structural: the skill model is wrong about where state lives (`~/.claude-octopus/results/` not the repo), wrong about the handoff write path (now.md not remember.md), and wrong about where quality gate truth comes from (tester agent output not memory). Patching these in a SKILL.md file is adding machine-readable constraints to a prose document. That is fighting the abstraction.

The right fix is to lift the enforcement concerns out of the skill and into a thin command that delegates to agents and uses machine-readable receipts. The skill survives as the "suggest this workflow exists" trigger — which is exactly what skill frontmatter description is for. The coordination logic moves to a command.

---

## Summary

**Round 1**: Assemble. All six community patterns missing from the current skill are already implemented in battle-tested tools. The four P1 bugs are all eliminated by composing from existing primitives (octo ledger, `_remember_local.py`, tester agent, Continuous Claude v3 ledger pattern) rather than building a parallel mechanism that diverges from the source of truth.

**Round 2**: Agent team required, but thin. A skill cannot enforce a gate — it can only recommend. The four agent roles needed are already filled by existing agents (researcher, tester, reviewer, plus the octo ledger as state manager). The gap is a thin coordinator command that uses TaskCreate/addBlockedBy to sequence them and receipt artifacts to make gate state machine-readable. Patching the P1 bugs inside a SKILL.md fights the abstraction. Lift enforcement to a command; keep the skill as the discovery trigger.
