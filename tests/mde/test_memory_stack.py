"""Tests for memory stack lifecycle management."""

from __future__ import annotations

import argparse
import subprocess
from unittest.mock import patch

from mde.domain.memory_stack import (
    dispatch,
    stack_down,
    stack_status,
    stack_up,
    stack_verify,
)


class TestStackUp:
    """Test stack_up validates HONCHO_DB_PASSWORD and starts compose."""

    def test_fails_without_db_password(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            result = stack_up()
            assert result != 0

    def test_succeeds_with_db_password(self) -> None:
        with (
            patch.dict("os.environ", {"HONCHO_DB_PASSWORD": "test123"}),
            patch("mde.domain.memory_stack.COMPOSE_FILE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.is_file.return_value = True
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"  # type: ignore[assignment]
            mock_run.return_value.returncode = 0
            result = stack_up()
            assert result == 0

    def test_fails_when_compose_file_missing(self) -> None:
        with (
            patch.dict("os.environ", {"HONCHO_DB_PASSWORD": "test123"}),
            patch("mde.domain.memory_stack.COMPOSE_FILE") as mock_cf,
        ):
            mock_cf.is_file.return_value = False
            result = stack_up()
            assert result != 0


class TestStackDown:
    """Test stack_down calls docker compose down."""

    def test_calls_docker_compose_down(self) -> None:
        with (
            patch("mde.domain.memory_stack.COMPOSE_FILE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"  # type: ignore[assignment]
            mock_run.return_value.returncode = 0
            result = stack_down()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert call_args == ["docker", "compose", "-f", "/fake/compose.yaml", "down"]


class TestStackStatus:
    """Test stack_status calls docker compose ps."""

    def test_calls_docker_compose_ps(self) -> None:
        with (
            patch("mde.domain.memory_stack.COMPOSE_FILE") as mock_cf,
            patch("subprocess.run") as mock_run,
        ):
            mock_cf.__str__ = lambda _self: "/fake/compose.yaml"  # type: ignore[assignment]
            mock_run.return_value.returncode = 0
            result = stack_status()
            assert result == 0
            call_args = mock_run.call_args[0][0]
            assert call_args == [
                "docker",
                "compose",
                "-f",
                "/fake/compose.yaml",
                "ps",
                "--format",
                "table",
            ]


class TestStackVerify:
    """Test stack_verify checks service health."""

    def test_verify_all_healthy(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "healthy"
            result = stack_verify()
            assert result == 0

    def test_verify_reports_unhealthy(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            result = stack_verify()
            assert result != 0

    def test_verify_timeout_returns_nonzero(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=15)
            result = stack_verify()
            assert result != 0


class TestDispatch:
    """Test dispatch routes to correct handler."""

    def test_dispatch_up(self) -> None:
        args = argparse.Namespace(memory_action="up")
        with patch("mde.domain.memory_stack._ACTION_TABLE", {"up": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_down(self) -> None:
        args = argparse.Namespace(memory_action="down")
        with patch("mde.domain.memory_stack._ACTION_TABLE", {"down": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_status(self) -> None:
        args = argparse.Namespace(memory_action="status")
        with patch("mde.domain.memory_stack._ACTION_TABLE", {"status": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_verify(self) -> None:
        args = argparse.Namespace(memory_action="verify")
        with patch("mde.domain.memory_stack._ACTION_TABLE", {"verify": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_unknown_returns_1(self) -> None:
        args = argparse.Namespace(memory_action=None)
        result = dispatch(args)
        assert result == 1
