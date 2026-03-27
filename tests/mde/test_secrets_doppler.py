"""Tests for Doppler CLI wrapper module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mde.secrets.doppler import (
    doppler_get_secret,
    doppler_list_secrets,
    doppler_set_secrets,
    is_doppler_available,
)


class TestIsDopplerAvailable:
    """Tests for is_doppler_available."""

    def test_returns_true_when_installed(self) -> None:
        """Returns True when doppler binary is on PATH."""
        with patch("shutil.which", return_value="/usr/local/bin/doppler"):
            assert is_doppler_available() is True

    def test_returns_false_when_not_installed(self) -> None:
        """Returns False when doppler binary is not on PATH."""
        with patch("shutil.which", return_value=None):
            assert is_doppler_available() is False


class TestDopplerListSecrets:
    """Tests for doppler_list_secrets."""

    def test_parses_json_output(self) -> None:
        """Parses JSON output from doppler secrets download."""
        mock_output = '{"API_KEY": "secret123", "DB_PASS": "pass456"}'
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            result = doppler_list_secrets(project="dotfiles", config="dev")
        assert result == {"API_KEY": "secret123", "DB_PASS": "pass456"}


class TestDopplerGetSecret:
    """Tests for doppler_get_secret."""

    def test_returns_stripped_value(self) -> None:
        """Returns stripped string value from doppler secrets get."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="secret123\n")
            result = doppler_get_secret("API_KEY", project="dotfiles", config="dev")
        assert result == "secret123"


class TestDopplerSetSecrets:
    """Tests for doppler_set_secrets."""

    def test_calls_doppler_secrets_set(self) -> None:
        """Calls doppler secrets set with correct arguments."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            doppler_set_secrets(
                {"KEY1": "val1", "KEY2": "val2"},
                project="dotfiles",
                config="dev",
            )
        args = mock_run.call_args[0][0]
        assert "doppler" in args
        assert "secrets" in args
        assert "set" in args
