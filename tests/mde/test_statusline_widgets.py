"""Tests for statusline widget functions."""

from __future__ import annotations

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
