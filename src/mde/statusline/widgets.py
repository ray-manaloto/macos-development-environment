"""Statusline widget functions.

Each widget receives a validated StatuslineInput and returns a string.
Empty string means the widget is suppressed from the metrics bar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mde.statusline.models import StatuslineInput

_SECONDS_PER_HOUR = 3600


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
