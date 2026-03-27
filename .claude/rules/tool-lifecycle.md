# Tool Lifecycle Policy

## How tools are managed

All developer tools flow through a declarative pipeline:

```
chezmoi apply
  1. Brewfile.tmpl         → brew bundle    (casks, taps, brew-only)
  2. mise config.toml.tmpl → mise install   (190+ CLI tools)
  3. post-install script   → rtk init -g    (tools needing bootstrap after binary install)
  4. zsh custom files      → shell env      (PATH, aliases, completions)
```

Source of truth: `.chezmoisource/` in this repo, applied by `chezmoi apply`.

## Where to declare tools

| Tool type | Where to add | Example |
|-----------|-------------|---------|
| CLI binary (rust, go, node, python) | `.chezmoisource/dot_config/mise/config.toml.tmpl` `[tools]` | `rtk = "latest"` |
| npm global CLI | Same file, npm backend | `"npm:@openai/codex" = "latest"` |
| pipx global CLI | Same file, pipx backend | `"pipx:srclight" = "0.8.1"` |
| macOS GUI app / cask | `.chezmoisource/Brewfile.tmpl` | `cask "docker"` |
| Brew-only formula (no mise backend) | `.chezmoisource/Brewfile.tmpl` | `brew "llvm"` |
| Project-local tool | `.mise.toml` in repo root `[tools]` | `hk = "latest"` |
| Tool needing post-install init | `.chezmoisource/.chezmoiscripts/run_onchange_after_install_mise.sh.tmpl` | `rtk init -g` |

## Adding a new tool (checklist)

1. Check mise registry: `mise registry | grep <tool>`
2. If found: add to `config.toml.tmpl` under appropriate section with comment
3. If not found: check `mise registry <name>` for alternative backends (github:, aqua:, npm:, pipx:)
4. If no mise backend exists: add to `Brewfile.tmpl` (last resort per mise-first policy)
5. If tool needs post-binary-install bootstrap (e.g., `rtk init -g`): add to the post-install chezmoi script
6. Apply: `chezmoi apply` (or `chezmoi diff` to preview)
7. Verify: `mise ls <tool>` and `which <tool>`

## Removing a tool

1. Remove from `config.toml.tmpl` or `Brewfile.tmpl`
2. Run `chezmoi apply` to regenerate configs
3. Run `mise prune` to remove orphaned versions

## Backend priority

See `mise-first.md` for the canonical backend priority order and policies.

## What is NOT managed here

- Claude Code plugins: installed via `/plugin install` (stored in `~/.claude/plugins/`)
- Claude Code itself: native installer (`claude update`), not mise (see Issue #52)
- OAuth tokens: interactive auth (codex login, gemini) — expected manual step
- Secrets: Doppler -> fnox -> mise env (see secrets-management.md)

## Enforcement

- `guard-install` hook: warns when Bash commands use `brew install`, `npm -g`, `pip install`
- `uv run mde-py validate --all`: checks mise doctor output for issues
- `hk.pkl` pre-commit: runs full quality gate before every commit
- `.claude/rules/mise-first.md`: loaded into every Claude Code session
