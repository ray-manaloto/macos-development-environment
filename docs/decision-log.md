# Decision Log

This file captures key choices made while aligning the environment with modern
best practices and your preferred tooling order.

## 2026-03 - Domain team routing and mirror-first research
- Decision: tooling and setup changes must be classified through
  `configs/mde-domain-catalog.json` and delegated to the owning domain SDLC
  team before they are adopted or remediated.
- Rationale: the `mise` orchestration teams were accumulating stale ecosystem
  assumptions and not consistently updating learnings.
- Impact: domain teams now own cookbook review, preset bundles, mirror-first
  reference bundles, authority records, and learning writeback.

## 2026-03 - Mirror-first reference contract
- Decision: official docs, upstream repos, cookbook pages, release notes, and
  curated tutorials/blogs are mirrored through `configs/mde-reference-sources.json`
  into `.artifacts/reference-mirror/`.
- Rationale: reduce repeated web searching and make agent runs cite the same
  source set.
- Impact: verification now treats missing or stale mirror metadata as policy
  drift instead of an optional convenience gap.

## 2026-03 - Python domain default bundle
- Decision: the `python-pixi-uv` domain defaults to a committed `pixi.toml`
  plus `pixi.lock` starter bundle under `configs/tool-bundles/python-pixi-uv/`.
- Rationale: `pixi.toml` is the first-class Pixi workspace manifest and matches
  the desired declarative direction for the Python domain.
- Impact: the Python domain team must still record the adopted realization path
  across `mise`, `pixi`, `uv`, optional `pyproject.toml`, and Pixi global
  manifests before imperative `pixi global install` or `uv tool install`
  patterns can be considered authoritative.

## 2026-01 - PATH ordering
- Decision: prioritize `mise` shims, then `bun`, then `pixi`, then `uv` tools,
  followed by Homebrew.
- Rationale: match your preferred precedence (mise > pixi > uv > pip; bun > node).
- Impact: deterministic resolution when tools overlap.

## 2026-01 - tmux installation on macOS
- Decision: default tmux install via Homebrew (pixi optional).
- Rationale: Homebrew tmux integrates better with macOS clipboard tooling.
- Impact: easier copy/paste; pixi can still be forced with `TMUX_INSTALL=pixi`.

## 2026-01 - tmux config defaults
- Decision: `tmux-256color`, RGB enabled, `set-clipboard on`, keep `C-b` prefix
  and add `C-a` as a secondary prefix.
- Rationale: modern terminal compatibility and fewer OS key conflicts.
- Impact: better color accuracy and fewer keybinding collisions.

## 2026-01 - Secrets management
- Decision: document a global `mise` config template but recommend per-project
  `.env` or `direnv` for repo-scoped secrets.
- Rationale: reduce accidental key leakage and scope access by project.
- Impact: safer defaults with flexibility for global envs.

## 2026-01 - Agent stack scope
- Decision: separate LangChain-only tooling from the broader agent CLI stack.
- Rationale: avoid mixing org-specific tooling with general-purpose CLIs.
- Impact: clearer installs and upgrades, fewer conflicts.

## 2026-01 - Launchd maintenance rename
- Decision: replace `com.github.domt4.homebrew-autoupdate` with
  `com.ray-manaloto.macos-dev-maintenance`.
- Rationale: the job now handles broader macOS dev setup maintenance.
- Impact: updated plist paths, logs, and script entrypoints.

## 2026-01 - Auto-fix and manager cleanup
- Decision: allow optional auto-fix to remove conflicting runtime managers
  (nvm/volta/asdf/pyenv) and sync managed configs.
- Rationale: reduce path conflicts and keep tooling aligned to mise-first
  preferences.
- Impact: `MDE_AUTOFIX=1` enables changes; strict mode optionally removes
  brew-managed runtimes.


## 2026-01 - Python runtime ownership
- Decision: disable uv-managed Python downloads by default and use mise as the
  single runtime source of truth.
- Rationale: avoid duplicated runtime installs and PATH conflicts.
- Impact: `UV_PYTHON_DOWNLOADS=never` set in templates and scripts; uv only
  manages tools/venvs.
- Update (2026-02): renamed from `UV_NO_MANAGED_PYTHON=1` to
  `UV_PYTHON_DOWNLOADS=never` to match the upstream uv variable name. All
  scripts were migrated; documentation updated in this cycle.


## 2026-01 - gcloud install source
- Decision: install Google Cloud SDK via the official installer under
  `/opt/google-cloud-sdk` and remove Homebrew `gcloud-cli`.
- Rationale: avoid Homebrew Python dependency conflicts with strict cleanup.
- Impact: `/opt/google-cloud-sdk/bin` added to PATH and maintained outside brew.

## 2026-01 - gcloud Python update
- Decision: use `gcloud components update-macos-python` (sudo) when needed to
  keep the SDK-managed Python current and rely on gcloud's internal venv.
- Rationale: keep gcloud runtime self-contained; `gsutil` is legacy and we use
  `gcloud storage` instead.
- Impact: no `CLOUDSDK_PYTHON` export needed; gcloud uses
  `~/.config/gcloud/virtenv` by default.

## 2026-01 - Secrets automation
- Decision: use 1Password service accounts with the `op` CLI for unattended
  secrets in automation scripts.
- Rationale: avoids interactive logins and keeps secrets out of shell startup
  files and launchd plists.
- Impact: maintenance script loads secrets via Keychain-backed
  `OP_SERVICE_ACCOUNT_TOKEN` and `MDE_OP_*_REF` mappings, with Keychain
  fallback for local-only runs.

## 2026-03 - fnox became the secret authority
- Decision: make `fnox` the primary secret authority, loaded through `mise`
  with host secrets migrated directly and repo-local 1Password overlays kept as
  plain `fnox.local.toml` config when needed.
- Rationale: this removes direct secret fetch shellouts from startup paths,
  keeps `mise` env caching in the loop, and avoids leaving migration-specific
  helper scripts behind once the host is in the target state.
- Impact: host secrets now resolve from `fnox`; shared 1Password mappings are
  expressed directly in gitignored `fnox.local.toml` overlays when needed.

## 2026-01 - LLVM install strategy
- Decision: install LLVM via Homebrew and keep it opt-in via shell toggles.
- Rationale: brew tracks the latest stable release; opt-in avoids SDK mismatches.
- Impact: `MDE_USE_LLVM=1` enables brewed LLVM in zsh without changing defaults.

## 2026-03 - Verification skip policy is explicit
- Decision: hard-check skips are failures by default and must be explicitly
  allowed per platform in `scripts/config/mde-verify.conf`.
- Rationale: prevent false-green verification when required checks were never
  executed.
- Impact: `scripts/verify-all.sh --json` now exits non-zero for unexpected hard
  skips and marks `skip_allowed` in output.

## 2026-03 - Devcontainer detection narrowed
- Decision: treat `DEVCONTAINER`/`CODESPACES` as `devcontainer`; treat plain
  `/.dockerenv` as `linux`.
- Rationale: avoid assuming every containerized environment is a VS Code
  devcontainer.
- Impact: platform-gated checks and docs now separate `devcontainer` behavior
  from generic Linux containers.

## 2026-03 - Local overrides are never managed
- Decision: keep `~/.oh-my-zsh/custom/99-local.zsh` outside chezmoi state and
  only create it when missing.
- Rationale: preserve user-owned local overrides across sync/apply cycles.
- Impact: managed sync is deterministic for core files while local customization
  remains stable.

## 2026-03 - Deterministic host remediation entrypoint
- Decision: add `scripts/mde-remediate.sh` and `mise run mde:remediate` as the
  single host-state repair command path.
- Rationale: make launchd/tooling/config/secrets remediation explicit and
  repeatable across operator runs.
- Impact: remediation is platform-gated (`macos` host-state steps become N/A on
  `devcontainer`/`linux`) and verification can be driven to a clean state with
  one command sequence.

## 2026-03 - Platform normalization parity (shell + scripts)
- Decision: normalize `MDE_PLATFORM=container` to `linux` in shell templates to
  match script runtime detection.
- Rationale: avoid divergent behavior between interactive shells and non-interactive verification scripts.
- Impact: platform-gated checks now behave consistently between `zsh` startup
  and script execution paths.
