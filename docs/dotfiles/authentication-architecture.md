# Authentication Architecture

How secrets, SSH keys, and credentials flow through the macOS development environment.

## Secrets Pipeline

```
Doppler (cloud source of truth)
  |
  v
uv run mde-py secrets sync
  |
  v
fnox (macOS Keychain cache, works offline)
  |
  v
mise env (_.fnox-env = { tools = true })
  |
  v
Tools, .mcp.json, shell sessions
```

### Layer 1: Doppler

All secrets originate in Doppler (project: `dotfiles`, config: `dev`).

```bash
# Add a new secret
doppler secrets set KEY=VALUE --project dotfiles --config dev

# Read a secret
doppler secrets get KEY --project dotfiles --config dev --plain
```

Doppler is the canonical source. Never add secrets directly to fnox, `.env` files,
shell profiles, or mise `[env]` blocks.

### Layer 2: fnox + macOS Keychain

`fnox` caches Doppler secrets in macOS Keychain (encrypted, works offline).

```bash
# Sync Doppler -> Keychain
uv run mde-py secrets sync

# Read from local cache
fnox get KEY

# List all cached secrets
fnox list
```

One exception: `OP_SERVICE_ACCOUNT_TOKEN` uses the `age` provider (encrypted in
`fnox.toml`) instead of Keychain. This secret bootstraps 1Password access and
cannot depend on online services.

### Layer 3: mise Environment

mise loads fnox secrets into the shell environment via the `fnox-env` plugin:

```toml
# ~/.config/mise/config.toml (managed by chezmoi)
[plugins]
fnox-env = "https://github.com/jdx/mise-env-fnox"

[env]
_.fnox-env = { tools = true }
```

Every new shell session gets all fnox-cached secrets as environment variables.
Tools like `gh`, `aws`, and MCP servers read their API keys from these variables.

### Layer 4: MCP Server Secrets

`.mcp.json` references secrets using `${VAR_NAME}` syntax. mise resolves these
from the fnox-backed environment at shell init:

```json
{
  "mcpServers": {
    "exa": {
      "env": {
        "EXA_API_KEY": "${EXA_API_KEY}"
      }
    }
  }
}
```

### Layer 5: chezmoi Templates

chezmoi can resolve Doppler secrets directly in templates via the `[doppler]`
config in `~/.config/chezmoi/chezmoi.toml`:

```toml
[doppler]
  project = "dotfiles"
  config = "dev"
```

Templates use `{{ doppler "KEY" }}` for secrets that must be baked into managed
files at `chezmoi apply` time (rare — most secrets flow through mise env instead).

## SSH Authentication

### Key Strategy

One SSH key per machine, stored in `~/.ssh/id_ed25519`.

```
~/.ssh/config (managed by chezmoi):
  # OrbStack SSH host override (must precede all Host blocks)
  Include ~/.orbstack/ssh/config

  # SkyPilot cluster SSH configs
  Include ~/.sky/generated/ssh/*

  Host github.com
    AddKeysToAgent yes
    UseKeychain yes
    IdentityFile ~/.ssh/id_ed25519
```

`UseKeychain yes` persists the passphrase in macOS Keychain so it survives reboots.
`AddKeysToAgent yes` loads the key into `ssh-agent` on first use.

### 1Password SSH Agent (darwin)

On macOS, 1Password can act as the SSH agent, serving keys stored in vaults:

- Keys live in 1Password vaults (one key per vault/machine class)
- The 1Password SSH agent serves keys to `ssh-agent` transparently
- `IdentityAgent` in SSH config points to the 1Password agent socket

This is an optional enhancement. The baseline setup uses a local `~/.ssh/id_ed25519`
key with Keychain passphrase caching.

## GitHub Authentication

Two authentication paths serve different protocols:

### SSH (git clone, push, pull)

```
ssh-agent (or 1Password SSH agent)
  -> ~/.ssh/id_ed25519
  -> github.com Host block in SSH config
```

Verify: `ssh -T git@github.com`

### HTTPS (gh CLI, API access)

```
gh auth login
  -> stores OAuth token in gh config
  -> git credential helper delegates to gh
```

The `.gitconfig` template wires this up:

```gitconfig
[credential "https://github.com"]
    helper =
    helper = !~/.local/share/mise/shims/gh auth git-credential

[credential "https://gist.github.com"]
    helper =
    helper = !~/.local/share/mise/shims/gh auth git-credential
```

The empty `helper =` line clears any prior credential helpers, ensuring `gh` is
the sole handler for GitHub HTTPS auth.

### GITHUB_TOKEN vs GITHUB_MCP_PAT

Two distinct tokens serve different scopes:

| Token | Purpose | Stored In |
|-------|---------|-----------|
| `GITHUB_TOKEN` | General GitHub API access (gh CLI, mise) | Doppler -> fnox -> Keychain |
| `GITHUB_MCP_PAT` | MCP server GitHub operations (scoped permissions) | Doppler -> fnox -> Keychain |

`MISE_GITHUB_TOKEN` is set conditionally on work machines to avoid GitHub API
rate limiting during `mise install`. On personal machines, the default
`GITHUB_TOKEN` suffices.

## Cloud Provider Auth

### AWS

```
AWS_ACCESS_KEY_ID      -> Doppler -> fnox -> mise env
AWS_SECRET_ACCESS_KEY  -> Doppler -> fnox -> mise env
AWS_DEFAULT_REGION     -> Doppler -> fnox -> mise env
```

The `aws-cli` tool in mise reads these environment variables directly.

### Azure

```
[credential "https://dev.azure.com"]
    useHttpPath = true
```

Azure DevOps uses `git-credential-manager` (GCM) for HTTPS auth, configured in
`.gitconfig` with `useHttpPath = true` for multi-org support.

## Secrets Inventory

Run `doppler secrets --project dotfiles --config dev` for the canonical list.

| Category | Keys | Notes |
|----------|------|-------|
| LLM APIs | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Subscription-based CLI tools |
| MCP Servers | `EXA_API_KEY`, `CONTEXT7_API_KEY` | Referenced as `${VAR}` in .mcp.json |
| GitHub | `GITHUB_TOKEN`, `GITHUB_MCP_PAT` | Distinct scopes |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_*_REGION` | CLI credentials |
| Observability | `OTEL_*`, `GRAFANA_*`, `LOKI_*`, `MIMIR_*`, `TEMPO_*` | Telemetry endpoints |
| LangSmith | `LANGSMITH_API_KEY`, `LANGSMITH_WORKSPACE_ID` | Agent tracing |
| Bootstrap | `OP_SERVICE_ACCOUNT_TOKEN` | age-encrypted, not in Doppler |

## Validation

```bash
# Full parity check: Doppler vs fnox
uv run mde-py secrets validate

# Quick check: is a secret available?
fnox get KEY
mise env | grep KEY

# Verify GitHub SSH auth
ssh -T git@github.com

# Verify GitHub HTTPS auth
gh auth status
```

## Adding a New Secret

1. Add to Doppler: `doppler secrets set KEY=VALUE --project dotfiles --config dev`
2. Sync to Keychain: `uv run mde-py secrets sync`
3. Validate: `uv run mde-py secrets validate`
4. Use in tools: reference as `$KEY` in shell or `${KEY}` in `.mcp.json`

Never add secrets to fnox without adding to Doppler first. The sync is
one-directional: Doppler -> fnox.

## Security Properties

- **At rest**: macOS Keychain (AES-256), age encryption for bootstrap secrets
- **In transit**: Doppler API (TLS), chezmoi template resolution (local)
- **No plaintext**: secrets never appear in git, `.env` files, or shell history
- **Offline capable**: fnox Keychain cache works without network access
- **Auditable**: `doppler audit` for cloud access logs, `fnox list` for local inventory
