"""JSON utility functions (migrated from lib/mde-json.sh)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_config(path: Path) -> dict[str, Any]:
    """Load a JSON config file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON as a dict.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file isn't valid JSON.
    """
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    if not isinstance(data, dict):
        msg = f"Expected JSON object at {path}, got {type(data).__name__}"
        raise TypeError(msg)
    return data
