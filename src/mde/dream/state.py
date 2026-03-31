"""Persistent state management for the dream pipeline.

State is stored as JSON in .generated/dream/state.json.
JSON format chosen per agent-notes policy (less likely to corrupt).
"""

from __future__ import annotations

import json
from pathlib import Path

from mde.dream.models import DreamState
from mde.lib.paths import get_paths


def _state_dir() -> Path:
    d = get_paths().dir_dream
    assert d is not None  # noqa: S101 — always set by model_post_init
    return d


def _state_path() -> Path:
    return _state_dir() / "state.json"


def load_state() -> DreamState:
    """Load dream state from disk, or return fresh state."""
    path = _state_path()
    if not path.exists():
        return DreamState()
    try:
        data = json.loads(path.read_text())
        return DreamState.model_validate(data)
    except (OSError, json.JSONDecodeError, ValueError):
        return DreamState()


def save_state(state: DreamState) -> None:
    """Persist dream state to disk."""
    sdir = _state_dir()
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "state.json").write_text(state.model_dump_json(indent=2) + "\n")
