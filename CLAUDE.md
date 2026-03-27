# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- `src/mde/hooks/` — Claude Code hook handlers (auto-discovered via `__hook_meta__`, never edit cli.py to add hooks)
- `src/mde/validate/` — Validators for configs, plugins, brew, docker
- `src/mde/research/` — Research pipeline CLI and clients
- `src/mde/domain/` — Pydantic domain models (some codegen'd — don't hand-edit `*_models.py`)
- `src/mde/codegen/` — Codegen postprocessors (run via `mise run mde:codegen:all`)
- `docs/schemas/` — JSON Schema sources for codegen (including official `claude-code-settings.schema.json`)
- `tests/` — pytest tests; `@pytest.mark.integration` for tests needing external tools
- `.claude/rules/` — Policy files loaded automatically (mise-first, no-shell-scripts, etc.)
- `.generated/` — Runtime artifacts, reports, logs, remember data (gitignored, never committed)
- `.remember` — Symlink to `.generated/remember/` (remember plugin compatibility)
- `rsm-subagents/` — Local plugin marketplace for Claude Code plugins

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
- Plugin validation (`uv run mde-py validate --plugins`) must produce 0 errors AND 0 warnings
- Unrelated errors encountered during work must be cataloged as GitHub Issues via `gh issue create`
- Before building any new tool/plugin/agent: search community plugins (`claude-plugins-community`), existing skills, and PyPI/npm first — build new is LAST RESORT
- Every candidate plugin/tool MUST be evaluated — never skip without explicit user approval. Write a verdict (INSTALL/EXTRACT/REJECT) with rationale for EACH candidate. Missing verdicts = incomplete work.
- ALWAYS invoke `/remember` before compaction, `/clear`, or session end — memory loss is permanent
- All runtime/transient data goes under `.generated/` — never create new artifact dirs at repo root

## Subagents

Defined in `.claude/agents/`. Use matching specialist types. Core: researcher (Haiku), coder, tester (pytest/ruff/ty), reviewer (Sonnet, read-only). Specialists: python-coder, mise-specialist, chezmoi-specialist, brew-specialist, security-auditor, claude-code-specialist, remember-specialist.

## Secrets

All secrets: **fnox (Keychain) -> mise (env) -> tools**. Set: `fnox set KEY --provider keychain --global`. Validate: `fnox list | grep KEY` (must show `provider (keychain)`). See `.claude/rules/secrets-management.md` for full guide.

## MCP Access

Use CLI wrappers, never MCP tool schemas in context:
- `mcp2cli @github <tool> [args]` for GitHub
- `mcp2cli @docker <tool> [args]` for Docker
- `npx agent-fetch "<url>" --json` for URL content (never WebFetch for research)

Subdirectory CLAUDE.md files can be added for module-specific instructions (e.g., `rsm-subagents/CLAUDE.md`).
