# Team B Spec: Full Tool Coverage Matrix (mise Ownership)

## Scope
Build ownership classification for this machine and repo workflow.

## Baseline Observations
Current shell evidence already shows `node`, `python`, `go`, `rustc`, `bun`, `uv`, and `pixi` resolving to `mise` shims.

## Ownership Matrix (Initial)
| Category | Tools | Owner | Decision | Risk | Verification |
|---|---|---|---|---|---|
| Core runtimes | python,node,bun,go,rust | mise | Keep mise-owned | Low | `command -v <tool>` under shims |
| Python CLI mgmt | uv,pipx tools | mise+uv | Keep uv under mise runtime | Low | `uv --version`, `uv tool list` |
| JS CLIs | claude,codex,gemini and npm CLIs | mise npm backend | Move/keep via mise npm backend | Medium | `mise ls --installed`, command path |
| Binary dev tools | rg,fd,bat,eza,yq,jq,shellcheck,hadolint | mise aqua/ubi | Keep under mise where stable | Low | path + version check |
| Cloud CLIs | awscli,gh,azure-cli,gcloud | mixed | Prefer mise where stable; gcloud likely exception | Medium | health + auth smoke tests |
| OS apps/casks | docker desktop, fonts, GUI apps | brew cask | Remain brew-owned | Low | `brew list --cask` |

## Candidate Migration Classes
1. Remaining globally installed npm CLIs outside mise backend.
2. Standalone binaries in custom paths if stable backend exists.
3. Brew formulae that are pure developer CLIs with mature mise backends.

## Exception Classes
1. Tool has no stable backend in `mise`.
2. Tool requires privileged install/update flow.
3. Tool update semantics are vendor-managed and incompatible with shim model.

## Migration Scoring
- Low: already shim-compatible and no auth side effects.
- Medium: auth wrappers/env coupling.
- High: privileged services, launch agents, or system-linked binaries.

## Acceptance Criteria
- every tool class has owner + rationale + verification command
- migration candidates and exception candidates are explicit
