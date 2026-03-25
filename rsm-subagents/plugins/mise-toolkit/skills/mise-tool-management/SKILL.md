---
name: mise-tool-management
description: >
  This skill should be used when the user asks to "add a tool to mise", "install a new
  CLI tool", "choose a mise backend", "search the mise registry", "detect tool drift",
  or mentions mise tool installation, backend selection, GIT_TERMINAL_PROMPT enforcement,
  or adding new dependencies to mise config.
---

# Mise Tool Management

## Backend Selection Decision Tree

When adding a new tool, choose the backend in this priority order:

1. **Registry shortname** — `mise registry | grep <tool>`. If found, use it.
2. **aqua:** — Pre-built binaries with SLSA/cosign verification. Preferred for CLIs.
3. **github:** — GitHub Releases (replaces deprecated `ubi:`).
4. **pipx:** — Python CLI tools from PyPI or git. Supports `extras`.
5. **npm:** — Node.js CLI tools. Uses bun via `npm.package_manager = "bun"`.
6. **cargo:** — Rust crates.
7. **go:** — Go tools. Requires Go runtime.

### Deprecated (do NOT use)
- `ubi:` — Use `github:` instead.

## How to Add a New Tool

1. Check registry: `mise registry | grep <tool>`
2. Choose optimal backend (see above)
3. Add to `.chezmoisource/dot_config/mise/config.toml.tmpl` under `[tools]`
4. Run `chezmoi apply` to deploy config
5. Run `mise install --yes && mise lock && mise reshim`

## Aqua Backend Discovery

For tools not in the mise registry, check aqua:
```bash
# Verify aqua backend availability
mise ls-remote "aqua:<org>/<repo>"

# Examples of aqua-discovered tools:
# buildkit:              mise ls-remote "aqua:moby/buildkit"
# session-manager-plugin: mise ls-remote "aqua:aws/session-manager-plugin"
# docker CLI:            mise ls-remote "aqua:docker/cli"
# docker-compose:        mise ls-remote "aqua:docker/compose"
```

## GitHub Backend Discovery

For tools distributed via GitHub Releases:
```bash
# Verify github backend availability
mise ls-remote "github:<org>/<repo>"

# Examples:
# docker-agent:  mise ls-remote "github:docker/docker-agent"
# xcodegen:      mise ls-remote "github:yonaskolb/XcodeGen"
```

## Bun/uv Global Cleanup

When migrating globals to mise:
```bash
# List bun globals that may duplicate mise
ls ~/.bun/install/global/node_modules/

# Remove specific bun global duplicate
bun remove -g <package>

# List uv tools that may duplicate mise
uv tool list

# Remove specific uv tool duplicate
uv tool uninstall <package>
```

## Drift Detection

- `mise outdated` — check version drift
- `mise doctor` — health checks
- No `~/package.json` (breaks bun hoisting)
- All config tools installed: `mise install --yes`

## Rules

- `GIT_TERMINAL_PROMPT=0` in all scripts with git operations
- Tools go in mise config, NOT in install scripts
- `mise lock` after any config change
