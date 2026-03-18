# Team C Spec: Homebrew Boundary and Exception Lifecycle

## Scope
Constrain Homebrew usage to prevent runtime ownership drift while preserving macOS operability.

## Boundary Policy
1. `brew` formula/cask usage is limited to:
   - OS-level dependencies and package manager prerequisites
   - GUI applications/casks
   - documented exceptions not viable in `mise`
2. Language runtime ownership through `brew` is disallowed by default.
3. Strict cleanup (`MDE_AUTOFIX_STRICT=1`) is only enabled when prerequisites pass.

## Anti-Drift Controls
1. Add drift check after maintenance update.
2. Fail verification if runtime binaries resolve to brew paths without exception.
3. Track brew-installed runtime formulae and alert on reintroduction.

## Exception Lifecycle
Each exception must include:
- tool name
- reason `mise` is not selected
- owner
- introduced date
- review cadence (default quarterly)
- retirement trigger (stable mise backend becomes available)

## Governance
- exception file is machine-readable and versioned in repo
- any new exception requires explicit justification and review sign-off

## Risks
- transitive dependencies can re-add runtime formulae
- strict removal may fail if formula is dependency of another package

## Acceptance Criteria
- boundary is explicit and enforceable
- exceptions are auditable and time-bounded
