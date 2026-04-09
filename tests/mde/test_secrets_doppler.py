"""Tests for secrets modules (Doppler, sync, validate)."""

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


class TestValidateSecretsParity:
    """Tests for validate_secrets_parity."""

    def test_returns_zero_when_keys_match(self) -> None:
        """Returns 0 when Doppler and fnox have the same keys."""
        fnox_output = (
            " KEY1   provider (doppler_dotfiles_dev_personal)  KEY1\n"
            " KEY2   provider (doppler_dotfiles_dev_personal)  KEY2\n"
        )
        with (
            patch("mde.secrets.validate_parity.is_doppler_available", return_value=True),
            patch("mde.secrets.validate_parity.doppler_list_secrets") as mock_list,
            patch("mde.secrets.validate_parity.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1", "KEY2": "val2"}
            mock_run.return_value = MagicMock(returncode=0, stdout=fnox_output)
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 0

    def test_returns_one_when_doppler_has_extra_keys(self) -> None:
        """Returns 1 when Doppler has keys not in fnox."""
        fnox_output = " KEY1   provider (doppler_dotfiles_dev_personal)  KEY1\n"
        with (
            patch("mde.secrets.validate_parity.is_doppler_available", return_value=True),
            patch("mde.secrets.validate_parity.doppler_list_secrets") as mock_list,
            patch("mde.secrets.validate_parity.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1", "KEY2": "val2"}
            mock_run.return_value = MagicMock(returncode=0, stdout=fnox_output)
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 1

    def test_returns_one_when_doppler_not_available(self) -> None:
        """Returns 1 if doppler is not installed."""
        with patch("mde.secrets.validate_parity.is_doppler_available", return_value=False):
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 1

    def test_returns_one_when_fnox_has_extra_keys(self) -> None:
        """Returns 1 when fnox has keys not in Doppler."""
        fnox_output = (
            " KEY1   provider (doppler_dotfiles_dev_personal)  KEY1\n"
            " KEY2   provider (doppler_dotfiles_dev_personal)  KEY2\n"
        )
        with (
            patch("mde.secrets.validate_parity.is_doppler_available", return_value=True),
            patch("mde.secrets.validate_parity.doppler_list_secrets") as mock_list,
            patch("mde.secrets.validate_parity.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1"}
            mock_run.return_value = MagicMock(returncode=0, stdout=fnox_output)
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 1

    def test_returns_one_when_fnox_list_fails(self) -> None:
        """Returns 1 if fnox list fails."""
        with (
            patch("mde.secrets.validate_parity.is_doppler_available", return_value=True),
            patch("mde.secrets.validate_parity.doppler_list_secrets") as mock_list,
            patch("mde.secrets.validate_parity.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {"KEY1": "val1"}
            mock_run.return_value = MagicMock(returncode=1, stderr="error")
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 1

    def test_ignores_doppler_meta_keys(self) -> None:
        """Doppler meta keys (DOPPLER_CONFIG etc.) are excluded from parity check."""
        fnox_output = " KEY1   provider (doppler_dotfiles_dev_personal)  KEY1\n"
        with (
            patch("mde.secrets.validate_parity.is_doppler_available", return_value=True),
            patch("mde.secrets.validate_parity.doppler_list_secrets") as mock_list,
            patch("mde.secrets.validate_parity.subprocess.run") as mock_run,
        ):
            mock_list.return_value = {
                "KEY1": "val1",
                "DOPPLER_CONFIG": "dev",
                "DOPPLER_ENVIRONMENT": "dev",
                "DOPPLER_PROJECT": "dotfiles",
            }
            mock_run.return_value = MagicMock(returncode=0, stdout=fnox_output)
            from mde.secrets.validate_parity import validate_secrets_parity

            result = validate_secrets_parity()
        assert result == 0


class TestSyncDopplerToFnox:
    """Tests for sync_doppler_to_fnox (single fnox sync --provider age call)."""

    def test_runs_fnox_sync_age_global_force(self) -> None:
        """Sync delegates to a single `fnox sync --provider age --global --force`."""
        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 0
        assert mock_run.call_count == 1
        assert mock_run.call_args.args[0] == [
            "fnox",
            "sync",
            "--provider",
            "age",
            "--global",
            "--force",
        ]

    def test_returns_one_when_doppler_not_available(self) -> None:
        """Returns 1 if doppler is not installed."""
        with patch("mde.secrets.sync.is_doppler_available", return_value=False):
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1

    def test_returns_one_on_fnox_failure(self) -> None:
        """Returns 1 if fnox sync exits non-zero."""
        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1

    def test_handles_fnox_timeout(self) -> None:
        """Returns 1 when fnox sync times out."""
        import subprocess as _subprocess

        with (
            patch("mde.secrets.sync.is_doppler_available", return_value=True),
            patch("mde.secrets.sync.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = _subprocess.TimeoutExpired(cmd="fnox", timeout=120)
            from mde.secrets.sync import sync_doppler_to_fnox

            result = sync_doppler_to_fnox()
        assert result == 1
