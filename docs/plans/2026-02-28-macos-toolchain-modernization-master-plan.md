# macOS Toolchain Modernization Master Plan (Document-First)

## Objective
Create a document-first, multi-agent modernization program for this Macbook development environment, focused on:
- `mise` as primary manager
- `brew` boundary hardening
- `oh-my-zsh` operational UX standardization
- consolidated spec/plan generation via author/reviewer/aggregator team workflow

No implementation changes are performed until document review is complete.

## Why This Plan
The repository already has mature automation (`launchd`, maintenance scripts, aliases, wrappers), but modernization requires:
- explicit ownership model for all tool categories
- modern `mise` registries/backend governance
- clear exception policy for non-viable `mise` coverage
- standardized operator command contract
- decision-complete implementation spec with independent review

## Current-State Evidence (Source of Truth)
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/macos-dev-maintenance.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/macos-env.zsh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/templates/oh-my-zsh/aliases.zsh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/mise-config.md`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/toolchain-precedence.md`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/multi-agent-runner.md`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/status-dashboard.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/health-check.sh`
- `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/scripts/verify-all.sh`

## Program Deliverables (Document Sequence)
1. Master plan (this doc)
2. Author team docs (A-E)
3. Reviewer team docs (R1-R3)
4. Consolidated implementation spec (single decision-complete document)

## Phase 1: Author Team Wave (Generate Domain Specs)

### Team A: `mise` Core + Registries + Backend Governance
**Output**
- `docs/plans/2026-02-28-team-a-mise-core-spec.md`

**Required contents**
- modern `mise` best practices
- registry strategy (default + additions)
- backend governance model:
  - languages
  - framework CLIs
  - SDK CLIs
  - general tooling
- version policy (`latest` vs pinned channels)
- trust/provenance requirements
- reproducibility and rollback strategy

### Team B: Full Tool Coverage Matrix For This Macbook
**Output**
- `docs/plans/2026-02-28-team-b-mise-coverage-matrix.md`

**Required contents**
- exhaustive inventory mapped to:
  - already `mise`-managed
  - candidate for migration to `mise`
  - exception (not reliable in `mise`)
- per-tool ownership decision and rationale
- migration effort and risk score
- verification command per tool

### Team C: `brew` Boundary + Exception Lifecycle
**Output**
- `docs/plans/2026-02-28-team-c-brew-boundary-spec.md`

**Required contents**
- policy limiting `brew` to OS/cask/explicit exceptions
- anti-drift controls for runtime reintroduction
- exception governance:
  - owner
  - reason
  - review cadence
  - retirement criteria

### Team D: `oh-my-zsh` + Operator UX Contract
**Output**
- `docs/plans/2026-02-28-team-d-shell-ux-spec.md`

**Required contents**
- PATH precedence and de-duplication rules
- alias contract for operational commands:
  - `mde-status`
  - `mde-update`
  - `mde-update-fast`
  - `mde-verify`
  - `mde-drift`
  - `mde-migrate`
  - `mde-agents-review`
- shell startup safety/performance constraints
- secret loading boundaries and override policy

### Team E: Maintenance + Validation Hardening
**Output**
- `docs/plans/2026-02-28-team-e-maintenance-validation-spec.md`

**Required contents**
- staged maintenance flow and failure semantics
- post-update drift checks
- strict mode gates and prerequisites
- telemetry/logging requirements for fast diagnosis

## Phase 2: Reviewer Team Wave (Independent Critique)

### Reviewer R1: Technical Correctness
**Output**
- `docs/plans/2026-02-28-review-r1-technical.md`

**Checks**
- consistency with current repo architecture
- feasibility and sequencing validity
- contradiction detection across A-E docs

### Reviewer R2: Security + Supply Chain
**Output**
- `docs/plans/2026-02-28-review-r2-security.md`

**Checks**
- plugin/backend trust and provenance controls
- secret handling implications
- update channel and binary integrity concerns

### Reviewer R3: Operability + Developer Experience
**Output**
- `docs/plans/2026-02-28-review-r3-operability.md`

**Checks**
- maintainability of operational command set
- failure recovery and rollback usability
- cognitive load and onboarding friction

## Phase 3: Aggregator Team (Consolidated Spec)

### Aggregation Input
- all Team A-E docs
- all Reviewer R1-R3 docs

### Aggregation Output
- `docs/plans/2026-02-28-macos-toolchain-modernization-consolidated-spec.md`

### Mandatory sections in consolidated spec
1. final objective and scope
2. current-state summary with evidence links
3. final ownership matrix (decision-complete)
4. `mise` registry/backend governance model
5. exception policy and lifecycle
6. `brew` boundary enforcement model
7. `oh-my-zsh`/alias command contract
8. maintenance/update/drift architecture
9. phased implementation plan with gates
10. validation matrix and acceptance criteria
11. rollback strategy
12. assumptions/defaults

## Required Public Interfaces (to be defined in consolidated spec)
- `scripts/mde-migrate-to-mise.sh`
- `scripts/mde-drift-check.sh`
- `scripts/mde-update.sh`
- `scripts/mde-agents-review.sh`

Environment contract:
- `MDE_TOOL_OWNERSHIP_FILE`
- `MDE_MISE_EXCEPTION_ALLOWLIST`
- `MDE_DRIFT_ENFORCE`

Alias contract:
- `mde-status`
- `mde-update`
- `mde-update-fast`
- `mde-verify`
- `mde-drift`
- `mde-migrate`
- `mde-agents-review`

## Acceptance Criteria (Document Stage Only)
- master plan exists and is complete
- five author docs produced (A-E)
- three independent reviewer docs produced (R1-R3)
- consolidated spec is decision-complete (no unresolved policy decisions)
- consolidated spec can be handed to implementation team with no architecture decisions left open

## Assumptions / Defaults
- existing multi-agent mechanism (`scripts/run-multi-agent.sh`) remains orchestration baseline
- no code mutation is performed during this document stage
- `mise` is primary by default, with explicit documented exceptions
- launchd-based maintenance architecture remains in place
