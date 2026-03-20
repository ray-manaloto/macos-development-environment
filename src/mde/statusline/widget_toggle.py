# src/mde/statusline/widget_toggle.py
"""Per-widget toggle for statusline metrics bar.

Persists config to .artifacts/statusline-widgets.json.
All widgets default to enabled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_WIDGET_CONFIG_FILE = Path(".artifacts/statusline-widgets.json")

ALL_WIDGETS = [
    "token_speed",
    "burn_rate",
    "block_timer",
    "daily_totals",
    "lines_changed",
    "cache_ratio",
    "rate_limits",
]


def read_widget_config() -> dict[str, bool]:
    """Read per-widget toggles, defaulting all to True."""
    try:
        data: dict[str, Any] = json.loads(_WIDGET_CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    return {name: bool(data.get(name, True)) for name in ALL_WIDGETS}


def _write_widget_config(config: dict[str, bool]) -> None:
    _WIDGET_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WIDGET_CONFIG_FILE.write_text(json.dumps(config, indent=4) + "\n")


def toggle_widget(name: str) -> int:
    """Toggle a widget on/off. Returns 0 on success, 1 on unknown name."""
    if name != "all" and name not in ALL_WIDGETS:
        print(f"Unknown widget: {name}. Valid: {', '.join(ALL_WIDGETS)}, all")
        return 1

    config = read_widget_config()

    if name == "all":
        new_state = not any(config.values())
        config = dict.fromkeys(ALL_WIDGETS, new_state)
    else:
        old = config[name]
        config[name] = not old
        print(f"{name}: {'on' if old else 'off'} \u2192 {'off' if old else 'on'}")

    _write_widget_config(config)
    return 0


def show_widgets() -> int:
    """Print widget toggle state table."""
    config = read_widget_config()
    for name, enabled in config.items():
        print(f"{name:<14} {'on' if enabled else 'off'}")
    return 0
