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
