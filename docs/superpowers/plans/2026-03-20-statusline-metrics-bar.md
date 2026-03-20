# Statusline Metrics Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bash statusline script with a unified Python renderer featuring 7 toggleable widgets, SDK-typed schema validation, and v2.1.80 rate limit display.

**Architecture:** Two-layer rendering — existing A/B/C mode output + appended metrics bar of independently toggleable widgets. Schema extraction via TypedDicts composing with `claude-agent-sdk` types. Rate limits parsed into SDK `RateLimitInfo` objects.

**Tech Stack:** Python 3.12+, `claude-agent-sdk` (PyPI), pytest, ruff ALL, ty

**Spec:** `docs/superpowers/specs/2026-03-19-statusline-metrics-bar-design.md`

---

## File Map

| File | Responsibility | New/Modify |
|------|---------------|------------|
| `pyproject.toml` | Add `claude-agent-sdk>=0.1.49` dependency | Modify |
| `src/mde/statusline/schema.py` | TypedDicts, `extract_all()`, coercion helpers, rate limit parsing | New |
| `src/mde/statusline/widget_toggle.py` | Per-widget toggle config read/write/CLI | New |
| `src/mde/statusline/widgets.py` | 7 widget functions + `_render_metrics_bar()` | New |
| `src/mde/statusline/render.py` | Compose metrics bar, 4-tier colors, `_osc8_link()` | Modify |
| `src/mde/statusline/__init__.py` | Updated docstring | Modify |
| `src/mde/cli.py` | `toggle-widget` and `show-widgets` subcommands | Modify |
| `tests/mde/test_statusline_schema.py` | Schema extraction + coercion tests | New |
| `tests/mde/test_statusline_widgets.py` | All 7 widgets + metrics bar tests | New |
| `tests/mde/test_widget_toggle.py` | Toggle config tests | New |
| `tests/mde/test_statusline.py` | Integration tests (new tests added to existing file) | Modify |

---

## Task 1: Add SDK Dependency

**Files:**
- Modify: `pyproject.toml:6-10`

- [ ] **Step 1: Add `claude-agent-sdk` to `[project] dependencies`**

In `pyproject.toml`, add `claude-agent-sdk>=0.1.49` to the dependencies list:

```toml
[project]
dependencies = [
    "pydantic>=2.10",
    "pyyaml>=6.0",
    "tomli>=2.0; python_version < '3.11'",
    "claude-agent-sdk>=0.1.49",
]
```

- [ ] **Step 2: Lock and verify**

Run: `uv lock && uv sync`
Expected: Resolves successfully, `claude-agent-sdk` installed

- [ ] **Step 3: Verify import and constructor signature**

Run: `uv run pytest --co -q -c /dev/null -k "not test" --import-mode importlib -p no:cacheprovider 2>/dev/null; uv run python3 -c "from claude_agent_sdk.types import RateLimitInfo; print(sorted(RateLimitInfo.__dataclass_fields__.keys())); r = RateLimitInfo(status='allowed', utilization=0.5, raw={}); print(f'OK: {r.status} {r.utilization} {r.resets_at}')"`
Expected: Prints field names including `status`, `resets_at`, `utilization`, `raw`. Constructor call succeeds with `status` as only required arg, others optional.

> **Note:** This one-time verification uses `python3 -c` to confirm the SDK's dataclass signature before we write tests against it. This is exempt from the `uv run python` policy since it's a dependency verification, not automation.

- [ ] **Step 4: Commit**

```
git add pyproject.toml uv.lock
git commit -m "feat(statusline): add claude-agent-sdk dependency for type reuse"
```

---

## Task 2: Schema Module — TypedDicts and Coercion Helpers

**Files:**
- Create: `src/mde/statusline/schema.py`
- Test: `tests/mde/test_statusline_schema.py`

- [ ] **Step 1: Write failing tests for coercion helpers**

```python
# tests/mde/test_statusline_schema.py
from __future__ import annotations


class TestCoerceFloat:
    def test_from_float(self) -> None:
        from mde.statusline.schema import _coerce_float

        assert _coerce_float(1.25) == 1.25

    def test_from_string(self) -> None:
        from mde.statusline.schema import _coerce_float

        assert _coerce_float("1.25") == 1.25

    def test_from_none(self) -> None:
        from mde.statusline.schema import _coerce_float

        assert _coerce_float(None) == 0.0

    def test_from_invalid(self) -> None:
        from mde.statusline.schema import _coerce_float

        assert _coerce_float("not-a-number") == 0.0


class TestCoerceInt:
    def test_from_int(self) -> None:
        from mde.statusline.schema import _coerce_int

        assert _coerce_int(42) == 42

    def test_from_string(self) -> None:
        from mde.statusline.schema import _coerce_int

        assert _coerce_int("42") == 42

    def test_from_none(self) -> None:
        from mde.statusline.schema import _coerce_int

        assert _coerce_int(None) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_statusline_schema.py -v`
Expected: FAIL — `mde.statusline.schema` does not exist

- [ ] **Step 3: Implement coercion helpers and TypedDicts**

Create `src/mde/statusline/schema.py` with:
- `_coerce_float()`, `_coerce_int()`, `_coerce_int_or_none()`, `_coerce_float_or_none()`
- `_safe_dict()` — returns `{}` for `None`, non-dict, or absent values
- All TypedDicts: `ModelInfo`, `CostInfo`, `TokenUsage`, `ContextWindow`, `WorkspaceInfo`, `WorktreeInfo`, `StatuslineInput`
- `_KNOWN_KEYS` frozenset from `StatuslineInput.__annotations__`
- `_warn_unknown_keys()` function

```python
"""Statusline stdin JSON schema types and extraction.

TypedDicts for the statusline stdin protocol (not typed in the SDK).
Composes with claude_agent_sdk.types for rate limit handling.
"""

from __future__ import annotations

from typing import Any, TypedDict

from typing_extensions import NotRequired


class ModelInfo(TypedDict):
    id: NotRequired[str]
    display_name: NotRequired[str]


class CostInfo(TypedDict):
    total_cost_usd: NotRequired[float]
    total_duration_ms: NotRequired[float]
    total_api_duration_ms: NotRequired[float]
    total_lines_added: NotRequired[int]
    total_lines_removed: NotRequired[int]


class TokenUsage(TypedDict):
    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]
    cache_creation_input_tokens: NotRequired[int]
    cache_read_input_tokens: NotRequired[int]


class ContextWindow(TypedDict):
    context_window_size: NotRequired[int | None]
    total_input_tokens: NotRequired[int | None]
    total_output_tokens: NotRequired[int | None]
    current_usage: NotRequired[TokenUsage | None]
    used_percentage: NotRequired[float | None]
    remaining_percentage: NotRequired[float | None]


class WorkspaceInfo(TypedDict):
    current_dir: NotRequired[str]
    project_dir: NotRequired[str]


class WorktreeInfo(TypedDict):
    name: str
    path: str
    branch: NotRequired[str]
    original_cwd: str
    original_branch: NotRequired[str]


class StatuslineInput(TypedDict):
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]
    model: NotRequired[str | ModelInfo]
    workspace: NotRequired[WorkspaceInfo]
    version: NotRequired[str]
    output_style: NotRequired[dict[str, str]]
    cost: NotRequired[CostInfo]
    context_window: NotRequired[ContextWindow | None]
    exceeds_200k_tokens: NotRequired[bool]
    rate_limits: NotRequired[dict[str, Any]]
    vim: NotRequired[dict[str, str] | None]
    agent: NotRequired[dict[str, str]]
    worktree: NotRequired[WorktreeInfo]


_KNOWN_KEYS = frozenset(StatuslineInput.__annotations__.keys())


def _warn_unknown_keys(data: dict[str, Any]) -> None:
    unknown = set(data.keys()) - _KNOWN_KEYS
    if unknown:
        import sys

        print(f"[statusline] unknown keys: {unknown}", file=sys.stderr)


def _coerce_float(val: object, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _coerce_int(val: object, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _coerce_float_or_none(val: object) -> float | None:
    if val is None:
        return None
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _coerce_int_or_none(val: object) -> int | None:
    if val is None:
        return None
    try:
        return int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _safe_dict(val: object) -> dict[str, Any]:
    return val if isinstance(val, dict) else {}


def _safe_str(data: dict[str, Any], dotpath: str, default: str = "") -> str:
    parts = dotpath.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return default
    return str(current) if current is not None else default
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/mde/test_statusline_schema.py -v`
Expected: All PASS

- [ ] **Step 5: Lint check**

Run: `uv run ruff check src/mde/statusline/schema.py --select ALL`
Expected: Zero violations

- [ ] **Step 6: Commit**

```
git add src/mde/statusline/schema.py tests/mde/test_statusline_schema.py
git commit -m "feat(statusline): add schema TypedDicts and coercion helpers"
```

---

## Task 3: Schema Module — `extract_all()` and Rate Limit Parsing

**Files:**
- Modify: `src/mde/statusline/schema.py`
- Modify: `tests/mde/test_statusline_schema.py`

- [ ] **Step 1: Write failing tests for `extract_all()` and rate limit parsing**

Add to `tests/mde/test_statusline_schema.py`:

```python
from claude_agent_sdk.types import RateLimitInfo


def _full_statusline_json() -> dict[str, object]:
    """Complete v2.1.80 statusline stdin JSON."""
    return {
        "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
        "cost": {"total_cost_usd": 2.50, "total_duration_ms": 120000, "total_lines_added": 156, "total_lines_removed": 23},
        "context_window": {
            "total_input_tokens": 50000, "total_output_tokens": 10000,
            "context_window_size": 200000, "used_percentage": 65,
            "current_usage": {"input_tokens": 8500, "cache_read_input_tokens": 2000, "cache_creation_input_tokens": 5000, "output_tokens": 1200},
        },
        "exceeds_200k_tokens": False,
        "version": "2.1.80",
        "session_id": "test-session",
    }


class TestExtractAll:
    def test_full_schema(self) -> None:
        from mde.statusline.schema import extract_all

        ctx = extract_all(_full_statusline_json())
        assert ctx["model"] == "Opus"
        assert ctx["total_cost_usd"] == 2.50
        assert ctx["total_duration_ms"] == 120000
        assert ctx["total_input_tokens"] == 50000
        assert ctx["total_lines_added"] == 156
        assert ctx["cache_read_tokens"] == 2000
        assert ctx["exceeds_200k"] is False

    def test_minimal(self) -> None:
        from mde.statusline.schema import extract_all

        ctx = extract_all({})
        assert ctx["model"] == "unknown"
        assert ctx["total_cost_usd"] == 0.0
        assert ctx["rate_5h"] is None

    def test_current_usage_null(self) -> None:
        from mde.statusline.schema import extract_all

        data = {"context_window": {"used_percentage": 10, "current_usage": None}}
        ctx = extract_all(data)
        assert ctx["cache_read_tokens"] == 0.0


class TestParseRateLimits:
    def test_absent(self) -> None:
        from mde.statusline.schema import _parse_rate_limits

        result = _parse_rate_limits(None)
        assert result["five_hour"] is None

    def test_shape_b_nested(self) -> None:
        from mde.statusline.schema import _parse_rate_limits

        raw = {"five_hour": {"status": "allowed_warning", "utilization": 0.42, "resetsAt": 1773273600}}
        result = _parse_rate_limits(raw)
        info = result["five_hour"]
        assert isinstance(info, RateLimitInfo)
        assert info.utilization == 0.42
        assert info.resets_at == 1773273600
        assert info.status == "allowed_warning"

    def test_shape_a_flat(self) -> None:
        from mde.statusline.schema import _parse_rate_limits

        raw = {"status": "allowed", "rateLimitType": "five_hour", "utilization": 0.62, "resetsAt": 1773273600}
        result = _parse_rate_limits(raw)
        assert result["five_hour"] is not None
        assert result["five_hour"].utilization == 0.62

    def test_model_specific_normalized(self) -> None:
        from mde.statusline.schema import _parse_rate_limits

        raw = {"status": "allowed", "rateLimitType": "seven_day_opus", "utilization": 0.15}
        result = _parse_rate_limits(raw)
        assert result["seven_day"] is not None
        assert result["seven_day"].utilization == 0.15


class TestWarnUnknownKeys:
    def test_warns_on_unknown(self, capsys: object) -> None:
        from mde.statusline.schema import _warn_unknown_keys

        _warn_unknown_keys({"model": {}, "unknown_field": True})
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "unknown_field" in captured.err

    def test_no_warning_on_known(self, capsys: object) -> None:
        from mde.statusline.schema import _warn_unknown_keys

        _warn_unknown_keys({"model": {}, "cost": {}})
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert captured.err == ""


class TestRateLimitsCamelToSnake:
    def test_camel_case_normalized(self) -> None:
        from mde.statusline.schema import _parse_rate_limits

        raw = {"five_hour": {"status": "allowed", "rateLimitType": "five_hour", "resetsAt": 1773273600, "utilization": 0.42}}
        result = _parse_rate_limits(raw)
        info = result["five_hour"]
        assert info is not None
        assert info.rate_limit_type == "five_hour"
        assert info.resets_at == 1773273600


class TestUnknownFieldsNoCrash:
    def test_extract_all_with_unknown_keys(self) -> None:
        from mde.statusline.schema import extract_all

        result = extract_all({"unknown_future_key": True, "another_new_field": [1, 2, 3]})
        assert isinstance(result, dict)
        assert result["model"] == "unknown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_statusline_schema.py::TestExtractAll -v`
Expected: FAIL — `extract_all` not defined

- [ ] **Step 3: Implement `extract_all()` and `_parse_rate_limits()`**

Add to `src/mde/statusline/schema.py`:

```python
from claude_agent_sdk.types import RateLimitInfo


def extract_all(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and validate all fields from Claude Code stdin JSON."""
    _warn_unknown_keys(data)

    cost = _safe_dict(data.get("cost"))
    ctx = _safe_dict(data.get("context_window"))
    usage = _safe_dict(ctx.get("current_usage")) if isinstance(ctx.get("current_usage"), dict) else {}
    rate_info = _parse_rate_limits(data.get("rate_limits"))

    return {
        "model": _safe_str(data, "model.display_name", "unknown"),
        "cost_usd": _coerce_float(cost.get("total_cost_usd")),
        "context_pct": _coerce_float(ctx.get("used_percentage")),
        "total_cost_usd": _coerce_float(cost.get("total_cost_usd")),
        "total_duration_ms": _coerce_float(cost.get("total_duration_ms")),
        "total_api_duration_ms": _coerce_float(cost.get("total_api_duration_ms")),
        "total_input_tokens": _coerce_float(ctx.get("total_input_tokens")),
        "total_output_tokens": _coerce_float(ctx.get("total_output_tokens")),
        "total_lines_added": _coerce_int(cost.get("total_lines_added")),
        "total_lines_removed": _coerce_int(cost.get("total_lines_removed")),
        "cache_read_tokens": _coerce_float(usage.get("cache_read_input_tokens")),
        "cache_create_tokens": _coerce_float(usage.get("cache_creation_input_tokens")),
        "input_tokens": _coerce_float(usage.get("input_tokens")),
        "rate_5h": rate_info.get("five_hour"),
        "rate_7d": rate_info.get("seven_day"),
        "rate_overage": rate_info.get("overage"),
        "exceeds_200k": bool(data.get("exceeds_200k_tokens", False)),
        "agent_name": _safe_str(data, "agent.name", ""),
        "version": str(data.get("version", "")),
    }


def _parse_rate_limits(raw: Any) -> dict[str, RateLimitInfo | None]:
    """Parse rate_limits from stdin JSON into SDK RateLimitInfo objects.

    Handles both Shape A (flat with rateLimitType) and Shape B (nested by window).
    Normalizes camelCase wire format to snake_case SDK fields.
    """
    if not isinstance(raw, dict):
        return {"five_hour": None, "seven_day": None, "overage": None}

    result: dict[str, RateLimitInfo | None] = {}

    # Shape B: nested by window name
    for window_name in ("five_hour", "seven_day", "overage"):
        window = raw.get(window_name)
        if isinstance(window, dict):
            result[window_name] = RateLimitInfo(
                status=window.get("status", "allowed"),
                resets_at=_coerce_int_or_none(window.get("resetsAt") or window.get("resets_at")),
                rate_limit_type=window.get("rateLimitType") or window.get("rate_limit_type"),
                utilization=_coerce_float_or_none(window.get("utilization")),
                raw=window,
            )
        else:
            result[window_name] = None

    # Shape A fallback: flat dict with rate_limit_type identifying the window
    if all(v is None for v in result.values()) and "status" in raw:
        window_name = raw.get("rateLimitType") or raw.get("rate_limit_type") or "five_hour"
        if window_name in ("seven_day_opus", "seven_day_sonnet"):
            window_name = "seven_day"
        result[window_name] = RateLimitInfo(
            status=raw.get("status", "allowed"),
            resets_at=_coerce_int_or_none(raw.get("resetsAt") or raw.get("resets_at")),
            rate_limit_type=raw.get("rateLimitType") or raw.get("rate_limit_type"),
            utilization=_coerce_float_or_none(raw.get("utilization")),
            raw=raw,
        )

    return result
```

- [ ] **Step 4: Run all schema tests**

Run: `uv run pytest tests/mde/test_statusline_schema.py -v`
Expected: All PASS

- [ ] **Step 5: Lint + type check**

Run: `uv run ruff check src/mde/statusline/schema.py --select ALL && uv run ty check src/mde/statusline/schema.py`
Expected: Zero violations

- [ ] **Step 6: Commit**

```
git add src/mde/statusline/schema.py tests/mde/test_statusline_schema.py
git commit -m "feat(statusline): add extract_all() with SDK rate limit parsing"
```

---

## Task 4: Widget Toggle Module

**Files:**
- Create: `src/mde/statusline/widget_toggle.py`
- Test: `tests/mde/test_widget_toggle.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/mde/test_widget_toggle.py
from __future__ import annotations

import json
from unittest.mock import patch


class TestReadWidgetConfig:
    def test_defaults_all_true(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            config = widget_toggle._read_widget_config()
        assert all(config.values())
        assert len(config) == 7

    def test_corrupt_defaults(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text("not json")
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            config = widget_toggle._read_widget_config()
        assert all(config.values())


class TestToggleWidget:
    def test_flips_on_to_off(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({"token_speed": True}))
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            assert widget_toggle.toggle_widget("token_speed") == 0
        data = json.loads(config_file.read_text())  # type: ignore[union-attr]
        assert data["token_speed"] is False

    def test_unknown_widget_returns_1(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            assert widget_toggle.toggle_widget("nonexistent") == 1

    def test_toggle_all_any_on_turns_all_off(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({"token_speed": True, "burn_rate": False}))
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            widget_toggle.toggle_widget("all")
            config = widget_toggle._read_widget_config()
        assert not any(config.values())

    def test_toggle_all_all_off_turns_all_on(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({k: False for k in widget_toggle._ALL_WIDGETS}))
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            widget_toggle.toggle_widget("all")
            config = widget_toggle._read_widget_config()
        assert all(config.values())


class TestShowWidgets:
    def test_output_format(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            widget_toggle.show_widgets()
        captured = capsys.readouterr()  # type: ignore[union-attr]
        for name in widget_toggle._ALL_WIDGETS:
            assert name in captured.out
        assert "on" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_widget_toggle.py -v`
Expected: FAIL — `widget_toggle` module does not exist

- [ ] **Step 3: Implement `widget_toggle.py`**

Create `src/mde/statusline/widget_toggle.py`:

```python
"""Per-widget toggle for statusline metrics bar.

Persists config to .artifacts/statusline-widgets.json.
All widgets default to enabled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_WIDGET_CONFIG_FILE = Path(".artifacts/statusline-widgets.json")

_ALL_WIDGETS = [
    "token_speed",
    "burn_rate",
    "block_timer",
    "daily_totals",
    "lines_changed",
    "cache_ratio",
    "rate_limits",
]


def _read_widget_config() -> dict[str, bool]:
    try:
        data: dict[str, Any] = json.loads(_WIDGET_CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    return {name: bool(data.get(name, True)) for name in _ALL_WIDGETS}


def _write_widget_config(config: dict[str, bool]) -> None:
    _WIDGET_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WIDGET_CONFIG_FILE.write_text(json.dumps(config, indent=4) + "\n")


def toggle_widget(name: str) -> int:
    if name != "all" and name not in _ALL_WIDGETS:
        print(f"Unknown widget: {name}. Valid: {', '.join(_ALL_WIDGETS)}, all")
        return 1

    config = _read_widget_config()

    if name == "all":
        new_state = not any(config.values())
        config = {k: new_state for k in _ALL_WIDGETS}
    else:
        old = config[name]
        config[name] = not old
        print(f"{name}: {'on' if old else 'off'} \u2192 {'off' if old else 'on'}")

    _write_widget_config(config)
    return 0


def show_widgets() -> int:
    config = _read_widget_config()
    for name, enabled in config.items():
        print(f"{name:<14} {'on' if enabled else 'off'}")
    return 0
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_widget_toggle.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widget_toggle.py tests/mde/test_widget_toggle.py
git commit -m "feat(statusline): add per-widget toggle module"
```

---

## Task 5: Widgets — `token_speed`, `burn_rate`, `block_timer`

**Files:**
- Create: `src/mde/statusline/widgets.py`
- Create: `tests/mde/test_statusline_widgets.py`

- [ ] **Step 1: Write failing tests for first 3 widgets**

```python
# tests/mde/test_statusline_widgets.py
from __future__ import annotations


class TestTokenSpeed:
    def test_normal(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        ctx = {"total_input_tokens": 20000.0, "total_output_tokens": 10000.0, "total_duration_ms": 60000.0}
        assert token_speed_widget(ctx) == "500 tok/s"

    def test_zero_duration(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        ctx = {"total_input_tokens": 100.0, "total_output_tokens": 0.0, "total_duration_ms": 0.0}
        assert token_speed_widget(ctx) == "\u2014 tok/s"

    def test_zero_tokens_with_duration(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        ctx = {"total_input_tokens": 0.0, "total_output_tokens": 0.0, "total_duration_ms": 60000.0}
        assert token_speed_widget(ctx) == "0 tok/s"

    def test_missing_fields(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        assert token_speed_widget({}) == "\u2014 tok/s"


class TestBurnRate:
    def test_normal(self) -> None:
        from mde.statusline.widgets import burn_rate_widget

        ctx = {"total_cost_usd": 1.50, "total_duration_ms": 60000.0}
        assert burn_rate_widget(ctx) == "$1.50/min"

    def test_zero_duration(self) -> None:
        from mde.statusline.widgets import burn_rate_widget

        ctx = {"total_cost_usd": 1.50, "total_duration_ms": 0.0}
        assert burn_rate_widget(ctx) == "$0.00/min"


class TestBlockTimer:
    def test_normal(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        assert block_timer_widget({"total_duration_ms": 125000.0}) == "2:05"

    def test_over_hour(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        assert block_timer_widget({"total_duration_ms": 3725000.0}) == "1:02:05"

    def test_zero(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        assert block_timer_widget({"total_duration_ms": 0.0}) == "0:00"

    def test_just_under_hour(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        assert block_timer_widget({"total_duration_ms": 3599000.0}) == "59:59"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Implement first 3 widgets**

Create `src/mde/statusline/widgets.py`:

```python
"""Statusline widget functions.

Each widget is a pure function: (ctx: dict[str, object]) -> str
Empty string means the widget is suppressed from the metrics bar.
"""

from __future__ import annotations

from typing import Any

from mde.statusline.schema import _coerce_float


def token_speed_widget(ctx: dict[str, Any]) -> str:
    input_tok = _coerce_float(ctx.get("total_input_tokens"))
    output_tok = _coerce_float(ctx.get("total_output_tokens"))
    duration_ms = _coerce_float(ctx.get("total_duration_ms"))
    if duration_ms <= 0:
        return "\u2014 tok/s"
    tok_per_sec = (input_tok + output_tok) / (duration_ms / 1000)
    return f"{int(tok_per_sec)} tok/s"


def burn_rate_widget(ctx: dict[str, Any]) -> str:
    cost = _coerce_float(ctx.get("total_cost_usd"))
    duration_ms = _coerce_float(ctx.get("total_duration_ms"))
    if duration_ms <= 0:
        return "$0.00/min"
    rate = cost / (duration_ms / 60_000)
    return f"${rate:.2f}/min"


def block_timer_widget(ctx: dict[str, Any]) -> str:
    duration_ms = _coerce_float(ctx.get("total_duration_ms"))
    total_sec = int(duration_ms / 1000)
    if total_sec >= 3600:
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        return f"{hours}:{mins:02d}:{secs:02d}"
    mins = total_sec // 60
    secs = total_sec % 60
    return f"{mins}:{secs:02d}"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widgets.py tests/mde/test_statusline_widgets.py
git commit -m "feat(statusline): add token_speed, burn_rate, block_timer widgets"
```

---

## Task 6: Widgets — `daily_totals`

**Files:**
- Modify: `src/mde/statusline/widgets.py`
- Modify: `tests/mde/test_statusline_widgets.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/mde/test_statusline_widgets.py`:

```python
import json
from unittest.mock import patch


class TestDailyTotals:
    def test_fresh(self, tmp_path: object) -> None:
        from mde.statusline import widgets

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        ctx = {"total_cost_usd": 2.50, "total_input_tokens": 50000.0, "total_output_tokens": 10000.0}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = widgets.daily_totals_widget(ctx)
        assert "day: $2.50" in result
        assert "60k tok" in result

    def test_accumulates(self, tmp_path: object) -> None:
        from datetime import date

        from mde.statusline import widgets

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        totals_file.write_text(json.dumps({"date": str(date.today()), "total_cost_usd": 1.00, "total_tokens": 20000}))
        ctx = {"total_cost_usd": 1.50, "total_input_tokens": 30000.0, "total_output_tokens": 10000.0}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = widgets.daily_totals_widget(ctx)
        assert "day: $2.50" in result
        assert "60k tok" in result

    def test_resets_on_new_day(self, tmp_path: object) -> None:
        from mde.statusline import widgets

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        totals_file.write_text(json.dumps({"date": "1999-01-01", "total_cost_usd": 999.0, "total_tokens": 999999}))
        ctx = {"total_cost_usd": 1.00, "total_input_tokens": 5000.0, "total_output_tokens": 5000.0}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = widgets.daily_totals_widget(ctx)
        assert "day: $1.00" in result
        assert "10k tok" in result

    def test_corrupt_file(self, tmp_path: object) -> None:
        from mde.statusline import widgets

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        totals_file.write_text("not json")
        ctx = {"total_cost_usd": 1.00, "total_input_tokens": 5000.0, "total_output_tokens": 5000.0}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = widgets.daily_totals_widget(ctx)
        assert "day: $1.00" in result
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/mde/test_statusline_widgets.py::TestDailyTotals -v`
Expected: FAIL

- [ ] **Step 3: Implement `daily_totals_widget`**

Add to `src/mde/statusline/widgets.py`:

```python
import json
from datetime import date
from pathlib import Path

_DAILY_TOTALS_FILE = Path(".artifacts/daily-totals.json")


def daily_totals_widget(ctx: dict[str, Any]) -> str:
    cost = _coerce_float(ctx.get("total_cost_usd"))
    tokens = _coerce_float(ctx.get("total_input_tokens")) + _coerce_float(ctx.get("total_output_tokens"))
    today = str(date.today())

    # Read existing totals
    try:
        data = json.loads(_DAILY_TOTALS_FILE.read_text())
        if not isinstance(data, dict) or data.get("date") != today:
            data = {}
    except (OSError, json.JSONDecodeError):
        data = {}

    if data.get("date") == today:
        cost += _coerce_float(data.get("total_cost_usd"))
        tokens += _coerce_float(data.get("total_tokens"))

    # Write back
    _DAILY_TOTALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DAILY_TOTALS_FILE.write_text(json.dumps({
        "date": today,
        "total_cost_usd": cost,
        "total_tokens": int(tokens),
    }) + "\n")

    return f"day: ${cost:.2f} {int(tokens) // 1000}k tok"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widgets.py tests/mde/test_statusline_widgets.py
git commit -m "feat(statusline): add daily_totals widget with persistence"
```

---

## Task 7: Widgets — `lines_changed`, `cache_ratio`

**Files:**
- Modify: `src/mde/statusline/widgets.py`
- Modify: `tests/mde/test_statusline_widgets.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/mde/test_statusline_widgets.py`:

```python
class TestLinesChanged:
    def test_both(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        ctx = {"total_lines_added": 156, "total_lines_removed": 23}
        result = lines_changed_widget(ctx)
        assert "+156" in result
        assert "-23" in result

    def test_add_only(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        ctx = {"total_lines_added": 156, "total_lines_removed": 0}
        result = lines_changed_widget(ctx)
        assert "+156" in result
        assert "-" not in result

    def test_remove_only(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        ctx = {"total_lines_added": 0, "total_lines_removed": 23}
        result = lines_changed_widget(ctx)
        assert "-23" in result
        assert "+" not in result

    def test_both_zero(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        assert lines_changed_widget({"total_lines_added": 0, "total_lines_removed": 0}) == ""


class TestCacheRatio:
    def test_normal(self) -> None:
        from mde.statusline.widgets import cache_ratio_widget

        ctx = {"cache_read_tokens": 620.0, "cache_create_tokens": 380.0, "input_tokens": 0.0}
        result = cache_ratio_widget(ctx)
        assert "cache:62%" in result

    def test_no_usage(self) -> None:
        from mde.statusline.widgets import cache_ratio_widget

        assert cache_ratio_widget({"cache_read_tokens": 0.0, "cache_create_tokens": 0.0, "input_tokens": 0.0}) == ""
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/mde/test_statusline_widgets.py::TestLinesChanged -v`
Expected: FAIL

- [ ] **Step 3: Implement both widgets**

Add to `src/mde/statusline/widgets.py`:

```python
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"


def lines_changed_widget(ctx: dict[str, Any]) -> str:
    added = int(_coerce_float(ctx.get("total_lines_added")))
    removed = int(_coerce_float(ctx.get("total_lines_removed")))
    if added == 0 and removed == 0:
        return ""
    parts = []
    if added > 0:
        parts.append(f"{_GREEN}+{added}{_RESET}")
    if removed > 0:
        parts.append(f"{_RED}-{removed}{_RESET}")
    return "/".join(parts)


def cache_ratio_widget(ctx: dict[str, Any]) -> str:
    read = _coerce_float(ctx.get("cache_read_tokens"))
    create = _coerce_float(ctx.get("cache_create_tokens"))
    inp = _coerce_float(ctx.get("input_tokens"))
    total = read + create + inp
    if total <= 0:
        return ""
    pct = int(read * 100 / total)
    if pct > 60:
        color = _GREEN
    elif pct > 30:
        color = _YELLOW
    else:
        color = _RED
    return f"{color}cache:{pct}%{_RESET}"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widgets.py tests/mde/test_statusline_widgets.py
git commit -m "feat(statusline): add lines_changed and cache_ratio widgets"
```

---

## Task 8: Widgets — `rate_limits`

**Files:**
- Modify: `src/mde/statusline/widgets.py`
- Modify: `tests/mde/test_statusline_widgets.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/mde/test_statusline_widgets.py`:

```python
import time

from claude_agent_sdk.types import RateLimitInfo


class TestRateLimits:
    def test_normal(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        ctx = {"rate_5h": RateLimitInfo(status="allowed", utilization=0.42, raw={}), "rate_7d": None}
        result = rate_limits_widget(ctx)
        assert "5h:42%" in result

    def test_both_windows(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        ctx = {
            "rate_5h": RateLimitInfo(status="allowed", utilization=0.42, raw={}),
            "rate_7d": RateLimitInfo(status="allowed", utilization=0.15, raw={}),
        }
        result = rate_limits_widget(ctx)
        assert "5h:42%" in result
        assert "7d:15%" in result

    def test_rejected(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        ctx = {"rate_5h": RateLimitInfo(status="rejected", raw={}), "rate_7d": None}
        result = rate_limits_widget(ctx)
        assert "LIMIT" in result

    def test_absent(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        assert rate_limits_widget({"rate_5h": None, "rate_7d": None}) == ""

    def test_countdown_when_high(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        future = int(time.time()) + 7200  # 2 hours from now
        ctx = {"rate_5h": RateLimitInfo(status="allowed_warning", utilization=0.85, resets_at=future, raw={}), "rate_7d": None}
        result = rate_limits_widget(ctx)
        assert "\u21bb" in result  # ↻ symbol
        assert "5h:85%" in result

    def test_allowed_warning_forces_color(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        ctx = {"rate_5h": RateLimitInfo(status="allowed_warning", utilization=0.30, raw={}), "rate_7d": None}
        result = rate_limits_widget(ctx)
        assert "5h:30%" in result
        # allowed_warning should show even at low utilization
        assert result != ""
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/mde/test_statusline_widgets.py::TestRateLimits -v`
Expected: FAIL

- [ ] **Step 3: Implement `rate_limits_widget` and `_format_countdown`**

Add to `src/mde/statusline/widgets.py`:

```python
import time

from claude_agent_sdk.types import RateLimitInfo

_ORANGE = "\033[38;5;208m"


def _color_for_pct(pct: float) -> str:
    if pct >= 90:
        return _RED
    if pct >= 70:
        return _ORANGE
    if pct >= 50:
        return _YELLOW
    return _GREEN


def _format_countdown(resets_at: int) -> str:
    remaining = max(0, resets_at - int(time.time()))
    hours = remaining // 3600
    mins = (remaining % 3600) // 60
    if hours > 0:
        return f"{hours}h{mins:02d}m"
    return f"{mins}m"


def rate_limits_widget(ctx: dict[str, Any]) -> str:
    parts: list[str] = []
    for label, key in [("5h", "rate_5h"), ("7d", "rate_7d")]:
        info: RateLimitInfo | None = ctx.get(key)
        if info is None:
            continue
        if info.status == "rejected":
            parts.append(f"{_RED}{label}:LIMIT{_RESET}")
        elif info.utilization is not None:
            pct = info.utilization * 100
            color = _color_for_pct(pct)
            text = f"{label}:{pct:.0f}%"
            if pct >= 70 and info.resets_at:
                text += f" \u21bb{_format_countdown(info.resets_at)}"
            parts.append(f"{color}{text}{_RESET}")
    return " ".join(parts)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widgets.py tests/mde/test_statusline_widgets.py
git commit -m "feat(statusline): add rate_limits widget with SDK RateLimitInfo"
```

---

## Task 9: Metrics Bar Composition

**Files:**
- Modify: `src/mde/statusline/widgets.py`
- Modify: `tests/mde/test_statusline_widgets.py`

- [ ] **Step 1: Write failing tests for `_render_metrics_bar()`**

Add to `tests/mde/test_statusline_widgets.py`:

```python
class TestMetricsBar:
    def test_all_enabled(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import _render_metrics_bar

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        ctx = {
            "total_input_tokens": 30000.0, "total_output_tokens": 0.0, "total_duration_ms": 60000.0,
            "total_cost_usd": 1.50, "total_lines_added": 10, "total_lines_removed": 5,
            "cache_read_tokens": 500.0, "cache_create_tokens": 300.0, "input_tokens": 200.0,
            "rate_5h": None, "rate_7d": None,
        }
        config = {k: True for k in ["token_speed", "burn_rate", "block_timer", "daily_totals", "lines_changed", "cache_ratio", "rate_limits"]}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = _render_metrics_bar(ctx, config)
        assert "tok/s" in result
        assert "$" in result
        assert " | " in result

    def test_all_disabled(self) -> None:
        from mde.statusline.widgets import _render_metrics_bar

        config = {k: False for k in ["token_speed", "burn_rate", "block_timer", "daily_totals", "lines_changed", "cache_ratio", "rate_limits"]}
        result = _render_metrics_bar({}, config)
        assert result == ""

    def test_suppresses_empty_widgets(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import _render_metrics_bar

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        ctx = {
            "total_input_tokens": 30000.0, "total_output_tokens": 0.0, "total_duration_ms": 60000.0,
            "total_cost_usd": 1.50, "total_lines_added": 0, "total_lines_removed": 0,
            "cache_read_tokens": 0.0, "cache_create_tokens": 0.0, "input_tokens": 0.0,
            "rate_5h": None, "rate_7d": None,
        }
        config = {k: True for k in ["token_speed", "burn_rate", "block_timer", "daily_totals", "lines_changed", "cache_ratio", "rate_limits"]}
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = _render_metrics_bar(ctx, config)
        assert " | " in result
        # lines_changed, cache_ratio, rate_limits all suppressed — no extra separators
        assert result.count(" | ") <= 3  # at most tok/s, $/min, timer, daily
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/mde/test_statusline_widgets.py::TestMetricsBar -v`
Expected: FAIL

- [ ] **Step 3: Implement `_render_metrics_bar()`**

Add to `src/mde/statusline/widgets.py`:

```python
def _render_metrics_bar(ctx: dict[str, Any], config: dict[str, bool]) -> str:
    widget_map: list[tuple[str, Any]] = [
        ("token_speed", token_speed_widget),
        ("burn_rate", burn_rate_widget),
        ("block_timer", block_timer_widget),
        ("daily_totals", daily_totals_widget),
        ("lines_changed", lines_changed_widget),
        ("cache_ratio", cache_ratio_widget),
        ("rate_limits", rate_limits_widget),
    ]
    parts = []
    for name, fn in widget_map:
        if not config.get(name, True):
            continue
        output = fn(ctx)
        if output:
            parts.append(output)
    return " | ".join(parts)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/mde/test_statusline_widgets.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```
git add src/mde/statusline/widgets.py tests/mde/test_statusline_widgets.py
git commit -m "feat(statusline): add metrics bar composition with widget suppression"
```

---

## Task 10: Integrate into Render Pipeline

**Files:**
- Modify: `src/mde/statusline/render.py`
- Modify: `tests/mde/test_statusline.py`

- [ ] **Step 1: Write failing integration tests**

Add to `tests/mde/test_statusline.py`:

```python
class TestMetricsBarIntegration:
    def test_mode_a_with_metrics_bar(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text('{"token_speed": true, "burn_rate": false, "block_timer": false, "daily_totals": false, "lines_changed": false, "cache_ratio": false, "rate_limits": false}')
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 1.23, "total_duration_ms": 60000},
            "context_window": {"used_percentage": 42, "total_input_tokens": 30000, "total_output_tokens": 0},
        }
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file),
            patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "$1.23" in captured.out
        assert "tok/s" in captured.out
        assert " | " in captured.out

    def test_mode_a_all_widgets_disabled(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({k: False for k in ["token_speed", "burn_rate", "block_timer", "daily_totals", "lines_changed", "cache_ratio", "rate_limits"]}))
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data = {"model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 1.23}, "context_window": {"used_percentage": 42}}
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file),
            patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "$1.23" in captured.out
        assert "tok/s" not in captured.out  # No metrics bar

    def test_mode_c_with_metrics_bar(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("C\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text('{"token_speed": true, "burn_rate": false, "block_timer": false, "daily_totals": false, "lines_changed": false, "cache_ratio": false, "rate_limits": false}')
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 2.50, "total_duration_ms": 60000},
            "context_window": {"used_percentage": 65, "total_input_tokens": 30000, "total_output_tokens": 0},
        }
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file),
            patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        lines = captured.out.strip().split("\n")
        assert len(lines) >= 2  # Mode C is multi-line, metrics on last line
        assert "tok/s" in lines[-1]  # Metrics bar is on the last line

    def test_4_tier_color_at_85_pct(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({k: False for k in ["token_speed", "burn_rate", "block_timer", "daily_totals", "lines_changed", "cache_ratio", "rate_limits"]}))
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data = {"model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 0}, "context_window": {"used_percentage": 85}}
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file),
            patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "85%" in captured.out
        assert "\033[38;5;208m" in captured.out  # Orange (not red)

    def test_rate_limits_in_full_render(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text('{"token_speed": false, "burn_rate": false, "block_timer": false, "daily_totals": false, "lines_changed": false, "cache_ratio": false, "rate_limits": true}')
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 1.00},
            "context_window": {"used_percentage": 42},
            "rate_limits": {"five_hour": {"status": "allowed_warning", "utilization": 0.72, "resetsAt": 9999999999}},
        }
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file),
            patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "5h:72%" in captured.out
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/mde/test_statusline.py::TestMetricsBarIntegration -v`
Expected: FAIL

- [ ] **Step 3: Modify `render.py`**

Update `src/mde/statusline/render.py`:
1. Replace `_extract_context()` with import from `schema.extract_all()`
2. Add `_ORANGE` constant and upgrade `_color_for_pct()` to 4-tier
3. Add `_osc8_link()` utility
4. In `render_statusline()`, after mode rendering, call `_render_metrics_bar()` and compose
5. Keep `_to_float` and `_to_int` for backward compat (mode renderers still use them)

Key change in `render_statusline()`:

```python
def render_statusline() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    from mde.statusline.schema import extract_all
    from mde.statusline.widget_toggle import _read_widget_config
    from mde.statusline.widgets import _render_metrics_bar

    ctx = extract_all(data)
    agents = _read_agent_state()
    mode = _read_mode()
    widget_config = _read_widget_config()

    if mode == "B":
        mode_output = _render_mode_b(ctx, agents)
    elif mode == "C":
        mode_output = _render_mode_c(ctx, agents)
    else:
        mode_output = _render_mode_a(ctx, agents)

    metrics = _render_metrics_bar(ctx, widget_config)

    if metrics:
        if mode == "C":
            output = mode_output + "\n" + metrics
        else:
            output = mode_output + " | " + metrics
    else:
        output = mode_output

    print(output)
    return 0
```

- [ ] **Step 4: Run ALL statusline tests**

Run: `uv run pytest tests/mde/ -k statusline -v`
Expected: All PASS (existing 15 + new integration tests)

- [ ] **Step 5: Lint + type check**

Run: `uv run ruff check src/mde/statusline/ --select ALL && uv run ty check src/mde/statusline/`
Expected: Zero violations

- [ ] **Step 6: Commit**

```
git add src/mde/statusline/render.py tests/mde/test_statusline.py
git commit -m "feat(statusline): integrate metrics bar into render pipeline"
```

---

## Task 11: CLI Subcommands

**Files:**
- Modify: `src/mde/cli.py`

- [ ] **Step 1: Add `toggle-widget` and `show-widgets` to the statusline parser**

In `src/mde/cli.py`, add to the statusline subparser:

```python
sl_sub.add_parser("toggle-widget", help="Toggle a widget on/off")
sl_sub.add_parser("show-widgets", help="Show widget config")
```

Add argument to `toggle-widget`:

```python
tw_p = sl_sub.add_parser("toggle-widget", help="Toggle a widget on/off")
tw_p.add_argument("widget_name", help="Widget name or 'all'")
```

Add dispatch cases in `_cmd_statusline`:

```python
if action == "toggle-widget":
    from mde.statusline.widget_toggle import toggle_widget
    return toggle_widget(args.widget_name)
if action == "show-widgets":
    from mde.statusline.widget_toggle import show_widgets
    return show_widgets()
```

- [ ] **Step 2: Test manually**

Run: `uv run mde-py statusline show-widgets`
Expected: All 7 widgets listed as `on`

Run: `uv run mde-py statusline toggle-widget token_speed`
Expected: `token_speed: on → off`

- [ ] **Step 3: Commit**

```
git add src/mde/cli.py
git commit -m "feat(statusline): add toggle-widget and show-widgets CLI subcommands"
```

---

## Task 12: Update `__init__.py` Docstring

**Files:**
- Modify: `src/mde/statusline/__init__.py`

- [ ] **Step 1: Update docstring**

```python
"""Multi-agent statusline renderer with toggleable metrics bar for Claude Code.

Subcommands:
- render: Render statusline (reads stdin JSON, outputs ANSI text)
- toggle: Cycle display mode A/B/C
- show-mode: Print current mode
- toggle-widget: Toggle individual metrics widgets on/off
- show-widgets: Print widget toggle state
"""
```

- [ ] **Step 2: Commit**

```
git add src/mde/statusline/__init__.py
git commit -m "docs(statusline): update module docstring with widget subcommands"
```

---

## Task 13: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/mde/ -k statusline -v`
Expected: All tests PASS

- [ ] **Step 2: Lint check**

Run: `uv run ruff check src/mde/statusline/ --select ALL`
Expected: Zero violations

- [ ] **Step 3: Type check**

Run: `uv run ty check src/mde/statusline/`
Expected: Zero errors

- [ ] **Step 4: Manual smoke test**

Run: `echo '{"model":{"display_name":"Opus"},"cost":{"total_cost_usd":1.23,"total_duration_ms":60000,"total_lines_added":42,"total_lines_removed":7},"context_window":{"used_percentage":42,"total_input_tokens":30000,"total_output_tokens":10000,"current_usage":{"input_tokens":8500,"cache_read_input_tokens":5000,"cache_creation_input_tokens":2000,"output_tokens":1200}}}' | uv run mde-py statusline render`
Expected: Mode A output with metrics bar including tok/s, $/min, timer, lines, cache ratio

- [ ] **Step 5: Commit any fixes and tag**

```
git add -A
git commit -m "feat(statusline): complete metrics bar implementation with 7 widgets

Adds per-widget toggleable metrics bar to the statusline renderer:
- 7 widgets: token_speed, burn_rate, block_timer, daily_totals, lines_changed, cache_ratio, rate_limits
- Schema validation with TypedDicts composing claude-agent-sdk types
- 4-tier color coding (green/yellow/orange/red)
- Rate limit display via SDK RateLimitInfo with countdown timers
- Per-widget JSON toggle config
- CLI subcommands: toggle-widget, show-widgets"
```
