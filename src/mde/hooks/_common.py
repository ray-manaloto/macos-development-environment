"""Shared utilities for Claude Code hook entry points."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mde.log import get_tracer, logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from opentelemetry.trace import Span

_tracer = get_tracer("mde.hooks")

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def parse_hook_stdin() -> dict[str, Any]:
    """Parse Claude Code hook JSON from stdin."""
    return json.load(sys.stdin)


def repo_root() -> Path:
    """Return the git repository root, falling back to cwd."""
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            env=_GIT_ENV,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return Path.cwd()


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


__all__ = ["hook_span", "logger", "parse_hook_stdin", "repo_root"]
