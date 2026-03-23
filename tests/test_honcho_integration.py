"""Tests for the Honcho SDK client factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mde.domain.honcho_models import HonchoClientConfig


class TestGetConfig:
    """Tests for get_config() env var handling."""

    def test_defaults_without_env_vars(self) -> None:
        from mde.domain.honcho import get_config

        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
        assert config.base_url == "http://localhost:8000"
        assert config.workspace_id == "mde"
        assert config.api_key is None
        assert config.timeout == 10
        assert config.max_retries == 0

    def test_reads_env_vars(self) -> None:
        from mde.domain.honcho import get_config

        env = {
            "HONCHO_BASE_URL": "http://custom:9000",
            "HONCHO_WORKSPACE_ID": "test-ws",
            "HONCHO_API_KEY": "secret-key",
            "HONCHO_TIMEOUT": "30",
            "HONCHO_MAX_RETRIES": "3",
        }
        with patch.dict("os.environ", env, clear=True):
            config = get_config()
        assert config.base_url == "http://custom:9000"
        assert config.workspace_id == "test-ws"
        assert config.api_key == "secret-key"
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_malformed_timeout_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with (
            patch.dict("os.environ", {"HONCHO_TIMEOUT": "abc"}, clear=True),
            pytest.raises(ValueError, match="HONCHO_TIMEOUT must be a number"),
        ):
            get_config()

    def test_malformed_max_retries_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with (
            patch.dict("os.environ", {"HONCHO_MAX_RETRIES": "xyz"}, clear=True),
            pytest.raises(ValueError, match="HONCHO_MAX_RETRIES must be an integer"),
        ):
            get_config()

    def test_partial_env_vars(self) -> None:
        """Test that setting some env vars doesn't affect defaults for others."""
        from mde.domain.honcho import get_config

        env = {"HONCHO_BASE_URL": "http://custom:9000"}
        with patch.dict("os.environ", env, clear=True):
            config = get_config()
        assert config.base_url == "http://custom:9000"
        assert config.workspace_id == "mde"  # default preserved
        assert config.api_key is None  # default preserved
        assert config.timeout == 10  # default preserved
        assert config.max_retries == 0  # default preserved

    def test_negative_timeout_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with (
            patch.dict("os.environ", {"HONCHO_TIMEOUT": "-5"}, clear=True),
            pytest.raises(ValueError, match="HONCHO_TIMEOUT must be positive"),
        ):
            get_config()

    def test_negative_max_retries_raises_valueerror(self) -> None:
        from mde.domain.honcho import get_config

        with (
            patch.dict("os.environ", {"HONCHO_MAX_RETRIES": "-1"}, clear=True),
            pytest.raises(ValueError, match="HONCHO_MAX_RETRIES must be non-negative"),
        ):
            get_config()


class TestGetClient:
    """Tests for get_client() SDK construction."""

    def test_passes_config_to_sdk(self) -> None:
        config = HonchoClientConfig(
            base_url="http://test:8000",
            workspace_id="test-ws",
            api_key="test-key",
            timeout=5.0,
            max_retries=2,
        )
        with patch("honcho.Honcho") as mock_cls:
            from mde.domain.honcho import get_client

            get_client(config)
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url="http://test:8000",
                workspace_id="test-ws",
                timeout=5.0,
                max_retries=2,
            )

    def test_uses_default_config_when_none(self) -> None:
        with (
            patch("honcho.Honcho") as mock_cls,
            patch.dict("os.environ", {}, clear=True),
        ):
            from mde.domain.honcho import get_client

            get_client()
            mock_cls.assert_called_once_with(
                api_key=None,
                base_url="http://localhost:8000",
                workspace_id="mde",
                timeout=10.0,
                max_retries=0,
            )


class TestTestConnection:
    """Tests for test_connection() health probe."""

    def test_success(self) -> None:
        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.return_value = []
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is True
        assert msg == "Connected"

    def test_connection_error(self) -> None:
        from honcho import ConnectionError as HonchoConnectionError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = HonchoConnectionError("refused")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Connection failed" in msg

    def test_timeout_error(self) -> None:
        from honcho import TimeoutError as HonchoTimeoutError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = HonchoTimeoutError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Timeout" in msg

    def test_auth_error(self) -> None:
        from honcho import AuthenticationError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = AuthenticationError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Auth required" in msg

    def test_not_found_error(self) -> None:
        from honcho import NotFoundError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = NotFoundError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "API v3" in msg

    def test_server_error(self) -> None:
        from honcho import ServerError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = ServerError("boom")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Server error" in msg

    def test_rate_limit_error(self) -> None:
        from honcho import RateLimitError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = RateLimitError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Rate limited" in msg

    def test_permission_denied_error(self) -> None:
        from honcho import PermissionDeniedError

        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = PermissionDeniedError()
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Permission denied" in msg

    def test_unexpected_error(self) -> None:
        with patch("honcho.Honcho") as mock_cls:
            mock_cls.return_value.workspaces.side_effect = RuntimeError("surprise")
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "Unexpected error" in msg


class TestTestConnectionImportError:
    """Test test_connection() when SDK is not installed."""

    def test_import_error_returns_false(self) -> None:
        import builtins

        real_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "honcho":
                msg = "No module named 'honcho'"
                raise ImportError(msg)
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            from mde.domain.honcho import test_connection

            ok, msg = test_connection()
        assert ok is False
        assert "not installed" in msg


class TestHonchoClientConfigValidation:
    """Tests for schema-enforced constraints on the generated model."""

    def test_rejects_zero_timeout(self) -> None:
        with pytest.raises(Exception, match="greater than 0"):
            HonchoClientConfig(timeout=0)

    def test_rejects_negative_max_retries(self) -> None:
        with pytest.raises(Exception, match="greater than or equal to 0"):
            HonchoClientConfig(max_retries=-1)

    def test_accepts_valid_config(self) -> None:
        config = HonchoClientConfig(timeout=5, max_retries=3)
        assert config.timeout == 5
        assert config.max_retries == 3


@pytest.mark.integration
class TestHonchoIntegration:
    """Integration tests requiring a running Honcho server.

    Skipped in CI. Run with: pytest -m integration
    Requires: mde-memory stack up (docker compose)
    """

    def test_real_connection(self) -> None:
        from mde.domain.honcho import test_connection

        ok, msg = test_connection()
        assert ok is True, f"Connection failed: {msg}"
