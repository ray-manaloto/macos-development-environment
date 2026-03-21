"""Typed SkillKit API client using httpx + Pydantic models.

Vendored from: https://github.com/rohitg00/skillkit/blob/main/clients/python/skillkit/client.py
License: Apache-2.0
Modified: converted from async to sync (httpx.Client instead of AsyncClient).

Talks to a local SkillKit server. Start it with: npx skillkit serve
Default URL: http://localhost:3737
"""

from __future__ import annotations

from typing import Self

import httpx

from mde.research.clients.skillkit_models import (
    CacheStats,
    Category,
    HealthResponse,
    SearchResponse,
    Skill,
)

__all__ = ["SkillKitClient"]


class SkillKitClient:
    """Sync client for a local SkillKit server.

    Usage::

        client = SkillKitClient()
        results = client.search("terraform", limit=5)
        for skill in results.skills:
            print(f"{skill.source}/{skill.name} ({skill.stars} stars)")
    """

    def __init__(  # noqa: D107
        self,
        base_url: str = "http://localhost:3737",
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.Client | None = None

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager, close HTTP client."""
        self.close()

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=self._timeout)
        return self._client

    def health(self) -> HealthResponse:
        """Check server health."""
        client = self._get_client()
        resp = client.get("/health")
        resp.raise_for_status()
        data = resp.json()
        return HealthResponse(
            status=data["status"],
            version=data["version"],
            skill_count=data.get("skillCount", 0),
            uptime=data.get("uptime", 0),
        )

    def search(
        self,
        query: str,
        limit: int = 20,
        *,
        include_content: bool = False,
    ) -> SearchResponse:
        """Search skills by keyword."""
        client = self._get_client()
        params: dict[str, str] = {"q": query, "limit": str(limit)}
        if include_content:
            params["include_content"] = "true"
        resp = client.get("/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        return SearchResponse(
            skills=[Skill(**s) for s in data["skills"]],
            total=data["total"],
            query=data["query"],
            limit=data["limit"],
        )

    def trending(self, limit: int = 20) -> list[Skill]:
        """Get trending skills."""
        client = self._get_client()
        resp = client.get("/trending", params={"limit": str(limit)})
        resp.raise_for_status()
        data = resp.json()
        return [Skill(**s) for s in data["skills"]]

    def categories(self) -> list[Category]:
        """List skill categories."""
        client = self._get_client()
        resp = client.get("/categories")
        resp.raise_for_status()
        data = resp.json()
        return [Category(**c) for c in data["categories"]]

    def cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        client = self._get_client()
        resp = client.get("/cache/stats")
        resp.raise_for_status()
        data = resp.json()
        return CacheStats(
            hits=data["hits"],
            misses=data["misses"],
            size=data["size"],
            max_size=data.get("maxSize", 0),
            hit_rate=data.get("hitRate", 0.0),
        )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
