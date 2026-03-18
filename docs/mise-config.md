# mise Configuration

This project treats `mise` as the source of truth for host-level runtimes,
global CLIs, and SDK CLIs. Domain-specific project manifests remain native to
their ecosystems and are tracked through the domain catalog, preset catalog,
and tool bundles in this repository.

## Example

Create `~/.config/mise/config.toml`:

```toml
[tools]
python = "latest"
node = "latest"
bun = "latest"
go = "latest"
rust = "latest"
claude = "latest"

[tool_alias]
claude = "npm:@anthropic-ai/claude-code"

[env]
# Identity
GITHUB_USER = "your_username"

# Python toolchain behavior
UV_PYTHON_DOWNLOADS = "never"
UV_CACHE_DIR = "{{env.HOME}}/Library/Caches/uv"
PIXI_HOME = "{{env.HOME}}/.pixi"

# LangChain observability (non-secret)
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "agent-sandbox-local"

# Optional: force the claude shorthand to npm backend globally
# (tool_alias is usually enough)
# MISE_BACKENDS_CLAUDE = "npm:@anthropic-ai/claude-code"
```

## Notes
- Keep secrets out of Git repositories.
- Prefer `fnox` for global secrets:
  - `~/.config/mise/config.toml` owns the `fnox` binary and `fnox-env` plugin.
  - `~/.config/fnox/config.toml` is the global secret authority.
  - Export `MISE_ENV_CACHE=1` before `mise activate ...` so secret resolution uses mise env caching.
- Use per-project `.env` or `direnv` for repo-scoped secrets.
- Ensure mise shims are early in `PATH` (handled in oh-my-zsh custom config).
- Verify registry mapping with `mise registry claude`.
- Verify fnox mapping with `mise registry fnox`.
- Verify npm backend package manager with `mise settings get npm.package_manager`.
- Treat `configs/mde-domain-catalog.json` as the routing table for language and tool domains.
- Treat `configs/mde-reference-sources.json` plus `.artifacts/reference-mirror/` as the default research path for agent teams.
- Treat `configs/mde-preset-catalog.json` and `configs/tool-bundles/` as the repo-scoped starter bundle and preset contract.
- The Python `pixi/uv` domain defaults to a committed `pixi.toml` plus `pixi.lock` bundle under `configs/tool-bundles/python-pixi-uv/`; the domain team remains responsible for recording the supported realization path across `mise`, `pixi`, `uv`, and Python packaging.

## fnox Workflow
- Install or refresh the fnox stack with `mise install`.
- Runtime source of truth for shell sessions is the global SOPS file loaded by `mise`:
  - `~/.config/mise/secrets.sops.json`
  - loaded by `/Users/rmanaloto/.config/mise/config.toml` via `[env]._.file`
- Refresh the SOPS file from the current merged `fnox` secret set:
  - `scripts/mde-sops-secrets-refresh.sh`
- Restore the SOPS file back into local Keychain-backed `fnox` secrets:
  - `scripts/mde-sops-secrets-import-keychain.sh`
- Back up the encrypted SOPS file into 1Password as a Document item:
  - `scripts/mde-sops-secrets-backup-1password.sh`
- Store local personal secrets with the keychain provider:
  - `fnox set OPENAI_API_KEY "..." --provider keychain`
- Store the 1Password service account token with the age provider:
  - `fnox set OP_SERVICE_ACCOUNT_TOKEN "ops_..." --provider age`
- Use repo or local overlays for shared secrets:
  - `fnox.toml` for shared repo declarations
  - `fnox.local.toml` for gitignored local overrides
- Export `SOPS_AGE_KEY_FILE` before `mise activate` so shell startup can decrypt the file:
  - `SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/mise/age.txt}"`
- Optional tools:
  - `fnox tui` for local inspection
  - `fnox sync` for encrypted local caches of remote secrets
  - `fnox mcp` for allowlisted agent secret brokering
