"""Learning system modules."""

from __future__ import annotations


def dispatch_learn(action: str, *, query: str = "") -> int:
    """Dispatch learn subcommand.

    Args:
        action: The learn action to perform.
        query: Search query for the 'search' action.

    Returns:
        Exit code.
    """
    if action == "status":
        from mde.learn.memory import show_status

        return show_status()
    if action == "search":
        from mde.learn.memory import search_memory

        return search_memory(query)
    if action == "verify":
        from mde.learn.verify import verify_learning

        return verify_learning()
    return 1
