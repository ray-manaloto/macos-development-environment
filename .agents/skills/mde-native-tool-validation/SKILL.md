---
name: mde-native-tool-validation
description: Enforce native lint, static analysis, and cache-safe validation commands per implementation language in this repo.
---

# MDE Native Tool Validation

Use this skill when adding or changing validation, linting, or static-analysis workflows.

## Validation Order

1. Python helpers: Python-native checks first.
2. Node or TypeScript helpers: JS or TS-native checks first.
3. Go helpers: Go-native checks first.
4. Rust helpers: cargo-native checks first.
5. Shell wrappers: ShellCheck only for the shell that remains.

## Cache Guidance

- Prefer validators that reuse the ecosystem cache rather than forcing redownloads.
- Avoid `--no-cache`, explicit cache deletion, or temp-home workarounds unless testing a failure mode.
- Record the native validation toolchain in `configs/mde-modernization-matrix.json`.

## Required Reads

- `configs/mde-modernization-matrix.json`
- `docs/research/ecosystem-decisions/2026-03-14-python-cli-mise-cache.md`
- `docs/research/ecosystem-decisions/2026-03-14-node-cli-mise-cache.md`
- `docs/research/ecosystem-decisions/2026-03-14-go-tooling-mise-cache.md`
- `docs/research/ecosystem-decisions/2026-03-14-rust-tooling-mise-cache.md`
