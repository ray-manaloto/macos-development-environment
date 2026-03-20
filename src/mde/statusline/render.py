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

from mde.statusline.models import Model

_MODE_FILE = Path(".artifacts/statusline-mode")
_AGENT_STATE_FILE = Path(".artifacts/agent-state.jsonl")
_EVENT_LOG_FILE = Path(".artifacts/statusline-events.jsonl")

# ANSI color codes
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_ORANGE = "\033[38;5;208m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_CTX_GREEN_MAX_PCT = 50
_CTX_YELLOW_MAX_PCT = 70
_CTX_ORANGE_MAX_PCT = 90
_ID_TRUNC_LEN = 6


def render_statusline() -> int:
    """Main entry point — read stdin JSON, output formatted statusline."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    from mde.statusline.schema import parse_rate_limits, parse_stdin
    from mde.statusline.widget_toggle import read_widget_config
    from mde.statusline.widgets import render_metrics_bar

    parsed = parse_stdin(data)
    agents = _read_agent_state()
    mode = _read_mode()
    widget_config = read_widget_config()
    rate_info = parse_rate_limits(parsed.rate_limits)

    # Build context dict for existing mode renderers (backward compat)
    ctx: dict[str, Any] = {
        "model": (
            parsed.model.display_name
            if isinstance(parsed.model, Model)
            else str(parsed.model or "unknown")
        ),
        "cost_usd": parsed.cost.total_cost_usd if parsed.cost else 0.0,
        "context_pct": parsed.context_window.used_percentage if parsed.context_window else 0,
        "exceeds_200k": parsed.exceeds_200k_tokens,
    }

    if mode == "B":
        mode_output = _render_mode_b(ctx, agents)
    elif mode == "C":
        mode_output = _render_mode_c(ctx, agents)
    else:
        mode_output = _render_mode_a(ctx, agents)

    metrics = render_metrics_bar(parsed, rate_info, widget_config)

    if metrics:
        sep = "\n" if mode == "C" else " | "
        output = mode_output + sep + metrics
    else:
        output = mode_output

    print(output)
    _write_event_log(data, output)
    return 0


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
    """Return ANSI color based on context percentage (4-tier)."""
    if pct >= _CTX_ORANGE_MAX_PCT:
        return _RED
    if pct >= _CTX_YELLOW_MAX_PCT:
        return _ORANGE
    if pct >= _CTX_GREEN_MAX_PCT:
        return _YELLOW
    return _GREEN


def _osc8_link(url: str, text: str) -> str:
    """Create an OSC 8 hyperlink escape sequence."""
    return f"\033]8;;{url}\a{text}\033]8;;\a"


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


def show_last_event() -> int:
    """Print the last captured statusline event (stdin + output)."""
    try:
        lines = _EVENT_LOG_FILE.read_text().strip().split("\n")
        last = json.loads(lines[-1])
        print(json.dumps(last, indent=2))
    except (OSError, json.JSONDecodeError, IndexError):
        print("No events captured yet. Capture is on by default.")
        return 1
    return 0


def _write_event_log(stdin_data: dict[str, Any], rendered_output: str) -> None:
    """Append a statusline event to a rotating JSONL log for validation and fixtures.

    Uses stdlib RotatingFileHandler for automatic rotation (5MB, 3 backups = 20MB max).
    Each line is a complete input/output pair: {"ts": ..., "stdin": {...}, "output": "..."}
    Enabled by default. Set MDE_STATUSLINE_CAPTURE=0 to disable.

    Why stdlib logging instead of structlog/loguru/aiofiles:
    - Zero new dependencies (per library-first policy evaluation)
    - Process is synchronous and short-lived (~300ms), not async
    - One write per invocation — import cost of third-party loggers not amortized
    - RotatingFileHandler provides rotation that raw open("a") lacks
    """
    import logging
    import os
    import time
    from logging.handlers import RotatingFileHandler

    if os.environ.get("MDE_STATUSLINE_CAPTURE", "1") == "0":
        return
    try:
        _EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger("mde.statusline.events")
        if not logger.handlers:
            handler = RotatingFileHandler(
                str(_EVENT_LOG_FILE),
                maxBytes=5_000_000,
                backupCount=3,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        event = json.dumps(
            {
                "ts": int(time.time()),
                "stdin": stdin_data,
                "output": rendered_output,
            },
            separators=(",", ":"),
        )
        logger.info(event)
    except OSError:
        pass
