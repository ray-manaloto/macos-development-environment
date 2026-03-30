"""Tests for the guard_main_commit PreToolUse hook."""

from __future__ import annotations

from unittest.mock import patch

from mde.hooks.guard_main_commit import check_main_commit


class TestCheckMainCommit:
    """Unit tests for check_main_commit logic."""

    def test_empty_command_returns_none(self) -> None:
        assert check_main_commit("") is None

    def test_non_commit_command_returns_none(self) -> None:
        assert check_main_commit("git status") is None
        assert check_main_commit("git push origin main") is None
        assert check_main_commit("git log --oneline") is None

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="main")
    def test_commit_on_main_warns(self, mock_branch: object) -> None:
        result = check_main_commit("git commit -m 'test'")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert "WARNING" in result["systemMessage"]
        assert "worktree" in result["systemMessage"].lower()

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="master")
    def test_commit_on_master_warns(self, mock_branch: object) -> None:
        result = check_main_commit("git commit -m 'test'")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="feat/my-feature")
    def test_commit_on_feature_branch_returns_none(self, mock_branch: object) -> None:
        assert check_main_commit("git commit -m 'test'") is None

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="main")
    def test_commit_amend_on_main_warns(self, mock_branch: object) -> None:
        result = check_main_commit("git commit --amend")
        assert result is not None

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="main")
    def test_chained_command_with_commit_warns(self, mock_branch: object) -> None:
        result = check_main_commit("git add -A && git commit -m 'test'")
        assert result is not None

    @patch("mde.hooks.guard_main_commit._current_branch", return_value=None)
    def test_detached_head_returns_none(self, mock_branch: object) -> None:
        """Detached HEAD (None) should not warn."""
        assert check_main_commit("git commit -m 'test'") is None

    def test_git_committed_not_matched(self) -> None:
        """Past tense 'committed' should not trigger."""
        assert check_main_commit("echo 'changes committed'") is None

    @patch("mde.hooks.guard_main_commit._current_branch", return_value="main")
    def test_heredoc_commit_on_main_warns(self, mock_branch: object) -> None:
        result = check_main_commit("git commit -m \"$(cat <<'EOF'\nfeat: my change\nEOF\n)\"")
        assert result is not None
