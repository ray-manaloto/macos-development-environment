"""CLI dispatcher for dream subcommands."""

from __future__ import annotations

import sys


def run_dream(action: str, *, force: bool = False, reject: str | None = None) -> int:
    """Execute a dream pipeline action.

    Args:
        action: One of extract, propose, apply, status.
        force: For apply — skip approval prompts.
        reject: For apply — reject a specific proposal by ID.

    Returns:
        Exit code (0 = success).
    """
    if action == "extract":
        from mde.dream.extract import extract_patterns

        state = extract_patterns()
        print(f"Extracted {len(state.patterns)} patterns ({state.extract_count} runs total)")  # noqa: T201
        return 0

    if action == "propose":
        from mde.dream.propose import generate_proposals

        new = generate_proposals()
        print(f"Generated {len(new)} new proposal(s)")  # noqa: T201
        return 0

    if action == "apply":
        from mde.dream.apply import apply_proposals, reject_proposal

        if reject:
            return 0 if reject_proposal(reject) else 1
        apply_proposals(force=force)
        return 0

    if action == "status":
        from mde.dream.status import show_status

        show_status()
        return 0

    print(f"Unknown dream action: {action}", file=sys.stderr)  # noqa: T201
    return 1
