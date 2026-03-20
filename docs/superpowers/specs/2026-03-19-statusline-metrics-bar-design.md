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

### Schema Validation Module

New file `src/mde/statusline/schema.py`:

```python
def validate_statusline_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize Claude Code stdin JSON.

    Returns a flat dict with all widget-relevant fields, safely
    extracted with type checking and defaults. Unknown fields
    are preserved in a 'raw' key for forward compatibility.
    """
```

This replaces `_extract_context()` and `_extract_widget_context()` with a single extraction point. All widgets read from this validated dict. Benefits:
- Single place to update when upstream schema changes
- Type-safe: every field is explicitly checked (not just `.get()` with hope)
- Forward-compatible: unknown fields preserved, never crash on new fields
- Numeric string coercion: handles `"1.25"` as `1.25` (ccstatusline pattern — Claude Code may send stringified numbers)

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

Replace both `_extract_context()` and the proposed `_extract_widget_context()` with a single validated extraction in `schema.py`:

```python
def extract_all(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and validate all fields from Claude Code stdin JSON.

    Returns a flat dict consumed by both mode renderers and widgets.
    """
    cost = _safe_dict(data.get("cost"))
    ctx = _safe_dict(data.get("context_window"))
    usage = _safe_dict(ctx.get("current_usage")) if ctx.get("current_usage") else {}
    rate = _safe_dict(data.get("rate_limits"))
    five_h = _safe_dict(rate.get("five_hour"))
    seven_d = _safe_dict(rate.get("seven_day"))

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

        # Rate limit fields (v2.1.80) — handle SDK-style and statusline-convention names
        # SDK uses utilization (0.0-1.0), statusline may use used_percentage (0-100)
        # SDK uses resets_at as Unix timestamp (int), statusline may use ISO 8601 (str)
        "rate_5h_pct": _normalize_rate_pct(five_h),  # Always returns 0-100
        "rate_5h_resets_at": five_h.get("resets_at"),  # int or str, handled downstream
        "rate_5h_status": five_h.get("status", ""),
        "rate_7d_pct": _normalize_rate_pct(seven_d),
        "rate_7d_resets_at": seven_d.get("resets_at"),
        "rate_7d_status": seven_d.get("status", ""),
        "rate_overage_status": _safe_dict(rate.get("overage", rate)).get("overage_status", ""),

        # Metadata
        "exceeds_200k": bool(data.get("exceeds_200k_tokens", False)),
        "agent_name": _safe_str(data, "agent.name", ""),
        "version": str(data.get("version", "")),
    }
```

The `_coerce_float` function handles numeric strings (`"1.25"` → `1.25`), `None` → `0.0`, and invalid values → `0.0`. This is the ccstatusline `CoercedNumberSchema` pattern adapted to Python.

The `_normalize_rate_pct` function resolves the schema uncertainty for rate limits:
```python
def _normalize_rate_pct(window: dict[str, Any]) -> float:
    """Extract rate limit percentage, normalizing SDK vs statusline conventions.

    SDK uses 'utilization' (0.0-1.0). Statusline may use 'used_percentage' (0-100).
    Returns 0-100 always.
    """
    # Try used_percentage first (0-100 range)
    pct = _coerce_float(window.get("used_percentage"))
    if pct > 0:
        return pct
    # Fall back to utilization (0.0-1.0 range) → convert to percentage
    util = _coerce_float(window.get("utilization"))
    return util * 100 if util <= 1.0 else util  # Guard against already-percentage values
```

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
| `src/mde/statusline/schema.py` | `extract_all()`, `_coerce_float()`, `_coerce_int()`, `_safe_dict()` (returns `{}` for `None`, non-dict, or absent values), schema constants |
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
| `test_rate_limits_absent` | Missing `rate_limits` → `rate_5h_pct` = 0.0 |
| `test_rate_limits_with_utilization_key` | `utilization` (API name) → correctly mapped |
| `test_rate_limits_with_used_percentage_key` | `used_percentage` (expected name) → correctly mapped |
| `test_current_usage_null` | `current_usage: null` → cache fields default to 0.0 |
| `test_unknown_fields_preserved` | Extra fields don't crash extraction |

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
| `test_rate_limits_normal` | `5h:42% 7d:15%` |
| `test_rate_limits_high_with_countdown` | `5h:85% ↻2h13m 7d:15%` |
| `test_rate_limits_absent` | Empty string (suppressed) |
| `test_rate_limits_utilization_key` | SDK-style `utilization` (0.42) → displays as `42%` |
| `test_rate_limits_rejected_status` | `status: "rejected"` → shows `5h:LIMIT` in red |
| `test_rate_limits_resets_at_unix` | Unix timestamp int → correct countdown |
| `test_rate_limits_resets_at_iso` | ISO 8601 string → correct countdown |
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
| [ccstatusline](https://github.com/sirmalloc/ccstatusline) | TypeScript | 5.5k | Zod schema validation → Python `_coerce_float` pattern |
| [CCometixLine](https://github.com/Haleclipse/CCometixLine) | Rust | 2.2k | 4-tier color coding |
| [ClaudeCodeStatusLine](https://github.com/daniel3303/ClaudeCodeStatusLine) | Shell | 330 | Rate limit display with countdown timer |
| [pyccsl](https://github.com/wolfdenpublishing/pyccsl) | Python | 81 | Zero-dep Python, cache ratio, structured exit codes |
| [claude-statusline-lite](https://github.com/simplpear/claude-statusline-lite) | Python | 13 | Unicode bar for quota visualization |
