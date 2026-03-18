---
name: mde-python-backend-selection
description: Choose the correct mise-managed backend for global Python CLIs in this repo, including cache-aware guidance for uv, pipx, and project manifests.
---

# MDE Python Backend Selection

Use this skill when changing Python CLI ownership, setup automation, migration flows, or validation rules.

## Decision Rules

1. Global Python CLIs stay `mise`-owned.
2. Repo Python dependencies stay in `pyproject.toml`, `uv.lock`, or other native project manifests.
3. Prefer `mise` with declarative `pipx:` entries for globally installed Python CLIs.
4. Keep `uv` itself as a direct `mise` tool entry. Do not use `uv tool install` as the long-term authority for global CLIs.
5. Treat git-clone-plus-patch install flows as explicit transition exceptions only.

## Cache Rules

- Reuse `UV_CACHE_DIR` for uv-managed downloads and wheels.
- Reuse `PIPX_HOME` and `PIPX_BIN_DIR` for pipx-managed CLI environments.
- Do not clear caches by default during automation.
- Only prune when a bounded maintenance flow explicitly calls for it.

## Required Reads

- `configs/mde-modernization-matrix.json`
- `configs/mde-tool-ownership.json`
- `docs/research/ecosystem-decisions/2026-03-14-python-cli-mise-cache.md`
- `.agents/skills/mde-package-cache-policy/SKILL.md`
