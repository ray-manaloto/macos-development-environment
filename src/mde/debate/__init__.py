"""Multi-model debate CLI — unified interface for codex, gemini, and sonnet invocation.

Built using CLI-Anything methodology: wraps the real CLI backends (codex exec,
gemini headless, claude subagent) behind a single consistent interface so agents
never have to remember per-CLI flags.

Usage:
    uv run mde-py debate "question" --model codex
    uv run mde-py debate "question" --model gemini
    uv run mde-py debate "question" --model all --output-dir debates/

Source of truth for CLI syntax: skill-debate.md lines 53-79 in claude-octopus.
"""
