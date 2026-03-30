# Debate Synthesis — Workflow Toolkit Architecture

**Date**: 2026-03-29
**Participants**: Opus, Sonnet, Gemini (full Round 2), Codex (failed — CLI prompt parsing)
**Rounds**: 2 (Build vs Assemble, Skill vs Agent Team)

---

## Consensus Map

| Question | Opus | Sonnet | Gemini |
|----------|------|--------|--------|
| Round 1: Build vs Assemble | **Integrate** (use existing octo ledger) | **Assemble** (compose from community patterns) | **Build custom team** |
| Round 2: Skill vs Agent Team | **Hybrid** (skill trigger + command enforcer) | **Agent team** (thin, 4 existing agents + coordinator) | Agent team (implied) |

### Round 1: Three-way split — Integrate vs Assemble vs Build

All participants agree the current skill is fundamentally broken. The
disagreement is about the fix:

- **Opus** says integrate with the existing octo bridge protocol (5 integration
  points, zero new systems). The octo task-ledger already provides warm-start
  state; we just need to read it.
- **Sonnet** says assemble from community patterns (Continuous Claude v3 ledger,
  gmickel receipt gating, existing agents). More components but each is proven.
- **Gemini** says build a custom agent team — argues that "Assemble" and
  "Integrate" are the same philosophy that produced the 6 P1 bugs. Integration
  points ARE failure points. A custom team that owns its state (treating the
  ledger as its primary database, not an external API) eliminates ambiguity.

**Gemini's strongest challenge:** "Opus claims integration is 5 points, not
a build. This is precisely what the failed skill attempted. The P1 bugs
demonstrate that these 5 points are actually 5 points of failure where context
is lost." This is a valid critique — the skill DID try to integrate with
existing infrastructure and failed at every point.

**Counter:** The skill failed not because integration is wrong, but because it
integrated with the WRONG things (searching repo for artifacts that live in
`~/.claude-octopus/`, writing to `remember.md` instead of `now.md`). The fix
is correct integration, not more layers.

**Verdict: Integrate (Opus), with Gemini's critique as a design constraint.**
Integration is correct, but each integration point must have a verified read
(boolean return, file existence check) — not advisory prose. Gemini's "own
the state" principle applies to the implementation: the command should treat
ledger reads as hard requirements, not optional lookups.

### Round 2: Command vs Agent Team — genuine disagreement

- **Opus** argues a command is sufficient — sequential execution, no parallelism
  needed, agent team overhead exceeds the actual work.
- **Sonnet** argues for a thin agent team with TaskCreate/addBlockedBy
  sequencing and receipt artifacts as machine-readable gates.
- **Gemini** argues strongly for a dedicated agent team — "a command is a
  30-second checklist; a workflow transition is a 30-minute reasoning task."
  A Gate-Keeper agent can analyze WHY a gate failed and decide whether to
  repeat or step back. A command can only check a boolean.

**Gemini's strongest challenge:** "The token cost of losing an entire session's
context (the 6 P1 bugs) is infinitely higher than spawning agents." And:
"A command cannot track 'agents in flight' because it terminates."

**Counter:** The "agents in flight" tracking concern is valid but doesn't
require a permanent agent team — it requires state in the ledger. A command
can write "agents_in_flight: [reviewer, tester]" to the ledger and the next
session reads it. The "WHY did the gate fail" analysis is compelling but can
be done by spawning a single reviewer subagent via Task tool, not a full team.

**Verdict: Hybrid with command (Opus), adopting Gemini's "own the state"
principle and Sonnet's receipt pattern.** Start with the command approach.
If real-world usage reveals cases where the command's sequential model fails
(e.g., gates that require adversarial analysis, not just pass/fail), promote
to an agent team in a future iteration. The self-improvement protocol will
capture these cases.

---

## Agreed Action Plan

### Architecture: Skill (discovery) + Command (enforcement)

1. **Keep the skill** as a trimmed discovery trigger (~30 lines)
   - Detects context (user says "next step", "wrap up", etc.)
   - Reads task-ledger for current phase summary
   - Suggests invoking the command

2. **Create a command** `/workflow-toolkit:transition` (~80 lines)
   - Reads `~/.claude-octopus/bridge/task-ledger.json` for phase state
   - Runs `uv run mde-py quality` and writes receipt to `.generated/receipts/`
   - Verifies receipt commit matches HEAD (blocks if stale)
   - Writes structured handoff to `now.md` via `_remember_local.py`
   - Records debate gate state and autonomy mode from ledger

3. **Receipt artifacts** (new, ~10-line JSON schema)
   - Quality gate receipt: `.generated/receipts/quality-{commit}.json`
   - Debate receipt: `.generated/receipts/debate-{timestamp}.json`
   - Command checks receipt freshness before writing handoff

4. **No new agents** — delegate to existing tester/reviewer via Bash/Task
5. **No agent team** — sequential execution in caller's context

### P1 Fixes (all addressed by integration)

| P1 Bug | Fix |
|--------|-----|
| Wrong handoff write path | Write to `now.md` via `_remember_local.py` |
| Phase detection wrong directory | Read `~/.claude-octopus/bridge/task-ledger.json` |
| Quality gate from memory | Run `uv run mde-py quality`, write receipt |
| Debate gate state lost | Record in receipt + ledger |
| bridge_config ignored | Read/write task-ledger as primary state |
| No verified write | Use `_remember_local.py` boolean return |

### Community patterns adopted

| Pattern | Source | How |
|---------|--------|-----|
| Receipt-based gating | gmickel, Spec-Flow | Quality + debate receipt JSON files |
| Ledger-based handoffs | Continuous Claude v3 / octo bridge | task-ledger.json as primary state |
| Goal-met exit conditions | Everything Claude Code, Autoresearch | Receipt freshness check, not fixed rounds |

### Deferred (not needed now)

- MI score tracking (cc-context-stats) — valuable but separate concern
- Branch-per-run experiment tracking — dream pipeline scope, not workflow transition
- Full agent team coordination — over-engineering for sequential workflow

---

## Debate Process Notes

### What worked
- Sonnet's adversarial skill review (6 P1 findings) was the strongest input
- Research across 14 workflow categories provided concrete evidence
- 4-way debate surfaced real architectural disagreement (command vs team)

### What failed
- Codex CLI: `-q` flag not valid in Round 1. In Round 2, `--full-auto`
  worked but prompt parsing included a trailing backtick in the filename,
  causing "file not found." Codex never successfully wrote a debate file.
- Gemini CLI: Shell quote escaping broke Round 1. Round 2 succeeded with
  file-based prompt — wrote a full detailed argument to debate-gemini.md.
- Codex is 0/2 on structured file output; Gemini is 1/2.

### Process improvements (validated by Round 2)
- Write debate prompts to temp files, pass via `$(cat /tmp/prompt.txt)` — WORKS
- Gemini successfully writes files when prompt is clean — confirmed Round 2
- Codex needs a different approach: either `codex -i /tmp/prompt.txt` if
  supported, or pre-create the output file and use `codex --full-auto` with
  explicit `cat > file` instructions in the prompt
- Never use `-q` flag with codex (not a valid flag)
- The `mde debate` library should wrap these CLIs with output validation:
  check if expected file exists after CLI exits, retry or extract from stdout
