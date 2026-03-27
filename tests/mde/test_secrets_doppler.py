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
        with patch("mde.secrets.doppler.shutil.which", return_value="/usr/local/bin/doppler"):
            assert is_doppler_available() is True

    def test_returns_false_when_not_installed(self) -> None:
        """Returns False when doppler binary is not on PATH."""
        with patch("mde.secrets.doppler.shutil.which", return_value=None):
            assert is_doppler_available() is False


class TestDopplerListSecrets:
    """Tests for doppler_list_secrets."""

    def test_parses_json_output(self) -> None:
        """Parses JSON output from doppler secrets download."""
        mock_output = '{"API_KEY": "secret123", "DB_PASS": "pass456"}'
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            result = doppler_list_secrets(project="dotfiles", config="dev")
        assert result == {"API_KEY": "secret123", "DB_PASS": "pass456"}

    def test_list_secrets_returns_empty_on_failure(self) -> None:
        """Returns empty dict when doppler exits with non-zero returncode."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = doppler_list_secrets(project="dotfiles", config="dev")
        assert result == {}

    def test_list_secrets_returns_empty_on_malformed_json(self) -> None:
        """Returns empty dict when doppler output is not valid JSON."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="not json", stderr="")
            result = doppler_list_secrets(project="dotfiles", config="dev")
        assert result == {}


class TestDopplerGetSecret:
    """Tests for doppler_get_secret."""

    def test_returns_stripped_value(self) -> None:
        """Returns stripped string value from doppler secrets get."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="secret123\n")
            result = doppler_get_secret("API_KEY", project="dotfiles", config="dev")
        assert result == "secret123"

    def test_get_secret_returns_none_on_failure(self) -> None:
        """Returns None when doppler exits with non-zero returncode."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not found")
            result = doppler_get_secret("MISSING_KEY", project="dotfiles", config="dev")
        assert result is None


class TestDopplerSetSecrets:
    """Tests for doppler_set_secrets."""

    def test_calls_doppler_secrets_set(self) -> None:
        """Calls doppler secrets set with correct arguments including KEY=VALUE pairs."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
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
        assert "KEY1=val1" in args
        assert "KEY2=val2" in args

    def test_set_secrets_returns_nonzero_on_failure(self) -> None:
        """Returns non-zero exit code when doppler exits with failure."""
        with patch("mde.secrets.doppler.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="error")
            result = doppler_set_secrets(
                {"KEY1": "val1"},
                project="dotfiles",
                config="dev",
            )
        assert result == 1
