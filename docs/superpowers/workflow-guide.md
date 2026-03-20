# Superpowers SDLC Workflow Guide

A practical reference mapping every superpowers plugin skill to a complete software development lifecycle.
Uses the **statusline enhancement project** as an applied example throughout.

> **Superpowers version:** 5.0.5 (14 skills across 5 categories)

---

## 1. Workflow Overview

### SDLC Stage → Skill Mapping

| Stage | Primary Skill | Supporting Skills | Statusline Example |
|-------|--------------|-------------------|-------------------|
| **Discovery** | `/brainstorming` | WebSearch, mcptube | Research terminal UI widget patterns |
| **Planning** | `/writing-plans` | `/brainstorming` output | Plan widget specs, file ownership |
| **Branch Setup** | `/using-git-worktrees` | — | `git worktree add` for isolated feature branch |
| **Implementation** | `/subagent-driven-development` | `/dispatching-parallel-agents` | Build widgets, toggle system, renderer |
| **Testing** | `/test-driven-development` | `/systematic-debugging` | RED-GREEN-REFACTOR per widget |
| **Debugging** | `/systematic-debugging` | `/verification-before-completion` | Null JSON fields, ANSI escapes |
| **Review** | `/requesting-code-review` | `/receiving-code-review` | Spec compliance → code quality |
| **Completion** | `/finishing-a-development-branch` | `/verification-before-completion` | Merge/PR decision |

### Invocation Flow

```
Discovery          Planning          Branch Setup         Implementation         Testing
/brainstorming  →  /writing-plans  →  /using-git-      →  /subagent-driven-  →  /test-driven-
                                       worktrees            development           development
                                       (REQUIRED)                 ↑                    |
                                                      /dispatching-parallel-          |
                                                       agents (independent widgets)   ↓
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
I want to enhance the statusline with new metrics: token speed, burn rate,
block timers, and daily totals. Each metric should be a toggleable widget.
The renderer should migrate from bash to Python.
```

**What the skill does:**
- Explores user intent, requirements, and design constraints
- Surfaces edge cases before implementation begins
- Identifies technical risks (e.g., ANSI rendering differences across terminals)
- Produces a structured requirements summary

**Expected output:**
- Refined requirements document (conversation artifact)
- Design constraints and trade-offs identified
- Open questions surfaced for user decision

**Statusline example:** Discovers that `used_percentage` can be `null` early in a session (already handled by `_to_int` in `src/mde/statusline/render.py:119-123`), identifies that burn rate needs a time window, and surfaces the question of whether daily totals persist across sessions.

---

### Phase 2: Planning — `/writing-plans`

**Trigger prompt:**
```
Write an implementation plan for the statusline enhancement. We need:
- 4 new widgets (token speed, burn rate, block timer, daily totals)
- Per-widget toggle control via the existing toggle system
- mcptube/deep-research integration for widget design inspiration
- Migration from bash to Python renderer (already started in src/mde/statusline/)
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

**Statusline example plan steps:**
1. Define widget protocol in `src/mde/statusline/widgets.py`
2. Implement `token_speed_widget()` — tokens/sec from `current_usage`
3. Implement `burn_rate_widget()` — cost/minute from `total_cost_usd` + `total_duration_ms`
4. Implement `block_timer_widget()` — elapsed time for current operation
5. Implement `daily_totals_widget()` — cumulative cost/tokens, persisted to `.artifacts/`
6. Extend `src/mde/statusline/toggle.py` for per-widget toggles
7. Update `src/mde/statusline/render.py` to compose enabled widgets
8. Write tests at `tests/mde/test_statusline_widgets.py`

---

### Phase 2.5: Branch Setup — `/using-git-worktrees` (REQUIRED)

**Trigger prompt:**
```
/using-git-worktrees
Create a worktree for the statusline enhancement feature.
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
- Feature branch created (e.g., `feat/statusline-metrics-bar`)
- Worktree directory ready for implementation
- `main` branch remains untouched

**Statusline example:** `git worktree add .claude/worktrees/statusline-metrics feat/statusline-metrics-bar`

---

### Phase 3: Implementation — `/subagent-driven-development` or `/executing-plans`

> **Prerequisite:** You MUST be on a feature branch (created by `/using-git-worktrees` above), NOT on `main`.

**Trigger prompt (same session):**
```
Execute the statusline enhancement plan using subagent-driven development.
```

**Trigger prompt (separate session):**
```
Execute the statusline enhancement plan from the previous session.
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

**Statusline example:** Sequential for toggle system refactor (shared state in `_MODE_FILE`), parallel for independent widgets (token speed, burn rate, block timer have no shared state).

---

### Phase 4: Testing — `/test-driven-development`

**Trigger prompt:**
```
Implement the burn rate widget using TDD.
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

**Statusline TDD example — burn rate widget:**

```python
# RED — tests/mde/test_statusline_widgets.py
def test_burn_rate_zero_duration(self) -> None:
    """Burn rate should be $0.00/min when duration is zero."""
    from mde.statusline.widgets import burn_rate_widget

    ctx = {"cost_usd": 1.50, "duration_ms": 0}
    assert burn_rate_widget(ctx) == "$0.00/min"

def test_burn_rate_normal(self) -> None:
    """$1.50 over 60s = $1.50/min."""
    from mde.statusline.widgets import burn_rate_widget

    ctx = {"cost_usd": 1.50, "duration_ms": 60_000}
    assert burn_rate_widget(ctx) == "$1.50/min"
```

```python
# GREEN — src/mde/statusline/widgets.py
def burn_rate_widget(ctx: dict[str, object]) -> str:
    cost = _to_float(ctx.get("cost_usd", 0.0))
    duration_ms = _to_float(ctx.get("duration_ms", 0.0))
    if duration_ms <= 0:
        return "$0.00/min"
    rate_per_min = cost / (duration_ms / 60_000)
    return f"${rate_per_min:.2f}/min"
```

```python
# REFACTOR — extract _to_float from render.py into shared utils
# Both render.py and widgets.py import from the same location
```

**Run tests:**
```
uv run pytest tests/mde/test_statusline_widgets.py -v
```

---

### Phase 5: Debugging — `/systematic-debugging`

**Trigger prompt:**
```
The burn rate widget shows "$inf/min" when duration_ms is missing from stdin JSON.
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

**Statusline example:** The issue is that `duration_ms` defaults to `0.0` via `_to_float`, causing division by zero. The fix is the `if duration_ms <= 0` guard shown in the TDD example above.

---

### Phase 6: Review — `/requesting-code-review` + `/receiving-code-review`

**Trigger prompt (requesting):**
```
Review the statusline widget implementation before merging.
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

**Statusline two-stage review:**

| Stage | Checks |
|-------|--------|
| **Spec compliance** | Does each widget match the plan? Are all 4 widgets implemented? Does toggle system support per-widget control? |
| **Code quality** | Follows `_to_float()` pattern? Uses `_GREEN`/`_YELLOW`/`_RED`/`_RESET` ANSI constants from `render.py`? ruff ALL clean? Type annotations present? |

---

### Phase 7: Completion — `/finishing-a-development-branch`

**Trigger prompt:**
```
The statusline enhancement is complete. All tests pass. How should we integrate?
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

### Applied: Statusline Enhancement

| Component | Strategy | Reason |
|-----------|----------|--------|
| Token speed widget | **Parallel** | Independent function, own test file section |
| Burn rate widget | **Parallel** | Independent function, no shared state |
| Block timer widget | **Parallel** | Independent function, no shared state |
| Daily totals widget | **Parallel** | Independent function (persistence is widget-internal) |
| Toggle system refactor | **Sequential** | Modifies shared `_MODE_FILE` and `_CYCLE` dict |
| Render pipeline update | **Sequential** | Depends on all widgets + toggle system existing |

### Parallel Dispatch Prompt

```
Dispatch 4 parallel agents with these file ownership boundaries:

Agent 1 (token-speed):
- OWNS: src/mde/statusline/widgets/token_speed.py
- OWNS: tests/mde/test_widget_token_speed.py
- READS (no modify): src/mde/statusline/render.py (for _to_float pattern)

Agent 2 (burn-rate):
- OWNS: src/mde/statusline/widgets/burn_rate.py
- OWNS: tests/mde/test_widget_burn_rate.py
- READS (no modify): src/mde/statusline/render.py

Agent 3 (block-timer):
- OWNS: src/mde/statusline/widgets/block_timer.py
- OWNS: tests/mde/test_widget_block_timer.py
- READS (no modify): src/mde/statusline/render.py

Agent 4 (daily-totals):
- OWNS: src/mde/statusline/widgets/daily_totals.py
- OWNS: tests/mde/test_widget_daily_totals.py
- READS (no modify): src/mde/statusline/render.py

Each widget function takes a dict[str, object] context and returns a str.
Use _to_float() for numeric conversion. Include TDD: write test first, then implementation.
```

### Integration Step (After Parallel Agents Return)

After all 4 widget agents complete:
1. Verify no file ownership conflicts: `git diff --name-only`
2. Run all widget tests: `uv run pytest tests/mde/test_widget_*.py -v`
3. Then proceed sequentially: toggle system → render pipeline → integration tests

---

## 4. Testing Strategy

### Three Levels of Testing

| Level | Scope | Files | What to Test |
|-------|-------|-------|-------------|
| **Unit** | Per widget | `tests/mde/test_widget_*.py` | Each widget function in isolation |
| **Integration** | Render pipeline | `tests/mde/test_statusline.py` | Widgets composed into full statusline output |
| **E2E** | CLI entry point | `tests/mde/test_statusline.py` | `render_statusline()` with real stdin JSON |

### RED-GREEN-REFACTOR Example: Token Speed Widget

**RED — Write the failing test first:**

```python
# tests/mde/test_widget_token_speed.py
from __future__ import annotations

import pytest


class TestTokenSpeedWidget:
    """Unit tests for the token speed widget."""

    def test_tokens_per_second_normal(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        ctx = {
            "total_input_tokens": 50_000,
            "total_output_tokens": 10_000,
            "duration_ms": 60_000,
        }
        # 60k tokens in 60s = 1000 tok/s
        assert token_speed_widget(ctx) == "1000 tok/s"

    def test_zero_duration_returns_dash(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        ctx = {"total_input_tokens": 100, "total_output_tokens": 0, "duration_ms": 0}
        assert token_speed_widget(ctx) == "— tok/s"

    def test_missing_fields_default_to_zero(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        assert token_speed_widget({}) == "— tok/s"
```

**GREEN — Minimal implementation:**

```python
# src/mde/statusline/widgets.py
from __future__ import annotations

from mde.statusline.render import _to_float


def token_speed_widget(ctx: dict[str, object]) -> str:
    """Tokens per second from total tokens and duration."""
    input_tok = _to_float(ctx.get("total_input_tokens", 0))
    output_tok = _to_float(ctx.get("total_output_tokens", 0))
    duration_ms = _to_float(ctx.get("duration_ms", 0))
    if duration_ms <= 0:
        return "— tok/s"
    total = input_tok + output_tok
    tok_per_sec = total / (duration_ms / 1000)
    return f"{int(tok_per_sec)} tok/s"
```

**REFACTOR — only after green:**
- Extract `_to_float` into a shared module if not already shared
- Consider whether `int()` truncation or `round()` is more appropriate

### Test Fixtures Pattern

Reuse the established `_sample_statusline_stdin()` pattern from `tests/mde/test_statusline.py:21-27`:

```python
def _sample_statusline_stdin() -> dict[str, object]:
    """Real Claude Code statusline JSON shape."""
    return {
        "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
        "cost": {"total_cost_usd": 1.23, "total_duration_ms": 45000},
        "context_window": {"used_percentage": 42, "context_window_size": 200000},
    }
```

### Anti-Patterns to Avoid

Refer to the superpowers `testing-anti-patterns` skill for the full list. Key ones for statusline:

- **Don't mock `_to_float`** — it's a pure function, test it through the widget
- **Don't test ANSI codes literally** — test semantic content, strip ANSI for assertions
- **Don't skip null-field tests** — Claude Code sends `null` for `used_percentage` early in sessions
- **Don't use `capsys` without `readouterr()`** — always capture before asserting

### Running Tests

```
uv run pytest tests/mde/test_statusline.py -v
uv run pytest tests/mde/test_widget_*.py -v
uv run pytest tests/mde/ -k statusline -v    # all statusline-related tests
```

---

## 5. Debugging Playbook

### Common Failure Modes → `/systematic-debugging` Phases

| Symptom | Likely Root Cause | Source File | Debug Phase |
|---------|-------------------|-------------|-------------|
| `"$inf/min"` in output | Division by zero — `duration_ms` is 0 or missing | `src/mde/statusline/render.py` | Hypothesis: missing guard on `_to_float` return |
| `"0%"` when context is clearly used | `used_percentage` is `null` in JSON | `src/mde/statusline/render.py:71` | Hypothesis: `_to_int(None)` returns 0 — correct behavior, but verify upstream sends non-null |
| ANSI codes visible as literal text | Terminal doesn't support ANSI or output is piped | `src/mde/statusline/render.py:22-27` | Hypothesis: add `isatty()` check before coloring |
| Stale agent count (shows agents that stopped) | JSONL dedup logic not seeing latest `stopped` event | `src/mde/statusline/render.py:83-107` | Hypothesis: check JSONL append order, verify `_read_agent_state()` keeps latest per ID |
| Toggle doesn't cycle | `_MODE_FILE` not writable or directory missing | `src/mde/statusline/toggle.py:23` | Hypothesis: `.artifacts/` directory doesn't exist — check `mkdir(parents=True)` |
| Widget shows in wrong mode | Render function dispatches on mode but new widget not gated | `src/mde/statusline/render.py:45-51` | Hypothesis: new widget added to `_render_mode_a` but not gated by toggle |

### Debugging Workflow

For each symptom:

1. **Reproduce** — Construct minimal stdin JSON that triggers the issue
2. **Hypothesize** — Form a specific, testable hypothesis (see table above)
3. **Gather evidence** — Read the source file at the suspected line
4. **Test** — Write a failing test that reproduces the bug
5. **Fix** — Make the minimal change to pass the test
6. **Verify** — Run full test suite: `uv run pytest tests/mde/ -k statusline -v`

### Example: Debugging Null `used_percentage`

```python
# 1. Reproduce — construct minimal input
data: dict[str, object] = {
    "context_window": {"used_percentage": None},
}

# 2. Hypothesis: _to_int(None) should return 0
# 3. Evidence: render.py line 119-123 shows _to_int handles TypeError
# 4. Test already exists: test_handles_null_used_percentage (line 154)
# 5. Fix: already handled by _to_int fallback
# 6. Verify:
# uv run pytest tests/mde/test_statusline.py::TestStatuslineRender::test_handles_null_used_percentage -v
```

---

## 6. Code Review Protocol

### Two-Stage Review (from `/subagent-driven-development`)

#### Stage 1: Spec Compliance

| Check | Question | Evidence |
|-------|----------|----------|
| Widget count | Are all 4 widgets implemented? | `grep -r "def.*_widget" src/mde/statusline/` |
| Widget signatures | Does each take `dict[str, object]` and return `str`? | Read each widget function |
| Toggle support | Can each widget be individually toggled? | Check `toggle.py` for per-widget keys |
| Mode integration | Do all 3 modes (A/B/C) render the new widgets? | Check `_render_mode_a/b/c` in `render.py` |
| JSON schema | Do widgets use fields from the official Claude Code stdin schema? | Compare against `_sample_statusline_stdin()` |

#### Stage 2: Code Quality

| Check | Question | Command |
|-------|----------|---------|
| `_to_float` pattern | Do all numeric conversions use `_to_float`/`_to_int`? | `uv run ruff check src/mde/statusline/` |
| ANSI constants | Are colors from `_GREEN`/`_YELLOW`/`_RED`/`_RESET`? | Grep for hardcoded escape codes |
| ruff ALL clean | No lint violations? | `uv run ruff check src/mde/statusline/ --select ALL` |
| Type annotations | All functions annotated? | `uv run ty check src/mde/statusline/` |
| Test coverage | Every widget has unit tests? | `uv run pytest tests/mde/ -k statusline --tb=short` |

### `/verification-before-completion` Gate

**After both review stages pass:**

```
uv run pytest tests/mde/ -k statusline -v
uv run ruff check src/mde/statusline/ --select ALL
uv run ty check src/mde/statusline/
```

All three must pass with zero errors/warnings before claiming review is complete.

---

## 7. Self-Improving Skills

### Creating Project-Specific Skills with `/writing-skills`

The `/writing-skills` skill guides creation of new skills with proper frontmatter, trigger descriptions, and content structure.

### Skill 1: `statusline-widget-testing`

**When to create:** After implementing the first widget, to codify the testing pattern.

**Creation prompt:**
```
/writing-skills

Create a skill called "statusline-widget-testing" that triggers when
implementing or testing new statusline widgets.

It should enforce:
- TDD cycle (RED test first, GREEN minimal impl, REFACTOR)
- Use _sample_statusline_stdin() as the base fixture
- Test null/missing fields using _to_float/_to_int patterns
- Test ANSI output semantically (strip codes, check content)
- Run: uv run pytest tests/mde/test_statusline*.py -v
```

**Expected trigger description:**
```
Use when implementing or testing statusline widgets. Enforces TDD with
_sample_statusline_stdin() fixtures and _to_float/_to_int null-safety patterns.
```

### Skill 2: `video-analysis-integration`

**When to create:** When integrating mcptube or deep-research output into the design process.

**Creation prompt:**
```
/writing-skills

Create a skill called "video-analysis-integration" that triggers when
integrating mcptube or deep-research output into feature design.

It should enforce:
- Extract actionable design patterns from video analysis
- Map patterns to specific implementation tasks
- Feed findings into /writing-plans as constraints
- Verify patterns against existing codebase conventions
```

### Improvement Cycle

```
Use skill → Find failure mode → /writing-skills to update → Use again
     ↑                                                          |
     └──────────────────────────────────────────────────────────┘
```

Example: After using `statusline-widget-testing`, you discover that widgets rendering multi-line output break Mode A (single-line). Update the skill to add a constraint: "Mode A widgets must return single-line strings."

---

## 8. Deep Research Integration

### Pattern: Research Before Planning

```
/brainstorming
  ↓ (surfaces research questions)
External research (WebSearch, mcptube, deep-research)
  ↓ (findings fed back)
/brainstorming (refined with research)
  ↓
/writing-plans (constraints from research baked in)
```

### Applied: Statusline Enhancement Research

**Step 1 — `/brainstorming` surfaces questions:**
- What widget patterns do starship/powerline/oh-my-posh use?
- How do terminal UIs handle variable-width widget composition?
- What are best practices for real-time metrics in terminal statuslines?

**Step 2 — External research:**
```
# WebSearch for widget patterns
"starship prompt module system architecture"
"powerline segment rendering pipeline"

# mcptube for terminal UI videos
# Analyze YouTube videos about terminal customization, prompt engineering
```

**Step 3 — Findings fed into planning:**
- Starship uses TOML-configurable modules with `format` strings → adopt per-widget format config
- Powerline uses a segment pipeline with separators → consider separator chars between widgets
- Real-time metrics need debouncing to avoid flicker → add minimum update interval

**Step 4 — `/writing-plans` with research constraints:**
```
Write an implementation plan for statusline widgets with these constraints
from research:
- Each widget is independently configurable (starship pattern)
- Widgets compose left-to-right with " | " separators (existing pattern in render.py:148)
- Minimum 100ms between re-renders to prevent flicker
```

---

## 9. Verification Gates

### Every Gate Where `/verification-before-completion` Is Mandatory

| Gate | When | Required Commands | Pass Criteria |
|------|------|------------------|---------------|
| **Post-TDD cycle** | After each RED-GREEN-REFACTOR | `uv run pytest tests/mde/test_statusline*.py -v` | All tests pass, new test included |
| **Post-widget implementation** | After each widget is complete | `uv run ruff check src/mde/statusline/ --select ALL` | Zero violations |
| **Post-integration** | After render pipeline updated | `uv run pytest tests/mde/ -k statusline -v` | All tests pass including integration |
| **Pre-review** | Before requesting code review | `uv run ty check src/mde/statusline/` | Zero type errors |
| **Post-review** | After review changes applied | All three commands below | All pass |
| **Pre-merge** | Before finishing development branch | All three commands below | All pass |

### The Three Verification Commands

```
# 1. Tests
uv run pytest tests/mde/ -k statusline -v

# 2. Lint
uv run ruff check src/mde/statusline/ --select ALL

# 3. Types
uv run ty check src/mde/statusline/
```

### Iron Rule

> **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**
>
> Every `/verification-before-completion` invocation must include the actual output
> of the verification commands, not assertions that they passed. Copy-paste the
> terminal output. If a command fails, fix it and re-run before claiming completion.

### Verification Prompt Template

```
/verification-before-completion

Run these verification commands and show me the output:
1. uv run pytest tests/mde/ -k statusline -v
2. uv run ruff check src/mde/statusline/ --select ALL
3. uv run ty check src/mde/statusline/

Do not claim completion until all three pass with zero errors.
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
