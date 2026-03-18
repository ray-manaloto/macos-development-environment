# MDE Update Remediation Plan

## Phase 1: Preserve the Working Updater Path
1. Keep the `curl` hardening, `bun` stable-cwd wrappers, `mise` npm exclusions, and `uv` managed-tool exclusions in place.
2. Treat the current rerun log as the canonical proof artifact because it is already at `0 error` matches.
3. Re-run the targeted shell checks after any updater change.

## Phase 2: Lock the Rerun Contract
1. Keep `scripts/teams/run-mde-update-remediation-team.sh` pointed at the supplied canonical log path.
2. Keep the explicit attempt loop bounded by `MDE_UPDATE_REMEDIATION_MAX_ATTEMPTS`.
3. Require each rerun attempt to overwrite the canonical log with the latest `mise run mde:update` result.
4. Keep `0 error` matches in the latest log as the hard finish condition.

## Phase 3: Validate Native Behavior After Each Change
1. Run `bash scripts/tests/mde-update-remediation.test.sh`.
2. Run `MDE_TEST_PROFILE=ci scripts/tests/run-all.sh`.
3. Run `mise run mde:verify -- --json` and confirm there are no hard failures.
4. Re-run `mise run mde:update` and confirm the canonical log stays at `0 error` matches.

## Phase 4: Close Remaining Ownership Gaps
1. Inventory npm-backed tools in `~/.config/mise/config.toml` that are still excluded from blanket `mise` upgrade but not owned by curated installers.
2. Decide whether each orphaned tool belongs in `scripts/install-agent-stack.sh`, a new npm-tool sync script, or a clearly optional bucket.
3. Keep retry-only behavior out of the design unless a package-specific failure mode is proven.

## Phase 5: Tighten Parity Where It Matters
1. Keep shared verification logic driven by `MDE_PLATFORM`.
2. Preserve the existing devcontainer bootstrap contract from `.devcontainer/post-create.sh`.
3. Reduce false-warning drift in parity-sensitive paths, especially devcontainer health-check noise around host maintenance logs.
4. Run the devcontainer smoke lane for any parity-sensitive change: `mise run mde:devcontainer:image:smoke`.

## Phase 6: Keep Soft Warnings Explicit
1. Treat missing provider secrets as soft warnings unless a specific install lane truly requires them.
2. Keep the Fabric PATH warning documented as informational unless the repo decides to auto-manage that path.
3. Document every remaining warning in the remediation packet instead of letting it blur with hard updater failures.

## Rerun Checkpoints
- Canonical log proof: `rg -n -e '^error:|mise ERROR|ERROR task failed|Install completed with failures' /Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/mde-update-results.20260213.log`
- Native verify: `mise run mde:verify -- --json`
- Devcontainer parity: `MDE_PLATFORM=devcontainer scripts/verify-all.sh --json`
- Shell regression suite: `MDE_TEST_PROFILE=ci scripts/tests/run-all.sh`

## Next Steps
1. Keep the team runner wired to the canonical log so every future attempt reruns `mise run mde:update` until the latest log stays at `0 error` matches.
2. Assign explicit ownership for the remaining excluded npm tools.
3. Decide whether any current soft warning should become a gated phase check.
4. Re-run the parity smoke lane after any change touching verification, platform detection, or devcontainer bootstrap.
