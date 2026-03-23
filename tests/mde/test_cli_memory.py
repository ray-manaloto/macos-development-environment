"""Tests for memory CLI subcommand wiring."""

from __future__ import annotations

from unittest.mock import patch

from mde.cli import run


class TestMemoryCLI:
    """Test memory subcommand is wired in CLI."""

    def test_memory_up_dispatches(self) -> None:
        with patch("mde.domain.memory_stack.dispatch", return_value=0) as mock_dispatch:
            result = run(["memory", "up"])
            assert result == 0
            mock_dispatch.assert_called_once()
            args = mock_dispatch.call_args[0][0]
            assert args.memory_action == "up"

    def test_memory_down_dispatches(self) -> None:
        with patch("mde.domain.memory_stack.dispatch", return_value=0) as mock_dispatch:
            result = run(["memory", "down"])
            assert result == 0
            mock_dispatch.assert_called_once()
            args = mock_dispatch.call_args[0][0]
            assert args.memory_action == "down"

    def test_memory_no_action_shows_usage(self) -> None:
        with patch("mde.domain.memory_stack.dispatch", return_value=1):
            result = run(["memory"])
            assert result == 1
