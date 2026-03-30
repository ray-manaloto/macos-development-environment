---
name: Quality gate baseline
description: Known-good baseline for quality gate and validate --all as of 2026-03-28
type: project
---

As of 2026-03-28, the expected clean state is:

**Quality gate (6/6) — last verified 2026-03-29:**
- ruff-check: 0 violations
- ruff-format: 195 files already formatted
- ty: 0 errors
- pyright: 0 errors, 0 warnings, 0 information
- pytest: 606 passed, 4 skipped
- mde-validate: OK (2 chezmoi warnings)

**--strict mode:** 2 chezmoi dirty-working-tree warnings cause `--strict` to fail. This is expected behavior.

**validate --all (2 expected warnings):**
- [WARNING] chezmoi: `[source-dir]` dirty git tree warning
- [WARNING] chezmoi: `[working-tree]` dirty git tree warning
- All plugin install paths valid, no stale temp dirs, no MCP collisions, 3 LSP binaries found

**hk validator tests (8/8):**
- `test_validate_hk.py` — 8 tests all PASS including the real binary integration test

**Why:** These 2 chezmoi warnings are structural (the repo is its own chezmoisource, always dirty during dev). They are not suppressible without upstream chezmoi config support.

**How to apply:** If validate --all shows more than 2 warnings or the warnings change category, investigate. If pytest drops below 606 passed, investigate regressions.
