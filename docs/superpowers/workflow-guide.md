# Superpowers SDLC Workflow Guide

A practical reference mapping every superpowers plugin skill to a complete software development lifecycle.

> **Superpowers version:** 5.0.5 (14 skills across 5 categories)

---

## 1. Workflow Overview

### SDLC Stage → Skill Mapping

| Stage | Primary Skill | Supporting Skills |
|-------|--------------|-------------------|
| **Discovery** | `/brainstorming` | agent-fetch, research skills |
| **Planning** | `/writing-plans` | `/brainstorming` output |
| **Branch Setup** | `/using-git-worktrees` | — |
| **Implementation** | `/subagent-driven-development` | `/dispatching-parallel-agents` |
| **Testing** | `/test-driven-development` | `/systematic-debugging` |
| **Debugging** | `/systematic-debugging` | `/verification-before-completion` |
| **Review** | `/requesting-code-review` | `/receiving-code-review` |
| **Completion** | `/finishing-a-development-branch` | `/verification-before-completion` |

### Invocation Flow

```
Discovery          Planning          Branch Setup         Implementation         Testing
/brainstorming  →  /writing-plans  →  /using-git-      →  /subagent-driven-  →  /test-driven-
                                       worktrees            development           development
                                       (REQUIRED)                 ↑                    |
                                                      /dispatching-parallel-          |
                                                       agents (independent tasks)     ↓
                                                                               Debugging
                                                                            /systematic-debugging
                                                                                  |
                                                                                  ↓
                                             Review                     Completion
                                      /requesting-code-review  →  /finishing-a-
                                      /receiving-code-review       development-branch
                                                 ↑                       ↑
                                      /verification-before-    /verification-before-
                                       completion               completion
```

> **CRITICAL: `/using-git-worktrees` is REQUIRED before implementation.** The `/subagent-driven-development` skill explicitly states: "Never start implementation on main/master branch without explicit user consent." The `/writing-plans` skill states: "This should be run in a dedicated worktree." Skipping this step means all commits go to `main`, requiring manual branch surgery at PR time.

### All 14 Superpowers Skills

| # | Skill | Category | When to Use |
|---|-------|----------|-------------|
| 1 | `/brainstorming` | Discovery | Before any creative work — features, components, modifications |
| 2 | `/writing-plans` | Planning | When you have specs for a multi-step task, before code |
| 3 | `/executing-plans` | Execution | Execute a plan in a separate session with review checkpoints |
| 4 | `/subagent-driven-development` | Execution | Execute plans with independent tasks in current session |
| 5 | `/dispatching-parallel-agents` | Execution | 2+ independent tasks with no shared state |
| 6 | `/test-driven-development` | Testing | Before writing implementation code |
| 7 | `/systematic-debugging` | Debugging | Any bug, test failure, or unexpected behavior |
| 8 | `/requesting-code-review` | Review | After completing tasks, before merging |
| 9 | `/receiving-code-review` | Review | When receiving feedback, before implementing suggestions |
| 10 | `/finishing-a-development-branch` | Completion | Implementation complete, all tests pass, ready to integrate |
| 11 | `/verification-before-completion` | Gates | Before claiming work is done — evidence before assertions |
| 12 | `/writing-skills` | Meta | Creating/editing project-specific skills |
| 13 | `/using-superpowers` | Meta | Conversation start — how to find and use skills |
| 14 | `/using-git-worktrees` | Isolation | Feature work needing isolation from current workspace |

---

## 2. Phase-by-Phase Prompts

### Phase 1: Discovery — `/brainstorming`

**Trigger prompt:**
```
I want to add [feature] to [system]. It should support [capability A],
[capability B], and [capability C].
```

**What the skill does:**
- Explores user intent, requirements, and design constraints
- Surfaces edge cases before implementation begins
- Identifies technical risks (e.g., edge cases, compatibility issues)
- Produces a structured requirements summary

**Expected output:**
- Refined requirements document (conversation artifact)
- Design constraints and trade-offs identified
- Open questions surfaced for user decision

---

### Phase 2: Planning — `/writing-plans`

**Trigger prompt:**
```
Write an implementation plan for [feature]. We need:
- [Component A]
- [Component B]
- [Integration with existing system X]
```

**What the skill does:**
- Creates a structured plan with numbered steps
- Identifies file paths, dependencies, and ordering
- Assigns clear success criteria per step
- Flags parallel-safe vs sequential tasks

**Expected output:**
- Plan document with ordered steps
- File manifest (create/modify)
- Dependency graph between steps

---

### Phase 2.5: Branch Setup — `/using-git-worktrees` (REQUIRED)

**Trigger prompt:**
```
/using-git-worktrees
Create a worktree for the [feature] branch.
```

**What the skill does:**
- Creates an isolated git worktree with a feature branch
- Verifies the branch doesn't already exist
- Switches to the worktree directory
- Ensures `main` stays clean — all implementation commits go to the feature branch

**Why this is required:**
- `/subagent-driven-development` says: "Never start implementation on main/master branch without explicit user consent"
- `/writing-plans` says: "This should be run in a dedicated worktree"
- Without this step, all commits go to `main`, requiring manual `git branch` / `git reset` surgery to create a PR later

**Expected output:**
- Feature branch created (e.g., `feat/my-feature`)
- Worktree directory ready for implementation
- `main` branch remains untouched

---

### Phase 3: Implementation — `/subagent-driven-development` or `/executing-plans`

> **Prerequisite:** You MUST be on a feature branch (created by `/using-git-worktrees` above), NOT on `main`.

**Trigger prompt (same session):**
```
Execute the [feature] plan using subagent-driven development.
```

**Trigger prompt (separate session):**
```
Execute the [feature] plan from the previous session.
```

**What `/subagent-driven-development` does:**
- Spawns subagents for independent tasks in current session
- Manages file ownership boundaries between agents
- Coordinates integration after parallel work completes
- Includes two-stage review: spec compliance → code quality

**What `/executing-plans` does:**
- Executes a written plan in a new session
- Adds review checkpoints between steps
- Ensures plan fidelity across session boundaries

**Expected output:**
- Implemented source files
- Tests written alongside implementation
- Integration verified

---

### Phase 4: Testing — `/test-driven-development`

**Trigger prompt:**
```
Implement [component] using TDD.
```

**What the skill does:**
- Enforces RED → GREEN → REFACTOR cycle
- Writes failing test first, then minimal implementation
- Refactors only after green
- Prevents premature abstraction

**Expected output:**
- Test file with failing test (RED)
- Minimal implementation to pass (GREEN)
- Cleaned-up code (REFACTOR)

**Run tests:**
```
uv run pytest tests/ -v
```

---

### Phase 5: Debugging — `/systematic-debugging`

**Trigger prompt:**
```
[Component] shows [unexpected behavior] when [condition].
```

**What the skill does:**
- Formulates hypotheses before touching code
- Gathers evidence systematically (logs, traces, reproduction)
- Tests one hypothesis at a time
- Documents root cause and fix

**Expected output:**
- Root cause identification with evidence
- Targeted fix (not shotgun debugging)
- Regression test added

---

### Phase 6: Review — `/requesting-code-review` + `/receiving-code-review`

**Trigger prompt (requesting):**
```
Review the [feature] implementation before merging.
```

**What `/requesting-code-review` does:**
- Prepares a review request with context
- Highlights areas of concern
- Lists verification evidence (test results, lint output)

**What `/receiving-code-review` does:**
- Requires technical rigor — no performative agreement
- Verifies suggestions before implementing blindly
- Pushes back on technically questionable feedback

**Expected output:**
- Review findings with severity levels
- Actionable items or justified dismissals

**Two-stage review:**

| Stage | Checks |
|-------|--------|
| **Spec compliance** | Does the implementation match the plan? Are all required components present? Does it integrate with existing systems correctly? |
| **Code quality** | Follows project patterns? Uses existing utilities? Lint-clean? Type annotations present? Tests passing? |

---

### Phase 7: Completion — `/finishing-a-development-branch`

**Trigger prompt:**
```
The [feature] is complete. All tests pass. How should we integrate?
```

**What the skill does:**
- Presents structured options: merge, PR, or cleanup
- Guides the completion decision based on branch state
- Ensures all gates have been passed

**Expected output:**
- Decision on integration method
- Final verification evidence
- Clean branch state

---

## 3. Multi-Agent Orchestration

### Decision Tree: Parallel vs Sequential

```
Is the task decomposable into 2+ independent subtasks?
├── YES → Do subtasks share mutable state or files?
│   ├── NO  → /dispatching-parallel-agents
│   └── YES → /subagent-driven-development (sequential)
└── NO  → Single agent, no orchestration needed
```

### Parallel Dispatch Pattern

```
Dispatch N parallel agents with these file ownership boundaries:

Agent 1 ([component-a]):
- OWNS: src/myproject/component_a.py
- OWNS: tests/test_component_a.py
- READS (no modify): src/myproject/shared_utils.py

Agent 2 ([component-b]):
- OWNS: src/myproject/component_b.py
- OWNS: tests/test_component_b.py
- READS (no modify): src/myproject/shared_utils.py

Each component takes [input type] and returns [output type].
Use existing patterns from shared_utils.py. Include TDD: write test first.
```

### Integration Step (After Parallel Agents Return)

After all parallel agents complete:
1. Verify no file ownership conflicts: `git diff --name-only`
2. Run all component tests: `uv run pytest tests/ -v`
3. Then proceed sequentially: integration layer → end-to-end tests

---

## 4. Testing Strategy

### Three Levels of Testing

| Level | Scope | What to Test |
|-------|-------|-------------|
| **Unit** | Per component | Each function/class in isolation |
| **Integration** | Composed pipeline | Components working together |
| **E2E** | CLI entry point | Full system with real inputs |

### RED-GREEN-REFACTOR Pattern

**RED — Write the failing test first:**

```python
# tests/test_my_component.py
import pytest


class TestMyComponent:
    def test_normal_case(self) -> None:
        from myproject.component import my_function

        result = my_function({"input": "value"})
        assert result == "expected"

    def test_missing_fields_default_gracefully(self) -> None:
        from myproject.component import my_function

        assert my_function({}) == "default"
```

**GREEN — Minimal implementation:**

```python
# src/myproject/component.py
def my_function(ctx: dict[str, object]) -> str:
    value = ctx.get("input", "default")
    return str(value)
```

**REFACTOR — only after green:**
- Extract shared utilities if multiple components repeat the same pattern
- Improve naming for clarity

### Anti-Patterns to Avoid

Refer to the superpowers `testing-anti-patterns` skill for the full list. Key ones:

- **Don't mock pure functions** — test them through the component
- **Don't skip null/missing field tests** — real systems send incomplete data
- **Don't use `capsys` without `readouterr()`** — always capture before asserting

---

## 5. Debugging Playbook

### Debugging Workflow (from `/systematic-debugging`)

For each unexpected behavior:

1. **Reproduce** — Construct minimal input that triggers the issue
2. **Hypothesize** — Form a specific, testable hypothesis
3. **Gather evidence** — Read the source file at the suspected location
4. **Test** — Write a failing test that reproduces the bug
5. **Fix** — Make the minimal change to pass the test
6. **Verify** — Run full test suite: `uv run mde-py quality`

### Debugging Prompt Template

```
/systematic-debugging

[Component] shows [symptom] when [condition].

Hypothesis: [specific guess about root cause].
Evidence needed: [what to read/check to confirm].
```

---

## 6. Code Review Protocol

### Two-Stage Review (from `/subagent-driven-development`)

#### Stage 1: Spec Compliance

| Check | Question |
|-------|----------|
| Component count | Are all required components implemented? |
| Signatures | Do interfaces match the plan? |
| Integration | Does the feature connect to existing systems as designed? |
| Test coverage | Does every component have tests? |

#### Stage 2: Code Quality

| Check | Command |
|-------|---------|
| Lint | `uv run ruff check src/` |
| Types | `uv run ty check src/` |
| Tests | `uv run pytest tests/ -v` |
| Full quality gate | `uv run mde-py quality` |

### `/verification-before-completion` Gate

**After both review stages pass:**

```
uv run mde-py quality
```

Must pass with zero errors/warnings before claiming review is complete.

---

## 7. Self-Improving Skills

### Creating Project-Specific Skills with `/writing-skills`

The `/writing-skills` skill guides creation of new skills with proper frontmatter, trigger descriptions, and content structure.

**Creation prompt template:**
```
/writing-skills

Create a skill called "[skill-name]" that triggers when
[use case description].

It should enforce:
- [Constraint 1]
- [Constraint 2]
- Run: uv run mde-py quality
```

### Improvement Cycle

```
Use skill → Find failure mode → /writing-skills to update → Use again
     ↑                                                          |
     └──────────────────────────────────────────────────────────┘
```

---

## 8. Deep Research Integration

### Pattern: Research Before Planning

```
/brainstorming
  ↓ (surfaces research questions)
External research (agent-fetch, mcptube, deep-research)
  ↓ (findings fed back)
/brainstorming (refined with research)
  ↓
/writing-plans (constraints from research baked in)
```

### Research Workflow

**Step 1 — `/brainstorming` surfaces questions:**
- What patterns do existing tools in this domain use?
- What are best practices for [problem type]?
- What trade-offs exist between approaches?

**Step 2 — External research:**
```bash
npx agent-fetch "https://example.com/docs/relevant-topic" --json
```

**Step 3 — Findings fed into planning:**
- Document design decisions and their rationale
- Map findings to specific implementation constraints

**Step 4 — `/writing-plans` with research constraints:**
```
Write an implementation plan for [feature] with these constraints
from research:
- [Constraint from finding 1]
- [Constraint from finding 2]
```

---

## 9. Verification Gates

### Every Gate Where `/verification-before-completion` Is Mandatory

| Gate | When | Required Command | Pass Criteria |
|------|------|-----------------|---------------|
| **Post-TDD cycle** | After each RED-GREEN-REFACTOR | `uv run pytest tests/ -v` | All tests pass, new test included |
| **Post-implementation** | After each component is complete | `uv run ruff check src/` | Zero violations |
| **Post-integration** | After integration layer updated | `uv run pytest tests/ -v` | All tests pass including integration |
| **Pre-review** | Before requesting code review | `uv run ty check src/` | Zero type errors |
| **Post-review** | After review changes applied | `uv run mde-py quality` | All pass |
| **Pre-merge** | Before finishing development branch | `uv run mde-py quality` | All pass |

### The Quality Gate Command

```
uv run mde-py quality
```

This runs lint, type check, and tests in one step. Use it at every gate.

### Iron Rule

> **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**
>
> Every `/verification-before-completion` invocation must include the actual output
> of the verification commands, not assertions that they passed. Copy-paste the
> terminal output. If a command fails, fix it and re-run before claiming completion.

### Verification Prompt Template

```
/verification-before-completion

Run the quality gate and show me the output:
  uv run mde-py quality

Do not claim completion until it passes with zero errors.
```

---

## 10. Resuming Existing Work

When a PR already has commits, the subagent-driven-development sequence still applies in full.

### Audit First

Before touching any code:

```bash
git log --oneline main..HEAD     # What commits exist?
git diff --stat main..HEAD       # What files changed?
uv run mde-py quality            # Does it currently pass?
```

If `uv run mde-py quality` fails: **fix first, then review.** Do not add new code on top of failing quality gates.

### Review Sequence Still Applies

Existing work does NOT skip review stages:

1. **Spec review** — Does the existing code match the plan?
2. **Fix loop** — Address spec gaps
3. **Quality review** — `uv run mde-py quality`
4. **Fix loop** — Address quality findings
5. **Completion** — `/finishing-a-development-branch`

### Key Principle

"There are already commits" is not a reason to skip any SDLC stage. Partial work needs the same rigor as new work.

---

## 11. Sequential PR Workflow

### One PR at a Time

**Never work on multiple PRs in parallel.**

```
implement → review → fix → verify → merge → pull → next PR
```

### After Merge

```bash
git pull origin main --ff-only
```

Fast-forward only. If it fails, investigate why — do not force.

### If Multiple PRs Exist

Merge simplest first:
1. Data-only changes (no logic) before code changes
2. Foundational changes before dependent changes
3. Independent changes before interdependent changes

### Why Sequential

Parallel PRs create merge conflicts, require rebases, and make it hard to verify each change in isolation. One at a time is faster overall.

---

## 12. Step Announcements

### Rule: Always Announce the Next Step

After completing each workflow step, Claude MUST announce the next superpowers workflow step AND the specific skill to invoke.

### Format

```
✓ [completed step]. Next workflow step: [SDLC stage from §1] → `/skill-name` — [what it does].
```

### Examples

```
✓ Plan written and approved. Next workflow step: Branch Setup → `/using-git-worktrees` — creates an isolated feature branch so commits don't land on main.
```

```
✓ Feature branch created at .worktrees/my-feature. Next workflow step: Implementation → `/subagent-driven-development` — executes the plan with subagents managing file ownership.
```

```
✓ All components implemented and tests pass. Next workflow step: Review → `/requesting-code-review` — prepares spec compliance and code quality review.
```

### Never Wait

Claude must not wait for the user to ask "what's next?" — announce the next step proactively after every completed stage. Reference the §1 SDLC stage mapping when in doubt.

---

## 13. Skill-Driven Tool Usage

### Rule: Invoke the Skill Before Running the Tool

Before running `ruff`, `ty`, `uv`, or `pyright` for Python work, invoke the corresponding skill to load current best practices.

| Tool | Skill to invoke | Why |
|------|----------------|-----|
| `ruff` | `/ruff` | Up-to-date rule configuration, correct invocation patterns |
| `ty` | `/ty` | Current type checking best practices, common pitfalls |
| `uv` | `/uv` | Correct package management patterns, avoid deprecated commands |

### When This Applies

Agents with `skills: [ruff, ty, uv]` in frontmatter MUST invoke these skills when their work touches Python code.

### What Skills Provide

- Current configuration guidance (pyproject.toml options, flags)
- Common pitfalls and how to avoid them
- Correct invocation patterns (e.g., `uv run ruff check` not `ruff check`)
- Migration guidance from older tools

### Example

```
# Before running ruff:
/ruff

# Now run ruff with confidence:
uv run ruff check src/ --fix
```

---

## 14. Zero Tolerance for Warnings

### Rule: Read ALL Output, Not Just Exit Codes

A command that exits 0 but prints warnings is NOT clean. Warnings must be addressed.

### What to Look For

- Deprecation notices
- Non-zero counts in summary lines ("3 warnings", "1 note")
- Lines beginning with `WARNING:`, `WARN:`, or `warning:`
- Skipped tests or excluded files

### Required Actions

| Output type | Action |
|-------------|--------|
| Warning with clear fix | Fix it immediately |
| Warning with unclear cause | Investigate, then fix or create GitHub Issue |
| Deprecation notice | Update to the recommended alternative |
| Non-zero warning count in passing run | Treat as a failure — investigate each |

### The Only Documented Exception

The `VIRTUAL_ENV` warning in git worktrees is benign — uv uses the correct project venv regardless. All other warnings require action. See `worktree-pr-workflow.md` for details.

### Subagent Report Requirements

Subagent reports MUST include the full output summary, not just "all passed." Example:

```
# Required format:
uv run mde-py quality output:
  ruff: 0 errors, 0 warnings
  ty: 0 errors, 0 warnings
  pytest: 42 passed, 0 failed, 0 warnings

# Not acceptable:
"All quality checks passed."
```

---

## Quick Reference Card

| I want to... | Use this skill |
|--------------|---------------|
| Explore requirements before coding | `/brainstorming` |
| Create a multi-step implementation plan | `/writing-plans` |
| **Set up a feature branch before coding** | **`/using-git-worktrees` (REQUIRED before implementation)** |
| Execute a plan in a new session | `/executing-plans` |
| Execute a plan with subagents now | `/subagent-driven-development` |
| Run independent tasks in parallel | `/dispatching-parallel-agents` |
| Write code test-first | `/test-driven-development` |
| Fix a bug systematically | `/systematic-debugging` |
| Request a code review | `/requesting-code-review` |
| Handle review feedback properly | `/receiving-code-review` |
| Finish and integrate a branch | `/finishing-a-development-branch` |
| Prove work is actually done | `/verification-before-completion` |
| Create a reusable skill | `/writing-skills` |
| Start a conversation right | `/using-superpowers` |
