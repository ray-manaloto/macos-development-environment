---
description: Enforce Doppler-first secrets management
globs: ["scripts/*.sh", "fnox.toml", ".env*", ".mcp.json", "src/mde/secrets/*.py"]
---

# Secrets Management

## Architecture

All secrets flow through: **Doppler (source of truth) -> sync -> fnox (Keychain cache) -> mise (env) -> tools**

1. **Doppler** (project: `dotfiles`, config: `dev`) stores canonical secrets in the cloud
2. **`uv run mde-py secrets sync`** pulls Doppler secrets into fnox/Keychain
3. **fnox** caches secrets in macOS Keychain (encrypted, works offline)
4. **mise** loads them via `_.fnox-env = { tools = true }` in `~/.config/mise/config.toml`
5. **`.mcp.json`** and other configs reference them as `${VAR_NAME}` — mise resolves at shell init
6. **chezmoi** manages the mise config file AND has `[doppler]` config for template functions
7. **chezmoi templates** can use `{{ doppler "KEY" }}` to resolve secrets directly

## Adding a new secret

```bash
# 1. Add to Doppler (source of truth)
doppler secrets set KEY=VALUE --project dotfiles --config dev

# 2. Sync to local Keychain
uv run mde-py secrets sync

# 3. Validate parity
uv run mde-py secrets validate
```

## Reading a secret

```bash
doppler secrets get KEY --project dotfiles --config dev --plain   # From Doppler
fnox get KEY                                                       # From local Keychain
mise env | grep KEY                                                # From mise env
chezmoi execute-template '{{ doppler "KEY" }}'                     # From chezmoi template
```

## Validating secrets

```bash
uv run mde-py secrets validate    # Compare Doppler vs fnox parity
fnox list | grep KEY               # Check local provider is (keychain)
doppler secrets ls --project dotfiles --config dev | grep KEY      # Check Doppler has it
```

## One-time migration (already done)

```bash
uv run mde-py secrets export      # fnox -> Doppler (40 secrets migrated)
uv run mde-py secrets validate    # Verify parity
```

## Current secrets inventory

Run `doppler secrets ls --project dotfiles --config dev` for the canonical list.
Key categories:
- **LLM API keys**: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
- **MCP server keys**: EXA_API_KEY
- **Cloud/infra**: AWS_*, GITHUB_TOKEN, GITHUB_MCP_PAT
- **Observability**: OTEL_*, GRAFANA_*, LOKI_*, MIMIR_*, TEMPO_*
- **Age-encrypted**: OP_SERVICE_ACCOUNT_TOKEN (fnox provider: age, not in Doppler)

## Rules

- NEVER commit plaintext secrets — use Doppler + fnox/Keychain
- NEVER add secrets directly to fnox without also adding to Doppler
- NEVER add secrets to `.env` files, shell profiles, or mise `[env]` blocks
- `.mcp.json` secrets use `${VAR_NAME}` syntax — mise resolves them from fnox/Keychain
- New secrets go to Doppler FIRST, then `uv run mde-py secrets sync`
- For AI agent access to secrets: `fnox mcp`
- Backup tier: age + sops for git-safe encrypted values (fnox.toml with `provider (age)`)
- Doppler meta keys (DOPPLER_CONFIG, DOPPLER_ENVIRONMENT, DOPPLER_PROJECT) are auto-injected and excluded from parity validation
