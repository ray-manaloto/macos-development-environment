---
name: transition
description: Execute an octo:embrace phase transition with quality gate verification, receipt-based gating, and structured handoff
argument-hint: "[phase]"
allowed-tools:
  ["Bash", "Read", "Write", "Glob", "Grep"]
---

# Phase Transition

Execute a structured octo:embrace phase transition. This command runs the
quality gate, writes a receipt, checks for staleness, writes a structured
handoff, and summarizes the transition for the user.

## Step 1: Read Phase State

Read `~/.claude-octopus/bridge/task-ledger.json` to determine the current
embrace phase and what was completed.

- If the file exists, extract `currentPhase`, `completedPhase`, and any
  summary fields.
- If the file is missing or the `[phase]` argument was provided, use the
  argument as the completed phase.
- If neither is available, ask the user which phase they are completing
  before proceeding.

Map phases to the embrace cycle:

| Completed | Next     |
|-----------|----------|
| probe     | grasp    |
| grasp     | tangle   |
| tangle    | ink      |
| ink       | probe    |

## Step 2: Run Quality Gate

Run the full quality gate and capture the output:

```bash
uv run mde-py quality
```

Record whether it passed (all 6 checks green), the test count, and any
warnings.

## Step 3: Write Quality Receipt

Get the current short commit hash:

```bash
git rev-parse --short HEAD
```

Write the receipt to `.generated/receipts/quality-<hash>.json`:

```json
{
  "commit": "<full-hash>",
  "timestamp": "<ISO-8601>",
  "passed": true,
  "tests": <count>,
  "warnings": <count>
}
```

Create the `.generated/receipts/` directory if it does not exist.

## Step 4: Check for Staleness

Compare the receipt commit with the current HEAD. If they differ (new commits
were made after the quality gate ran), warn the user and re-run the quality
gate from Step 2.

## Step 5: Write Structured Handoff

Append (do NOT overwrite) to `.generated/remember/now.md` using this format:

```markdown
## Session Handoff — <date> <time>

### Current State
- **Branch**: <branch name from `git branch --show-current`>
- **Quality gate**: <pass/fail, N tests, N warnings>
- **Unpushed commits**: <list from `git log @{u}..HEAD --oneline`, or "none">

### Embrace Phase Transition
- **Completed phase**: <phase>
- **Next phase**: <next phase>
- **Direction**: <advance/repeat/step-back> — <one-line reason>

### Next Session Instructions

Execute `/octo:<next-phase>` with the following context:

<2-4 sentences: what was accomplished, what the next phase should focus on,
any constraints or decisions already made>

<If a debate is warranted for the next phase, add:>
Before proceeding, run `/octo:debate` on:
- <specific decision or question>
- <constraints and context>

### Artifacts
- <key files produced or modified this session>
```

IMPORTANT: Write to `now.md`, NOT `remember.md`. The remember.md file is a
one-shot briefing that gets cleared on session start. The now.md file persists
across sessions as fallback context.

## Step 6: Record Debate Gate (if applicable)

If the transition involves a decision that was debated during this session,
append a note to the handoff indicating the debate outcome and verdict so the
next session does not re-debate a settled question.

## Step 7: Summary

Display to the user:
1. Quality gate result (pass/fail)
2. Receipt file path
3. Phase transition (completed -> next)
4. Key contents of the handoff
5. Suggest `/clear` when ready to start the next session
