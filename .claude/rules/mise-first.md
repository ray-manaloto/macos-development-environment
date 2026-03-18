---
description: Enforce mise-first declarative tool management
globs: ["scripts/*.sh", ".mise.toml", "Brewfile"]
---

# Mise-First Policy

- ALL tools MUST be in mise config, not install scripts
- Backend priority: Registry > aqua > github > pipx > npm > cargo > go
- NEVER use deprecated `ubi:` backend — use `github:`
- ALL scripts MUST set `GIT_TERMINAL_PROMPT=0` if they do git operations
- Do NOT add tools to Brewfile if already in mise config
- Install scripts should only handle non-declarative installs (curl, gh extensions, symlinks)
