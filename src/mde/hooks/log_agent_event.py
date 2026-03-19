"""SubagentStart/SubagentStop hook — logs agent lifecycle events.

Called by Claude Code when subagents start or stop.
Reads JSON from stdin with the actual Claude Code payload:
  - agent_id: unique hex identifier
  - agent_type: e.g. "Explore", "coder", "tester"
  - hook_event_name: "SubagentStart" or "SubagentStop"

Always exits 0 (never blocks).
Appends structured JSONL to .artifacts/agent-state.jsonl.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_AGENT_STATE_FILE = Path(".artifacts/agent-state.jsonl")


def log_agent_event() -> int:
    """Read agent event JSON from stdin, log to JSONL file."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    # Claude Code sends: agent_id, agent_type, hook_event_name
    agent_id = str(data.get("agent_id", "unknown"))
    agent_type = str(data.get("agent_type", "unknown"))
    hook_event = str(data.get("hook_event_name", "unknown"))

    # Derive a readable event name from the hook event
    event = "started" if hook_event == "SubagentStart" else "stopped"

    record = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "agent_name": agent_type,
        "agent_id": agent_id,
        "event": event,
    }

    try:
        _AGENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _AGENT_STATE_FILE.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass

    return 0
