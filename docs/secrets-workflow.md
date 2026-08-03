# Secrets Workflow

Doppler is the cloud source of truth. The local machine holds only `DOPPLER_TOKEN` (in macOS Keychain under service `mde-fnox`) and an age private key (`~/.config/mise/age.txt`); everything else flows from `fnox sync --provider age --global` into `~/.config/fnox/config.toml` and is exposed to the shell via `fnox activate zsh` chpwd/precmd hooks installed by `~/.zshrc.d/50-mde-secrets.zsh`. One unified CLI (`mde-py secrets {add,update,rm,sync,validate,bootstrap-config,doctor}`) performs Doppler-first writes followed by a single resync, so all layers stay coherent.

## DOPPLER_TOKEN setup

`DOPPLER_TOKEN` is the Doppler service/CLI token (prefix `dp.ct.` for `doppler login` tokens, `dp.st.` for service tokens) that authenticates the `doppler` CLI when no other auth state is available. The architecture relies on it being in the `mde-fnox` macOS Keychain entry so that `fnox hook-env` can export it to every new shell and the `doppler` CLI — and `mde-py secrets doctor` — can always find it without interactive prompts.

**Two seeding paths depending on machine state:**

**(A) Existing machine where `doppler login` was already run** — Doppler CLI already has a token in its own storage (`~/.doppler/.doppler.yaml` points at a macOS keychain item under service `doppler-cli`). Mirror it into `mde-fnox`:

```bash
fnox set DOPPLER_TOKEN "$(doppler configure get token --plain)" \
  --provider keychain --global
```

**(B) Fresh machine (no `doppler login` yet)** — retrieve the token from your out-of-band channel (team password manager / second Mac / printed paper) and seed both:

```bash
# 1. seed fnox's mde-fnox keychain entry
fnox set DOPPLER_TOKEN <TOKEN_VALUE> --provider keychain --global

# 2. temporarily export so doppler CLI picks it up during bootstrap
export DOPPLER_TOKEN="$(fnox get DOPPLER_TOKEN)"

# 3. run `doppler login` to establish the doppler CLI's own auth state
doppler login
```

After either path, verify with:

```bash
mde-py secrets doctor          # expects rc=0
fnox get DOPPLER_TOKEN         # expects the dp.ct.* / dp.st.* token
```

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
│   │  ~/.config/mise/age.txt   (0600)                     │    │
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

## Per-operation flow

### ADD / UPDATE (upsert, same code path)

```
mde-secret-add KEY              (zsh wrapper:
                                 eval "$(command mde-py secrets add KEY)")
  │
  ├─[1]─▶ read value from stdin (no ps/history leak)
  │
  ├─[2]─▶ doppler secrets set KEY=VALUE
  │        --project dotfiles --config dev_personal --silent
  │        on failure: abort (exit 1, nothing else changed)
  │
  ├─[3]─▶ fnox sync --provider age --global --force
  │        fnox pulls ALL secrets from Doppler, encrypts with age,
  │        writes `sync` field on each secret in ~/.config/fnox/config.toml
  │        SELF-HEALING: drift from any source gets corrected here
  │        on failure: exit 2 (Doppler ahead; local cache stale; next run fixes)
  │
  ├─[4]─▶ print to stdout: export KEY='<escaped-value>'
  │
  └─[5]─▶ zsh wrapper evals stdout → $KEY in current shell
```

### REMOVE

```
mde-secret-remove KEY
  │
  ├─[1]─▶ doppler secrets delete KEY --yes
  │        --project dotfiles --config dev_personal
  │        idempotent: if missing, log info and continue
  │
  ├─[2]─▶ fnox sync --provider age --global --force
  │        the removed key drops from ~/.config/fnox/config.toml
  │
  ├─[3]─▶ print to stdout: unset KEY
  │
  └─[4]─▶ zsh wrapper evals stdout → $KEY removed from current shell
```

## Bootstrap chain (fresh machine setup)

```
Fresh machine
    │
    ├─[1]─▶ mise install (gets fnox, doppler CLIs)
    │
    ├─[2]─▶ User manually: get DOPPLER_TOKEN from team/password mgr
    │        fnox set DOPPLER_TOKEN <value> --provider keychain --global
    │
    ├─[3]─▶ export DOPPLER_TOKEN=$(fnox get DOPPLER_TOKEN)
    │
    ├─[4]─▶ doppler secrets get AGE_PRIVATE_KEY --plain \
    │        > ~/.config/mise/age.txt
    │        chmod 600 ~/.config/mise/age.txt
    │
    ├─[5]─▶ uv run mde-py secrets bootstrap-config
    │        (writes ~/.config/fnox/config.toml with providers and
    │         declarations pointing at Doppler)
    │
    ├─[6]─▶ uv run mde-py secrets sync
    │        (fnox sync --provider age --global --force; encrypts and
    │         writes ciphertext for all 50 secrets)
    │
    ├─[7]─▶ eval "$(fnox activate zsh)"  (or via 50-mde-secrets.zsh)
    │
    └─[8]─▶ Restart shell. Secrets available via env vars.
```

## CLI usage

```bash
# Add / update (stdin keeps the value out of ps + history)
echo 'ghp_xxxxxxxxxxxx' | uv run mde-py secrets add GITHUB_TOKEN
uv run mde-py secrets update GITHUB_TOKEN --value 'ghp_yyy'

# Remove
uv run mde-py secrets rm GITHUB_TOKEN

# Full re-sync (after editing in Doppler web UI)
uv run mde-py secrets sync

# Parity / drift check
uv run mde-py secrets validate

# One-time fresh-machine bootstrap
uv run mde-py secrets bootstrap-config

# Health/diagnostic
uv run mde-py secrets doctor
```

## Emergency recovery runbook

### If you lose `~/.config/mise/age.txt`

The local age private key is just a cache — Doppler holds the canonical copy.

```bash
# 1. Retrieve DOPPLER_TOKEN from your out-of-band channel
#    (team password manager, Doppler web UI service token, printed paper, etc.)
fnox set DOPPLER_TOKEN <value> --provider keychain --global
export DOPPLER_TOKEN=$(fnox get DOPPLER_TOKEN)

# 2. Re-fetch the age private key from Doppler
mkdir -p ~/.config/mise
doppler secrets get AGE_PRIVATE_KEY --plain \
  --project dotfiles --config dev_personal > ~/.config/mise/age.txt
chmod 600 ~/.config/mise/age.txt

# 3. Re-run bootstrap + sync
uv run mde-py secrets bootstrap-config
uv run mde-py secrets sync
```

### If you lose `DOPPLER_TOKEN`

`DOPPLER_TOKEN` is the **single point of failure** in this architecture. If you
lose it AND your local machine cannot decrypt its age cache, you must recover
through Doppler's account-level recovery flow:

1. Log into the Doppler web UI with your account credentials (separate from
   the service token).
2. Issue a new service token from `dotfiles → dev_personal → Access`.
3. Store it in macOS Keychain via `fnox set DOPPLER_TOKEN <new> --provider keychain --global`.
4. Follow the "lost age key" runbook above.

**Mitigation:** keep `DOPPLER_TOKEN` in a second password manager (1Password,
Bitwarden, paper safe). Never let it live only in this Keychain.

### Fresh machine bootstrap (full sequence)

```bash
# 1. Install mise + tools (this brings in fnox + doppler CLIs)
curl https://mise.run | sh
mise install

# 2. Bootstrap DOPPLER_TOKEN into Keychain
fnox set DOPPLER_TOKEN <value-from-team-vault> --provider keychain --global
export DOPPLER_TOKEN=$(fnox get DOPPLER_TOKEN)

# 3. Pull the age private key from Doppler
mkdir -p ~/.config/mise
doppler secrets get AGE_PRIVATE_KEY --plain \
  --project dotfiles --config dev_personal > ~/.config/mise/age.txt
chmod 600 ~/.config/mise/age.txt

# 4. Generate ~/.config/fnox/config.toml with providers + declarations
uv run mde-py secrets bootstrap-config

# 5. First full sync (encrypts all 50 secrets with age)
uv run mde-py secrets sync

# 6. Activate the shell hook
eval "$(fnox activate zsh)"
# Or add permanently via home/dot_oh-my-zsh/custom/50-mde-secrets.zsh
```

## Age key rotation (manual, documented only)

This is a documented procedure — there is no automation today (tracked as
follow-up Issue A). Run when the age private key is compromised, when a
teammate departs, or on a scheduled rotation cadence.

1. Generate a new age keypair: `age-keygen -o ~/.config/mise/age.txt.new`
2. Update Doppler: `doppler secrets set AGE_PRIVATE_KEY="$(cat ~/.config/mise/age.txt.new)" --project dotfiles --config dev_personal`
3. Update `[providers.age].recipients` in `~/.config/fnox/config.toml` with the new public key (`age-keygen -y ~/.config/mise/age.txt.new`).
4. Replace the old key: `mv ~/.config/mise/age.txt.new ~/.config/mise/age.txt && chmod 600 ~/.config/mise/age.txt`
5. Re-encrypt the cache: `uv run mde-py secrets sync` (i.e. `fnox sync --provider age --global --force`).
6. **On every other machine** that holds a local cache: follow the "lost age key" runbook to pull the new key from Doppler and re-sync.

## Known failure modes and mitigations

- **Partial sync drift.** A `mde-py secrets add` that succeeds in Doppler but fails the subsequent `fnox sync` returns exit code 2. The cloud is ahead of the cache; the next `mde-py secrets sync` (or any subsequent add/update/rm) reconciles automatically.
- **DOPPLER_TOKEN single point of failure.** Losing the token without an out-of-band copy means recovery via Doppler's web UI account flow. Mitigate by storing the token in a second password manager.
- **Repo `fnox.toml` overlay shadowing.** Earlier in this branch, the repo-level `fnox.toml` declared 43 entries with `provider = "keychain"`, which shadowed the new global `provider = "doppler"` declarations because fnox merges repo over global. **Fixed in Phase 4a** by stripping the overlay. Lesson: any future repo `fnox.toml` must avoid declaring secret keys that the global config owns; use repo `fnox.toml` only for repo-only overrides.
- **Cold-start latency.** `fnox activate zsh` reads the age cache, not Doppler, so chpwd hooks are O(ms). The slow path is `mde-py secrets sync`, which re-encrypts all 50 secrets — expect several seconds per call.

## Follow-up issues

These items are deferred and tracked as GitHub issues (placeholders — actual
numbers filed in Phase 8 of the architecture-A plan):

- **Issue A** — Automate age key rotation (currently a manual runbook).
- **Issue B** — Add `mde-py secrets doctor` end-to-end health check (Doppler reachability, age key permissions, fnox provider listing, parity).
- **Issue C** — Multi-machine fan-out helper for re-sync after rotation.
- **Issue D** — Keychain entry for a backup `DOPPLER_TOKEN` recovery escrow.
- **Issue E** — Periodic drift alarm (cron) running `mde-py secrets validate`.
- **Issue F** — Migrate Phase 3 shell wrapper from oh-my-zsh to starship after the planned shell migration lands.
