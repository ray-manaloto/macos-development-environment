"""Claude Code hook handlers for the mde CLI.

Subcommands:
- verify-task-completion: TaskCompleted gate (exit 2 blocks)
- check-teammate-work: TeammateIdle gate (exit 2 keeps working)
- log-edit-outcome: PostToolUse logger (always exit 0)
- log-agent-event: SubagentStarted/SubagentCompleted logger (always exit 0)
"""

from __future__ import annotations


def dispatch_hooks(action: str) -> int:
    """Dispatch to the appropriate hook handler."""
    if action == "verify-task-completion":
        from mde.hooks.verify_task import verify_task_completion

        return verify_task_completion()
    if action == "check-teammate-work":
        from mde.hooks.check_teammate import check_teammate_work

        return check_teammate_work()
    if action == "log-edit-outcome":
        from mde.hooks.log_outcome import log_edit_outcome

        return log_edit_outcome()
    if action == "log-agent-event":
        from mde.hooks.log_agent_event import log_agent_event

        return log_agent_event()

    import sys

    print(f"Unknown hook action: {action}", file=sys.stderr)
    return 1


__all__ = [
    "dispatch_hooks",
]
