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

# AUTO-DISCOVERED: This hook is registered automatically by cli.py via __hook_meta__.
# To add a new hook, create a new module in src/mde/hooks/ with __hook_meta__ — do NOT edit cli.py.
__hook_meta__ = {
    "help": "SubagentStart/SubagentStop logger",
    "entry": "log_agent_event",
}

import json
from datetime import UTC, datetime
from pathlib import Path

from mde.hooks._common import hook_span, parse_hook_stdin
from mde.log import logger

_AGENT_STATE_FILE = Path(".artifacts/agent-state.jsonl")


def log_agent_event() -> int:
    """Read agent event JSON from stdin, log to JSONL file."""
    try:
        data = parse_hook_stdin()
    except (json.JSONDecodeError, ValueError) as exc:
        logger.bind(hook="log_agent_event", error=str(exc)).warning("hook_stdin_parse_failed")
        return 0

    # Claude Code sends: agent_id, agent_type, hook_event_name
    hook_event = str(data.get("hook_event_name", "unknown"))

    with hook_span("log_agent_event", hook_event, data) as span:
        agent_id = str(data.get("agent_id", "unknown"))
        agent_type = str(data.get("agent_type", "unknown"))

        span.set_attribute("hook.agent_id", agent_id)
        span.set_attribute("hook.agent_type", agent_type)

        # Derive a readable event name from the hook event
        event = "started" if hook_event == "SubagentStart" else "stopped"

        session_id = data.get("session_id", "")
        record = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "session_id": session_id,
            "agent_name": agent_type,
            "agent_id": agent_id,
            "event": event,
        }

        try:
            _AGENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _AGENT_STATE_FILE.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            span.record_exception(exc)

        logger.bind(
            hook="log_agent_event",
            agent_type=agent_type,
            agent_event=event,
            session_id=session_id,
        ).info("hook_completed")
        return 0
