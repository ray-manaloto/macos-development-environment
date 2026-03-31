# CLAUDE.md

<!-- MANUAL -->
## Claude Code

### Subagents

Defined in `.claude/agents/`. Use matching specialist types. Core: researcher (Sonnet), coder, tester (pytest/ruff/ty), reviewer (Sonnet, read-only). Specialists: python-coder, mise-specialist, chezmoi-specialist, brew-specialist, security-auditor, claude-code-specialist, remember-specialist. Agents write discoveries to `$MDE_DIR_LEARNINGS` for dream pipeline consumption. All `.generated/` paths are managed via `MDE_*` env vars — see `.claude/rules/generated-paths.md`.

### Hooks

Auto-discovered in `src/mde/hooks/` via `__hook_meta__`. Never edit `cli.py` to add hooks. Policy files in `.claude/rules/` are loaded automatically. See `hooks-auto-discovery.md` for the convention. Key advisory hooks (all exit 0): `session-start` (SessionStart — prints recent git context + clears stale auto-memory dirty-files at session start, Issue #69), `check-knowledge` (PostToolUse — detects stale hook/test/subcommand counts in auto-memory and agent defs), `guard-debate` (PreToolUse — warns when raw codex/gemini CLI used instead of `mde debate`), `check-observability` (SessionStart — checks OTLP :4318/Grafana/Loki/Tempo health + Loki data arrival for all 5 services; port 13133 NOT exposed by grafana/otel-lgtm image), `dream-extract` (Stop — extracts patterns into dream pipeline), `remember-stop` (Stop — writes session context to `now.md`). Full telemetry validation: `uv run mde-py telemetry verify`.

### Plugins

Local marketplace at `rsm-subagents/` (7 plugins: mise-toolkit, chezmoi-toolkit, hk-toolkit, marketplace-evaluator, research-review-toolkit, devcontainer-toolkit, workflow-toolkit). Plugin validation (`uv run mde-py validate --plugins`) must produce 0 errors AND 0 warnings.

### Remember

`.remember` symlinks to `.generated/remember/`. ALWAYS invoke `/remember` before compaction, `/clear`, or session end — memory loss is permanent.

### Plugin/Tool Evaluation

Before building any new tool/plugin/agent: search community plugins (`claude-community` marketplace), existing skills, and PyPI/npm first — build new is LAST RESORT. Every candidate MUST be evaluated — never skip without explicit user approval.
<!-- END MANUAL -->

<!-- AUTO-MANAGED: project-description -->
## Overview

**mde** — Typed Python package for macOS development environment management. Entry point: `uv run mde-py <subcommand>`.

Universal instructions for all AI coding agents working in this repository. See [agents.md standard](https://agents.md/) for the specification this file follows.
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: build-commands -->
## Build & Development Commands

```bash
uv run mde-py quality          # Full quality gate (ruff + ty + pyright + vulture + import-linter + pytest)
uv run mde-py validate --all   # All validators (configs, brew, docker, plugins, skills, paths)
uv run mde-py validate --plugins  # Plugin validation only (zero warnings tolerance)
uv run mde-py validate --paths    # Path centralization checks (9 checks)
uv run pytest tests/ -v -m "not integration"  # Tests only
uv run ruff check src/mde/     # Lint only
uv run ruff format src/mde/    # Format only
uv run ty check src/mde/       # Type check only
mise fmt --check               # mise config formatting
```
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: architecture -->
## Architecture

- `src/mde/` — All automation lives here as Python modules (17 subpackages). **No shell scripts.**
- `src/mde/cli.py` — CLI dispatcher with lazy imports (26 subcommands)
- `src/mde/hooks/` — Claude Code hooks (22 handlers, auto-discovered via `__hook_meta__`)
- `src/mde/validate/` — Validators for configs, plugins, brew, docker, paths
- `src/mde/debate/` — Multi-model debate library (codex/gemini CLIs)
- `src/mde/dream/` — Self-improvement pipeline (extract/propose/apply/status); extract scans 6 sources: auto-memory, remember files, retro snapshots, hook feedback, learnings (`$MDE_DIR_LEARNINGS`), transcripts (`$MDE_DIR_TRANSCRIPTS`)
- `src/mde/secrets/` — Doppler/fnox secrets sync and validation
- `src/mde/research/` — Research pipeline CLI and clients
- `src/mde/lib/` — Shared utilities (`paths.py` MdePaths BaseSettings, logging)
- `src/mde/teams/` — Agent team coordination
- `src/mde/domain/` — Pydantic domain models (some codegen'd — don't hand-edit `*_models.py`)
- `src/mde/codegen/` — Codegen postprocessors (run via `mise run mde:codegen:all`)
- `docs/schemas/` — JSON Schema sources for codegen
- `tests/` — pytest tests; `@pytest.mark.integration` for tests needing external tools
- `.generated/` — Runtime artifacts via `MDE_*` env vars; use `from mde.lib.paths import get_paths`
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->
## Code Conventions

- **Commits**: conventional commits (`feat:`, `fix:`, `docs:`, `research:`)
- **Branches**: `feat/` prefix, worktree-based PR workflow — never merge to main for verification
- **Dependencies**: declare in `pyproject.toml` `[dependency-groups]` for dev, `[project.dependencies]` for runtime
- **Config**: all tool config in `pyproject.toml` — never standalone `.cfg`, `.ini`, or `.yaml`
- **Git hooks**: `hk.pkl` (managed by mise) — ruff fixers + quality gate on pre-commit
- **Imports**: use `from __future__ import annotations` and lazy imports in CLI paths
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: patterns -->
## Detected Patterns

- **Hook auto-discovery**: modules in `src/mde/hooks/` with `__hook_meta__` dict are auto-registered
- **Pydantic BaseSettings**: `MdePaths(BaseSettings)` for env-var-driven path config
- **Lazy CLI imports**: `cli.py` uses deferred imports for startup speed
- **Validator pattern**: each validator returns `(errors, warnings)` tuples; quality gate aggregates
- **Domain codegen**: JSON Schema → Pydantic models via `mde:codegen:all`
- **Dream promotion ladder**: patterns reach thresholds (MEMORY=1, DOCS=2, RULE/CLAUDE_MD=3, AGENT_DEF=5, HOOK/SKILL=10); AUTO tier applied without approval, APPROVE tier requires user review
<!-- END AUTO-MANAGED -->

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
