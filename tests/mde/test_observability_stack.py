"""Tests for observability stack lifecycle management."""

from __future__ import annotations

import argparse
import subprocess
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, Mock, patch

if TYPE_CHECKING:
    import pytest

from mde.domain.observability_stack import (
    COMPOSE_FILE,
    dispatch,
    stack_down,
    stack_status,
    stack_up,
    stack_verify,
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
            assert mock_run.call_count == 1

    def test_timeout_stopping_orphan_does_not_propagate(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """TimeoutExpired on docker stop should be caught, not propagated."""
        mock_ps = "codex-otel-collector\totel/opentelemetry-collector-contrib:0.107.0\tUp 2 hours"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_ps
            mock_run.return_value.returncode = 0
            # Second call (docker stop) raises TimeoutExpired
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=mock_ps),
                subprocess.TimeoutExpired(cmd=["docker", "stop"], timeout=30),
            ]
            # Should NOT raise
            stop_orphan_collectors()
            captured = capsys.readouterr()
            assert "WARNING" in captured.err
            assert "codex-otel-collector" in captured.err


class TestStackUp:
    """Test stack_up validates GRAFANA_PASSWORD and starts compose."""

    def test_fails_without_grafana_password(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = stack_up()
            assert result != 0

    def test_succeeds_with_password(self) -> None:
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

    def test_fails_when_compose_missing(self) -> None:
        with (
            patch.dict("os.environ", {"GRAFANA_PASSWORD": "test123"}),
            patch("mde.domain.observability_stack.COMPOSE_FILE") as mock_cf,
        ):
            mock_cf.is_file.return_value = False
            result = stack_up()
            assert result != 0

    def test_timeout_returns_nonzero(self) -> None:
        with (
            patch.dict("os.environ", {"GRAFANA_PASSWORD": "test123"}),
            patch("mde.domain.observability_stack.COMPOSE_FILE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.is_file.return_value = True
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"  # type: ignore[assignment]
            # First call is stop_orphan_collectors (succeeds), second is compose up (timeout)
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=""),  # docker ps for orphan check
                subprocess.TimeoutExpired(cmd=[], timeout=120),  # compose up
            ]
            result = stack_up()
            assert result == 1


class TestStackDown:
    """Test stack_down calls docker compose down."""

    def test_calls_compose_down(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_down()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert "down" in call_args

    def test_timeout_returns_nonzero(self) -> None:
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=[], timeout=60),
        ):
            result = stack_down()
            assert result == 1


class TestStackStatus:
    """Test stack_status calls docker compose ps."""

    def test_calls_compose_ps(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = stack_status()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert "ps" in call_args

    def test_timeout_returns_nonzero(self) -> None:
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=[], timeout=10),
        ):
            result = stack_status()
            assert result == 1


class TestStackVerify:
    """Test stack_verify checks service health."""

    def test_all_healthy(self) -> None:
        with (
            patch("mde.domain.observability_stack.urllib.request.urlopen"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result = stack_verify()
            assert result == 0

    def test_collector_unhealthy(self) -> None:
        """When collector health check fails, result is nonzero."""
        import urllib.error

        with (
            patch(
                "mde.domain.observability_stack.urllib.request.urlopen",
                side_effect=urllib.error.URLError("connection refused"),
            ),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            result = stack_verify()
            assert result == 1

    def test_one_unhealthy(self) -> None:
        def side_effect(cmd: list[str], **_: Any) -> MagicMock:
            m = MagicMock()
            if "grafana" in cmd:
                m.returncode = 1
            else:
                m.returncode = 0
            return m

        with (
            patch("mde.domain.observability_stack.urllib.request.urlopen"),
            patch("subprocess.run", side_effect=side_effect),
        ):
            result = stack_verify()
            assert result == 1

    def test_unhealthy_includes_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """When a health check fails, stderr from the check should be printed."""
        with (
            patch("mde.domain.observability_stack.urllib.request.urlopen"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "connection refused"
            mock_run.return_value.stdout = ""
            stack_verify()
            captured = capsys.readouterr()
            assert "connection refused" in captured.err

    def test_timeout(self) -> None:
        with (
            patch("mde.domain.observability_stack.urllib.request.urlopen"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=15)
            result = stack_verify()
            assert result == 1


class TestDispatch:
    """Test dispatch routes to correct handler."""

    def test_dispatch_up(self) -> None:
        args = argparse.Namespace(observability_action="up")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"up": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_down(self) -> None:
        args = argparse.Namespace(observability_action="down")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"down": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_status(self) -> None:
        args = argparse.Namespace(observability_action="status")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"status": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_verify(self) -> None:
        args = argparse.Namespace(observability_action="verify")
        with patch("mde.domain.observability_stack._ACTION_TABLE", {"verify": lambda: 0}):
            assert dispatch(args) == 0

    def test_unknown_returns_1(self) -> None:
        args = argparse.Namespace(observability_action=None)
        result = dispatch(args)
        assert result == 1

    def test_docker_not_found(self) -> None:
        args = argparse.Namespace(observability_action="up")
        with patch(
            "mde.domain.observability_stack._ACTION_TABLE",
            {"up": Mock(side_effect=FileNotFoundError)},
        ):
            assert dispatch(args) == 1


class TestComposeFile:
    """Test compose file path is correct."""

    def test_compose_file_path(self) -> None:
        assert COMPOSE_FILE.name == "compose.yaml"
        assert "docker/observability" in str(COMPOSE_FILE)
