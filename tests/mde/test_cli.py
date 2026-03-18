"""Tests for the CLI dispatcher."""

from __future__ import annotations

from mde.cli import run


class TestCli:
    """Tests for CLI argument parsing and dispatch."""

    def test_no_args_returns_zero(self) -> None:
        """No arguments should print help and return 0."""
        assert run([]) == 0

    def test_unknown_command_fails(self) -> None:
        """Unknown commands should cause argparse to exit."""
        import pytest

        with pytest.raises(SystemExit):
            run(["nonexistent"])
