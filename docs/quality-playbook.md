# Quality Playbook

This repo keeps a lightweight, repeatable checklist for review, QA, and docs.

## Review Checklist
- Confirm PATH ordering aligns with preference policy (mise > pixi > uv > pip; bun > node).
- Validate scripts use safe defaults and clear fallbacks.
- Scan for conflicting CLIs (e.g., `langchain`, `deepagents`).

## QA / Validation
- `scripts/quality-checks.sh`
- Ensure scripts are bash-safe (`bash -n`).
- Run `shellcheck` if installed.
- CI-safe shell tests:
  - `scripts/tests/run-all.sh`
- Host-state shell tests:
  - `MDE_TEST_PROFILE=host scripts/tests/run-all.sh`
- Optional: run `scripts/run-multi-agent.sh` if a runner is configured.

## Test Lanes
- `ci` profile (default): hermetic tests only; skips host-mutation/host-assumption suites.
- `host` profile: includes host-assumption suites for local machine validation.
- Determinism constraints:
  - no network required for CI profile tests,
  - temp HOME and temp PATH mocks are preferred for remediation transitions.

## Documentation
- Update `docs/setup-notes.md` with any new scripts or paths.
- Keep `docs/decision-log.md` current for tooling decisions.

## Agent Playbook
- Use `docs/agent-playbook.md` for the default workflow.
- Use `docs/langchain-langsmith-weekly-checklist.md` for weekly reviews.

## Suggested Sequence
1. Review
2. QA
3. Docs sync
