"""Platform detection utilities (migrated from lib/mde-platform.sh)."""

from __future__ import annotations

import os
import platform
from pathlib import Path

_EXPLICIT_MAP: dict[str, str] = {
    "macos": "macos",
    "darwin": "macos",
    "devcontainer": "devcontainer",
    "linux": "linux",
    "container": "linux",
}

_SYSTEM_MAP: dict[str, str] = {
    "Darwin": "macos",
    "Linux": "linux",
}


def detect_platform() -> str:
    """Detect the current platform.

    Returns:
        One of 'macos', 'devcontainer', 'linux', 'unknown'.
    """
    explicit = os.environ.get("MDE_PLATFORM", "")
    if explicit:
        result = _EXPLICIT_MAP.get(explicit.lower())
        if result:
            return result

    if os.environ.get("DEVCONTAINER") or os.environ.get("CODESPACES"):
        return "devcontainer"

    if Path("/.dockerenv").exists():
        return "linux"

    return _SYSTEM_MAP.get(platform.system(), "unknown")


def is_macos() -> bool:
    """Check if running on macOS."""
    return detect_platform() == "macos"


def is_devcontainer() -> bool:
    """Check if running in a devcontainer."""
    return detect_platform() == "devcontainer"
