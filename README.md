# macos-development-environment

Typed Python package for managing macOS developer tooling — tool lifecycle, secrets, validation, and multi-model AI workflows.

## Quickstart

```bash
# Install dependencies
uv sync

# Run quality gate (ruff + ty + pytest)
uv run mde-py quality

# Validate all configs
uv run mde-py validate --all

# Apply dotfiles
chezmoi apply
```

## Architecture

All automation is Python in `src/mde/`. Entry point: `uv run mde-py <subcommand>`.

```
src/mde/
  cli.py          — CLI dispatcher (lazy imports)
  hooks/          — Claude Code hook handlers (auto-discovered)
  debate/         — Multi-model debate library (codex, gemini, claude)
  validate/       — Config, plugin, brew, docker validators
  dream/          — Self-improvement pipeline (extract/propose/apply)
  research/       — Research pipeline and clients
  domain/         — Pydantic domain models
  codegen/        — Schema-driven code generation
```

## Tool Management

Tools flow through a declarative pipeline managed by [chezmoi](https://chezmoi.io):

1. `Brewfile.tmpl` — brew bundle (casks, taps, brew-only formulas)
2. `mise config.toml.tmpl` — mise install (190+ CLI tools)
3. Post-install script — tools needing bootstrap after binary install
4. zsh custom files — PATH, aliases, completions

Source of truth: `home/` directory, applied by `chezmoi apply`.

## Secrets

Doppler (cloud) -> fnox (macOS Keychain cache) -> mise (env vars) -> tools.

```bash
doppler secrets set KEY=VAL --project dotfiles --config dev
uv run mde-py secrets sync
uv run mde-py secrets validate
```

## AI Agent Integration

This repo is designed for multi-agent collaboration:

- **AGENTS.md** — Universal instructions for all AI coding agents ([agents.md standard](https://agents.md/))
- **CLAUDE.md** — Claude Code-specific additions (hooks, plugins, subagents)
- `.claude/agents/` — Subagent definitions (researcher, coder, tester, reviewer)
- `.claude/rules/` — Policy files loaded automatically into every session
- `rsm-subagents/` — Local plugin marketplace (7 plugins)
- `src/mde/debate/` — Multi-model adversarial review (codex + gemini + claude)

## Key Commands

| Command | Description |
|---------|-------------|
| `uv run mde-py quality` | Full quality gate (6 checks) |
| `uv run mde-py validate --all` | All validators |
| `uv run mde-py validate --plugins` | Plugin validation (zero tolerance) |
| `uv run mde-py auto-dream status` | Self-improvement pipeline status |
| `uv run mde-py debate "prompt"` | Multi-model debate |
| `uv run mde-py secrets validate` | Doppler/fnox parity check |
| `uv run mde-py research status` | Research pipeline status |

## Development

```bash
uv run pytest tests/ -v       # Run tests
uv run ruff check src/mde/    # Lint
uv run ruff format src/mde/   # Format
uv run ty check src/mde/      # Type check
```

Conventions: conventional commits, `feat/` branch prefix, worktree-based PR workflow.

## License

Private repository.
