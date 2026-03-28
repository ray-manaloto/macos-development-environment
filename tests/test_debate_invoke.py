"""Tests for mde.debate.invoke — multi-model CLI invocation backend."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mde.debate.invoke import (
    DebateModel,
    InvocationResult,
    _extract_gemini_json,
    _strip_codex_noise,
    _strip_gemini_noise,
    invoke_all,
    invoke_all_parallel,
    invoke_model,
)

# ── Model enum ────────────────────────────────────────────────────────────


class TestDebateModel:
    """Test DebateModel enum."""

    def test_all_models_exist(self) -> None:
        assert DebateModel.CODEX.value == "codex"
        assert DebateModel.GEMINI.value == "gemini"
        assert DebateModel.CLAUDE.value == "claude"
        assert DebateModel.SONNET.value == "sonnet"

    def test_from_string(self) -> None:
        assert DebateModel("codex") == DebateModel.CODEX
        assert DebateModel("gemini") == DebateModel.GEMINI


# ── Noise stripping ──────────────────────────────────────────────────────


class TestStripCodexNoise:
    """Test Codex output noise stripping."""

    def test_strips_boot_header(self) -> None:
        output = (
            "OpenAI Codex v0.116.0 (research preview)\n"
            "--------\n"
            "workdir: /tmp/test\n"
            "model: gpt-5.4\n"
            "provider: openai\n"
            "approval: never\n"
            "sandbox: workspace-write\n"
            "reasoning effort: xhigh\n"
            "reasoning summaries: none\n"
            "session id: abc-123\n"
            "--------\n"
            "user\n"
            "IMPORTANT: Skip all skills.\n"
            "warning: unstable features\n"
            "mcp: exa starting\n"
            "mcp: exa ready\n"
            "This is the actual response.\n"
            "tokens used\n"
            "120000\n"
        )
        result = _strip_codex_noise(output)
        assert result == "This is the actual response."

    def test_preserves_multiline_response(self) -> None:
        output = "Line one of response.\nLine two.\nLine three.\ntokens used\n500\n"
        result = _strip_codex_noise(output)
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result
        assert "tokens used" not in result

    def test_strips_otel_errors(self) -> None:
        output = "Response here.\nERROR opentelemetry_sdk: export failed\ntokens used\n100\n"
        result = _strip_codex_noise(output)
        assert "opentelemetry" not in result
        assert "Response here." in result


class TestStripGeminiNoise:
    """Test Gemini output noise stripping."""

    def test_strips_extension_boot(self) -> None:
        output = (
            "Registered theme: firebase-default-dark (firebase)\n"
            "Timeout of 30000 exceeds the interval\n"
            "The 'metricReader' option is deprecated.\n"
            "Loaded cached credentials.\n"
            "Loading extension: chrome-devtools-mcp\n"
            "This is the actual response.\n"
            "Export took longer than 10000 milliseconds\n"
        )
        result = _strip_gemini_noise(output)
        assert result == "This is the actual response."

    def test_strips_mcp_noise(self) -> None:
        output = (
            "Scheduling MCP context refresh...\n"
            "Executing MCP context refresh...\n"
            "MCP context refresh complete.\n"
            "Server 'github' supports tool updates.\n"
            "Registering notification handlers\n"
            "Actual content here.\n"
        )
        result = _strip_gemini_noise(output)
        assert result == "Actual content here."

    def test_strips_stack_traces(self) -> None:
        output = (
            "Response text.\n"
            "    at McpError.fromError (file:///path/types.js:2035:16)\n"
            "    at Client._onclose (file:///path/protocol.js:259:32)\n"
        )
        result = _strip_gemini_noise(output)
        assert "McpError" not in result
        assert "Response text." in result


# ── Unified invocation ────────────────────────────────────────────────────


class TestInvokeModel:
    """Test unified model invocation."""

    @patch("mde.debate.invoke._invoke_codex")
    def test_dispatches_to_codex(self, mock_codex: MagicMock) -> None:
        mock_codex.return_value = InvocationResult(
            model="codex",
            prompt="test",
            response="answer",
            success=True,
            duration_seconds=1.0,
        )
        result = invoke_model("codex", "test prompt")
        assert result.success is True
        assert result.model == "codex"
        mock_codex.assert_called_once()

    @patch("mde.debate.invoke._invoke_gemini")
    def test_dispatches_to_gemini(self, mock_gemini: MagicMock) -> None:
        mock_gemini.return_value = InvocationResult(
            model="gemini",
            prompt="test",
            response="answer",
            success=True,
            duration_seconds=2.0,
        )
        result = invoke_model("gemini", "test prompt")
        assert result.success is True
        assert result.model == "gemini"

    def test_claude_returns_error(self) -> None:
        result = invoke_model("claude", "test")
        assert result.success is False
        assert "Agent tool" in (result.error or "")

    def test_sonnet_returns_error(self) -> None:
        result = invoke_model("sonnet", "test")
        assert result.success is False
        assert "Agent tool" in (result.error or "")


class TestInvokeAll:
    """Test multi-model invocation."""

    @patch("mde.debate.invoke._invoke_codex")
    @patch("mde.debate.invoke._invoke_gemini")
    def test_invokes_both_defaults(self, mock_gemini: MagicMock, mock_codex: MagicMock) -> None:
        mock_codex.return_value = InvocationResult(
            model="codex", prompt="q", response="a", success=True, duration_seconds=1.0
        )
        mock_gemini.return_value = InvocationResult(
            model="gemini", prompt="q", response="b", success=True, duration_seconds=2.0
        )
        results = invoke_all("question")
        assert len(results) == 2
        models = [r.model for r in results]
        assert "codex" in models
        assert "gemini" in models

    @patch("mde.debate.invoke._invoke_codex")
    @patch("mde.debate.invoke._invoke_gemini")
    def test_saves_to_output_dir(
        self, mock_gemini: MagicMock, mock_codex: MagicMock, tmp_path: Path
    ) -> None:
        mock_codex.return_value = InvocationResult(
            model="codex", prompt="q", response="a", success=True, duration_seconds=1.0
        )
        mock_gemini.return_value = InvocationResult(
            model="gemini", prompt="q", response="b", success=True, duration_seconds=2.0
        )
        invoke_all("question", output_dir=tmp_path)
        assert (tmp_path / "codex.json").exists()
        assert (tmp_path / "gemini.json").exists()

    def test_skips_claude_sonnet(self) -> None:
        """Claude and Sonnet are skipped (they need Agent tool)."""
        results = invoke_all("q", models=["claude", "sonnet"])
        assert len(results) == 0  # Both skipped

    def test_unknown_model_returns_error(self) -> None:
        results = invoke_all("q", models=["unknown"])
        assert len(results) == 1
        assert results[0].success is False
        assert "Unknown model" in (results[0].error or "")


# ── Async parallel invocation ────────────────────────────────────────────


class TestInvokeAllParallel:
    """Test async parallel multi-model invocation."""

    @patch("mde.debate.invoke._invoke_codex")
    @patch("mde.debate.invoke._invoke_gemini")
    def test_invokes_both_concurrently(self, mock_gemini: MagicMock, mock_codex: MagicMock) -> None:
        import asyncio

        mock_codex.return_value = InvocationResult(
            model="codex", prompt="q", response="a", success=True, duration_seconds=1.0
        )
        mock_gemini.return_value = InvocationResult(
            model="gemini", prompt="q", response="b", success=True, duration_seconds=2.0
        )
        results = asyncio.run(invoke_all_parallel("question"))
        assert len(results) == 2
        models = [r.model for r in results]
        assert "codex" in models
        assert "gemini" in models

    @patch("mde.debate.invoke._invoke_codex")
    @patch("mde.debate.invoke._invoke_gemini")
    def test_saves_to_output_dir(
        self, mock_gemini: MagicMock, mock_codex: MagicMock, tmp_path: Path
    ) -> None:
        import asyncio

        mock_codex.return_value = InvocationResult(
            model="codex", prompt="q", response="a", success=True, duration_seconds=1.0
        )
        mock_gemini.return_value = InvocationResult(
            model="gemini", prompt="q", response="b", success=True, duration_seconds=2.0
        )
        asyncio.run(invoke_all_parallel("question", output_dir=tmp_path))
        assert (tmp_path / "codex.json").exists()
        assert (tmp_path / "gemini.json").exists()

    def test_unknown_model_returns_error(self) -> None:
        import asyncio

        results = asyncio.run(invoke_all_parallel("q", models=["unknown"]))
        assert len(results) == 1
        assert results[0].success is False
        assert "Unknown model" in (results[0].error or "")

    def test_claude_sonnet_return_errors(self) -> None:
        import asyncio

        results = asyncio.run(invoke_all_parallel("q", models=["claude", "sonnet"]))
        assert len(results) == 2
        assert all(not r.success for r in results)
        assert all("Agent tool" in (r.error or "") for r in results)


# ── Gemini JSON extraction ───────────────────────────────────────────────


class TestExtractGeminiJson:
    """Test gemini JSON output extraction."""

    def test_extracts_text_from_array(self) -> None:
        stdout = json.dumps([{"text": "Hello from Gemini"}])
        result = _extract_gemini_json(stdout)
        assert result == "Hello from Gemini"

    def test_extracts_text_from_object(self) -> None:
        stdout = json.dumps({"text": "Hello from Gemini"})
        result = _extract_gemini_json(stdout)
        assert result == "Hello from Gemini"

    def test_concatenates_multiple_parts(self) -> None:
        stdout = json.dumps([{"text": "Part 1"}, {"text": "Part 2"}])
        result = _extract_gemini_json(stdout)
        assert "Part 1" in result
        assert "Part 2" in result

    def test_falls_back_to_noise_strip_on_invalid_json(self) -> None:
        stdout = "Not JSON at all\nActual response here.\n"
        result = _extract_gemini_json(stdout)
        # Should fall back to _strip_gemini_noise
        assert "Actual response here." in result

    def test_handles_string_array(self) -> None:
        stdout = json.dumps(["response text"])
        result = _extract_gemini_json(stdout)
        assert result == "response text"

    def test_handles_response_key_in_object(self) -> None:
        stdout = json.dumps({"response": "Hello from Gemini"})
        result = _extract_gemini_json(stdout)
        assert result == "Hello from Gemini"

    def test_handles_empty_array(self) -> None:
        stdout = json.dumps([])
        result = _extract_gemini_json(stdout)
        assert result == "[]"  # Falls back to stdout.strip()

    def test_handles_empty_string(self) -> None:
        result = _extract_gemini_json("")
        assert isinstance(result, str)


# ── Gemini -o json flag in command ───────────────────────────────────────


class TestGeminiUsesJsonOutput:
    """Verify gemini invocation uses -o json flag."""

    @patch("mde.debate.invoke.subprocess.run")
    @patch("mde.debate.invoke.shutil.which", return_value="/usr/bin/gemini")
    def test_gemini_cmd_uses_json_output(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{"text": "test response"}]),
            stderr="",
        )
        from mde.debate.invoke import _invoke_gemini

        result = _invoke_gemini("test prompt")
        assert result.success is True
        assert result.response == "test response"

        # Verify the command includes -o json
        cmd = mock_run.call_args[0][0]
        assert "-o" in cmd
        json_idx = cmd.index("-o")
        assert cmd[json_idx + 1] == "json"


# ── Gemini env isolation ─────────────────────────────────────────────────


class TestGeminiIsolatedEnv:
    """Test gemini config isolation via system settings override."""

    def test_isolation_settings_file_created(self, tmp_path: Path) -> None:
        from mde.debate.invoke import _get_gemini_isolation_settings

        settings_dir = tmp_path / ".generated" / "gemini"
        settings_dir.mkdir(parents=True)
        # Patch Path.cwd() to return tmp_path
        with patch("mde.debate.invoke.Path.cwd", return_value=tmp_path):
            settings_path = _get_gemini_isolation_settings()
        assert settings_path.exists()
        data = json.loads(settings_path.read_text())
        assert data["admin"]["extensions"]["enabled"] is False
        assert data["admin"]["mcp"]["enabled"] is False

    def test_isolation_env_sets_system_settings_path(self) -> None:
        from mde.debate.invoke import _gemini_isolated_env

        env = _gemini_isolated_env()
        assert "GEMINI_CLI_SYSTEM_SETTINGS_PATH" in env
        assert env["GEMINI_CLI_SYSTEM_SETTINGS_PATH"].endswith("isolated-settings.json")

    @patch("mde.debate.invoke.subprocess.run")
    @patch("mde.debate.invoke.shutil.which", return_value="/usr/bin/gemini")
    def test_gemini_invocation_uses_isolated_env(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        _ = mock_which  # consumed by @patch decorator
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{"text": "response"}]),
            stderr="",
        )
        from mde.debate.invoke import _invoke_gemini

        _invoke_gemini("test")
        # Verify env kwarg contains isolation key
        call_kwargs = mock_run.call_args[1]
        env = call_kwargs.get("env", {})
        assert "GEMINI_CLI_SYSTEM_SETTINGS_PATH" in env
