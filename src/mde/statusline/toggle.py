"""Statusline mode toggle — cycles A -> B -> C -> A.

Persists mode to .artifacts/statusline-mode.
"""

from __future__ import annotations

from pathlib import Path

_MODE_FILE = Path(".artifacts/statusline-mode")
_CYCLE = {"A": "B", "B": "C", "C": "A"}


def toggle_mode() -> int:
    """Cycle display mode and write to state file."""
    try:
        current = _MODE_FILE.read_text().strip().upper()
    except OSError:
        current = "A"

    next_mode = _CYCLE.get(current, "B")  # Unknown defaults to B (as if from A)

    _MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MODE_FILE.write_text(next_mode + "\n")

    print(f"{current} \u2192 {next_mode}")
    return 0


def show_mode() -> int:
    """Print current display mode."""
    try:
        mode = _MODE_FILE.read_text().strip().upper()
    except OSError:
        mode = "A"

    print(mode)
    return 0
