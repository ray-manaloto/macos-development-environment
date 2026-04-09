"""Tests for mde.secrets.manage (CRUD + bootstrap + doctor)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from mde.secrets import manage

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _tty_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)


def _non_tty_stdin(monkeypatch: pytest.MonkeyPatch, data: str) -> None:
    fake = io.StringIO(data)
    fake.isatty = lambda: False  # type: ignore[method-assign]
    monkeypatch.setattr("sys.stdin", fake)


class TestAddSecret:
    """Tests for manage.add_secret upsert behavior."""

    def test_writes_doppler_then_runs_fnox_sync_then_emits_export(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0) as sync_m,
        ):
            rc = manage.add_secret("GITHUB_TOKEN", "ghp_xyz")
        assert rc == 0
        set_m.assert_called_once()
        sync_m.assert_called_once_with(verify_key="GITHUB_TOKEN", verify_value="ghp_xyz")
        captured = capsys.readouterr()
        assert captured.out.strip() == "export GITHUB_TOKEN='ghp_xyz'"

    def test_doppler_failure_aborts_before_fnox_sync(self) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=1),
            patch("mde.secrets.manage._run_fnox_sync_age") as sync_m,
        ):
            rc = manage.add_secret("API_KEY", "v")
        assert rc == 1
        sync_m.assert_not_called()

    def test_fnox_sync_failure_returns_partial(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0),
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=2),
        ):
            rc = manage.add_secret("API_KEY", "v")
        assert rc == 2
        assert "export API_KEY" not in capsys.readouterr().out

    def test_update_is_alias_for_add(self) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0),
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            assert manage.update_secret("KEY", "v") == 0

    def test_value_from_stdin_when_no_arg_and_stdin_not_tty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _non_tty_stdin(monkeypatch, "stdin_val\n")
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY")
        assert set_m.call_args.args[0] == {"KEY": "stdin_val"}

    def test_value_from_flag_overrides_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _non_tty_stdin(monkeypatch, "from_stdin")
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY", "explicit")
        assert set_m.call_args.args[0] == {"KEY": "explicit"}

    def test_value_from_env_var_when_stdin_tty_and_no_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _tty_stdin(monkeypatch)
        monkeypatch.setenv("MDE_SECRET_VALUE", "from_env")
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY")
        assert set_m.call_args.args[0] == {"KEY": "from_env"}

    def test_value_from_getpass_when_all_else_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _tty_stdin(monkeypatch)
        monkeypatch.delenv("MDE_SECRET_VALUE", raising=False)
        with (
            patch("getpass.getpass", return_value="typed"),
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY")
        assert set_m.call_args.args[0] == {"KEY": "typed"}

    def test_empty_string_value_allowed_via_explicit_flag(self) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY", "")
        assert set_m.call_args.args[0] == {"KEY": ""}

    def test_quote_escaping_in_export_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0),
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY", 'it\'s "fine"')
        out = capsys.readouterr().out.strip()
        assert out == "export KEY='it'\\''s \"fine\"'"

    def test_invalid_key_name_rejected(self) -> None:
        for bad in ("lower", "9LEAD", "BAD-NAME", ""):
            assert manage.add_secret(bad, "v") == 3

    def test_default_config_is_dev_personal(self) -> None:
        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0) as set_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            manage.add_secret("KEY", "v")
        assert set_m.call_args.kwargs["config"] == "dev_personal"
        assert set_m.call_args.kwargs["project"] == "dotfiles"

    def test_post_sync_verification_catches_drift(self) -> None:
        # Simulate fnox sync returning 0, but fnox get returning a different value.
        def fake_run(cmd: list[str], *_a: object, **_kw: object) -> MagicMock:
            if cmd[:2] == ["fnox", "sync"]:
                return MagicMock(returncode=0, stdout="", stderr="")
            if cmd[:2] == ["fnox", "get"]:
                return MagicMock(returncode=0, stdout="wrong\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("mde.secrets.manage.doppler_set_secrets", return_value=0),
            patch("mde.secrets.manage.subprocess.run", side_effect=fake_run),
        ):
            rc = manage.add_secret("KEY", "expected")
        assert rc == 2


class TestFnoxSyncRetry:
    """Tests for manage._run_fnox_sync_age retry + verification logic."""

    def test_retries_once_on_transient_failure(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], *_a: object, **_kw: object) -> MagicMock:
            calls.append(cmd)
            if cmd[:2] == ["fnox", "sync"]:
                if len([c for c in calls if c[:2] == ["fnox", "sync"]]) == 1:
                    return MagicMock(returncode=1, stdout="", stderr="transient")
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("mde.secrets.manage.subprocess.run", side_effect=fake_run),
            patch("mde.secrets.manage.time.sleep"),
        ):
            rc = manage._run_fnox_sync_age()
        assert rc == 0
        assert len([c for c in calls if c[:2] == ["fnox", "sync"]]) == 2

    def test_fails_after_two_attempts(self) -> None:
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=1, stdout="", stderr="boom"),
            ),
            patch("mde.secrets.manage.time.sleep"),
        ):
            assert manage._run_fnox_sync_age() == 2


class TestRemoveSecret:
    """Tests for manage.remove_secret."""

    def test_deletes_from_doppler_then_runs_fnox_sync_then_emits_unset(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            patch("mde.secrets.manage.doppler_delete_secret", return_value=0) as del_m,
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0) as sync_m,
        ):
            rc = manage.remove_secret("OLD_KEY")
        assert rc == 0
        del_m.assert_called_once()
        sync_m.assert_called_once()
        assert capsys.readouterr().out.strip() == "unset OLD_KEY"

    def test_idempotent_when_key_missing_from_doppler(self) -> None:
        # doppler_delete_secret returns 0 for "not found" per its own logic;
        # manage.remove_secret should still succeed.
        with (
            patch("mde.secrets.manage.doppler_delete_secret", return_value=0),
            patch("mde.secrets.manage._run_fnox_sync_age", return_value=0),
        ):
            assert manage.remove_secret("MISSING") == 0

    def test_doppler_failure_aborts(self) -> None:
        with (
            patch("mde.secrets.manage.doppler_delete_secret", return_value=1),
            patch("mde.secrets.manage._run_fnox_sync_age") as sync_m,
        ):
            assert manage.remove_secret("KEY") == 1
        sync_m.assert_not_called()

    def test_invalid_key_rejected(self) -> None:
        assert manage.remove_secret("bad-name") == 3


class TestBootstrapConfig:
    """Tests for manage.bootstrap_config."""

    def test_creates_providers_and_declarations(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        age_file = tmp_path / "mise" / "age.txt"
        age_file.parent.mkdir()
        age_file.write_text("AGE-SECRET-KEY-FAKE\n")
        config_file = tmp_path / "fnox" / "config.toml"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1recipient\n", stderr=""),
            ),
            patch(
                "mde.secrets.manage.doppler_list_secrets",
                return_value={"GITHUB_TOKEN": "val", "AWS_ACCESS_KEY_ID": "val"},
            ),
        ):
            rc = manage.bootstrap_config()
        assert rc == 0
        content = config_file.read_text()
        assert "[providers.age]" in content
        assert "age1recipient" in content
        assert "[providers.doppler_dotfiles_dev_personal]" in content
        assert 'DOPPLER_TOKEN = { provider = "keychain", value = "DOPPLER_TOKEN" }' in content
        assert "GITHUB_TOKEN" in content
        assert "AWS_ACCESS_KEY_ID" in content

    def test_is_idempotent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1xxx\n", stderr=""),
            ),
            patch(
                "mde.secrets.manage.doppler_list_secrets",
                return_value={"KEY_A": "v", "KEY_B": "v"},
            ),
        ):
            manage.bootstrap_config()
            first = config_file.read_text()
            manage.bootstrap_config()
            second = config_file.read_text()
        assert first == second

    def test_fails_closed_on_empty_doppler_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression test for codex H2: empty/failed Doppler list must not truncate config."""
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1xxx\n", stderr=""),
            ),
            patch("mde.secrets.manage.doppler_list_secrets", return_value={}),
        ):
            rc = manage.bootstrap_config()
        assert rc == 1
        assert not config_file.exists()


class TestDoctor:
    """Tests for manage.doctor health checks."""

    def test_reports_missing_age_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing = tmp_path / "absent.txt"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", missing)
        with patch(
            "mde.secrets.manage.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        ):
            assert manage.doctor() == 1
