# Skill Sync & Install Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure all tools on this Mac are declaratively managed by creating bidirectional skill symlinks between `.agents/skills/` and `.claude/skills/`, a sync validator, and a PreToolUse hook that blocks ad-hoc installs.

**Architecture:** Three new Python modules in `src/mde/`: a sync engine (`maintain/skill_sync.py`), a validator (`validate/skill_sync.py`), and a hook handler (`hooks/guard_install.py`). The sync engine creates symlinks from `.agents/skills/<name>` → `.claude/skills/<name>` (and vice versa). The validator checks all skills have bidirectional symlinks. The hook intercepts `Bash` tool calls matching install commands and returns a `"deny"` decision.

**Tech Stack:** Python 3.12+, Pydantic (existing `ValidationResult`), pathlib, JSON (hook I/O), argparse (CLI wiring)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/mde/maintain/skill_sync.py` | Sync engine: scan both dirs, create missing symlinks |
| Create | `src/mde/validate/skill_sync.py` | Validator: check symlink parity between dirs |
| Create | `src/mde/hooks/guard_install.py` | PreToolUse hook: block ad-hoc install commands |
| Create | `tests/test_skill_sync.py` | Tests for sync engine |
| Create | `tests/test_validate_skill_sync.py` | Tests for sync validator |
| Create | `tests/test_guard_install.py` | Tests for install guard hook |
| Modify | `src/mde/cli.py` | Add `skill sync` subcommand, `hooks guard-install` |
| ~~Modify~~ | ~~`src/mde/hooks/__init__.py`~~ | ~~Not needed — `cli.py` dispatches directly~~ |
| Modify | `src/mde/validate/__init__.py` | Wire `validate_skill_sync` into `validate_all` |
| Modify | `.claude/settings.json` | Add PreToolUse Bash hook |

---

### Task 1: Skill Sync Engine

**Files:**
- Create: `src/mde/maintain/skill_sync.py`
- Test: `tests/test_skill_sync.py`

- [ ] **Step 1: Write the failing test for sync discovery**

```python
# tests/test_skill_sync.py
"""Tests for skill sync engine."""

from __future__ import annotations

from pathlib import Path

from mde.maintain.skill_sync import discover_unsynced_skills


def test_discover_unsynced_agents_skill(tmp_path: Path) -> None:
    """Skill in .agents/skills/ without .claude/skills/ symlink is discovered."""
    agents_dir = tmp_path / ".agents" / "skills" / "mise-enforcement"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: mise-enforcement\n---\n")
    claude_dir = tmp_path / ".claude" / "skills"
    claude_dir.mkdir(parents=True)

    result = discover_unsynced_skills(root=tmp_path)
    assert len(result.agents_only) == 1
    assert result.agents_only[0].name == "mise-enforcement"
    assert len(result.claude_only) == 0
    assert len(result.synced) == 0


def test_discover_unsynced_claude_skill(tmp_path: Path) -> None:
    """Skill in .claude/skills/ without .agents/skills/ symlink is discovered."""
    claude_dir = tmp_path / ".claude" / "skills" / "agent-browser"
    claude_dir.mkdir(parents=True)
    (claude_dir / "SKILL.md").write_text("---\nname: agent-browser\n---\n")
    agents_dir = tmp_path / ".agents" / "skills"
    agents_dir.mkdir(parents=True)

    result = discover_unsynced_skills(root=tmp_path)
    assert len(result.claude_only) == 1
    assert result.claude_only[0].name == "agent-browser"
    assert len(result.agents_only) == 0


def test_synced_skill_detected(tmp_path: Path) -> None:
    """Skill with symlink in both dirs is marked synced."""
    agents_dir = tmp_path / ".agents" / "skills" / "kubectl"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: kubectl\n---\n")
    claude_link = tmp_path / ".claude" / "skills" / "kubectl"
    claude_link.parent.mkdir(parents=True, exist_ok=True)
    claude_link.symlink_to(agents_dir)

    result = discover_unsynced_skills(root=tmp_path)
    assert len(result.synced) == 1
    assert len(result.agents_only) == 0
    assert len(result.claude_only) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_skill_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mde.maintain.skill_sync'`

- [ ] **Step 3: Implement the sync engine**

```python
# src/mde/maintain/skill_sync.py
"""Bidirectional skill sync between .agents/skills/ and .claude/skills/."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

_AGENTS_SKILLS = Path(".agents") / "skills"
_CLAUDE_SKILLS = Path(".claude") / "skills"


class SkillEntry(BaseModel):
    """A discovered skill directory."""

    name: str
    path: Path
    source: str = Field(description="'agents' or 'claude'")


class SyncDiscovery(BaseModel):
    """Result of scanning both skill directories."""

    agents_only: list[SkillEntry] = Field(default_factory=list)
    claude_only: list[SkillEntry] = Field(default_factory=list)
    synced: list[SkillEntry] = Field(default_factory=list)


def _is_skill_dir(path: Path) -> bool:
    """Check if a directory contains a SKILL.md file."""
    return path.is_dir() and (path / "SKILL.md").exists()


def _list_skills(base: Path) -> dict[str, Path]:
    """List skill directories under a base path, resolving symlinks."""
    if not base.exists():
        return {}
    return {
        d.name: d
        for d in sorted(base.iterdir())
        if _is_skill_dir(d)
    }


def discover_unsynced_skills(root: Path | None = None) -> SyncDiscovery:
    """Scan .agents/skills/ and .claude/skills/ for sync gaps."""
    root = root or Path.cwd()
    agents_skills = _list_skills(root / _AGENTS_SKILLS)
    claude_skills = _list_skills(root / _CLAUDE_SKILLS)
    result = SyncDiscovery()

    all_names = sorted(set(agents_skills) | set(claude_skills))
    for name in all_names:
        in_agents = name in agents_skills
        in_claude = name in claude_skills
        if in_agents and in_claude:
            # Check if one is a symlink to the other
            agents_path = agents_skills[name]
            claude_path = claude_skills[name]
            if claude_path.is_symlink() or agents_path.is_symlink():
                result.synced.append(
                    SkillEntry(name=name, path=agents_path, source="both")
                )
            else:
                # Both exist as real dirs — treat agents as canonical
                result.synced.append(
                    SkillEntry(name=name, path=agents_path, source="both")
                )
        elif in_agents:
            result.agents_only.append(
                SkillEntry(name=name, path=agents_skills[name], source="agents")
            )
        else:
            result.claude_only.append(
                SkillEntry(name=name, path=claude_skills[name], source="claude")
            )
    return result


def sync_skills(root: Path | None = None, *, dry_run: bool = False) -> list[str]:
    """Create missing symlinks to sync both directories.

    Convention: .agents/skills/ is canonical (per Vercel skills CLI).
    - Skills only in .agents/skills/ get a symlink in .claude/skills/
    - Skills only in .claude/skills/ get a symlink in .agents/skills/

    Uses relative symlinks for portability across machines.

    Returns list of actions taken (or that would be taken in dry_run).
    """
    root = root or Path.cwd()
    discovery = discover_unsynced_skills(root)
    actions: list[str] = []

    agents_base = root / _AGENTS_SKILLS
    claude_base = root / _CLAUDE_SKILLS

    for entry in discovery.agents_only:
        target = agents_base / entry.name
        link = claude_base / entry.name
        rel_target = os.path.relpath(target, link.parent)
        action = f"symlink {link} -> {rel_target}"
        actions.append(action)
        if not dry_run:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(rel_target)

    for entry in discovery.claude_only:
        target = claude_base / entry.name
        link = agents_base / entry.name
        rel_target = os.path.relpath(target, link.parent)
        action = f"symlink {link} -> {rel_target}"
        actions.append(action)
        if not dry_run:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(rel_target)

    return actions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_skill_sync.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write test for the sync action itself**

```python
# Append to tests/test_skill_sync.py

import os

from mde.maintain.skill_sync import sync_skills


def test_sync_creates_symlink_for_agents_only(tmp_path: Path) -> None:
    """sync_skills creates .claude/skills/<name> symlink for agents-only skill."""
    agents_dir = tmp_path / ".agents" / "skills" / "mise-enforcement"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: mise-enforcement\n---\n")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    actions = sync_skills(root=tmp_path)
    assert len(actions) == 1
    assert "symlink" in actions[0]
    link = tmp_path / ".claude" / "skills" / "mise-enforcement"
    assert link.is_symlink()
    assert link.is_symlink()
    assert link.resolve() == agents_dir.resolve()
    # Verify relative symlink (portable)
    assert not os.path.isabs(os.readlink(str(link)))


def test_sync_creates_symlink_for_claude_only(tmp_path: Path) -> None:
    """sync_skills creates .agents/skills/<name> symlink for claude-only skill."""
    claude_dir = tmp_path / ".claude" / "skills" / "agent-browser"
    claude_dir.mkdir(parents=True)
    (claude_dir / "SKILL.md").write_text("---\nname: agent-browser\n---\n")
    (tmp_path / ".agents" / "skills").mkdir(parents=True)

    actions = sync_skills(root=tmp_path)
    assert len(actions) == 1
    link = tmp_path / ".agents" / "skills" / "agent-browser"
    assert link.is_symlink()
    assert link.resolve() == claude_dir.resolve()
    assert not os.path.isabs(os.readlink(str(link)))


def test_sync_dry_run_creates_no_symlinks(tmp_path: Path) -> None:
    """dry_run=True reports actions but creates no symlinks."""
    agents_dir = tmp_path / ".agents" / "skills" / "kubectl"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: kubectl\n---\n")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    actions = sync_skills(root=tmp_path, dry_run=True)
    assert len(actions) == 1
    link = tmp_path / ".claude" / "skills" / "kubectl"
    assert not link.exists()
```

- [ ] **Step 6: Run all sync tests**

Run: `uv run pytest tests/test_skill_sync.py -v`
Expected: PASS (6 tests)

- [ ] **Step 7: Commit**

```bash
git add src/mde/maintain/skill_sync.py tests/test_skill_sync.py
git commit -m "feat(skill-sync): add bidirectional skill sync engine

Scans .agents/skills/ and .claude/skills/ for sync gaps and creates
missing symlinks. Convention: .agents/skills/ is canonical per Vercel
skills CLI; .claude/skills/ gets symlinks for Claude Code discovery."
```

---

### Task 2: Skill Sync Validator

**Files:**
- Create: `src/mde/validate/skill_sync.py`
- Create: `tests/test_validate_skill_sync.py`
- Modify: `src/mde/validate/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validate_skill_sync.py
"""Tests for skill sync validator."""

from __future__ import annotations

from pathlib import Path

from mde.validate.skill_sync import validate_skill_sync


def test_unsynced_agents_skill_is_error(tmp_path: Path) -> None:
    """Skill in .agents/skills/ without .claude/skills/ symlink is an error."""
    agents_dir = tmp_path / ".agents" / "skills" / "mise-enforcement"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: mise-enforcement\n---\n")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    result = validate_skill_sync(root=tmp_path)
    assert not result.passed
    assert result.error_count == 1
    assert "mise-enforcement" in result.findings[0].message


def test_synced_skills_pass(tmp_path: Path) -> None:
    """Skills with symlinks in both dirs pass validation."""
    agents_dir = tmp_path / ".agents" / "skills" / "kubectl"
    agents_dir.mkdir(parents=True)
    (agents_dir / "SKILL.md").write_text("---\nname: kubectl\n---\n")
    claude_link = tmp_path / ".claude" / "skills" / "kubectl"
    claude_link.parent.mkdir(parents=True, exist_ok=True)
    claude_link.symlink_to(agents_dir)

    result = validate_skill_sync(root=tmp_path)
    assert result.passed
    assert result.error_count == 0


def test_no_skill_dirs_passes(tmp_path: Path) -> None:
    """Missing skill directories is not an error."""
    result = validate_skill_sync(root=tmp_path)
    assert result.passed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_validate_skill_sync.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the validator**

```python
# src/mde/validate/skill_sync.py
"""Validate bidirectional symlink parity between .agents/skills/ and .claude/skills/."""

from __future__ import annotations

from pathlib import Path

from mde.maintain.skill_sync import discover_unsynced_skills
from mde.models.result import ValidationResult


def validate_skill_sync(root: Path | None = None) -> ValidationResult:
    """Check that every skill in one dir has a symlink in the other.

    Errors on unsynced skills. Run ``uv run mde-py skill sync`` to fix.
    """
    result = ValidationResult()
    root = root or Path.cwd()

    discovery = discover_unsynced_skills(root)

    checked = (
        len(discovery.agents_only)
        + len(discovery.claude_only)
        + len(discovery.synced)
    )
    result.files_checked += checked

    for entry in discovery.agents_only:
        result.add_error(
            str(entry.path),
            f"Skill '{entry.name}' in .agents/skills/ has no .claude/skills/ symlink. "
            "Run: uv run mde-py skill sync",
            rule="skill-sync.missing-claude",
            fixable=True,
        )

    for entry in discovery.claude_only:
        result.add_error(
            str(entry.path),
            f"Skill '{entry.name}' in .claude/skills/ has no .agents/skills/ symlink. "
            "Run: uv run mde-py skill sync",
            rule="skill-sync.missing-agents",
            fixable=True,
        )

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_validate_skill_sync.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Wire validator into validate_all**

In `src/mde/validate/__init__.py`:
- Add import: `from mde.validate.skill_sync import validate_skill_sync`
- Add `result.merge(validate_skill_sync())` to the full validation block, after the `validate_skill_frontmatter()` call (~line 67)
- No new CLI flag needed — sync validation always runs as part of `--all` / full validation

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest tests/test_validate_skill_sync.py tests/test_skill_sync.py -v`
Expected: PASS (all 9 tests)

- [ ] **Step 7: Commit**

```bash
git add src/mde/validate/skill_sync.py tests/test_validate_skill_sync.py src/mde/validate/__init__.py
git commit -m "feat(validate): add skill sync validator

Checks bidirectional symlink parity between .agents/skills/ and
.claude/skills/. Reports fixable errors with 'uv run mde-py skill sync'."
```

---

### Task 3: Install Guard Hook

**Files:**
- Create: `src/mde/hooks/guard_install.py`
- Create: `tests/test_guard_install.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_guard_install.py
"""Tests for install guard PreToolUse hook."""

from __future__ import annotations

import json

from mde.hooks.guard_install import check_install_command


def test_blocks_npm_install_global() -> None:
    """npm install -g should be blocked."""
    result = check_install_command("npm install -g typescript")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_brew_install() -> None:
    """brew install should be blocked."""
    result = check_install_command("brew install jq")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_pip_install() -> None:
    """pip install should be blocked."""
    result = check_install_command("pip install requests")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_cargo_install() -> None:
    """cargo install should be blocked."""
    result = check_install_command("cargo install ripgrep")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_go_install() -> None:
    """go install should be blocked."""
    result = check_install_command("go install golang.org/x/tools/gopls@latest")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_bun_add_global() -> None:
    """bun add -g should be blocked."""
    result = check_install_command("bun add -g typescript")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_uv_tool_install() -> None:
    """uv tool install should be blocked."""
    result = check_install_command("uv tool install ruff")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_pipx_install() -> None:
    """pipx install should be blocked."""
    result = check_install_command("pipx install black")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_yarn_global_add() -> None:
    """yarn global add should be blocked."""
    result = check_install_command("yarn global add typescript")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_blocks_npm_install_long_global() -> None:
    """npm install --global should be blocked."""
    result = check_install_command("npm install --global typescript")
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_allows_npm_install_local() -> None:
    """npm install (local, no -g) should be allowed."""
    result = check_install_command("npm install typescript")
    assert result is None


def test_allows_pip_install_in_venv() -> None:
    """uv pip install (project dep) should be allowed."""
    result = check_install_command("uv pip install requests")
    assert result is None


def test_allows_mise_install() -> None:
    """mise install should be allowed."""
    result = check_install_command("mise install")
    assert result is None


def test_allows_unrelated_command() -> None:
    """Regular commands should be allowed."""
    result = check_install_command("git status")
    assert result is None


def test_allows_brew_bundle() -> None:
    """brew bundle (declarative) should be allowed."""
    result = check_install_command("brew bundle --file=Brewfile")
    assert result is None


def test_allows_npx_skills_add() -> None:
    """npx skills add (skill installer) should be allowed."""
    result = check_install_command("npx skills add teng-lin/agent-fetch")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_guard_install.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the guard**

```python
# src/mde/hooks/guard_install.py
"""PreToolUse hook: block ad-hoc global installs.

Reads Bash tool_input from stdin JSON. Returns deny decision for
commands that install tools outside the declarative mise/Brewfile chain.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

# Patterns that indicate a GLOBAL install (should be in mise config)
_BLOCK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bnpm\s+install\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bnpm\s+i\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bbun\s+add\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\bbun\s+install\s+(?:.*\s)?(-g|--global)\b"),
    re.compile(r"\byarn\s+global\s+add\b"),
    re.compile(r"\bpip\s+install\b(?!.*(?:-e\s*\.|\.))"),  # bare pip install
    re.compile(r"\bpip3\s+install\b"),
    re.compile(r"\bpipx\s+install\b"),
    re.compile(r"\buv\s+tool\s+install\b"),
    re.compile(r"\bcargo\s+install\b"),
    re.compile(r"\bgo\s+install\b"),
    re.compile(r"\bbrew\s+install\b"),
]

# Patterns that are explicitly ALLOWED (declarative or local)
_ALLOW_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bmise\s+install\b"),
    re.compile(r"\bbrew\s+bundle\b"),
    re.compile(r"\bnpx\s+skills\b"),
    re.compile(r"\buv\s+pip\s+install\b"),  # project-local via uv
    re.compile(r"\buv\s+sync\b"),
    re.compile(r"\buv\s+add\b"),
]

_DENY_REASON = (
    "BLOCKED: Direct global install detected. "
    "This project uses mise as the tool authority. "
    "Add the tool to .chezmoisource/dot_config/mise/config.toml.tmpl instead. "
    "See .agents/skills/mise-tool-management/SKILL.md for backend selection."
)


def check_install_command(command: str) -> dict[str, Any] | None:
    """Check if a command is a blocked install.

    Returns deny-decision dict if blocked, None if allowed.
    """
    # Allow-list takes precedence
    for pattern in _ALLOW_PATTERNS:
        if pattern.search(command):
            return None

    for pattern in _BLOCK_PATTERNS:
        if pattern.search(command):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _DENY_REASON,
                }
            }
    return None


def guard_install() -> int:
    """Entry point for PreToolUse Bash hook. Reads JSON from stdin."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Can't parse — don't block

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return 0

    result = check_install_command(command)
    if result is not None:
        json.dump(result, sys.stdout)
        return 0

    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_guard_install.py -v`
Expected: PASS (16 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mde/hooks/guard_install.py tests/test_guard_install.py
git commit -m "feat(hooks): add install guard PreToolUse hook

Blocks npm -g, brew install, pip install, cargo install, go install,
pipx install, uv tool install, and bun -g. Allows mise install,
brew bundle, npx skills, and uv pip install (local)."
```

---

### Task 4: CLI Wiring

**Files:**
- Modify: `src/mde/cli.py`

- [ ] **Step 1: Add `skill sync` subcommand to cli.py**

In `_build_parser()`, after the `install` block (~line 83), add:

```python
    # skill
    skill_p = sub.add_parser("skill", help="Skill management")
    skill_sub = skill_p.add_subparsers(dest="skill_action")
    sync_p = skill_sub.add_parser("sync", help="Sync .agents/skills/ <-> .claude/skills/")
    sync_p.add_argument("--dry-run", action="store_true", help="Show what would be done")
```

- [ ] **Step 2: Add `guard-install` to hooks subparser**

In `_build_parser()`, in the hooks_sub section (~line 90), add:

```python
    hooks_sub.add_parser("guard-install", help="PreToolUse install guard")
```

- [ ] **Step 3: Add `_cmd_skill` handler**

```python
def _cmd_skill(args: argparse.Namespace) -> int:
    action = args.skill_action
    if action == "sync":
        from mde.maintain.skill_sync import sync_skills

        actions = sync_skills(dry_run=args.dry_run)
        if not actions:
            print("All skills are synced.", file=sys.stderr)
            return 0
        prefix = "[dry-run] " if args.dry_run else ""
        for a in actions:
            print(f"{prefix}{a}", file=sys.stderr)
        return 0
    print(f"Unknown skill action: {action}", file=sys.stderr)
    return 1
```

- [ ] **Step 4: Add guard-install dispatch to `_cmd_hooks`**

In `_cmd_hooks()`, add before the unknown-action print:

```python
    if action == "guard-install":
        from mde.hooks.guard_install import guard_install

        return guard_install()
```

- [ ] **Step 5: Add "skill" to `_DISPATCH_TABLE`**

```python
_DISPATCH_TABLE: dict[str, Callable[[argparse.Namespace], int]] = {
    ...
    "skill": _cmd_skill,
}
```

- [ ] **Step 6: Verify CLI works**

Run: `uv run mde-py skill sync --dry-run`
Expected: Lists unsynced skills with `[dry-run]` prefix

Run: `uv run mde-py hooks guard-install <<< '{"tool_input":{"command":"npm install -g foo"}}'`
Expected: JSON with `"permissionDecision": "deny"`

- [ ] **Step 7: Commit**

```bash
git add src/mde/cli.py
git commit -m "feat(cli): wire skill sync subcommand and guard-install hook

Adds 'mde-py skill sync [--dry-run]' for bidirectional skill symlinks.
Adds 'mde-py hooks guard-install' for PreToolUse Bash interception."
```

---

### Task 5: Wire Settings & Run Sync

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Add PreToolUse hook to settings.json**

Add to the `"hooks"` object in `.claude/settings.json`:

```json
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run mde-py hooks guard-install"
          }
        ]
      }
    ]
```

- [ ] **Step 2: Run the initial sync**

Run: `uv run mde-py skill sync`
Expected: Creates ~40 symlinks in `.claude/skills/` for `.agents/skills/` entries and ~20 symlinks in `.agents/skills/` for `.claude/skills/` entries.

- [ ] **Step 3: Verify validation passes**

Run: `uv run mde-py validate --all`
Expected: No skill-sync errors

- [ ] **Step 4: Verify guard hook works end-to-end**

Run: `echo '{"tool_input":{"command":"brew install jq"}}' | uv run mde-py hooks guard-install`
Expected: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}`

Run: `echo '{"tool_input":{"command":"mise install"}}' | uv run mde-py hooks guard-install`
Expected: No output (exit 0, allowed)

- [ ] **Step 5: Run full linting and type checks**

Run: `uv run ruff check src/mde/maintain/skill_sync.py src/mde/validate/skill_sync.py src/mde/hooks/guard_install.py`
Expected: No errors

Run: `uv run ty check src/mde/`
Expected: No new errors

- [ ] **Step 6: Commit**

```bash
git add .claude/settings.json
git commit -m "feat(hooks): enable PreToolUse install guard in settings.json

Blocks ad-hoc global installs (npm -g, brew install, pip install, etc.)
and directs agents to use mise declarative config instead."
```

---

### Task 6: Install the Three New Skills

**Files:**
- Modify: `.chezmoisource/dot_config/mise/config.toml.tmpl` (add tool declarations)
- Modify: `.chezmoisource/Brewfile.tmpl` (add Obsidian cask)

- [ ] **Step 1: Install skills via npx skills add**

```bash
npx skills add https://github.com/sean-esk/second-brain-gtd --skill second-brain
npx skills add teng-lin/notebooklm-py
npx skills add teng-lin/agent-fetch
```

- [ ] **Step 2: Run skill sync to create bidirectional symlinks**

Run: `uv run mde-py skill sync`
Expected: Creates symlinks for the 3 new skills

- [ ] **Step 3: Add tool dependencies to mise config template**

In `.chezmoisource/dot_config/mise/config.toml.tmpl` under `[tools]`, add:

```toml
"npm:@teng-lin/agent-fetch" = "latest"
"pipx:notebooklm-py" = "latest"
```

- [ ] **Step 4: Add Obsidian to Brewfile template**

In `.chezmoisource/Brewfile.tmpl`, under the casks section, add:

```ruby
cask "obsidian"
```

- [ ] **Step 5: Apply and install**

```bash
chezmoi apply
mise install --yes
brew bundle --file="$(chezmoi source-path)/Brewfile.tmpl"
```

- [ ] **Step 6: Verify tools are available**

```bash
which agent-fetch   # Should resolve to mise shim
which notebooklm    # Should resolve to mise shim
which obsidian      # Should be in /Applications/
```

- [ ] **Step 7: Validate everything**

Run: `uv run mde-py validate --all`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add .chezmoisource/dot_config/mise/config.toml.tmpl .chezmoisource/Brewfile.tmpl
git commit -m "feat(tools): add agent-fetch, notebooklm-py, obsidian

agent-fetch: npm CLI for full-content web fetching with TLS impersonation
notebooklm-py: Python CLI for Google NotebookLM API
obsidian: GUI app for second-brain-gtd skill (Homebrew cask)"
```
