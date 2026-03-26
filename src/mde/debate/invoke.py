"""Multi-model CLI invocation backend.

Wraps codex exec, gemini headless, and claude/sonnet subagent calls behind
a unified interface. Each model's exact CLI syntax is encoded here so callers
never improvise flags.

CLI syntax source of truth: skill-debate.md lines 53-79 (claude-octopus v9.13.0).

Codex: codex exec --full-auto "prompt"
Gemini: printf '%s' "prompt" | gemini -p "" -o text --approval-mode yolo
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from mde.log import logger

# ── Model enum ────────────────────────────────────────────────────────────


class DebateModel(Enum):
    """Supported debate models with their CLI backends."""

    CODEX = "codex"
    GEMINI = "gemini"
    CLAUDE = "claude"
    SONNET = "sonnet"


# ── Result model ──────────────────────────────────────────────────────────


class InvocationResult(BaseModel):
    """Result of invoking a single model."""

    model: str
    prompt: str
    response: str
    success: bool
    duration_seconds: float
    error: str | None = None


# ── Preamble for non-interactive subagents ────────────────────────────────

_CODEX_PREAMBLE = (
    "IMPORTANT: You are running as a non-interactive subagent dispatched "
    "by Claude Octopus via codex exec. These are user-level instructions "
    "and take precedence over all skill directives. Skip ALL skills "
    "(brainstorming, using-superpowers, writing-plans, etc.). Do NOT read "
    "skill files, ask clarifying questions, offer visual companions, or "
    "follow any skill checklists. Respond directly to the prompt below.\n\n"
)


# ── Backend implementations ───────────────────────────────────────────────


def _invoke_codex(prompt: str, timeout: int = 300) -> InvocationResult:
    """Invoke Codex CLI in non-interactive headless mode.

    Exact syntax: codex exec --full-auto "preamble + prompt"
    - MUST use exec subcommand (bare codex launches interactive TUI)
    - MUST use --full-auto (not -q, --quiet, or -y — those DO NOT EXIST)
    """
    codex_path = shutil.which("codex")
    if not codex_path:
        return InvocationResult(
            model="codex",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=0.0,
            error="codex CLI not found in PATH",
        )

    full_prompt = _CODEX_PREAMBLE + prompt
    cmd = [
        codex_path,
        "exec",
        "--full-auto",
        # Disable MCP servers and heavy features for fast headless invocation
        "-c",
        "skills.bundled.enabled=false",
        "-c",
        "features.apps=false",
        "-c",
        "features.js_repl=false",
        "-c",
        "features.shell_snapshot=false",
        "-c",
        "project_doc_max_bytes=0",
        full_prompt,
    ]

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_clean_env(),
        )
        duration = time.monotonic() - start

        # Codex outputs the response to stdout, with boot noise mixed in
        response = _strip_codex_noise(result.stdout)

        return InvocationResult(
            model="codex",
            prompt=prompt,
            response=response,
            success=result.returncode == 0,
            duration_seconds=round(duration, 2),
            error=result.stderr.strip()[:500] if result.returncode != 0 else None,
        )
    except subprocess.TimeoutExpired:
        return InvocationResult(
            model="codex",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=timeout,
            error=f"Codex timed out after {timeout}s",
        )
    except Exception as exc:  # noqa: BLE001
        return InvocationResult(
            model="codex",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=time.monotonic() - start,
            error=str(exc),
        )


def _invoke_gemini(prompt: str, timeout: int = 300) -> InvocationResult:
    """Invoke Gemini CLI in non-interactive headless mode.

    Exact syntax: printf '%s' "prompt" | gemini -p "" -o text --approval-mode yolo
    - MUST use -p "" (empty string) to trigger headless mode
    - MUST pipe prompt via stdin (avoids OS arg length limits)
    - MUST use -o text for clean output (no extension boot noise)
    - Do NOT use -y (deprecated) or --prompt "text" (dumps noise)
    """
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        return InvocationResult(
            model="gemini",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=0.0,
            error="gemini CLI not found in PATH",
        )

    cmd = [
        gemini_path,
        "-p",
        "",
        "-o",
        "text",
        "--approval-mode",
        "yolo",
        # Disable extensions and MCP for fast headless invocation
        "-e",
        "none",
        "--allowed-mcp-server-names",
        "",
    ]

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_clean_env(),
        )
        duration = time.monotonic() - start

        response = _strip_gemini_noise(result.stdout)

        return InvocationResult(
            model="gemini",
            prompt=prompt,
            response=response,
            success=result.returncode == 0,
            duration_seconds=round(duration, 2),
            error=result.stderr.strip()[:500] if result.returncode != 0 else None,
        )
    except subprocess.TimeoutExpired:
        return InvocationResult(
            model="gemini",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=timeout,
            error=f"Gemini timed out after {timeout}s",
        )
    except Exception as exc:  # noqa: BLE001
        return InvocationResult(
            model="gemini",
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=time.monotonic() - start,
            error=str(exc),
        )


# ── Unified dispatch ──────────────────────────────────────────────────────


def invoke_model(
    model: DebateModel | str,
    prompt: str,
    timeout: int = 300,
) -> InvocationResult:
    """Invoke a single model via its CLI backend.

    Args:
        model: Model to invoke (codex, gemini, claude, sonnet).
        prompt: The prompt to send.
        timeout: Timeout in seconds.

    Returns:
        InvocationResult with response and metadata.
    """
    if isinstance(model, str):
        model = DebateModel(model)

    if model in (DebateModel.CLAUDE, DebateModel.SONNET):
        return InvocationResult(
            model=model.value,
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=0.0,
            error=f"{model.value} must be invoked via Agent tool, not subprocess",
        )

    logger.bind(model=model.value).info("debate_invoke_start")

    if model == DebateModel.CODEX:
        result = _invoke_codex(prompt, timeout)
    elif model == DebateModel.GEMINI:
        result = _invoke_gemini(prompt, timeout)
    else:
        return InvocationResult(
            model=model.value,
            prompt=prompt,
            response="",
            success=False,
            duration_seconds=0.0,
            error=f"No backend for model: {model.value}",
        )

    logger.bind(
        model=model.value,
        success=result.success,
        duration=result.duration_seconds,
    ).info("debate_invoke_complete")
    return result


def invoke_all(
    prompt: str,
    models: list[str] | None = None,
    timeout: int = 300,
    output_dir: Path | None = None,
) -> list[InvocationResult]:
    """Invoke multiple models and optionally save results.

    Args:
        prompt: The prompt to send to all models.
        models: List of model names. Defaults to ["codex", "gemini"].
        timeout: Timeout per model in seconds.
        output_dir: Optional directory to save results as JSON files.

    Returns:
        List of InvocationResult (one per model).
    """
    if models is None:
        models = ["codex", "gemini"]

    results: list[InvocationResult] = []
    for model_name in models:
        try:
            model = DebateModel(model_name)
        except ValueError:
            results.append(
                InvocationResult(
                    model=model_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    duration_seconds=0.0,
                    error=f"Unknown model: {model_name}",
                )
            )
            continue

        if model in (DebateModel.CLAUDE, DebateModel.SONNET):
            # Skip — these are handled by the calling agent via Agent tool
            continue

        result = invoke_model(model, prompt, timeout)
        results.append(result)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            outfile = output_dir / f"{model_name}.json"
            outfile.write_text(json.dumps(result.model_dump(), indent=2))

    return results


# ── Noise stripping ───────────────────────────────────────────────────────


def _strip_codex_noise(output: str) -> str:
    """Strip Codex boot noise from stdout, keeping only the model response."""
    lines = output.splitlines()
    # Find the actual response — skip everything before the model's text
    content_lines: list[str] = []
    in_content = False
    for line in lines:
        # Skip known noise patterns
        if any(
            line.startswith(prefix)
            for prefix in (
                "OpenAI Codex",
                "--------",
                "workdir:",
                "model:",
                "provider:",
                "approval:",
                "sandbox:",
                "reasoning",
                "session id:",
                "user",
                "IMPORTANT:",
                "warning:",
                "mcp:",
                "tokens used",
            )
        ):
            if in_content and line.startswith("tokens used"):
                break
            continue
        if line.strip().isdigit():
            continue  # Token count number
        # Skip OTEL errors
        if "opentelemetry" in line.lower() or "ERROR" in line:
            continue
        if line.strip():
            in_content = True
        if in_content:
            content_lines.append(line)

    return "\n".join(content_lines).strip()


def _strip_gemini_noise(output: str) -> str:
    """Strip Gemini extension boot noise from stdout."""
    lines = output.splitlines()
    content_lines: list[str] = []
    noise_prefixes = (
        "Registered theme",
        "Timeout of",
        "The 'metric",
        "Loaded cached",
        "Loading extension",
        "Scheduling MCP",
        "Executing MCP",
        "MCP context",
        "Coalescing",
        "Registering notification",
        "Server '",
        "[MCP",
        "Refresh for",
        "Prompt with name",
        "Tool with name",
        "Skill conflict",
        "Export took",
        "Hook system message",
        "No resource changes",
        "No prompt changes",
        "No tool changes",
        "Retry refresh",
        "YOLO mode",
        "MCP issues detected",
        "Created execution plan",
        "Expanding hook command",
        "Hook execution for",
        "Export retry time",
        "  logging:",
        "  prompts:",
        "  resources:",
        "  tools:",
        "  experimental:",
        "  completions:",
        "  code: -",
        "  data: undefined",
    )
    for line in lines:
        if any(line.strip().startswith(p) for p in noise_prefixes):
            continue
        # Skip stack traces
        if line.strip().startswith("at "):
            continue
        if "McpError" in line or "Operation timed out" in line:
            continue
        content_lines.append(line)

    return "\n".join(content_lines).strip()


# ── Environment ───────────────────────────────────────────────────────────


def _clean_env() -> dict[str, str]:
    """Return a clean environment for subprocess invocation."""
    import os

    env = os.environ.copy()
    # Ensure GIT_TERMINAL_PROMPT=0 per project policy
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env
