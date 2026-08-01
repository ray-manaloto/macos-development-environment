"""Tests for mde.secrets.manage (CRUD + bootstrap + doctor)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from mde.secrets import manage

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _never_touch_the_real_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the real ``~/.config/fnox/config.toml`` for EVERY test here.

    Without this, tests that exercise ``add_secret``/``remove_secret`` reach the
    user's live config: those call ``bootstrap_config()`` for real, and only
    ``doppler_set_secrets`` and ``_run_fnox_sync_age`` are mocked. On 2026-08-01
    that path rewrote the live config on this machine — dropping ``env =
    "exec"``, five per-secret opt-ins and every provider field — which is the
    exact wipe class mde #82 documents.

    Tests that need their own paths simply monkeypatch again; the last write
    wins, so this fixture is a floor, not a constraint.
    """
    monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", tmp_path / "fnox-config.toml")
    monkeypatch.setattr(manage, "_AGE_KEY_PATH", tmp_path / "age.txt")


def _tty_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)


def _non_tty_stdin(monkeypatch: pytest.MonkeyPatch, data: str) -> None:
    fake = io.StringIO(data)
    fake.isatty = lambda: False  # type: ignore[method-assign]
    monkeypatch.setattr("sys.stdin", fake)


@pytest.fixture
def _stub_bootstrap() -> object:
    """Stub the ``bootstrap_config`` collaborator.

    ``add_secret``/``remove_secret`` call it to reconcile declarations. These
    classes test the CRUD wrapper's own contract — "call it, bail on non-zero" —
    and ``TestBootstrapConfig`` covers the real thing. Before this stub existed,
    the tests ran the REAL bootstrap: the real age key, a real ``age-keygen``, a
    real Doppler network call, and a real write to the user's config. They
    passed because that environment happened to be present.
    """
    with patch("mde.secrets.manage.bootstrap_config", return_value=0) as stub:
        yield stub


@pytest.mark.usefixtures("_stub_bootstrap")
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


@pytest.mark.usefixtures("_stub_bootstrap")
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


def _fnox_argv(run_mock: MagicMock) -> list[list[str]]:
    """Every ``fnox`` argv the code under test spawned, in call order."""
    return [call.args[0] for call in run_mock.call_args_list if call.args[0][0] == "fnox"]


class TestBootstrapConfig:
    """Tests for manage.bootstrap_config."""

    def test_creates_providers_and_declares_via_fnox(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """First run writes the providers block itself; declarations go through fnox."""
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
            ) as run_mock,
            patch(
                "mde.secrets.manage.doppler_list_secrets",
                return_value={"GITHUB_TOKEN": "val", "AWS_ACCESS_KEY_ID": "val"},
            ),
        ):
            rc = manage.bootstrap_config()
            argv = _fnox_argv(run_mock)
        assert rc == 0
        content = config_file.read_text()
        assert "[providers.age]" in content
        assert "age1recipient" in content
        assert "[providers.doppler_dotfiles_dev_personal]" in content
        assert 'DOPPLER_TOKEN = { provider = "keychain", value = "DOPPLER_TOKEN" }' in content
        # The declarations are NOT written by this module any more.
        assert "GITHUB_TOKEN" not in content
        assert [
            argv_line
            for argv_line in argv
            if argv_line[:4] == ["fnox", "set", "GITHUB_TOKEN", "GITHUB_TOKEN"]  # value == key name
        ], argv
        assert [
            argv_line
            for argv_line in argv
            if argv_line[:4] == ["fnox", "set", "AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"]
        ], argv
        # Every declare targets the Doppler provider and this config file.
        for argv_line in argv:
            if argv_line[1] == "set":
                assert "--provider" in argv_line
                assert argv_line[argv_line.index("--provider") + 1] == (
                    "doppler_dotfiles_dev_personal"
                )
                assert argv_line[argv_line.index("--config") + 1] == str(config_file)

    def test_config_file_mode_is_600(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
            patch("mde.secrets.manage.doppler_list_secrets", return_value={"KEY_A": "v"}),
        ):
            assert manage.bootstrap_config() == 0
        assert config_file.stat().st_mode & 0o777 == 0o600

    def test_never_rewrites_an_existing_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression test for mde #82: the env mode and opt-ins must survive.

        The wipe happened because the config was regenerated from a template
        that never emitted ``env``. Nothing is regenerated now, so with fnox
        mocked out the file must come back byte-identical.
        """
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        original = (
            'env = "exec"\n'
            "\n"
            "[providers.keychain]\n"
            'type = "keychain"\n'
            "[providers.age]\n"
            'type = "age"\n'
            "[providers.doppler_dotfiles_dev_personal]\n"
            'type = "doppler"\n'
            "\n"
            "[secrets]\n"
            'KEY_A = { provider = "doppler_dotfiles_dev_personal", '
            'value = "KEY_A", env = true }\n'
        )
        config_file.write_text(original)
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
            assert manage.bootstrap_config() == 0
        assert config_file.read_text() == original

    def test_prunes_stale_declarations_via_fnox(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[providers.keychain]\n"
            "[providers.age]\n"
            "[providers.doppler_dotfiles_dev_personal]\n"
            "\n"
            "[secrets]\n"
            'DOPPLER_TOKEN = { provider = "keychain", value = "DOPPLER_TOKEN" }\n'
            'GONE_FROM_DOPPLER = { provider = "doppler_dotfiles_dev_personal", '
            'value = "GONE_FROM_DOPPLER" }\n'
        )
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1xxx\n", stderr=""),
            ) as run_mock,
            patch("mde.secrets.manage.doppler_list_secrets", return_value={"KEY_A": "v"}),
        ):
            assert manage.bootstrap_config() == 0
            argv = _fnox_argv(run_mock)
        assert ["fnox", "remove", "GONE_FROM_DOPPLER", "--config", str(config_file)] in argv
        # DOPPLER_TOKEN is on the skip list: never declared, never pruned.
        assert not [line for line in argv if "DOPPLER_TOKEN" in line], argv

    def test_skip_list_keys_are_never_declared(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A keychain-backed or auto-injected key must never reach `fnox set`.

        `fnox set` against the keychain provider performs a REAL keychain write,
        so declaring DOPPLER_TOKEN this way would overwrite the live token with
        the literal string "DOPPLER_TOKEN".
        """
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1xxx\n", stderr=""),
            ) as run_mock,
            patch(
                "mde.secrets.manage.doppler_list_secrets",
                return_value={
                    "KEY_A": "v",
                    "DOPPLER_TOKEN": "v",
                    "AGE_PRIVATE_KEY": "v",
                    "DOPPLER_PROJECT": "v",
                    "DOPPLER_CONFIG": "v",
                    "DOPPLER_ENVIRONMENT": "v",
                },
            ),
        ):
            assert manage.bootstrap_config() == 0
            declared = [line[2] for line in _fnox_argv(run_mock) if line[1] == "set"]
        assert declared == ["KEY_A"]

    def test_missing_provider_fails_loud_without_writing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An existing config with no doppler provider is not silently rewritten."""
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        original = "[providers.keychain]\n[providers.age]\n\n[secrets]\n"
        config_file.write_text(original)
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)
        with (
            patch(
                "mde.secrets.manage.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="age1xxx\n", stderr=""),
            ),
            patch("mde.secrets.manage.doppler_list_secrets", return_value={"KEY_A": "v"}),
        ):
            assert manage.bootstrap_config() == 1
        assert config_file.read_text() == original

    def test_declare_failure_is_reported_not_swallowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        age_file = tmp_path / "age.txt"
        age_file.write_text("k")
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr(manage, "_AGE_KEY_PATH", age_file)
        monkeypatch.setattr(manage, "_FNOX_CONFIG_PATH", config_file)

        def _run(cmd: list[str], **_kwargs: object) -> MagicMock:
            if cmd[0] == "fnox":
                return MagicMock(returncode=1, stdout="", stderr="boom")
            return MagicMock(returncode=0, stdout="age1xxx\n", stderr="")

        with (
            patch("mde.secrets.manage.subprocess.run", side_effect=_run),
            patch("mde.secrets.manage.doppler_list_secrets", return_value={"KEY_A": "v"}),
        ):
            assert manage.bootstrap_config() == 1

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
