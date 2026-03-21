"""Typed SkillsMP API client using httpx + Pydantic models.

SDK-first: all responses are parsed into typed Pydantic models.
Reads SKILLSMP_API_KEY from environment (set by fnox → mise → keychain).

API docs: https://skillsmp.com/docs/api
Rate limit: 500 requests/day per API key.
"""

from __future__ import annotations

import os

import httpx

from mde.research.clients.skillsmp_models import (
    AISearchResponse,
    ErrorResponse,
    SkillSearchResponse,
)

__all__ = ["SkillsMPClient"]

_BASE_URL = "https://skillsmp.com/api/v1/skills"


class SkillsMPClient:
    """Typed client for SkillsMP REST API.

    Usage::

        client = SkillsMPClient()  # reads SKILLSMP_API_KEY from env
        response = client.search("chezmoi", limit=5)
        for skill in response.data.skills:
            print(f"{skill.author}/{skill.name} ({skill.stars} stars)")
    """

    def __init__(  # noqa: D107
        self,
        api_key: str | None = None,
        base_url: str = _BASE_URL,
        timeout: float = 10.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("SKILLSMP_API_KEY", "")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Whether an API key is available."""
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "mde-py/1.0 (skill-discovery)",
        }

    def search(
        self,
        query: str,
        *,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "stars",
    ) -> SkillSearchResponse | ErrorResponse:
        """Keyword search across SkillsMP catalog.

        Args:
            query: Search terms.
            page: Page number (1-indexed).
            limit: Results per page (max 100).
            sort_by: Sort order — "stars" or "recent".

        Returns:
            Typed SkillSearchResponse or ErrorResponse.
        """
        if not self.is_configured:
            return ErrorResponse(
                success=False,
                error={  # type: ignore[arg-type]
                    "code": "MISSING_API_KEY",
                    "message": (
                        "SKILLSMP_API_KEY not set. Store in keychain: "
                        "security add-generic-password -a $USER -s mde-fnox -D SKILLSMP_API_KEY"
                    ),
                },
            )

        try:
            resp = httpx.get(
                f"{self._base_url}/search",
                params={"q": query, "page": page, "limit": limit, "sortBy": sort_by},
                headers=self._headers(),
                timeout=self._timeout,
            )
            data = resp.json()
            if data.get("success"):
                return SkillSearchResponse.model_validate(data)
            return ErrorResponse.model_validate(data)
        except httpx.HTTPError as e:
            return ErrorResponse(
                success=False,
                error={"code": "HTTP_ERROR", "message": str(e)},  # type: ignore[arg-type]
            )

    def ai_search(self, query: str) -> AISearchResponse | ErrorResponse:
        """AI semantic search powered by Cloudflare AI.

        Args:
            query: Natural language query.

        Returns:
            Typed AISearchResponse or ErrorResponse.
        """
        if not self.is_configured:
            return ErrorResponse(
                success=False,
                error={  # type: ignore[arg-type]
                    "code": "MISSING_API_KEY",
                    "message": "SKILLSMP_API_KEY not set.",
                },
            )

        try:
            resp = httpx.get(
                f"{self._base_url}/ai-search",
                params={"q": query},
                headers=self._headers(),
                timeout=self._timeout,
            )
            data = resp.json()
            if data.get("success"):
                return AISearchResponse.model_validate(data)
            return ErrorResponse.model_validate(data)
        except httpx.HTTPError as e:
            return ErrorResponse(
                success=False,
                error={"code": "HTTP_ERROR", "message": str(e)},  # type: ignore[arg-type]
            )
