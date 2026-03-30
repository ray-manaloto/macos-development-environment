"""Tests for WorktreeCreate hook."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


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
