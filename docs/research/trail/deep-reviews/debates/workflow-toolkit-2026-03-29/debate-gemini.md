# Debate — Workflow Toolkit Architecture

**Participant**: Gemini (gemini-2-0-flash)
**Date**: 2026-03-29
**Position**: Build a Custom Agent Team; Dedicated Agent Team for Enforcement

---

## Round 1: Build vs Assemble

**Position: Build a Custom Agent Team. Stop trying to fix a glue layer with more glue.**

I disagree with both Sonnet and Opus. Their "Assemble" and "Integrate" positions are essentially an attempt to double down on the very "glue layer" philosophy that resulted in 6 P1 critical bugs. The adversarial review found that the current `next-workflow-step` skill is a "well-intentioned glue layer" that fails because it doesn't own its state, its logic, or its enforcement.

### The Failure of Assembly
Sonnet argues for assembling from existing primitives like `Continuous Claude v3` and `gmickel`. However, the research in `research-awesome-workflows.md` shows that these high-star projects are successful precisely because they are **integrated frameworks**, not loosely coupled scripts. "Assembling" from different plugins created by different authors with different state assumptions is how we ended up writing to `remember.md` (P1 #1) while the octo plugin expects artifacts at `~/.claude-octopus/results/` (P1 #2).

### Why "Build" is the Only Path to P1 Remediation
1. **First-Class State Ownership**: Integration (Opus's preference) assumes the `task-ledger.json` is sufficient. But P1 #4 and #5 show that the ledger is being ignored because the *skill doesn't own the reading logic*. A custom-built agent team treats the ledger not as an external "bridge" to check, but as its primary database.
2. **Eliminating the "Ambiguity" Fallback**: Sonnet notes that the current skill's fallback is "ask the user" (P2 #2.4). This is the inevitable result of assembly. When you glue two systems together, the seams are always ambiguous. A custom-built team defines the "Embrace" lifecycle natively, eliminating the need to guess between conflicting plugin states.
3. **Receipt-Based Gating as a Primitive**: Research (§2) highlights "Receipt-based gating" as a community standard. Attempting to "assemble" this via commands (Opus) or prose (the current skill) is what leads to P1 #3 (quality gates populated from memory). A custom team can implement receipts as a first-class file-system event, ensuring the Gate-Keeper agent cannot proceed without a verified artifact.

### Addressing Opus's "Integrate" Fallacy
Opus claims that "integration is 5 points, not a build." This is precisely what the failed skill attempted. The P1 bugs demonstrate that these "5 points" are actually 5 points of failure where context is lost. Integrating with the `octo` bridge protocol is necessary, but it is a **component** of a custom build, not a substitute for it.

---

## Round 2: Skill vs Agent Team

**Position: A Dedicated Agent Team is mandatory. A "Hybrid Command" is a brittle checklist that will fail the first time a gate is missed.**

I disagree with Opus's claim that an agent team is "over-engineering." Opus views a workflow transition as a "30-second sequential checklist." This fundamentally misinterprets the Double Diamond workflow.

### The "Adversarial" Requirement
The `next-workflow-step` skill exists to enforce "adversarial debate on complex decisions" (Skill §1). A command-line script (Opus's hybrid) cannot participate in a debate. It can only check a boolean. 
- If the `tangle` phase (Develop) fails its quality gate, a command simply exits non-zero.
- A **Gate-Keeper Agent**, however, can analyze *why* it failed, look at the `tangle-implementation-*.md` artifact, and decide whether we need to "Repeat" or "Step back" (Skill Step 3).

### Why Skills and Commands Fail the SDLC
The research-skill-analysis.md (§3.1) is the most critical piece of evidence: "The handoff may claim 'quality gate: pass' based on a gate that was run hours ago." 
- **Skill-only**: Advisory prose. (P1 #3)
- **Command-only**: Brittle exit codes. If the disk is full or permissions are wrong (P1 #2.2), a command might fail, but it can't self-remediate or explain the state to the next session.
- **Agent Team**: An `Orchestrator` agent combined with a `State-Manager` agent (Continuous Claude v3 pattern) ensures that "In-flight work" (P2 #1.4) is tracked. A command cannot track "agents in flight" because it terminates.

### The "Overhead" is the Security
Opus worries about the token cost of spawning agents. I argue that the token cost of **losing an entire session's context** (the 6 P1 bugs) is infinitely higher. 
- The **Orchestrator** manages the ledger and `_remember_local.py` path (Remediating P1 #1, #5, #6).
- The **Gate-Keeper** runs the `tester` agent and verifies receipts (Remediating P1 #3).
- The **State-Manager** ensures artifacts are in `~/.claude-octopus/results/` (Remediating P1 #2).

### Unique Perspective: The "Domain-Specific Team"
We should not build a *generic* agent team, but a **Workflow-Native Team**. This team's "context" is the `embrace.yaml` and the `task-ledger.json`. By having agents dedicated to these roles, we move from "asking the user to remember the phase" (P2 #2.4) to a system where the agents **own the memory**.

As noted in `research-awesome-workflows.md` (§3), the "Founder OS queue with blocked_by" is the closest community pattern to a formal dependency graph. We should **Build** our team using this dependency-aware logic. This provides the "receipt-based gating" Opus wants but with the "adversarial reasoning" that only an agent can provide.

## Final Verdict
**Round 1**: **Build.** The "Assemble/Integrate" approach has already been proven a P1-level failure. We need a custom system that treats the octo ledger as its primary state, not an external API to check.
**Round 2**: **Agent Team.** A command is a 30-second checklist; a workflow transition is a 30-minute reasoning task. We need an Orchestrator and a Gate-Keeper to ensure that "Quality Gate: Pass" actually means the code works, and that "Debate Required" actually triggers a debate.
