---
name: mise-config-settings
description: >
  This skill should be used when the user asks to "configure mise settings",
  "change mise config", "format mise.toml", "trust a config file", "set up
  IDE integration for mise", or mentions mise config, mise settings, mise fmt,
  mise trust, mise.local.toml, or IDE/editor integration with mise.
---

# Mise Configuration & Settings

Manage mise configuration files, settings, formatting, trust, and IDE integration.

## Config Management

```bash
mise config ls                  # List loaded config files
mise config get tools.node      # Get specific config value
mise config set tools.node 22   # Set config value
mise fmt                        # Format mise.toml
mise trust                      # Trust current directory's config
mise trust --all                # Trust all config files
```

## Settings

```bash
mise settings                   # Show all settings
mise settings set KEY VALUE     # Set a setting
mise settings unset KEY         # Remove a setting
```

### Key Settings

| Setting | Purpose | Example |
|---------|---------|---------|
| `experimental` | Enable experimental features | `true` |
| `not_found_auto_install` | Auto-install missing tools | `true` |
| `npm.package_manager` | npm backend uses bun/npm | `"bun"` |
| `python.uv_venv_auto` | Auto-create venv with uv | `true` |
| `status.missing_tools` | Warning behavior | `"if_other_versions_installed"` |
| `env_cache` | Cache computed environment | `true` |

## Config File Hierarchy

1. `~/.config/mise/config.toml` — global (chezmoi-managed)
2. `.mise.toml` — project-level
3. `mise.local.toml` — local overrides (gitignored)
4. `mise.<ENV>.toml` — environment-specific

Higher-numbered files override lower-numbered ones.

## Trust System

Mise requires explicit trust for config files that set env vars or run tasks:

```bash
mise trust                      # Trust current config
mise trust /path/to/mise.toml   # Trust specific file
mise trust --all                # Trust all untrusted configs
```

## IDE Integration

### VSCode

Install the `mise-vscode` extension. Add to `~/.zprofile`:
```bash
eval "$(mise activate zsh --shims)"
```

### JetBrains

Install `intellij-mise` plugin. Workaround for tool detection:
```bash
ln -s ~/.local/share/mise ~/.asdf
```

### Neovim

Use shims in PATH for LSP servers to find mise-managed tools.

## Formatting

```bash
mise fmt                        # Format all mise.toml files
mise fmt --check                # Check without modifying
```

## Anti-Patterns

- Never edit `~/.config/mise/config.toml` directly if chezmoi-managed
- Use `mise.local.toml` for machine-specific overrides, not editing `.mise.toml`
- Shims cannot load arbitrary `[env]` vars — only tool PATHs
- Changing mise.toml in IDE does not reload env vars in running IDE
