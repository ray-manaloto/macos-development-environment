"""Telemetry utilities (migrated from lib/mde-telemetry.sh)."""

from __future__ import annotations

import os


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled.

    Returns:
        True if telemetry is not explicitly disabled.
    """
    return os.environ.get("MDE_TELEMETRY_DISABLED", "0") != "1"
