# Research Brief: Doppler + chezmoi + mise + fnox Integration

**Research Date:** 2026-03-27
**Provenance:** finding-doppler-secrets-setup.yaml
**Phase:** deep-research (post-brainstorming)

## Context

Migrating 40 secrets from fnox/Keychain-only to Doppler as source of truth.
Current: fnox.toml -> macOS Keychain -> mise (_.fnox-env) -> env vars -> tools
Target: Doppler (project: dotfiles, config: dev) -> sync -> fnox/Keychain -> mise

## Key Findings

### chezmoi Native Doppler Support (CONFIRMED)
- `{{ doppler "SECRET_NAME" "project" "config" }}` — single secret, cached
- `{{ dopplerProjectJson "project" "config" }}` — all secrets as JSON
- Config: `[doppler] project = "dotfiles" config = "dev"` in chezmoi.toml
- Source: chezmoi.io/user-guide/password-managers/doppler/

### mise [env] Doppler Patterns (FROM skills.sh)
- exec pattern: `{{ exec(command='doppler secrets get KEY --plain') }}`
- cache pattern: `{{ cache(key='k', duration='1h', run='doppler secrets get KEY --plain') }}`
- Recommended: keep _.fnox-env + build sync command (zero mise changes)
- Source: skills.sh/terrylica/cc-skills/doppler-secret-validation

### Doppler Bulk Set (CONFIRMED)
- `doppler secrets set KEY1="v1" KEY2="v2" --project dotfiles --config dev`
- Source: docs.doppler.com/docs/setting-secrets

### Critical Gotcha: --command flag
- `doppler run --command='echo $SECRET'` (CORRECT)
- `doppler run -- echo $SECRET` (WRONG: premature shell expansion)

### srclight: pip install srclight, 29 MCP tools, Python 3.11+
### mcp2cli: already installed, exa is Tier 1 (excellent CLI fit)

## Recommended: Pattern C (_.fnox-env + sync)
Zero mise changes, Doppler as source of truth, fnox/Keychain as cache.

---

## Original Comparison

1. **Doppler** — Cloud-based secrets manager with CLI, 20+ integrations, team RBAC
2. **fnox + macOS Keychain** — Local-first secrets store, native integration

## Quick Setup: Doppler

### Installation (macOS)

```bash
# Install gnupg for signature verification
brew install gnupg

# Install Doppler CLI
brew install dopplerhq/cli/doppler

# Verify
doppler --version
doppler update  # for future upgrades
```

### First Time Setup

```bash
# Browser-based authentication (one-time per workspace)
doppler login

# Navigate to your project
cd /path/to/project

# Interactive setup (select project + config)
doppler setup

# Or use declarative doppler.yaml
cat > doppler.yaml << 'EOF'
setup:
  - project: example
    config: dev_personal
EOF
```

### Run Commands with Secrets

```bash
# Inject secrets as environment variables
doppler run -- npm start

# Or with command string
doppler run --command="./script.sh && npm test"

# Access in code
echo $DATABASE_URL
```

### For Production / CI

```bash
# Create read-only service token (scoped to single config)
doppler setup  # select project/config first
doppler configs tokens create prod-token --plain

# Use in CI/CD
export DOPPLER_TOKEN='dp.st.prd.xxxx'
doppler run -- your-app-binary
```

## Feature Comparison Matrix

| Feature | Doppler | fnox + Keychain |
|---------|---------|-----------------|
| **Cloud Sync** | ✅ Yes (primary) | ❌ No (local only) |
| **Team RBAC** | ✅ Yes (built-in) | ❌ No (local users) |
| **Offline Access** | ✅ Encrypted fallback cache | ✅ Native (always local) |
| **Cost** | Free (3 users) → $8-21/user | $0 (built-in to macOS) |
| **Integrations** | ✅ 20+ platforms | ❌ Keychain-locked |
| **macOS Native** | ⚠️ No (but has fallback) | ✅ Yes (native Keychain) |
| **API Automation** | ✅ REST + Postman | ⚠️ CLI only |
| **Secret Rotation** | ✅ Team+ plan | ❌ Manual |
| **Activity Logs** | ✅ 3-90 days | ❌ None |
| **Portability** | ✅ Multi-platform | ❌ macOS-only |

## Pricing Breakdown

### Doppler Developer Plan (Free for 3 users)

- **Cost**: Free for solo dev
- **Includes**:
  - Doppler CLI for local development
  - 5 config syncs (to external platforms)
  - 3-day activity logs
  - Service tokens (read-only)
  - Email alerts
  - API + webhooks access
  - Secrets referencing

- **When to upgrade**: If adding team members ($8/mo per additional user)

### fnox + Keychain

- **Cost**: $0 (built-in to macOS)
- **Setup**: Already installed in your project (`src/mde/domain/secrets.py`)
- **Trade-off**: No cloud sync, team sharing, or integrations

## Integration Ecosystem

### Doppler Supports

**Cloud Platforms:**
- AWS (Parameter Store, Secrets Manager)
- Azure (Key Vault, App Service)
- Google Cloud (GCP Secret Manager)

**CI/CD:**
- GitHub Actions, GitLab CI, CircleCI, Bitbucket Pipelines

**Deployment:**
- Kubernetes, Docker, Heroku, Vercel, Netlify, Render, Railway, Fly.io

**Other:**
- Terraform Cloud, Supabase, Laravel Forge, Cloudflare Pages

**fnox + Keychain:**
- None (Keychain is local-only; no platform integrations)

## Scenarios & Recommendations

### Scenario 1: Solo Dev, No Scaling Plans

**Recommendation**: Keep fnox + Keychain

**Why:**
- Zero cost
- No network dependency
- Native macOS experience
- Already working in your project

**Setup:**
```bash
# Your current approach
uv run mde-py cli ...  # uses fnox internally
```

---

### Scenario 2: Solo Dev, Want Cloud Backup & Future Scaling

**Recommendation**: Doppler (free tier) + fnox wrapper

**Why:**
- Doppler free tier is truly free
- Get team-ready RBAC if expanding
- 20+ integrations ready if you expand
- Encrypted fallback lets you work offline

**Setup:**
```bash
# Primary: Use Doppler for secrets
doppler run -- uv run your-command

# Optional: wrapper to sync to Keychain for offline use
# (requires custom scripting; not documented in Doppler)
```

---

### Scenario 3: Already Using Doppler at Company

**Recommendation**: Doppler personal workspace

**Why:**
- Consistency across work/personal projects
- Can share setup patterns with team
- Service tokens already familiar
- Integrations might be useful later

**Setup:**
```bash
# Create Doppler account (personal)
# Set up project + dev_personal config
doppler login
doppler setup
doppler run -- your-command
```

---

### Scenario 4: Hybrid: Doppler Primary + Keychain Cache

**Recommendation**: Doppler with custom fnox sync

**Why:**
- Doppler = source of truth (cloud backup)
- Keychain = offline fallback (native macOS)
- Best of both worlds

**Requires:**
- Custom wrapper: `doppler run` → fetch secrets → fnox push to Keychain
- Not documented by either tool
- Bidirectional sync logic (which system wins?)

---

## Implementation: Doppler + Keychain Hybrid

### Conceptual Wrapper (Pseudo-code)

```python
#!/usr/bin/env python
# wrapper: doppler_keychain_sync.py

import subprocess
import json
from pathlib import Path

def doppler_secrets_to_keychain():
    """Fetch Doppler secrets and cache in Keychain via fnox."""

    # 1. Download secrets from Doppler
    result = subprocess.run(
        ['doppler', 'secrets', 'download', '--no-file', '-z'],
        capture_output=True,
        text=True,
        check=True
    )

    secrets = json.loads(result.stdout)

    # 2. Push to Keychain via fnox
    for name, value in secrets.items():
        subprocess.run(
            ['fnox', 'set', name, value],
            check=True
        )

    print(f"Synced {len(secrets)} secrets to Keychain")

if __name__ == '__main__':
    doppler_secrets_to_keychain()
```

**To integrate with mise:**

```toml
# mise.toml
[tasks.sync-secrets]
description = "Download Doppler secrets + sync to Keychain"
run = "python doppler_keychain_sync.py"

[tasks.dev]
depends = ["sync-secrets"]
run = "doppler run -- your-dev-command"
```

---

## Migration Path: fnox → Doppler

If you later decide to switch to Doppler as primary:

### Step 1: Export fnox secrets

```bash
# fnox doesn't have native export; workaround:
# Manually create doppler.yaml with all secrets, or use API bulk import
```

### Step 2: Import to Doppler Dashboard

```bash
# Login and create project
doppler login
# Create project via dashboard
# Add secrets via dashboard UI or API
```

### Step 3: Switch CLI Usage

```bash
# Old
uv run mde-py secret get KEY_NAME

# New
doppler run -- your-command  # or $DOPPLER_TOKEN
```

---

## Known Gaps

1. **No bulk import documented** — Doppler API preview was truncated; API endpoints exist but not fully documented in fetched materials.

2. **No Keychain integration** — Doppler doesn't sync to native macOS Keychain. Would require custom wrapper (like the pseudo-code above).

3. **fnox export** — fnox doesn't have native export-to-Doppler; would need to manually add secrets via Doppler dashboard or script the API calls.

4. **mise integration** — Neither tool has native mise task integration. Requires wrapper scripts or manual `doppler setup` + `doppler.yaml` config.

---

## Next Steps

1. **For Solo Dev (current state)**: No action needed. fnox + Keychain is working fine.

2. **If Scaling to Team**: Migrate to Doppler free tier (3 users) → Set up GitHub Actions integration → Use Service Tokens for CI/CD.

3. **If Expanding Platforms**: Leverage Doppler's 20+ integrations (AWS, Azure, Kubernetes, etc.) as you add infrastructure.

4. **If Wanting Hybrid**: Design and test fnox↔Doppler sync wrapper (requires custom Python/shell script) — likely overkill for solo dev.

---

## References

- **Provenance Record**: `docs/research/trail/findings/finding-doppler-secrets-setup.yaml`
- **Source Catalog**: Updated `docs/research/source-catalog.md` with Doppler URLs
- **Doppler Docs**: https://docs.doppler.com/docs/install-cli
