# Doppler Secrets Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use ultrapowers:subagent-driven-development (recommended) or ultrapowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make Doppler the cloud source of truth for all 40 secrets, with fnox/Keychain as local offline cache synced via `uv run mde-py secrets sync`.

**Architecture:** Doppler (project: dotfiles, config: dev) stores canonical secrets. A new `src/mde/secrets/` module provides CLI commands to export fnox->Doppler (one-time migration), sync Doppler->fnox (ongoing), validate parity, and list status. Existing mise `_.fnox-env` chain remains unchanged as the runtime delivery mechanism.

**Tech Stack:** Python 3.14, Doppler CLI, fnox CLI, mise, chezmoi, srclight, mcp2cli

**Skills:** @doppler-secrets, @mise-toolkit:mise-tool-management, @chezmoi-toolkit:chezmoi-config, @ultrapowers-dev:python-best-practices, @ultrapowers-dev:testing-tdd, @srclight:setup, @mcp2cli:convert

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/mde/secrets/__init__.py` | Modify: add dispatch for new actions (sync, export, validate, list) |
| `src/mde/secrets/doppler.py` | Create: Doppler CLI wrapper (list, get, set, bulk set) |
| `src/mde/secrets/sync.py` | Create: Doppler->fnox/Keychain sync logic |
| `src/mde/secrets/export_to_doppler.py` | Create: one-time fnox->Doppler migration |
| `src/mde/secrets/validate.py` | Create: parity check between Doppler and fnox |
| `src/mde/cli.py:186-187` | Modify: extend secrets action choices |
| `.mise.toml` | Modify: add doppler, srclight to [tools] |
| `CLAUDE.md` | Modify: update Secrets section |
| `.claude/rules/secrets-management.md` | Modify: rewrite for Doppler-first flow |
| `.claude/rules/research-tools.md` | Create: enforce srclight, mcp2cli, context7-cli |
| `tests/mde/test_secrets_doppler.py` | Create: tests for all new secrets commands |

---

## Task 1: Install Doppler CLI via mise

**Files:**
- Modify: `.mise.toml` (add doppler to [tools])

- [x] **Step 1: Check mise registry for doppler** — DONE: github:DopplerHQ/cli
- [x] **Step 2: Add doppler to .mise.toml [tools]** — DONE: doppler = "latest"
- [x] **Step 3: Install and verify** — DONE: v3.75.3
- [x] **Step 4: Authenticate** — DONE: logged in as Raymond
- [x] **Step 5: Create project and config** — DONE: dotfiles with dev/stg/prd configs
- [x] **Step 6: Commit** — DONE: e5b178e, pushed to main

---

## Task 2: Build Doppler CLI wrapper module

**Files:**
- Create: `src/mde/secrets/doppler.py`
- Test: `tests/mde/test_secrets_doppler.py`

- [x] **Step 1: Write failing tests for doppler wrapper**

```python
# tests/mde/test_secrets_doppler.py
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from mde.secrets.doppler import (
    doppler_list_secrets,
    doppler_get_secret,
    doppler_set_secrets,
    is_doppler_available,
)


def test_is_doppler_available_when_installed():
    with patch("shutil.which", return_value="/usr/local/bin/doppler"):
        assert is_doppler_available() is True


def test_is_doppler_available_when_not_installed():
    with patch("shutil.which", return_value=None):
        assert is_doppler_available() is False


def test_doppler_list_secrets_parses_json():
    mock_output = '{"API_KEY": "secret123", "DB_PASS": "pass456"}'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
        result = doppler_list_secrets(project="dotfiles", config="dev")
    assert result == {"API_KEY": "secret123", "DB_PASS": "pass456"}


def test_doppler_get_secret_returns_value():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="secret123\n")
        result = doppler_get_secret("API_KEY", project="dotfiles", config="dev")
    assert result == "secret123"


def test_doppler_set_secrets_calls_cli():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        doppler_set_secrets(
            {"KEY1": "val1", "KEY2": "val2"},
            project="dotfiles",
            config="dev",
        )
    args = mock_run.call_args[0][0]
    assert "doppler" in args
    assert "secrets" in args
    assert "set" in args
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_secrets_doppler.py -v`
Expected: FAIL with ImportError (module not found).

- [x] **Step 3: Implement doppler.py**

```python
# src/mde/secrets/doppler.py
"""Doppler CLI wrapper for secrets management."""

from __future__ import annotations

import json
import shutil
import subprocess

from mde.log import logger

_PROJECT = "dotfiles"
_CONFIG = "dev"


def is_doppler_available() -> bool:
    return shutil.which("doppler") is not None


def doppler_list_secrets(
    *, project: str = _PROJECT, config: str = _CONFIG
) -> dict[str, str]:
    result = subprocess.run(
        [
            "doppler", "secrets", "download",
            "--project", project,
            "--config", config,
            "--no-file", "--format", "json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("doppler_list_failed")
        return {}
    return json.loads(result.stdout)


def doppler_get_secret(
    key: str, *, project: str = _PROJECT, config: str = _CONFIG
) -> str | None:
    result = subprocess.run(
        [
            "doppler", "secrets", "get", key,
            "--project", project,
            "--config", config,
            "--plain",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def doppler_set_secrets(
    secrets: dict[str, str],
    *,
    project: str = _PROJECT,
    config: str = _CONFIG,
) -> int:
    if not secrets:
        return 0
    pairs = [f"{k}={v}" for k, v in secrets.items()]
    result = subprocess.run(
        [
            "doppler", "secrets", "set",
            *pairs,
            "--project", project,
            "--config", config,
            "--silent",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        logger.bind(stderr=result.stderr).error("doppler_set_failed")
    return result.returncode
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/mde/test_secrets_doppler.py -v`
Expected: all PASS.

- [x] **Step 5: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed.

- [x] **Step 6: Commit**

```bash
git add src/mde/secrets/doppler.py tests/mde/test_secrets_doppler.py
git commit -m "feat: add Doppler CLI wrapper module with tests"
git push origin main
```

---

## Task 3: Build fnox->Doppler export (one-time migration)

**Files:**
- Create: `src/mde/secrets/export_to_doppler.py`
- Modify: `src/mde/secrets/__init__.py`
- Test: `tests/mde/test_secrets_doppler.py` (extend)

- [x] **Step 1: Write failing test for export function**

```python
def test_export_fnox_to_doppler_calls_doppler_set():
    mock_fnox_output = (
        " OPENAI_API_KEY   provider (keychain)  OPENAI_API_KEY\n"
        " GEMINI_API_KEY   provider (keychain)  GEMINI_API_KEY\n"
    )
    with (
        patch("subprocess.run") as mock_run,
        patch("mde.secrets.export_to_doppler.doppler_set_secrets") as mock_set,
    ):
        # fnox list
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=mock_fnox_output),  # fnox list
            MagicMock(returncode=0, stdout="sk-abc123\n"),      # fnox get OPENAI
            MagicMock(returncode=0, stdout="key-xyz789\n"),     # fnox get GEMINI
        ]
        mock_set.return_value = 0
        from mde.secrets.export_to_doppler import export_fnox_to_doppler
        result = export_fnox_to_doppler()
    assert result == 0
    mock_set.assert_called_once()
```

- [x] **Step 2: Run test, verify fail**

- [x] **Step 3: Implement export_to_doppler.py**

Parse `fnox list` output for `provider (keychain)` entries, `fnox get` each value, bulk `doppler secrets set`.

- [x] **Step 4: Wire into CLI dispatch**

Update `src/mde/secrets/__init__.py` dispatch_secrets to handle `"export"` action.
Update `src/mde/cli.py:187` choices to include `"export"`.

- [x] **Step 5: Run tests, verify pass**
- [x] **Step 6: Run quality gate**
- [x] **Step 7: Commit**

```bash
git add src/mde/secrets/export_to_doppler.py src/mde/secrets/__init__.py src/mde/cli.py tests/mde/test_secrets_doppler.py
git commit -m "feat: add fnox-to-Doppler export command"
git push origin main
```

---

## Task 4: Build Doppler->fnox sync command

**Files:**
- Create: `src/mde/secrets/sync.py`
- Test: `tests/mde/test_secrets_doppler.py` (extend)

- [x] **Step 1: Write failing test**

Test that sync downloads from Doppler and calls `fnox set KEY --provider keychain --global` for each secret.

- [x] **Step 2: Run test, verify fail**
- [x] **Step 3: Implement sync.py**

`doppler_list_secrets()` -> for each key, `fnox set KEY VALUE --provider keychain --global`.

- [x] **Step 4: Wire into CLI dispatch** (add `"sync"` action)
- [x] **Step 5: Run tests, verify pass**
- [x] **Step 6: Run quality gate**
- [x] **Step 7: Commit**

---

## Task 5: Build validate (parity check) command

**Files:**
- Create: `src/mde/secrets/validate.py`
- Test: `tests/mde/test_secrets_doppler.py` (extend)

- [x] **Step 1: Write failing test**

Test that validate compares Doppler keys vs fnox keys and reports mismatches.

- [x] **Step 2-5: Implement, wire CLI, test, quality gate**
- [x] **Step 6: Commit**

---

## Task 6: Run the one-time migration

**Prerequisite:** Doppler project `dotfiles` exists and authenticated.

- [x] **Step 1: Export all fnox secrets to Doppler**

Run: `uv run mde-py secrets export`

- [x] **Step 2: Validate parity**

Run: `uv run mde-py secrets validate`
Expected: all 40 secrets match.

- [x] **Step 3: Verify in Doppler dashboard**

Run: `doppler secrets ls --project dotfiles --config dev | wc -l`
Expected: 40 secrets listed.

---

## Task 7: Install srclight and index repo

**Files:**
- Modify: `.mise.toml` (add srclight)
- Modify: `.gitignore` (add .srclight/)

- [x] **Step 1: Install srclight via pipx in mise**

Add to `.mise.toml`: `"pipx:srclight" = "latest"` then `mise install`.

- [x] **Step 2: Index the repo**

Run: `srclight index`
Verify: `.srclight/` directory created.

- [x] **Step 3: Add .srclight/ to .gitignore**
- [x] **Step 4: Test search**

Run: `srclight search "secrets"` — verify results.

- [x] **Step 5: Commit**

```bash
git add .mise.toml mise.lock .gitignore
git commit -m "feat: add srclight code indexing"
git push origin main
```

---

## Task 8: Convert exa MCP to CLI via mcp2cli

- [x] **Step 1: Analyze feasibility**

Run: `/analyze-mcp` on exa MCP server (Tier 1 SaaS API wrapper).

- [x] **Step 2: Convert**

Run: `/convert` for exa MCP server.

- [x] **Step 3: Test the CLI**

Run: `mcp2cli @exa web_search_exa --query "doppler mise integration"`
Expected: search results returned.

- [x] **Step 4: Commit any generated files**

---

## Task 9: Integrate Doppler with chezmoi

**Files:**
- Modify: chezmoi source for `~/.config/chezmoi/chezmoi.toml`

- [x] **Step 1: Add [doppler] defaults to chezmoi.toml**

```toml
[doppler]
project = "dotfiles"
config = "dev"
```

Via: `chezmoi edit ~/.config/chezmoi/chezmoi.toml`

- [x] **Step 2: Test template function**

Create a test template or verify: `chezmoi execute-template '{{ doppler "EXA_API_KEY" }}'`
Expected: returns the API key value.

- [x] **Step 3: Commit chezmoi source changes**

---

## Task 10: Update documentation and enforcement

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/rules/secrets-management.md`
- Create: `.claude/rules/research-tools.md`

- [x] **Step 1: Update CLAUDE.md Secrets section**

Change from fnox-only to Doppler-first:
```
## Secrets

All secrets: **Doppler (source of truth) -> sync -> fnox (Keychain cache) -> mise (env) -> tools**.
New secrets: `doppler secrets set KEY --project dotfiles --config dev`, then `uv run mde-py secrets sync`.
Validate: `uv run mde-py secrets validate`. See `.claude/rules/secrets-management.md` for full guide.
```

- [x] **Step 2: Rewrite .claude/rules/secrets-management.md**

Update architecture diagram, set/get/validate commands, rules to reference Doppler as primary.

- [x] **Step 3: Create .claude/rules/research-tools.md**

```markdown
---
description: Enforce research tool usage
globs: ["*.md", "docs/**"]
---

# Research Tools Policy

- Use srclight for code indexing and search (not grep/glob for complex queries)
- Use mcp2cli @exa for web search (not raw MCP tool schemas)
- Use context7-cli or /context7-plugin:docs for library documentation
- Use agent-fetch for full URL content (not WebFetch)
```

- [x] **Step 4: Run quality gate**

Run: `uv run mde-py quality`
Expected: 6/6 passed.

- [x] **Step 5: Commit**

```bash
git add CLAUDE.md .claude/rules/secrets-management.md .claude/rules/research-tools.md
git commit -m "docs: update secrets and research tool policies for Doppler-first flow"
git push origin main
```

---

## Verification Checklist

- [ ] `doppler secrets ls --project dotfiles --config dev` shows all 40 secrets
- [ ] `uv run mde-py secrets validate` shows Doppler vs fnox parity
- [ ] `uv run mde-py secrets sync` pulls Doppler -> fnox/Keychain successfully
- [ ] `mise exec -- bash -c 'echo $EXA_API_KEY'` resolves after sync
- [ ] `chezmoi execute-template '{{ doppler "EXA_API_KEY" }}'` returns value
- [ ] `srclight search "secrets"` returns results from indexed repo
- [ ] `uv run mde-py quality` passes 6/6
