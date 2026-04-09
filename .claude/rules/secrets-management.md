---
description: Enforce Doppler-first secrets management
globs: ["scripts/*.sh", "fnox.toml", ".env*", ".mcp.json", "src/mde/secrets/*.py"]
---

# Secrets Management

See [`docs/secrets-workflow.md`](../../docs/secrets-workflow.md) for the full
architecture, diagrams, recovery runbooks, and age key rotation procedure.

## Architecture (one line)

`Doppler (dotfiles/dev_personal) → fnox sync --provider age --global → ~/.config/fnox/config.toml → fnox activate zsh hooks → shell env`

Only two pieces of state live on the local machine:

1. **`DOPPLER_TOKEN`** in macOS Keychain (the bootstrap secret).
2. **`~/.config/mise/age.txt`** (0600) — the age private key, mirrored in
   Doppler as `AGE_PRIVATE_KEY` so a fresh machine can recover.

Everything else is encrypted ciphertext inside `~/.config/fnox/config.toml`,
re-derived from Doppler on every `mde-py secrets sync`.

## Adding / updating a secret

```bash
echo 'value' | uv run mde-py secrets add KEY        # stdin (preferred)
uv run mde-py secrets update KEY --value 'value'    # explicit flag
```

The CLI writes Doppler first, then runs `fnox sync --provider age --global --force`,
then prints `export KEY='value'` to stdout so the zsh wrapper can eval it into
the current shell.

## Removing a secret

```bash
uv run mde-py secrets rm KEY
```

Deletes from Doppler, re-runs `fnox sync` (which drops the orphaned entry), and
prints `unset KEY` to stdout.

## Reading / validating

```bash
doppler secrets get KEY --project dotfiles --config dev_personal --plain
fnox get KEY                                  # local age-decrypted cache
uv run mde-py secrets validate                # fnox sync --dry-run drift check
uv run mde-py secrets doctor                  # full health check
```

## Fresh-machine bootstrap

```bash
fnox set DOPPLER_TOKEN <value> --provider keychain --global
export DOPPLER_TOKEN=$(fnox get DOPPLER_TOKEN)
doppler secrets get AGE_PRIVATE_KEY --plain \
  --project dotfiles --config dev_personal > ~/.config/mise/age.txt
chmod 600 ~/.config/mise/age.txt
uv run mde-py secrets bootstrap-config
uv run mde-py secrets sync
```

Full runbook (including loss-of-token recovery): [`docs/secrets-workflow.md`](../../docs/secrets-workflow.md).

## Rules

- NEVER commit plaintext secrets — Doppler is the source of truth.
- NEVER add a secret directly to fnox/Keychain without going through Doppler first.
- NEVER add secrets to `.env` files, shell profiles, or mise `[env]` blocks.
- NEVER declare a secret in repo `fnox.toml` that the global config owns —
  repo overlays shadow global, which silently breaks the new architecture.
- New secrets go through `mde-py secrets add` (Doppler first, sync second).
- `.mcp.json` references secrets as `${VAR_NAME}` — fnox/mise resolves at shell init.
- Doppler meta keys (DOPPLER_CONFIG, DOPPLER_ENVIRONMENT, DOPPLER_PROJECT) are
  auto-injected and excluded from parity validation.
- 1Password and SOPS providers have been removed (subscription expired,
  redundant with age). Do not reintroduce them without an architecture review.
