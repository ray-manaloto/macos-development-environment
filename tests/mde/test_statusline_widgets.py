"""Tests for statusline widget functions."""

from __future__ import annotations

import json
from unittest.mock import patch

from mde.statusline.models import StatuslineInput


def _make(overrides: dict) -> StatuslineInput:
    """Build StatuslineInput with defaults + overrides via model_validate."""
    return StatuslineInput.model_validate(overrides)


class TestTokenSpeed:
    """Tests for token_speed_widget."""

    def test_normal(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        data = _make(
            {
                "cost": {"total_duration_ms": 60000},
                "context_window": {
                    "total_input_tokens": 20000,
                    "total_output_tokens": 10000,
                },
            }
        )
        assert token_speed_widget(data) == "500 tok/s"

    def test_zero_duration(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        data = _make(
            {
                "cost": {"total_duration_ms": 0},
                "context_window": {"total_input_tokens": 100},
            }
        )
        assert token_speed_widget(data) == "\u2014 tok/s"

    def test_zero_tokens_with_duration(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        data = _make({"cost": {"total_duration_ms": 60000}})
        assert token_speed_widget(data) == "0 tok/s"

    def test_missing_fields(self) -> None:
        from mde.statusline.widgets import token_speed_widget

        data = _make({})
        assert token_speed_widget(data) == "\u2014 tok/s"


class TestBurnRate:
    """Tests for burn_rate_widget."""

    def test_normal(self) -> None:
        from mde.statusline.widgets import burn_rate_widget

        data = _make(
            {
                "cost": {"total_cost_usd": 1.50, "total_duration_ms": 60000},
            }
        )
        assert burn_rate_widget(data) == "$1.50/min"

    def test_zero_duration(self) -> None:
        from mde.statusline.widgets import burn_rate_widget

        data = _make(
            {
                "cost": {"total_cost_usd": 1.50, "total_duration_ms": 0},
            }
        )
        assert burn_rate_widget(data) == "$0.00/min"


class TestBlockTimer:
    """Tests for block_timer_widget."""

    def test_normal(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        data = _make({"cost": {"total_duration_ms": 125000}})
        assert block_timer_widget(data) == "2:05"

    def test_over_hour(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        data = _make({"cost": {"total_duration_ms": 3725000}})
        assert block_timer_widget(data) == "1:02:05"

    def test_zero(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        data = _make({"cost": {"total_duration_ms": 0}})
        assert block_timer_widget(data) == "0:00"

    def test_just_under_hour(self) -> None:
        from mde.statusline.widgets import block_timer_widget

        data = _make({"cost": {"total_duration_ms": 3599000}})
        assert block_timer_widget(data) == "59:59"


class TestDailyTotals:
    """Tests for daily_totals_widget."""

    def test_fresh(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import daily_totals_widget

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        data = _make(
            {
                "cost": {"total_cost_usd": 2.50},
                "context_window": {
                    "total_input_tokens": 50000,
                    "total_output_tokens": 10000,
                },
            }
        )
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = daily_totals_widget(data)
        assert "day: $2.50" in result
        assert "60k tok" in result

    def test_accumulates(self, tmp_path: object) -> None:
        import datetime

        from mde.statusline import widgets
        from mde.statusline.widgets import daily_totals_widget

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        today = str(datetime.datetime.now(tz=datetime.UTC).date())
        totals_file.write_text(
            json.dumps(
                {
                    "date": today,
                    "total_cost_usd": 1.00,
                    "total_tokens": 20000,
                }
            )
        )
        data = _make(
            {
                "cost": {"total_cost_usd": 1.50},
                "context_window": {
                    "total_input_tokens": 30000,
                    "total_output_tokens": 10000,
                },
            }
        )
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = daily_totals_widget(data)
        assert "day: $2.50" in result
        assert "60k tok" in result

    def test_resets_on_new_day(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import daily_totals_widget

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        totals_file.write_text(
            json.dumps(
                {
                    "date": "1999-01-01",
                    "total_cost_usd": 999,
                    "total_tokens": 999999,
                }
            )
        )
        data = _make(
            {
                "cost": {"total_cost_usd": 1.00},
                "context_window": {
                    "total_input_tokens": 5000,
                    "total_output_tokens": 5000,
                },
            }
        )
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = daily_totals_widget(data)
        assert "day: $1.00" in result
        assert "10k tok" in result

    def test_corrupt_file(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import daily_totals_widget

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        totals_file.write_text("not json")
        data = _make(
            {
                "cost": {"total_cost_usd": 1.00},
                "context_window": {
                    "total_input_tokens": 5000,
                    "total_output_tokens": 5000,
                },
            }
        )
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = daily_totals_widget(data)
        assert "day: $1.00" in result


class TestLinesChanged:
    """Tests for lines_changed_widget."""

    def test_both(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        data = _make({"cost": {"total_lines_added": 156, "total_lines_removed": 23}})
        result = lines_changed_widget(data)
        assert "+156" in result
        assert "-23" in result

    def test_add_only(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        data = _make({"cost": {"total_lines_added": 156, "total_lines_removed": 0}})
        result = lines_changed_widget(data)
        assert "+156" in result
        assert "-" not in result

    def test_remove_only(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        data = _make({"cost": {"total_lines_added": 0, "total_lines_removed": 23}})
        result = lines_changed_widget(data)
        assert "-23" in result
        assert "+" not in result

    def test_both_zero(self) -> None:
        from mde.statusline.widgets import lines_changed_widget

        assert lines_changed_widget(_make({})) == ""


class TestCacheRatio:
    """Tests for cache_ratio_widget."""

    def test_normal(self) -> None:
        from mde.statusline.widgets import cache_ratio_widget

        data = _make(
            {
                "context_window": {
                    "current_usage": {
                        "cache_read_input_tokens": 620,
                        "cache_creation_input_tokens": 380,
                        "input_tokens": 0,
                    },
                },
            }
        )
        result = cache_ratio_widget(data)
        assert "cache:62%" in result

    def test_no_usage(self) -> None:
        from mde.statusline.widgets import cache_ratio_widget

        data = _make({"context_window": {"current_usage": None}})
        assert cache_ratio_widget(data) == ""

    def test_all_zero(self) -> None:
        from mde.statusline.widgets import cache_ratio_widget

        data = _make(
            {
                "context_window": {
                    "current_usage": {
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                        "input_tokens": 0,
                    },
                },
            }
        )
        assert cache_ratio_widget(data) == ""
