# Sync-Dotfiles Migration + Secrets Pipeline Simplification — Handoff

**Created:** 2026-04-08
**Status:** Plan ready, execution not started. Awaiting codex adversarial review before writing Python.
**Branch:** `main` (no feature branch yet)
**Owner:** @ray-manaloto

---

> ## ⚠️ PHASE 2 (SECRETS SIMPLIFICATION) IS SUPERSEDED
>
> **Phase 2 of this document is based on an incorrect architectural assumption** that `fnox sync --provider keychain` works. Two live CLI tests performed 2026-04-08 proved that both `fnox sync --provider keychain` AND `fnox import --provider keychain` are explicitly rejected by fnox with `provider_unsupported` errors. The fnox CLI requires an **encryption provider** (age, aws-kms) as the sync target; storage providers like keychain are not supported.
>
> **Replacement plan**: [`docs/plans/2026-04-08-secrets-crud-architecture-a.md`](./2026-04-08-secrets-crud-architecture-a.md)
>
> The replacement plan uses the fnox-canonical Architecture A: **Doppler → `fnox sync --provider age --global` → age-encrypted cache in `~/.config/fnox/config.toml` → `fnox activate zsh` hooks → shell env**. The age key is bootstrapped from Doppler (circular-but-functional via `DOPPLER_TOKEN` in Keychain).
>
> **Phase 1 (Chezmoi sync-dotfiles migration) of this document is UNAFFECTED** and remains valid. That work — migrating `scripts/ensure-managed-configs.sh` to `src/mde/maintain/sync_dotfiles.py` and repairing `~/.config/chezmoi/chezmoi.toml` — is independent of the secrets work and can execute before, during, or after the replacement plan.
>
> **When resuming post-`/clear`**: read the replacement plan first for the current secrets architecture; read this document's Phase 1 for the chezmoi fix. Phase 2 of this document can be skipped entirely.

---

## RESUME PROTOCOL (read this first)

If you are a new Claude session resuming this work, do these in order:

1. **Verify the working tree is where this doc expects it to be** — run:
   ```bash
   git status --short
   git log --oneline -5
   ```
   Compare against the "Working tree at handoff" section below. If diverged, STOP and ask the user what happened between sessions.

2. **Re-verify the live diagnostic facts** — run:
   ```bash
   fnox --version                                    # Expect: 1.20.0
   fnox provider list                                # Expect: age, doppler_dotfiles_dev_personal, keychain
   chezmoi source-path                               # Expect: ~/.local/share/chezmoi (WRONG — that's the bug)
   chezmoi managed | wc -l                           # Expect: 0 (WRONG — that's the bug)
   grep -c '^sourceDir' ~/.config/chezmoi/chezmoi.toml   # Expect: 0 (WRONG — that's the bug)
   ls templates/                                     # Expect: only agent_cloud.yaml
   grep -n -- '--source' scripts/ensure-managed-configs.sh   # Expect: lines 207 & 225
   ```
   Any divergence means the repo state moved since this handoff was written. STOP and reconcile.

3. **Check codex auth** — run:
   ```bash
   node "/Users/rmanaloto/.claude/plugins/cache/openai-codex/codex/1.0.3/scripts/codex-companion.mjs" setup --json | grep -A1 loggedIn
   ```
   At the time this handoff was written, codex was `loggedIn: false` with `ECONNREFUSED` on the broker socket. This was because the broker socket for the prior Claude session was dead. A fresh session (this one) should spin up a new broker. If still `loggedIn: false`, user needs to run `!codex login` again.

4. **Run the adversarial review on this plan file** — this is the blocker before writing any Python:
   ```
   /codex:adversarial-review --wait "focus on the sync-dotfiles python migration plan in docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md, specifically: (1) is the --source flag actually the root cause of the chezmoi.toml corruption, or am I wrong? (2) is the preflight check design safe for symlinked repos, locale, whitespace? (3) what's the correct bootstrap ordering for devcontainer when ensure-managed-configs.sh is deleted? (4) is dropping all fallback actually safe?"
   ```
   Return codex's JSON findings verbatim to the user. Do NOT start writing code until the user has read the findings and approved next steps.

5. **Only after codex findings are reviewed**, proceed to the Execution Order section below.

---

## EXECUTIVE SUMMARY

Two entangled simplifications, decided during a discovery session on 2026-04-08:

1. **Secrets pipeline simplification**: fnox 1.20.0 shipped a native Doppler provider, which makes our bespoke Python sync layer in `src/mde/secrets/` obsolete. Combined with: (a) user's 1Password subscription expired and must be removed from the pipeline, (b) the `age` provider is already dead code in the live config, and (c) the `mise-env-fnox` plugin has been disabled due to oh-my-zsh integration issues. End state: Doppler (source of truth) → `fnox sync` (1.20.0 native) → Keychain (service `mde-fnox`) → `fnox activate` (shell hook via oh-my-zsh mise plugin) → tools. Delete 6 of 7 Python files in `src/mde/secrets/`, 3 bash scripts, 1 skill, and all 1Password/age/sops references.

2. **Chezmoi sync-dotfiles migration**: `scripts/ensure-managed-configs.sh` (314 lines of bash) violates `.claude/rules/no-shell-scripts.md`, has dead `legacy_sync()` code pointing at a deleted `templates/` directory, and passes `--source "$CHEZMOI_SOURCE"` to `chezmoi apply` on lines 207 and 225 — which is the **suspected but unproven** root cause of `~/.config/chezmoi/chezmoi.toml` losing its `sourceDir` field and being replaced with a version that has stale tempdir PATH in `[scriptEnv]`. Migrate to `src/mde/maintain/sync_dotfiles.py`, no fallback, preflight-check chezmoi config, update 7 callsites, delete the bash script.

These blockers must be fixed before the secrets simplification can be executed, because almost every secrets doc change is a chezmoi template edit, and chezmoi is currently not actually managing any files on this machine. Chezmoi breakage is the highest-priority fix.

---

## DECISIONS LOCKED IN (do not re-litigate)

User made these choices during the 2026-04-08 session. Carry them forward verbatim:

1. **Path A** over Path B: fix chezmoi properly first before any other work. No band-aids on deployed files.
2. **Python module, not minimal bash patch**: the sync-dotfiles logic becomes `src/mde/maintain/sync_dotfiles.py` per `no-shell-scripts.md`.
3. **No fallback**: "it should just work." Drop `legacy_sync()` entirely. Drop chezmoi-trust-error fallback regex. Chezmoi is required; fail loudly if missing.
4. **All-in-one migration**: update all 7 callsites + Python module + delete bash script + delete bash test + update devcontainer hash manifest + docs in a single PR.
5. **Pydantic BaseModel over dataclass** for `SyncResult` — consistent with `library-first.md` and the rest of `src/mde/`.
6. **Drop age provider entirely**: level (a) — remove as active provider, delete sops wrappers, delete sops shell scripts. Level (b) — leave the `age` CLI tool in Brewfile/mise if available for non-secrets uses (not an active decision; I'll default to "leave" unless user says otherwise in next session).
7. **Drop 1Password entirely**: subscription expired. No `fnox set ... --provider age` patterns referencing `OP_SERVICE_ACCOUNT_TOKEN`. Remove from tool list, Brewfile, skills, docs.
8. **Use fnox 1.20.0 native Doppler provider** for source → encryption sync. Not the bespoke Python layer. Not the Doppler CLI directly.
9. **Point fnox at `dotfiles/dev_personal`**, not `dev`. `dev_personal` is a strict superset (48 shared keys + 2 extras: `GITHUB_API_TOKEN`, `MISE_GITHUB_TOKEN`). Verified via `doppler secrets --only-names` comparison.
10. **`fnox activate` as the shell integration**, not `mise-env-fnox` plugin. User re-enabled `mise-env-fnox` in `home/dot_config/mise/config.toml.tmpl` during this session for diagnostic purposes, but the eventual state is: drop `mise-env-fnox`, add `mise` to oh-my-zsh plugins (already done in template), use `eval "$(fnox activate zsh)"` in `.zshrc` (NOT yet done).
11. **Adversarial review via `/codex:adversarial-review --wait`** against this plan file before writing Python. Two prior attempts via `codex:codex-rescue` stalled due to ECONNREFUSED on the broker socket and unescaped regex in self-initiated ripgrep commands.

---

## VERIFIED FACTS (with evidence, captured 2026-04-08 20:24)

### fnox

- **Version**: `fnox 1.20.0` (confirms native Doppler provider support)
- **Providers declared** (`fnox provider list`):
  - `age`
  - `doppler_dotfiles_dev_personal` ← **TYPO** (missing "l")
  - `keychain`
- **Global config at `~/.config/fnox/config.toml`**:
  ```toml
  if_missing = "warn"

  [providers]
  keychain = { type = "keychain", service = "mde-fnox" }
  # keychain = { type = "keychain", service = "fnox" }    ← old service, commented out
  doppler_dotfiles_dev_personal = { type = "doppler", project = "dotfiles", config = "dev_personal" }
  ```
- **Repo-level `fnox.toml`**: declares 43 secret names, all `provider = "keychain"` + `if_missing = "ignore"`. Comment line 3 mentions 1Password — needs updating.

### Doppler

- **Project**: `dotfiles`
- **Configs compared**:
  - `dev`: 48 secrets (50 raw lines from `doppler secrets --only-names`, minus 2 header lines)
  - `dev_personal`: 50 secrets (52 raw lines minus 2 header lines)
- **Extras in `dev_personal`** (strict superset):
  - `GITHUB_API_TOKEN`
  - `MISE_GITHUB_TOKEN`
- **Shared keys**: 48
- **Implication**: Pointing fnox at `dev_personal` loses nothing from `dev` and gains 2 personal GitHub tokens.

### Chezmoi (BROKEN)

- **`chezmoi source-path`** returns `/Users/rmanaloto/.local/share/chezmoi` (the default). Should return `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/home`.
- **`chezmoi managed`** returns 0 lines (empty). Should return dozens of dotfiles.
- **`~/.config/chezmoi/chezmoi.toml`** has:
  - `[data]` with `is_dev_computer`, `is_personal`, `is_ephemeral`, `is_ci` (none of which are in the template)
  - `[scriptEnv].PATH` with stale tempdir `/var/folders/z4/.../tmp.nlvpGMEnLY/.local/bin:...tmp.nlvpGMEnLY/.local/share/mise/shims:...`
  - `[git].autoCommit`, `commitMessageTemplate`
  - `[diff].pager = "delta"`
  - **Missing**: `sourceDir` (grep count = 0), `[data.git]`, `[doppler]`
  - mtime: Apr 7 17:18:55 2026 (actively being rewritten by automation, NOT a months-old stale file)
- **Template `home/.chezmoi.toml.tmpl`** (correct and current):
  ```
  {{- $remote := or ... -}}
  {{- $gitName := promptStringOnce . "git.name" "Git author name" -}}
  {{- $gitEmail := promptStringOnce . "git.email" "Git author email" -}}
  sourceDir = {{ .chezmoi.sourceDir | dir | quote }}

  [data]
    remote = {{ $remote }}

  [data.git]
    name = {{ $gitName | quote }}
    email = {{ $gitEmail | quote }}

  [doppler]
    project = "dotfiles"
    config = "dev"                ← NOTE: hardcoded to "dev", should be "dev_personal"
  ```
- **`.chezmoiroot`** = `home` (correct)
- **`~/.zshrc` vs `home/dot_zshrc.tmpl`**: different inodes (136209532 vs 136540378), no symlink, no hardlink. The deployed file was NEVER generated from the template by chezmoi. Same story for `~/.config/mise/config.toml`.

### Templates directory (DEAD CODE)

- **`templates/`** contains only `agent_cloud.yaml` (442 bytes, last touched Jan 18).
- **`templates/oh-my-zsh/`** does not exist.
- **`templates/zprofile/`** does not exist.
- **`scripts/ensure-managed-configs.sh:242-281`** (`legacy_sync()`) copies files from `templates/oh-my-zsh/*`, `templates/tmux.conf`, `templates/zprofile/*` — **every source path is deleted**. `legacy_sync()` has been dead on arrival since before this session.

### ensure-managed-configs.sh (THE BUG)

- **Line 207**: `if chezmoi diff --source "$CHEZMOI_SOURCE" >"$diff_out" 2>"$diff_err"; then`
- **Line 225**: `if chezmoi apply --force --no-tty --source "$CHEZMOI_SOURCE" 2>"$apply_err"; then`
- **Line 15**: fallback regex: `"not trusted|error parsing config file|source state.+not initialized|run.*chezmoi init|config file.+not found"` — if any of these match stderr, falls through to `legacy_sync()` (which is dead).
- **`CHEZMOI_SOURCE`** = `"${MDE_CHEZMOI_SOURCE:-$REPO_ROOT/home}"` at line 7.
- **Hypothesis (unproven)**: passing `--source` to `chezmoi apply` causes the persisted `~/.config/chezmoi/chezmoi.toml` to be regenerated without `sourceDir`, because the `--source` value is ephemeral and not persisted. This is what the adversarial review should verify or refute.
- **`src/mde/maintain/update.py:229`** runs `["chezmoi", "apply", "--force"]` WITHOUT `--source` — that callsite is clean.

### Callers of ensure-managed-configs.sh (7)

| # | File | Lines | Role |
|---|---|---|---|
| 1 | `.mise.toml` | 3 | `mde:sync-dotfiles` mise task. PRIMARY CORRUPTION SOURCE — runs against real chezmoi + real HOME |
| 2 | `scripts/mde-remediate.sh` | 102, 104 | Remediation pipeline; passes through `MDE_PLATFORM` |
| 3 | `scripts/macos-dev-maintenance.sh` | 220-223 | launchd daily runner |
| 4 | `.devcontainer/post-create.sh` | 74, 168 | Container bootstrap; ALSO hashed into `bootstrap_manifest_hash()` at line 74 |
| 5 | `scripts/devcontainer-lifecycle-smoke.sh` | 68, 76 | Devcontainer smoke test |
| 6 | `scripts/tests/chezmoi-fallback.test.sh` | 5 (and throughout) | Bash test of fallback behavior. Uses fake chezmoi binary — does NOT corrupt real config. Will be replaced by pytest. |
| 7 | `scripts/tests/devcontainer-bootstrap-contract.test.sh` | 129 | Greps the path as a literal string; not an executor |

Plus metadata references (non-executable) in `configs/mde-modernization-matrix.json` (3 mentions).

### Codex

- **Version**: `codex-cli 0.118.0; advanced runtime available`
- **Node**: `v25.9.0`
- **npm**: `11.12.1`
- **Auth status (at handoff time)**: `loggedIn: false`, `detail: "connect ECONNREFUSED /var/folders/z4/.../cxc-cD82Gq/broker.sock"`, `source: app-server`
- **Review gate**: enabled for this repo (via `/codex:setup --enable-review-gate` during 2026-04-08 session)
- **Why login shows false**: the broker socket is tied to the current Claude Code session's shared runtime. After `/clear`, a new session will create a new socket. If user ran `!codex login` during the old session, the token should persist; the next session just needs to spin up a fresh broker. If the next session still shows `loggedIn: false`, re-run `!codex login`.

### Working tree at handoff (`git status --short`)

```
 M .claude/rules/observability-stack.md
 M .claude/settings.json
 M .gitignore                                         ← modified this session: added $HOME/ rule
 M .mise.toml
 D .omc/state/last-tool-error.json
 M CLAUDE.md
 M docs/research/source-catalog.md
 M home/Brewfile.tmpl
 M home/dot_oh-my-zsh/custom/10-mde-core.zsh
 M home/dot_tmux.conf
 M home/dot_zprofile.d/macos-dev-env.zsh
 M home/dot_zshrc.tmpl                                ← modified this session: plugins=(git gh mise)
 M mise.lock
 M scripts/agent-hud
 M scripts/status-dashboard.sh
?? .claude/claude-octopus.local.md
?? scripts/tests/mise-shell-bootstrap.test.sh        ← untracked; likely created $HOME/ shadow dir
```

Most modifications predate this session (see session-start git status in chat log). The only changes made during this session are the two explicitly marked above, plus deletion of the `$HOME/` shadow directory (208K, not in git).

---

## WORK COMPLETED THIS SESSION (2026-04-08)

1. **Deleted `$HOME/` shadow directory** at repo root (208K). Contents were: mise cache leakage, claude-octopus state, full fnox-env plugin git clone. All transient, canonical copies exist in the real `~`. Command used: `rm -rf '$HOME'` (single-quoted to prevent expansion).

2. **Added `$HOME/` rule to `.gitignore`** (line 53ish) with explanatory comment pointing at `scripts/tests/mise-shell-bootstrap.test.sh` as the likely culprit. Verified via `git check-ignore -v '$HOME/'`.

3. **Edited `home/dot_zshrc.tmpl:80`**: `plugins=(git gh)` → `plugins=(git gh mise)`. **NOTE: this edit is ineffective** until chezmoi is repaired, because `~/.zshrc` is not actually managed by chezmoi right now. The edit is correct for the target state, just not deployed.

4. **Verified Doppler config superset**: `dev_personal` strictly contains `dev`. See "Doppler" section above.

5. **Ran `/codex:setup --enable-review-gate`**: enabled stop-time review gate, but codex is not authed (see Codex section above).

6. **Dispatched two adversarial reviews via `codex:codex-rescue`** — both stalled. First stalled on self-initiated ripgrep with unescaped regex. Second (status ping) resumed an idle wrapper agent which just re-forwarded the original prompt. **Zero findings delivered.** Root cause of the stalls: codex was not authed and the broker socket was dead. Resolution: re-run in the next session via `/codex:adversarial-review --wait` after confirming codex auth.

---

## OPEN QUESTIONS / UNPROVEN HYPOTHESES

These are explicit unknowns. Do NOT proceed past them silently — either verify or flag to the user.

### Q1: Is `--source` actually the root cause of chezmoi.toml corruption?

**Hypothesis**: `chezmoi apply --source "$CHEZMOI_SOURCE"` triggers config regeneration without persisting `sourceDir`, causing every invocation of `ensure-managed-configs.sh` to wipe the field.

**Evidence for**: chezmoi.toml mtime matches recent automation runs; `ensure-managed-configs.sh` is the only callsite using `--source`; `update.py:229` uses no `--source` and is clean.

**Evidence against**: I have NOT read chezmoi's source code or confirmed docs behavior for `--source` on `apply`. Chezmoi may treat `--source` as purely ephemeral and never regenerate config. In that case, the corruption source is somewhere else entirely.

**How to resolve**: (a) Read chezmoi source code or official docs for `--source` behavior on `apply`. (b) Run `chezmoi apply --source "$PWD/home" --force` in isolation and `stat` the config file before/after to see if mtime changes. (c) Let codex adversarial review do this verification.

### Q2: Source of `[scriptEnv]` tempdir PATH pollution?

**What's polluted**: `~/.config/chezmoi/chezmoi.toml` has `[scriptEnv].PATH = "/var/folders/z4/.../tmp.nlvpGMEnLY/.local/bin:...tmp.nlvpGMEnLY/.local/share/mise/shims:..."` — a deleted tempdir.

**Known**: `[scriptEnv]` is populated at `chezmoi init` time, not `chezmoi apply`. Something is calling `chezmoi init` (or equivalent) with a fake `HOME=$tmp_dir` and the real `~/.config/chezmoi/` as the output target simultaneously.

**Suspects ruled out**:
- `scripts/tests/chezmoi-fallback.test.sh` uses a stub chezmoi binary in `$tmp_bin` — cannot write real config.
- `scripts/tests/mde-cache-policy.test.sh` does `export HOME="$tmp_home"` but only sources a lib, never invokes chezmoi/mise binaries.
- `scripts/tests/mise-shell-bootstrap.test.sh` uses a stub mise binary and HOME-prefixed subshells, not `export HOME`.

**Still unchecked**: any test or script that runs real `chezmoi init`, `chezmoi execute-template`, or any Go binary that goes through `getpwuid()` (macOS Directory Services) instead of honoring `$HOME`.

**How to resolve**: (a) `git log --all -p -- ~/.config/chezmoi/chezmoi.toml` won't work (outside repo). (b) Add a `fs_usage` or `opensnoop` trace filtered on `~/.config/chezmoi/chezmoi.toml` and run the test suite. (c) Ask codex to investigate.

**Why this matters for the migration**: if the Python sync-dotfiles migration doesn't fix Q2, `~/.config/chezmoi/chezmoi.toml` will be re-polluted on the next test run, and we're back to square one. Q1 and Q2 might be the same bug or might be independent.

### Q3: What actually broke `mise-env-fnox`?

User's report (verbatim from session): "the problem was with the integration with oh-my-zsh. if you add mise in: ~/.zshrc from: plugins=(git gh) to plugins=(git gh mise)". The implication is that the mise oh-my-zsh plugin conflicts with `mise-env-fnox` plugin in some way.

**Status**: not diagnosed. User said "re-enable those and then run a new bash tool and review what is going on" but the chezmoi breakage investigation derailed this path before we got to actually running a diagnostic shell.

**How to resolve**: After chezmoi is repaired and sync-dotfiles migration is done, enable BOTH (mise oh-my-zsh plugin AND fnox-env) temporarily, spawn a fresh bash with `bash -lx` tracing, and capture the interaction. The oh-my-zsh mise plugin source is at `$ZSH/plugins/mise/mise.plugin.zsh`; fnox-env hooks are in `~/.local/share/mise/plugins/fnox-env/hooks/mise_env.lua`.

### Q4: Does the preflight check handle edge cases?

**Proposed check**: `Path(subprocess.run(["chezmoi", "source-path"]).stdout.strip()) == get_paths().project_dir / "home"`.

**Fails on**:
- Symlinked repo (`source-path` returns resolved path, `project_dir` may be unresolved)
- Trailing whitespace/newline differences across platforms
- Locale affecting path encoding
- `MDE_PROJECT_DIR` env var being set to a different path than CWD's git root

**Proposed fix**: `Path(...).resolve()` on both sides, and use `MDE_PROJECT_DIR` as the authoritative source with fallback to git rev-parse. Still has corner cases.

**How to resolve**: codex should stress-test this in the adversarial review.

---

## PHASE 1: Chezmoi Sync-Dotfiles Migration

### Goal

Replace `scripts/ensure-managed-configs.sh` with `src/mde/maintain/sync_dotfiles.py`. Make chezmoi actually work. No fallback code paths.

### New Python module: `src/mde/maintain/sync_dotfiles.py`

Target ~200 lines. Structure:

```python
"""Sync managed dotfiles via chezmoi.

Replaces scripts/ensure-managed-configs.sh. Migrated to Python per
.claude/rules/no-shell-scripts.md.

CRITICAL DESIGN DECISION: this module does NOT pass --source to chezmoi
apply/diff. The prior bash script did, which is the suspected cause of
~/.config/chezmoi/chezmoi.toml losing its sourceDir field on every
invocation (see docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md).
The correct pattern is to persist sourceDir once via chezmoi init, then
rely on the persisted config.

No legacy fallback: chezmoi is required. The prior script had a
legacy_sync() path that copied files from templates/, but that
directory has been empty for months (only templates/agent_cloud.yaml
remains). Dead code removed.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mde.lib.paths import get_paths
from mde.log import logger


class SyncResult(BaseModel):
    """Result of a sync-dotfiles invocation.

    Uses Pydantic per .claude/rules/library-first.md — consistent with
    the rest of src/mde/ which uses pydantic-settings and domain models.
    """
    mode: str = Field(..., description="'check' or 'apply'")
    drift_detected: bool = False
    messages: list[str] = Field(default_factory=list)
    post_sync_completed: bool = False

    @property
    def exit_code(self) -> int:
        return 1 if self.drift_detected else 0


def sync_dotfiles(*, check: bool = False) -> SyncResult:
    """Sync managed dotfiles via chezmoi.

    Args:
        check: If True, only report drift (`chezmoi diff`). No writes.

    Returns:
        SyncResult with drift state and message log.

    Raises:
        SystemExit: If chezmoi is not installed or sourceDir is misconfigured.
            No fallback — this is a hard failure per user decision 2026-04-08.
    """
    result = SyncResult(mode="check" if check else "apply")

    _require_chezmoi(result)
    _preflight_sourcedir(result)
    _run_chezmoi(result, check=check)

    if not check and not result.drift_detected:
        _post_sync(result)

    return result


def _require_chezmoi(result: SyncResult) -> None:
    """Fail loudly if chezmoi is not on PATH."""
    if not shutil.which("chezmoi"):
        logger.error("chezmoi_not_installed")
        result.messages.append(
            "chezmoi is required but not installed. Install via mise: mise use chezmoi"
        )
        raise SystemExit(2)


def _preflight_sourcedir(result: SyncResult) -> None:
    """Verify chezmoi's persisted sourceDir points at our repo's home/ dir.

    This REPLACES the old `--source $CHEZMOI_SOURCE` approach. If sourceDir
    is wrong, fail loudly with a repair command instead of silently passing
    --source (which is suspected of causing the sourceDir to be wiped).

    Edge cases handled:
    - Symlinked repo: uses .resolve() on both sides
    - Trailing whitespace: strips stdout
    - Missing source-path output: treats as error
    """
    expected = (get_paths().project_dir / "home").resolve()

    try:
        proc = subprocess.run(
            ["chezmoi", "source-path"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.bind(error=str(e)).error("chezmoi_source_path_failed")
        raise SystemExit(2)

    if proc.returncode != 0:
        logger.bind(stderr=proc.stderr.strip()).error("chezmoi_source_path_nonzero")
        result.messages.append(
            f"chezmoi source-path failed: {proc.stderr.strip()}. "
            f"Fix: chezmoi init --source={expected} --force"
        )
        raise SystemExit(2)

    actual_raw = proc.stdout.strip()
    if not actual_raw:
        result.messages.append(
            f"chezmoi source-path returned empty. "
            f"Fix: chezmoi init --source={expected} --force"
        )
        raise SystemExit(2)

    actual = Path(actual_raw).resolve()
    if actual != expected:
        logger.bind(expected=str(expected), actual=str(actual)).error(
            "chezmoi_sourcedir_mismatch"
        )
        result.messages.append(
            f"chezmoi sourceDir is {actual}, expected {expected}. "
            f"This usually means ~/.config/chezmoi/chezmoi.toml lost its "
            f"sourceDir field (see docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md). "
            f"Fix: chezmoi init --source={expected} --force"
        )
        raise SystemExit(2)


def _run_chezmoi(result: SyncResult, *, check: bool) -> None:
    """Run chezmoi diff or apply. No --source flag."""
    if check:
        cmd = ["chezmoi", "diff"]
    else:
        cmd = ["chezmoi", "apply", "--force", "--no-tty"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        result.messages.append(f"chezmoi {cmd[1]} timed out (120s)")
        result.drift_detected = True
        return

    if proc.returncode != 0:
        logger.bind(stderr=proc.stderr, stdout=proc.stdout).error(f"chezmoi_{cmd[1]}_failed")
        result.messages.append(f"chezmoi {cmd[1]} failed: {proc.stderr.strip() or proc.stdout.strip()}")
        result.drift_detected = True
        return

    if check and proc.stdout.strip():
        result.drift_detected = True
        result.messages.append("chezmoi diff: drift detected")


def _post_sync(result: SyncResult) -> None:
    """Post-sync tasks: bun completion symlink, zprofile include, wrapper scripts.

    Only runs in apply mode after successful chezmoi apply.
    """
    _ensure_zprofile_include(result)
    _sync_bun_completion(result)
    _sync_wrapper_scripts(result)
    result.post_sync_completed = True


def _ensure_zprofile_include(result: SyncResult) -> None:
    """Ensure ~/.zprofile sources ~/.zprofile.d/macos-dev-env.zsh."""
    zprofile = Path.home() / ".zprofile"
    sentinel = "macos-dev-env.zsh"
    if zprofile.exists() and sentinel in zprofile.read_text(errors="ignore"):
        return
    block = (
        "\n# Managed by macos-development-environment\n"
        'if [ -f "$HOME/.zprofile.d/macos-dev-env.zsh" ]; then\n'
        '  . "$HOME/.zprofile.d/macos-dev-env.zsh"\n'
        "fi\n"
    )
    with zprofile.open("a") as f:
        f.write(block)
    result.messages.append(f"appended zprofile include to {zprofile}")


def _sync_bun_completion(result: SyncResult) -> None:
    """Symlink ~/.bun/_bun into oh-my-zsh completions if bun is installed."""
    bun_src = Path.home() / ".bun" / "_bun"
    if not bun_src.exists():
        return
    target_dir = Path.home() / ".oh-my-zsh" / "custom" / "completions"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "_bun"
    if target.is_symlink() and target.resolve() == bun_src.resolve():
        return
    if target.exists():
        target.unlink()
    target.symlink_to(bun_src)
    result.messages.append(f"symlinked {target} -> {bun_src}")


def _sync_wrapper_scripts(result: SyncResult) -> None:
    """Install wrapper scripts into ~/.local/bin/.

    These are the scripts the old bash had via sync_exec:
    - langsmith-wrapper.sh -> langsmith-fetch, langsmith-migrator, langsmith-mcp-server
    - fabric-wrapper.sh -> fabric

    UNCERTAINTY: these wrapper scripts may not all still exist in the repo.
    Check scripts/langsmith-wrapper.sh and scripts/fabric-wrapper.sh before
    writing this function. If either is missing, drop the corresponding target.
    """
    ...  # TODO: verify sources exist, then implement
```

### CLI wiring: `src/mde/cli.py`

Add a `maintain sync-dotfiles` subcommand. The CLI uses lazy imports per the repo convention:

```python
# In the maintain dispatcher:
def _maintain_sync_dotfiles(args: list[str]) -> int:
    from mde.maintain.sync_dotfiles import sync_dotfiles
    check = "--check" in args or "--diff" in args
    result = sync_dotfiles(check=check)
    for msg in result.messages:
        print(msg)
    return result.exit_code
```

### Tests: `tests/mde/test_sync_dotfiles.py`

pytest-native. Replaces `scripts/tests/chezmoi-fallback.test.sh` (which tests fallback behavior we're deleting). New test coverage:

- `test_missing_chezmoi_raises_systemexit`: monkeypatch `shutil.which` to return None, expect `SystemExit(2)`.
- `test_sourcedir_mismatch_raises_systemexit`: mock `subprocess.run` to return a different path, expect `SystemExit(2)` and correct repair message.
- `test_sourcedir_empty_raises_systemexit`: mock `subprocess.run` to return empty stdout.
- `test_sourcedir_matches_proceeds_to_apply`: happy path, mock chezmoi source-path + chezmoi apply, expect `SyncResult` with `drift_detected=False`.
- `test_check_mode_detects_drift`: mock `chezmoi diff` with non-empty stdout, expect `drift_detected=True`, `exit_code=1`.
- `test_check_mode_no_drift_clean`: mock `chezmoi diff` with empty stdout.
- `test_apply_failure_reports_drift`: mock `chezmoi apply` returncode != 0.
- `test_apply_timeout_reports_drift`: mock `subprocess.TimeoutExpired`.
- `test_post_sync_ensures_zprofile_include_when_missing`: use `tmp_path`, patch `Path.home`, verify block appended.
- `test_post_sync_skips_bun_completion_when_bun_not_installed`: create no `~/.bun/_bun`, verify no symlink attempted.
- `test_post_sync_creates_bun_symlink_when_bun_installed`: create `tmp_path/.bun/_bun`, verify symlink.
- `test_post_sync_replaces_wrong_bun_symlink`: existing symlink pointing elsewhere.
- `test_preflight_handles_symlinked_repo`: the `.resolve()` edge case.

Use `monkeypatch` for HOME (`monkeypatch.setenv("HOME", str(tmp_path))` and `monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)`), `tmp_path` for all filesystem, and mock `subprocess.run` rather than installing fake binaries. Much faster than the bash test; deterministic.

### Callsite migration (7 callsites)

Replace every invocation:
```bash
# Old                                               New
scripts/ensure-managed-configs.sh                   uv run mde-py maintain sync-dotfiles
scripts/ensure-managed-configs.sh --check           uv run mde-py maintain sync-dotfiles --check
scripts/ensure-managed-configs.sh --diff            uv run mde-py maintain sync-dotfiles --check
```

Note: the old script accepts `--no-chezmoi` and `--legacy` — both become no-ops (fallback is deleted). Any caller passing these needs the flag removed.

**Per-file changes**:

1. **`.mise.toml:3`**:
   ```toml
   # OLD
   [tasks."mde:sync-dotfiles"]
   description = "Sync managed shell/config files (chezmoi-first, legacy fallback)"
   run = "scripts/ensure-managed-configs.sh"

   # NEW
   [tasks."mde:sync-dotfiles"]
   description = "Sync managed shell/config files via chezmoi"
   run = "uv run mde-py maintain sync-dotfiles"
   ```

2. **`scripts/mde-remediate.sh:102,104`**: replace both lines with `uv run mde-py maintain sync-dotfiles --check` and `uv run mde-py maintain sync-dotfiles` respectively. Drop the `MDE_PLATFORM=...` prefix if no longer used (verify).

3. **`scripts/macos-dev-maintenance.sh:220-223`**: replace the `"$SCRIPT_DIR/ensure-managed-configs.sh" || true` block with `(cd "$REPO_ROOT" && uv run mde-py maintain sync-dotfiles) || true`. Note: the `|| true` is load-bearing because this runs in launchd and must not fail the daily cron.

4. **`.devcontainer/post-create.sh`**: TWO changes:
   - **Line 74** in `bootstrap_manifest_hash()`: replace `"$REPO_ROOT/scripts/ensure-managed-configs.sh"` with `"$REPO_ROOT/src/mde/maintain/sync_dotfiles.py"`. This hashes the Python module into the devcontainer refresh manifest so reinstalls trigger when it changes.
   - **Line 168** in `sync_managed_configs()`: replace `(cd "$REPO_ROOT" && scripts/ensure-managed-configs.sh)` with `(cd "$REPO_ROOT" && uv run mde-py maintain sync-dotfiles)`.

5. **`scripts/devcontainer-lifecycle-smoke.sh:68,76`**: replace `scripts/ensure-managed-configs.sh --check` (both) with `uv run mde-py maintain sync-dotfiles --check`.

6. **`scripts/tests/chezmoi-fallback.test.sh`**: **DELETE** this file entirely. Replaced by pytest in `tests/mde/test_sync_dotfiles.py`.

7. **`scripts/tests/devcontainer-bootstrap-contract.test.sh:129`**: this is a `grep -q 'scripts/ensure-managed-configs.sh' "$POST_CREATE"` assertion. Update the grep pattern to match the new invocation: `grep -q 'uv run mde-py maintain sync-dotfiles' "$POST_CREATE"`.

### Deletions

- `scripts/ensure-managed-configs.sh` (314 lines)
- `scripts/tests/chezmoi-fallback.test.sh` (99 lines)

### Metadata updates

- `configs/mde-modernization-matrix.json`: 3 references to `scripts/ensure-managed-configs.sh`. Update to point at `src/mde/maintain/sync_dotfiles.py` or the CLI invocation as appropriate for the schema.

### One-time repair of `~/.config/chezmoi/chezmoi.toml`

**After** the Python module exists and all callsites updated:

```bash
# 1. Snapshot the corrupted config for rollback
cp ~/.config/chezmoi/chezmoi.toml ~/.config/chezmoi/chezmoi.toml.backup-2026-04-08

# 2. Regenerate from the template with correct sourceDir
cd ~/dev/github/ray-manaloto/macos-development-environment
chezmoi init --source="$PWD/home" --force

# 3. Verify
chezmoi source-path        # Expect: .../macos-development-environment/home
chezmoi managed | head     # Expect: non-empty list of dotfiles
chezmoi diff               # Expect: drift between deployed and template

# 4. Review the drift carefully — ~/.zshrc and ~/.config/mise/config.toml
#    have been hand-edited for months and never propagated to the template.
#    Promote intentional changes into home/ templates, then apply.

# 5. Apply
chezmoi apply --force
```

**CRITICAL**: Step 4 is the point where the user decides drift resolution. Do not auto-apply without showing the user what would change.

### Doc updates for Phase 1

- **`.claude/rules/chezmoi-config-safety.md`**: add a new section "Never use `--source` on `chezmoi apply` in automation scripts". Reference this plan file.
- **`docs/tool-audit/*.md`** (if any mention `ensure-managed-configs.sh`): spot-update.
- **This file**: mark Phase 1 complete at the bottom.

### Phase 1 success criteria

- [ ] `uv run mde-py maintain sync-dotfiles` runs without errors
- [ ] `uv run mde-py maintain sync-dotfiles --check` reports clean
- [ ] `chezmoi source-path` returns the repo's `home/` dir
- [ ] `chezmoi managed` returns a non-empty file list
- [ ] `grep -c sourceDir ~/.config/chezmoi/chezmoi.toml` returns > 0
- [ ] `~/.config/chezmoi/chezmoi.toml` has `[data.git]` and `[doppler]` sections
- [ ] `uv run mde-py quality` passes (6/6)
- [ ] `uv run mde-py validate --all` passes (including `validate_chezmoi` checks)
- [ ] `scripts/ensure-managed-configs.sh` does not exist in the repo
- [ ] All 7 callsites updated
- [ ] `pytest tests/mde/test_sync_dotfiles.py -v` all pass
- [ ] The `.mise.toml` task `mde:sync-dotfiles` works end-to-end: `mise run mde:sync-dotfiles`

---

## PHASE 2: Secrets Pipeline Simplification

**Blocked by**: Phase 1 complete. Almost all doc changes in Phase 2 are to chezmoi-templated files in `home/` — without working chezmoi, edits don't propagate.

### Goal

Collapse `src/mde/secrets/` (7 files, ~400 LOC) into a thin wrapper around fnox 1.20.0. Remove 1Password, age, and sops entirely. End with 3-command interface: `fnox sync`, `fnox list`, `fnox activate`.

### End-state architecture

```
Doppler (dotfiles/dev_personal)      ← cloud SoT (50 secrets)
     ↓ fnox sync (native 1.20.0 Doppler provider)
Keychain service="mde-fnox"          ← offline cache
     ↓ fnox activate (zsh hook in .zshrc)
shell env → mise tasks → tools
```

Three active providers in `~/.config/fnox/config.toml`: `keychain`, `doppler_dotfiles_dev_personal` (typo fixed). No age. No sops. No 1Password. No `mise-env-fnox` plugin.

### Sub-phase 2a: Fix the typo + verify the native Doppler provider

```bash
# 1. Rename the fnox provider typo
#    Edit ~/.config/fnox/config.toml directly:
#    doppler_dotfiles_dev_personal → doppler_dotfiles_dev_personal

# 2. Verify the provider works
fnox provider test doppler_dotfiles_dev_personal
# Expect: success, connection to Doppler confirmed

# 3. Dry-run the sync
fnox sync --source doppler_dotfiles_dev_personal --provider keychain --global --dry-run
# Expect: list of ~50 keys that would be written

# 4. Real sync
fnox sync --source doppler_dotfiles_dev_personal --provider keychain --global --force

# 5. Verify
fnox list                           # Expect: ~50 entries under provider (keychain)
echo $?                             # Expect: 0
```

### Sub-phase 2b: Delete 1Password artifacts

Files to delete:
- `scripts/mde-sops-secrets-backup-1password.sh`
- `scripts/mde-sops-secrets-refresh.sh`
- `scripts/mde-sops-secrets-import-keychain.sh`
- `.agents/skills/1password-fnox/` (entire directory)
- `src/mde/secrets/keychain.py` (wraps `mde-sops-secrets-import-keychain.sh`, both die together)

Files to edit:
- **`.mise.toml`**: remove `[tasks."mde:secrets:backup:1password"]` block (lines 129-131)
- **`home/.chezmoidata/tools.yaml:95-97`**: remove the `infrastructure_darwin` entry for `1password-cli`
- **`home/Brewfile.tmpl`**: if `1password-cli` or `1password` cask exists, remove
- **`.claude/rules/secrets-management.md`**: delete line 65 (`OP_SERVICE_ACCOUNT_TOKEN (fnox provider: age, not in Doppler)`) and line 75 ("Backup tier: age + sops for git-safe encrypted values (fnox.toml with `provider (age)`)")
- **`.claude/agents/security-auditor.md:34`**: change "Tier 1: fnox + macOS Keychain + age encryption" → "Tier 1: fnox + macOS Keychain + Doppler"
- **`docs/mise-config.md:72`**: remove `fnox set OP_SERVICE_ACCOUNT_TOKEN "ops_..." --provider age`
- **`docs/setup-notes.md:262-276`**: remove the 1Password service-account-token instructions block
- **`fnox.toml` (repo root) line 3**: update comment — no more "Local 1Password-backed overlays belong in fnox.local.toml". Just "Repo-level fnox overlay. Global personal secrets live in ~/.config/fnox/config.toml."

Leave alone (historical/research):
- `docs/research/trail/**`
- `docs/research/source-catalog.md`
- `docs/plans/2026-02-28-*.md`
- `docs/dotfiles/**`
- `docs/tool-audit/**`
- `rsm-subagents/plugins/chezmoi-toolkit/skills/chezmoi-config/references/password-managers.md`
- `rsm-subagents/plugins/mise-toolkit/skills/mise-jdx-ecosystem/SKILL.md` (generic fnox description, still valid)

Keychain cleanup:
```bash
fnox list | grep OP_ && fnox remove OP_SERVICE_ACCOUNT_TOKEN
# May also: security delete-generic-password -s "mde-fnox" -a "OP_SERVICE_ACCOUNT_TOKEN"
```

### Sub-phase 2c: Delete age/sops artifacts

Files to delete:
- `src/mde/secrets/sops.py`
- `scripts/mde-sops-secrets-refresh.sh` (already deleted in 2b)
- Any remaining `.sops*` files at repo root (none currently)

Files to edit:
- **`src/mde/secrets/__init__.py:16`**: remove `from mde.secrets.sops import refresh_secrets` import
- **`tests/mde/test_secrets_doppler.py:419,427,438`**: delete the three test cases importing `mde.secrets.sops.refresh_secrets`

fnox provider cleanup (in `~/.config/fnox/config.toml`):
```toml
# Remove this line:
# age = { ... }
# If it exists — user said to drop age, but the current file only declares keychain and doppler_...,
# so there may be nothing to remove here. Verify first.
```

Leave alone: the `age` CLI binary itself (may still be used for non-secrets encryption) — user did not explicitly say to uninstall it. Default is leave-in-place.

### Sub-phase 2d: Collapse `src/mde/secrets/`

Current state (7 files):
- `__init__.py` — dispatcher, imports sops lazily
- `doppler.py` — Doppler CLI wrapper (73 LOC)
- `export_to_doppler.py` — one-time fnox→Doppler migration (56 LOC) — already run
- `keychain.py` — wraps SOPS→Keychain bash script (23 LOC)
- `smoke.py` — smoke test, unclear if still used — VERIFY before deleting
- `sops.py` — wraps SOPS refresh bash script (26 LOC)
- `sync.py` — Python-native Doppler→fnox sync (48 LOC)
- `validate_parity.py` — parity check Doppler vs fnox (66 LOC)

Target state (2 files):
- `__init__.py` — dispatcher
- `fnox_sync.py` — thin wrappers around `fnox sync` and `fnox sync -n`

New `src/mde/secrets/fnox_sync.py` (~40 LOC):

```python
"""Thin wrappers around `fnox sync` for secret sync and audit.

Replaces the bespoke Doppler→fnox Python layer. fnox 1.20.0 ships a
native Doppler provider, making the Python CLI wrapper redundant.

End-state secrets pipeline:
    Doppler (dotfiles/dev_personal)
        ↓ fnox sync (native Doppler provider)
    Keychain service="mde-fnox"
        ↓ fnox activate (shell hook in .zshrc)
    shell env → tools
"""
from __future__ import annotations

import subprocess

from mde.log import logger

_SOURCE_PROVIDER = "doppler_dotfiles_dev_personal"
_DEST_PROVIDER = "keychain"


def sync() -> int:
    """Pull all secrets from Doppler into Keychain via fnox.

    Wraps: fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f
    """
    return subprocess.run(
        ["fnox", "sync",
         "-s", _SOURCE_PROVIDER,
         "-p", _DEST_PROVIDER,
         "-g", "-f"],
    ).returncode


def validate() -> int:
    """Check parity between Doppler and Keychain via fnox dry-run.

    Wraps: fnox sync -s ... -p ... -g -n (dry run). Exit code 0 if
    in sync, non-zero if drift detected.
    """
    return subprocess.run(
        ["fnox", "sync",
         "-s", _SOURCE_PROVIDER,
         "-p", _DEST_PROVIDER,
         "-g", "-n"],
    ).returncode
```

Update `src/mde/secrets/__init__.py` to re-export `sync` and `validate` from `fnox_sync`.

Delete these files after confirming no external imports:
- `src/mde/secrets/doppler.py`
- `src/mde/secrets/export_to_doppler.py`
- `src/mde/secrets/keychain.py`
- `src/mde/secrets/sops.py`
- `src/mde/secrets/sync.py`
- `src/mde/secrets/validate_parity.py`
- Possibly `src/mde/secrets/smoke.py` — VERIFY callers first

Update `src/mde/cli.py`: the `secrets` dispatcher should just call `fnox_sync.sync()` and `fnox_sync.validate()`.

### Sub-phase 2e: Update shell integration

**Drop `mise-env-fnox` plugin**:
- `home/dot_config/mise/config.toml.tmpl`: remove the `[plugins] fnox-env = ...` and `_.fnox-env = { tools = true }` lines. During this session, these were re-enabled for diagnostic purposes (never got to run the diagnostic). The final state is: remove them entirely.

**Add `fnox activate` to zsh**:
- `home/dot_zshrc.tmpl`: append `eval "$(fnox activate zsh)"` somewhere after the oh-my-zsh source line. Or place it in a new `home/dot_oh-my-zsh/custom/50-fnox.zsh` file for modularity.

**Keep `mise` in oh-my-zsh plugins**:
- Already done this session: `home/dot_zshrc.tmpl:80` has `plugins=(git gh mise)`. No change needed.

### Sub-phase 2f: Update docs

- **`CLAUDE.md`**: the "Secrets" section (line 107) currently says `uv run mde-py secrets sync` and `--config dev`. Update to:
  > All secrets: **Doppler (dotfiles/dev_personal) → `fnox sync` → Keychain → `fnox activate` → tools**. New secrets: `doppler secrets set KEY=VAL --project dotfiles --config dev_personal`, then `fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f`. Validate: `fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -n`. See `.claude/rules/secrets-management.md` for full guide.

- **`.claude/rules/secrets-management.md`**: rewrite the pipeline diagram, drop `uv run mde-py secrets *` commands, add `fnox activate` setup instructions, remove age/sops/1Password mentions, update Doppler config from `dev` to `dev_personal`.

- **`docs/mise-config.md`**: remove 1Password setup section, update fnox setup to use native Doppler provider.

- **`docs/setup-notes.md`**: same.

- **`home/.chezmoi.toml.tmpl:15`**: `[doppler] config = "dev"` → `[doppler] config = "dev_personal"`.

- **`fnox.toml` (repo root)**: consider updating the 43 hardcoded secret entries. The `if_missing = "ignore"` pattern on every key is a footgun (missing secrets silently become empty strings). Either tighten to `warn` (matches global default) or remove the repo-level list entirely and let fnox inherit from the global config. USER DECISION NEEDED.

### Phase 2 success criteria

- [ ] `fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f` succeeds
- [ ] `fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -n` reports clean
- [ ] `fnox list | wc -l` matches the Doppler count (50+ keys)
- [ ] Fresh shell loads `fnox activate` correctly; `echo $GRAFANA_PASSWORD` returns a non-empty value
- [ ] `docker compose -f docker/observability/compose.yaml config` passes without `GRAFANA_PASSWORD=$(...)` prefix
- [ ] `src/mde/secrets/` contains only `__init__.py` and `fnox_sync.py` (and maybe `smoke.py` if verified needed)
- [ ] `scripts/mde-sops-*.sh` do not exist
- [ ] `.agents/skills/1password-fnox/` does not exist
- [ ] `grep -r '1password\|1Password\|OP_SERVICE_ACCOUNT_TOKEN\|provider.*age' src/ home/ .claude/ scripts/` returns only historical/research hits in `docs/research/**`
- [ ] `uv run mde-py quality` passes 6/6
- [ ] `uv run mde-py validate --all` passes

---

## EXECUTION ORDER (the actual step-by-step)

Assuming codex adversarial review on this plan has been completed and findings incorporated.

### Step 0: Pre-flight
```bash
cd ~/dev/github/ray-manaloto/macos-development-environment
git checkout -b feat/sync-dotfiles-migration
git status --short                    # Confirm clean-ish tree
uv run mde-py quality                 # Baseline — note any pre-existing warnings
uv run mde-py validate --all          # Baseline
```

### Step 1: Write Python module + tests
```bash
# Create src/mde/maintain/sync_dotfiles.py per Phase 1 spec
# Create tests/mde/test_sync_dotfiles.py per Phase 1 spec
# Add maintain sync-dotfiles dispatcher to src/mde/cli.py

uv run pytest tests/mde/test_sync_dotfiles.py -v
uv run ruff check src/mde/maintain/sync_dotfiles.py tests/mde/test_sync_dotfiles.py
uv run ruff format src/mde/maintain/sync_dotfiles.py tests/mde/test_sync_dotfiles.py
uv run ty check src/mde/maintain/sync_dotfiles.py
```

### Step 2: Verify the CLI works before migrating callsites
```bash
uv run mde-py maintain sync-dotfiles --check
# EXPECT: SystemExit(2) with message about sourceDir mismatch, because chezmoi
# is still broken. This is the correct behavior — the preflight check is firing.
```

### Step 3: One-time repair of chezmoi config
```bash
cp ~/.config/chezmoi/chezmoi.toml ~/.config/chezmoi/chezmoi.toml.backup-$(date +%Y%m%d)
chezmoi init --source="$PWD/home" --force
chezmoi source-path                    # EXPECT: .../macos-development-environment/home
chezmoi managed | wc -l                # EXPECT: > 0
grep -c '^sourceDir' ~/.config/chezmoi/chezmoi.toml    # EXPECT: 1
```

### Step 4: Review drift before applying
```bash
chezmoi diff > /tmp/chezmoi-drift-$(date +%Y%m%d).diff
less /tmp/chezmoi-drift-$(date +%Y%m%d).diff
# Review carefully. User decides what's intentional drift vs. accidental.
# Promote intentional drift into home/ templates BEFORE applying.
# Accidental drift will be wiped by apply — that's the point.
```

### Step 5: Apply chezmoi
```bash
chezmoi apply --force
# Verify: ~/.zshrc should now have plugins=(git gh mise) if the template edit
# from this session carried through correctly.
grep 'plugins=' ~/.zshrc                # EXPECT: plugins=(git gh mise)
```

### Step 6: Re-verify the Python module now passes preflight
```bash
uv run mde-py maintain sync-dotfiles --check
# EXPECT: exit 0, "chezmoi diff: clean" or similar
```

### Step 7: Migrate callsites (all 7)

Per the per-file changes in Phase 1. Use sed or direct Edit. Verify each:

```bash
# After each callsite update:
uv run mde-py quality
```

### Step 8: Delete the bash script + bash test

```bash
git rm scripts/ensure-managed-configs.sh
git rm scripts/tests/chezmoi-fallback.test.sh
```

### Step 9: Run full verification

```bash
uv run mde-py quality
uv run mde-py validate --all
uv run pytest tests/ -v -m "not integration"
mise run mde:sync-dotfiles              # End-to-end smoke
```

### Step 10: Commit Phase 1

```bash
git add -A
git commit -m "feat(maintain): migrate sync-dotfiles to Python, drop --source flag bug

Replaces scripts/ensure-managed-configs.sh (314 lines) with
src/mde/maintain/sync_dotfiles.py. Root cause: the bash script passed
--source to chezmoi apply, which is suspected of causing
~/.config/chezmoi/chezmoi.toml to lose its sourceDir field on every
invocation (see docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md).

Key changes:
- New Pydantic SyncResult model per library-first.md
- Preflight check: verify chezmoi source-path matches repo home/ dir
- No --source flag; rely on persisted config
- No fallback: templates/ has been empty for months, legacy_sync() was dead code
- 7 callsites updated; bash test replaced by pytest
- Hash manifest in .devcontainer/post-create.sh updated to hash Python module

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

### Step 11: Phase 2 — Secrets simplification

Execute Phase 2 sub-phases in order: 2a (typo fix + verify), 2b (1Password deletion), 2c (age/sops deletion), 2d (collapse src/mde/secrets/), 2e (shell integration), 2f (doc updates). Commit after each sub-phase.

### Step 12: Final verification + open PR

```bash
uv run mde-py quality
uv run mde-py validate --all
git push -u origin feat/sync-dotfiles-migration
gh pr create --title "feat: sync-dotfiles Python migration + secrets pipeline simplification" --body "..."
```

---

## VERIFICATION CHECKLIST (run at end)

- [ ] `fnox 1.20.0` installed
- [ ] `fnox provider list` shows: `doppler_dotfiles_dev_personal` (no typo), `keychain`, no `age`
- [ ] `fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f` works
- [ ] `chezmoi source-path` returns the repo home/ dir
- [ ] `chezmoi managed` is non-empty
- [ ] `grep -c sourceDir ~/.config/chezmoi/chezmoi.toml` > 0
- [ ] `~/.config/chezmoi/chezmoi.toml` has `[data.git]` and `[doppler] config = "dev_personal"`
- [ ] `uv run mde-py maintain sync-dotfiles --check` exits 0
- [ ] `uv run mde-py maintain sync-dotfiles` applies cleanly
- [ ] `mise run mde:sync-dotfiles` works end-to-end
- [ ] Fresh shell: `echo $GRAFANA_PASSWORD` returns non-empty
- [ ] `docker compose -f docker/observability/compose.yaml config` works without env prefix
- [ ] `scripts/ensure-managed-configs.sh` does not exist
- [ ] `scripts/tests/chezmoi-fallback.test.sh` does not exist
- [ ] `src/mde/secrets/` has only `__init__.py` and `fnox_sync.py`
- [ ] `.agents/skills/1password-fnox/` does not exist
- [ ] `uv run mde-py quality` passes 6/6
- [ ] `uv run mde-py validate --all` passes
- [ ] `uv run pytest tests/ -v -m "not integration"` passes
- [ ] `$HOME/` shadow dir does not exist in repo root
- [ ] `git status --short` shows no unexpected untracked files

---

## ROLLBACK PROCEDURES

### Rollback Phase 1 only
```bash
git checkout main
git branch -D feat/sync-dotfiles-migration
# Restore chezmoi config from backup if Step 3 ran
cp ~/.config/chezmoi/chezmoi.toml.backup-YYYYMMDD ~/.config/chezmoi/chezmoi.toml
```

### Rollback Phase 2 only (Phase 1 already merged)
```bash
git checkout main
git revert <phase-2-commit-sha>
# Re-populate Keychain from Doppler via the old path if needed:
# (But the old Python sync.py will be gone, so use fnox directly:)
fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f
```

### Full rollback
```bash
git checkout main
git reset --hard <pre-migration-sha>    # Use with caution
cp ~/.config/chezmoi/chezmoi.toml.backup-YYYYMMDD ~/.config/chezmoi/chezmoi.toml
```

---

## COMMANDS CHEAT SHEET

```bash
# Verify fnox + Doppler pipeline
fnox --version                                                              # 1.20.0
fnox provider list                                                          # age, doppler_..., keychain
fnox provider test doppler_dotfiles_dev_personal
fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -n                # dry run
fnox sync -s doppler_dotfiles_dev_personal -p keychain -g -f                # apply
fnox list

# Doppler direct
doppler secrets --project dotfiles --config dev_personal --only-names
doppler secrets --project dotfiles --config dev_personal | head

# Chezmoi diagnostics
chezmoi source-path
chezmoi managed | wc -l
chezmoi diff
chezmoi apply --force
chezmoi init --source="$PWD/home" --force                                   # one-time repair

# MDE quality gate
uv run mde-py quality
uv run mde-py validate --all
uv run mde-py maintain sync-dotfiles --check
uv run mde-py maintain sync-dotfiles

# Codex
node "/Users/rmanaloto/.claude/plugins/cache/openai-codex/codex/1.0.3/scripts/codex-companion.mjs" setup --json
# If auth broken: !codex login
/codex:adversarial-review --wait "focus text here"

# Observability stack (if needed)
GRAFANA_PASSWORD=$(fnox get GRAFANA_PASSWORD) docker compose -f docker/observability/compose.yaml up -d
docker compose -f docker/observability/compose.yaml ps
```

---

## LINKED RULES (load these when resuming)

- `.claude/rules/no-shell-scripts.md` — why the migration exists
- `.claude/rules/library-first.md` — why Pydantic BaseModel
- `.claude/rules/chezmoi-config-safety.md` — the 2026-03-29 incident this recurs
- `.claude/rules/mise-first.md` — tool ownership
- `.claude/rules/secrets-management.md` — current (stale) secrets doc, to be updated
- `.claude/rules/declarative-config.md` — no standalone config files
- `.claude/rules/no-warning-suppression.md` — error handling standard
- `CLAUDE.md` Secrets section — to be updated

---

## SESSION HISTORY SUMMARY (for context, not action)

2026-04-08 session highlights:
- User asked whether `$HOME/` at repo root was a symlink → discovered 208K shadow dir from tempdir-leakage bug. Deleted, gitignored.
- User noted fnox 1.20.0 added native Doppler provider → proposed simplification of `src/mde/secrets/`.
- User noted 1Password subscription expired → added deletion to scope.
- User disabled `mise-env-fnox` in deployed mise config due to oh-my-zsh integration issues → decided final state is `fnox activate` via oh-my-zsh mise plugin, not the env plugin.
- Doppler `dev` vs `dev_personal` comparison → confirmed `dev_personal` is strict superset.
- User said to drop `age` entirely.
- Discovered chezmoi was not actually managing any files (`chezmoi managed` empty, `source-path` returns default).
- Initially suspected chezmoi-config-safety.md 2026-03-29 incident recurrence; user corrected: "it's not chezmoi, it's our code".
- Traced to `scripts/ensure-managed-configs.sh:207,225` passing `--source` flag.
- Dispatched adversarial review via `codex:codex-rescue` — stalled (regex error + dead broker socket).
- Ran `/codex:setup --enable-review-gate` — enabled gate but auth still broken.
- User wrote this handoff before `/clear`.

---

**End of handoff. Good luck, next session.**
