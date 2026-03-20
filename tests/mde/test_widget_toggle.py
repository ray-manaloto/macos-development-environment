"""Tests for per-widget toggle config in statusline metrics bar."""

from __future__ import annotations

import json
from unittest.mock import patch


class TestReadWidgetConfig:
    """Verify read_widget_config defaults and corrupt-file recovery."""

    def test_defaults_all_true(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            config = widget_toggle.read_widget_config()
        assert all(config.values())
        assert len(config) == 7

    def test_corrupt_defaults(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text("not json")
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            config = widget_toggle.read_widget_config()
        assert all(config.values())


class TestToggleWidget:
    """Verify toggle_widget flips state, handles unknown names, and toggle-all."""

    def test_flips_on_to_off(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps({"token_speed": True}))
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            assert widget_toggle.toggle_widget("token_speed") == 0
        data = json.loads(config_file.read_text())
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
            config = widget_toggle.read_widget_config()
        assert not any(config.values())

    def test_toggle_all_all_off_turns_all_on(self, tmp_path: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        config_file.write_text(json.dumps(dict.fromkeys(widget_toggle.ALL_WIDGETS, False)))
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            widget_toggle.toggle_widget("all")
            config = widget_toggle.read_widget_config()
        assert all(config.values())


class TestShowWidgets:
    """Verify show_widgets prints all widget names with on/off state."""

    def test_output_format(self, tmp_path: object, capsys: object) -> None:
        from mde.statusline import widget_toggle

        config_file = tmp_path / "statusline-widgets.json"  # type: ignore[operator]
        with patch.object(widget_toggle, "_WIDGET_CONFIG_FILE", config_file):
            widget_toggle.show_widgets()
        captured = capsys.readouterr()  # type: ignore[union-attr]
        for name in widget_toggle.ALL_WIDGETS:
            assert name in captured.out
        assert "on" in captured.out
