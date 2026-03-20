"""Statusline widget functions.

Each widget receives a validated StatuslineInput and returns a string.
Empty string means the widget is suppressed from the metrics bar.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from claude_agent_sdk.types import RateLimitInfo

    from mde.statusline.models import StatuslineInput

_SECONDS_PER_HOUR = 3600
_DAILY_TOTALS_FILE = Path(".artifacts/daily-totals.json")

_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_ORANGE = "\033[38;5;208m"
_RESET = "\033[0m"

_CACHE_HIGH_THRESHOLD = 60
_CACHE_LOW_THRESHOLD = 30

_RATE_RED_THRESHOLD = 90
_RATE_ORANGE_THRESHOLD = 70
_RATE_YELLOW_THRESHOLD = 50
_RATE_COUNTDOWN_THRESHOLD = 70


def token_speed_widget(data: StatuslineInput) -> str:
    """Tokens per second from total tokens and duration."""
    ctx = data.context_window
    cost = data.cost
    duration_ms = cost.total_duration_ms if cost else 0
    if duration_ms <= 0:
        return "\u2014 tok/s"
    input_tok = ctx.total_input_tokens if ctx else 0
    output_tok = ctx.total_output_tokens if ctx else 0
    tok_per_sec = (input_tok + output_tok) / (duration_ms / 1000)
    return f"{int(tok_per_sec)} tok/s"


def burn_rate_widget(data: StatuslineInput) -> str:
    """Cost per minute from total cost and duration."""
    cost = data.cost
    if not cost or cost.total_duration_ms <= 0:
        return "$0.00/min"
    rate = cost.total_cost_usd / (cost.total_duration_ms / 60_000)
    return f"${rate:.2f}/min"


def block_timer_widget(data: StatuslineInput) -> str:
    """Format session duration as M:SS or H:MM:SS."""
    cost = data.cost
    duration_ms = cost.total_duration_ms if cost else 0
    total_sec = int(duration_ms / 1000)
    if total_sec >= _SECONDS_PER_HOUR:
        hours = total_sec // _SECONDS_PER_HOUR
        mins = (total_sec % _SECONDS_PER_HOUR) // 60
        secs = total_sec % 60
        return f"{hours}:{mins:02d}:{secs:02d}"
    mins = total_sec // 60
    secs = total_sec % 60
    return f"{mins}:{secs:02d}"


def daily_totals_widget(data: StatuslineInput) -> str:
    """Cumulative daily cost and tokens, persisted to .artifacts/."""
    cost = data.cost
    ctx = data.context_window
    session_cost = cost.total_cost_usd if cost else 0
    input_tok = ctx.total_input_tokens if ctx else 0
    output_tok = ctx.total_output_tokens if ctx else 0
    session_tokens = input_tok + output_tok
    today = str(datetime.datetime.now(tz=datetime.UTC).date())

    try:
        existing = json.loads(_DAILY_TOTALS_FILE.read_text())
        if not isinstance(existing, dict) or existing.get("date") != today:
            existing = {}
    except (OSError, json.JSONDecodeError):
        existing = {}

    prev_cost = existing.get("total_cost_usd", 0)
    prev_tokens = existing.get("total_tokens", 0)
    is_today = existing.get("date") == today
    total_cost = session_cost + (prev_cost if is_today else 0)
    total_tokens = int(session_tokens + (prev_tokens if is_today else 0))

    _DAILY_TOTALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": today,
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
    }
    _DAILY_TOTALS_FILE.write_text(json.dumps(payload) + "\n")

    return f"day: ${total_cost:.2f} {total_tokens // 1000}k tok"


def lines_changed_widget(data: StatuslineInput) -> str:
    """Lines added/removed, color-coded."""
    cost = data.cost
    added = cost.total_lines_added if cost else 0
    removed = cost.total_lines_removed if cost else 0
    if added == 0 and removed == 0:
        return ""
    parts = []
    if added > 0:
        parts.append(f"{_GREEN}+{added}{_RESET}")
    if removed > 0:
        parts.append(f"{_RED}-{removed}{_RESET}")
    return "/".join(parts)


def cache_ratio_widget(data: StatuslineInput) -> str:
    """Cache hit ratio from current_usage tokens."""
    ctx = data.context_window
    usage = ctx.current_usage if ctx else None
    if not usage:
        return ""
    read = usage.cache_read_input_tokens
    create = usage.cache_creation_input_tokens
    inp = usage.input_tokens
    total = read + create + inp
    if total <= 0:
        return ""
    pct = int(read * 100 / total)
    if pct > _CACHE_HIGH_THRESHOLD:
        color = _GREEN
    elif pct > _CACHE_LOW_THRESHOLD:
        color = _YELLOW
    else:
        color = _RED
    return f"{color}cache:{pct}%{_RESET}"


def _color_for_pct(pct: float) -> str:
    """4-tier color: green (<50), yellow (50-69), orange (70-89), red (90+)."""
    if pct >= _RATE_RED_THRESHOLD:
        return _RED
    if pct >= _RATE_ORANGE_THRESHOLD:
        return _ORANGE
    if pct >= _RATE_YELLOW_THRESHOLD:
        return _YELLOW
    return _GREEN


def _format_countdown(resets_at: int) -> str:
    """Format Unix timestamp as relative countdown."""
    remaining = max(0, resets_at - int(time.time()))
    hours = remaining // 3600
    mins = (remaining % 3600) // 60
    if hours > 0:
        return f"{hours}h{mins:02d}m"
    return f"{mins}m"


def rate_limits_widget(rate_info: dict[str, RateLimitInfo | None]) -> str:
    """Rate limit usage for 5h and 7d windows."""
    parts: list[str] = []
    for label, key in [("5h", "five_hour"), ("7d", "seven_day")]:
        info = rate_info.get(key)
        if info is None:
            continue
        if info.status == "rejected":
            parts.append(f"{_RED}{label}:LIMIT{_RESET}")
        elif info.utilization is not None:
            pct = info.utilization * 100
            color = _color_for_pct(pct)
            text = f"{label}:{pct:.0f}%"
            if pct >= _RATE_COUNTDOWN_THRESHOLD and info.resets_at:
                text += f" \u21bb{_format_countdown(info.resets_at)}"
            parts.append(f"{color}{text}{_RESET}")
    return " ".join(parts)
