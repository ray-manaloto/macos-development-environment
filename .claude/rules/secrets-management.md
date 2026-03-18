---
description: Enforce tiered secrets management
globs: ["scripts/*.sh", "fnox.toml", ".env*"]
---

# Secrets Management

- Tier 1 (local): fnox + macOS Keychain + age encryption
- Tier 2 (cloud): Doppler Free or 1Password (optional)
- Tier 3 (backup): age + sops for git-safe encrypted values
- NEVER commit plaintext secrets
- Use `mde_load_secrets` in scripts needing secrets
- fnox MCP for AI agent access: `fnox mcp`
