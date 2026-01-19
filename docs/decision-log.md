# Decision Log

This file captures key choices made while aligning the environment with modern
best practices and your preferred tooling order.

## 2026-01 - Toolchain ownership
- Decision: `mise` owns runtimes (python/node/bun). pixi/uv are installed via
  their official installers when missing.
- Rationale: mise plugins for pixi/uv are not consistently maintained.
- Impact: runtime updates are stable; pixi/uv remain current via their native
  update paths.

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
- Impact: `UV_NO_MANAGED_PYTHON=1` set in templates and scripts; uv only manages
  tools/venvs.


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
