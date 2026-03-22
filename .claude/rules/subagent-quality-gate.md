# Subagent Quality Gate Enforcement

Every subagent that modifies code MUST run `uv run mde-py quality` before committing.
The pre-commit hook in hk.pkl is a SAFETY NET, not the primary check.

See [Workflow Guide](../../docs/superpowers/workflow-guide.md) for the full process:
- §10: Resuming existing work
- §11: Sequential PR workflow
- §12: Step announcements (announce next step after completing work)
- §13: Skill-driven tool usage (invoke /ruff, /ty, /uv skills before running tools)
- §14: Zero tolerance for warnings

## Rules
- Quality gate output (6/6 passed) MUST be in the subagent's report
- Controllers MUST NOT dispatch a reviewer until quality gate passes
- After reviewer findings are fixed, run quality gate again before re-review
- Read ALL output — warnings and deprecation notices must be addressed, not just exit codes
- Only documented exception: VIRTUAL_ENV worktree warning (see worktree-pr-workflow.md)
