"""Tests for statusline widget functions."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from claude_agent_sdk.types import RateLimitInfo

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


class TestRateLimits:
    """Tests for rate_limits_widget."""

    def test_normal(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        info = {
            "five_hour": RateLimitInfo(status="allowed", utilization=0.42, raw={}),
            "seven_day": None,
            "overage": None,
        }
        result = rate_limits_widget(info)
        assert "5h:42%" in result

    def test_both_windows(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        info = {
            "five_hour": RateLimitInfo(status="allowed", utilization=0.42, raw={}),
            "seven_day": RateLimitInfo(status="allowed", utilization=0.15, raw={}),
            "overage": None,
        }
        result = rate_limits_widget(info)
        assert "5h:42%" in result
        assert "7d:15%" in result

    def test_rejected(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        info = {
            "five_hour": RateLimitInfo(status="rejected", raw={}),
            "seven_day": None,
            "overage": None,
        }
        result = rate_limits_widget(info)
        assert "LIMIT" in result

    def test_absent(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        info = {"five_hour": None, "seven_day": None, "overage": None}
        assert rate_limits_widget(info) == ""

    def test_countdown_when_high(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        future = int(time.time()) + 7200
        info = {
            "five_hour": RateLimitInfo(
                status="allowed_warning",
                utilization=0.85,
                resets_at=future,
                raw={},
            ),
            "seven_day": None,
            "overage": None,
        }
        result = rate_limits_widget(info)
        assert "\u21bb" in result  # ↻ countdown symbol
        assert "5h:85%" in result
        assert "h" in result  # countdown format: XhYYm
        assert "m" in result

    def test_allowed_warning_shows(self) -> None:
        from mde.statusline.widgets import rate_limits_widget

        info = {
            "five_hour": RateLimitInfo(
                status="allowed_warning",
                utilization=0.30,
                raw={},
            ),
            "seven_day": None,
            "overage": None,
        }
        result = rate_limits_widget(info)
        assert "5h:30%" in result
        assert result != ""


class TestMetricsBar:
    """Tests for render_metrics_bar."""

    def test_all_enabled(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle, widgets
        from mde.statusline.widgets import render_metrics_bar

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        data = _make(
            {
                "cost": {
                    "total_cost_usd": 1.50,
                    "total_duration_ms": 60000,
                    "total_lines_added": 10,
                    "total_lines_removed": 5,
                },
                "context_window": {
                    "total_input_tokens": 30000,
                    "total_output_tokens": 0,
                    "current_usage": {
                        "cache_read_input_tokens": 500,
                        "cache_creation_input_tokens": 300,
                        "input_tokens": 200,
                    },
                },
            }
        )
        rate_info = {"five_hour": None, "seven_day": None, "overage": None}
        config = dict.fromkeys(widget_toggle.ALL_WIDGETS, True)
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = render_metrics_bar(data, rate_info, config)
        assert "tok/s" in result
        assert " | " in result

    def test_all_disabled(self) -> None:
        from mde.statusline.widgets import render_metrics_bar

        data = _make({})
        rate_info = {"five_hour": None, "seven_day": None, "overage": None}
        config = dict.fromkeys(
            [
                "token_speed",
                "burn_rate",
                "block_timer",
                "daily_totals",
                "lines_changed",
                "cache_ratio",
                "rate_limits",
            ],
            False,
        )
        assert render_metrics_bar(data, rate_info, config) == ""

    def test_suppresses_empty_widgets(self, tmp_path: object) -> None:
        from mde.statusline import widgets
        from mde.statusline.widgets import render_metrics_bar

        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]
        data = _make(
            {
                "cost": {"total_cost_usd": 1.50, "total_duration_ms": 60000},
                "context_window": {"total_input_tokens": 30000},
            }
        )
        rate_info = {"five_hour": None, "seven_day": None, "overage": None}
        config = dict.fromkeys(
            [
                "token_speed",
                "burn_rate",
                "block_timer",
                "daily_totals",
                "lines_changed",
                "cache_ratio",
                "rate_limits",
            ],
            True,
        )
        with patch.object(widgets, "_DAILY_TOTALS_FILE", totals_file):
            result = render_metrics_bar(data, rate_info, config)
        # lines_changed, cache_ratio, rate_limits all suppressed
        assert "tok/s" in result
        assert result.count(" | ") <= 3
