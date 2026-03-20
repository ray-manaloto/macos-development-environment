# Statusline Metrics Bar — Design Spec

**Date:** 2026-03-19 (revised 2026-03-20)
**Status:** Draft (v2 — expanded scope)
**Scope:** Full bash→Python migration with per-widget toggleable metrics bar, rate limit display, and schema validation

---

## Problem

The statusline has two rendering paths: a feature-rich bash script (`~/.claude/statusline-command.sh`) and a Python renderer at `src/mde/statusline/render.py` that only handles agent state in A/B/C modes. This split means features implemented in bash (cost coloring, cache ratio, lines changed, agent name) aren't available to the Python widget system, and the bash script can't leverage Python's testability or the per-widget toggle architecture.

Additionally, Claude Code v2.1.80 added a `rate_limits` field to statusline stdin JSON (5-hour and 7-day usage windows), which neither the bash script nor the Python renderer currently displays.

## Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hybrid — metrics bar appended to active mode | Preserves existing agent display system |
| Scope | Full bash migration — 7 widgets + schema | Eliminates dual-path maintenance |
| Burn rate window | Session total (`cost / duration`) | Data already in stdin |
| Block timer source | `total_duration_ms` from stdin | Zero state |
| Daily totals persistence | Single JSON file with date key | Simple, auto-resets at midnight |
| Token speed formula | `(input + output) / (duration / 1000)` | All fields in stdin |
| Rate limits source | `rate_limits` field from stdin (v2.1.80) | No OAuth API calls needed |
| SDK dependency | `claude-agent-sdk` (PyPI) | Reuse `BaseHookInput`, `RateLimitInfo`, `RateLimitType` — stays in sync via version bumps |
| Toggle mechanism | Per-widget JSON config | Independent of A/B/C mode |
| Default state | All widgets enabled | Opt-out, not opt-in |
| Error handling | Silent defaults, never crash | Matches existing patterns |
| Schema validation | Explicit type-safe extraction with documented fields | Catches upstream changes early |
| Color tiers | 4-tier: green (<50%), yellow (50-69%), orange (70-89%), red (90%+) | Matches ecosystem consensus |
| Clickable links | OSC 8 for repo/docs links only | Cannot execute CLI commands |

---

## Architecture

### Current State (Two Paths)

```
Path 1 (bash):   stdin JSON → jq → printf ANSI → stdout
                  Features: cost, ctx%, duration, lines, cache, agent, git

Path 2 (Python):  stdin JSON → _extract_context() → _render_mode_X() → stdout
                  Features: agent count, cost, ctx% (3 modes)
```

### Proposed State (Unified Python)

```
stdin JSON → _validate_schema() → _extract_context() ─┬─ _read_mode() → _render_mode_X() ──┐
                                                       │                                      ├─ compose → stdout
                                                       └─ _read_widget_config() → _render_metrics_bar() ─┘
```

One rendering path. The bash script is replaced entirely. The Python renderer absorbs all bash features as toggleable widgets.

### Composition Rules

| Mode | Join Method | Example |
|------|-------------|---------|
| A (single-line) | ` \| ` separator | `2 agents \| $1.23 \| 42% \| 500 tok/s \| $0.75/min \| 2:05 \| +156/-23 \| cache:62% \| 5h:42% 7d:15%` |
| B (single-line) | ` \| ` separator | `42% researcher:started coder:started \| 500 tok/s \| $0.75/min \| 2:05 \| +156/-23 \| cache:62% \| 5h:42% 7d:15%` |
| C (multi-line) | New line | Metrics bar as final line of dashboard |

If all widgets are disabled, no metrics bar is appended — identical to current behavior.

---

## Stdin JSON Schema (v2.1.80)

### Schema Reference

**Primary sources (in order of authority):**

1. **Official docs**: `https://code.claude.com/docs/en/statusline` — canonical but lags behind releases
2. **Claude Agent SDK** (Python): `claude-agent-sdk` on PyPI — `claude_agent_sdk.types` defines `RateLimitInfo`, `HookInput`, etc. This is the authoritative type source for rate limits and hook events.
3. **Claude Agent SDK** (TypeScript): `@anthropic-ai/claude-agent-sdk` on npm — `sdk.d.ts` exports `SDKRateLimitInfo`, `HookEvent`, etc.
4. **Release notes**: `https://github.com/anthropics/claude-code/releases`
5. **Docs index**: `https://code.claude.com/docs/llms.txt` (67 pages)
6. **ccstatusline Zod schema**: `StatusJSON.ts` — community reference, tracks upstream closely

**Important**: The statusline stdin JSON is NOT typed in the SDK — it's a CLI-to-shell pipe interface. The SDK streams `SDKRateLimitEvent` messages via its API; the statusline gets a different `rate_limits` object in its stdin JSON. We define our own Python types for the stdin schema, using the SDK types as reference for shared structures like rate limits.

**SDK was renamed**: "Claude Code SDK" → "Claude Agent SDK". Old packages (`claude-code-sdk`, `@anthropic-ai/claude-code`) are deprecated.

### Full Schema

```json
{
  "cwd": "string",
  "session_id": "string",
  "transcript_path": "string",
  "version": "string",
  "exceeds_200k_tokens": "boolean",

  "model": {
    "id": "string",
    "display_name": "string"
  },

  "workspace": {
    "current_dir": "string",
    "project_dir": "string"
  },

  "output_style": {
    "name": "string"
  },

  "cost": {
    "total_cost_usd": "number",
    "total_duration_ms": "number",
    "total_api_duration_ms": "number",
    "total_lines_added": "number",
    "total_lines_removed": "number"
  },

  "context_window": {
    "total_input_tokens": "number",
    "total_output_tokens": "number",
    "context_window_size": "number",
    "used_percentage": "number|null",
    "remaining_percentage": "number|null",
    "current_usage": {
      "input_tokens": "number",
      "output_tokens": "number",
      "cache_creation_input_tokens": "number",
      "cache_read_input_tokens": "number"
    }
  },

  "rate_limits": {
    "type": "object — UNCONFIRMED in stdin, inferred from SDK + release notes",
    "note": "Field names may differ from SDK RateLimitInfo. Implementation must try multiple field names.",
    "possible_shape_a (SDK-aligned)": {
      "status": "allowed|allowed_warning|rejected",
      "rate_limit_type": "five_hour|seven_day|seven_day_opus|seven_day_sonnet|overage",
      "utilization": "number (0.0-1.0 fraction)",
      "resets_at": "number (Unix timestamp)"
    },
    "possible_shape_b (statusline convention)": {
      "five_hour": { "used_percentage": "number (0-100)", "resets_at": "string (ISO 8601)" },
      "seven_day": { "used_percentage": "number (0-100)", "resets_at": "string (ISO 8601)" }
    }
  },

  "vim": { "mode": "string" },
  "agent": { "name": "string" },
  "worktree": {
    "name": "string",
    "path": "string",
    "branch": "string|absent",
    "original_cwd": "string",
    "original_branch": "string|absent"
  }
}
```

### Nullability and Absence Rules

| Field | Behavior |
|-------|----------|
| `context_window.current_usage` | `null` before first API call |
| `context_window.used_percentage` | May be `null` early in session |
| `vim`, `agent`, `worktree` | Entirely absent when not applicable |
| `rate_limits` | Absent on API-key plans; present on Claude.ai subscription plans |
| `rate_limits` field structure | **UNCONFIRMED** — the SDK defines `RateLimitInfo` with `utilization` (0.0-1.0 fraction) and `resets_at` (Unix timestamp int). The statusline stdin may use different naming. Implementation must handle both SDK-style and statusline-convention field names. **Capture raw JSON to confirm before finalizing.** |

### Schema Validation Module — Option B: SDK + TypedDicts

**Dependency:** `claude-agent-sdk` (PyPI) — declared in `pyproject.toml` `[project] dependencies`:

```toml
# pyproject.toml
[project]
dependencies = [
    "pydantic>=2.10",
    "pyyaml>=6.0",
    "tomli>=2.0; python_version < '3.11'",
    "claude-agent-sdk>=0.1.49",
]
```

Per the declarative configuration policy (`.claude/rules/declarative-config.md`), all dependencies are declared in `pyproject.toml` — never via ad-hoc `uv add` commands. Lock with `uv lock` after editing.

New file `src/mde/statusline/schema.py` defines typed structures that **compose with the SDK types** where fields overlap, and hand-code the statusline-specific types that the SDK doesn't cover.

**Why Option B:**
- Reuse `BaseHookInput` (session_id, transcript_path, cwd) from the SDK — stays in sync automatically
- Reuse `RateLimitInfo`, `RateLimitStatus`, `RateLimitType` for rate limit handling — field names match the CLI's wire format
- The SDK's `RateLimitInfo.raw` dict preserves unmodeled fields for forward compatibility
- Only hand-code the statusline-specific types (`CostInfo`, `ContextWindow`, `TokenUsage`) that the SDK doesn't define
- When the SDK adds statusline types in the future, we can drop our hand-coded versions

**What the SDK provides (importable):**

```python
from claude_agent_sdk.types import (
    BaseHookInput,       # TypedDict: session_id, transcript_path, cwd
    RateLimitInfo,       # dataclass: status, resets_at (Unix int), utilization (0.0-1.0),
                         #   rate_limit_type, overage_status, raw
    RateLimitStatus,     # Literal["allowed", "allowed_warning", "rejected"]
    RateLimitType,       # Literal["five_hour", "seven_day", "seven_day_opus",
                         #         "seven_day_sonnet", "overage"]
    RateLimitEvent,      # dataclass: rate_limit_info, uuid, session_id
    SubagentStartHookInput,   # TypedDict: hook_event_name, agent_id, agent_type
    SubagentStopHookInput,    # TypedDict: hook_event_name, agent_id, agent_type, ...
)
```

**What we hand-code (statusline-specific, not in SDK):**

```python
from __future__ import annotations

from typing import Any, TypedDict
from typing_extensions import NotRequired


class ModelInfo(TypedDict):
    """Claude Code model info from statusline stdin."""
    id: NotRequired[str]
    display_name: NotRequired[str]


class CostInfo(TypedDict):
    """Session cost metrics from statusline stdin."""
    total_cost_usd: NotRequired[float]
    total_duration_ms: NotRequired[float]
    total_api_duration_ms: NotRequired[float]
    total_lines_added: NotRequired[int]
    total_lines_removed: NotRequired[int]


class TokenUsage(TypedDict):
    """Per-turn token breakdown from context_window.current_usage."""
    input_tokens: NotRequired[int]
    output_tokens: NotRequired[int]
    cache_creation_input_tokens: NotRequired[int]
    cache_read_input_tokens: NotRequired[int]


class ContextWindow(TypedDict):
    """Context window metrics from statusline stdin."""
    context_window_size: NotRequired[int | None]
    total_input_tokens: NotRequired[int | None]
    total_output_tokens: NotRequired[int | None]
    current_usage: NotRequired[TokenUsage | None]
    used_percentage: NotRequired[float | None]
    remaining_percentage: NotRequired[float | None]


class WorkspaceInfo(TypedDict):
    """Workspace paths from statusline stdin."""
    current_dir: NotRequired[str]
    project_dir: NotRequired[str]


class WorktreeInfo(TypedDict):
    """Worktree info, absent outside --worktree sessions."""
    name: str
    path: str
    branch: NotRequired[str]
    original_cwd: str
    original_branch: NotRequired[str]


class StatuslineInput(TypedDict):
    """Complete statusline stdin JSON schema (v2.1.80).

    Extends the pattern from claude_agent_sdk.types.BaseHookInput
    for the shared session_id/transcript_path/cwd fields.
    Statusline-specific fields are defined here since the SDK
    does not type the statusline stdin protocol.
    """
    # Shared with BaseHookInput
    session_id: NotRequired[str]
    transcript_path: NotRequired[str]
    cwd: NotRequired[str]

    # Statusline-specific
    model: NotRequired[str | ModelInfo]
    workspace: NotRequired[WorkspaceInfo]
    version: NotRequired[str]
    output_style: NotRequired[dict[str, str]]
    cost: NotRequired[CostInfo]
    context_window: NotRequired[ContextWindow | None]
    exceeds_200k_tokens: NotRequired[bool]
    rate_limits: NotRequired[dict[str, Any]]  # Shape unconfirmed, use SDK RateLimitInfo for parsing
    vim: NotRequired[dict[str, str] | None]
    agent: NotRequired[dict[str, str]]
    worktree: NotRequired[WorktreeInfo]
```

**Schema version detection** — log a warning for unknown top-level keys:

```python
_KNOWN_KEYS = frozenset(StatuslineInput.__annotations__.keys())

def _warn_unknown_keys(data: dict[str, Any]) -> None:
    unknown = set(data.keys()) - _KNOWN_KEYS
    if unknown:
        import sys
        print(f"[statusline] unknown keys: {unknown}", file=sys.stderr)
```

This replaces `_extract_context()` and `_extract_widget_context()` with a single typed extraction point. Benefits:
- SDK types stay in sync: bump version pin in `pyproject.toml` `[project] dependencies`, then `uv lock`
- TypedDicts give IDE autocompletion and type checker support
- `_warn_unknown_keys` alerts us when upstream adds new fields
- Forward-compatible: `rate_limits` uses `dict[str, Any]` until the stdin shape is confirmed, parsed via SDK's `RateLimitInfo` pattern
- Numeric string coercion: handles `"1.25"` as `1.25` (ccstatusline pattern)

---

## Widget Specifications

Each widget is a pure function: `(ctx: dict[str, object]) -> str`

### 7 Widgets

#### 1. token_speed

- **Input:** `context_window.total_input_tokens`, `context_window.total_output_tokens`, `cost.total_duration_ms` (flattened in `extract_all()` as `total_input_tokens`, `total_output_tokens`, `total_duration_ms`)
- **Formula:** `(input + output) / (duration_ms / 1000)`
- **Output:** `"{int} tok/s"` or `"— tok/s"` when duration is 0
- **Edge cases:**
  - Missing/null fields default to 0 via `_to_float`
  - Duration is 0 but tokens are present → `"— tok/s"` (division guard takes precedence)
  - Tokens are 0 but duration is present → `"0 tok/s"` (valid: no tokens processed yet)

#### 2. burn_rate

- **Input:** `total_cost_usd`, `total_duration_ms`
- **Formula:** `cost / (duration_ms / 60000)`
- **Output:** `"${rate:.2f}/min"` or `"$0.00/min"` when duration is 0
- **Edge cases:** Missing cost defaults to 0.0

#### 3. block_timer

- **Input:** `total_duration_ms`
- **Formula:** Format milliseconds as `M:SS` (no leading zero on minutes) or `H:MM:SS` when >= 3600000ms
- **Output:** `"2:05"` for 125s, `"1:02:05"` for 3725s, `"59:59"` for 3599s
- **Format change from bash:** The bash script uses `Xs`/`Xm`/`XhYm` format (e.g., `5m`, `1h23m`). The Python widget uses `M:SS`/`H:MM:SS` for precision. This is an intentional improvement, not a bug.
- **Edge cases:** 0 or missing → `"0:00"`

#### 4. daily_totals

- **Input:** `total_cost_usd`, `total_input_tokens`, `total_output_tokens`
- **Persistence:** `.artifacts/daily-totals.json` (CWD-relative, same as `.artifacts/statusline-mode`). This means daily totals are per-project. A user working across multiple projects will have separate daily totals per project. This is intentional — it matches the per-project convention of all other `.artifacts/` files.
- **Schema:**
  ```json
  {"date": "2026-03-19", "total_cost_usd": 4.50, "total_tokens": 120000}
  ```
- **Logic:** Read file → if date matches today, add current session values → write back. If date is stale or file missing/corrupt, start fresh from current session values.
- **Atomicity:** Non-atomic read-modify-write. Acceptable for single-user local tool — matches `toggle.py` write pattern. Concurrent renders may produce slightly stale totals; this is tolerable since daily totals are approximate by nature.
- **Output:** `"day: ${cost:.2f} {tokens}k tok"` — tokens are floor-divided by 1000 (`total // 1000`). Values under 1000 display as `0k`.
- **Edge cases:** Missing/corrupt file → create fresh; stale date → reset

#### 5. lines_changed (NEW — from bash script)

- **Input:** `total_lines_added`, `total_lines_removed`
- **Output:** `"+156/-23"` — green for added, red for removed (ANSI colored)
- **Edge cases:** Both 0 → widget returns empty string (suppressed from bar). Only additions → `"+156"`. Only removals → `"-23"` (no leading slash — the `/` separator is only present when both sides are shown).
- **Bash equivalent:** Lines 100-108 of `statusline-command.sh`

#### 6. cache_ratio (NEW — from bash script)

- **Input:** `current_usage.cache_read_input_tokens`, `current_usage.cache_creation_input_tokens`, `current_usage.input_tokens`
- **Formula:** `cache_read / (input + cache_read + cache_create) * 100`
- **Output:** `"cache:62%"` — color-coded: green (>60%), yellow (30-60%), red (<30%)
- **Edge cases:** `current_usage` is `null` (before first API call) → widget returns empty string (suppressed). All values 0 → suppressed.
- **Bash equivalent:** Lines 110-124 of `statusline-command.sh`

#### 7. rate_limits (NEW — v2.1.80)

- **Input:** Rate limit data from `rate_limits` field in stdin JSON
- **SDK reference type:** `claude_agent_sdk.types.RateLimitInfo` — uses `utilization` (0.0-1.0), `resets_at` (Unix timestamp int), `rate_limit_type` (Literal), `status` (Literal)
- **Output:** `"5h:42% 7d:15%"` — each color-coded with 4-tier thresholds
- **Color tiers:** green (<50%), yellow (50-69%), orange (70-89%), red (90%+)
- **Reset time:** When either window is >=70%, append relative countdown: `"5h:85% ↻2h13m 7d:15%"`
- **Rate limit types (from SDK):** `five_hour`, `seven_day`, `seven_day_opus`, `seven_day_sonnet`, `overage`
  - Display `five_hour` and the most relevant `seven_day*` variant for the current model
  - Show `overage` status if present and `is_using_overage` is true
- **Data extraction:** The stdin `rate_limits` field structure is unconfirmed. Implementation must try:
  1. SDK-aligned: `rate_limits.utilization` (0.0-1.0) → multiply by 100 for display
  2. Statusline-convention: `rate_limits.five_hour.used_percentage` (0-100)
  3. Nested: `rate_limits.five_hour.utilization` (0.0-1.0)
  - For `resets_at`: try `int` (Unix timestamp) first, then `str` (ISO 8601)
- **Edge cases:**
  - `rate_limits` absent (API-key users) → widget returns empty string (suppressed)
  - `rate_limits.status == "rejected"` → show `"5h:LIMIT"` in red
  - `rate_limits.status == "allowed_warning"` → force orange/red color regardless of percentage
  - Unknown rate_limit_type → skip that window
  - `resets_at` parsing failure → omit countdown, show percentage only
- **Schema uncertainty:** The `rate_limits` field is confirmed in v2.1.80 release notes but NOT yet documented at code.claude.com. **Capture raw JSON from a live v2.1.80 session to confirm field names before finalizing implementation.** A capture script is prepared at `/tmp/capture-statusline.py`.

### Widget Suppression

Widgets that return an empty string are automatically suppressed from the metrics bar. This means:
- `lines_changed` disappears when no lines have been changed
- `cache_ratio` disappears before the first API call
- `rate_limits` disappears for API-key users
- The bar shrinks/grows dynamically based on available data

### 4-Tier Color Function

Replace the existing 2-tier `_color_for_pct` with a 4-tier version:

```python
_ORANGE = "\033[38;5;208m"  # 256-color orange (no standard ANSI orange)

def _color_for_pct(pct: float) -> str:
    if pct >= 90:
        return _RED
    if pct >= 70:
        return _ORANGE
    if pct >= 50:
        return _YELLOW
    return _GREEN
```

This is a breaking change to the existing function signature (same name, different thresholds). The 3 integration tests that check color output will need updating.

---

## Context Extraction (Unified)

Replace both `_extract_context()` and the proposed `_extract_widget_context()` with a single validated extraction in `schema.py` that uses the SDK types:

```python
from claude_agent_sdk.types import RateLimitInfo, RateLimitStatus

def extract_all(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and validate all fields from Claude Code stdin JSON.

    Uses StatuslineInput TypedDict for structure, SDK's RateLimitInfo
    for rate limit parsing. Returns a flat dict consumed by both mode
    renderers and widgets.
    """
    _warn_unknown_keys(data)

    cost = _safe_dict(data.get("cost"))
    ctx = _safe_dict(data.get("context_window"))
    usage = _safe_dict(ctx.get("current_usage")) if isinstance(ctx.get("current_usage"), dict) else {}

    # Parse rate limits using SDK's field naming convention
    rate_info = _parse_rate_limits(data.get("rate_limits"))

    return {
        # Existing mode renderer fields
        "model": _safe_str(data, "model.display_name", "unknown"),
        "cost_usd": _coerce_float(cost.get("total_cost_usd")),
        "context_pct": _coerce_float(ctx.get("used_percentage")),

        # Widget fields
        "total_cost_usd": _coerce_float(cost.get("total_cost_usd")),
        "total_duration_ms": _coerce_float(cost.get("total_duration_ms")),
        "total_api_duration_ms": _coerce_float(cost.get("total_api_duration_ms")),
        "total_input_tokens": _coerce_float(ctx.get("total_input_tokens")),
        "total_output_tokens": _coerce_float(ctx.get("total_output_tokens")),
        "total_lines_added": _coerce_int(cost.get("total_lines_added")),
        "total_lines_removed": _coerce_int(cost.get("total_lines_removed")),

        # Cache fields
        "cache_read_tokens": _coerce_float(usage.get("cache_read_input_tokens")),
        "cache_create_tokens": _coerce_float(usage.get("cache_creation_input_tokens")),
        "input_tokens": _coerce_float(usage.get("input_tokens")),

        # Rate limit fields — parsed via SDK RateLimitInfo pattern
        "rate_5h": rate_info.get("five_hour"),   # RateLimitInfo | None
        "rate_7d": rate_info.get("seven_day"),   # RateLimitInfo | None
        "rate_overage": rate_info.get("overage"), # RateLimitInfo | None

        # Metadata
        "exceeds_200k": bool(data.get("exceeds_200k_tokens", False)),
        "agent_name": _safe_str(data, "agent.name", ""),
        "version": str(data.get("version", "")),
    }


def _parse_rate_limits(raw: Any) -> dict[str, RateLimitInfo | None]:
    """Parse rate_limits from stdin JSON into SDK RateLimitInfo objects.

    The CLI sends camelCase on the wire (rateLimitType, resetsAt, isUsingOverage).
    The SDK's RateLimitInfo expects snake_case. This function handles both,
    mirroring the SDK's own parser (see claude-agent-sdk commit 2d5c3cb3).

    Confirmed wire format from SDK e2e test:
        status: "allowed_warning"
        resets_at / resetsAt: 1773273600 (Unix timestamp int)
        rate_limit_type / rateLimitType: "seven_day"
        utilization: 0.62 (0.0-1.0 fraction)
    """
    if not isinstance(raw, dict):
        return {"five_hour": None, "seven_day": None, "overage": None}

    result: dict[str, RateLimitInfo | None] = {}

    # The statusline stdin may deliver rate_limits as:
    #   Shape A: {"status": "...", "rateLimitType": "five_hour", "utilization": 0.42, ...}
    #   Shape B: {"five_hour": {"utilization": 0.42, ...}, "seven_day": {...}}
    # Try Shape B first (nested by window), fall back to Shape A (flat)

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
        # Normalize model-specific types to base window
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

**Rate limit display in widgets** uses SDK types directly:

```python
from claude_agent_sdk.types import RateLimitInfo

def rate_limits_widget(ctx: dict[str, Any]) -> str:
    parts = []
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
                text += f" ↻{_format_countdown(info.resets_at)}"
            parts.append(f"{color}{text}{_RESET}")
    return " ".join(parts)
```

The `_coerce_float` function handles numeric strings (`"1.25"` → `1.25`), `None` → `0.0`, and invalid values → `0.0`. This is the ccstatusline `CoercedNumberSchema` pattern adapted to Python.

---

## Toggle System

### State File

**Path:** `.artifacts/statusline-widgets.json`

```json
{
    "token_speed": true,
    "burn_rate": true,
    "block_timer": true,
    "daily_totals": true,
    "lines_changed": true,
    "cache_ratio": true,
    "rate_limits": true
}
```

### Read Logic

```python
_ALL_WIDGETS = [
    "token_speed", "burn_rate", "block_timer", "daily_totals",
    "lines_changed", "cache_ratio", "rate_limits",
]

def _read_widget_config() -> dict[str, bool]:
    """Read per-widget toggles, defaulting all to True."""
    try:
        data = json.loads(_WIDGET_CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    return {name: bool(data.get(name, True)) for name in _ALL_WIDGETS}
```

### CLI Subcommands

| Command | Action |
|---------|--------|
| `uv run mde-py statusline toggle-widget <name>` | Flip one widget on/off |
| `uv run mde-py statusline toggle-widget all` | If any widget is on, turn all off; if all are off, turn all on |
| `uv run mde-py statusline show-widgets` | Print widget config table |

**Valid widget names:** `token_speed`, `burn_rate`, `block_timer`, `daily_totals`, `lines_changed`, `cache_ratio`, `rate_limits`, `all`

---

## Bash Script Retirement

### Migration Mapping

| Bash Feature (line #) | Python Widget | Notes |
|----------------------|---------------|-------|
| Cost color coding (52-64) | Existing mode renderer + 4-tier colors | Upgrade from 2-tier |
| Context % color (67-81) | Existing mode renderer + 4-tier colors | Upgrade from 2-tier |
| `>200k` warning (77-79) | Mode renderer (add `exceeds_200k` flag) | New indicator |
| Duration formatting (84-97) | `block_timer` widget | Already in spec |
| Lines +/- (100-108) | `lines_changed` widget | New |
| Cache ratio (110-124) | `cache_ratio` widget | New |
| Agent name (127-129) | Mode renderer (already shows agent info) | Already handled |
| Active subagent count (132-148) | Mode renderer (already reads JSONL) | Already handled |
| Git branch + dirty (10-18, 26-31) | **NOT migrated** — stays in bash or separate widget in v2 | Git requires subprocess calls that add latency |

### Post-Migration

After the Python renderer is complete and verified:
1. Update `~/.claude/settings.json` statusline command to: `uv run mde-py statusline render`
2. Archive `~/.claude/statusline-command.sh` (don't delete — user may want to reference)
3. The global statusline config change is a **user action**, not automated

### Git Branch Decision

Git branch/status display requires `subprocess` calls (`git branch --show-current`, `git status --porcelain`) which add 50-200ms latency per render. The bash script already handles this. Options:
- Omit from v1 (keep bash for git-only display)
- Add as opt-in widget with caching (v2)
- Accept latency since statusline debounces at 300ms anyway

**Decision: Omit from v1.** The existing bash script's git display works well. If the user wants git info AND the new metrics, they can chain scripts. Full git integration is a v2 item.

---

## OSC 8 Clickable Links

OSC 8 escape sequences make text Cmd+clickable (macOS) / Ctrl+clickable (Linux):

```python
def _osc8_link(url: str, text: str) -> str:
    return f"\033]8;;{url}\a{text}\033]8;;\a"
```

**Supported uses:**
- Repo link in Mode C dashboard (clickable repo name → GitHub)
- Version indicator → release notes URL
- Session transcript path → `file://` link to transcript

**NOT supported:**
- Widget toggle via click — OSC 8 only opens URLs, cannot execute CLI commands
- Any action that requires shell execution

**Terminal compatibility:**
- Works: iTerm2, Kitty, WezTerm
- Does NOT work: Terminal.app (macOS default)
- May be stripped: SSH, tmux (config-dependent)

Add `_osc8_link()` as a utility in `render.py`. Usage is optional — widgets that want clickable text call it, others don't. No widget toggle functionality through links.

---

## Error Handling

Matches existing statusline conventions: silent defaults, return 0 always, never block Claude Code.

| Failure | Behavior |
|---------|----------|
| `statusline-widgets.json` missing | All widgets enabled |
| `statusline-widgets.json` corrupt | All widgets enabled |
| `daily-totals.json` missing | Create fresh from current session |
| `daily-totals.json` corrupt | Overwrite with current session |
| Widget receives `None`/missing fields | `_coerce_float` returns `0.0` |
| Division by zero (duration=0) | Guard returns dash or `$0.00` |
| `rate_limits` absent from stdin | Widget returns empty string (suppressed) |
| `rate_limits` field names differ | Try both `used_percentage` and `utilization` |
| `resets_at` unparseable | Omit countdown, show percentage only |
| Numeric string in JSON (`"1.25"`) | `_coerce_float` handles coercion |
| Unknown widget name in `toggle-widget` | Print error, return 1 |

---

## File Manifest

### New Files

| File | Purpose |
|------|---------|
| `src/mde/statusline/schema.py` | `StatuslineInput` TypedDict, `CostInfo`, `ContextWindow`, `TokenUsage`, `ModelInfo`, `WorkspaceInfo`, `WorktreeInfo` TypedDicts; `extract_all()`, `_parse_rate_limits()`, `_warn_unknown_keys()`, `_coerce_float()`, `_coerce_int()`, `_safe_dict()` |
| `src/mde/statusline/widgets.py` | 7 widget functions + `_render_metrics_bar()` |
| `src/mde/statusline/widget_toggle.py` | `_read_widget_config()`, `toggle_widget()`, `show_widgets()` |
| `tests/mde/test_statusline_schema.py` | Schema validation tests (coercion, nulls, absent fields, forward compat) |
| `tests/mde/test_statusline_widgets.py` | Unit tests for all 7 widgets + metrics bar composition |
| `tests/mde/test_widget_toggle.py` | Toggle read/write/cycle + CLI integration tests |

### Modified Files

| File | Change |
|------|--------|
| `src/mde/statusline/render.py` | Replace `_extract_context()` with `schema.extract_all()`; add `_render_metrics_bar()` call; upgrade `_color_for_pct()` to 4-tier; add `_osc8_link()` utility |
| `src/mde/statusline/__init__.py` | Updated docstring |
| `src/mde/cli.py` | Add `toggle-widget` and `show-widgets` subcommands |

### Unchanged Files

- `src/mde/statusline/toggle.py` — A/B/C cycling untouched
- `src/mde/hooks/log_agent_event.py` — agent logging untouched
- `.claude/settings.json` — no new hooks needed

### Existing Test Impact

The 4-tier color upgrade changes `_color_for_pct` thresholds (50/80 → 50/70/90). However, **none of the 15 existing tests assert on ANSI color codes** — they only assert on semantic content (`"2 agents"`, `"$1.23"`, `"65%"`). Therefore, **all existing tests pass without modification** despite the color threshold change. New tests should explicitly cover the 4-tier boundaries.

---

## Testing Plan

### Unit Tests — `tests/mde/test_statusline_schema.py` (NEW)

| Test | Assertion |
|------|-----------|
| `test_extract_all_full_schema` | All fields extracted from complete v2.1.80 JSON |
| `test_extract_all_minimal` | Empty dict → all defaults |
| `test_coerce_float_from_string` | `"1.25"` → `1.25` |
| `test_coerce_float_from_none` | `None` → `0.0` |
| `test_coerce_float_from_invalid` | `"not-a-number"` → `0.0` |
| `test_rate_limits_absent` | Missing `rate_limits` → all `None` |
| `test_rate_limits_shape_b_nested` | `{"five_hour": {"utilization": 0.42, ...}}` → `RateLimitInfo` with correct fields |
| `test_rate_limits_shape_a_flat` | `{"status": "allowed", "rateLimitType": "five_hour", ...}` → parsed correctly |
| `test_rate_limits_camel_to_snake` | `resetsAt` → `resets_at`, `rateLimitType` → `rate_limit_type` |
| `test_rate_limits_model_specific_type` | `seven_day_opus` → normalized to `seven_day` key |
| `test_current_usage_null` | `current_usage: null` → cache fields default to 0.0 |
| `test_unknown_fields_warns_stderr` | Extra top-level keys → warning printed to stderr |
| `test_unknown_fields_no_crash` | Extra fields don't crash extraction |

### Unit Tests — `tests/mde/test_statusline_widgets.py`

Per widget: normal case, zero/missing fields, edge cases.

| Test | Assertion |
|------|-----------|
| `test_token_speed_normal` | `500 tok/s` for 30k tokens in 60s |
| `test_token_speed_zero_duration` | `— tok/s` |
| `test_token_speed_missing_fields` | `— tok/s` (duration defaults to 0, triggers guard) |
| `test_token_speed_zero_tokens_with_duration` | `0 tok/s` (valid: no tokens yet) |
| `test_burn_rate_normal` | `$1.50/min` for $1.50 in 60s |
| `test_burn_rate_zero_duration` | `$0.00/min` |
| `test_block_timer_normal` | `2:05` for 125000ms |
| `test_block_timer_over_hour` | `1:02:05` for 3725000ms |
| `test_block_timer_zero` | `0:00` |
| `test_daily_totals_fresh` | Creates file, returns correct string |
| `test_daily_totals_accumulates` | Adds to existing same-day totals |
| `test_daily_totals_resets_on_new_day` | Stale date resets to current values |
| `test_daily_totals_corrupt_file` | Overwrites, returns current values |
| `test_lines_changed_both` | `+156/-23` |
| `test_lines_changed_add_only` | `+156` |
| `test_lines_changed_remove_only` | `-23` (no slash — standalone) |
| `test_lines_changed_both_zero` | Empty string (suppressed) |
| `test_cache_ratio_normal` | `cache:62%` for 620 read / 1000 total |
| `test_cache_ratio_no_usage` | Empty string (suppressed, current_usage null) |
| `test_cache_ratio_all_zero` | Empty string (suppressed) |
| `test_rate_limits_normal` | `RateLimitInfo(utilization=0.42)` → `5h:42%` |
| `test_rate_limits_both_windows` | Both `rate_5h` and `rate_7d` present → `5h:42% 7d:15%` |
| `test_rate_limits_high_with_countdown` | `utilization=0.85, resets_at=<future>` → `5h:85% ↻2h13m` |
| `test_rate_limits_absent` | Both `None` → empty string (suppressed) |
| `test_rate_limits_rejected` | `status="rejected"` → `5h:LIMIT` in red |
| `test_rate_limits_allowed_warning` | `status="allowed_warning"` → forced orange/red color |
| `test_rate_limits_countdown_format` | Unix timestamp → `↻Xh Ym` relative format |
| `test_metrics_bar_all_enabled` | All 7 widgets joined by ` \| ` |
| `test_metrics_bar_some_disabled` | Only enabled widgets appear |
| `test_metrics_bar_all_disabled` | Returns empty string |
| `test_metrics_bar_suppresses_empty_widgets` | Widgets returning `""` don't produce extra separators |

### Unit Tests — `tests/mde/test_widget_toggle.py`

| Test | Assertion |
|------|-----------|
| `test_read_config_defaults_all_true` | Missing file → all 7 enabled |
| `test_read_config_corrupt_defaults` | Invalid JSON → all enabled |
| `test_toggle_widget_flips` | `on → off`, `off → on` |
| `test_toggle_all_any_on_turns_all_off` | Mixed state → all off |
| `test_toggle_all_all_off_turns_all_on` | All off → all on |
| `test_show_widgets_output` | Correct table format for 7 widgets |
| `test_unknown_widget_name` | Returns error, exit code 1 |

### Integration Tests — `tests/mde/test_statusline.py` (new tests added)

Integration tests must patch all state file paths to `tmp_path`, following the existing pattern:
- `_MODE_FILE` and `_AGENT_STATE_FILE` (from `render.py`) — already patched in existing tests
- `_WIDGET_CONFIG_FILE` (from `widget_toggle.py`) — new
- `_DAILY_TOTALS_FILE` (from `widgets.py`) — new, required for any test that exercises the `daily_totals` widget

| Test | Assertion |
|------|-----------|
| `test_mode_a_with_metrics_bar` | Mode A output + ` \| ` + widget output |
| `test_mode_c_with_metrics_bar` | Dashboard + metrics on final line |
| `test_mode_a_all_widgets_disabled` | Output identical to current Mode A |
| `test_4_tier_color_at_85_pct` | 85% → orange (not red) |
| `test_rate_limits_in_full_render` | Full render includes rate limit display |

### Test Commands

```
uv run pytest tests/mde/test_statusline_schema.py -v
uv run pytest tests/mde/test_statusline_widgets.py -v
uv run pytest tests/mde/test_widget_toggle.py -v
uv run pytest tests/mde/test_statusline.py -v
uv run pytest tests/mde/ -k statusline -v          # all statusline tests
```

---

## Success Criteria

1. All 7 widgets render correct output for normal and edge-case inputs
2. Per-widget toggles work independently of A/B/C mode cycling
3. Metrics bar appends cleanly to all 3 existing modes
4. Daily totals persist across sessions and reset at midnight
5. Rate limits display when `rate_limits` field is present in stdin
6. Schema validation handles coercion, nulls, and absent fields gracefully
7. Empty widgets are suppressed (no extra separators)
8. All existing tests pass (with 4-tier color threshold updates)
9. `uv run ruff check src/mde/statusline/ --select ALL` — zero violations
10. `uv run ty check src/mde/statusline/` — zero type errors
11. `uv run mde-py statusline render` produces functionally equivalent output to `~/.claude/statusline-command.sh` for the same stdin JSON, with these intentional differences: no git branch display, `M:SS` timer format instead of `Xm`, and 4-tier color thresholds instead of 3-tier

---

## Ecosystem References

| Project | Language | Stars | Key Pattern Adopted |
|---------|----------|-------|-------------------|
| [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) | Python | Official | `RateLimitInfo`, `BaseHookInput`, `SubagentStartHookInput` types imported directly |
| [ccstatusline](https://github.com/sirmalloc/ccstatusline) | TypeScript | 5.5k | Zod schema validation → Python `_coerce_float` pattern |
| [CCometixLine](https://github.com/Haleclipse/CCometixLine) | Rust | 2.2k | 4-tier color coding |
| [ClaudeCodeStatusLine](https://github.com/daniel3303/ClaudeCodeStatusLine) | Shell | 330 | Rate limit display with countdown timer |
| [pyccsl](https://github.com/wolfdenpublishing/pyccsl) | Python | 81 | Zero-dep Python, cache ratio, structured exit codes |
| [claude-statusline-lite](https://github.com/simplpear/claude-statusline-lite) | Python | 13 | Unicode bar for quota visualization |
