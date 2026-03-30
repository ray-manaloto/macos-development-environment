---
name: next-workflow-step
description: >
  Use this skill when the user wants to transition to the next workflow step,
  wrap up a session cleanly, prepare a handoff, or says things like "next step",
  "continue the workflow", "wrap up", "hand off", "move to the next phase",
  "what's next in embrace", or "prepare for /clear". Also triggers when the
  current octo:embrace phase appears complete and no explicit next action is set.
---

# Next Workflow Step

Detects when a session transition is needed and suggests the structured
transition command.

## Detection

1. Read `~/.claude-octopus/bridge/task-ledger.json` if it exists to determine
   the current octo:embrace phase and progress summary.
2. If the file is missing or unreadable, note that phase state is unknown.

## Action

Suggest the user invoke `/workflow-toolkit:transition` to execute the full
phase transition with quality gate verification, receipt-based gating, and
structured handoff.

Example response:

> It looks like you are ready to transition. Run `/workflow-toolkit:transition`
> to execute the quality gate, write a structured handoff, and prepare for the
> next embrace phase.

Do NOT execute the transition logic yourself — delegate to the command.
