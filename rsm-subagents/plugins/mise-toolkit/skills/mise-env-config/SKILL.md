---
name: mise-env-config
description: >
  This skill should be used when the user asks to "configure environment variables",
  "set up mise env", "add env vars to mise.toml", "use _.file for secrets",
  "set up redact", "configure multi-environment", or mentions mise [env] section,
  mise set/unset, _.file, _.path, _.python.venv, or secrets in mise config.
---

# Mise Environment Configuration

Manage environment variables, secrets, and multi-environment setups through mise's `[env]` section.

## Core Commands

```bash
mise set KEY=VALUE              # Set env var in mise.toml
mise set -g KEY=VALUE           # Set global env var
mise unset KEY                  # Remove env var
mise env                        # Show active env vars
mise env --json                 # JSON output for agent consumption
```

## [env] Section Patterns

### Basic Variables

```toml
[env]
NODE_ENV = "development"
DATABASE_URL = "postgresql://localhost/mydb"
```

### Secrets with Redaction

```toml
[env]
_.file = { path = ".env.secrets", redact = true }
```

The `redact = true` flag hides values from `mise env` output and logs.

### Path Manipulation

```toml
[env]
_.path = ["./node_modules/.bin", "./scripts"]   # Prepend to PATH
```

### Python Virtual Environment

```toml
[env]
_.python.venv = { path = ".venv", create = true }
```

## Multi-Environment Support

Use `mise.<ENV>.toml` files for environment-specific config:

```bash
mise -E production run deploy    # Load mise.production.toml
mise -E staging run test         # Load mise.staging.toml
```

```toml
# mise.production.toml
[env]
_.file = { path = ".env.production", redact = true }
NODE_ENV = "production"
```

## Integration with fnox

For advanced secrets management, use fnox (jdx's secrets manager):

```toml
[env]
_.file = "fnox exec --env-file"   # Load secrets from fnox
```

See the **mise-jdx-ecosystem** skill for fnox integration details.

## Anti-Patterns

- Never hardcode secrets in `[env]` — use `_.file` with `redact = true`
- Never commit `.env.secrets` or `.env.production` — add to `.gitignore`
- Task-level `env = {}` does NOT propagate to `depends` tasks
- Use `mise env --json` for agent consumption, not `mise env` (which exposes secrets)

## Validation

```bash
mise doctor          # Check env configuration health
mise env --json      # Verify vars are set correctly
```
