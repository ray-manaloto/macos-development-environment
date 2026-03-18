# Team E Spec: Maintenance and Validation Hardening

## Scope
Harden maintenance update flow and verification gates for safe `mise`-first operations.

## Staged Maintenance Flow
1. Pre-flight:
   - lock acquisition
   - path setup
   - secret loading
2. Update phase:
   - brew (bounded scope)
   - mise
   - bun/uv/pixi
   - agent tool refresh (if enabled)
3. Post-update phase:
   - drift detection
   - ownership checks
   - summarized status output
4. Optional auto-fix phase:
   - manager cleanup
   - strict runtime cleanup (gated)

## Failure Semantics
- each stage sets explicit failure markers
- final exit code non-zero when critical stage fails
- logs include stage identifiers for diagnosis

## Strict Mode Gates
Enable strict mode only when:
- `mise` installed and active
- runtime command paths resolve to mise shims
- drift check clean in two consecutive runs

## Telemetry and Logs
- maintain machine-readable status output (`--json`)
- include drift summary in status dashboard output
- preserve operator-friendly one-line tmux output

## Acceptance Criteria
- maintenance run is stage-structured and diagnosable
- strict mode has explicit guardrails
- post-update drift checks are mandatory in verification flow
