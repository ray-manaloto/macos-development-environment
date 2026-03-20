"""Tests for multi-agent statusline renderer, toggle, and agent event hook.

Uses the REAL Claude Code JSON schemas discovered via raw payload capture:
- statusline stdin: {model, cost, context_window}
- SubagentStart: {agent_id, agent_type, hook_event_name: "SubagentStart"}
- SubagentStop:  {agent_id, agent_type, hook_event_name: "SubagentStop"}
"""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch


def _make_stdin(data: dict[str, object]) -> io.StringIO:
    return io.StringIO(json.dumps(data))


def _sample_statusline_stdin() -> dict[str, object]:
    """Real Claude Code statusline JSON shape."""
    return {
        "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
        "cost": {"total_cost_usd": 1.23, "total_duration_ms": 45000},
        "context_window": {"used_percentage": 42, "context_window_size": 200000},
    }


def _agent_started(agent_id: str, agent_type: str) -> dict[str, object]:
    """Agent state JSONL entry as produced by the fixed log_agent_event hook."""
    return {"agent_name": agent_type, "agent_id": agent_id, "event": "started"}


def _agent_stopped(agent_id: str, agent_type: str) -> dict[str, object]:
    """Agent state JSONL entry for a stopped agent."""
    return {"agent_name": agent_type, "agent_id": agent_id, "event": "stopped"}


def _subagent_start_payload(agent_id: str, agent_type: str) -> dict[str, object]:
    """Real Claude Code SubagentStart stdin JSON shape."""
    return {
        "session_id": "test-session",
        "agent_id": agent_id,
        "agent_type": agent_type,
        "hook_event_name": "SubagentStart",
        "cwd": "/tmp/test",
    }


def _subagent_stop_payload(agent_id: str, agent_type: str) -> dict[str, object]:
    """Real Claude Code SubagentStop stdin JSON shape."""
    return {
        "session_id": "test-session",
        "agent_id": agent_id,
        "agent_type": agent_type,
        "hook_event_name": "SubagentStop",
        "cwd": "/tmp/test",
        "permission_mode": "bypassPermissions",
    }


class TestStatuslineRender:
    """Tests for the statusline render modes."""

    def test_mode_a_shows_agent_count_and_cost(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        state_file.write_text(
            json.dumps(_agent_started("abc123", "researcher"))
            + "\n"
            + json.dumps(_agent_started("def456", "coder"))
            + "\n"
        )
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "2 agents" in captured.out
        assert "$1.23" in captured.out

    def test_mode_b_shows_per_agent_state(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        state_file.write_text(json.dumps(_agent_started("abc123", "researcher")) + "\n")
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("B\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "researcher:" in captured.out
        assert "started" in captured.out

    def test_mode_c_shows_dashboard(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        state_file.write_text(json.dumps(_agent_started("abc123def", "coder")) + "\n")
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("C\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "Opus" in captured.out
        assert "coder" in captured.out
        assert "abc123" in captured.out  # truncated agent_id
        assert "running" in captured.out

    def test_defaults_to_mode_a(self, tmp_path: object) -> None:
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "nonexistent-mode"  # type: ignore[operator]

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

    def test_handles_invalid_json(self) -> None:
        from mde.statusline.render import render_statusline

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert render_statusline() == 0

    def test_handles_null_used_percentage(self, tmp_path: object, capsys: object) -> None:
        """Docs: used_percentage may be null early in session."""
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 0.0},
            "context_window": {"used_percentage": None, "remaining_percentage": None},
        }
        stdin = _make_stdin(data)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "0%" in captured.out

    def test_handles_full_official_schema(self, tmp_path: object, capsys: object) -> None:
        """Integration test with the complete official JSON schema from docs."""
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        full_schema: dict[str, object] = {
            "cwd": "/Users/test/project",
            "session_id": "abc123",
            "transcript_path": "/path/to/transcript.jsonl",
            "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
            "workspace": {
                "current_dir": "/Users/test/project",
                "project_dir": "/Users/test/project",
            },
            "version": "1.0.80",
            "output_style": {"name": "default"},
            "cost": {
                "total_cost_usd": 2.50,
                "total_duration_ms": 120000,
                "total_api_duration_ms": 5000,
                "total_lines_added": 200,
                "total_lines_removed": 50,
            },
            "context_window": {
                "total_input_tokens": 50000,
                "total_output_tokens": 10000,
                "context_window_size": 200000,
                "used_percentage": 65,
                "remaining_percentage": 35,
                "current_usage": {
                    "input_tokens": 8500,
                    "output_tokens": 1200,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 2000,
                },
            },
            "exceeds_200k_tokens": False,
        }
        stdin = _make_stdin(full_schema)
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "$2.50" in captured.out
        assert "65%" in captured.out

    def test_handles_no_agents(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            assert render.render_statusline() == 0

        captured = capsys.readouterr()  # type: ignore[union-attr]
        # No "agent" text when count is 0
        assert "agent" not in captured.out
        assert "$1.23" in captured.out

    def test_stopped_agents_filtered_out(self, tmp_path: object, capsys: object) -> None:
        """Agents whose last event is 'stopped' should not appear."""
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        state_file.write_text(
            json.dumps(_agent_started("abc123", "researcher"))
            + "\n"
            + json.dumps(_agent_stopped("abc123", "researcher"))
            + "\n"
            + json.dumps(_agent_started("def456", "coder"))
            + "\n"
        )
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            render.render_statusline()

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "1 agent" in captured.out  # researcher stopped, only coder remains

    def test_agent_dedup_by_id(self, tmp_path: object, capsys: object) -> None:
        """Multiple events for same agent_id should keep latest only."""
        from mde.statusline import render

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        state_file.write_text(
            json.dumps(_agent_started("abc123", "coder"))
            + "\n"
            + json.dumps(_agent_started("abc123", "coder"))
            + "\n"
        )
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        stdin = _make_stdin(_sample_statusline_stdin())
        with (
            patch.object(render, "_MODE_FILE", mode_file),
            patch.object(render, "_AGENT_STATE_FILE", state_file),
            patch.object(sys, "stdin", stdin),
        ):
            render.render_statusline()

        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "1 agent" in captured.out  # deduplicated by agent_id


class TestStatuslineToggle:
    """Tests for mode toggle cycling."""

    def test_cycles_a_to_b(self, tmp_path: object) -> None:
        from mde.statusline import toggle

        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")

        with patch.object(toggle, "_MODE_FILE", mode_file):
            assert toggle.toggle_mode() == 0

        assert mode_file.read_text().strip() == "B"  # type: ignore[union-attr]

    def test_cycles_b_to_c(self, tmp_path: object) -> None:
        from mde.statusline import toggle

        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("B\n")

        with patch.object(toggle, "_MODE_FILE", mode_file):
            assert toggle.toggle_mode() == 0

        assert mode_file.read_text().strip() == "C"  # type: ignore[union-attr]

    def test_cycles_c_to_a(self, tmp_path: object) -> None:
        from mde.statusline import toggle

        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("C\n")

        with patch.object(toggle, "_MODE_FILE", mode_file):
            assert toggle.toggle_mode() == 0

        assert mode_file.read_text().strip() == "A"  # type: ignore[union-attr]

    def test_defaults_to_a_when_no_file(self, tmp_path: object) -> None:
        from mde.statusline import toggle

        mode_file = tmp_path / "nonexistent"  # type: ignore[operator]

        with patch.object(toggle, "_MODE_FILE", mode_file):
            assert toggle.show_mode() == 0


def _widget_config_json(**overrides: bool) -> str:
    """Build widget config JSON with all widgets disabled except overrides."""
    from mde.statusline.widget_toggle import ALL_WIDGETS

    config = dict.fromkeys(ALL_WIDGETS, False)
    config.update(overrides)
    return json.dumps(config)


class TestMetricsBarIntegration:
    """Integration tests for metrics bar in the render pipeline."""

    def test_mode_a_with_metrics_bar(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(_widget_config_json(token_speed=True))
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 1.23, "total_duration_ms": 60000},
            "context_window": {
                "used_percentage": 42,
                "total_input_tokens": 30000,
                "total_output_tokens": 0,
            },
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

    def test_mode_c_with_metrics_bar(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("C\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(_widget_config_json(token_speed=True))
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 2.50, "total_duration_ms": 60000},
            "context_window": {
                "used_percentage": 65,
                "total_input_tokens": 30000,
                "total_output_tokens": 0,
            },
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
        assert len(lines) >= 2
        assert "tok/s" in lines[-1]

    def test_mode_a_all_widgets_disabled(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(_widget_config_json())
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 1.23},
            "context_window": {"used_percentage": 42},
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
        assert "tok/s" not in captured.out

    def test_4_tier_color_at_85_pct(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(_widget_config_json())
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 0},
            "context_window": {"used_percentage": 85},
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
        assert "85%" in captured.out
        assert "\033[38;5;208m" in captured.out  # Orange

    def test_rate_limits_in_full_render(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import render, widget_toggle, widgets

        state_file = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        mode_file = tmp_path / "statusline-mode"  # type: ignore[operator]
        mode_file.write_text("A\n")
        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(_widget_config_json(rate_limits=True))
        totals_file = tmp_path / "daily-totals.json"  # type: ignore[operator]

        data: dict[str, object] = {
            "model": {"display_name": "Opus"},
            "cost": {"total_cost_usd": 1.00},
            "context_window": {"used_percentage": 42},
            "rate_limits": {
                "five_hour": {
                    "status": "allowed_warning",
                    "utilization": 0.72,
                    "resetsAt": 9999999999,
                }
            },
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


class TestLogAgentEvent:
    """Tests for SubagentStart/SubagentStop hook using REAL Claude Code payloads."""

    def test_logs_subagent_start(self, tmp_path: object) -> None:
        from mde.hooks import log_agent_event

        outfile = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        with patch.object(log_agent_event, "_AGENT_STATE_FILE", outfile):
            data = _subagent_start_payload("ae145dfb68a7cfee7", "Explore")
            stdin = io.StringIO(json.dumps(data))
            with patch.object(sys, "stdin", stdin):
                assert log_agent_event.log_agent_event() == 0

        lines = outfile.read_text().strip().split("\n")  # type: ignore[union-attr]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["agent_name"] == "Explore"
        assert record["agent_id"] == "ae145dfb68a7cfee7"
        assert record["event"] == "started"

    def test_logs_subagent_stop(self, tmp_path: object) -> None:
        from mde.hooks import log_agent_event

        outfile = tmp_path / "agent-state.jsonl"  # type: ignore[operator]
        with patch.object(log_agent_event, "_AGENT_STATE_FILE", outfile):
            data = _subagent_stop_payload("ae145dfb68a7cfee7", "Explore")
            stdin = io.StringIO(json.dumps(data))
            with patch.object(sys, "stdin", stdin):
                assert log_agent_event.log_agent_event() == 0

        lines = outfile.read_text().strip().split("\n")  # type: ignore[union-attr]
        record = json.loads(lines[0])
        assert record["agent_name"] == "Explore"
        assert record["agent_id"] == "ae145dfb68a7cfee7"
        assert record["event"] == "stopped"

    def test_handles_invalid_json(self) -> None:
        from mde.hooks.log_agent_event import log_agent_event

        stdin = io.StringIO("not json")
        with patch.object(sys, "stdin", stdin):
            assert log_agent_event() == 0
