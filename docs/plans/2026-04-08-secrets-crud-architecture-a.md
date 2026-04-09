# Unified Secrets CRUD Wrapper with fnox-blessed Architecture (Architecture A)

**Created:** 2026-04-08 (continuation of earlier session work)
**Status:** Plan complete, awaiting codex adversarial review, then user approval, then execution
**Branch:** `main` (no feature branch yet)
**Supersedes:** Phase 2 (Secrets Simplification) of `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` — that plan's Phase 2 used an incorrect `fnox sync --provider keychain` assumption that was proven impossible via live CLI testing in this session
**Does NOT supersede:** Phase 1 (chezmoi sync-dotfiles migration) of the earlier plan — that work is independent and still valid

---

## RESUME PROTOCOL (read this first, for post-`/clear` sessions)

If you are a new Claude session resuming this work after a `/clear`:

1. **Verify the working tree is where this doc expects it to be** — run:
   ```bash
   git status --short
   git log --oneline -5
   ```
   At handoff time, the working tree had these modifications (from this session and prior session work; none are this plan's execution):
   ```
    M .claude/rules/observability-stack.md
    M .claude/settings.json
    M .gitignore                                   ← this session: added $HOME/ rule
    M .mise.toml
    D .omc/state/last-tool-error.json
    M CLAUDE.md
    M docs/research/source-catalog.md
    M home/Brewfile.tmpl
    M home/dot_oh-my-zsh/custom/10-mde-core.zsh
    M home/dot_tmux.conf
    M home/dot_zprofile.d/macos-dev-env.zsh
    M home/dot_zshrc.tmpl                          ← this session: plugins=(git gh mise)
    M mise.lock
    M scripts/agent-hud
    M scripts/status-dashboard.sh
   ?? .claude/claude-octopus.local.md
   ?? docs/plans/2026-04-08-secrets-crud-architecture-a.md   ← this plan (copied from ~/.claude/plans/)
   ?? docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md  ← prior plan (chezmoi + original secrets work)
   ?? scripts/tests/mise-shell-bootstrap.test.sh
   ```
   If diverged significantly, STOP and ask the user.

2. **Re-verify the critical live diagnostic facts** (plan makes claims that must still be true):
   ```bash
   fnox --version                                      # Expect: 1.20.0
   fnox provider list                                  # Expect: age, doppler_dotfiles_dev_personal (typo), keychain
   echo 'TEST=x' | fnox import --provider keychain --global --dry-run env 2>&1 | grep -E 'target_unsupported|provider_unsupported'
                                                        # Expect: match (still rejected)
   fnox sync --source doppler_dotfiles_dev_personal --provider keychain --global --dry-run 2>&1 | grep -E 'target_unsupported|provider_unsupported'
                                                        # Expect: match (still rejected)
   doppler secrets --project dotfiles --config dev_personal --only-names 2>&1 | wc -l
                                                        # Expect: 52 (50 secrets + 2 header lines)
   ```
   If any of these change (e.g., a fnox update adds keychain sync support), STOP and reconsider — the plan's architecture depends on sync-to-keychain being impossible.

3. **Check codex auth**:
   ```bash
   node "/Users/rmanaloto/.claude/plugins/cache/openai-codex/codex/1.0.3/scripts/codex-companion.mjs" setup --json | grep -A1 loggedIn
   ```
   At handoff time, codex was `loggedIn: false` with `ECONNREFUSED` on the broker socket. The broker socket is per-Claude-session, so a fresh session should spin up a new one. If still failing, run `!codex login`.

4. **Run the adversarial review on this plan** — BEFORE writing any code:
   ```
   /codex:adversarial-review --wait "focus on the architecture plan in docs/plans/2026-04-08-secrets-crud-architecture-a.md — specifically: (1) the bootstrap chain (DOPPLER_TOKEN in Keychain → age key in Doppler → circular dependency) — is this safe on a fresh machine, can it be recovered if DOPPLER_TOKEN is lost; (2) the age key rotation story — what happens when AGE_PRIVATE_KEY needs to change, does every machine need to re-sync; (3) the `fnox sync --provider age --global --force` call on every add/update — latency, rate limits, failure modes; (4) whether deleting validate_parity.py and relying on fnox sync --dry-run loses test coverage; (5) whether the shell wrapper in 50-mde-secrets.zsh conflicts with the already-disabled mise-env-fnox plugin; (6) whether this plan correctly handles the 43 stale entries in repo fnox.toml that will shadow the global config declarations until cleaned up"
   ```
   Return codex's findings verbatim. Do NOT start writing code until the user has read and approved any changes.

5. **Only after codex review is incorporated and approved**, proceed to the Execution Order section below.

---

## Context

The user's end goal is a secrets pipeline where:
- **Doppler** is the cloud source of truth (`dotfiles/dev_personal`, ~50 secrets)
- **OS Keychain** stores only the Doppler bootstrap token (`DOPPLER_TOKEN`)
- **Shell environment** has all secrets auto-loaded on directory change
- **One unified command** adds/updates/removes a secret across all layers

The current state has significant drift from that goal:
- `src/mde/secrets/` contains 8 files (~400 LOC) wrapping Doppler CLI calls and writing plaintext to Keychain one key at a time. `sync_doppler_to_fnox()` hardcodes `config="dev"` instead of the intended `dev_personal`
- No `add`/`update`/`remove` operations exist — only a bulk `sync` that pulls all 50 secrets in a loop
- `mise-env-fnox` plugin was disabled by the user due to oh-my-zsh conflicts, so secrets currently don't auto-load into shell env on `cd`
- 1Password provider is scheduled for removal (subscription expired)
- Earlier in this session, I drafted a plan using `fnox sync --provider keychain` as the propagation step. **This turned out to be architecturally impossible** — two live CLI tests confirmed that both `fnox sync --provider keychain` and `fnox import --provider keychain` are rejected with `provider_unsupported` errors. Per fnox's design, sync and import require **encryption providers** (age, aws-kms), never storage providers

The user reviewed the failing approach and proposed a cleaner architecture: "the only requirement is that os keychain has the doppler api key. Then run `fnox sync` from Doppler to propagate everywhere else." With the correction that `fnox sync` requires an encryption provider, the path that matches the user's simplification spirit is the canonical fnox pattern: **Doppler → fnox sync --provider age → ~/.config/fnox/config.toml → fnox activate hooks → shell**. This plan implements that.

---

## DECISIONS LOCKED IN (do not re-litigate)

User explicitly made these choices in this session's conversation. Carry them forward verbatim:

1. **Architecture A** — the fnox-canonical pattern: Doppler → `fnox sync --provider age --global` → age-encrypted cache in `~/.config/fnox/config.toml` → `fnox activate zsh` chpwd/precmd hooks → shell env. User said: "let's try A".

2. **Age key stored in Doppler** for backup/bootstrap. User said: "doppler". The bootstrap chain is: DOPPLER_TOKEN in Keychain → authenticates doppler CLI → fetches AGE_PRIVATE_KEY from Doppler → writes to `~/.config/fnox/age.txt` (0600) → enables fnox sync decryption.

3. **Global config only** for fnox secret declarations (not repo `fnox.toml`). User answered Q1 of the earlier AskUserQuestion: "Global config only". All `mde secrets add/update/rm` operations write to `~/.config/fnox/config.toml` only. The 43 stale entries in repo `fnox.toml` will be stripped in a followup PR.

4. **Stdout `export` line + zsh wrapper function** for current-shell propagation. Implied by the user's "Variant A" selection and their confirmation of the `mde-secret-add` wrapper pattern in Diagram C of the earlier analysis.

5. **Doppler-first atomicity**: write to Doppler before any local state change. If Doppler fails, nothing else runs. If Doppler succeeds but `fnox sync` fails, return exit 2 (partial) and rely on the next run to reconcile.

6. **Delete dead code**: `src/mde/secrets/{sops,smoke,keychain,export_to_doppler,validate_parity}.py`, plus `scripts/mde-sops-secrets-{refresh,import-keychain,backup-1password}.sh`, plus `scripts/secrets-smoke-test.sh`, plus `.agents/skills/1password-fnox/`.

7. **Drop `mise-env-fnox` plugin** — user disabled it due to oh-my-zsh conflicts. Shell integration now happens via `fnox activate zsh` in `home/dot_oh-my-zsh/custom/50-mde-secrets.zsh`.

8. **Keep `mise` in oh-my-zsh plugins**: already done in this session. `home/dot_zshrc.tmpl:80` has `plugins=(git gh mise)`.

9. **Use `dev_personal` everywhere**, not `dev`. Strict superset (+2 keys: GITHUB_API_TOKEN, MISE_GITHUB_TOKEN). Fix hardcoded `_CONFIG = "dev"` in `src/mde/secrets/doppler.py:12`.

10. **Fix the `doppler_` typo** in `~/.config/fnox/config.toml` → `doppler_dotfiles_dev_personal` as part of bootstrap setup.

11. **Adversarial review via `/codex:adversarial-review --wait`** against this plan file BEFORE implementation. User explicitly asked for this workflow: "the documentation should have this workflow diagram and the handoff document should link to it" + "have the /codex:adversarial-review validate the plan also as we had agreed to".

---

## VERIFIED FACTS (with evidence, captured 2026-04-08)

### fnox runtime behavior

- **Version**: `fnox 1.20.0`
- **Providers currently declared** (verified via `fnox provider list`):
  - `age`
  - `doppler_dotfiles_dev_personal` (TYPO — will fix as part of bootstrap)
  - `keychain`
- **`fnox sync --provider keychain` is REJECTED**. Verbatim error:
  ```
  Error: fnox::sync::target_unsupported (https://fnox.jdx.dev/cli/sync)
    × Provider 'keychain' cannot be used as a sync target
    help: The target provider must support encryption (e.g., 'age', 'aws-kms').
          Remote storage providers cannot be used as sync targets.
  ```
- **`fnox import --provider keychain` is ALSO REJECTED**. Verbatim error:
  ```
  Error: fnox::import::provider_unsupported (https://fnox.jdx.dev/cli/import)
    × Provider 'keychain' cannot be used for import
    help: Remote storage providers are not yet supported for import.
          Use an encryption provider like 'age' instead.
  ```
- **`fnox sync --help`** confirms `-s/--source <SOURCE>`, `-p/--provider <PROVIDER>`, `-g/--global`, `-f/--force`, `-n/--dry-run`, `--filter <REGEX>` are all first-class flags.
- **`fnox remove <KEY> --global` EXISTS** as a first-class subcommand (aliases: `rm`, `delete`). Flags: `-c/--config`, `-g/--global`, `-n/--dry-run`, `-P/--profile`, `--if-missing`. No need for a `security delete-generic-password` fallback.
- **`fnox set <KEY> <VALUE> --provider <PROVIDER> --global`** writes:
  1. Value to macOS Keychain (for keychain provider) via Security.framework
  2. Declaration entry to `~/.config/fnox/config.toml`
  Both in one call. This is what the existing `sync_doppler_to_fnox()` loop does.
- **`fnox activate zsh`** produces a `_fnox_hook` function wired to `chpwd_functions` + `precmd_functions`. Verified via Explore agent — successfully resolved 47 secrets and exported to env when tested.
- **Provider resolution chain**: `fnox hook-env` (called by activate) merges `~/.config/fnox/config.toml` (global) with the nearest `fnox.toml` in CWD or parent dirs (repo-level). Currently this means 47 secrets come from the merge of global + repo fnox.toml (43 entries).

### fnox docs summary (from https://fnox.jdx.dev/guide/sync.html)

Verbatim quote from the sync guide (fetched this session):
> `fnox sync` fetches secrets from remote providers (1Password, AWS Secrets Manager, etc.) and re-encrypts them with a local encryption provider (age, YubiKey via age plugin, AWS KMS, etc.). The encrypted values are stored in `fnox.local.toml` (gitignored)... When fnox resolves secrets, it checks for a `sync` field first and uses that instead of calling the original provider.

Key properties of `fnox sync --provider age --global --force`:
- Reads all secrets that have a source provider declared (e.g., `{ provider = "doppler", value = "KEY" }`)
- For each, calls the source provider's API to get plaintext
- Encrypts with age recipient (public key from `[providers.age].recipients`)
- Writes ciphertext back into the SAME config file as a `sync` field on each secret:
  ```toml
  [secrets]
  GITHUB_TOKEN = {
    provider = "doppler",
    value = "GITHUB_TOKEN",
    sync = { provider = "age", value = "YWdlLWVuY3J5cHRpb24..." }
  }
  ```
- `--global` flag means write to `~/.config/fnox/config.toml` instead of the default `fnox.local.toml`
- `--force` skips confirmation prompt
- `--dry-run` shows what would happen without modifying files

### Doppler state

- **Project**: `dotfiles`
- **Configs**:
  - `dev`: 48 secrets (50 raw lines from `doppler secrets --only-names`, minus 2 header lines)
  - `dev_personal`: 50 secrets (strict superset: shares 48 with `dev`, adds `GITHUB_API_TOKEN` and `MISE_GITHUB_TOKEN`)
- **User explicitly chose `dev_personal`** as the target config

### Current `src/mde/secrets/` inventory

Verified via Explore agent, 376 LOC total across 8 files:

| File | LOC | Purpose | Fate |
|---|---|---|---|
| `__init__.py` | 35 | `dispatch_secrets(action)` router | **Modify** (extend signature) |
| `doppler.py` | 104 | `is_doppler_available()`, `doppler_list_secrets()`, `doppler_get_secret()`, `doppler_set_secrets()` | **Modify** (add `doppler_delete_secret`, fix `_CONFIG`) |
| `sync.py` | 48 | `sync_doppler_to_fnox()` — per-key loop calling `fnox set --provider keychain --global` | **Rewrite** (replace loop with single `fnox sync --provider age --global`) |
| `validate_parity.py` | 65 | `validate_secrets_parity()` — compares Doppler vs Keychain | **Delete** (replaced by `fnox sync --dry-run`) |
| `smoke.py` | 19 | Delegates to `scripts/secrets-smoke-test.sh` | **Delete** (dead) |
| `keychain.py` | 23 | Wraps `scripts/mde-sops-secrets-import-keychain.sh` | **Delete** (dead) |
| `sops.py` | 26 | Wraps `scripts/mde-sops-secrets-refresh.sh` | **Delete** (dead) |
| `export_to_doppler.py` | 56 | One-time `fnox → Doppler` migration | **Delete** (already run) |

Current CLI dispatch at `src/mde/cli.py:200-204`:
```python
secrets_p = sub.add_parser("secrets", help="Secrets management")
secrets_p.add_argument(
    "action", choices=["refresh", "smoke", "export", "sync", "validate"], ...
)
```

And `_cmd_secrets` at `src/mde/cli.py:440-447`:
```python
def _cmd_secrets(args: argparse.Namespace) -> int:
    with _traced_command("secrets", action=args.action) as ctx:
        from mde.secrets import dispatch_secrets
        result = dispatch_secrets(args.action)
        ctx["span"].set_attribute("secrets.action", args.action)
        ctx["result"] = result
        return result
```

### Repo `fnox.toml` state

43 secrets declared with `provider = "keychain", if_missing = "ignore"`. This creates a merge conflict with the new architecture: the global config will use `provider = "doppler", sync = {...}` for the same keys, while the repo `fnox.toml` still says `provider = "keychain"`. **fnox's merge chain gives repo-level precedence over global**, so unless the repo entries are removed, they will shadow the new declarations.

**Followup work** (explicitly out of scope for this plan, but flagged): strip the 43 entries from repo `fnox.toml` in a separate commit after parity verification.

### Codex state (at handoff time)

- **Version**: `codex-cli 0.118.0`
- **Node**: `v25.9.0`, **npm**: `11.12.1`
- **Auth**: `loggedIn: false`, `ECONNREFUSED` on broker socket
- **Review gate**: enabled for this repo
- **Reason for ECONNREFUSED**: broker socket is per-Claude-session; prior session's socket is dead. A fresh session after `/clear` will create a new broker socket. If still failing, re-run `!codex login`.

### Chezmoi state (separate issue, not blocking this plan)

- `chezmoi source-path` returns `/Users/rmanaloto/.local/share/chezmoi` (wrong — should be repo's `home/`)
- `chezmoi managed` returns 0 lines
- `~/.config/chezmoi/chezmoi.toml` is missing `sourceDir`, `[data.git]`, `[doppler]` fields
- `~/.zshrc` and `~/.config/mise/config.toml` are NOT actually managed by chezmoi (different inodes from templates)
- **This plan does NOT depend on chezmoi being fixed.** The secrets CRUD wrapper lands in `src/mde/`, `tests/`, `docs/`, and global config files — none of which require chezmoi. The shell wrapper edit at `home/dot_oh-my-zsh/custom/50-mde-secrets.zsh` technically goes through chezmoi templates, but the user can manually copy it to `~/.oh-my-zsh/custom/50-mde-secrets.zsh` if chezmoi is still broken.
- Chezmoi repair is documented in the prior plan at `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` Phase 1. That work is independent and can be executed before, during, or after this plan.

---

## OPEN QUESTIONS / UNPROVEN HYPOTHESES

### Q1: Does `fnox sync` write encrypted blobs to `~/.config/fnox/config.toml` or to a separate `fnox.local.toml`?

**Claim in plan**: `--global` flag writes to `~/.config/fnox/config.toml`, as a `sync` field on each secret.

**Evidence**: fnox docs (https://fnox.jdx.dev/guide/sync.html) say the default target is `fnox.local.toml` but the `--global` flag redirects to `~/.config/fnox/config.toml`. No live verification yet — the plan depends on this being correct.

**How to resolve before execution**: run `fnox sync --provider age --global --dry-run` once (after bootstrap) and inspect where it says it will write. If it writes to a separate file, adjust the plan's expectations about where declarations live.

### Q2: Does `fnox sync` delete secrets from the sync cache when they're removed from the source provider?

**Claim in plan**: Yes — remove flow relies on this. After `doppler secrets delete KEY`, running `fnox sync --provider age --global --force` should drop the `sync` field for the removed key (since its source provider no longer has it).

**Evidence**: None — I inferred this from the "re-sync" semantics of sync commands in general. Not explicitly verified from docs or CLI behavior.

**How to resolve**: After bootstrap, test with a dummy secret: add to Doppler, sync, verify in `config.toml`, delete from Doppler, sync again, verify the sync field is gone. If fnox sync doesn't clean up orphans, the remove flow needs an explicit `fnox remove KEY --global` step after the sync.

### Q3: Will `fnox activate zsh` work correctly after we switch secrets from `provider = "keychain"` to `provider = "doppler", sync = {age:...}`?

**Claim in plan**: Yes — the `fnox hook-env` chpwd hook reads the `sync` field first per fnox docs ("When fnox resolves secrets, it checks for a `sync` field first and uses that instead of calling the original provider").

**Evidence**: Docs quote. Live verification from explore agent showed activate works with the current keychain-based declarations. Not yet tested with doppler+age declarations.

**How to resolve**: After bootstrap + first sync, run `fnox activate zsh 2>&1 | head -20` and verify the emitted exports include the secrets decrypted from age cache (fast), not from Doppler API (slow).

### Q4: How does the age key rotation story work?

**Concern**: If we ever need to rotate the age key (compromised machine, departing teammate, key file lost), every machine with a sync'd cache becomes un-decryptable. The rotation flow would require:
1. Generate new age keypair
2. Store new private key in Doppler as `AGE_PRIVATE_KEY` (overwriting)
3. Update `[providers.age].recipients` in `~/.config/fnox/config.toml`
4. Run `fnox sync --provider age --global --force` to re-encrypt all secrets with new recipient
5. Distribute new private key to every other machine (they'd need to run step 4 too)

**Evidence**: Inference from age's asymmetric encryption model. Not tested.

**How to resolve**: This is a process concern, not a code concern. Document in `docs/secrets-workflow.md`. Not blocking execution of this plan, but worth flagging as a failure mode.

### Q5: What if the repo `fnox.toml` shadows the global config declarations?

**Concern**: fnox merges configs with repo-level taking precedence. Until we strip the 43 entries in the followup PR, `fnox hook-env` will resolve (say) `GITHUB_TOKEN` using the repo `fnox.toml`'s `provider = "keychain"` declaration instead of the new global `provider = "doppler", sync = {age:...}` declaration. Result: the old Keychain value (possibly stale) wins until the repo fnox.toml is stripped.

**Evidence**: fnox hierarchical config docs + merge order documented in `fnox.jdx.dev/guide/hierarchical-config.html` (not fetched this session).

**How to resolve**: Either (a) strip repo `fnox.toml` entries as part of THIS plan (would expand scope), or (b) execute the followup PR immediately after this one, or (c) confirm via live test that the new architecture's declarations actually take effect by running `fnox list --sources` and checking which file each key resolves from. Option (c) first, then decide.

### Q6: The circular bootstrap — is it recoverable if DOPPLER_TOKEN is lost?

**Concern**: The plan stores `AGE_PRIVATE_KEY` in Doppler. To access Doppler, you need `DOPPLER_TOKEN`. To access `AGE_PRIVATE_KEY` without Doppler, you need... nothing else in this plan. If both DOPPLER_TOKEN and `~/.config/fnox/age.txt` are lost simultaneously, the machine cannot decrypt its local cache and cannot re-fetch the age key.

**Recovery path**: The user must have an out-of-band way to recover DOPPLER_TOKEN (team password manager, service account in ops vault, printed on paper, etc.). Once DOPPLER_TOKEN is recovered, `doppler secrets get AGE_PRIVATE_KEY --plain` rebuilds the age file, and `fnox sync` rebuilds the cache.

**Single point of failure**: DOPPLER_TOKEN. Its loss is unrecoverable from the local machine alone.

**Mitigation options**:
- Keep DOPPLER_TOKEN in 1Password (oh wait, subscription expired)
- Keep DOPPLER_TOKEN in a team-shared password manager
- Keep DOPPLER_TOKEN printed on paper in a safe
- Accept the risk — Doppler itself offers account recovery via their web UI if the token is lost

**How to resolve**: Document this in `docs/secrets-workflow.md` as an explicit failure mode and mitigation. Not blocking.

---

## WORK COMPLETED THIS SESSION (2026-04-08, before plan mode was activated)

1. **Deleted `$HOME/` shadow directory** at repo root (208K of stray mise/claude-octopus cache). Added `$HOME/` to `.gitignore` line 53ish.
2. **Edited `home/dot_zshrc.tmpl:80`**: `plugins=(git gh)` → `plugins=(git gh mise)`. Ineffective until chezmoi is repaired (separate issue, not blocking).
3. **Verified Doppler config superset**: `dev_personal` is a strict superset of `dev` (+2 keys).
4. **Verified that `fnox sync --provider keychain` is explicitly rejected** by the CLI.
5. **Verified that `fnox import --provider keychain` is also explicitly rejected**.
6. **Verified that `fnox remove <KEY> --global` is a first-class subcommand**.
7. **Fetched fnox docs** for sync, import, Doppler provider, keychain provider via `agent-fetch`. Summary in VERIFIED FACTS section above.
8. **Wrote the earlier handoff** at `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` covering chezmoi fix + (now-superseded) secrets simplification with the wrong `fnox sync -p keychain` approach.
9. **Re-designed secrets architecture** after the user's feedback on the wrong approach, arriving at Architecture A (this plan).
10. **Dispatched and abandoned two codex adversarial reviews** via `codex:codex-rescue` — both stalled due to broker socket being dead.
11. **Ran `/codex:setup --enable-review-gate`** — gate enabled, auth broken at session time.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   CLOUD (source of truth)                      │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  Doppler                                             │    │
│   │    project: dotfiles                                 │    │
│   │    config:  dev_personal  (~50 secrets + AGE_KEY)    │    │
│   └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
        ▲                                          │
        │ (1) doppler secrets set (direct write)   │ (2) fnox sync
        │                                          │     --provider age
        │                                          │     --global
        │                                          ▼
┌────────────────────────────────────────────────────────────────┐
│               LOCAL MACHINE (offline cache)                    │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  macOS Keychain   service="mde-fnox"                 │    │
│   │    DOPPLER_TOKEN  ← bootstrap only, manual one-time  │    │
│   └──────────────────────────────────────────────────────┘    │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  ~/.config/fnox/age.txt   (0600)                     │    │
│   │    age private key  (bootstrapped from Doppler once) │    │
│   └──────────────────────────────────────────────────────┘    │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  ~/.config/fnox/config.toml                          │    │
│   │    [providers]                                       │    │
│   │      keychain = { type = "keychain", ... }           │    │
│   │      doppler  = { type = "doppler", project = ..., } │    │
│   │      age      = { type = "age", recipients = [...] } │    │
│   │                                                      │    │
│   │    [secrets]                                         │    │
│   │      DOPPLER_TOKEN = { provider = "keychain", ... }  │    │
│   │      GITHUB_TOKEN  = {                               │    │
│   │        provider = "doppler",                         │    │
│   │        value = "GITHUB_TOKEN",                       │    │
│   │        sync = { provider = "age",                    │    │
│   │                 value = "<ciphertext>" }             │    │
│   │      }                                               │    │
│   │      ...                                             │    │
│   └──────────────────────────────────────────────────────┘    │
│                              │                                │
│                              │ fnox activate zsh              │
│                              │ (chpwd + precmd hooks)         │
│                              ▼                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  shell env (zsh)                                     │    │
│   │    $GITHUB_TOKEN, $AWS_ACCESS_KEY_ID, ...            │    │
│   └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### Per-operation flow

```
ADD / UPDATE  (upsert semantics; same code path)
──────────────────────────────────────────────
  mde-secret-add KEY              (zsh wrapper:
                                   eval "$(command mde-py secrets add KEY)")
    │
    ├─[1]─▶ read value from stdin (no ps/history leak)
    │
    ├─[2]─▶ doppler_set_secrets({KEY: VALUE}, project, config)
    │        subprocess: doppler secrets set KEY=VALUE
    │                      --project dotfiles --config dev_personal --silent
    │        on failure: abort (exit 1, nothing else changed)
    │
    ├─[3]─▶ subprocess: fnox sync --provider age --global --force
    │        fnox pulls ALL 50 secrets from Doppler, encrypts each with age,
    │        writes `sync` field on each secret in ~/.config/fnox/config.toml
    │        SELF-HEALING: drift from any source gets corrected here
    │        on failure: exit 2 (Doppler ahead; local cache stale; next run fixes)
    │
    ├─[4]─▶ print to stdout: export KEY='<escaped-value>'
    │
    └─[5]─▶ zsh wrapper evals stdout → $KEY in current shell


REMOVE
──────
  mde-secret-remove KEY
    │
    ├─[1]─▶ subprocess: doppler secrets delete KEY --yes
    │                      --project dotfiles --config dev_personal
    │        on failure: abort (exit 1)
    │        idempotent: if key doesn't exist in Doppler, log info + continue
    │
    ├─[2]─▶ subprocess: fnox sync --provider age --global --force
    │        fnox re-syncs; the removed key is no longer in Doppler,
    │        so its sync field is dropped from ~/.config/fnox/config.toml
    │        This is why remove can use the SAME propagation step as add.
    │        NOTE: verify this behavior via Q2 test before relying on it.
    │        If fnox sync does NOT delete orphans, add an explicit
    │        `fnox remove KEY --global` step here.
    │        on failure: exit 2
    │
    ├─[3]─▶ print to stdout: unset KEY
    │
    └─[4]─▶ zsh wrapper evals stdout → $KEY removed from current shell
```

### Bootstrap chain (fresh machine setup)

```
Fresh machine
    │
    ├─[1]─▶ mise install (gets fnox, doppler CLIs)
    │
    ├─[2]─▶ User manually: get DOPPLER_TOKEN from team/password mgr
    │        fnox set DOPPLER_TOKEN <value> --provider keychain --global
    │        ← ONLY bootstrap secret in Keychain
    │
    ├─[3]─▶ export DOPPLER_TOKEN=$(fnox get DOPPLER_TOKEN)
    │        ← use the just-set Keychain value to authenticate doppler CLI
    │
    ├─[4]─▶ doppler secrets get AGE_PRIVATE_KEY --plain \
    │        > ~/.config/fnox/age.txt
    │        chmod 600 ~/.config/fnox/age.txt
    │        ← bootstrap age key from Doppler (DOPPLER_TOKEN already in Keychain
    │          from step 2)
    │
    ├─[5]─▶ uv run mde-py secrets bootstrap-config
    │        (new sub-subcommand; writes ~/.config/fnox/config.toml with
    │         [providers] and [secrets] declarations pointing at Doppler)
    │
    ├─[6]─▶ uv run mde-py secrets sync
    │        ← runs fnox sync --provider age --global --force under the hood,
    │          encrypts all 50 secrets with age, writes to config.toml
    │
    ├─[7]─▶ eval "$(fnox activate zsh)"
    │        or add permanently via home/dot_oh-my-zsh/custom/50-mde-secrets.zsh
    │        → chpwd/precmd hooks installed
    │
    └─[8]─▶ Restart shell. Secrets available via env vars.
```

---

## CLI surface (changes to `src/mde/cli.py:200-204`)

```python
secrets_p = sub.add_parser("secrets", help="Secrets management")
secrets_p.add_argument(
    "action",
    choices=["sync", "validate", "add", "update", "rm", "bootstrap-config"],
    help="Secrets action",
)
secrets_p.add_argument("key", nargs="?", default=None,
    help="Secret key (for add/update/rm)")
secrets_p.add_argument("--value", default=None,
    help="Secret value (omit to read from stdin or prompt)")
secrets_p.add_argument("--project", default="dotfiles")
secrets_p.add_argument("--config", default="dev_personal")
```

**Deleted actions** (one-time migrations or dead wrappers):
- `refresh` — wraps dead `sops.py` → `mde-sops-secrets-refresh.sh`
- `smoke`   — wraps dead `smoke.py` → `scripts/secrets-smoke-test.sh`
- `export`  — one-time `fnox → Doppler` migration already run

**New actions**:
- `add KEY` — upsert Doppler + fnox sync + emit `export`
- `update KEY` — alias for `add`
- `rm KEY` — delete from Doppler + fnox sync (which drops from cache) + emit `unset`
- `bootstrap-config` — one-time: write `~/.config/fnox/config.toml` with providers + declarations pointing at Doppler. Safe to re-run (idempotent)

**Kept actions**:
- `sync` — now calls `fnox sync --provider age --global --force` instead of the per-key loop
- `validate` — now calls `fnox sync --provider age --global --dry-run` instead of custom parity logic

### Usage

```bash
# Add/update (stdin is default, safest)
echo 'ghp_xxxxxxxxxxxx' | mde-py secrets add GITHUB_TOKEN
# or via zsh wrapper
mde-secret-add GITHUB_TOKEN        # prompts via getpass

# Remove
mde-py secrets rm GITHUB_TOKEN
# or
mde-secret-remove GITHUB_TOKEN

# Full sync (after a change outside mde, e.g., via Doppler web UI)
mde-py secrets sync

# Parity check
mde-py secrets validate

# One-time bootstrap on fresh machine
mde-py secrets bootstrap-config
```

---

## File-by-file changes

### Create

| File | Purpose |
|---|---|
| `src/mde/secrets/manage.py` | New module with `add_secret()`, `update_secret()` (alias), `remove_secret()`, `bootstrap_config()`. Private helpers: `_run_fnox_sync_age()` and `_read_secret_value()` (stdin → `--value` → `MDE_SECRET_VALUE` env → `getpass` prompt) |
| `tests/mde/test_secrets_manage.py` | Pytest mocks for all operations (happy path, Doppler failure, fnox sync failure, stdin vs arg vs env, quote escaping, key name validation) |
| `home/dot_oh-my-zsh/custom/50-mde-secrets.zsh` | Zsh wrapper functions: `mde-secret-add`, `mde-secret-update`, `mde-secret-remove`, plus `eval "$(fnox activate zsh)"` hook installation |
| `docs/secrets-workflow.md` | User-facing doc containing: architecture diagram, per-operation flow diagrams, bootstrap chain diagram, age key rotation procedure, failure modes + mitigation, recovery from DOPPLER_TOKEN loss. (User explicitly asked for docs to contain the diagrams.) |
| `docs/plans/2026-04-08-secrets-crud-architecture-a.md` | Copy of this plan file into the repo for codex adversarial review and persistent reference. First post-approval action. |

### Modify

| File:line | Change |
|---|---|
| `src/mde/secrets/__init__.py:6` | Extend `dispatch_secrets` signature: `dispatch_secrets(action, *, key=None, value=None, project=None, config=None)`. Route `add`/`update`/`rm`/`bootstrap-config` to `manage.py`. Remove dispatch entries for `refresh`/`smoke`/`export` |
| `src/mde/secrets/doppler.py:11-12` | Change `_PROJECT = "dotfiles"` (keep), `_CONFIG = "dev"` → `_CONFIG = "dev_personal"`. Verify all callsites in the module use the constant, not a hardcoded literal |
| `src/mde/secrets/doppler.py` (append) | Add `doppler_delete_secret(key, project, config) -> int` wrapping `doppler secrets delete KEY --yes`. Used by `remove_secret()` |
| `src/mde/secrets/sync.py` | Replace the per-key loop in `sync_doppler_to_fnox()` with a single `subprocess.run(["fnox", "sync", "--provider", "age", "--global", "--force"])`. Fix hardcoded `config="dev"` default to `"dev_personal"`. LOC drops from 48 → ~20 |
| `src/mde/cli.py:200-204` | Update `secrets_p` action choices per CLI surface section above. Add positional `key` and `--value`/`--project`/`--config` flags |
| `src/mde/cli.py:440-447` | Extend `_cmd_secrets` to read `args.key`, `args.value`, resolve value via precedence chain, pass kwargs to `dispatch_secrets`. Preserve `_traced_command` span wrapper |
| `~/.config/fnox/config.toml` (one-time, via `mde-py secrets bootstrap-config`) | Add `[providers.age]` with user's age recipient key. Rename `doppler_dotfiles_dev_personal` → `doppler_dotfiles_dev_personal`. Rewrite `[secrets]` section so each entry uses `provider = "doppler", value = "KEY_NAME"` |
| `~/.config/fnox/age.txt` (one-time) | Generate new age keypair via `age-keygen -o ~/.config/fnox/age.txt`, then `chmod 600` |
| Doppler: `AGE_PRIVATE_KEY` secret (one-time) | `doppler secrets set AGE_PRIVATE_KEY="$(cat ~/.config/fnox/age.txt)"` — enables fresh-machine bootstrap |
| `home/dot_config/mise/config.toml.tmpl` | Remove `[plugins]` and `_.fnox-env = { tools = true }` lines (shell integration now happens via `fnox activate` in `50-mde-secrets.zsh` instead of `mise-env-fnox`) |
| `CLAUDE.md` Secrets section | Rewrite to reference new CLI (`mde-py secrets add/update/rm/sync/validate`), `dev_personal` config, and `fnox activate` shell integration. Link to `docs/secrets-workflow.md` |
| `.claude/rules/secrets-management.md` | Update pipeline diagram and examples. Drop 1Password/sops mentions. Drop `uv run mde-py secrets refresh/smoke/export`. Reference the age keypair bootstrap. Link to `docs/secrets-workflow.md` |
| `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` | **Post-approval only**: add a prominent NOTE at top marking the Phase 2 section as SUPERSEDED by `docs/secrets-workflow.md` and `docs/plans/2026-04-08-secrets-crud-architecture-a.md`. Phase 1 (chezmoi fix) is untouched. |

### Delete

| Path | Reason |
|---|---|
| `src/mde/secrets/sops.py` | Wraps dead SOPS bash scripts. Three tests in `tests/mde/test_secrets_doppler.py:419,427,438` import this — delete those tests |
| `src/mde/secrets/keychain.py` | Wraps `scripts/mde-sops-secrets-import-keychain.sh` (dead) |
| `src/mde/secrets/smoke.py` | Wraps `scripts/secrets-smoke-test.sh` (dead) |
| `src/mde/secrets/export_to_doppler.py` | One-time migration already run |
| `src/mde/secrets/validate_parity.py` | Replaced by `fnox sync --provider age --global --dry-run` (reports drift without writes) |
| `scripts/mde-sops-secrets-refresh.sh` | Wrapped by deleted `sops.py` |
| `scripts/mde-sops-secrets-import-keychain.sh` | Wrapped by deleted `keychain.py` |
| `scripts/mde-sops-secrets-backup-1password.sh` | 1Password removal (subscription expired) |
| `scripts/secrets-smoke-test.sh` | Wrapped by deleted `smoke.py` |
| `.agents/skills/1password-fnox/` | 1Password removal |
| `.mise.toml` task `mde:secrets:backup:1password` | 1Password removal |
| `home/.chezmoidata/tools.yaml` line 96 (`1password-cli`) | 1Password removal |

---

## Tests (`tests/mde/test_secrets_manage.py`)

Use the monkeypatch + `subprocess.run` mock pattern from existing `tests/mde/test_secrets_doppler.py`. Cases:

1. `test_add_secret_writes_doppler_then_runs_fnox_sync_then_emits_export`
2. `test_add_secret_doppler_failure_aborts_before_fnox_sync` — exit 1, fnox never called
3. `test_add_secret_fnox_sync_failure_returns_partial` — exit 2, export NOT emitted (state uncertain)
4. `test_update_is_alias_for_add`
5. `test_remove_secret_deletes_from_doppler_then_runs_fnox_sync_then_emits_unset`
6. `test_remove_secret_idempotent_when_key_missing_from_doppler` — doppler returns "not found", continue
7. `test_value_from_stdin_when_no_arg_and_stdin_not_tty`
8. `test_value_from_flag_overrides_stdin`
9. `test_value_from_env_var_when_stdin_tty_and_no_flag`
10. `test_value_from_getpass_when_all_else_missing`
11. `test_empty_string_value_allowed_via_explicit_flag`
12. `test_quote_escaping_in_export_line` — `'` → `'\''`
13. `test_invalid_key_name_rejected` — lowercase/hyphen/leading digit → exit 3
14. `test_default_config_is_dev_personal`
15. `test_fnox_sync_failure_surfaces_stderr_to_caller`
16. `test_bootstrap_config_creates_providers_and_declarations` — idempotent, respects existing DOPPLER_TOKEN entry
17. `test_bootstrap_config_is_idempotent` — running twice is a no-op

---

## Execution Order (after codex review + user approval)

### Phase 0 — Setup
```bash
cd ~/dev/github/ray-manaloto/macos-development-environment
git checkout -b feat/secrets-crud-architecture-a
uv run mde-py quality    # baseline, note any pre-existing warnings
```

### Phase 1 — Write code
1. Create `src/mde/secrets/manage.py` with `add_secret`, `update_secret`, `remove_secret`, `bootstrap_config`, `_run_fnox_sync_age`, `_read_secret_value`
2. Fix `_CONFIG` in `src/mde/secrets/doppler.py:12`
3. Add `doppler_delete_secret` to `src/mde/secrets/doppler.py`
4. Rewrite `src/mde/secrets/sync.py` to call `fnox sync --provider age --global --force`
5. Extend `src/mde/secrets/__init__.py:dispatch_secrets` signature
6. Update `src/mde/cli.py:200-204` (parser) and `440-447` (handler)
7. Create `tests/mde/test_secrets_manage.py`
8. Run `uv run mde-py quality` — should pass

### Phase 2 — Bootstrap (one-time manual, before first use)
```bash
# 1. Snapshot current state
cp ~/.config/fnox/config.toml ~/.config/fnox/config.toml.backup-$(date +%Y%m%d)

# 2. Generate age keypair
mkdir -p ~/.config/fnox
age-keygen -o ~/.config/fnox/age.txt
chmod 600 ~/.config/fnox/age.txt

# 3. Extract public key for recipient
age-keygen -y ~/.config/fnox/age.txt  # prints age1... recipient

# 4. Store private key in Doppler for fresh-machine recovery
doppler secrets set AGE_PRIVATE_KEY="$(cat ~/.config/fnox/age.txt)" \
  --project dotfiles --config dev_personal --silent

# 5. Write new ~/.config/fnox/config.toml
uv run mde-py secrets bootstrap-config

# 6. First sync
uv run mde-py secrets sync
# → fnox sync --provider age --global --force
# → pulls 50 secrets from Doppler, encrypts, writes to config.toml

# 7. Verify
uv run mde-py secrets validate   # fnox sync --dry-run, should be clean
grep -c 'sync = ' ~/.config/fnox/config.toml   # should be ~50
```

### Phase 3 — Shell integration
1. Create `home/dot_oh-my-zsh/custom/50-mde-secrets.zsh` with wrapper functions + `fnox activate` hook install
2. Remove `[plugins]` and `_.fnox-env` from `home/dot_config/mise/config.toml.tmpl`
3. If chezmoi is working: `chezmoi apply`. If not: manually copy `50-mde-secrets.zsh` to `~/.oh-my-zsh/custom/`
4. Open a new shell, verify `$GITHUB_TOKEN` is in env

### Phase 4 — Delete dead code
Delete files per the Delete table above. Run `uv run mde-py quality` + `pytest` to confirm nothing breaks.

### Phase 5 — Docs
1. Create `docs/secrets-workflow.md` with all diagrams from this plan + failure modes + age rotation procedure + recovery procedure
2. Update `CLAUDE.md` Secrets section
3. Update `.claude/rules/secrets-management.md`
4. Update prior plan `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` with SUPERSEDED note on Phase 2
5. Copy this plan to `docs/plans/2026-04-08-secrets-crud-architecture-a.md`

### Phase 6 — Commits
Split into logical chunks:
- Commit 1: bootstrap support (`bootstrap_config` + CLI wiring)
- Commit 2: `manage.py` + tests + CLI wiring for add/update/rm
- Commit 3: simplify `sync.py` to use `fnox sync` directly + fix `dev` → `dev_personal`
- Commit 4: delete dead files (sops, keychain, smoke, export_to_doppler, validate_parity, bash scripts, 1password skill)
- Commit 5: shell integration (`50-mde-secrets.zsh`, remove `mise-env-fnox` from config template)
- Commit 6: docs (`secrets-workflow.md`, `CLAUDE.md`, `secrets-management.md`, prior plan update, copy to docs/plans/)

### Phase 7 — Verification (see Verification section below)

### Phase 8 — Open PR

---

## Verification

Run these commands in order, confirm each expected result:

```bash
# 1. Quality gate
uv run mde-py quality                     # 6/6 pass
uv run pytest tests/mde/test_secrets_manage.py -v   # all pass

# 2. Provider verification
fnox provider list                         # keychain, doppler_dotfiles_dev_personal (no typo), age

# 3. Bootstrap verification (after Phase 2)
cat ~/.config/fnox/age.txt | head -2       # shows "# created: ..." and public key comment
fnox get DOPPLER_TOKEN                      # returns the token from Keychain
doppler secrets get AGE_PRIVATE_KEY --plain | diff - ~/.config/fnox/age.txt
                                            # should be empty (matches)

# 4. Full sync
uv run mde-py secrets sync                  # runs fnox sync --provider age --global --force

# 5. Parity check
uv run mde-py secrets validate              # fnox sync --dry-run, reports clean

# 6. Add flow
echo 'test_value_12345' | uv run mde-py secrets add MDE_TEST_SECRET
                                            # stdout: export MDE_TEST_SECRET='test_value_12345'
doppler secrets get MDE_TEST_SECRET --plain # returns test_value_12345
grep MDE_TEST_SECRET ~/.config/fnox/config.toml
                                            # entry exists with sync.provider=age

# 7. Shell integration (open a NEW terminal)
echo $MDE_TEST_SECRET                       # test_value_12345

# 8. Remove flow
uv run mde-py secrets rm MDE_TEST_SECRET
doppler secrets get MDE_TEST_SECRET --plain 2>&1 | grep -q "not found"
grep MDE_TEST_SECRET ~/.config/fnox/config.toml || echo "not in config ✓"

# 9. Current-shell propagation via eval wrapper
eval "$(uv run mde-py secrets add DEMO_KEY --value demo_val)"
echo $DEMO_KEY                              # demo_val
eval "$(uv run mde-py secrets rm DEMO_KEY)"
echo $DEMO_KEY                              # empty / unset

# 10. Open questions answered
# Q1: where does fnox sync write?
fnox sync --provider age --global --dry-run 2>&1 | grep -i 'config\|file'
# Q2: does fnox sync delete orphans?
# (tested empirically in step 8 above)
# Q3: does activate resolve from sync field?
fnox activate zsh 2>&1 | head -20 | grep GITHUB_TOKEN
```

---

## Out of scope (followup work)

- **Stripping 43 declarations from repo `fnox.toml`** — these will SHADOW the new global config declarations until removed (see Q5). Addressed in a separate commit after this plan's parity verification.
- **Chezmoi repair** — the earlier plan at `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` Phase 1. Independent work, not blocking.
- **`$HOME/` shadow dir + `[scriptEnv]` tempdir pollution** — same prior plan, separate work.
- **`fnox.toml` `if_missing = "ignore"` tightening** — currently every secret has `if_missing = "ignore"`. Consider moving to `"warn"` for production secrets.
- **YubiKey-backed age identity** — if hardware-backed decryption is desired, swap `[providers.age]` to use `age-plugin-yubikey` recipient. Not in scope for initial migration.
- **Rotation procedure for AGE_PRIVATE_KEY** — document in `docs/secrets-workflow.md` but not automated.
- **Multi-machine synchronization** — if the user uses mde on multiple machines, each needs its own bootstrap. Out of scope but document.

---

## Rollback

Data loss risk: **zero** (Doppler is unchanged throughout).

```bash
# 1. Revert code
git revert <migration-commit-shas>
git push

# 2. Restore previous ~/.config/fnox/config.toml
cp ~/.config/fnox/config.toml.backup-YYYYMMDD ~/.config/fnox/config.toml

# 3. Re-populate Keychain via the old Python loop (from the pre-revert state)
uv run mde-py secrets sync    # runs the old sync.py loop

# 4. If reverting back to pre-age state
rm ~/.config/fnox/age.txt
doppler secrets delete AGE_PRIVATE_KEY --yes --project dotfiles --config dev_personal
```

---

## LINKED RULES (load these when resuming)

- `.claude/rules/secrets-management.md` — current (stale) secrets doc, to be updated
- `.claude/rules/library-first.md` — why Pydantic BaseModel for any new models
- `.claude/rules/no-shell-scripts.md` — why the migration exists in the first place
- `.claude/rules/no-warning-suppression.md` — error handling standard
- `.claude/rules/declarative-config.md` — no standalone config files
- `.claude/rules/mise-first.md` — tool ownership
- `CLAUDE.md` Secrets section — to be updated
- `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md` — prior plan, Phase 1 still valid, Phase 2 superseded by this

---

## SESSION HISTORY SUMMARY (for context, not action)

2026-04-08 session highlights relevant to this plan:
- User asked about `$HOME/` directory → deleted shadow dir, gitignored
- User noted fnox 1.20.0 added native Doppler provider + expired 1Password subscription → proposed secrets simplification
- User disabled `mise-env-fnox` plugin due to oh-my-zsh conflicts → needed new shell integration path
- Doppler `dev` vs `dev_personal` comparison → `dev_personal` is strict superset
- User said to drop `age` entirely → later reversed after seeing fnox sync requires encryption provider
- Discovered chezmoi not managing any files → separate plan (not this one)
- Dispatched wrong-architecture adversarial review via `codex:codex-rescue` → stalled
- I wrote first handoff (`docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md`) based on wrong `fnox sync -p keychain` assumption
- User asked to verify assumption → two live CLI tests proved both `fnox sync -p keychain` and `fnox import -p keychain` are rejected
- User proposed simplified "Doppler + sync" workflow → I explained the mismatch and presented Architecture A (fnox-blessed age encryption) vs B (loop-to-keychain)
- User chose Architecture A + age key stored in Doppler
- User entered plan mode and requested a comprehensive plan with diagrams, targeting codex adversarial review
- This plan file was written

---

## RELATIONSHIP TO EARLIER HANDOFF

This plan **supersedes Phase 2 only** of `docs/plans/2026-04-08-sync-dotfiles-and-secrets-simplification.md`.

That earlier handoff has two phases:
- **Phase 1 — Chezmoi sync-dotfiles migration**: still valid. Independent work. Covers `scripts/ensure-managed-configs.sh` → `src/mde/maintain/sync_dotfiles.py` migration + chezmoi config repair. Not affected by this plan.
- **Phase 2 — Secrets simplification**: WRONG architecture (used `fnox sync --provider keychain`). **This plan replaces it.**

Execution ordering between the two plans:
- Phase 1 of earlier plan can execute independently (chezmoi repair). Low risk.
- This plan can also execute independently — the secrets CRUD wrapper doesn't depend on chezmoi being fixed, but the shell integration piece (`home/dot_oh-my-zsh/custom/50-mde-secrets.zsh`) ideally flows through chezmoi. If chezmoi is still broken, manually copy the file.
- Both plans can land in separate PRs.

---

## ADVERSARIAL REVIEW RESPONSE (2026-04-08, codex verdict: needs-attention)

Codex flagged 3 HIGH and 2 MEDIUM issues. User decision: **get the happy path working fast, iterate to close gaps**. Each finding is addressed below with a pragmatic MVP posture — what we do in THIS PR vs what moves to a tracked follow-up issue. Nothing is dismissed; nothing is suppressed.

### H1 — Repo `fnox.toml` shadows new global provider (codex HIGH)
**Verdict:** FOLD INTO THIS PR. This is the one finding we cannot defer — codex is right that declaring victory while the repo overlay silently wins is false confidence.
**Action:**
- Phase 2 step 6 (first sync) is blocked until repo `fnox.toml` is cleaned.
- New Phase 2.5: run `fnox list --sources` and confirm NO secret resolves from the repo file. If any do, strip those entries from `fnox.toml` in THIS PR (new commit: `refactor(secrets): strip repo fnox.toml keychain overlay`).
- Acceptance gate: `fnox list --sources 2>&1 | grep -c '/fnox.toml'` must be 0 for all managed secrets before Phase 3.
- The originally-planned "followup PR to strip 43 entries" is cancelled — it's done in this PR.

### H2 — Single unrecoverable token path + no tested rotation (codex HIGH)
**Verdict:** PARTIAL IN THIS PR, rest → follow-up issues. Accept the single-point-of-failure for now because the user is a single operator on a single primary machine; dual-recipient overlap is overkill for MVP.
**In this PR:**
- `docs/secrets-workflow.md` MUST contain a literal, copy-pasteable **"Emergency recovery"** runbook (not hand-wavy prose): exact commands to rebuild `age.txt` from Doppler given only `DOPPLER_TOKEN`, and exact commands to re-bootstrap a fresh machine end-to-end.
- Bootstrap script MUST store `DOPPLER_TOKEN` in the macOS Keychain under a well-known label AND print a reminder to copy it into a second location (password manager of user's choice). No second automated channel, but the reminder is mandatory.
- `mde-py secrets doctor` (new, tiny — ~30 LOC): checks that `~/.config/fnox/age.txt` exists + 0600, that `DOPPLER_TOKEN` is retrievable from Keychain, and that `doppler secrets get AGE_PRIVATE_KEY --plain` matches `~/.config/fnox/age.txt`. Run in Phase 7 verification.
**Tracked as follow-up** (create GitHub issues with `auto:agent-discovered` label during Phase 8):
- Issue A: "Two-phase age key rotation with dual-recipient overlap window"
- Issue B: "Scripted `mde-py secrets bootstrap` one-shot fresh-machine setup"
- Issue C: "Second recovery channel for DOPPLER_TOKEN (e.g., age-encrypted copy in a separate cloud store)"

### H3 — Age key path moved but existing shell exporters not migrated (codex HIGH)
**Verdict:** FOLD INTO THIS PR. This is a one-line edit per file — no reason to defer, and leaving it creates silent shell-vs-script divergence.
**Action:** Add to the Modify table:
- `home/dot_oh-my-zsh/custom/10-mde-core.zsh:43` — change `FNOX_AGE_KEY_FILE=$HOME/.config/mise/age.txt` → `$HOME/.config/fnox/age.txt`
- `home/dot_zprofile.d/macos-dev-env.zsh:45` — same change
- **Simpler alternative (adopted):** KEEP existing `~/.config/mise/age.txt` path to avoid touching shell exporters at all. Update Phase 2 bootstrap to write there instead of `~/.config/fnox/age.txt`. This eliminates the migration entirely and codex's concern goes away. `FNOX_AGE_KEY_FILE` already points there; fnox's age provider honors the env var.
- **Decision: adopt the simpler alternative.** Phase 2 step 2 now writes `~/.config/mise/age.txt`. Plan section "File-by-file changes" — remove the `~/.config/fnox/age.txt` row, add `~/.config/mise/age.txt` instead. Shell exporters remain untouched.

### M1 — Full-provider fanout on every mutation (codex MEDIUM)
**Verdict:** ACCEPT FOR MVP, iterate later. The user has ~50 secrets and mutations are manual/infrequent; a 2-3s full resync per `mde secrets add` is acceptable to ship. Codex's concern is real but premature for this scale.
**In this PR:**
- Add bounded retry: `fnox sync` retried once on transient failure (network timeout, rate limit), no backoff fancier than `sleep 2`.
- Add post-sync verification: after `fnox sync`, run `fnox get KEY` for the just-mutated key and confirm the value matches what was written to Doppler. If mismatch → exit 2 with clear "drift detected, re-run `mde secrets sync`" message.
- Exit codes unchanged: 0 = success, 1 = Doppler failed (nothing changed), 2 = Doppler OK but local cache stale.
**Tracked as follow-up:**
- Issue D: "Targeted single-key fnox update path to avoid full resync on every mutation" — only worth doing if the secret count grows or sync latency becomes user-visible.

### M2 — Deleting `validate_parity.py` loses bidirectional coverage (codex MEDIUM)
**Verdict:** KEEP `validate_parity.py` FOR THIS PR. Codex is right that `fnox sync --dry-run` is an unverified substitute. Deferring the delete costs us nothing — the file is 65 LOC and its tests already exist.
**Action:**
- Remove `src/mde/secrets/validate_parity.py` from the Delete table. Keep it.
- Keep the 3 tests in `tests/mde/test_secrets_doppler.py:191-279` that cover it.
- Update the validator's internals to read `dev_personal` instead of `dev` (one-line fix).
- `mde-py secrets validate` still calls `validate_secrets_parity()`. Add a SECOND check: also run `fnox sync --provider age --global --dry-run` and report any drift it finds. Two signals are better than one during migration.
**Tracked as follow-up:**
- Issue E: "Evaluate whether `fnox sync --dry-run` is a complete replacement for `validate_parity.py` — add integration tests proving bidirectional equivalence (orphaned local keys, repo/global shadowing), then delete `validate_parity.py`."

### Summary of plan amendments (delta from original plan above)

| Section | Change |
|---|---|
| Execution Order Phase 2 | Insert new step 2.5: `fnox list --sources` gate before first sync |
| Execution Order Phase 2 step 2 | Age key path: `~/.config/mise/age.txt` (NOT `~/.config/fnox/age.txt`) |
| Execution Order Phase 4 (Delete) | Remove `validate_parity.py` from deletion list |
| Execution Order Phase 4 (Delete) | ADD: strip 35+ repo-level keychain entries from `fnox.toml` |
| Execution Order Phase 6 (Commits) | New commit: `refactor(secrets): strip repo fnox.toml keychain overlay` |
| Execution Order Phase 7 | Add: `mde-py secrets doctor` verification run |
| Execution Order Phase 8 | Add: create GitHub issues A–E with `auto:agent-discovered` label |
| File-by-file changes Create | Add `docs/secrets-workflow.md` "Emergency recovery" runbook requirement |
| File-by-file changes Modify | `src/mde/secrets/manage.py` — add bounded retry + post-sync verification to `_run_fnox_sync_age` |
| File-by-file changes Modify | `src/mde/secrets/validate_parity.py` — change `dev` → `dev_personal` constant |
| File-by-file changes Modify | Add `mde-py secrets doctor` subcommand |
| File-by-file changes Delete | REMOVE `validate_parity.py` row (keep the file) |
| CLI surface | Add `doctor` action to `choices=[...]` |
| Tests | Add `test_add_secret_post_sync_verification_catches_drift` |
| Tests | Add `test_fnox_sync_retries_once_on_transient_failure` |
| Tests | Add `test_doctor_reports_age_file_missing_permissions_mismatch` |

### What is explicitly deferred to follow-up issues (not in this PR)

- Issue A: Dual-recipient age key rotation with overlap window
- Issue B: Scripted `mde-py secrets bootstrap` one-shot fresh-machine setup (replaces manual Phase 2 steps)
- Issue C: Second recovery channel for `DOPPLER_TOKEN`
- Issue D: Targeted single-key fnox update path (only if sync latency becomes painful)
- Issue E: Delete `validate_parity.py` after `fnox sync --dry-run` is proven equivalent

These MUST be filed during Phase 8 (PR open) and linked from the PR description.

---

**End of plan. Review complete: 2026-04-08. Ready to proceed to Phase 0 after user approval of this Adversarial Review Response.**
