"""Persistent state management for the dream pipeline.

State is stored as JSON in .generated/dream/state.json.
JSON format chosen per agent-notes policy (less likely to corrupt).
"""

from __future__ import annotations

import json
from pathlib import Path

from mde.dream.models import DreamState

_STATE_DIR = Path(".generated/dream")
_STATE_PATH = _STATE_DIR / "state.json"


def load_state() -> DreamState:
    """Load dream state from disk, or return fresh state."""
    if not _STATE_PATH.exists():
        return DreamState()
    try:
        data = json.loads(_STATE_PATH.read_text())
        return DreamState.model_validate(data)
    except (OSError, json.JSONDecodeError, ValueError):
        return DreamState()


def save_state(state: DreamState) -> None:
    """Persist dream state to disk."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(state.model_dump_json(indent=2) + "\n")
