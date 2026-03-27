---
description: Enforce tiered secrets management
globs: ["scripts/*.sh", "fnox.toml", ".env*", ".mcp.json"]
---

# Secrets Management

## Architecture

All secrets flow through a single chain: **fnox (Keychain) -> mise (env) -> tools (.mcp.json, scripts)**

1. **fnox** stores secrets in macOS Keychain (encrypted, never plaintext on disk)
2. **mise** loads them via `_.fnox-env = { tools = true }` in `~/.config/mise/config.toml`
3. **`.mcp.json`** and other configs reference them as `${VAR_NAME}` — mise resolves at shell init
4. **chezmoi** manages the mise config file, ensuring `_.fnox-env` persists across machines
5. **chezmoi apply** does NOT affect Keychain entries — secrets survive config reapplication

## Setting a new secret

```bash
# CORRECT: stores in macOS Keychain, available globally via mise
fnox set SECRET_NAME --provider keychain --global

# WRONG: stores as local "stored value", not in Keychain
fnox set SECRET_NAME  # Missing --provider keychain --global
```

Always use `--provider keychain --global` to ensure the secret is:
- Stored in macOS Keychain (encrypted, survives reboots and chezmoi apply)
- Available globally (not scoped to a single project's fnox.toml)
- Loaded by mise automatically via `_.fnox-env = { tools = true }`

## Getting/reading a secret

```bash
fnox get SECRET_NAME            # Print the value from fnox
mise env | grep SECRET_NAME     # Verify mise resolves it
mise exec -- bash -c 'echo $SECRET_NAME'  # Test in a fresh mise shell
```

## Validating secrets are correctly configured

```bash
# 1. Check fnox has it as provider (keychain), NOT "stored value"
fnox list | grep SECRET_NAME
# Expected: SECRET_NAME  provider (keychain)  SECRET_NAME
# Bad:      SECRET_NAME  stored value

# 2. Check mise loads it
mise env | grep SECRET_NAME
# Expected: export SECRET_NAME=<value>

# 3. Check it's in macOS Keychain directly
security find-generic-password -s "SECRET_NAME" -w 2>/dev/null && echo "IN KEYCHAIN" || echo "NOT IN KEYCHAIN"

# 4. Test in a fresh shell (current session may be stale)
mise exec -- bash -c 'echo "SECRET_NAME=$SECRET_NAME"'
```

## Fixing a mistyped secret (stored value instead of keychain)

```bash
fnox remove SECRET_NAME                              # Remove local entry
fnox set SECRET_NAME --provider keychain --global     # Re-add to Keychain
fnox list | grep SECRET_NAME                          # Verify: provider (keychain)
```

## Current secrets inventory

Run `fnox list` to see all secrets. Keychain-backed entries show `provider (keychain)`.
Key categories:
- **LLM API keys**: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
- **MCP server keys**: EXA_API_KEY (used by `.mcp.json`)
- **Cloud/infra**: AWS_*, GITHUB_TOKEN, GITHUB_MCP_PAT
- **Observability**: OTEL_*, GRAFANA_*, LOKI_*, MIMIR_*, TEMPO_*
- **Age-encrypted**: OP_SERVICE_ACCOUNT_TOKEN (provider: age)

## Rules

- NEVER commit plaintext secrets — use fnox + Keychain
- NEVER use `fnox set KEY` without `--provider keychain --global`
- NEVER add secrets to `.env` files, shell profiles, or mise `[env]` blocks
- `.mcp.json` secrets use `${VAR_NAME}` syntax — mise resolves them from fnox/Keychain
- For AI agent access to secrets: `fnox mcp`
- Backup tier: age + sops for git-safe encrypted values (fnox.toml with `provider (age)`)
