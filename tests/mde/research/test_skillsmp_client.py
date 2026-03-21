"""Tests for SkillsMP API client."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import httpx

from mde.research.clients.skillsmp_client import SkillsMPClient
from mde.research.clients.skillsmp_models import (
    ErrorResponse,
    SkillSearchResponse,
)


class TestSkillsMPClientConfig:
    """Configuration and missing-key behavior."""

    @patch.dict(os.environ, {"SKILLSMP_API_KEY": ""})
    def test_no_api_key_is_not_configured(self) -> None:
        client = SkillsMPClient(api_key="")
        assert client.is_configured is False

    def test_api_key_is_configured(self) -> None:
        client = SkillsMPClient(api_key="test-key-123")
        assert client.is_configured is True

    @patch.dict(os.environ, {"SKILLSMP_API_KEY": ""})
    def test_search_without_key_returns_error(self) -> None:
        client = SkillsMPClient(api_key="")
        result = client.search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "MISSING_API_KEY"

    @patch.dict(os.environ, {"SKILLSMP_API_KEY": ""})
    def test_ai_search_without_key_returns_error(self) -> None:
        client = SkillsMPClient(api_key="")
        result = client.ai_search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "MISSING_API_KEY"


class TestSkillsMPClientSearch:
    """Search endpoint with mocked HTTP layer."""

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_successful_search(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True,
            "data": {
                "skills": [{"id": "1", "name": "terraform", "author": "hashicorp", "stars": 50}],
                "total": 1,
                "page": 1,
                "limit": 10,
            },
        }
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform", limit=10)

        assert isinstance(result, SkillSearchResponse)
        assert result.success is True
        assert result.data is not None
        assert len(result.data.skills) == 1
        assert result.data.skills[0].name == "terraform"

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_api_error_response(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": False,
            "error": {"code": "RATE_LIMIT", "message": "Too many requests"},
        }
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "RATE_LIMIT"

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_http_error_returns_error_response(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "HTTP_ERROR"

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_search_passes_params(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True,
            "data": {"skills": [], "total": 0, "page": 2, "limit": 5},
        }
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="key", base_url="https://example.com/api")
        client.search("test", page=2, limit=5, sort_by="recent")

        call_args = mock_get.call_args
        assert call_args[1]["params"]["q"] == "test"
        assert call_args[1]["params"]["page"] == 2
        assert call_args[1]["params"]["limit"] == 5
        assert call_args[1]["params"]["sortBy"] == "recent"
