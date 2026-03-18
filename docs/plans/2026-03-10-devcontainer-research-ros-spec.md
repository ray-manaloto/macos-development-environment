# Devcontainer Research ROS Spec (2026-03-10)

## Objective
Produce a decision-complete implementation spec for devcontainer + mise + verification automation using the ROS source-priority workflow.

## Workflow Compliance
- Source-priority stack applied from `docs/research/devcontainer-ros-workflow.md`: GitHub -> Reddit/HN -> curated lists.
- Query rule constraints preserved (stars floor, recency bounds, `archived:false`, path/content qualifiers).
- Skills applied: `research-source-discovery`, `github-repo-mining`, `social-signal-mining`, `evidence-synthesis`.

## Evidence Coverage
- Source classes: curated, github, social
- Repositories mined: 15
- Non-repo artifacts reviewed: 21
- Discovery records: 52
- Pattern records: 36

All workflow thresholds are satisfied (`>=3` source classes, `>=10` repositories, `>=20` non-repo artifacts).

## Decision Records
1. **adopt**: mise-first toolchain authority and task routing.
Proof: https://github.com/jdx/mise/blob/9985fcbbf44a6d74efc119535911877bd9b7c489/mise.toml ; https://news.ycombinator.com/item?id=42347917
2. **adopt**: devcontainer lifecycle hooks + CI devcontainer validation lanes.
Proof: https://github.com/devcontainers/cli/tree/9207699460457b79cfeb960982aa40692f648ea1/.github/workflows ; https://github.com/a5chin/python-uv/blob/7c033f985b57210f1d7105d8bc17770b55c09b0d/.github/workflows/devcontainer.yml
3. **adopt**: keep hard-fail and hard-skip allowlist semantics in `mde-verify`.
Proof: `scripts/verify-all.sh` skip logic + executed hard-skip allow/deny checks.
4. **adapt**: prebuilt image strategy with right-sized CI matrix.
Proof: https://github.com/devcontainers/images/tree/b873a927a301a64726aa60d23da7335dbf5c3450/.github/workflows ; https://www.reddit.com/r/github/comments/1j2i58k/speed_up_your_devcontainer_setup_with_prebuilt/
5. **adapt**: portable dotfiles bootstrap patterns only; strip user-specific secret assumptions.
Proof: https://github.com/felipecrs/dotfiles/blob/e35c74f9619a5bc88ead8969e9b16f209cab5554/install.sh ; https://github.com/MovieMaker93/devpod-dotfiles-chezmoi/blob/29ecaf3b42ff073e853716abfc9ec53167c1ff5c/run_onchange_install-packages.sh.tmpl
6. **adapt**: phase drift warnings into enforceable gates.
Proof: `scripts/mde-drift-check.sh` output (6 warnings on 2026-03-10).
7. **reject**: dotfiles-only patterns without runtime + CI verification evidence.
Proof: https://github.com/kutsan/dotfiles/blob/3cc076228581047550bb282148cba7454fe82264/home/.chezmoi.toml.tmpl
8. **adopt**: status JSON parseability as hard acceptance criterion.
Proof: `scripts/status-dashboard.sh --json` produced invalid JSON (`Invalid control character`).

## Executed Acceptance Proofs (2026-03-10)
1. `rg -n "MDE_PLATFORM=devcontainer|ensure-managed-configs\.sh" .devcontainer/post-create.sh docs/devcontainer.md`
Observed: expected bootstrap + managed sync hooks found.
2. `scripts/ensure-managed-configs.sh --check`
Observed: `chezmoi drift: clean`, `Managed configs: clean`.
3. `command -v mise && mise --version && mise tasks | rg '^mde:'`
Observed: mise present (`2026.3.6`) and `mde:*` tasks available.
4. `scripts/mde-drift-check.sh`
Observed: warnings for brew-owned python, PATH ordering, duplicate bun/uv/pixi ownership.
5. `scripts/mde-verify --json > /tmp/mde-verify.json`
Observed: `exit=1`, `overall=fail`, `hard_fail_count=1`.
6. `MDE_VERIFY_CONFIG=<hard-skip-unallowed> scripts/mde-verify --json`
Observed: `exit=1`, `status=skip`, `skip_allowed=False`.
7. `MDE_VERIFY_CONFIG=<hard-skip-allowed> scripts/mde-verify --json`
Observed: `exit=0`, `status=skip`, `skip_allowed=True`.
8. `scripts/status-dashboard.sh --json > /tmp/mde-status.json && python3 -c 'import json; json.load(...)'`
Observed: `status_exit=0` but `json_parse=fail` due control characters.

## Implementation Spec
1. Enforce mise-first execution
- Route bootstrap/update/verify/status via `mise run mde:*`.
- Add CI guard that fails if required tasks bypass mise.
2. Standardize devcontainer contracts
- Keep deterministic `onCreateCommand`/`postCreateCommand` lifecycle in `.devcontainer`.
- Add/retain dedicated devcontainer validation lane in CI.
3. Harden verification and policy gates
- Preserve current hard-fail + hard-skip semantics.
- Introduce staged promotion for drift warnings to hard failures.
4. Fix blocking gap
- Patch `scripts/status-dashboard.sh --json` to emit strict JSON with no ANSI/control characters.
- Add regression check: strict JSON parse step in `mde:verify`.
5. Dotfiles/bootstrap portability
- Reuse idempotent installer patterns.
- Exclude machine-personal secret/bootstrap assumptions from shared workflows.

## Exit Criteria
- `mde:verify` passes with no hard failures.
- `scripts/status-dashboard.sh --json` is strictly parseable JSON.
- Drift policy baseline agreed and enforced per phase plan.
- Evidence links and decisions remain synchronized in `reports/research-ros/2026-03-10-research-bundle.json`.
