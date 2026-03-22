---
name: mise-enforcement
description: Use when installing or updating CLI tools, configuring devcontainer tooling, or validating runtime/tool commands to ensure a strict mise-first workflow.
---

# Mise Enforcement

This repository treats `mise` as the authority for global runtimes, global CLIs, and SDK CLIs.
mise is the authority for global tools.

## Use This Skill When

- Installing or updating command-line tools.
- Changing setup, bootstrap, migration, automation, or devcontainer workflows.
- Reviewing scripts or docs that mention `brew install`, `npm -g`, `bun add -g`, `uv tool install`, `pipx install`, `cargo install`, or `go install`.

## Contract

1. Global runtimes and global CLIs belong under `mise` authority, with `/Users/rmanaloto/.config/mise/config.toml` plus `configs/mde-modernization-matrix.json` defining whether the declaration is a direct `mise` entry or a backend-native declarative config consumed by `mise`.
2. Repository libraries belong in native manifests such as `package.json`, `pyproject.toml`, `uv.lock`, `pixi`, `Cargo.toml`, and `go.mod`.
3. Use `mise run <task>` for repo automation and `mise x <tool> -- <args>` for one-off tool execution.
4. Prefer backend-native declarative config when the backend exposes one; otherwise use a direct declarative `mise` entry.
5. Do not resolve missing tools with direct global installers unless the tool is in `configs/mde-install-exceptions.json` and break-glass override is explicitly set.
6. Do not rely on implicit auto-install behavior in agent contexts. Use explicit `mise install`, `mise run`, or `mise x`.
7. reuse backend-native caches by default. Do not clear or bypass package-manager caches unless a bounded maintenance or exception flow explicitly allows it.

## Required Checks

- Read `configs/mde-tool-ownership.json` before changing tool ownership.
- Read `configs/mde-modernization-matrix.json` before changing declarative package sources or script authority.
- Read `configs/mde-skill-registry.json` before introducing new repo-local skill IDs.
- Load `.agents/skills/mde-package-cache-policy/SKILL.md` when cache behavior or cache directories are part of the change.
- Load `.agents/skills/mde-chezmoi-dotfiles/SKILL.md` when editing any file under `.chezmoisource/`.
- Run `mise run mde:agent:preflight` before agent-driven setup, migration, or research flows.
- Run `mise run mde:drift` after changing ownership rules or managed tool surfaces.

## Explicitly Disallowed Defaults

- `brew install` for repo-managed CLIs.
- `npm -g` or `bun add -g` for repo-managed CLIs.
- `uv tool install`, `pipx install`, `cargo install`, or `go install` as the default path for repo-managed CLIs.
- Installing repo libraries globally to fix a missing import or command.

## Quick Verification

```bash
mise run mde:agent:preflight
mise run mde:drift
mise run mde:agent:report
```
