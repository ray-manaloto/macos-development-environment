"""Claude Code hook handlers for the mde CLI.

Subcommands (dispatched via _HOOKS_DISPATCH in cli.py):
- guard-install: PreToolUse install guard (exit 2 blocks)
- log-edit-outcome: PostToolUse logger (always exit 0)
- log-agent-event: SubagentStart/SubagentStop logger (always exit 0)
- session-start: SessionStart context setup (always exit 0)
- post-compact: PostCompact event logger (always exit 0)
- validate-agents: PostToolUse validator for .claude/agents/ frontmatter (exit 1 blocks)
- team-quality-gate: Per-team quality gate validation (exit 1 on failure)
"""

from __future__ import annotations
