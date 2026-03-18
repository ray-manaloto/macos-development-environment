# macOS Toolchain Modernization Consolidated Spec

## 1. Final Objective and Scope
Adopt a `mise`-first toolchain governance model for this macOS development environment, with:
- explicit ownership of runtimes/tools
- hardened `brew` boundary
- standardized `oh-my-zsh` operator contract
- deterministic maintenance and drift enforcement

Implementation is allowed only after this spec is approved.

## 2. Current-State Summary
Current environment and repository already provide:
- launchd-managed maintenance script
- status and health scripts
- managed shell templates and aliases
- wrapper-based CLI consistency

Evidence paths:
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/macos-env.zsh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/aliases.zsh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/status-dashboard.sh`

## 3. Final Ownership Matrix (Decision-Complete)
### Owner: `mise`
- language runtimes: python,node,bun,go,rust
- developer CLIs with stable `mise` backends
- binary CLIs available via `aqua`/`ubi` backends
- npm/pipx/cargo-driven CLIs where stable under `mise`

### Owner: `brew`
- OS-level dependencies
- GUI casks and system-integrated packages
- explicit exceptions only

### Owner: exception policy
- tools lacking stable `mise` support
- tools requiring privileged/vendor-managed lifecycle

## 4. mise Registry and Backend Governance
1. default registry remains baseline.
2. backend selection order:
   - native plugin/backend
   - `aqua`
   - `ubi`
   - `npm`
   - `pipx`
   - `cargo`
3. versions:
   - core runtimes pinned to controlled channels
   - selected CLIs may track `latest` only when verification remains green
4. provenance:
   - no undocumented curl installer paths
   - exception entries require source/provenance metadata

## 5. Exception Policy and Lifecycle
Machine-readable file required: `docs/tooling/mise-exceptions.yaml`

Schema (required fields):
- `tool`
- `owner`
- `reason`
- `source`
- `introduced_on`
- `review_due_on`
- `retirement_condition`

Governance rules:
- quarterly review minimum
- no automatic exception insertion
- every exception has named owner

## 6. brew Boundary Enforcement Model
1. forbid brew runtime ownership by default.
2. drift checker flags brew-owned runtime commands.
3. strict cleanup allowed only if gate conditions pass.
4. if uninstall blocked by dependencies, fail with actionable log output.

## 7. Shell/Alias Contract
Required commands:
- `mde-status`
- `mde-update`
- `mde-update-fast`
- `mde-verify`
- `mde-drift`
- `mde-migrate`
- `mde-agents-review`

Shell rules:
- deterministic path ordering with `mise` shims first
- no network side effects in shell startup
- no secrets embedded in alias/template files

## 8. Maintenance, Update, and Drift Architecture
Required execution order:
1. pre-flight lock + env setup
2. bounded updates (brew/mise/bun/uv/pixi)
3. post-update drift check
4. verification summary
5. optional gated strict cleanup

Drift checker outcomes:
- warning mode: advisory output
- enforce mode (`MDE_DRIFT_ENFORCE=1`): non-zero on policy violation

## 9. Phased Implementation Plan With Gates
### Phase P1: Policy and interfaces
- add ownership/exception docs
- add script interface stubs and alias mapping
- gate: docs reviewed and accepted

### Phase P2: Migration + drift tooling
- implement migration and drift scripts
- add dry-run/apply modes
- gate: dry-run clean on baseline machine

### Phase P3: Maintenance integration
- integrate drift checks into maintenance + verify flow
- optional strict mode enablement
- gate: two consecutive clean verification cycles

## 10. Validation Matrix and Acceptance Criteria
Validation commands:
- `scripts/verify-all.sh`
- `scripts/status-dashboard.sh --json`
- `scripts/mde-drift-check.sh --fail-on-warning`

Must pass:
1. runtime paths resolve to `mise` (or documented exception).
2. maintenance run exits clean under normal mode.
3. alias contract resolves to valid scripts.
4. exception file schema validates.

## 11. Rollback Strategy
- keep pre-migration baseline commit/tag.
- disable enforcement flags to return to advisory mode.
- restore prior shell templates/aliases if command contract regressions occur.
- rerun full verification after rollback.

## 12. Assumptions and Defaults
- existing `run-multi-agent` remains orchestration baseline for review workflows.
- launchd architecture remains unchanged.
- migration remains staged and reversible.
- `mise` remains primary owner by default.

## Required Public Interfaces
New scripts to implement:
- `scripts/mde-migrate-to-mise.sh`
- `scripts/mde-drift-check.sh`
- `scripts/mde-update.sh`
- `scripts/mde-agents-review.sh`

Environment variables:
- `MDE_TOOL_OWNERSHIP_FILE`
- `MDE_MISE_EXCEPTION_ALLOWLIST`
- `MDE_DRIFT_ENFORCE`

## Quick Command Cheat-Sheet
- posture: `mde-status`
- full update: `mde-update`
- fast update: `mde-update-fast`
- verify everything: `mde-verify`
- detect policy drift: `mde-drift`
- run migrations: `mde-migrate`
- run document review teams: `mde-agents-review`
