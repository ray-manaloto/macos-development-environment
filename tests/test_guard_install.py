"""Tests for the install guard PreToolUse hook."""

from __future__ import annotations

from mde.hooks.guard_install import check_install_command


class TestBlockedCommands:
    """Commands that should be blocked (return deny dict)."""

    def test_blocks_npm_install_global(self) -> None:
        result = check_install_command("npm install -g typescript")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_brew_install(self) -> None:
        result = check_install_command("brew install jq")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_pip_install(self) -> None:
        result = check_install_command("pip install requests")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_cargo_install(self) -> None:
        result = check_install_command("cargo install ripgrep")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_go_install(self) -> None:
        result = check_install_command("go install golang.org/x/tools/gopls@latest")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_bun_add_global(self) -> None:
        result = check_install_command("bun add -g typescript")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_uv_tool_install(self) -> None:
        result = check_install_command("uv tool install ruff")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_pipx_install(self) -> None:
        result = check_install_command("pipx install black")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_yarn_global_add(self) -> None:
        result = check_install_command("yarn global add typescript")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_blocks_npm_install_long_global(self) -> None:
        result = check_install_command("npm install --global typescript")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestAllowedCommands:
    """Commands that should be allowed (return None)."""

    def test_allows_npm_install_local(self) -> None:
        assert check_install_command("npm install typescript") is None

    def test_allows_pip_install_in_venv(self) -> None:
        assert check_install_command("uv pip install requests") is None

    def test_allows_mise_install(self) -> None:
        assert check_install_command("mise install") is None

    def test_allows_unrelated_command(self) -> None:
        assert check_install_command("git status") is None

    def test_allows_brew_bundle(self) -> None:
        assert check_install_command("brew bundle --file=Brewfile") is None

    def test_allows_npx_skills_add(self) -> None:
        assert check_install_command("npx skills add teng-lin/agent-fetch") is None
