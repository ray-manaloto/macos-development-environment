"""Tests for statusline stdin parsing and rate limit normalization."""

from __future__ import annotations

from claude_agent_sdk.types import RateLimitInfo


def _full_stdin_json() -> dict[str, object]:
    """Complete v2.1.80 statusline stdin JSON."""
    return {
        "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
        "cost": {
            "total_cost_usd": 2.50,
            "total_duration_ms": 120000,
            "total_lines_added": 156,
            "total_lines_removed": 23,
        },
        "context_window": {
            "total_input_tokens": 50000,
            "total_output_tokens": 10000,
            "context_window_size": 200000,
            "used_percentage": 65,
            "current_usage": {
                "input_tokens": 8500,
                "cache_read_input_tokens": 2000,
                "cache_creation_input_tokens": 5000,
                "output_tokens": 1200,
            },
        },
        "exceeds_200k_tokens": False,
        "version": "2.1.80",
        "session_id": "test-session",
    }


class TestParseStdin:
    """Validate parse_stdin with various input shapes."""

    def test_full_schema(self) -> None:
        from mde.statusline.schema import parse_stdin

        result = parse_stdin(_full_stdin_json())
        assert result.model is not None
        assert result.model.display_name == "Opus"  # type: ignore[union-attr]
        assert result.cost is not None
        assert result.cost.total_cost_usd == 2.50
        assert result.context_window is not None
        assert result.context_window.used_percentage == 65.0
        assert result.context_window.current_usage is not None
        assert result.context_window.current_usage.cache_read_input_tokens == 2000.0

    def test_empty_dict(self) -> None:
        from mde.statusline.schema import parse_stdin

        result = parse_stdin({})
        assert result.cost is None
        assert result.model is None

    def test_string_number_coercion(self) -> None:
        from mde.statusline.schema import parse_stdin

        result = parse_stdin(
            {
                "cost": {"total_cost_usd": "1.25", "total_duration_ms": "60000"},
            }
        )
        assert result.cost is not None
        assert result.cost.total_cost_usd == 1.25
        assert result.cost.total_duration_ms == 60000.0

    def test_null_current_usage(self) -> None:
        from mde.statusline.schema import parse_stdin

        result = parse_stdin(
            {
                "context_window": {
                    "used_percentage": None,
                    "current_usage": None,
                },
            }
        )
        assert result.context_window is not None
        assert result.context_window.current_usage is None
        assert result.context_window.used_percentage is None

    def test_invalid_json_returns_defaults(self) -> None:
        from mde.statusline.schema import parse_stdin_raw

        result = parse_stdin_raw("not json")
        assert result.cost is None

    def test_invalid_string_number_raises(self) -> None:
        """Pydantic V2 raises ValidationError on non-numeric strings."""
        import pytest

        from mde.statusline.schema import parse_stdin

        with pytest.raises(Exception):  # noqa: B017, PT011
            parse_stdin({"cost": {"total_cost_usd": "not-a-number"}})

    def test_unknown_fields_preserved(self) -> None:
        from mde.statusline.schema import parse_stdin

        result = parse_stdin(
            {
                "unknown_future_field": True,
                "model": {"display_name": "Opus"},
            }
        )
        assert result.model_extra is not None
        assert "unknown_future_field" in result.model_extra

    def test_unknown_fields_warned(self, capsys: object) -> None:
        from mde.statusline.schema import parse_stdin

        parse_stdin({"unknown_future_field": True})
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "unknown_future_field" in captured.err


class TestParseRateLimits:
    """Validate rate limit parsing across Shape A, Shape B, and edge cases."""

    def test_absent(self) -> None:
        from mde.statusline.schema import parse_rate_limits

        result = parse_rate_limits(None)
        assert result["five_hour"] is None
        assert result["seven_day"] is None

    def test_shape_b_nested(self) -> None:
        from mde.statusline.schema import parse_rate_limits

        raw = {
            "five_hour": {
                "status": "allowed_warning",
                "utilization": 0.42,
                "resetsAt": 1773273600,
            },
        }
        result = parse_rate_limits(raw)
        info = result["five_hour"]
        assert isinstance(info, RateLimitInfo)
        assert info.utilization == 0.42
        assert info.resets_at == 1773273600
        assert info.status == "allowed_warning"

    def test_shape_a_flat(self) -> None:
        from mde.statusline.schema import parse_rate_limits

        raw = {
            "status": "allowed",
            "rateLimitType": "five_hour",
            "utilization": 0.62,
            "resetsAt": 1773273600,
        }
        result = parse_rate_limits(raw)
        assert result["five_hour"] is not None
        assert result["five_hour"].utilization == 0.62

    def test_camel_to_snake(self) -> None:
        from mde.statusline.schema import parse_rate_limits

        raw = {
            "five_hour": {
                "status": "allowed",
                "rateLimitType": "five_hour",
                "resetsAt": 1773273600,
            },
        }
        info = parse_rate_limits(raw)["five_hour"]
        assert info is not None
        assert info.rate_limit_type == "five_hour"
        assert info.resets_at == 1773273600

    def test_model_specific_normalized(self) -> None:
        from mde.statusline.schema import parse_rate_limits

        raw = {
            "status": "allowed",
            "rateLimitType": "seven_day_opus",
            "utilization": 0.15,
        }
        result = parse_rate_limits(raw)
        assert result["seven_day"] is not None
        assert result["seven_day"].utilization == 0.15
