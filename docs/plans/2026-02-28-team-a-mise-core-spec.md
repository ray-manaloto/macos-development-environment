# Team A Spec: mise Core, Registries, and Backend Governance

## Scope
Define a modern, reproducible, secure `mise`-first governance model for this Macbook environment.

## Decisions
1. `mise` is the default owner for runtimes and developer-facing CLIs whenever a stable backend exists.
2. `brew` is not used for language runtime ownership except documented exceptions.
3. Backend selection order for tools:
   - native `mise` plugin/backend
   - `aqua` backend via `mise` for release binaries
   - `ubi` backend via `mise` for GitHub release assets
   - `npm` backend via `mise` for Node CLIs
   - `pipx` backend via `mise` for Python CLIs
   - `cargo` backend via `mise` for Rust CLIs
4. Registries remain default unless a documented internal registry is introduced.
5. Version policy:
   - core runtimes: pinned major/minor or explicit version windows
   - volatile CLIs: `latest` allowed only if verified by drift + verification suite
6. Trust/provenance:
   - prefer signed release channels where available
   - forbid ad-hoc curl installers unless in exception policy
   - require documented source for every exception tool

## Backend Governance Model
### Language runtimes
- Python, Node, Bun, Go, Rust: `mise` runtime ownership.

### Framework CLIs
- Prefer `npm`/`pipx`/`cargo` backends under `mise` so command resolution stays under shims.

### SDK/Cloud CLIs
- Prefer `mise` when backend is stable.
- If unstable or unavailable, route through documented exception list.

### General tooling
- Prefer `aqua`/`ubi` via `mise` for binary tooling to minimize custom installers.

## Reproducibility and Rollback
- Maintain canonical `mise` config as source of truth.
- Add lock/verification snapshots in status and drift outputs.
- Any migration must be dry-run first, then apply, then verify.

## Risks
- plugin instability for niche CLIs
- fast-moving `latest` channels causing drift
- hidden transitive dependency reintroducing `brew` runtimes

## Acceptance Criteria
- tool ownership model is explicit for all categories
- backend choice algorithm is deterministic
- exceptions are policy-driven, not ad hoc
