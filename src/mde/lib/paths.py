"""Centralized MDE path configuration.

All ``.generated/`` subdirectory paths are managed here via a single
pydantic-settings ``BaseSettings`` model. Environment variables are set by
mise (via chezmoi-managed global config) and read automatically.

Usage::

    from mde.lib.paths import get_paths

    paths = get_paths()
    dest = paths.dir_remember  # Path(".generated/remember")

Testing::

    paths = MdePaths(project_dir=tmp_path)  # no env vars needed
"""

from __future__ import annotations

import contextlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

# Subdirectory names under .generated/ — single source of truth for defaults
_CHILD_DEFAULTS: dict[str, str] = {
    "dir_remember": "remember",
    "dir_learnings": "learnings",
    "dir_transcripts": "transcripts",
    "dir_schemas": "schemas",
    "dir_reports": "reports",
    "dir_context": "context",
    "dir_dream": "dream",
}


def _detect_repo_root() -> Path:
    """Detect git repo root via git rev-parse, falling back to cwd."""
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


class MdePaths(BaseSettings):
    """Centralized MDE path configuration.

    Reads MDE_* environment variables (set by mise via chezmoi-managed global config).
    Applies cascading defaults: project_dir -> generated_dir -> child dirs.
    Pass explicit values in tests: ``MdePaths(project_dir=tmp_path)``.
    """

    model_config = SettingsConfigDict(
        env_prefix="MDE_",
        populate_by_name=True,
        extra="ignore",
    )

    project_dir: Path | None = Field(
        default=None,
        description="Repository root (MDE_PROJECT_DIR). Detected via git if unset.",
    )
    generated_dir: Path | None = Field(
        default=None,
        description="Root of all runtime artifacts (MDE_GENERATED_DIR).",
    )
    dir_remember: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_REMEMBER",
    )
    dir_learnings: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_LEARNINGS",
    )
    dir_transcripts: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_TRANSCRIPTS",
    )
    dir_schemas: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_SCHEMAS",
    )
    dir_reports: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_REPORTS",
    )
    dir_context: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_CONTEXT",
    )
    dir_dream: Path | None = Field(
        default=None,
        validation_alias="MDE_DIR_DREAM",
    )

    def model_post_init(self, _context: Any) -> None:
        """Apply cascading defaults: project_dir -> generated_dir -> child dirs."""
        if self.project_dir is None:
            self.project_dir = _detect_repo_root()
        if self.generated_dir is None:
            self.generated_dir = self.project_dir / ".generated"
        for field_name, subdir in _CHILD_DEFAULTS.items():
            if getattr(self, field_name) is None:
                setattr(self, field_name, self.generated_dir / subdir)


@lru_cache(maxsize=1)
def get_paths() -> MdePaths:
    """Return the singleton MdePaths instance.

    Cached for the process lifetime. All consumers use this
    instead of constructing MdePaths directly.
    """
    return MdePaths()


# ── Backward-compatible aliases (remove after full migration) ──


def repo_root() -> Path:
    """Return the repository root. Alias for get_paths().project_dir."""
    p = get_paths().project_dir
    assert p is not None  # noqa: S101 — always set by model_post_init
    return p


def generated_dir() -> Path:
    """Return .generated/ dir. Alias for get_paths().generated_dir."""
    p = get_paths().generated_dir
    assert p is not None  # noqa: S101 — always set by model_post_init
    return p
