"""Statusline stdin parsing — wraps generated Pydantic models + SDK rate limit types.

Generated models: src/mde/statusline/models.py (never hand-edit).
Regenerate: mise run mde:codegen:statusline
JSON Schema source: src/mde/statusline/statusline-stdin.schema.json
Official docs: https://code.claude.com/docs/en/statusline
"""

from __future__ import annotations

import json
import sys
from typing import Any

from claude_agent_sdk.types import RateLimitInfo

from mde.statusline.models import StatuslineInput

_KNOWN_KEYS = frozenset(StatuslineInput.model_fields.keys())


def parse_stdin(data: dict[str, Any]) -> StatuslineInput:
    """Validate stdin dict into a typed StatuslineInput.

    Pydantic V2 handles string-to-number coercion, null defaults,
    and extra field preservation automatically.
    """
    _warn_unknown_keys(data)
    return StatuslineInput.model_validate(data)


def parse_stdin_raw(raw: str) -> StatuslineInput:
    """Parse raw JSON string from stdin into StatuslineInput.

    Returns default (empty) StatuslineInput on invalid JSON.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        data = {}
    return parse_stdin(data) if isinstance(data, dict) else StatuslineInput()


def parse_rate_limits(raw: Any) -> dict[str, RateLimitInfo | None]:
    """Parse rate_limits from stdin JSON into SDK RateLimitInfo objects.

    Handles both Shape A (flat with rateLimitType) and Shape B (nested by window).
    Normalizes camelCase wire format to snake_case SDK fields.
    """
    if not isinstance(raw, dict):
        return {"five_hour": None, "seven_day": None, "overage": None}

    result: dict[str, RateLimitInfo | None] = {}

    # Shape B: nested by window name
    for window_name in ("five_hour", "seven_day", "overage"):
        window = raw.get(window_name)
        if isinstance(window, dict):
            result[window_name] = RateLimitInfo(
                status=window.get("status", "allowed"),
                resets_at=_int_or_none(window.get("resetsAt") or window.get("resets_at")),
                rate_limit_type=window.get("rateLimitType") or window.get("rate_limit_type"),
                utilization=_float_or_none(window.get("utilization")),
                raw=window,
            )
        else:
            result[window_name] = None

    # Shape A fallback: flat dict with rate_limit_type identifying the window
    if all(v is None for v in result.values()) and "status" in raw:
        window_name = raw.get("rateLimitType") or raw.get("rate_limit_type") or "five_hour"
        if window_name in ("seven_day_opus", "seven_day_sonnet"):
            window_name = "seven_day"
        result[window_name] = RateLimitInfo(
            status=raw.get("status", "allowed"),
            resets_at=_int_or_none(raw.get("resetsAt") or raw.get("resets_at")),
            rate_limit_type=raw.get("rateLimitType") or raw.get("rate_limit_type"),
            utilization=_float_or_none(raw.get("utilization")),
            raw=raw,
        )

    return result


def _warn_unknown_keys(data: dict[str, Any]) -> None:
    unknown = set(data.keys()) - _KNOWN_KEYS
    if unknown:
        print(f"[statusline] unknown stdin keys: {unknown}", file=sys.stderr)


def _float_or_none(val: object) -> float | None:
    if val is None:
        return None
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _int_or_none(val: object) -> int | None:
    if val is None:
        return None
    try:
        return int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
