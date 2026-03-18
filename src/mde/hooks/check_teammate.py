"""TeammateIdle hook — keeps teammate working if deliverables incomplete.

Called by Claude Code when a teammate goes idle.
Reads JSON from stdin with: teammate_name, team_name.

Exit 2 = keep working (send feedback message).
Exit 0 = allow idle.
"""

from __future__ import annotations

import json
import sys


def check_teammate_work() -> int:
    """Read teammate JSON from stdin, check if work is complete."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    teammate_name = data.get("teammate_name", "unknown")
    team_name = data.get("team_name", "unknown")

    # Log the idle event for analysis
    print(
        f"Teammate '{teammate_name}' in team '{team_name}' went idle. "
        "Checking if deliverables are complete.",
        file=sys.stderr,
    )

    # Default: allow idle. Teams should override with specific checks.
    return 0
