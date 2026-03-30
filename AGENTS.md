# AGENTS.md

Universal instructions for all AI coding agents working in this repository.
See [agents.md standard](https://agents.md/) for the specification this file follows.

## Project

Typed Python package (`src/mde/`) managing macOS developer tooling. Entry point: `uv run mde-py <subcommand>`.

## Commands

```bash
uv run mde-py quality          # Full quality gate (ruff check + format + ty + pytest) — run before every commit
uv run mde-py validate --all   # All validators (configs, brew, docker, plugins, skills)
uv run mde-py validate --plugins  # Plugin validation only (zero warnings tolerance)
uv run pytest tests/ -v        # Tests only
uv run ruff check src/mde/     # Lint only
uv run ruff format src/mde/    # Format only
uv run ty check src/mde/       # Type check only
mise fmt --check               # mise config formatting
```

## Architecture

- `src/mde/` — All automation lives here as Python modules. **No shell scripts.**
- `src/mde/cli.py` — CLI dispatcher with lazy imports for startup speed (keep minimal, delegate to modules)
- `src/mde/hooks/` — Claude Code hook handlers (auto-discovered via `__hook_meta__`, never edit cli.py to add hooks); includes advisory `check-knowledge` (PostToolUse staleness detector), `check-observability` (SessionStart OTEL stack health check), `dream-extract`/`remember-stop` (Stop hooks), and `guard-debate` (PreToolUse debate integrity guard)
- `src/mde/debate/` — Multi-model debate library; wraps codex/gemini CLIs with output validation; use `mde debate` commands, never invoke codex/gemini directly
- `src/mde/validate/` — Validators for configs, plugins, brew, docker
- `src/mde/dream/` — Self-improvement pipeline; CLI: `auto-dream` (extract/propose/apply/status) with promotion ladder and tiered autonomy; extract scans 5 signal sources: auto_memory, remember, retro, hook_feedback, learnings
- `src/mde/research/` — Research pipeline CLI and clients
- `src/mde/domain/` — Pydantic domain models (some codegen'd — don't hand-edit `*_models.py`)
- `src/mde/codegen/` — Codegen postprocessors (run via `mise run mde:codegen:all`)
- `docs/schemas/` — JSON Schema sources for codegen (including official `claude-code-settings.schema.json`)
- `tests/` — pytest tests; `@pytest.mark.integration` for tests needing external tools
- `.generated/` — Runtime artifacts, reports, logs, remember data (gitignored, never committed)

## Conventions

- **Commits**: conventional commits (`feat:`, `fix:`, `docs:`, `research:`)
- **Branches**: `feat/` prefix, worktree-based PR workflow — never merge to main for verification
- **Dependencies**: declare in `pyproject.toml` `[dependency-groups]` for dev, `[project.dependencies]` for runtime
- **Config**: all tool config in `pyproject.toml` — never standalone `.cfg`, `.ini`, or `.yaml`
- **Git hooks**: `hk.pkl` (managed by mise) — ruff fixers + quality gate on pre-commit
- **Imports**: use `from __future__ import annotations` and lazy imports in CLI paths

## Enforcement (zero tolerance)

- All warnings from `uv run mde-py quality` must be fixed — never skip or dismiss
- All tools must be in mise config — never install via brew/npm/pip if mise can manage it
- All automation must be Python in `src/mde/` — never create `.sh` files
- Never use `uv run python` — use `uv run <entry-point>` or `uv run <tool>`
- Unrelated errors encountered during work must be cataloged as GitHub Issues via `gh issue create`
- All runtime/transient data goes under `.generated/` — never create new artifact dirs at repo root

## Secrets

All secrets: **Doppler (source of truth) -> sync -> fnox (Keychain cache) -> mise (env) -> tools**. New secrets: `doppler secrets set KEY=VAL --project dotfiles --config dev`, then `uv run mde-py secrets sync`. Validate: `uv run mde-py secrets validate`. See `.claude/rules/secrets-management.md` for full guide.

## MCP Access

Use CLI wrappers, never MCP tool schemas in context:
- `mcp2cli @github <tool> [args]` for GitHub
- `mcp2cli @docker <tool> [args]` for Docker
- `mcp2cli @exa <tool> [args]` for web search (Exa)
- `npx agent-fetch "<url>" --json` for URL content (never WebFetch for research)
