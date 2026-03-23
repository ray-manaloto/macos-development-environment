"""Shared utilities for Claude Code hook entry points."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from mde.log import get_tracer, logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from opentelemetry.trace import Span

_tracer = get_tracer("mde.hooks")


def parse_hook_stdin() -> dict[str, Any]:
    """Parse Claude Code hook JSON from stdin."""
    return json.load(sys.stdin)


@contextmanager
def hook_span(
    name: str,
    event: str,
    data: dict[str, Any],
) -> Generator[Span]:
    """Open a traced span for a hook with standard attributes."""
    session_id = data.get("session_id", "")
    tool_use_id = data.get("tool_use_id", "")
    with _tracer.start_as_current_span(f"mde.hook.{name}") as span:
        span.set_attribute("hook.event", event)
        span.set_attribute("claude.session_id", session_id)
        if tool_use_id:
            span.set_attribute("claude.tool_use_id", tool_use_id)
        yield span


__all__ = ["hook_span", "logger", "parse_hook_stdin"]
