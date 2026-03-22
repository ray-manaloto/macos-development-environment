"""Tests for telemetry configuration verification."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    import pytest

from mde.telemetry_verify import (
    _check_env_vars,
    _check_hooks_dispatch,
    _check_plugins,
    verify_telemetry,
)


class TestCheckEnvVars:
    """Tests for _check_env_vars."""

    def test_all_set_correctly(self) -> None:
        """All required vars set to expected values returns all OK."""
        env = {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
        }
        results = _check_env_vars(env)
        assert all(status == "OK" for _, status, _ in results)

    def test_missing_var(self) -> None:
        """Missing env var returns MISSING status."""
        env: dict[str, str] = {}
        with patch.dict("os.environ", {}, clear=True):
            results = _check_env_vars(env)
        statuses = {name: status for name, status, _ in results}
        assert statuses["CLAUDE_CODE_ENABLE_TELEMETRY"] == "MISSING"

    def test_wrong_value(self) -> None:
        """Wrong value for a fixed-value var returns MISMATCH."""
        env = {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
        }
        results = _check_env_vars(env)
        statuses = {name: status for name, status, _ in results}
        assert statuses["CLAUDE_CODE_ENABLE_TELEMETRY"] == "MISMATCH"

    def test_endpoint_any_value_ok(self) -> None:
        """OTEL_EXPORTER_OTLP_ENDPOINT accepts any non-empty value."""
        env = {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://custom:9999",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
        }
        results = _check_env_vars(env)
        statuses = {name: status for name, status, _ in results}
        assert statuses["OTEL_EXPORTER_OTLP_ENDPOINT"] == "OK"

    def test_falls_back_to_os_environ(self) -> None:
        """Falls back to os.environ when not in settings_env."""
        env: dict[str, str] = {}
        with patch.dict("os.environ", {"CLAUDE_CODE_ENABLE_TELEMETRY": "1"}, clear=True):
            results = _check_env_vars(env)
        statuses = {name: status for name, status, _ in results}
        assert statuses["CLAUDE_CODE_ENABLE_TELEMETRY"] == "OK"


class TestCheckPlugins:
    """Tests for _check_plugins."""

    def test_conflicting_plugin_disabled(self) -> None:
        """Conflicting plugin set to false is OK."""
        settings = {"enabledPlugins": {"hookify@claude-plugins-official": False}}
        results = _check_plugins(settings)
        assert all(status == "OK" for _, status, _ in results)

    def test_conflicting_plugin_enabled(self) -> None:
        """Conflicting plugin set to true is MISMATCH."""
        settings = {"enabledPlugins": {"hookify@claude-plugins-official": True}}
        results = _check_plugins(settings)
        statuses = {name: status for name, status, _ in results}
        assert statuses["hookify@claude-plugins-official"] == "MISMATCH"

    def test_conflicting_plugin_absent(self) -> None:
        """Plugin not present at all is OK."""
        settings = {"enabledPlugins": {}}
        results = _check_plugins(settings)
        assert all(status == "OK" for _, status, _ in results)

    def test_no_enabled_plugins_key(self) -> None:
        """Missing enabledPlugins key is OK (plugins not configured)."""
        settings: dict[str, object] = {}
        results = _check_plugins(settings)
        assert all(status == "OK" for _, status, _ in results)


class TestCheckHooksDispatch:
    """Tests for _check_hooks_dispatch."""

    def test_all_dispatch_entries_have_subparsers(self) -> None:
        """Every _HOOKS_DISPATCH key should have a matching subparser."""
        results = _check_hooks_dispatch()
        failed = [(name, status, detail) for name, status, detail in results if status != "OK"]
        assert not failed, f"Hooks dispatch/subparser mismatches: {failed}"


class TestVerifyTelemetry:
    """Integration tests for verify_telemetry."""

    def test_returns_int(self) -> None:
        """verify_telemetry returns an integer exit code."""
        result = verify_telemetry()
        assert isinstance(result, int)
        assert result in (0, 1)

    def test_all_pass_with_correct_settings(self, tmp_path: pytest.TempPathFactory) -> None:
        """Returns 0 when all settings are correct."""
        settings = {
            "enabledPlugins": {"hookify@claude-plugins-official": False},
            "env": {
                "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
                "OTEL_METRICS_EXPORTER": "otlp",
                "OTEL_LOGS_EXPORTER": "otlp",
            },
        }
        with patch("mde.telemetry_verify._load_settings", return_value=(settings, settings["env"])):
            result = verify_telemetry()
        assert result == 0

    def test_fails_with_missing_env(self, tmp_path: pytest.TempPathFactory) -> None:
        """Returns 1 when required env vars are missing."""
        settings: dict[str, object] = {
            "enabledPlugins": {"hookify@claude-plugins-official": False},
            "env": {},
        }
        with (
            patch("mde.telemetry_verify._load_settings", return_value=(settings, {})),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = verify_telemetry()
        assert result == 1
