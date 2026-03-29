"""Shared path utilities for the mde package."""

from __future__ import annotations

import contextlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Return the git repository root, falling back to cwd.

    Cached for the lifetime of the process since the repo root
    doesn't change during a single CLI invocation.
    """
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


def generated_dir() -> Path:
    """Return the .generated/ directory under repo root."""
    return repo_root() / ".generated"
