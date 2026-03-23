"""Tests for docker CLI subcommand wiring."""

from __future__ import annotations

from unittest.mock import patch

from mde.cli import run


class TestDockerCLI:
    """Test docker subcommand is wired in CLI."""

    def test_docker_up_dispatches(self) -> None:
        with patch("mde.domain.docker_aggregate.dispatch", return_value=0) as mock_dispatch:
            result = run(["docker", "up"])
            assert result == 0
            mock_dispatch.assert_called_once()
            args = mock_dispatch.call_args[0][0]
            assert args.docker_action == "up"

    def test_docker_down_dispatches(self) -> None:
        with patch("mde.domain.docker_aggregate.dispatch", return_value=0) as mock_dispatch:
            result = run(["docker", "down"])
            assert result == 0
            mock_dispatch.assert_called_once()
            args = mock_dispatch.call_args[0][0]
            assert args.docker_action == "down"

    def test_docker_no_action_shows_usage(self) -> None:
        with patch("mde.domain.docker_aggregate.dispatch", return_value=1):
            result = run(["docker"])
            assert result == 1
