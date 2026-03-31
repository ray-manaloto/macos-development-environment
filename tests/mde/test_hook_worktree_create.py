"""Tests for WorktreeCreate hook."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    import pytest


def _make_stdin(
    name: str = "test-wt",
    session_id: str = "abc12345def",
    cwd: str | None = None,
) -> str:
    """Create a JSON string mimicking WorktreeCreate stdin."""
    return json.dumps(
        {
            "session_id": session_id,
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": cwd or "/tmp/repo",
            "hook_event_name": "WorktreeCreate",
            "name": name,
        }
    )


class TestWorktreeCreation:
    """Core worktree creation behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_creates_worktree_at_expected_path(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Worktree created at <cwd>/.claude/worktrees/<name>."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        expected_path = cwd / ".claude" / "worktrees" / "feat-auth"

        mock_run.return_value = (0, "")
        result = _create_worktree(name="feat-auth", session_id="abc12345", cwd=cwd)

        assert result == expected_path
        git_call = mock_run.call_args_list[0]
        assert "git" in git_call.args[0][0]
        assert "worktree" in git_call.args[0]
        assert str(expected_path) in git_call.args[0]

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_branch_name_includes_session_id(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Branch name is worktree-<name>-<session_id[:8]> for uniqueness."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        mock_run.return_value = (0, "")

        _create_worktree(name="feat-auth", session_id="abc12345def", cwd=cwd)

        git_call = mock_run.call_args_list[0]
        cmd = git_call.args[0]
        assert any("worktree-feat-auth-abc12345" in str(arg) for arg in cmd)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_branches_from_head_not_origin(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Worktree bases from HEAD (current branch), not origin/HEAD."""
        from mde.hooks.worktree_create import _create_worktree

        cwd = tmp_path / "repo"
        cwd.mkdir()
        mock_run.return_value = (0, "")

        _create_worktree(name="test", session_id="abc12345", cwd=cwd)

        git_call = mock_run.call_args_list[0]
        cmd = git_call.args[0]
        assert "HEAD" in cmd
        assert "origin/HEAD" not in " ".join(cmd)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_git_failure_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Returns None when git worktree add fails."""
        from mde.hooks.worktree_create import _create_worktree

        mock_run.return_value = (128, "fatal: already exists")

        result = _create_worktree(name="bad", session_id="abc12345", cwd=tmp_path)
        assert result is None

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_existing_path_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Returns None when worktree path already exists."""
        from mde.hooks.worktree_create import _create_worktree

        wt_path = tmp_path / ".claude" / "worktrees" / "existing"
        wt_path.mkdir(parents=True)

        result = _create_worktree(name="existing", session_id="abc12345", cwd=tmp_path)
        assert result is None
        mock_run.assert_not_called()


class TestEnvironmentSetup:
    """mise trust and uv sync behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_trusts_mise_config(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Mise trust called on worktree path after creation."""
        from mde.hooks.worktree_create import _setup_environment

        mock_run.return_value = (0, "")
        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path.parent)

        mise_calls = [c for c in mock_run.call_args_list if "mise" in str(c)]
        assert len(mise_calls) >= 1
        assert "trust" in str(mise_calls[0])

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_removes_virtual_env(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Uv sync runs with VIRTUAL_ENV removed from env dict."""
        from mde.hooks.worktree_create import _setup_environment

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        mock_run.return_value = (0, "")

        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path.parent)

        uv_calls = [c for c in mock_run.call_args_list if "uv" in str(c)]
        assert len(uv_calls) >= 1
        env_arg = uv_calls[0].kwargs.get("env", {})
        assert "VIRTUAL_ENV" not in env_arg


class TestStdoutPurity:
    """Stdout must contain ONLY the worktree path."""

    def test_stdout_contains_only_the_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Stdout is exactly one line containing only the absolute path."""
        import io

        from mde.hooks.worktree_create import worktree_create

        wt_path = tmp_path / ".claude" / "worktrees" / "test-wt"
        stdin_data = _make_stdin(name="test-wt", cwd=str(tmp_path))

        with (
            patch("mde.hooks.worktree_create._create_worktree", return_value=wt_path),
            patch("mde.hooks.worktree_create._setup_environment", return_value=True),
        ):
            monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
            captured = io.StringIO()
            monkeypatch.setattr("sys.stdout", captured)

            result = worktree_create()

            assert result == 0
            output = captured.getvalue()
            assert output.strip() == str(wt_path)
            assert len(output.strip().splitlines()) == 1


class TestRememberSymlink:
    """Recreate .remember symlink in worktree."""

    def test_remember_symlink_recreated(self, tmp_path: Path) -> None:
        """If .remember is a symlink in repo root, it's recreated in worktree."""
        from mde.hooks.worktree_create import _setup_environment

        repo = tmp_path / "repo"
        repo.mkdir()
        wt = tmp_path / "worktree"
        wt.mkdir()

        target = repo / ".generated" / "remember"
        target.mkdir(parents=True)
        (repo / ".remember").symlink_to(target)

        with patch("mde.hooks.worktree_create._run_cmd", return_value=(0, "")):
            _setup_environment(worktree_path=wt, repo_root=repo)

        assert (wt / ".remember").is_symlink()
        assert (wt / ".remember").resolve() == target.resolve()


class TestWorktreeInclude:
    """Copy .worktreeinclude-matched files."""

    def test_copies_matching_files(self, tmp_path: Path) -> None:
        """Files matching .worktreeinclude patterns are copied."""
        from mde.hooks.worktree_create import _copy_worktreeinclude

        repo = tmp_path / "repo"
        repo.mkdir()
        wt = tmp_path / "worktree"
        wt.mkdir()

        (repo / ".env").write_text("SECRET=val")
        (repo / ".env.local").write_text("LOCAL=val")
        (repo / "README.md").write_text("not copied")
        (repo / ".worktreeinclude").write_text(".env\n.env.local\n")

        _copy_worktreeinclude(repo_root=repo, worktree_path=wt)

        assert (wt / ".env").read_text() == "SECRET=val"
        assert (wt / ".env.local").read_text() == "LOCAL=val"
        assert not (wt / "README.md").exists()

    def test_missing_worktreeinclude_is_fine(self, tmp_path: Path) -> None:
        """No error when .worktreeinclude doesn't exist."""
        from mde.hooks.worktree_create import _copy_worktreeinclude

        _copy_worktreeinclude(repo_root=tmp_path, worktree_path=tmp_path / "wt")


class TestErrorHandling:
    """Failure behavior."""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_mise_failure_is_nonfatal(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Continues when mise trust fails."""
        from mde.hooks.worktree_create import _setup_environment

        mock_run.side_effect = [(1, "trust error"), (0, "")]
        result = _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)
        assert result is True

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_fatal_for_python_project(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """UV sync failure is fatal when pyproject.toml exists in repo root."""
        from mde.hooks.worktree_create import _setup_environment

        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        mock_run.side_effect = [(0, ""), (1, "sync error")]

        result = _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)
        assert result is False

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_uv_sync_skipped_for_non_python(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """UV sync skipped when no pyproject.toml."""
        from mde.hooks.worktree_create import _setup_environment

        mock_run.return_value = (0, "")
        _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)

        # Check the command (first positional arg), not full repr which includes env dicts
        cmd_lists = [c.args[0] for c in mock_run.call_args_list]
        assert any("mise" in cmd[0] for cmd in cmd_lists)
        assert not any("uv" in cmd[0] for cmd in cmd_lists)

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_git_failure_returns_nonzero(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Non-zero exit when git worktree add fails (both attempts)."""
        from mde.hooks.worktree_create import _create_worktree

        mock_run.return_value = (128, "fatal: error")
        result = _create_worktree(name="bad", session_id="abc12345", cwd=tmp_path)
        assert result is None

    def test_stderr_for_diagnostics(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """All non-path output goes to stderr, not stdout."""
        from mde.hooks.worktree_create import _setup_environment

        with patch("mde.hooks.worktree_create._run_cmd", return_value=(1, "some error")):
            _setup_environment(worktree_path=tmp_path, repo_root=tmp_path)

        captured = capsys.readouterr()
        assert captured.out == ""

    @patch("mde.hooks.worktree_create._run_cmd")
    def test_existing_branch_reused_without_force_reset(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """If -b fails (branch exists), fallback checks out existing branch without -B."""
        from mde.hooks.worktree_create import _create_worktree

        mock_run.side_effect = [(128, "already exists"), (0, "")]
        result = _create_worktree(name="existing", session_id="abc12345", cwd=tmp_path)

        assert result is not None
        second_call = mock_run.call_args_list[1]
        cmd = second_call.args[0]
        assert "-b" not in cmd
        assert "-B" not in cmd
