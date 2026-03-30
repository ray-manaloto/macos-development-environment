# Debate Context — Workflow Toolkit Architecture

## Background
We created a `workflow-toolkit` plugin with a `next-workflow-step` skill for automating
octo:embrace Double Diamond phase transitions. An adversarial review found 6 P1 critical
bugs and 6 P2 issues. Research on 14 categories of community workflows revealed patterns
our skill doesn't implement.

## Key P1 Findings from Review
1. Handoff writes to `remember.md` but that's a one-shot file cleared on SessionStart
2. Phase detection looks for artifacts in the repo, but they live at `~/.claude-octopus/results/`
3. Quality gate is populated from memory, not actually run
4. Debate gate state (config + outcome) is not captured across sessions
5. `bridge_config` task-ledger (warm-start state) is completely ignored
6. No verified write — handoff failure is undetected

## Key Community Patterns Not Implemented
1. Receipt-based gating (machine-readable phase completion artifacts)
2. Ledger-based handoffs (Continuous Claude v3 pattern)
3. Goal-met exit conditions (not fixed iteration counts)
4. MI score tracking for context degradation
5. Iterate-until-approved loops with machine-readable approval signals
6. Branch-per-run experiment tracking

## Current Architecture
- `src/mde/hooks/remember_stop.py` — writes to `now.md` on Stop
- `src/mde/hooks/dream_extract.py` — scans `now.md` for patterns on Stop
- `.generated/remember/` — remember plugin data (now.md, today-*.md, recent.md, archive.md)
- `~/.claude-octopus/` — octo plugin state (results/, bridge/)
- Existing agents: researcher, coder, tester, reviewer, python-coder, security-auditor
- `embrace.yaml` — formal workflow definition with phases, quality gates, autonomy modes

## Debate Questions

### Round 1: Build vs Assemble
Should we build a custom agent team for workflow orchestration, or compose from existing
plugins (agent-teams, octo agents, community workflows)?

### Round 2: Skill vs Agent Team
Is a skill-only approach sufficient for SDLC enforcement, or does it require an agent
team with dedicated roles (orchestrator, gate-keeper, state-manager)?
