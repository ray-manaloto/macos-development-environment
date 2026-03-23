"""Tests for observability stack management."""

from __future__ import annotations

from unittest.mock import patch

from mde.domain.observability_stack import (
    COMPOSE_FILE,
    stack_up,
    stop_orphan_collectors,
)


class TestStopOrphanCollectors:
    """Test legacy codex-otel-collector detection and removal."""

    def test_stops_codex_collector(self) -> None:
        mock_ps = "codex-otel-collector\totel/opentelemetry-collector-contrib:0.107.0\tUp 2 hours"
        with (
            patch("subprocess.run") as mock_run,
        ):
            # First call: docker ps
            mock_run.return_value.stdout = mock_ps
            mock_run.return_value.returncode = 0
            stop_orphan_collectors()
            # Should have called docker stop
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("stop" in c and "codex-otel-collector" in c for c in calls)

    def test_noop_when_no_orphans(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            stop_orphan_collectors()
            # Only the ps call, no stop
            assert mock_run.call_count == 1


class TestStackUp:
    """Test stack_up validates GRAFANA_PASSWORD and starts compose."""

    def test_fails_without_grafana_password(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = stack_up()
            assert result != 0

    def test_succeeds_with_grafana_password(self) -> None:
        with (
            patch.dict("os.environ", {"GRAFANA_PASSWORD": "test123"}),
            patch("mde.domain.observability_stack.COMPOSE_FILE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.is_file.return_value = True
            mock_cf.__str__ = lambda _self: "/fake/docker-compose.yml"
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result = stack_up()
            assert result == 0


class TestComposeFile:
    """Test compose file path is correct."""

    def test_compose_file_path(self) -> None:
        assert COMPOSE_FILE.name == "docker-compose.yml"
        assert "docker/observability" in str(COMPOSE_FILE)
