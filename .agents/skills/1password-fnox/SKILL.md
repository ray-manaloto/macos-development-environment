---
name: 1password-fnox
description: Configure and validate 1Password-backed fnox secrets for this repo using the declarative mise + fnox contract. Use when enabling shared secrets with op:// refs, repairing 1Password auth, or migrating keychain-backed shared secrets into 1Password overlays.
---

# 1Password + fnox

Use this skill for 1Password-backed secret workflows in this repository.

## Load With

- `.agents/skills/mde-agent-runtime-contract/SKILL.md`
- `.agents/skills/mise-enforcement/SKILL.md`

## Authority

- Global CLI ownership: `/Users/rmanaloto/.config/mise/config.toml`
- Global fnox provider config: `/Users/rmanaloto/.config/fnox/config.toml`
- Global runtime secret file: `/Users/rmanaloto/.config/mise/secrets.sops.json`
- Repo shared declarations: `fnox.toml`
- Local gitignored overrides: `fnox.local.toml`
- Repo skill registry: `configs/mde-skill-registry.json`

Do not solve this workflow with ad hoc `export`, plaintext env files, or unmanaged `op read` shellouts in shell startup files.

## Runtime Model

- `mise` loads one encrypted SOPS file for terminal sessions.
- `fnox` remains the refresh and restore layer for provider-backed secrets.
- 1Password is the preferred cloud backup target for the encrypted SOPS file, not a second live runtime authority for the same keys.

## Expected Backend Split

- `keychain`: machine-local personal secrets
- `1password`: shared or team-managed secrets via explicit `op://...` references
- `age`: bootstrap or headless-safe secrets such as `OP_SERVICE_ACCOUNT_TOKEN`

## Workflow

1. Verify the `op` CLI is mise-managed and available:
   - `mise which op`
   - `mise ls 1password-cli`
2. Verify fnox providers exist:
   - `fnox providers`
   - inspect `/Users/rmanaloto/.config/fnox/config.toml` if needed
3. Verify 1Password auth:
   - interactive desktop flow: `eval "$(op signin)"`
   - service-account flow: `fnox get OP_SERVICE_ACCOUNT_TOKEN`
4. If the service-account token is missing, store it in the age provider:
   - `fnox set OP_SERVICE_ACCOUNT_TOKEN "ops_..." --provider age`
5. Discover the real secret references with `op item get ...` or `op read op://vault/item/field`.
6. Create or update `fnox.local.toml` with explicit `op://...` mappings for shared secrets.
7. Refresh the SOPS runtime file:
   - `scripts/mde-sops-secrets-refresh.sh`
8. Validate resolution:
   - `fnox get <KEY>`
   - `mise env -s bash | grep '^<KEY>='`
9. Back up the encrypted file to 1Password if required:
   - `scripts/mde-sops-secrets-backup-1password.sh`
10. Only after successful resolution, remove superseded shared keys from `keychain` if strict separation is required.

## Local Overlay Pattern

Use gitignored `fnox.local.toml` for machine-local 1Password refs:

```toml
[secrets]
GRAFANA_PASSWORD = { provider = "1password", value = "op://Vault/Item/password" }
GOOGLE_CLIENT_ID = { provider = "1password", value = "op://Vault/Item/client_id" }
GOOGLE_CLIENT_SECRET = { provider = "1password", value = "op://Vault/Item/client_secret" }
```

Keep repo-wide `fnox.toml` for shared declaration shape only when the URI is safe and intentionally committed.

## Verification

- `mise run mde:agent:preflight`
- `mise run mde:drift`
- `fnox get GRAFANA_PASSWORD`
- `zsh -i -c 'env | grep "^GRAFANA_PASSWORD="'`

## Prohibitions

- No plaintext `secrets.env`
- No secrets in `~/.oh-my-zsh/custom/*`
- No direct `op read ...` in shell startup files
- No unmanaged `brew install op` unless an exception workflow is explicitly being exercised
