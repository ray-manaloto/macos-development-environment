---
name: mise-jdx-ecosystem
description: >
  This skill should be used when the user asks about "pitchfork", "fnox", "hk git hooks",
  "usage CLI specs", "jdx tools", or mentions process management with mise, secrets
  management with fnox, git hooks with hk, or CLI argument parsing with usage. Also
  use when integrating multiple jdx tools together.
---

# jdx Ecosystem Integration

The jdx organization builds complementary tools that integrate with mise. Understanding
the ecosystem enables powerful declarative developer environments.

## Core Tools

### mise (26k stars) — Tool/Env/Task Manager
The hub. Manages tool versions, environment variables, and task runners.
All other jdx tools are installable via mise.

### hk (695 stars) — Git Hooks Manager
Pkl-based git hook configuration with auto-fix and profiles.

```bash
mise use -g hk                  # Install
hk install                      # Set up git hooks
hk check                        # Run all hook checks
hk fix                          # Auto-fix issues
```

Config: `hk.pkl` with pre-commit steps for linting, formatting, quality gates.
Features: `fix=true` (auto-fix), `stash="git"` (stash untracked), profiles (slow/fast).

### pitchfork (229 stars) — Daemon/Service Manager
Process management with ready checks, dependency graphs, and auto-start.

```bash
mise use -g pitchfork           # Install
pitchfork start postgres        # Start a daemon
pitchfork stop                  # Stop all daemons
pitchfork tui                   # Interactive dashboard
```

Config: `pitchfork.toml` with ready checks (HTTP, output match, delay),
dependency graphs, cron scheduling, and auto-start/stop on directory change.

### fnox (1.3k stars) — Secrets Manager
Encrypted/remote secrets with multi-provider support.

```bash
mise use -g fnox                # Install
fnox exec -- <cmd>              # Run command with secrets loaded
fnox activate bash              # Shell activation
fnox mcp                        # MCP server for AI agents
```

Providers: age, AWS KMS/SM, Azure KV, GCP SM, 1Password, Vault, Bitwarden, Keychain.
Config: `fnox.toml` with `[profiles]` for multi-environment secrets.

### usage (593 stars) — CLI Specification Format
Like OpenAPI but for CLI tools. Generates completions, docs, man pages.

```bash
mise use -g usage               # Install
usage generate completions      # Generate shell completions
usage generate docs             # Generate markdown docs
```

Used internally by mise for task argument parsing via the `usage` task property.

## Integration Patterns

### Declarative Dev Environment
```
mise.toml        → tools + env + tasks
hk.pkl           → git hooks (pre-commit, pre-push)
pitchfork.toml   → background services (postgres, redis, API)
fnox.toml        → secrets (API keys, DB passwords)
```

### New Developer Onboarding
```bash
git clone <repo>
mise trust && mise install      # Tools + env ready
hk install                      # Git hooks ready
pitchfork start                 # Services ready
```

### CI/CD Pipeline
```bash
mise install --locked           # Reproducible tool install
mise run test                   # Run task with env loaded
# fnox injects secrets via CI environment variables
```

## Anti-Patterns

- Don't use direnv alongside mise — PATH conflicts
- Don't use make alongside mise tasks — redundant orchestration
- Don't use pre-commit alongside hk — pick one hook manager
- Don't manage secrets in mise `[env]` when fnox is available
