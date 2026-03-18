# Operational Checklist (`macOS` + `devcontainer`)

This is the canonical run checklist for both supported profiles.

## 1) First Run
- `mise trust`
- `scripts/ensure-managed-configs.sh`
- `scripts/mde-verify --json`
- If host state is not clean, run deterministic remediation:
  - `mise run mde:remediate`

## 2) Platform Selection
- Override: `MDE_PLATFORM=macos|devcontainer|linux`
- Auto-detect:
  - `DEVCONTAINER` or `CODESPACES` => `devcontainer`
  - plain `/.dockerenv` => `linux`
  - otherwise `uname` fallback (`macos`/`linux`)

## 3) Maintenance
- Primary command: `mise run mde:update`
- Config sync is always run (chezmoi-first, legacy fallback).
- Verify status:
  - `mise run mde:verify`
  - `mise run mde:drift`
  - `mise run mde:status`

## 4) Verification Policy
- Hard-check skip is failure by default.
- Allowed hard skips must be explicit in
  `scripts/config/mde-verify.conf`.
- JSON contract:
  - `scripts/mde-verify --json` exits non-zero on hard failures.
  - `scripts/mde-verify --json` exits non-zero on unexpected hard skips.

## 5) Platform Acceptance
- macOS:
  - launchd/keychain checks are applicable.
  - log root: `~/Library/Logs/com.ray-manaloto.macos-dev-maintenance`
- devcontainer:
  - launchd/keychain checks are N/A (not hard-fail).
  - bootstrap: `.devcontainer/post-create.sh`
  - log root: `~/.local/state/macos-dev-maintenance`

## 6) Tests + Static Validation
- `scripts/quality-checks.sh`
- `scripts/tests/run-all.sh` (CI-safe profile, default)
- `MDE_TEST_PROFILE=host scripts/tests/run-all.sh` (host-state profile)

## 7) Host Remediation Workflow (Pre -> Remediate -> Post)
1. Pre-check:
   - `scripts/ensure-managed-configs.sh --check`
   - `scripts/mde-drift-check.sh`
   - `scripts/mde-verify --json`
2. Remediate:
   - `mise trust`
   - `mise run mde:remediate`
   - Optional runtime ownership apply path:
     - `mise run mde:remediate --runtime-apply`
3. Post-check:
   - `scripts/ensure-managed-configs.sh --check`
   - `scripts/mde-verify --json`
   - `mise run mde:status`
