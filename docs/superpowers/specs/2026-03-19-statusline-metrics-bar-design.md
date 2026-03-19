# Statusline Metrics Bar — Design Spec

**Date:** 2026-03-19
**Status:** Draft
**Scope:** Add a per-widget toggleable metrics bar to the existing statusline renderer

---

## Problem

The statusline shows agent state, cost, and context % but lacks real-time performance metrics. Users want to see token throughput, spend rate, session duration, and daily cumulative totals without losing the existing A/B/C mode functionality.

## Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hybrid — metrics bar appended to active mode | Preserves existing system, zero regression risk |
| Burn rate window | Session total (`cost / duration`) | Data already in stdin, no persistence needed |
| Block timer source | `total_duration_ms` from stdin | Zero state, already available |
| Daily totals persistence | Single JSON file with date key | Simple, auto-resets at midnight |
| Token speed formula | `(input + output) / (duration / 1000)` | All fields available in stdin |
| Toggle mechanism | Per-widget JSON config | Independent of A/B/C mode, future-proof |
| Default state | All widgets enabled | Opt-out, not opt-in |
| Error handling | Silent defaults, never crash | Matches existing statusline patterns |

---

## Architecture

### Current Rendering Pipeline

```
stdin JSON → _extract_context() → _read_mode() → _render_mode_X() → stdout
```

### Proposed Rendering Pipeline

```
stdin JSON → _extract_context() ─┬─ _read_mode() → _render_mode_X() ──┐
                                 │                                      ├─ compose → stdout
                                 └─ _read_widget_config() → _render_metrics_bar() ─┘
```

Two independent rendering paths joined at composition. The existing mode pipeline is unchanged. The metrics bar reads the same `ctx` dict plus its own widget config.

### Composition Rules

| Mode | Join Method | Example |
|------|-------------|---------|
| A (single-line) | ` \| ` separator | `2 agents \| $1.23 \| 42% \| 500 tok/s \| $1.25/min \| 2:05 \| day: $4.50 120k tok` |
| B (single-line) | ` \| ` separator | `42% researcher:started coder:started \| 500 tok/s \| $1.25/min \| 2:05 \| day: $4.50 120k tok` |
| C (multi-line) | New line | Metrics bar as final line of dashboard |

If all widgets are disabled, no metrics bar is appended — output is identical to current behavior.

---

## Widget Specifications

Each widget is a pure function: `(ctx: dict[str, object]) -> str`

### token_speed

- **Input:** `total_input_tokens`, `total_output_tokens`, `total_duration_ms`
- **Formula:** `(input + output) / (duration_ms / 1000)`
- **Output:** `"{int} tok/s"` or `"— tok/s"` when duration is 0
- **Edge cases:**
  - Missing/null fields default to 0 via `_to_float`
  - Duration is 0 but tokens are present → `"— tok/s"` (division guard takes precedence)
  - Tokens are 0 but duration is present → `"0 tok/s"` (valid: no tokens processed yet)

### burn_rate

- **Input:** `total_cost_usd`, `total_duration_ms`
- **Formula:** `cost / (duration_ms / 60000)`
- **Output:** `"${rate:.2f}/min"` or `"$0.00/min"` when duration is 0
- **Edge cases:** Missing cost defaults to 0.0

### block_timer

- **Input:** `total_duration_ms`
- **Formula:** Format milliseconds as `M:SS` (no leading zero on minutes) or `H:MM:SS` when >= 3600000ms
- **Output:** `"2:05"` for 125s, `"1:02:05"` for 3725s, `"59:59"` for 3599s
- **Edge cases:** 0 or missing → `"0:00"`

### daily_totals

- **Input:** `total_cost_usd`, `total_input_tokens`, `total_output_tokens`
- **Persistence:** `.artifacts/daily-totals.json`
- **Schema:**
  ```json
  {"date": "2026-03-19", "total_cost_usd": 4.50, "total_tokens": 120000}
  ```
- **Logic:** Read file → if date matches today, add current session values → write back. If date is stale or file missing/corrupt, start fresh from current session values.
- **Atomicity:** Non-atomic read-modify-write. Acceptable for single-user local tool — matches `toggle.py` write pattern. Concurrent renders may produce slightly stale totals; this is tolerable since daily totals are approximate by nature.
- **Output:** `"day: ${cost:.2f} {tokens}k tok"` — tokens are floor-divided by 1000 (`total // 1000`). Values under 1000 display as `0k`.
- **Edge cases:** Missing/corrupt file → create fresh; stale date → reset

### Context Extraction

`_extract_context()` in `render.py` already extracts `cost_usd` and `context_pct`. The widgets need additional fields (`total_duration_ms`, token counts) not in that dict. A separate extraction function keeps the existing interface stable. Note: `total_cost_usd` is intentionally duplicated here rather than coupling widgets to `_extract_context()`'s `cost_usd` key — this keeps the widget pipeline self-contained.

```python
def _extract_widget_context(data: dict[str, Any]) -> dict[str, Any]:
    """Extract fields needed by widgets from Claude Code JSON."""
    cost_info = data.get("cost", {})
    ctx_info = data.get("context_window", {})
    current = ctx_info.get("current_usage", {}) if isinstance(ctx_info, dict) else {}
    return {
        "total_cost_usd": cost_info.get("total_cost_usd", 0.0),
        "total_duration_ms": cost_info.get("total_duration_ms", 0),
        "total_input_tokens": ctx_info.get("total_input_tokens", 0),
        "total_output_tokens": ctx_info.get("total_output_tokens", 0),
    }
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
    "daily_totals": true
}
```

### Read Logic

```python
def _read_widget_config() -> dict[str, bool]:
    """Read per-widget toggles, defaulting all to True."""
    try:
        data = json.loads(_WIDGET_CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    return {
        "token_speed": bool(data.get("token_speed", True)),
        "burn_rate": bool(data.get("burn_rate", True)),
        "block_timer": bool(data.get("block_timer", True)),
        "daily_totals": bool(data.get("daily_totals", True)),
    }
```

### Write Logic

Toggle flips a single widget's boolean and writes the full config back. Uses `mkdir(parents=True)` for the `.artifacts/` directory, matching the existing pattern in `toggle.py:23`.

### CLI Subcommands

| Command | Action |
|---------|--------|
| `uv run mde-py statusline toggle-widget <name>` | Flip one widget on/off |
| `uv run mde-py statusline toggle-widget all` | If any widget is on, turn all off; if all are off, turn all on |
| `uv run mde-py statusline show-widgets` | Print widget config table |

**Valid widget names:** `token_speed`, `burn_rate`, `block_timer`, `daily_totals`, `all`

**Output examples:**
```
$ uv run mde-py statusline toggle-widget burn_rate
burn_rate: on → off

$ uv run mde-py statusline show-widgets
token_speed   on
burn_rate     off
block_timer   on
daily_totals  on
```

---

## Error Handling

Matches existing statusline conventions: silent defaults, return 0 always, never block Claude Code.

| Failure | Behavior |
|---------|----------|
| `statusline-widgets.json` missing | All widgets enabled |
| `statusline-widgets.json` corrupt | All widgets enabled |
| `daily-totals.json` missing | Create fresh from current session |
| `daily-totals.json` corrupt | Overwrite with current session |
| Widget receives `None`/missing fields | `_to_float` returns `0.0` |
| Division by zero (duration=0) | Guard returns dash or `$0.00` |
| Unknown widget name in `toggle-widget` | Print error, return 1 |

---

## File Manifest

### New Files

| File | Purpose |
|------|---------|
| `src/mde/statusline/widgets.py` | 4 widget functions + `_extract_widget_context` + `_render_metrics_bar` |
| `src/mde/statusline/widget_toggle.py` | `_read_widget_config`, `toggle_widget`, `show_widgets` |
| `tests/mde/test_statusline_widgets.py` | Unit tests for all 4 widgets + metrics bar composition |
| `tests/mde/test_widget_toggle.py` | Toggle read/write/cycle + CLI integration tests |

### Modified Files

| File | Change |
|------|--------|
| `src/mde/statusline/render.py` | Import `_render_metrics_bar` and `_extract_widget_context`; call in `render_statusline()` after mode render (~5 lines) |
| `src/mde/statusline/__init__.py` | Updated docstring to mention widgets |
| `src/mde/cli.py` | Add `toggle-widget` and `show-widgets` subcommands to statusline parser |

### Unchanged Files

- `src/mde/statusline/toggle.py` — A/B/C cycling untouched
- `src/mde/hooks/log_agent_event.py` — agent logging untouched
- `.claude/settings.json` — no new hooks needed
- All 15 existing tests pass without modification

---

## Testing Plan

### Unit Tests — `tests/mde/test_statusline_widgets.py`

Per widget: normal case, zero/missing duration, missing fields, null values.

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
| `test_metrics_bar_all_enabled` | All 4 widgets joined by ` \| ` |
| `test_metrics_bar_some_disabled` | Only enabled widgets appear |
| `test_metrics_bar_all_disabled` | Returns empty string |

### Unit Tests — `tests/mde/test_widget_toggle.py`

| Test | Assertion |
|------|-----------|
| `test_read_config_defaults_all_true` | Missing file → all enabled |
| `test_read_config_corrupt_defaults` | Invalid JSON → all enabled |
| `test_toggle_widget_flips` | `on → off`, `off → on` |
| `test_toggle_all_any_on_turns_all_off` | Mixed state → all off |
| `test_toggle_all_all_off_turns_all_on` | All off → all on |
| `test_show_widgets_output` | Correct table format |
| `test_unknown_widget_name` | Returns error, exit code 1 |

### Integration Tests — `tests/mde/test_statusline.py` (new tests added)

Integration tests must patch `_WIDGET_CONFIG_FILE` (from `widget_toggle.py`) and `_DAILY_TOTALS_FILE` (from `widgets.py`) to `tmp_path` paths, following the same pattern as existing tests that patch `_MODE_FILE` and `_AGENT_STATE_FILE`.

| Test | Assertion |
|------|-----------|
| `test_mode_a_with_metrics_bar` | Mode A output + ` \| ` + widget output |
| `test_mode_c_with_metrics_bar` | Dashboard + metrics on final line |
| `test_mode_a_all_widgets_disabled` | Output identical to current Mode A |

### Test Commands

```
uv run pytest tests/mde/test_statusline_widgets.py -v
uv run pytest tests/mde/test_widget_toggle.py -v
uv run pytest tests/mde/test_statusline.py -v
uv run pytest tests/mde/ -k statusline -v          # all statusline tests
```

---

## Success Criteria

1. All 4 widgets render correct output for normal and edge-case inputs
2. Per-widget toggles work independently of A/B/C mode cycling
3. Metrics bar appends cleanly to all 3 existing modes
4. Daily totals persist across sessions and reset at midnight
5. All existing 15 tests pass without modification
6. `uv run ruff check src/mde/statusline/ --select ALL` — zero violations
7. `uv run ty check src/mde/statusline/` — zero type errors
