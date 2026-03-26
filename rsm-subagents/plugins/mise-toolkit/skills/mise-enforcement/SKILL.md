---
name: mise-enforcement
description: >
  This skill should be used when the user asks to "install a CLI tool", "add a global
  tool", "check mise policy", "enforce mise-first", or when reviewing scripts that
  mention brew install, npm -g, bun add -g, bun install -g, pipx install, pip install
  --user, cargo install, go install, or gem install. Also use when validating
  runtime/tool commands to ensure a strict mise-first workflow. After blocking a
  direct install, see the mise-tool-management skill for the correct path to add
  tools via mise.
---

# Mise Enforcement

This repository treats `mise` as the authority for global runtimes, global CLIs, and SDK CLIs.
mise is the authority for global tools.

## Use This Skill When

- Installing or updating command-line tools.
- Changing setup, bootstrap, migration, automation, or devcontainer workflows.
- Reviewing scripts or docs that mention `brew install`, `npm -g`, `bun add -g`, `uv tool install`, `pipx install`, `cargo install`, or `go install`.

## Contract

1. Global runtimes and global CLIs belong under `mise` authority, with `~/.config/mise/config.toml` defining whether the declaration is a direct `mise` entry or a backend-native declarative config consumed by `mise`.
2. Repository libraries belong in native manifests such as `package.json`, `pyproject.toml`, `uv.lock`, `pixi`, `Cargo.toml`, and `go.mod`.
3. Use `mise run <task>` for repo automation and `mise x <tool> -- <args>` for one-off tool execution.
4. Prefer backend-native declarative config when the backend exposes one; otherwise use a direct declarative `mise` entry.
5. Do not resolve missing tools with direct global installers unless a break-glass override is explicitly set.
6. Do not rely on implicit auto-install behavior in agent contexts. Use explicit `mise install`, `mise run`, or `mise x`.
7. reuse backend-native caches by default. Do not clear or bypass package-manager caches unless a bounded maintenance or exception flow explicitly allows it.

## Required Checks

- Run `mise ls` to check current tool ownership before changing declarations.
- Review the project's declarative package sources before changing script authority.
- Check cache behavior policies when cache directories are part of the change.
- Run `mise doctor` before agent-driven setup, migration, or research flows.
- Run `mise outdated` after changing ownership rules or managed tool surfaces.

## Explicitly Disallowed Defaults

- `brew install` for repo-managed CLIs.
- `npm -g` or `bun add -g` for repo-managed CLIs.
- `uv tool install`, `pipx install`, `cargo install`, or `go install` as the default path for repo-managed CLIs.
- Installing repo libraries globally to fix a missing import or command.

## Quick Verification

```bash
mise doctor          # Check mise configuration health
mise ls              # Verify tool ownership
mise outdated        # Check for drift in tool versions
```
