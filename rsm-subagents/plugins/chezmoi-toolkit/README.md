# chezmoi-toolkit

Comprehensive chezmoi expertise for Claude Code: dotfile management, templates, secrets, migration, troubleshooting, AI agent config distribution, and source-first workflow enforcement.

## Components

### Agent

- **chezmoi-specialist** — Proactive dotfile management expert with 6 skills

### Skills (6)

| Skill | Purpose |
|-------|---------|
| chezmoi-config | Templates, externals, scripts, password managers, Go template syntax |
| chezmoi-workflows | Daily operations: add, sync, diff, apply, backup |
| chezmoi-troubleshooting | Doctor interpretation, state management, diff debugging |
| chezmoi-migration | Fresh install, import from stow/yadm/bare-git, one-shot mode |
| chezmoi-advanced-config | Monorepo, cleanup, git automation, age/GPG encryption |
| chezmoi-agent-config | AI agent config templating (CLAUDE.md, permissions, MCP, skills) |

### Hooks (2)

| Hook | Event | Purpose |
|------|-------|---------|
| guard-direct-dotfile-edit | PreToolUse:Bash | Block direct edits to managed dotfiles |
| remind-chezmoi-commit | PostToolUse:Bash | Remind to commit after chezmoi apply |

## Installation

```bash
claude --plugin-dir /path/to/chezmoi-toolkit
```

Or add to your marketplace configuration.

## Requirements

- [chezmoi](https://www.chezmoi.io/) installed (`brew install chezmoi`)
- Git for dotfile version control
- Optional: age for encryption, op (1Password CLI) for secrets
