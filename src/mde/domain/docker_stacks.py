"""Shared Docker stack path constants and helpers.

All Docker infrastructure paths are defined here. Modules like
observability_stack.py and memory_stack.py import from this module
to avoid duplicating path logic.

HISTORY: Created in PR B (2026-03-23) to consolidate paths when
the project moved from single-stack to multi-stack Docker architecture
with root Compose + include directive.
"""

from __future__ import annotations

from pathlib import Path

# All Docker infrastructure lives under docker/ in the project root.
DOCKER_DIR = Path(__file__).resolve().parents[3] / "docker"

# Root compose.yaml — single entry point that includes sub-stacks.
ROOT_COMPOSE = DOCKER_DIR / "compose.yaml"

# Sub-stack compose files
OBSERVABILITY_COMPOSE = DOCKER_DIR / "observability" / "compose.yaml"
MEMORY_COMPOSE = DOCKER_DIR / "memory" / "compose.yaml"
