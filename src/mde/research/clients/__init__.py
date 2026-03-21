"""Typed API clients for skill discovery marketplaces.

SDK-first approach: use typed Pydantic clients, not raw HTTP.

Available clients:
    SkillKitClient — Local SkillKit server (localhost:3737)
    SkillsMPClient — SkillsMP REST API (requires SKILLSMP_API_KEY)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mde.research.clients.skillkit_client import SkillKitClient
    from mde.research.clients.skillsmp_client import SkillsMPClient

__all__ = ["SkillKitClient", "SkillsMPClient"]


def __getattr__(name: str) -> object:
    """Lazy imports to avoid loading httpx at module import time."""
    if name == "SkillsMPClient":
        from mde.research.clients.skillsmp_client import SkillsMPClient

        return SkillsMPClient
    if name == "SkillKitClient":
        from mde.research.clients.skillkit_client import SkillKitClient

        return SkillKitClient
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
