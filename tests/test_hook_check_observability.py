"""Tests for the check_observability SessionStart hook."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mde.hooks.check_observability import _check_endpoint, check_services


class TestCheckEndpoint:
    """Test individual endpoint health checks."""

    @patch("mde.hooks.check_observability.urllib.request.urlopen")
    def test_returns_true_when_healthy(self, mock_urlopen: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        assert _check_endpoint("http://localhost:13133") is True

    @patch(
        "mde.hooks.check_observability.urllib.request.urlopen",
        side_effect=ConnectionRefusedError("Connection refused"),
    )
    def test_returns_false_when_down(self, mock_urlopen: MagicMock) -> None:
        _ = mock_urlopen
        assert _check_endpoint("http://localhost:13133") is False

    @patch(
        "mde.hooks.check_observability.urllib.request.urlopen",
        side_effect=TimeoutError("timed out"),
    )
    def test_returns_false_on_timeout(self, mock_urlopen: MagicMock) -> None:
        _ = mock_urlopen
        assert _check_endpoint("http://localhost:13133") is False


class TestCheckServices:
    """Test multi-service health check."""

    @patch("mde.hooks.check_observability._check_endpoint", return_value=True)
    def test_all_healthy(self, mock_check: MagicMock) -> None:
        results = check_services()
        assert all(results.values())
        assert set(results.keys()) == {"grafana", "loki", "tempo"}
        assert mock_check.call_count == 3

    @patch("mde.hooks.check_observability._check_endpoint")
    def test_partial_failure(self, mock_check: MagicMock) -> None:
        """Reports which specific services are down."""
        mock_check.side_effect = [True, False, True]  # grafana ok, loki down, tempo ok
        results = check_services()
        assert results["grafana"] is True
        assert results["loki"] is False
        assert results["tempo"] is True

    @patch("mde.hooks.check_observability._check_endpoint", return_value=False)
    def test_all_down(self, mock_check: MagicMock) -> None:
        results = check_services()
        assert not any(results.values())
        assert mock_check.call_count == 3
