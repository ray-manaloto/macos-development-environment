# Devcontainer Profile

This repo supports both native macOS and Linux devcontainers via `MDE_PLATFORM`.

## Auto-detection
- `macos`: host Darwin shells.
- `devcontainer`: when `DEVCONTAINER` or `CODESPACES` is present.
- `linux`: when only `/.dockerenv` is present (generic container).
- `linux`: fallback for non-container Linux.

## Bring-up
1. Open the repo in a devcontainer (pulls `ghcr.io/ray-manaloto/macos-development-environment/devcontainer:main` from `.devcontainer/devcontainer.json`).
2. Post-create restores the declarative bootstrap contract in this order:
   - verifies the baked image baseline exposes `mise`
   - trusts the repo task config and the repo-owned `.devcontainer/mise.toml`
   - copies the repo-owned devcontainer mise config and lockfile into `~/.config/mise/`
   - installs the pinned container toolchain with `mise install --locked`
   - syncs managed configs with `scripts/ensure-managed-configs.sh` in `chezmoi`-first mode
   - runs `mise run mde:verify`, `mise run mde:drift`, and validates `mise run mde:status`
   - stores a bootstrap hash under `~/.local/state/macos-development-environment/devcontainer-bootstrap.sha256`
3. Bootstrap is hash-gated. Reinstall work reruns only when the post-create script, devcontainer mise manifest/lockfile, managed config source, or related bootstrap inputs change.
4. Verify:
   - `mise trust`
   - `scripts/ensure-managed-configs.sh --check`
   - `mise run mde:verify`
   - `mise run mde:drift`
   - `mise run mde:status`

## Image Workflow
- The authored image definition remains `.devcontainer/Dockerfile`.
- CI validates raw image smoke on `linux/amd64` and `linux/arm64`, then publishes the multi-arch GHCR image on merges to `main`.
- Local reproduction uses two validation lanes:
  - `mise run mde:devcontainer:image:build`
  - `mise run mde:devcontainer:image:smoke`
  - `mise run mde:devcontainer:lifecycle:smoke`

### Lane Definitions
- `scripts/devcontainer-image-smoke.sh`
  - validates only the baked image baseline
  - does not mount the repo or execute `.devcontainer/post-create.sh`
- `scripts/devcontainer-lifecycle-smoke.sh`
  - runs `devcontainer up` against the real `.devcontainer/devcontainer.json`
  - verifies `remoteUser`, `containerEnv`, `postCreateCommand`, and the pinned bootstrap contract
  - reruns `.devcontainer/post-create.sh` to prove idempotence

### Local Image Override
- `.devcontainer/devcontainer.json` stays image-based.
- Local lifecycle smoke can override the image via `MDE_DEVCONTAINER_IMAGE` without reintroducing a `build` stanza.

## Notes
- Host-only checks (launchd/keychain) are skipped on devcontainer.
- `scripts/ensure-managed-configs.sh` is `chezmoi`-first, with legacy fallback when `chezmoi` is unavailable.
- If `mise` shims complain about trust, run `mise trust` in the repo once.
- `mise run mde:remediate --check` is safe on devcontainer and reports
  platform-gated N/A host steps.
