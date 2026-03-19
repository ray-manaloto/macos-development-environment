"""Statusline renderer with three display modes for multi-agent awareness.

Mode A (Lightweight): Agent count + aggregate cost + parent context %
Mode B (Per-agent): Each agent's type + state (started/stopped)
Mode C (Dashboard): Multi-line with agent list and states

Reads Claude Code JSON from stdin, agent state from .artifacts/agent-state.jsonl.
Outputs ANSI-colored text to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_MODE_FILE = Path(".artifacts/statusline-mode")
_AGENT_STATE_FILE = Path(".artifacts/agent-state.jsonl")

# ANSI color codes
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_CTX_WARN_PCT = 50
_CTX_CRIT_PCT = 80
_ID_TRUNC_LEN = 6


def render_statusline() -> int:
    """Main entry point — read stdin JSON, output formatted statusline."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    ctx = _extract_context(data)
    agents = _read_agent_state()
    mode = _read_mode()

    if mode == "B":
        output = _render_mode_b(ctx, agents)
    elif mode == "C":
        output = _render_mode_c(ctx, agents)
    else:
        output = _render_mode_a(ctx, agents)

    print(output)
    return 0


def _extract_context(data: dict[str, Any]) -> dict[str, Any]:
    """Extract model, cost, context % from Claude Code JSON."""
    model_info = data.get("model", {})
    if not isinstance(model_info, dict):
        model_info = {}
    cost_info = data.get("cost", {})
    if not isinstance(cost_info, dict):
        cost_info = {}
    ctx_info = data.get("context_window", {})
    if not isinstance(ctx_info, dict):
        ctx_info = {}

    return {
        "model": model_info.get("display_name", "unknown"),
        "cost_usd": cost_info.get("total_cost_usd", 0.0),
        "context_pct": ctx_info.get("used_percentage", 0),
    }


def _read_mode() -> str:
    """Read current display mode from state file, default to 'A'."""
    try:
        return _MODE_FILE.read_text().strip().upper()
    except OSError:
        return "A"


def _read_agent_state() -> list[dict[str, Any]]:
    """Read agent state entries from JSONL, keeping latest per agent_id.

    Only returns agents whose last event was 'started' (i.e., still running).
    Agents that have 'stopped' are filtered out.
    """
    try:
        lines = _AGENT_STATE_FILE.read_text().strip().split("\n")
    except OSError:
        return []

    agents: dict[str, dict[str, Any]] = {}
    for line in lines:
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Use agent_id as unique key (agent_name/type can repeat)
        agent_id = str(entry.get("agent_id", entry.get("agent_name", "unknown")))
        agents[agent_id] = entry

    # Only show agents that are still running
    return [a for a in agents.values() if a.get("event") != "stopped"]


def _to_float(val: object, default: float = 0.0) -> float:
    """Safely convert an arbitrary value to float."""
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _to_int(val: object, default: int = 0) -> int:
    """Safely convert an arbitrary value to int."""
    try:
        return int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _color_for_pct(pct: float) -> str:
    """Return ANSI color based on context percentage thresholds."""
    if pct >= _CTX_CRIT_PCT:
        return _RED
    if pct >= _CTX_WARN_PCT:
        return _YELLOW
    return _GREEN


def _render_mode_a(ctx: dict[str, Any], agents: list[dict[str, Any]]) -> str:
    """Mode A (Lightweight): agent count + aggregate cost + context %."""
    count = len(agents)
    cost = _to_float(ctx.get("cost_usd", 0.0))
    pct = _to_int(ctx.get("context_pct", 0))
    color = _color_for_pct(pct)

    parts = []
    if count > 0:
        parts.append(f"{count} agent{'s' if count != 1 else ''}")
    parts.append(f"${cost:.2f}")
    parts.append(f"{color}{pct}%{_RESET}")

    return " | ".join(parts)


def _render_mode_b(ctx: dict[str, Any], agents: list[dict[str, Any]]) -> str:
    """Mode B (Per-agent): parent context % + each agent's type and state."""
    pct = _to_int(ctx.get("context_pct", 0))
    color = _color_for_pct(pct)
    parts = [f"{color}{pct}%{_RESET}"]

    for agent in agents:
        name = str(agent.get("agent_name", "?"))
        state = str(agent.get("event", "?"))
        state_color = _GREEN if state == "started" else _DIM
        parts.append(f"{name}:{state_color}{state}{_RESET}")

    return " ".join(parts)


def _render_mode_c(ctx: dict[str, Any], agents: list[dict[str, Any]]) -> str:
    """Mode C (Dashboard): multi-line with agent list and states."""
    pct = _to_int(ctx.get("context_pct", 0))
    cost = _to_float(ctx.get("cost_usd", 0.0))
    model = str(ctx.get("model", "unknown"))
    color = _color_for_pct(pct)

    lines = [f"{_BOLD}{model}{_RESET} {color}{pct}%{_RESET} ${cost:.2f}"]

    for agent in agents:
        name = str(agent.get("agent_name", "?"))
        agent_id = str(agent.get("agent_id", "?"))
        state = str(agent.get("event", "?"))
        short_id = agent_id[:_ID_TRUNC_LEN] if len(agent_id) > _ID_TRUNC_LEN else agent_id
        if state == "started":
            state_indicator = f"{_GREEN}running{_RESET}"
        else:
            state_indicator = f"{_DIM}{state}{_RESET}"
        lines.append(f"  {name:<12} {_DIM}{short_id}{_RESET} [{state_indicator}]")

    if not agents:
        lines.append(f"  {_DIM}no agents{_RESET}")

    return "\n".join(lines)
