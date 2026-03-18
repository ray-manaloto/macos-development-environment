# MDE Update Remediation Spec

## Context
- Review date: March 13, 2026.
- Source evidence: `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/mde-update-results.20260213.log`.
- Current state: the canonical log now reflects a fresh `mise run mde:update` rerun with `0 error` matches for `^error:`, `mise ERROR`, `ERROR task failed`, and `Install completed with failures`.
- Current warnings remaining in the rerun log are soft only: missing `OPENAI_API_KEY`, missing `ANTHROPIC_API_KEY`, and a Fabric installer PATH warning.

## Problem Summary
The original February 13 log captured hard updater failures across four surfaces:
1. blanket `mise upgrade --yes` touched Bun-backed npm tools and produced `ENOENT`, `EEXIST`, and `mise ERROR bun failed` bursts;
2. blanket Bun global update inherited caller workspace state and amplified Node CLI failures;
3. generic `uv` upgrade touched repo-managed LangChain/internal tools that should have stayed under the curated installer;
4. team automation around this remediation was not yet tied to a canonical log path plus a rerun-until-clean loop.

Those hard failures are now remediated in the codebase and the rerun log is clean, but the repo still needs a clear acceptance contract around soft warnings, orphaned npm-tool ownership, and native/devcontainer parity boundaries.

## Goals
- Keep `mise run mde:update` bounded to deterministic ownership surfaces and preserve `0 error` matches in the canonical rerun log.
- Keep `curl` resolution explicit before `brew update` so Homebrew does not fail on tool discovery.
- Keep `bun` global actions isolated from caller cwd and workspace state.
- Keep repo-managed LangChain/internal tools out of generic `uv` upgrade paths.
- Keep devcontainer and native macOS verification behavior intentionally aligned for shared contracts while preserving platform-specific skips.
- Keep the multi-agent remediation team runnable against a supplied log path and make the validator fail if the latest log is not clean.

## Non-Goals
- Do not disable provenance, signature verification, or Rekor-related checks as a shortcut.
- Do not make missing provider secrets hard blockers for the entire maintenance flow unless a specific phase truly requires them.
- Do not force devcontainer to emulate host-only facilities such as launchd, Homebrew, or Keychain.
- Do not hide optional internal-tool instability by silently broadening retry loops without ownership decisions.

## Requirements
### Maintenance Hardening
- `scripts/macos-dev-maintenance.sh` must resolve and export a usable Homebrew `curl` path before `brew update`.
- `scripts/macos-dev-maintenance.sh` must keep npm-backed `mise` tools excluded from blanket `mise upgrade --yes`.
- `scripts/macos-dev-maintenance.sh` must not run a blanket Bun global update path.
- `scripts/install-agent-stack.sh` and `scripts/install-langchain-cli-tools.sh` must keep Bun installs inside `with_stable_cwd()`.
- `scripts/macos-dev-maintenance.sh` must keep repo-managed LangChain/internal tools excluded from generic `uv` upgrade handling.
- `scripts/install-langchain-cli-tools.sh` must keep unstable/internal tools best-effort when upstream packaging is not reliable.

### Native and Devcontainer Parity
- `scripts/verify-all.sh` must continue to respect `MDE_PLATFORM` and allow hard skips only where the policy explicitly marks them `skip_allowed=true`.
- `.devcontainer/post-create.sh` must continue to set `MDE_PLATFORM=devcontainer`, disable env/keychain autoload, sync managed configs first, and then run `mise install`.
- `scripts/health-check.sh` and `scripts/status-dashboard.sh` must keep platform-scoped behavior explicit so devcontainer runs do not regress into host-only expectations.
- Devcontainer smoke coverage must remain available through `mise run mde:devcontainer:image:smoke` for parity-sensitive changes.

### Team Orchestration
- `scripts/teams/run-mde-update-remediation-team.sh` must default to `mde-update-results.20260213.log`, accept an override path, and rerun `mise run mde:update` until the latest supplied log has `0 error` matches or the max attempt cap is reached.
- `scripts/teams/validate-mde-update-remediation-output.sh` must consume a dynamic log path and fail if the latest log still contains updater error lines.
- Team prompts and docs must reference the supplied log path, rerun attempts, and the `0 error` success criterion instead of the stale `20260413` filename.

## Acceptance Criteria
- `bash scripts/tests/mde-update-remediation.test.sh` passes.
- `MDE_TEST_PROFILE=ci scripts/tests/run-all.sh` passes.
- `rg -n -e '^error:|mise ERROR|ERROR task failed|Install completed with failures' /Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/mde-update-results.20260213.log` returns no matches.
- A fresh `mise run mde:update` completes without hard updater errors; soft warnings may remain only for non-blocking secrets or informational PATH notices.
- `mise run mde:verify -- --json` returns no hard failures; current acceptable state is overall `warn` due only to soft `secrets-smoke-test` failure.
- `MDE_PLATFORM=devcontainer scripts/verify-all.sh --json` returns overall `pass` with only policy-allowed hard skips.
- The team runner and validator accept the canonical log path and enforce the `0 error` contract.
- The remediation packet contains triage, maintenance, parity, validation, spec, and plan outputs grounded in current repository evidence.

## Open Follow-up Items
- Decide which npm-backed tools in `~/.config/mise/config.toml` need an explicit curated owner beyond the three already covered in `scripts/install-agent-stack.sh`.
- Decide whether the Fabric installer PATH warning should be eliminated in maintenance or documented as acceptable post-install noise.
- Reduce devcontainer `health-check.sh` warnings around host maintenance logs where that warning is not actionable inside containers.
- Revisit whether missing `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` should stay advisory for `mise run mde:update` or become phase-specific gates for optional AI tooling.
