---
name: mise-codegen
description: >
  This skill should be used when the user asks to "generate a GitHub Action for mise",
  "create a devcontainer with mise", "generate a bootstrap script", "generate task
  documentation", "create task stubs", or mentions mise generate, CI/CD setup with
  mise, devcontainer configuration, or mise bootstrap scripts.
---

# Mise Code Generation

Generate configuration files for CI/CD, devcontainers, bootstrapping, and documentation.

## Available Generators

```bash
mise generate github-action     # GitHub Actions workflow
mise generate devcontainer      # VS Code devcontainer config
mise generate bootstrap         # Bootstrap script (curl | sh)
mise generate git-pre-commit    # Git pre-commit hook
mise generate task-docs         # Documentation for tasks
mise generate task-stubs        # Shims to run mise tasks
mise generate config            # Generate a mise.toml template
mise generate tool-stub         # HTTP-based tool stub
```

## GitHub Actions

```bash
mise generate github-action > .github/workflows/mise.yml
```

Generates a workflow that:
- Installs mise via the official `jdx/mise-action`
- Runs `mise install` to set up tools
- Caches tool installations
- Supports matrix builds across versions

## Devcontainer

```bash
mise generate devcontainer > .devcontainer/devcontainer.json
```

Creates a devcontainer that bootstraps mise and installs all tools from config.

## Bootstrap Script

```bash
mise generate bootstrap > scripts/bootstrap.sh
```

Creates a portable script for new developers: `curl -fsSL .../bootstrap.sh | sh`

## Task Documentation

```bash
mise generate task-docs > docs/tasks.md
```

Generates markdown documentation for all tasks in the project, including descriptions,
dependencies, and arguments.

## Task Stubs

```bash
mise generate task-stubs
```

Creates shell scripts in `./bin/` that wrap `mise run <task>` — useful for tools
that expect executables in PATH.

## Pre-Commit Hook

```bash
mise generate git-pre-commit > .git/hooks/pre-commit
```

Note: This project uses **hk** (jdx's hook manager) instead. Prefer `hk install` over
raw pre-commit hooks. See the **mise-jdx-ecosystem** skill for hk integration.

## Best Practices

- Commit generated CI/CD files — they're project infrastructure
- Re-generate after adding new tools to keep CI in sync
- Use `mise generate task-docs` to keep task documentation current
- Prefer `hk` over raw `git-pre-commit` for hook management
