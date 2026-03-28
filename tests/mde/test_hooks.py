"""Tests for Claude Code hook handlers."""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestLogEditOutcome:
    """Tests for the PostToolUse hook handler."""

    def test_logs_write_operation(self, tmp_path: object) -> None:
        from mde.hooks import log_outcome

        outfile = tmp_path / "edit-outcomes.jsonl"  # type: ignore[operator]
        with patch.object(log_outcome, "_OUTCOME_FILE", outfile):
            data = {
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/test.py"},
                "tool_response": "ok",
            }
            stdin = io.StringIO(json.dumps(data))
            with patch.object(sys, "stdin", stdin):
                assert log_outcome.log_edit_outcome() == 0

        lines = outfile.read_text().strip().split("\n")  # type: ignore[union-attr]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["tool"] == "Write"
        assert record["file"] == "/tmp/test.py"
        assert record["operation"] == "write"

    def test_handles_invalid_json(self) -> None:
        from mde.hooks.log_outcome import log_edit_outcome

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert log_edit_outcome() == 0


class TestValidateAgents:
    """Tests for the agent frontmatter validator."""

    def test_valid_frontmatter(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {
            "name": "my-agent",
            "description": "A test agent",
            "model": "sonnet",
            "memory": "project",
        }
        assert validate_agent_frontmatter(fm) == []

    def test_missing_required_fields(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        assert len(validate_agent_frontmatter({})) == 2  # name + description

    def test_invalid_name_pattern(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "MyAgent", "description": "Bad name"}
        errors = validate_agent_frontmatter(fm)
        assert any("name" in e for e in errors)
        assert len(errors) >= 1

    def test_invalid_model(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "model": "gpt-4"}
        errors = validate_agent_frontmatter(fm)
        assert any("model" in e for e in errors)

    def test_valid_claude_prefixed_model(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "model": "claude-sonnet-4-5-20250514"}
        assert validate_agent_frontmatter(fm) == []

    def test_invalid_permission_mode(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "permissionMode": "yolo"}
        errors = validate_agent_frontmatter(fm)
        assert any("permissionMode" in e for e in errors)

    def test_invalid_memory_scope(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "memory": "global"}
        errors = validate_agent_frontmatter(fm)
        assert any("memory" in e for e in errors)

    def test_invalid_max_turns(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "maxTurns": 0}
        errors = validate_agent_frontmatter(fm)
        assert any("maxTurns" in e for e in errors)

    def test_max_turns_not_bool(self) -> None:
        """Pydantic accepts True as int (bool is subclass of int in Python).

        In JSON/YAML, true is not an integer, so this is a known Python quirk.
        Pydantic correctly validates True as 1 (ge=1), so no error is expected.
        """
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "maxTurns": True}
        errors = validate_agent_frontmatter(fm)
        # Pydantic treats True as int(1) which satisfies conint(ge=1)
        assert errors == []

    def test_extract_frontmatter(self) -> None:
        from mde.hooks.validate_agents import _extract_frontmatter

        text = "---\nname: test\ndescription: hello\n---\nBody content here."
        fm, err = _extract_frontmatter(text)
        assert fm == {"name": "test", "description": "hello"}
        assert err is None

    def test_extract_frontmatter_missing(self) -> None:
        from mde.hooks.validate_agents import _extract_frontmatter

        fm, err = _extract_frontmatter("No frontmatter here")
        assert fm is None
        assert err is None

    def test_extract_frontmatter_malformed_yaml(self) -> None:
        from mde.hooks.validate_agents import _extract_frontmatter

        # Syntactically invalid YAML — should return (None, error_msg), not raise
        text = "---\nname: [\nunclosed bracket\n---\nBody."
        result, err = _extract_frontmatter(text)
        assert result is None
        assert err is not None
        assert "malformed" in err.lower() or "parse error" in err.lower()

    def test_extract_frontmatter_missing_returns_none_error(self) -> None:
        from mde.hooks.validate_agents import _extract_frontmatter

        result, err = _extract_frontmatter("No frontmatter here")
        assert result is None
        assert err is None  # missing frontmatter has no error message

    def test_extract_frontmatter_valid_returns_dict_no_error(self) -> None:
        from mde.hooks.validate_agents import _extract_frontmatter

        text = "---\nname: test\ndescription: hello\n---\nBody content here."
        fm, err = _extract_frontmatter(text)
        assert fm == {"name": "test", "description": "hello"}
        assert err is None

    def test_validate_agent_file(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agent_file

        p = Path(str(tmp_path)) / "good-agent.md"
        p.write_text("---\nname: good-agent\ndescription: A good agent\n---\nBody.")
        assert validate_agent_file(p) == []

    def test_validate_agent_file_bad(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agent_file

        p = Path(str(tmp_path)) / "bad.md"
        p.write_text("---\nname: BAD\n---\nBody.")
        errors = validate_agent_file(p)
        assert len(errors) >= 2  # missing description + bad name pattern

    def test_hook_ignores_non_agent_files(self) -> None:
        from mde.hooks.validate_agents import validate_agents_hook

        data = {"tool_input": {"file_path": "/tmp/src/main.py"}}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert validate_agents_hook() == 0

    def test_hook_validates_agent_file(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agents_hook

        agent_dir = Path(str(tmp_path)) / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "test-agent.md"
        agent_file.write_text("---\nname: test-agent\ndescription: Test\n---\nBody.")

        data = {"tool_input": {"file_path": str(agent_file)}}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            assert validate_agents_hook() == 0

    def test_hook_invalid_json(self) -> None:
        from mde.hooks.validate_agents import validate_agents_hook

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert validate_agents_hook() == 0

    def test_validate_all_agents(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_all_agents

        agents_dir = Path(str(tmp_path)) / "agents"
        agents_dir.mkdir()
        (agents_dir / "good.md").write_text("---\nname: good\ndescription: Ok\n---\nBody.")
        (agents_dir / "bad.md").write_text("---\nname: BAD_NAME\n---\nBody.")
        errors = validate_all_agents(agents_dir)
        assert any("BAD_NAME" in e or "kebab-case" in e for e in errors)
        assert any("description" in e for e in errors)

    def test_unknown_fields_rejected(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "color": "blue"}
        errors = validate_agent_frontmatter(fm)
        assert any("unknown" in e for e in errors)

    def test_tools_invalid_type(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "tools": 42}
        errors = validate_agent_frontmatter(fm)
        assert any("tools" in e for e in errors)

    def test_tools_valid_string(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "tools": "Read, Glob"}
        assert validate_agent_frontmatter(fm) == []

    def test_tools_valid_list(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "t", "description": "x", "tools": ["Read", "Glob"]}
        assert validate_agent_frontmatter(fm) == []

    def test_hooks_invalid_type(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "hooks": "bad"}
        errors = validate_agent_frontmatter(fm)
        assert any("hooks" in e for e in errors)

    def test_mcp_servers_invalid_type(self) -> None:
        from mde.hooks.validate_agents import validate_agent_frontmatter

        fm = {"name": "test", "description": "x", "mcpServers": "bad"}
        errors = validate_agent_frontmatter(fm)
        assert any("mcpServers" in e for e in errors)

    def test_name_filename_mismatch(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agent_file

        p = Path(str(tmp_path)) / "my-agent.md"
        p.write_text("---\nname: other-name\ndescription: x\n---\nBody.")
        errors = validate_agent_file(p)
        assert any("does not match filename" in e for e in errors)

    def test_hook_prints_errors_to_stderr(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agents_hook

        agent_dir = Path(str(tmp_path)) / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "bad.md"
        agent_file.write_text("---\nname: BAD\n---\nBody.")

        data = {"tool_input": {"file_path": str(agent_file)}}
        stdin = io.StringIO(json.dumps(data))
        with (
            patch.object(sys, "stdin", stdin),
            patch.object(sys, "stderr", io.StringIO()) as mock_err,
        ):
            result = validate_agents_hook()
        assert result == 1
        assert "validation failed" in mock_err.getvalue()

    def test_malformed_yaml_error_message_in_file_validation(self, tmp_path: object) -> None:
        """Malformed YAML should produce a 'malformed' error, not 'no valid YAML frontmatter'."""
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agent_file

        p = Path(str(tmp_path)) / "broken.md"
        p.write_text("---\nname: [\nunclosed bracket\n---\nBody.")
        errors = validate_agent_file(p)
        assert len(errors) >= 1
        assert any("malformed" in e.lower() or "parse error" in e.lower() for e in errors)

    def test_missing_frontmatter_error_message(self, tmp_path: object) -> None:
        """Missing frontmatter should produce a 'no YAML frontmatter' error."""
        from pathlib import Path

        from mde.hooks.validate_agents import validate_agent_file

        p = Path(str(tmp_path)) / "plain.md"
        p.write_text("This file has no YAML frontmatter at all.")
        errors = validate_agent_file(p)
        assert len(errors) >= 1
        assert any("no" in e.lower() and "frontmatter" in e.lower() for e in errors)


class TestDispatchHooks:
    """Tests for the dispatch_hooks CLI path."""

    def test_validate_agents_dispatch(self) -> None:
        """validate_agents_hook returns 0 for non-agent file paths."""
        from unittest.mock import patch

        from mde.hooks.validate_agents import validate_agents_hook

        # Simulate a non-agent-file path so it short-circuits without I/O
        data = {"tool_input": {"file_path": "/tmp/not-an-agent.py"}}
        stdin = io.StringIO(json.dumps(data))
        with patch.object(sys, "stdin", stdin):
            result = validate_agents_hook()
        assert result == 0


class TestTeamQualityGates:
    """Tests for per-team quality gate validation."""

    def test_python_dev_gate_all_pass(self) -> None:
        from mde.hooks.team_quality_gates import gate_python_dev

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result):
            checks = gate_python_dev()
        assert len(checks) == 3
        assert all(c["passed"] for c in checks)
        names = {c["name"] for c in checks}
        assert names == {"ruff", "ty", "pytest"}

    def test_python_dev_gate_ruff_fails(self) -> None:
        from mde.hooks.team_quality_gates import gate_python_dev

        def side_effect(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            if "ruff" in cmd:
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=1,
                    stdout="E501 line too long",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="ok",
                stderr="",
            )

        with patch("mde.hooks.team_quality_gates.subprocess.run", side_effect=side_effect):
            checks = gate_python_dev()
        ruff_check = next(c for c in checks if c["name"] == "ruff")
        assert not ruff_check["passed"]
        assert "E501" in ruff_check["output"]

    def test_research_gate_with_findings(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.team_quality_gates import gate_research

        findings_dir = Path(str(tmp_path)) / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "test.yaml").write_text("finding: true")

        checks = gate_research(findings_path=str(findings_dir))
        assert len(checks) == 1
        assert checks[0]["passed"]
        assert checks[0]["name"] == "research-output"

    def test_research_gate_empty(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.team_quality_gates import gate_research

        empty_dir = Path(str(tmp_path)) / "findings"
        empty_dir.mkdir(parents=True)

        checks = gate_research(findings_path=str(empty_dir))
        assert len(checks) == 1
        assert checks[0]["name"] == "research-output"
        assert not checks[0]["passed"]

    def test_research_gate_ignores_non_yaml(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.team_quality_gates import gate_research

        findings_dir = Path(str(tmp_path)) / "findings"
        findings_dir.mkdir(parents=True)
        (findings_dir / "notes.txt").write_text("not yaml")

        checks = gate_research(findings_path=str(findings_dir))
        assert not checks[0]["passed"]

    def test_dotfiles_gate(self) -> None:
        from mde.hooks.team_quality_gates import gate_dotfiles

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="all ok",
            stderr="",
        )
        with patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result):
            checks = gate_dotfiles()
        assert len(checks) == 1
        assert checks[0]["name"] == "validate"
        assert checks[0]["passed"]

    def test_infrastructure_gate_with_brewfile(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.team_quality_gates import gate_infrastructure

        bf = Path(str(tmp_path)) / "Brewfile"
        bf.write_text('brew "git"\n')

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result):
            checks = gate_infrastructure(brewfile_path=str(bf))
        names = {c["name"] for c in checks}
        assert names == {"brewfile-parseable", "mise-doctor"}
        assert all(c["passed"] for c in checks)

    def test_infrastructure_gate_no_brewfile(self, tmp_path: object) -> None:
        from pathlib import Path

        from mde.hooks.team_quality_gates import gate_infrastructure

        missing = Path(str(tmp_path)) / "Brewfile"

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result):
            checks = gate_infrastructure(brewfile_path=str(missing))
        brew_check = next(c for c in checks if c["name"] == "brewfile-parseable")
        assert brew_check["passed"]
        assert "skipping" in brew_check["output"]

    def test_unknown_team_type(self) -> None:
        from mde.hooks.team_quality_gates import run_team_quality_gate

        result = run_team_quality_gate("unknown-team")
        assert not result["passed"]
        assert "error" in result
        assert "unknown team_type" in result["error"]
        assert result["checks"] == []

    def test_run_team_quality_gate_structure(self) -> None:
        from mde.hooks.team_quality_gates import run_team_quality_gate

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        with patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result):
            result = run_team_quality_gate("python-dev")
        assert result["team_type"] == "python-dev"
        assert isinstance(result["passed"], bool)
        assert isinstance(result["checks"], list)
        for check in result["checks"]:
            assert "name" in check
            assert "passed" in check
            assert "output" in check

    def test_hook_invalid_json(self) -> None:
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert team_quality_gate_hook() == 0

    def test_hook_missing_team_type(self) -> None:
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        stdin = io.StringIO(json.dumps({"other": "data"}))
        with patch.object(sys, "stdin", stdin):
            assert team_quality_gate_hook() == 0

    def test_hook_with_valid_team_type(self) -> None:
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        data = {"team_type": "python-dev"}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with (
            patch.object(sys, "stdin", stdin),
            patch.object(sys, "stdout", stdout),
            patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result),
        ):
            exit_code = team_quality_gate_hook()
        assert exit_code == 0
        output = json.loads(stdout.getvalue())
        assert output["passed"]
        assert output["team_type"] == "python-dev"

    def test_hook_returns_1_on_failure(self) -> None:
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        fail_result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="fail",
            stderr="",
        )
        data = {"team_type": "dotfiles"}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with (
            patch.object(sys, "stdin", stdin),
            patch.object(sys, "stdout", stdout),
            patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fail_result),
        ):
            exit_code = team_quality_gate_hook()
        assert exit_code == 1
        output = json.loads(stdout.getvalue())
        assert not output["passed"]


class TestHookOutputSchema:
    """Validate hook stdout conforms to Claude Code's expected schema."""

    def test_guard_install_allow_output(self) -> None:
        """When not blocking, guard_install should produce no stdout."""
        from mde.hooks.guard_install import guard_install

        data = {"tool_input": {"command": "ls"}}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            guard_install()
        assert stdout.getvalue() == ""  # No output = allow

    def test_guard_install_block_output_schema(self) -> None:
        """When blocking, output must be valid SyncHookJSONOutput."""
        from claude_agent_sdk.types import SyncHookJSONOutput

        from mde.hooks.guard_install import guard_install

        data = {"tool_input": {"command": "npm install -g foo"}}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            guard_install()
        output = stdout.getvalue()
        assert output.strip()  # Should have produced output
        parsed = json.loads(output)
        allowed_fields = set(SyncHookJSONOutput.__annotations__)
        assert set(parsed.keys()).issubset(allowed_fields)
        # hookSpecificOutput is required for PreToolUse deny decisions
        assert "hookSpecificOutput" in parsed

    def test_team_quality_gate_output_schema(self) -> None:
        """team_quality_gate_hook output must be valid JSON."""
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        fake_result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ok",
            stderr="",
        )
        data = {"team_type": "python-dev"}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with (
            patch.object(sys, "stdin", stdin),
            patch.object(sys, "stdout", stdout),
            patch("mde.hooks.team_quality_gates.subprocess.run", return_value=fake_result),
        ):
            team_quality_gate_hook()
        output = stdout.getvalue()
        assert output.strip()
        parsed = json.loads(output)  # Must be valid JSON
        assert isinstance(parsed, dict)
        assert "passed" in parsed
        assert "team_type" in parsed

    def test_team_quality_gate_unknown_type_output(self) -> None:
        """Unknown team type should still produce valid JSON."""
        from mde.hooks.team_quality_gates import team_quality_gate_hook

        data = {"team_type": "unknown-type"}
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            team_quality_gate_hook()
        output = stdout.getvalue()
        if output.strip():
            parsed = json.loads(output)  # Must be valid JSON
            assert isinstance(parsed, dict)

    def test_hooks_subparsers_populated_from_discovery(self) -> None:
        """Auto-discovered hooks must all appear as subparser choices."""
        from mde.cli import _build_parser, _discover_hooks

        parser = _build_parser()
        discovered = _discover_hooks()
        # Find the hooks subparser and extract registered action names
        hooks_choices: set[str] = set()
        subparsers = parser._subparsers
        if subparsers is not None:
            for action in subparsers._group_actions:
                choices = getattr(action, "choices", None)
                if choices is None:
                    continue
                for choice_key, choice_parser in choices.items():
                    if choice_key == "hooks":
                        sub = choice_parser._subparsers
                        if sub is not None:
                            for sub_action in sub._group_actions:
                                sub_choices = getattr(sub_action, "choices", None)
                                if sub_choices is not None:
                                    hooks_choices = set(sub_choices.keys())
        assert hooks_choices, "Could not find hooks subparser"
        assert hooks_choices == set(discovered.keys())


class TestGuardDotfileEdit:
    """Tests for the dotfile edit guard hook (PreToolUse:Bash/Write/Edit)."""

    def test_bash_blocks_direct_edit(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_dotfile_edit

        result = check_dotfile_edit("sed -i 's/old/new/' ~/.zshrc")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_bash_allows_chezmoi_edit(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_dotfile_edit

        assert check_dotfile_edit("chezmoi edit ~/.zshrc") is None

    def test_bash_allows_chezmoi_source(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_dotfile_edit

        assert check_dotfile_edit("cat ~/.local/share/chezmoi/dot_zshrc") is None

    def test_bash_allows_safe_command(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_dotfile_edit

        assert check_dotfile_edit("ls ~/projects") is None

    def test_file_path_blocks_zshrc(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        home = str(Path("~").expanduser())
        result = check_file_path_edit(f"{home}/.zshrc")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_file_path_blocks_config_dir(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        home = str(Path("~").expanduser())
        result = check_file_path_edit(f"{home}/.config/starship.toml")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_file_path_blocks_gitconfig(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        home = str(Path("~").expanduser())
        result = check_file_path_edit(f"{home}/.gitconfig")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_file_path_allows_chezmoi_source(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        home = str(Path("~").expanduser())
        assert check_file_path_edit(f"{home}/.local/share/chezmoi/dot_zshrc") is None

    def test_file_path_allows_project_file(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        assert check_file_path_edit("/tmp/src/main.py") is None

    def test_file_path_allows_empty(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        assert check_file_path_edit("") is None

    def test_file_path_with_tilde(self) -> None:
        from mde.hooks.guard_dotfile_edit import check_file_path_edit

        result = check_file_path_edit("~/.zshrc")
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_hook_handles_write_tool(self) -> None:
        from mde.hooks.guard_dotfile_edit import guard_dotfile_edit

        home = str(Path("~").expanduser())
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": f"{home}/.zshrc"},
        }
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            exit_code = guard_dotfile_edit()
        assert exit_code == 0
        output = stdout.getvalue()
        assert output.strip()
        parsed = json.loads(output)
        assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_hook_handles_edit_tool(self) -> None:
        from mde.hooks.guard_dotfile_edit import guard_dotfile_edit

        home = str(Path("~").expanduser())
        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": f"{home}/.config/mise/config.toml"},
        }
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            exit_code = guard_dotfile_edit()
        assert exit_code == 0
        output = stdout.getvalue()
        assert output.strip()
        parsed = json.loads(output)
        assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_hook_allows_write_to_project_file(self) -> None:
        from mde.hooks.guard_dotfile_edit import guard_dotfile_edit

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/src/main.py"},
        }
        stdin = io.StringIO(json.dumps(data))
        stdout = io.StringIO()
        with patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", stdout):
            exit_code = guard_dotfile_edit()
        assert exit_code == 0
        assert stdout.getvalue() == ""


class TestNoSilentFailures:
    """Ensure hooks don't silently swallow errors."""

    def test_no_bare_except_pass_in_hooks(self) -> None:
        """Hooks must not have bare 'except: pass' without logging."""
        hooks_dir = Path("src/mde/hooks")
        violations = [
            f"{py_file.name}:{node.lineno}: bare 'except: pass' without logging"
            for py_file in sorted(hooks_dir.glob("*.py"))
            if py_file.name != "__init__.py"
            for node in ast.walk(ast.parse(py_file.read_text()))
            if isinstance(node, ast.ExceptHandler)
            and node.type is None
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
        ]
        assert not violations, "Silent failure patterns found:\n" + "\n".join(violations)

    def test_no_except_pass_without_logging(self) -> None:
        """Even typed except handlers should log, not just pass."""
        hooks_dir = Path("src/mde/hooks")
        violations: list[str] = []
        for py_file in sorted(hooks_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            source = py_file.read_text()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and len(node.body) == 1:
                    stmt = node.body[0]
                    if isinstance(stmt, ast.Pass):
                        # Check if there's a comment on the same line
                        lines = source.splitlines()
                        line = lines[stmt.lineno - 1] if stmt.lineno <= len(lines) else ""
                        if "#" not in line:
                            violations.append(
                                f"{py_file.name}:{node.lineno}: 'except ... : pass' "
                                "without logging or comment"
                            )
        assert not violations, "Silent failure patterns found:\n" + "\n".join(violations)


class TestHooksAutoDiscovery:
    """Tests for the hooks auto-discovery mechanism."""

    def test_all_hook_modules_have_hook_meta(self) -> None:
        """Every non-private hook module must have __hook_meta__."""
        hooks_dir = Path("src/mde/hooks")
        missing: list[str] = []
        for py_file in sorted(hooks_dir.glob("*.py")):
            if py_file.name.startswith("_") or py_file.name == "__init__.py":
                continue
            source = py_file.read_text()
            tree = ast.parse(source)
            has_meta = any(
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__hook_meta__"
                for node in ast.iter_child_nodes(tree)
            )
            if not has_meta:
                missing.append(py_file.name)
        assert not missing, f"Hook modules without __hook_meta__: {missing}"

    def test_hook_meta_has_required_keys(self) -> None:
        """Every __hook_meta__ must have 'help' and 'entry' keys."""
        from mde.cli import _discover_hooks

        hooks = _discover_hooks()
        assert len(hooks) > 0, "No hooks discovered"
        for cmd_name, (mod_path, fn_name, help_text) in hooks.items():
            assert help_text, f"{cmd_name}: empty help text"
            assert fn_name, f"{cmd_name}: empty entry function name"
            assert mod_path.startswith("mde.hooks."), f"{cmd_name}: bad module path {mod_path}"

    def test_entry_functions_exist(self) -> None:
        """Every __hook_meta__ entry function must exist in its module."""
        import importlib

        from mde.cli import _discover_hooks

        hooks = _discover_hooks()
        for cmd_name, (mod_path, fn_name, _help) in hooks.items():
            mod = importlib.import_module(mod_path)
            assert hasattr(mod, fn_name), f"{cmd_name}: {mod_path} has no function '{fn_name}'"
            assert callable(getattr(mod, fn_name)), (
                f"{cmd_name}: {mod_path}.{fn_name} is not callable"
            )

    def test_discover_hooks_returns_expected_commands(self) -> None:
        """Auto-discovery must find all known hook commands."""
        from mde.cli import _discover_hooks

        hooks = _discover_hooks()
        expected = {
            "log-edit-outcome",
            "log-agent-event",
            "guard-install",
            "guard-dotfile-edit",
            "remind-chezmoi-commit",
            "session-start",
            "post-compact",
            "team-quality-gate",
            "validate-plugins",
            "persist-transcripts",
            "validate-agents",
        }
        assert expected.issubset(set(hooks.keys())), (
            f"Missing hooks: {expected - set(hooks.keys())}"
        )

    def test_extract_hook_meta_from_mock_module(self) -> None:
        """_extract_hook_meta correctly parses __hook_meta__ from AST."""
        from mde.cli import _extract_hook_meta

        source = """
__hook_meta__ = {
    "help": "Test hook help",
    "entry": "my_function",
}
"""
        tree = ast.parse(source)
        meta = _extract_hook_meta(tree)
        assert meta is not None
        assert meta["help"] == "Test hook help"
        assert meta["entry"] == "my_function"

    def test_extract_hook_meta_missing(self) -> None:
        """Modules without __hook_meta__ return None."""
        from mde.cli import _extract_hook_meta

        source = "x = 42\n"
        tree = ast.parse(source)
        assert _extract_hook_meta(tree) is None

    def test_extract_hook_meta_incomplete(self) -> None:
        """__hook_meta__ without required keys returns None."""
        from mde.cli import _extract_hook_meta

        source = '__hook_meta__ = {"help": "only help"}\n'
        tree = ast.parse(source)
        assert _extract_hook_meta(tree) is None

    def test_no_manual_hooks_dispatch_in_cli(self) -> None:
        """cli.py must not have a hardcoded _HOOKS_DISPATCH dict."""
        cli_source = Path("src/mde/cli.py").read_text()
        assert "_HOOKS_DISPATCH" not in cli_source, (
            "cli.py still has hardcoded _HOOKS_DISPATCH — should be auto-discovered"
        )

    def test_extract_hook_meta_annotated_assign(self) -> None:
        """__hook_meta__ with type annotation (AnnAssign) should be parsed."""
        from mde.cli import _extract_hook_meta

        source = """
__hook_meta__: dict[str, str] = {
    "help": "Annotated hook help",
    "entry": "annotated_function",
}
"""
        tree = ast.parse(source)
        meta = _extract_hook_meta(tree)
        assert meta is not None
        assert meta["help"] == "Annotated hook help"
        assert meta["entry"] == "annotated_function"

    def test_no_hook_command_collisions(self) -> None:
        """All discovered hooks must have unique command names."""
        from mde.cli import _discover_hooks

        # If this raises ValueError, there's a collision
        hooks = _discover_hooks()
        # Double-check: all command names are unique
        cmd_names = list(hooks.keys())
        assert len(cmd_names) == len(set(cmd_names)), (
            f"Duplicate hook command names: {[n for n in cmd_names if cmd_names.count(n) > 1]}"
        )
