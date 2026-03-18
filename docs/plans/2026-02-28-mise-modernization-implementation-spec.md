# Modern `mise`-First macOS Dev Environment Modernization Spec

Date: 2026-02-28  
Audience: AI coding agent implementing improvements in this repository

## Objective
Modernize this repository's macOS development setup to match current best practices for a `mise`-managed system:
- reproducible and deterministic
- idempotent and non-interactive
- clear ownership for each tool manager
- clean verification with minimal side effects

## Reference Templates (Use As Pattern Sources)
These are the 3 primary template sources for this migration:

1. thoughtbot/laptop
- Repo: https://github.com/thoughtbot/laptop
- Why use it: highly reliable idempotent bootstrap flow, explicit logging/debugging expectations, clear "run repeatedly" behavior.

2. br3ndonland/dotfiles
- Repo: https://github.com/br3ndonland/dotfiles
- Why use it: comprehensive, well-documented setup with explicit bootstrap variables and a dedicated `mise-en-place` section.

3. basnijholt/dotfiles
- Repo: https://github.com/basnijholt/dotfiles
- Why use it: strong cross-machine reproducibility, practical automation scripts, and heavy emphasis on smooth bootstrap/install experience.

Supplemental non-GitHub docs:
- `mise` docs: https://mise.jdx.dev/
- chezmoi macOS docs (for machine-specific templating patterns): https://www.chezmoi.io/user-guide/machines/macos/

## Current Gaps To Fix
1. Overuse of `latest` versions for core toolchain in global setup (low reproducibility).
2. Mixed tool ownership across `mise`, `uv tool`, and `bun -g` with overlap.
3. `verify` workflow includes side effects (credentials writes / service restarts).
4. Optional/experimental tools can fail whole maintenance.
5. `uv self update` conflicts when `uv` is `mise`-managed.
6. Some tools are install-verified as if they expose executables even when they do not.

## Target Architecture
### A. Tool Ownership Model (Single Source Per Tool)
- Runtime/toolchain owners:
  - `mise`: python, node, bun, go, rust, awscli, pixi, uv
- Python app-level CLIs:
  - `uv tool`: app CLIs only (no duplicate manager for same binary)
- Node app-level CLIs:
  - `bun -g`: app CLIs only (no duplicate manager for same binary)
- Rule: no tool binary should be installed by more than one manager.

### B. Update vs Verify Separation
- `update` scripts: mutating actions only.
- `verify` scripts: read-only checks only.
- `repair` scripts: targeted remediation for known drift/failure cases.

### C. Optional Components
- Optional stacks must default to "skip without failing overall verification."
- Add explicit gates for optional domains (e.g., AI research marketplace, extra plugin packs).

## Implementation Plan (Phased)
## Phase 1: Deterministic Version Policy
### Changes
1. Introduce pinned version policy for core toolchain.
2. Add a single canonical version manifest file for managed core tools.
3. Replace `latest` for core runtime/toolchain installs in setup scripts with pinned versions.

### Files
- `.config/mise/config.toml` (if managed here) and any setup scripts that enforce globals:
  - `scripts/macos-dev-maintenance.sh`
  - `scripts/install-agent-stack.sh`

### Acceptance
- `mise outdated` may show updates available, but installed versions must match pinned policy unless intentionally bumped.
- Re-running setup does not unexpectedly roll major/minor versions.

## Phase 2: Manager Ownership Cleanup
### Changes
1. Build a manager-ownership table (tool -> owner) in docs.
2. Remove duplicate install paths for identical CLIs across managers.
3. Ensure wrapper scripts point to the owner-managed binary path.

### Files
- `docs/toolchain-precedence.md` (or add new `docs/tool-ownership.md`)
- `scripts/install-agent-stack.sh`
- `scripts/install-langchain-cli-tools.sh`
- wrapper scripts under `scripts/*-wrapper.sh`

### Acceptance
- A command appears once in ownership map.
- No duplicate installed command paths for core binaries (`which -a <cmd>` should not show conflicting manager-owned entries, wrappers excluded).

## Phase 3: Make Verification Read-Only
### Changes
1. Split side-effect checks from verification:
  - move mutations in `verify-tooling.sh` into a dedicated repair/update path.
2. Keep verification limited to:
  - command presence
  - version checks
  - API reachability checks (non-mutating)

### Files
- `scripts/verify-tooling.sh`
- `scripts/setup-skypilot-aws.sh` (if currently used as verifier and mutates state)
- `scripts/sky-status.sh`

### Acceptance
- Running `./scripts/verify-tooling.sh` performs no writes and no service restarts.
- Exit code reflects only health status, not side-effect failures.

## Phase 4: Optional Components as Soft Checks
### Changes
1. Gate optional sections with env flags defaulting to `0`.
2. Optional checks log `skip` or `warn`, but do not fail whole run unless strict mode enabled.

### Files
- `scripts/verify-tooling.sh`
- optional verification/install scripts

### Acceptance
- Base verification passes on a machine without optional marketplaces/plugins.
- Strict mode (`MDE_VERIFY_STRICT_OPTIONAL=1`) can enforce optional dependencies.

## Phase 5: `uv`/`mise` Interaction Hardening
### Changes
1. In all scripts, skip `uv self update` when `uv` path is under `mise`.
2. Keep only `uv tool upgrade --all` for app-level tools where appropriate.

### Files
- `scripts/macos-dev-maintenance.sh`
- `scripts/install-agent-stack.sh`

### Acceptance
- No `uv self update` error when `uv` is `mise`-managed.
- Maintenance exits 0 when all non-optional checks pass.

## Required Script Behavior Rules
1. Every script must be idempotent.
2. Every script must be non-interactive by default.
3. Every script must classify failures:
- `hard`: core setup breakage
- `soft`: optional component unavailable
4. Every verification script should support `--json` summary mode.

## Suggested New/Updated Interfaces
1. `scripts/update-tooling.sh`
- Mutating updates only.

2. `scripts/verify-tooling.sh`
- Read-only checks only.
- Add `--json` output.

3. `scripts/repair-tooling.sh`
- Fix known drift cases (broken uv tool metadata, wrapper mismatch, stale paths).

## JSON Verification Output Schema (Required)
```json
{
  "timestamp": "2026-02-28T16:00:00Z",
  "overall": "pass|fail|warn",
  "checks": [
    {
      "name": "langchain-tools",
      "status": "pass|fail|warn|skip",
      "severity": "hard|soft",
      "details": "string"
    }
  ]
}
```

## Test Matrix (Must Run Before Completion)
Run in this order:
1. `./scripts/update-tooling.sh` (or current equivalent).
2. `brew outdated --formula && brew outdated --cask`
3. `mise outdated || true`
4. `uv tool list`
5. `./scripts/verify-tooling.sh`
6. `./scripts/verify-tooling.sh --json` (if added)

## Completion Criteria
Mark work complete only when all are true:
1. Core updates run without interactive prompts.
2. Base verification returns exit code 0.
3. Optional components do not fail base verification.
4. No duplicate ownership for core tools.
5. Docs reflect implemented behavior exactly.

## Non-Goals
1. Migrating entire dotfile management to chezmoi in this pass.
2. Replacing launchd strategy in this pass.
3. Redesigning all wrapper scripts unless required for ownership consistency.

## Notes For Agent
1. Prefer minimal, targeted edits over broad rewrites.
2. Keep backward-compatible env vars where possible.
3. If removing behavior, add migration notes in docs.
4. Do not claim success without command output evidence from the test matrix.
