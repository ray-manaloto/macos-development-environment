"""Tests for the debate guard PreToolUse hook."""

from __future__ import annotations

from mde.hooks.guard_debate import check_debate_command


class TestWarnsRawCLI:
    """Commands that should trigger an advisory warning."""

    def test_warns_codex_exec(self) -> None:
        result = check_debate_command('codex exec "prompt"')
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert "systemMessage" in result
        assert "uv run mde-py debate" in result["systemMessage"]

    def test_warns_codex_review(self) -> None:
        result = check_debate_command("codex review src/")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert "systemMessage" in result

    def test_warns_gemini_direct(self) -> None:
        result = check_debate_command('gemini -p "" "prompt"')
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert "systemMessage" in result

    def test_warns_gemini_piped(self) -> None:
        """Catches gemini after a bare pipe — the canonical invocation pattern."""
        result = check_debate_command('printf \'%s\' "$p" | gemini -p "" -o json -y')
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_warns_gemini_chained(self) -> None:
        result = check_debate_command("echo hi && gemini -p '' -y")
        assert result is not None


class TestAllowedCommands:
    """Commands that should pass without warning (return None)."""

    def test_allows_mde_debate(self) -> None:
        assert check_debate_command("uv run mde-py debate invoke") is None

    def test_allows_mde_other(self) -> None:
        assert check_debate_command("uv run mde-py quality") is None

    def test_allows_which_codex(self) -> None:
        assert check_debate_command("which codex") is None

    def test_allows_which_gemini(self) -> None:
        assert check_debate_command("which gemini") is None

    def test_allows_codex_version(self) -> None:
        assert check_debate_command("codex --version") is None

    def test_allows_gemini_version(self) -> None:
        assert check_debate_command("gemini --version") is None

    def test_allows_codex_login(self) -> None:
        assert check_debate_command("codex login") is None

    def test_no_warning_non_bash(self) -> None:
        assert check_debate_command("") is None

    def test_allows_unrelated_command(self) -> None:
        assert check_debate_command("git status") is None
