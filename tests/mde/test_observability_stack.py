"""Tests for observability stack management."""

from __future__ import annotations

import argparse
from unittest.mock import patch

from mde.domain.observability_stack import (
    COMPOSE_FILE,
    dispatch,
    stack_down,
    stack_status,
    stack_up,
    stop_orphan_collectors,
)


class TestStopOrphanCollectors:
    """Test legacy codex-otel-collector detection and removal."""

    def test_stops_codex_collector(self) -> None:
        mock_ps = "codex-otel-collector\totel/opentelemetry-collector-contrib:0.107.0\tUp 2 hours"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_ps
            mock_run.return_value.returncode = 0
            stop_orphan_collectors()
            assert mock_run.call_count == 2
            stop_call = mock_run.call_args_list[1]
            assert stop_call.args[0] == ["docker", "stop", "codex-otel-collector"]

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
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"  # type: ignore[assignment]
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result = stack_up()
            assert result == 0


class TestStackDown:
    """Test stack_down calls docker compose down."""

    def test_calls_docker_compose_down(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_down()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert "down" in call_args


class TestStackStatus:
    """Test stack_status calls docker compose ps."""

    def test_calls_docker_compose_ps(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_status()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert "ps" in call_args


class TestDispatch:
    """Test dispatch routes to correct handler."""

    def test_dispatch_up(self) -> None:
        args = argparse.Namespace(observability_action="up")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"up": lambda: 0}):
            result = dispatch(args)
            assert result == 0

    def test_dispatch_down(self) -> None:
        args = argparse.Namespace(observability_action="down")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"down": lambda: 0}):
            result = dispatch(args)
            assert result == 0

    def test_dispatch_status(self) -> None:
        args = argparse.Namespace(observability_action="status")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"status": lambda: 0}):
            result = dispatch(args)
            assert result == 0

    def test_dispatch_unknown_returns_1(self) -> None:
        args = argparse.Namespace(observability_action=None)
        result = dispatch(args)
        assert result == 1


class TestComposeFile:
    """Test compose file path is correct."""

    def test_compose_file_path(self) -> None:
        assert COMPOSE_FILE.name == "compose.yaml"
        assert "docker/observability" in str(COMPOSE_FILE)
