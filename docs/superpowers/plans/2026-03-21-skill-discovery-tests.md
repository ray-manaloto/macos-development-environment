# Skill Discovery Tests & Schema-Driven Codegen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive tests for the skill discovery modules, convert hand-coded Pydantic models to schema-driven codegen, register a mise task, and update the SKILL.md to reference the CLI.

**Architecture:** Test-first (TDD red-green-refactor). All external calls (subprocess, httpx) are mocked. Schema-driven codegen uses `datamodel-codegen` from JSON Schema → Pydantic models, following the established `statusline/models.py` pattern. Generated files get per-file-ignores in pyproject.toml.

**Tech Stack:** pytest, unittest.mock, datamodel-codegen, ruff, ty, pyright

**Worktree:** `.worktrees/pr8-skill-discovery-tests` on branch `feat/skill-discovery-tests`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `tests/mde/research/test_skill_discover.py` | Tests for `skill_discover.py` (≥10 tests) |
| Create | `tests/mde/research/test_skillsmp_client.py` | Tests for `skillsmp_client.py` (≥5 tests) |
| Create | `tests/mde/research/test_skillsmp_models.py` | Tests for `skillsmp_models.py` (≥3 tests) |
| Create | `docs/schemas/skillsmp-search.schema.json` | JSON Schema for SkillsMP search response |
| Create | `docs/schemas/skillsmp-ai-search.schema.json` | JSON Schema for SkillsMP AI search response |
| Create | `docs/schemas/skillsmp-error.schema.json` | JSON Schema for SkillsMP error response |
| Regenerate | `src/mde/research/clients/skillsmp_models.py` | Generated from schemas via datamodel-codegen |
| Modify | `pyproject.toml` | Add per-file-ignores for generated models |
| Modify | `.mise.toml` | Add `mde:research:skill-discover` task |
| Modify | `.agents/skills/skill-discovery/SKILL.md` | Reference `uv run mde-py research skill-discover` |

---

## Task 1: Create JSON Schemas for SkillsMP Models

The existing `skillsmp_models.py` is hand-coded. Per project policy, Pydantic models must be generated from JSON Schema via `datamodel-codegen`. We create the schemas first, then regenerate.

**Files:**
- Create: `docs/schemas/skillsmp-search.schema.json`
- Create: `docs/schemas/skillsmp-ai-search.schema.json`
- Create: `docs/schemas/skillsmp-error.schema.json`

**Context for implementer:**
- The existing models are in `src/mde/research/clients/skillsmp_models.py` (92 lines)
- Models: `Skill`, `SkillSearchData`, `SkillSearchResponse`, `AISearchResult`, `AISearchData`, `AISearchResponse`, `ErrorDetail`, `ErrorResponse`
- `Skill` uses `Field(alias=...)` for camelCase API fields: `githubUrl`, `skillUrl`, `updatedAt`
- `Skill` has `model_config = {"populate_by_name": True}` for both snake_case and camelCase access
- Use JSON Schema draft 2020-12

- [ ] **Step 1: Create `docs/schemas/skillsmp-search.schema.json`**

This schema covers the keyword search endpoint response. It must define:
- `SkillSearchResponse` as the root with `success: bool` and `data: SkillSearchData | null`
- `SkillSearchData` with `skills: Skill[]`, `total: int`, `page: int`, `limit: int`
- `Skill` with fields: `id`, `name`, `author`, `description`, `githubUrl`, `skillUrl`, `stars`, `updatedAt` — all using camelCase names as they appear in the API

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "skillsmp-search.schema.json",
  "title": "SkillSearchResponse",
  "description": "Response from GET /api/v1/skills/search",
  "type": "object",
  "required": ["success"],
  "properties": {
    "success": { "type": "boolean" },
    "data": {
      "oneOf": [
        { "$ref": "#/$defs/SkillSearchData" },
        { "type": "null" }
      ]
    }
  },
  "$defs": {
    "Skill": {
      "type": "object",
      "required": ["id", "name", "author"],
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "author": { "type": "string" },
        "description": { "type": "string", "default": "" },
        "githubUrl": { "type": "string", "default": "" },
        "skillUrl": { "type": "string", "default": "" },
        "stars": { "type": "integer", "default": 0 },
        "updatedAt": { "type": "string", "default": "" }
      }
    },
    "SkillSearchData": {
      "type": "object",
      "properties": {
        "skills": {
          "type": "array",
          "items": { "$ref": "#/$defs/Skill" },
          "default": []
        },
        "total": { "type": "integer", "default": 0 },
        "page": { "type": "integer", "default": 1 },
        "limit": { "type": "integer", "default": 20 }
      }
    }
  }
}
```

- [ ] **Step 2: Create `docs/schemas/skillsmp-ai-search.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "skillsmp-ai-search.schema.json",
  "title": "AISearchResponse",
  "description": "Response from GET /api/v1/skills/ai-search",
  "type": "object",
  "required": ["success"],
  "properties": {
    "success": { "type": "boolean" },
    "data": {
      "oneOf": [
        { "$ref": "#/$defs/AISearchData" },
        { "type": "null" }
      ]
    }
  },
  "$defs": {
    "AISearchResult": {
      "type": "object",
      "properties": {
        "file_id": { "type": "string", "default": "" },
        "filename": { "type": "string", "default": "" },
        "score": { "type": "number", "default": 0.0 }
      }
    },
    "AISearchData": {
      "type": "object",
      "properties": {
        "object": { "type": "string", "default": "" },
        "search_query": { "type": "string", "default": "" },
        "data": {
          "type": "array",
          "items": { "$ref": "#/$defs/AISearchResult" },
          "default": []
        }
      }
    }
  }
}
```

- [ ] **Step 3: Create `docs/schemas/skillsmp-error.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "skillsmp-error.schema.json",
  "title": "ErrorResponse",
  "description": "Error response from SkillsMP API",
  "type": "object",
  "properties": {
    "success": { "type": "boolean", "default": false },
    "error": {
      "oneOf": [
        { "$ref": "#/$defs/ErrorDetail" },
        { "type": "null" }
      ]
    }
  },
  "$defs": {
    "ErrorDetail": {
      "type": "object",
      "properties": {
        "code": { "type": "string", "default": "" },
        "message": { "type": "string", "default": "" }
      }
    }
  }
}
```

- [ ] **Step 4: Commit schemas**

```bash
git add docs/schemas/skillsmp-*.schema.json
git commit -m "feat: add JSON Schemas for SkillsMP API responses

Three schemas for keyword search, AI search, and error responses.
These will be used to generate Pydantic models via datamodel-codegen."
```

---

## Task 2: Generate SkillsMP Models from Schemas + Configure Codegen

Regenerate `skillsmp_models.py` from the schemas. Add per-file-ignores and codegen mise task.

**Files:**
- Regenerate: `src/mde/research/clients/skillsmp_models.py`
- Modify: `pyproject.toml` (per-file-ignores for generated file)
- Modify: `.mise.toml` (codegen task)

**Context for implementer:**
- The existing codegen pattern is `mde:codegen:statusline` in `.mise.toml` (lines 195-213)
- The existing per-file-ignores pattern is `src/mde/statusline/models.py` in `pyproject.toml` (lines 58-64)
- datamodel-codegen is already a dev dependency
- The generated file MUST have `# generated by datamodel-codegen` in the header
- After generation, the `skillsmp_client.py` imports must still work: `SkillSearchResponse`, `AISearchResponse`, `ErrorDetail`, `ErrorResponse`
- The `skill_discover.py` imports: `SkillSearchResponse` from `skillsmp_models`
- **CRITICAL**: The generated model names and field names must match the current hand-coded ones exactly, or imports break

- [ ] **Step 1: Add codegen mise task to `.mise.toml`**

Add after the existing `mde:codegen:statusline` task (around line 213):

```toml
[tasks."mde:codegen:skillsmp"]
description = "Regenerate SkillsMP Pydantic models from JSON Schemas"
run = """
uv run datamodel-codegen \
  --input docs/schemas/skillsmp-search.schema.json \
  --input docs/schemas/skillsmp-ai-search.schema.json \
  --input docs/schemas/skillsmp-error.schema.json \
  --input-file-type jsonschema \
  --output src/mde/research/clients/skillsmp_models.py \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.12 \
  --use-annotated \
  --use-union-operator \
  --field-constraints \
  --use-default-kwarg \
  --collapse-root-models \
  --strict-nullable \
  --use-one-literal-as-default \
  --allow-extra-fields \
  --formatters ruff-format ruff-check
"""
```

- [ ] **Step 2: Run codegen and verify output**

```bash
mise run mde:codegen:skillsmp
```

After running, verify:
1. `head -1 src/mde/research/clients/skillsmp_models.py` contains `# generated by datamodel-codegen`
2. The generated file exports: `SkillSearchResponse`, `AISearchResponse`, `ErrorDetail`, `ErrorResponse`, `Skill`, `SkillSearchData`, `AISearchResult`, `AISearchData`
3. If model names don't match (datamodel-codegen may use different names from the schema titles), you'll need to adjust the schemas or add `--aliases` flags

**IMPORTANT**: If the generated models don't match the existing API (field names, class names), iterate on the schema + codegen flags until they do. The `skillsmp_client.py` imports must not break.

- [ ] **Step 3: Add `__all__` export list if missing**

The generated file may not have `__all__`. If missing, add it at the top (after imports):

```python
__all__ = [
    "AISearchResponse",
    "AISearchResult",
    "ErrorDetail",
    "ErrorResponse",
    "Skill",
    "SkillSearchData",
    "SkillSearchResponse",
]
```

Note: `AISearchData` is internal to `AISearchResponse`, so it can be omitted from `__all__` if not imported elsewhere. Check `skillsmp_client.py` imports to confirm.

- [ ] **Step 4: Add per-file-ignores in pyproject.toml**

Add after the existing `statusline/models.py` entry (around line 64):

```toml
"src/mde/research/clients/skillsmp_models.py" = [
    "D100",     # generated file — no module docstring
    "D101",     # generated file — no class docstrings
    "ERA001",   # generated file — codegen header comments
    "N815",     # generated file — camelCase field aliases
    "E501",     # generated file — long descriptions from schema
    "COM812",   # generated file — trailing comma style
]
```

- [ ] **Step 5: Verify imports still work**

```bash
uv run python -c "from mde.research.clients.skillsmp_client import SkillsMPClient; print('OK')"
uv run python -c "from mde.research.skill_discover import discover_skills; print('OK')"
```

Both must print `OK`.

- [ ] **Step 6: Run lint + type check**

```bash
uv run ruff check src/mde/research/clients/skillsmp_models.py
uv run ruff format --check src/mde/research/clients/skillsmp_models.py
```

Both must exit 0.

- [ ] **Step 7: Commit**

```bash
git add src/mde/research/clients/skillsmp_models.py pyproject.toml .mise.toml
git commit -m "feat: generate skillsmp_models.py from JSON Schema

Replace hand-coded Pydantic models with datamodel-codegen output.
Schemas: docs/schemas/skillsmp-*.schema.json
Pattern: same as statusline/models.py codegen pipeline."
```

---

## Task 3: Tests for `skillsmp_models.py` (≥3 tests)

Pure data model tests — no mocking needed. Validate Pydantic parsing, defaults, aliases.

**Files:**
- Create: `tests/mde/research/test_skillsmp_models.py`

**Context for implementer:**
- Models are in `src/mde/research/clients/skillsmp_models.py`
- `Skill` has camelCase aliases (`githubUrl` → `github_url`, etc.)
- `Skill` has `model_config = {"populate_by_name": True}` — both snake_case and camelCase work
- All fields have defaults, so `Skill(id="x", name="y", author="z")` is valid
- `SkillSearchResponse(success=True, data=None)` is valid (data is optional)
- Test existing patterns in `tests/mde/research/` (e.g., `test_catalog.py`, `test_score.py`)

- [ ] **Step 1: Write failing tests**

```python
"""Tests for SkillsMP Pydantic models."""

from __future__ import annotations

from mde.research.clients.skillsmp_models import (
    AISearchResponse,
    ErrorDetail,
    ErrorResponse,
    Skill,
    SkillSearchData,
    SkillSearchResponse,
)


class TestSkill:
    """Tests for the Skill model."""

    def test_minimal_construction(self) -> None:
        """Skill with only required fields uses defaults."""
        skill = Skill(id="abc123", name="terraform", author="hashicorp")
        assert skill.name == "terraform"
        assert skill.author == "hashicorp"
        assert skill.stars == 0
        assert skill.description == ""

    def test_camel_case_alias_parsing(self) -> None:
        """Skill parses camelCase JSON keys from API response."""
        data = {
            "id": "1",
            "name": "test",
            "author": "me",
            "githubUrl": "https://github.com/me/test",
            "skillUrl": "https://skillsmp.com/skills/test",
            "updatedAt": "2026-01-01",
        }
        skill = Skill.model_validate(data)
        assert skill.github_url == "https://github.com/me/test"
        assert skill.skill_url == "https://skillsmp.com/skills/test"
        assert skill.updated_at == "2026-01-01"

    def test_snake_case_construction(self) -> None:
        """Skill can be constructed with snake_case field names."""
        skill = Skill(
            id="1",
            name="test",
            author="me",
            github_url="https://example.com",
        )
        assert skill.github_url == "https://example.com"


class TestSkillSearchResponse:
    """Tests for SkillSearchResponse parsing."""

    def test_success_with_data(self) -> None:
        """Parse a successful search response with skills."""
        data = {
            "success": True,
            "data": {
                "skills": [
                    {"id": "1", "name": "terraform", "author": "hashicorp", "stars": 100}
                ],
                "total": 1,
                "page": 1,
                "limit": 20,
            },
        }
        resp = SkillSearchResponse.model_validate(data)
        assert resp.success is True
        assert resp.data is not None
        assert len(resp.data.skills) == 1
        assert resp.data.skills[0].stars == 100

    def test_success_with_null_data(self) -> None:
        """Parse response where data is null."""
        resp = SkillSearchResponse(success=True, data=None)
        assert resp.data is None


class TestErrorResponse:
    """Tests for ErrorResponse parsing."""

    def test_error_response(self) -> None:
        """Parse an error response."""
        data = {
            "success": False,
            "error": {"code": "RATE_LIMIT", "message": "Too many requests"},
        }
        resp = ErrorResponse.model_validate(data)
        assert resp.success is False
        assert resp.error is not None
        assert resp.error.code == "RATE_LIMIT"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/research/test_skillsmp_models.py -v
```

Expected: Tests should PASS if the generated models match the existing API. If they FAIL, the schema or codegen flags need adjustment (go back to Task 2).

- [ ] **Step 3: Fix any model mismatches**

If tests fail because generated model names/fields differ from hand-coded ones:
1. Adjust schemas (title names, property names)
2. Re-run codegen: `mise run mde:codegen:skillsmp`
3. Re-run tests until all pass

- [ ] **Step 4: Commit**

```bash
git add tests/mde/research/test_skillsmp_models.py
git commit -m "test: add tests for SkillsMP Pydantic models

7 tests covering Skill construction, camelCase alias parsing,
SkillSearchResponse with data/null, and ErrorResponse parsing."
```

---

## Task 4: Tests for `skillsmp_client.py` (≥5 tests)

Mock `httpx.get` to test the client without hitting the real API.

**Files:**
- Create: `tests/mde/research/test_skillsmp_client.py`

**Context for implementer:**
- Client is in `src/mde/research/clients/skillsmp_client.py` (139 lines)
- Two methods: `search()` and `ai_search()`
- Both return `SkillSearchResponse | ErrorResponse` or `AISearchResponse | ErrorResponse`
- `is_configured` property checks if API key is set
- Without API key, methods return `ErrorResponse` with code `MISSING_API_KEY`
- Client uses `httpx.get()` — mock this, not the whole httpx module
- Base URL: `https://skillsmp.com/api/v1/skills`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for SkillsMP API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from mde.research.clients.skillsmp_client import SkillsMPClient
from mde.research.clients.skillsmp_models import (
    ErrorResponse,
    SkillSearchResponse,
)


class TestSkillsMPClientConfig:
    """Tests for client configuration."""

    def test_no_api_key_is_not_configured(self) -> None:
        """Client without API key reports not configured."""
        client = SkillsMPClient(api_key="")
        assert client.is_configured is False

    def test_api_key_is_configured(self) -> None:
        """Client with API key reports configured."""
        client = SkillsMPClient(api_key="test-key-123")
        assert client.is_configured is True

    def test_search_without_key_returns_error(self) -> None:
        """Search without API key returns ErrorResponse."""
        client = SkillsMPClient(api_key="")
        result = client.search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "MISSING_API_KEY"

    def test_ai_search_without_key_returns_error(self) -> None:
        """AI search without API key returns ErrorResponse."""
        client = SkillsMPClient(api_key="")
        result = client.ai_search("terraform")
        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "MISSING_API_KEY"


class TestSkillsMPClientSearch:
    """Tests for search method with mocked HTTP."""

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_successful_search(self, mock_get: MagicMock) -> None:
        """Successful search returns SkillSearchResponse."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True,
            "data": {
                "skills": [
                    {"id": "1", "name": "terraform", "author": "hashicorp", "stars": 50}
                ],
                "total": 1,
                "page": 1,
                "limit": 10,
            },
        }
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform", limit=10)

        assert isinstance(result, SkillSearchResponse)
        assert result.success is True
        assert result.data is not None
        assert len(result.data.skills) == 1
        assert result.data.skills[0].name == "terraform"

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "terraform" in str(call_kwargs)

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_api_error_response(self, mock_get: MagicMock) -> None:
        """API error response is parsed as ErrorResponse."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": False,
            "error": {"code": "RATE_LIMIT", "message": "Too many requests"},
        }
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform")

        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "RATE_LIMIT"

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_http_error_returns_error_response(self, mock_get: MagicMock) -> None:
        """HTTP transport error is wrapped in ErrorResponse."""
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        client = SkillsMPClient(api_key="test-key")
        result = client.search("terraform")

        assert isinstance(result, ErrorResponse)
        assert result.error is not None
        assert result.error.code == "HTTP_ERROR"

    @patch("mde.research.clients.skillsmp_client.httpx.get")
    def test_search_passes_params(self, mock_get: MagicMock) -> None:
        """Search passes query, page, limit, sort params."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {"skills": [], "total": 0, "page": 2, "limit": 5}}
        mock_get.return_value = mock_resp

        client = SkillsMPClient(api_key="key", base_url="https://example.com/api")
        client.search("test", page=2, limit=5, sort_by="recent")

        call_args = mock_get.call_args
        assert call_args[1]["params"]["q"] == "test"
        assert call_args[1]["params"]["page"] == 2
        assert call_args[1]["params"]["limit"] == 5
        assert call_args[1]["params"]["sortBy"] == "recent"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/mde/research/test_skillsmp_client.py -v
```

Expected: FAIL if models changed in Task 2 and broke imports; otherwise should PASS since client code already exists.

- [ ] **Step 3: Fix any failures**

Adjust imports or mock targets if model regeneration changed names.

- [ ] **Step 4: Commit**

```bash
git add tests/mde/research/test_skillsmp_client.py
git commit -m "test: add tests for SkillsMP API client

8 tests covering: config (no key, with key), search (success, API error,
HTTP error, param passing), and ai_search without key."
```

---

## Task 5: Tests for `skill_discover.py` (≥10 tests)

The main module. Mock all three search backends (subprocess for skills.sh/GitHub, import for SkillsMP).

**Files:**
- Create: `tests/mde/research/test_skill_discover.py`

**Context for implementer:**
- Module: `src/mde/research/skill_discover.py` (266 lines)
- Key functions: `discover_skills(query)`, `cli_main(args)`, `_parse_skills_sh_line()`, `_strip_ansi()`, `_get_installed_skills()`, `_search_skills_sh()`, `_search_github()`, `_search_skillsmp()`
- `_search_skills_sh` and `_search_github` use `subprocess.run` — mock `subprocess.run`
- `_search_skillsmp` lazily imports `SkillsMPClient` — mock the client
- `_get_installed_skills` checks `Path(".claude/skills")` and `Path(".agents/skills")` — use `tmp_path` fixture
- `discover_skills()` calls all three search functions, catches exceptions, deduplicates by `(author/name)`, sorts by `sort_key`
- `cli_main()` uses argparse and prints results — capture stdout
- `SkillResult.sort_key` returns `(-installs, -stars, name)` — higher installs/stars sort first

- [ ] **Step 1: Write failing tests**

```python
"""Tests for unified skill discovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mde.research.skill_discover import (
    DiscoveryResult,
    SkillResult,
    _parse_skills_sh_line,
    _strip_ansi,
    cli_main,
    discover_skills,
)


class TestStripAnsi:
    """Tests for ANSI escape code removal."""

    def test_removes_color_codes(self) -> None:
        """Strip ANSI color codes from text."""
        assert _strip_ansi("\x1b[32mhello\x1b[0m") == "hello"

    def test_plain_text_unchanged(self) -> None:
        """Plain text passes through unchanged."""
        assert _strip_ansi("hello world") == "hello world"


class TestParseSkillsShLine:
    """Tests for skills.sh output line parsing."""

    def test_parses_skill_with_installs(self) -> None:
        """Parse a line with skill name and install count."""
        skills: list[SkillResult] = []
        _parse_skills_sh_line("hashicorp@terraform-style-guide 2,000 installs", skills)
        assert len(skills) == 1
        assert skills[0].name == "terraform-style-guide"
        assert skills[0].author == "hashicorp"
        assert skills[0].installs == 2000
        assert skills[0].source == "skills.sh"

    def test_parses_url_line(self) -> None:
        """Parse a URL line and attach to last skill."""
        skills: list[SkillResult] = []
        _parse_skills_sh_line("test@my-skill 50 installs", skills)
        _parse_skills_sh_line("└ https://skills.sh/test/my-skill", skills)
        assert skills[0].url == "https://skills.sh/test/my-skill"

    def test_ignores_irrelevant_lines(self) -> None:
        """Lines without 'installs' or 'skills.sh/' are ignored."""
        skills: list[SkillResult] = []
        _parse_skills_sh_line("Some random output", skills)
        assert len(skills) == 0

    def test_k_suffix_multiplied(self) -> None:
        """Install count with K suffix is multiplied by 1000."""
        skills: list[SkillResult] = []
        _parse_skills_sh_line("author@skill 7.3K installs", skills)
        assert skills[0].installs == 7300


class TestSkillResultSortKey:
    """Tests for sort ordering."""

    def test_higher_installs_sorts_first(self) -> None:
        """Skills with more installs sort before fewer."""
        a = SkillResult(name="a", author="x", source="s", installs=100)
        b = SkillResult(name="b", author="x", source="s", installs=50)
        assert a.sort_key < b.sort_key

    def test_same_installs_higher_stars_first(self) -> None:
        """With equal installs, more stars sorts first."""
        a = SkillResult(name="a", author="x", source="s", installs=10, stars=50)
        b = SkillResult(name="b", author="x", source="s", installs=10, stars=20)
        assert a.sort_key < b.sort_key

    def test_same_metrics_alphabetical(self) -> None:
        """With equal metrics, sort alphabetically by name."""
        a = SkillResult(name="alpha", author="x", source="s")
        b = SkillResult(name="beta", author="x", source="s")
        assert a.sort_key < b.sort_key


class TestDiscoverSkills:
    """Tests for the main discover_skills function."""

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_merges_results_from_all_sources(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        """Results from all sources are merged into one list."""
        mock_installed.return_value = set()
        mock_sh.return_value = [SkillResult(name="skill-a", author="a", source="skills.sh", installs=10)]
        mock_gh.return_value = [SkillResult(name="skill-b", author="b", source="github")]
        mock_smp.return_value = [SkillResult(name="skill-c", author="c", source="skillsmp", stars=5)]

        result = discover_skills("test")
        assert len(result.skills) == 3
        assert set(result.sources_searched) == {"skills.sh", "github", "skillsmp"}

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_deduplicates_by_author_name(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        """Duplicate skills (same author/name) keep highest installs."""
        mock_installed.return_value = set()
        mock_sh.return_value = [SkillResult(name="terraform", author="hashicorp", source="skills.sh", installs=100)]
        mock_gh.return_value = [SkillResult(name="terraform", author="hashicorp", source="github", installs=0)]
        mock_smp.return_value = []

        result = discover_skills("terraform")
        assert len(result.skills) == 1
        assert result.skills[0].installs == 100

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_marks_installed_skills(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        """Skills matching installed set are marked as installed."""
        mock_installed.return_value = {"terraform"}
        mock_sh.return_value = [SkillResult(name="terraform", author="h", source="skills.sh")]
        mock_gh.return_value = []
        mock_smp.return_value = []

        result = discover_skills("terraform")
        assert result.skills[0].installed is True

    @patch("mde.research.skill_discover._search_skillsmp")
    @patch("mde.research.skill_discover._search_github")
    @patch("mde.research.skill_discover._search_skills_sh")
    @patch("mde.research.skill_discover._get_installed_skills")
    def test_failed_source_recorded(
        self,
        mock_installed: MagicMock,
        mock_sh: MagicMock,
        mock_gh: MagicMock,
        mock_smp: MagicMock,
    ) -> None:
        """Sources that raise exceptions are recorded in sources_failed."""
        mock_installed.return_value = set()
        mock_sh.side_effect = TimeoutError("timed out")
        mock_gh.return_value = []
        mock_smp.return_value = []

        result = discover_skills("test")
        assert len(result.sources_failed) == 1
        assert "skills.sh" in result.sources_failed[0]
        assert "github" in result.sources_searched


class TestCliMain:
    """Tests for CLI entry point."""

    @patch("mde.research.skill_discover.discover_skills")
    def test_json_output(self, mock_discover: MagicMock, capsys: object) -> None:
        """--json flag outputs valid JSON."""
        import json

        mock_discover.return_value = DiscoveryResult(
            query="test",
            skills=[SkillResult(name="s", author="a", source="sh")],
            sources_searched=["skills.sh"],
        )

        result = cli_main(["test", "--json"])
        assert result == 0

        import sys
        captured = capsys.readouterr()  # type: ignore[union-attr]
        data = json.loads(captured.out)
        assert data["query"] == "test"
        assert len(data["skills"]) == 1

    @patch("mde.research.skill_discover.discover_skills")
    def test_no_results_message(self, mock_discover: MagicMock, capsys: object) -> None:
        """Empty results prints 'No skills found.'"""
        mock_discover.return_value = DiscoveryResult(
            query="nonexistent",
            skills=[],
            sources_searched=["skills.sh"],
        )

        result = cli_main(["nonexistent"])
        assert result == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "No skills found" in captured.out
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
uv run pytest tests/mde/research/test_skill_discover.py -v
```

Expected: All PASS (code already exists, tests exercise it via mocks).

- [ ] **Step 3: Count tests — must be ≥10**

```bash
uv run pytest tests/mde/research/test_skill_discover.py --co -q | tail -1
```

Expected: `14 tests collected` (or more)

- [ ] **Step 4: Commit**

```bash
git add tests/mde/research/test_skill_discover.py
git commit -m "test: add 14 tests for unified skill discovery

Covers: ANSI stripping, skills.sh line parsing (installs, URLs, K suffix),
sort ordering, discover_skills merging/dedup/installed marking/error handling,
and CLI JSON/no-results output."
```

---

## Task 6: Update SKILL.md + Add mise Task

**Files:**
- Modify: `.agents/skills/skill-discovery/SKILL.md`
- Modify: `.mise.toml`

**Context for implementer:**
- The SKILL.md currently tells users to run raw `npx skills search`, `npx skillkit search`, etc.
- It should reference `uv run mde-py research skill-discover` as the primary CLI
- The mise task should be `mde:research:skill-discover` following the existing pattern at lines 89-99 of `.mise.toml`
- Verification: `grep 'uv run mde-py research skill-discover' .agents/skills/skill-discovery/SKILL.md` must exit 0
- Verification: `mise task ls 2>/dev/null | grep skill-discover` must exit 0

- [ ] **Step 1: Add mise task to `.mise.toml`**

Add after the existing `mde:research:status` task (around line 99):

```toml
[tasks."mde:research:skill-discover"]
description = "Search all skill sources (skills.sh + GitHub + SkillsMP)"
run = "uv run mde-py research skill-discover \"$@\""
```

- [ ] **Step 2: Update SKILL.md to reference CLI**

In `.agents/skills/skill-discovery/SKILL.md`, add a "Quick Start" section near the top (after the frontmatter description, before "The Discovery Pipeline"):

```markdown
## Quick Start

```bash
# Unified search across all sources (skills.sh + GitHub + SkillsMP)
uv run mde-py research skill-discover <query>

# JSON output for programmatic use
uv run mde-py research skill-discover <query> --json

# Via mise task
mise run mde:research:skill-discover -- <query>
```
```

- [ ] **Step 3: Verify both checks**

```bash
grep 'uv run mde-py research skill-discover' .agents/skills/skill-discovery/SKILL.md
mise task ls 2>/dev/null | grep skill-discover
```

Both must produce output (exit 0).

- [ ] **Step 4: Commit**

```bash
git add .agents/skills/skill-discovery/SKILL.md .mise.toml
git commit -m "feat: add skill-discover mise task and update SKILL.md

Register mde:research:skill-discover in mise tasks.
Add Quick Start section to SKILL.md referencing the unified CLI."
```

---

## Task 7: Full Quality Gate

Run the complete quality gate and fix any issues.

**Files:** None new — this is verification only.

- [ ] **Step 1: Run full quality gate**

```bash
uv run mde-py quality
```

Expected: 6/6 checks pass, exit 0.

- [ ] **Step 2: Run all new tests specifically**

```bash
uv run pytest tests/mde/research/test_skill_discover.py tests/mde/research/test_skillsmp_client.py tests/mde/research/test_skillsmp_models.py -v
```

Count: ≥18 tests total (14 + 8 + 7 = 29 expected)

- [ ] **Step 3: Verify generated file header**

```bash
head -1 src/mde/research/clients/skillsmp_models.py
```

Must contain `# generated by datamodel-codegen`.

- [ ] **Step 4: Run deliverable verification matrix**

```bash
# D1: ≥10 tests for skill_discover.py
uv run pytest tests/mde/research/test_skill_discover.py --co -q | tail -1

# D2: ≥5 tests for skillsmp_client.py
uv run pytest tests/mde/research/test_skillsmp_client.py --co -q | tail -1

# D3: ≥3 tests for skillsmp_models.py
uv run pytest tests/mde/research/test_skillsmp_models.py --co -q | tail -1

# D4: SKILL.md references CLI
grep -c 'uv run mde-py research skill-discover' .agents/skills/skill-discovery/SKILL.md

# D5: mise task registered
mise task ls 2>/dev/null | grep skill-discover

# D6: Generated file header
head -1 src/mde/research/clients/skillsmp_models.py | grep -c 'generated by datamodel-codegen'

# D7: Full quality gate
uv run mde-py quality
```

All must show passing results.
