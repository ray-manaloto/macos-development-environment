"""Tests for aggregate Docker stack lifecycle management."""

from __future__ import annotations

import argparse
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

if TYPE_CHECKING:
    import pytest

from mde.domain.docker_aggregate import (
    dispatch,
    stack_down,
    stack_status,
    stack_up,
    stack_verify,
)


class TestStackUp:
    """Test stack_up delegates to both sub-stacks."""

    def test_succeeds_when_both_pass(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=0),
            patch("mde.domain.memory_stack.stack_up", return_value=0),
        ):
            assert stack_up() == 0

    def test_fails_when_memory_fails(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=0),
            patch("mde.domain.memory_stack.stack_up", return_value=1),
        ):
            assert stack_up() == 1

    def test_fails_when_observability_fails(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=1),
            patch("mde.domain.memory_stack.stack_up", return_value=0),
        ):
            assert stack_up() == 1

    def test_fails_when_both_fail(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=1),
            patch("mde.domain.memory_stack.stack_up", return_value=1),
        ):
            result = stack_up()
            assert result == 1

    def test_both_fail_message_includes_both_names(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=1),
            patch("mde.domain.memory_stack.stack_up", return_value=1),
        ):
            stack_up()
            captured = capsys.readouterr()
            assert "observability" in captured.err
            assert "memory" in captured.err
            assert "Failed:" in captured.err

    def test_timeout_on_observability_returns_nonzero(self) -> None:
        with (
            patch(
                "mde.domain.observability_stack.stack_up",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=120),
            ),
            patch("mde.domain.memory_stack.stack_up", return_value=0),
        ):
            assert stack_up() == 1

    def test_timeout_on_memory_returns_nonzero(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_up", return_value=0),
            patch(
                "mde.domain.memory_stack.stack_up",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=120),
            ),
        ):
            assert stack_up() == 1


class TestStackDown:
    """Test stack_down delegates to both sub-stacks."""

    def test_succeeds_when_both_pass(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_down", return_value=0),
            patch("mde.domain.observability_stack.stack_down", return_value=0),
        ):
            assert stack_down() == 0

    def test_fails_when_memory_fails(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_down", return_value=1),
            patch("mde.domain.observability_stack.stack_down", return_value=0),
        ):
            assert stack_down() == 1

    def test_fails_when_observability_fails(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_down", return_value=0),
            patch("mde.domain.observability_stack.stack_down", return_value=1),
        ):
            assert stack_down() == 1

    def test_fails_when_both_fail(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_down", return_value=1),
            patch("mde.domain.observability_stack.stack_down", return_value=1),
        ):
            assert stack_down() == 1

    def test_timeout_on_memory_returns_nonzero(self) -> None:
        with (
            patch(
                "mde.domain.memory_stack.stack_down",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=60),
            ),
            patch("mde.domain.observability_stack.stack_down", return_value=0),
        ):
            assert stack_down() == 1

    def test_timeout_on_observability_returns_nonzero(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_down", return_value=0),
            patch(
                "mde.domain.observability_stack.stack_down",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=60),
            ),
        ):
            assert stack_down() == 1


class TestStackStatus:
    """Test stack_status delegates to both sub-stacks."""

    def test_succeeds_when_both_pass(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_status", return_value=0),
            patch("mde.domain.observability_stack.stack_status", return_value=0),
        ):
            assert stack_status() == 0

    def test_fails_when_memory_fails(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_status", return_value=1),
            patch("mde.domain.observability_stack.stack_status", return_value=0),
        ):
            assert stack_status() == 1

    def test_fails_when_observability_fails(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_status", return_value=0),
            patch("mde.domain.observability_stack.stack_status", return_value=1),
        ):
            assert stack_status() == 1

    def test_fails_when_both_fail(self) -> None:
        with (
            patch("mde.domain.memory_stack.stack_status", return_value=1),
            patch("mde.domain.observability_stack.stack_status", return_value=1),
        ):
            assert stack_status() == 1

    def test_timeout_on_memory_returns_nonzero(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_status", return_value=0),
            patch(
                "mde.domain.memory_stack.stack_status",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=10),
            ),
        ):
            assert stack_status() == 1

    def test_timeout_on_observability_returns_nonzero(self) -> None:
        with (
            patch(
                "mde.domain.observability_stack.stack_status",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=10),
            ),
            patch("mde.domain.memory_stack.stack_status", return_value=0),
        ):
            assert stack_status() == 1


class TestStackVerify:
    """Test stack_verify aggregates sub-stack verification."""

    def test_verify_all_healthy(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_verify", return_value=0),
            patch("mde.domain.memory_stack.stack_verify", return_value=0),
        ):
            assert stack_verify() == 0

    def test_verify_memory_unhealthy_only(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_verify", return_value=0),
            patch("mde.domain.memory_stack.stack_verify", return_value=1),
        ):
            assert stack_verify() == 1

    def test_verify_observability_unhealthy_only(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_verify", return_value=1),
            patch("mde.domain.memory_stack.stack_verify", return_value=0),
        ):
            assert stack_verify() == 1

    def test_verify_both_unhealthy(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_verify", return_value=1),
            patch("mde.domain.memory_stack.stack_verify", return_value=1),
        ):
            assert stack_verify() == 1

    def test_timeout_on_memory_returns_nonzero(self) -> None:
        with (
            patch("mde.domain.observability_stack.stack_verify", return_value=0),
            patch(
                "mde.domain.memory_stack.stack_verify",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=15),
            ),
        ):
            assert stack_verify() == 1

    def test_timeout_on_observability_returns_nonzero(self) -> None:
        with (
            patch(
                "mde.domain.observability_stack.stack_verify",
                side_effect=subprocess.TimeoutExpired(cmd=[], timeout=15),
            ),
            patch("mde.domain.memory_stack.stack_verify", return_value=0),
        ):
            assert stack_verify() == 1


class TestDispatch:
    """Test dispatch routes to correct handler."""

    def test_dispatch_up(self) -> None:
        args = argparse.Namespace(docker_action="up")
        with patch("mde.domain.docker_aggregate._ACTION_TABLE", {"up": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_down(self) -> None:
        args = argparse.Namespace(docker_action="down")
        with patch("mde.domain.docker_aggregate._ACTION_TABLE", {"down": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_status(self) -> None:
        args = argparse.Namespace(docker_action="status")
        with patch("mde.domain.docker_aggregate._ACTION_TABLE", {"status": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_verify(self) -> None:
        args = argparse.Namespace(docker_action="verify")
        with patch("mde.domain.docker_aggregate._ACTION_TABLE", {"verify": lambda: 0}):
            assert dispatch(args) == 0

    def test_dispatch_unknown_returns_1(self) -> None:
        args = argparse.Namespace(docker_action=None)
        assert dispatch(args) == 1

    def test_dispatch_docker_not_found(self) -> None:
        args = argparse.Namespace(docker_action="up")
        with patch(
            "mde.domain.docker_aggregate._ACTION_TABLE",
            {"up": Mock(side_effect=FileNotFoundError)},
        ):
            assert dispatch(args) == 1
