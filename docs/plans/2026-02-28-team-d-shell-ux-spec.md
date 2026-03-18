# Team D Spec: oh-my-zsh Shell UX and Operator Contract

## Scope
Define standardized, low-friction operational commands and shell safety rules.

## PATH Contract
1. `mise` shims precede all other tool paths.
2. wrapper paths (`~/.local/bin`) remain ahead of manager binaries.
3. duplicates are removed deterministically.
4. shell startup must avoid expensive operations.

## Alias Contract (Required)
- `mde-status`: quick posture and inventories
- `mde-update`: full managed update cycle
- `mde-update-fast`: manager-only short cycle
- `mde-verify`: complete verification suite
- `mde-drift`: ownership/path drift report
- `mde-migrate`: dry-run/apply migration helper
- `mde-agents-review`: orchestrate document-review teams

## Safety Rules
1. no secrets hardcoded in alias/templates.
2. secret precedence is explicit (`.env` then optional secure override policy).
3. aliases point to repo scripts only (single source of truth).
4. backward-compatible aliases retained during transition window.

## Performance Rules
1. avoid network calls during shell init.
2. avoid command substitutions that trigger heavy checks at startup.
3. keep initialization deterministic between login and non-login shells.

## Acceptance Criteria
- alias set is complete and consistent with consolidated spec
- shell initialization remains deterministic and secure
