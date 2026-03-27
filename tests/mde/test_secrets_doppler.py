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


class TestExportFnoxToDoppler:
    """Tests for export_fnox_to_doppler."""

    def test_exports_keychain_secrets_to_doppler(self) -> None:
        """Exports only keychain-provider secrets to Doppler, skipping age entries."""
        mock_fnox_list = (
            " OPENAI_API_KEY   provider (keychain)  OPENAI_API_KEY\n"
            " GEMINI_API_KEY   provider (keychain)  GEMINI_API_KEY\n"
            " OP_TOKEN         provider (age)       OP_TOKEN\n"
        )
        with (
            patch("mde.secrets.export_to_doppler.subprocess.run") as mock_run,
            patch("mde.secrets.export_to_doppler.doppler_set_secrets") as mock_set,
            patch("mde.secrets.export_to_doppler.is_doppler_available", return_value=True),
        ):
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=mock_fnox_list),  # fnox list
                MagicMock(returncode=0, stdout="sk-abc123\n"),  # fnox get OPENAI
                MagicMock(returncode=0, stdout="key-xyz789\n"),  # fnox get GEMINI
            ]
            mock_set.return_value = 0
            from mde.secrets.export_to_doppler import export_fnox_to_doppler

            result = export_fnox_to_doppler()
        assert result == 0
        mock_set.assert_called_once()
        secrets_arg = mock_set.call_args[0][0]
        assert "OPENAI_API_KEY" in secrets_arg
        assert "GEMINI_API_KEY" in secrets_arg
        assert "OP_TOKEN" not in secrets_arg  # age provider should be excluded

    def test_returns_one_when_fnox_list_fails(self) -> None:
        """Returns exit code 1 when fnox list fails."""
        with (
            patch("mde.secrets.export_to_doppler.subprocess.run") as mock_run,
            patch("mde.secrets.export_to_doppler.doppler_set_secrets"),
            patch("mde.secrets.export_to_doppler.is_doppler_available", return_value=True),
        ):
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="fnox: command failed"
            )
            from mde.secrets.export_to_doppler import export_fnox_to_doppler

            result = export_fnox_to_doppler()
        assert result == 1

    def test_partial_fnox_get_failure_still_exports_successes(self) -> None:
        """Exports successfully retrieved secrets even when some fnox get calls fail."""
        mock_fnox_list = (
            " OPENAI_API_KEY   provider (keychain)  OPENAI_API_KEY\n"
            " GEMINI_API_KEY   provider (keychain)  GEMINI_API_KEY\n"
        )
        with (
            patch("mde.secrets.export_to_doppler.subprocess.run") as mock_run,
            patch("mde.secrets.export_to_doppler.doppler_set_secrets") as mock_set,
            patch("mde.secrets.export_to_doppler.is_doppler_available", return_value=True),
        ):
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=mock_fnox_list),  # fnox list
                MagicMock(
                    returncode=1, stdout="", stderr="keychain error"
                ),  # fnox get OPENAI fails
                MagicMock(returncode=0, stdout="key-xyz789\n"),  # fnox get GEMINI succeeds
            ]
            mock_set.return_value = 0
            from mde.secrets.export_to_doppler import export_fnox_to_doppler

            result = export_fnox_to_doppler()
        assert result == 0
        mock_set.assert_called_once()
        secrets_arg = mock_set.call_args[0][0]
        assert "OPENAI_API_KEY" not in secrets_arg  # failed get should be excluded
        assert "GEMINI_API_KEY" in secrets_arg  # successful get should be included

    def test_returns_one_when_doppler_not_available(self) -> None:
        """Returns exit code 1 immediately when doppler is not installed."""
        with (
            patch("mde.secrets.export_to_doppler.is_doppler_available", return_value=False),
            patch("mde.secrets.export_to_doppler.subprocess.run") as mock_run,
        ):
            from mde.secrets.export_to_doppler import export_fnox_to_doppler

            result = export_fnox_to_doppler()
        assert result == 1
        mock_run.assert_not_called()  # fnox list must not be called when doppler unavailable


class TestSyncDopplerToFnox:
    """Tests for sync_doppler_to_fnox."""

    def test_syncs_all_secrets_to_fnox(self) -> None:
        """Sync downloads from Doppler and sets each in fnox."""
        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.doppler_list_secrets") as mock_list,
            patch("mde.secrets.sync.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1", "KEY2": "val2"}
            mock_run.return_value = MagicMock(returncode=0)
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 0
        assert mock_run.call_count == 2
        # Verify fnox set commands
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ["fnox", "set", "KEY1", "val1", "--provider", "keychain", "--global"] in calls
        assert ["fnox", "set", "KEY2", "val2", "--provider", "keychain", "--global"] in calls

    def test_returns_one_when_doppler_not_available(self) -> None:
        """Returns 1 if doppler is not installed."""
        with patch("mde.secrets.sync.is_doppler_available", return_value=False):
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1

    def test_returns_one_when_no_secrets(self) -> None:
        """Returns 1 if Doppler returns empty."""
        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.doppler_list_secrets", return_value={}),
        ):
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1

    def test_returns_one_on_partial_failure(self) -> None:
        """Returns 1 if some fnox set calls fail."""
        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.doppler_list_secrets") as mock_list,
            patch("mde.secrets.sync.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1", "KEY2": "val2"}
            mock_run.side_effect = [
                MagicMock(returncode=0),  # KEY1 succeeds
                MagicMock(returncode=1, stderr="error"),  # KEY2 fails
            ]
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1
