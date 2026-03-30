# Adversarial Review: workflow-toolkit / next-workflow-step Skill

**Date**: 2026-03-29
**Reviewer**: reviewer agent (Sonnet)
**Target**: `rsm-subagents/plugins/workflow-toolkit/skills/next-workflow-step/SKILL.md`
**Compared against**: `~/.claude/plugins/cache/nyldn-plugins/octo/9.15.2/workflows/embrace.yaml`, local agent definitions, remember infrastructure

---

## Summary Verdict

The skill is a well-intentioned glue layer but has critical reliability gaps that make it likely to silently lose information in exactly the scenarios it claims to prevent. Three P1 bugs exist around the handoff write path. Several embrace phases are structurally absent from the skill's model. The self-improvement loop is advisory with no enforcement mechanism.

---

## 1. Gaps: SDLC Phases and Transitions Not Covered

### 1.1 No coverage of the embrace clarification intake (P2)

`embrace.md` begins with a mandatory `AskUserQuestion` call gathering scope, focus areas, autonomy mode, and debate gate preferences. The next-workflow-step skill has no concept of this configuration state. If a user's mid-workflow session ends, the handoff template records "Embrace Phase Transition" but drops the autonomy mode that was negotiated at workflow start. The next session will re-enter with default autonomy or guess wrong, potentially skipping gates the user explicitly requested.

### 1.2 No coverage of debate gate state (P1)

`embrace.md` Step 3 describes three distinct debate gate configurations: at the Define→Develop boundary, at both boundaries, or auto-triggered on divergence. The handoff template (Step 5) records only whether "debate is required" as a boolean for the *next* phase. It does not capture:

- Which gate configuration was selected at workflow start
- Whether the Define→Develop gate has already fired
- The outcome of any completed debate (agreed/risks-surfaced/revised)

If a session ends between the Define→Develop debate gate and the start of Tangle, the next session has no way to know the debate already ran with a "proceed with risks" outcome. It will either skip the gate (context lost) or re-run it (duplicate work, user confusion).

### 1.3 No coverage of the Develop→Deliver debate gate (P2)

The skill's phase table maps `tangle → ink` as a simple next-step relationship. It does not model the optional Develop→Deliver gate at all. This gate is described in `embrace.md` Step 3c and is architecturally distinct from the Define→Develop gate.

### 1.4 No coverage of the parallel code-review and E2E agents (P2)

`embrace.md` Step 3d mandates spawning two background agents after Develop completes: a Sonnet code-reviewer and an E2E verification agent. These are long-running, potentially spanning a session boundary. The skill has no concept of "agents in flight" as a state category. If a session ends while these agents are running, the handoff contains no mention of their existence, status, or where to find their output.

### 1.5 No coverage of `~/.claude-octopus/results/` as canonical artifact location (P2)

`embrace.md` and `embrace.yaml` both write outputs to `~/.claude-octopus/results/`. The skill's phase detection logic (Step 2) looks for artifacts named `probe-synthesis-*.md`, `grasp-consensus-*.md`, etc., but does not specify *where* to look. It implicitly assumes the working directory or the repo — those files live outside the repo at `~/.claude-octopus/results/`. Phase detection will fail silently on a fresh session because `glob("probe-synthesis-*.md")` against the repo will return nothing, and the skill will report phase as "ambiguous" rather than correctly detecting the completed phase.

### 1.6 No coverage of the `ink → probe` cycle boundary (P2)

The phase table correctly notes that after Ink the cycle restarts with a new probe. However, the skill has no handling for the case where Ink has just completed and the *next* artifact set would have a new `task_group` identifier. There is no mechanism to carry the `task_group` token across the session boundary, so the next session cannot locate the prior cycle's outputs to use as context for the new probe.

---

## 2. Weaknesses: Where Handoffs Can Fail or Lose Information

### 2.1 The handoff write path is wrong (P1 — silent data loss)

Step 5 instructs writing to `.generated/remember/remember.md`. This conflicts with the existing remember infrastructure documented in `remember-policy.md` and implemented in `_remember_local.py`.

The policy states:

> `remember.md` is a ONE-SHOT briefing: SessionStart reads it, then CLEARS it (`:>`)

The `remember_stop.py` hook appends to `now.md`, not `remember.md`. The `remember_precompact` hook also writes to `now.md`. The manual `/remember` skill is the *only* thing that writes to `remember.md`. If the skill writes to `remember.md` and the user then runs `/clear` without a subsequent `/remember` invocation, `SessionStart` will read the skill's handoff content and immediately wipe it — the next session starts with the handoff gone.

More critically: if the Stop hook fires first (the user closes the session without `/clear`), `now.md` receives a generic checkpoint entry from `remember_stop.py`. The skill's handoff in `remember.md` is preserved but the `now.md` entry does not reference it. The next session's context load order is: `now.md` first, `remember.md` second. If the operator loads in that order, the fallback context may override the structured handoff.

### 2.2 No verification that the handoff write succeeded (P1)

Step 6 says "Verify handoff is written: Confirm `.generated/remember/remember.md` is non-empty." This is advisory — it is a check Claude performs in natural language, not a command with an exit code. If the write silently fails (disk full, permissions, missing parent directory), the skill proceeds as if the handoff is safe. The infrastructure in `_remember_local.py` returns a boolean from `append_now_entry()` and logs a warning on failure, but the skill bypasses this infrastructure entirely by instructing Claude to write directly.

### 2.3 Phase detection relies on artifact filename patterns that may not exist (P1)

The detection table maps artifact filenames to phases:

| Artifact | Phase |
|----------|-------|
| `probe-synthesis-*.md` | Completed Discover |
| `grasp-consensus-*.md` | Completed Define |

These files are written to `~/.claude-octopus/results/` by `orchestrate.sh`. A Claude agent searching for them in the repo will find nothing and fall through to "conversation context" heuristics — which are inherently unreliable across session boundaries. The skill provides no fallback that reads the actual `~/.claude-octopus/results/` directory, and no instruction to check `bridge_config.ledger_path` (`~/.claude-octopus/bridge/task-ledger.json`) which the embrace.yaml schema declares as the authoritative state ledger.

### 2.4 "Ask the user" is the ambiguity resolution strategy for phase detection (P2)

When phase detection is ambiguous (which it will be frequently, per §2.3), the skill falls back to "state your best guess with reasoning and ask the user to confirm." This is not a reliable handoff mechanism — it recreates exactly the problem the skill was designed to solve. The user is asked to remember the phase.

### 2.5 Uncommitted changes check is advisory (P2)

Step 1 says "if there are meaningful changes, ask the user whether to commit before transitioning." The word "meaningful" is undefined and the decision is delegated to the user. A developer who says "no, just hand off" can lose staged changes that are not committed but are also not mentioned in the handoff, because the handoff template has no field for "uncommitted work."

### 2.6 Open issues check has no query to verify (P2)

Step 1.3 checks "Any errors/warnings encountered but not tracked? Create GitHub Issues." This requires the agent to mentally reconstruct the session's errors from conversation context — exactly the kind of recall that degrades as context fills. There is no instruction to run `gh issue list --label auto:agent-discovered` to establish a baseline before creating new issues, which means issues may be double-created across sessions.

---

## 3. Missing Enforcement: What Should Be Enforced But Is Only Advisory

### 3.1 The quality gate check has no enforcement (P1)

The handoff template includes a "Quality gate: [pass/fail]" field. The skill instructs Claude to populate this from memory, but there is no instruction to *run* `uv run mde-py quality` as part of Step 1. The handoff may claim "quality gate: pass" based on a gate that was run hours ago with different code. The `tester` agent enforces the gate via `uv run mde-py quality --strict` with real output — the skill bypasses this agent entirely.

### 3.2 Debate enforcement has no trigger (P2)

Step 4 defines clear criteria for when to mandate debate. But the actual mechanism for "always debate when..." is a recommendation that Claude evaluates and records. There is no hook, no pre-transition check, and no gate that blocks the handoff if debate was required but not run. A session can complete, generate a handoff that says "debate required: yes," and the next session can choose to ignore that note.

### 3.3 No enforcement of session agent types (P2)

The `agent-teams-lifecycle.md` rule is explicit: subagents spawned as team members must use types that have `SendMessage` and `TaskUpdate`. The skill may direct the user to spawn agents in the next session (e.g., "execute `/octo:discover`"), but it never verifies the agent types that were or will be used. If the prior session used a read-only agent type like `claude-code-guide` as a team member, those agents are zombies and their state cannot be recovered — but the skill's phase detection will still try to read their "output."

### 3.4 Git commit enforcement is optional (P2)

The skill asks whether to commit but cannot force it. There is no check equivalent to `git stash --include-untracked` before `/clear`. The no-shell-scripts policy prevents adding a hook here, but the skill should at minimum fail loudly if there are uncommitted changes when the user approves the transition — rather than proceeding silently.

---

## 4. Agent Coordination Gaps

### 4.1 No delegation to the `reviewer` agent (P1)

`embrace.md` Step 3d explicitly spawns a `feature-dev:code-reviewer` Sonnet agent for post-Develop code review. The local `reviewer` agent definition exists at `.claude/agents/reviewer.md` and is the correct agent type for this project. The skill does not reference the `reviewer` agent at all — neither for triggering review before handoff nor for verifying that review completed before declaring Develop done. If the session ends while the review agent is running, there is no mention of this in the handoff.

### 4.2 No delegation to the `tester` agent (P2)

The `tester` agent knows how to run `uv run mde-py quality --strict` and report structured results. Step 1 of the skill asks Claude to populate the quality gate status from memory. The correct implementation would invoke the `tester` agent to produce the authoritative quality gate snapshot before writing the handoff. Using the tester agent would catch regressions that occurred after the last manual run.

### 4.3 No delegation to the `researcher` agent for context capture (P2)

The `researcher` agent has a defined output contract: YAML provenance files to `docs/research/trail/findings/`, append-only source catalog. When the skill instructs Claude to "write research findings to disk," it bypasses the researcher agent's format and paths. If findings are written in freeform markdown to an arbitrary path, they will not be indexed by the research pipeline and will not contribute to the baseline improvement score.

### 4.4 No integration with the dream pipeline (P3)

The self-improvement notes section in the handoff template instructs Claude to note learnings "that should feed into the dream pipeline." But the dream extract hook (`remember_stop.py` calls `dream-extract`) scans `now.md`, not `remember.md` or `docs/research/trail/`. Learnings written only in the handoff's self-improvement section are not automatically discovered by dream extract. They require a manual step (noted in the skill but easily skipped).

---

## 5. Comparison to embrace.yaml: What the Skill Is Missing

### 5.1 Autonomy modes are invisible to the skill

`embrace.yaml` defines three autonomy modes (`supervised`, `semi_autonomous`, `autonomous`) with different `transition_type` values. The skill treats all sessions identically — the handoff template has no field for autonomy mode. A supervised-mode session and an autonomous-mode session produce identical handoff documents. The next session has no way to resume with the correct autonomy mode.

### 5.2 Quality gate thresholds are not captured

`embrace.yaml` defines per-phase quality thresholds: probe at 0.5, grasp at 0.75, tangle at 0.75, ink at 0.80. The handoff records only pass/fail. If a phase passed at 0.76 (barely above the 0.75 threshold for tangle), the next session has no visibility into how close to failure the gate was.

### 5.3 Provider availability is not captured in the handoff

`embrace.yaml` marks codex and gemini as optional providers. `embrace.md` Step 2 mandates a provider availability check. If a session ran with only Claude available (codex and gemini missing), the probe phase used a degraded research corpus. The handoff does not record this degradation. The next session may assume full multi-provider research was completed.

### 5.4 `on_failure` semantics differ between yaml and skill

`embrace.yaml` defines `on_failure: halt` for probe and grasp, `on_failure: retry` for tangle. The skill's Step 3 direction taxonomy (advance/repeat/step-back) does not map onto these. If a phase failed at the yaml level with `on_failure: halt`, the skill may classify the session as "phase complete with repeat direction" rather than recognizing the workflow halted.

### 5.5 `bridge_config` and task-ledger are completely absent

`embrace.yaml` metadata includes:
```yaml
bridge_config:
  ledger_path: "~/.claude-octopus/bridge/task-ledger.json"
  warm_start: true
```

This is the formal state record for warm-starting across sessions. The skill does not read this file in phase detection, does not write to it on handoff, and does not mention it. A warm-start-capable workflow is being handed off cold because the skill ignores the ledger.

### 5.6 `features_required` are not verified

`embrace.yaml` metadata requires `TeammateIdle`, `TaskCompleted`, `agent_memory`, and `task_agent_type` features. The minimum Claude Code version is `2.1.38`. The skill performs no version or feature check before generating a handoff that assumes these features will be available in the next session.

---

## 6. Self-Improvement Gaps

### 6.1 The learnings file path is not in the dream pipeline's scan scope (P2)

Step 7 of the self-improvement protocol writes learnings to `.generated/learnings/workflow-handoff.md`. The dream extract hook scans `now.md` via `remember_stop.py`. It does not scan `.generated/learnings/workflow-handoff.md` unless the dream pipeline's extractor explicitly includes that path. If it does not, learnings accumulate in that file without ever being promoted to the dream pipeline. The skill assumes a scan path that may not exist.

### 6.2 No feedback loop between "what failed" and skill updates (P2)

The self-improvement protocol records issues with issue types (`phase-detection-wrong`, `context-lost`, etc.) but has no mechanism to promote these to skill changes. The dream pipeline's promote step would need to process these specifically. Without an explicit `dream-extract` trigger pointing at `workflow-handoff.md`, the feedback loop is broken at the first step.

### 6.3 Success is not measurable (P3)

Step 1 of the self-improvement protocol asks: "Did the next session successfully pick up the handoff?" There is no automated way to answer this. The skill has no checkpoint that the *receiving* session can write to confirm successful load. The self-improvement loop operates on subjective retrospection, not on observable signals.

### 6.4 No version or changelog for the skill itself (P3)

The skill has no version field and no changelog. The `plugin.json` declares `version: "0.1.0"` but the SKILL.md has no corresponding version. If the skill is updated, there is no way to know whether a handoff was written by the old version or new version, which matters if the handoff format changes between versions.

---

## Priority Matrix

| Finding | Priority | Impact |
|---------|----------|--------|
| Handoff write path conflicts with remember.md lifecycle | P1 | Silent context loss on `/clear` |
| No verification that handoff write succeeded | P1 | Undetected silent failure |
| Phase detection looks in wrong directory for artifacts | P1 | Always "ambiguous", defeats purpose |
| Debate gate config and outcome not captured | P1 | Duplicate or skipped gates next session |
| Quality gate not actually run, populated from memory | P1 | Stale/wrong quality state in handoff |
| `bridge_config` task-ledger ignored | P1 | Warm-start capability unused |
| Parallel review/E2E agents not tracked as in-flight state | P2 | Lost agent results |
| Autonomy mode dropped across session boundary | P2 | Wrong gate behavior next session |
| Provider availability not recorded | P2 | Degraded research not flagged |
| No reviewer/tester agent delegation | P2 | Bypasses project enforcement agents |
| Learnings file not in dream scan path | P2 | Self-improvement loop broken at step 1 |
| `ink → probe` cycle boundary missing task_group carryover | P2 | Next cycle cannot find prior outputs |
| Debate enforcement is advisory only | P2 | Gate can be silently skipped |
| No measurable success signal for self-improvement | P3 | Feedback loop is subjective |
| Skill has no version in SKILL.md | P3 | Handoff format version unknowable |
