# Debate — Workflow Toolkit Architecture

**Participant**: Opus (claude-opus-4-6)
**Date**: 2026-03-29
**Position**: Assemble with ledger integration; Hybrid skill+command architecture

---

## Round 1: Build vs Assemble

**Position: Assemble — but with a critical nuance Sonnet underweights.**

I agree with Sonnet's core argument that all six P1 bugs map to existing
primitives being ignored. The evidence is unambiguous:

- The octo task-ledger at `~/.claude-octopus/bridge/task-ledger.json` IS the
  authoritative state. The skill ignores it. Reading it eliminates P1 #2, #4, #5.
- `_remember_local.py` IS the correct write path. Using it eliminates P1 #1, #6.
- The tester agent IS the quality gate authority. Delegating eliminates P1 #3.

**Where I diverge from Sonnet:** the assembly target is not just "existing agents
plus a coordinator." The assembly must also include the octo bridge protocol.
embrace.yaml declares `warm_start: true` — this means the octo plugin already
expects cross-session state persistence. We are not building a new state
management system; we are plugging into one that already exists and is already
being ignored.

The Continuous Claude v3 ledger pattern (cited in the research) is architecturally
identical to the octo bridge pattern. Both use a JSON file as cross-session state.
We don't need to adopt Continuous Claude v3 — we need to stop ignoring the ledger
we already have.

**The build-vs-assemble question has a third answer: integrate.** The octo plugin
already provides the state management, quality gates, and phase definitions. Our
skill built a parallel system that conflicts with the real one. The correct fix
is not to assemble a new coordination layer from community tools — it is to
integrate with the coordination layer we are already paying for via the octo plugin.

### Concrete integration points

1. **Read** `~/.claude-octopus/bridge/task-ledger.json` for phase state
2. **Read** `~/.claude-octopus/results/` for phase artifacts
3. **Write** handoff to `now.md` via `_remember_local.py` (verified boolean return)
4. **Delegate** to tester agent for quality gate (receipt artifact)
5. **Use** `mde debate` for adversarial gates (already exists)

This is 5 integration points, not a build. Zero new frameworks, zero new state
management, zero new agents.

---

## Round 2: Skill vs Agent Team

**Position: The skill should remain as the entry point. A thin command handles
enforcement. No new agent team is needed.**

I agree with Sonnet that a skill cannot enforce gates. But I disagree that we
need an "agent team" — even a thin one. Here's why:

### The coordination overhead is not justified

The agent-teams-lifecycle.md policy documents the overhead of agent teams:
- TeamCreate before spawning
- Background mode coordination
- Shutdown protocol with structured JSON
- SendMessage/TaskUpdate requirements

For a workflow transition that takes 30 seconds of real work (read ledger, run
quality gate, write handoff), spawning an agent team is over-engineering. The
agent team abstraction is designed for parallel workstreams that run for minutes
to hours. A workflow transition is a sequential checklist.

### Commands can enforce without teams

A command (in `rsm-subagents/plugins/workflow-toolkit/commands/`) has
`allowed-tools` that includes Bash, Read, Write, and Task. A command CAN:
- Run `uv run mde-py quality` directly via Bash
- Read the task-ledger via Read
- Write receipts via Write
- Spawn a single tester subagent via Task if needed

A command CANNOT spawn a team, but it doesn't need to. The enforcement is
sequential: check state → run gate → verify gate passed → write handoff.
There's no parallelism to coordinate.

### The hybrid architecture

1. **Skill** (`next-workflow-step`): Triggers when the user says "next step",
   "wrap up", etc. The skill's job is DISCOVERY — detect the situation and
   invoke the command. The skill becomes ~30 lines: detect context, print
   phase summary, suggest invoking the command.

2. **Command** (`/workflow-toolkit:transition`): Handles ENFORCEMENT. Reads
   the task-ledger, runs quality gate, writes receipt, writes handoff to
   now.md. Has `allowed-tools` for Bash/Read/Write. This is where the
   machine-readable gates live. ~80 lines.

3. **No new agents**: The tester, reviewer, and researcher agents already
   exist. The command delegates to them via Bash (`uv run mde-py quality`)
   or Task tool, not via an agent team.

### Why this is better than a team

| Concern | Agent Team | Command |
|---------|-----------|---------|
| Context overhead | Spawns 3-4 agents (each with full context load) | Runs in caller's context |
| Shutdown complexity | Requires structured shutdown_request per agent | No agents to shut down |
| Failure mode | Zombie agents if shutdown fails | Command exits cleanly |
| Token cost | 3-4x context window loads | 1x (no subagent context) |
| Time | Agent spawn + coordination + shutdown | Sequential execution |

The agent team abstraction adds value when you need parallelism and isolation.
A workflow transition needs neither.

### Receipt artifacts — the real missing piece

The community research identified receipt-based gating as the key pattern.
Both Sonnet and I agree on this. The implementation is trivial:

```json
{
  "type": "quality-gate",
  "timestamp": "2026-03-29T18:30:00Z",
  "commit": "f65675a",
  "result": "pass",
  "tests": 606,
  "warnings": 2,
  "threshold": 0.75,
  "score": 1.0
}
```

Written to `.generated/receipts/quality-{commit}.json`. The command reads
this before writing the handoff. If the receipt's commit doesn't match HEAD,
the command runs the gate. If it matches, it reuses the result.

---

## Dissent from Sonnet

### Sonnet overcomplicates the coordinator

Sonnet proposes: "Promote the skill to a command, spawn three background agents
(tester, reviewer, researcher), gate via addBlockedBy, write to now.md via
_remember_local.py."

This is over-engineered. The three background agents add:
- 3 context window loads (~50K tokens each)
- Shutdown protocol for each
- addBlockedBy dependency management
- TaskCreate/TaskUpdate bookkeeping

For what? Running `uv run mde-py quality` via Bash takes 6 seconds. Reading
the ledger takes 1 line. Writing the handoff takes 5 lines. The total
execution is under 30 seconds. The agent team coordination overhead exceeds
the actual work.

### Gemini's verdict is correct but unsupported

Gemini says "Build a Custom Agent Team. Stop trying to fix a glue layer."
The conclusion is directionally right (the skill is a broken glue layer)
but the solution is wrong. You don't fix a glue layer by adding MORE layers
(an agent team). You fix it by connecting to the existing system properly
(the octo ledger).

---

## Final Position

**Round 1**: Integrate, not build or assemble. The octo bridge protocol already
provides cross-session state. The skill ignores it. Fix: read the ledger,
delegate to existing agents via Bash, write to now.md. Five integration points,
zero new systems.

**Round 2**: Hybrid skill + command. The skill remains as the discovery trigger.
A new command handles enforcement with machine-readable receipts. No agent team
needed — the coordination overhead exceeds the actual work. Sequential execution
in the caller's context is sufficient.
