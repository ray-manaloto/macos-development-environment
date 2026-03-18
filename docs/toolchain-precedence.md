# Toolchain Precedence (Agent Runtime Contract)

Audience: Claude Code / Codex CLI operating this Mac's toolchain updates.
Goal: keep runtime and tool installs deterministic and conflict-free.

## First-Run Prerequisite
- Run `mise trust` in the repo before invoking `mise run mde:*` tasks.
- If trust/bootstrap drift appears, run `mise run mde:remediate`.
- In devcontainers, `.devcontainer/post-create.sh` verifies the baked
  `mise` baseline, disables autoloaded env/secrets, copies the repo-owned
  `.devcontainer/mise.toml` and `.devcontainer/mise.lock` into the container's
  global mise config root, runs `mise install --locked`, syncs managed
  declarative configs, and executes verify/drift/status checks.
- Devcontainer bootstrap must not inherit host `~/.config/mise/config.toml`;
  the container contract is repo-owned and deterministic.

## Precedence Model
Order of authority:
1) `mise` shims for global runtimes, global CLIs, and SDK CLIs
2) native repo manifests for dependencies and libraries
3) explicit exception registry for OS-level packages

Rationale:
- `mise` owns language runtimes and host-level CLIs used by agents.
- `bun`, `uv`, and `pixi` operate under `mise`-managed runtimes instead of acting as separate global authorities.
- `configs/mde-modernization-matrix.json` records whether each tool should use a direct `mise` declaration or a backend-native declarative config consumed by `mise`.
- `configs/mde-modernization-matrix.json` also records the required cache policy for each managed tool family.
- `configs/mde-domain-catalog.json` routes ecosystem-specific decisions to the owning domain SDLC team.
- `configs/mde-reference-sources.json` plus `.artifacts/reference-mirror/` define the mirror-first research contract for agent teams.
- `configs/mde-preset-catalog.json` and `configs/tool-bundles/` define the repo-scoped preset and starter-bundle contract.
- Homebrew is reserved for explicit exceptions only.

## Runtime Ownership Rules
- `mise` manages runtime versions globally.
- `uv` is prevented from managing Python downloads via `UV_PYTHON_DOWNLOADS=never`.
- `bun` package operations must not become the source of truth for global tool ownership.
- The `python-pixi-uv` domain defaults to a committed `pixi.toml` plus `pixi.lock` bundle for its starter surface; the domain team is responsible for documenting when companion `pyproject.toml`, Pixi global manifests, or `mise` global declarations are required.
- Backend-native caches must be reused by default through declared directories such as `UV_CACHE_DIR`, `BUN_INSTALL`, `GOCACHE`, `GOMODCACHE`, `CARGO_HOME`, and `RUSTUP_HOME`.

## Maintenance Script Behavior
Script: `scripts/macos-dev-maintenance.sh`

Key update actions:
- Sync managed configs first.
- Refresh `mise` and repo-declared automation entrypoints.
- Reconcile host drift through `mise run mde:agent:preflight`, `mise run mde:drift`, and `mise run mde:migrate:global-tools`.
- Keep any human-only exception workflows outside agent execution paths.

Guard flags:
- `MDE_AUTOFIX=1` enables cleanup and config sync.
- `MDE_AUTOFIX_STRICT=1` removes brew-managed runtimes if mise is active.

## Strict Cleanup (when enabled)
If `MDE_AUTOFIX_STRICT=1`:
- Removes brew-managed runtimes: node, python, go, rust.
- Requires mise to be installed and active.
- Can break scripts that hardcode `/opt/homebrew/bin/*`.

## Tool Manager Scope
- `bun`, `uv`, and `pixi` may be used inside the ownership boundaries declared by `mise`.
- Prefer the backend package manager's modern declarative config when it exists; otherwise use a direct declarative `mise` entry.
- Treat imperative `pixi global install` and `uv tool install` flows as execution details, not the long-term authority surface, unless the owning domain team records and adopts that model explicitly.
- Agent contexts must not use unmanaged global install commands to repair missing tools.
- Agent contexts must not clear or bypass package-manager caches unless an explicit maintenance or exception flow allows it.
- If a global CLI is missing, fix `/Users/rmanaloto/.config/mise/config.toml` and/or the backend-native config referenced by `configs/mde-modernization-matrix.json`, then run explicit `mise install` or `mise run`.
- In devcontainers, fix `.devcontainer/mise.toml` and `.devcontainer/mise.lock`,
  then rerun `.devcontainer/post-create.sh` or the lifecycle smoke task instead
  of mutating container-global state by hand.

## AI Checklist (before change)
- Confirm `mise` shims are ahead of Homebrew on `PATH`.
- Confirm `UV_PYTHON_DOWNLOADS=never`.
- Confirm declared cache env vars point at writable directories.
- If strict cleanup is desired, verify `which node/python/go/rustc` -> mise.

## AI Checklist (after change)
- Run `scripts/health-check.sh`.
- Verify CLI paths with `which node python go rustc bun uv`.
- Run `scripts/verify-tooling.sh` if toolchain changes occurred.
- Validate command contract:
  - `mise run mde:agent:preflight`
  - `mise run mde:agent:verify`
  - `mise run mde:agent:report`
  - `mise run mde:update`
  - `mise run mde:verify`
  - `mise run mde:drift`
  - `mise run mde:migrate:global-tools -- --report`
  - `mise run mde:research:autoimprove -- --report`
  - `mise run mde:status`
  - `mise run mde:test`
