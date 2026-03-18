"""Tests for platform detection."""

from __future__ import annotations

import os

from mde.lib.platform import detect_platform, is_macos


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_explicit_macos(self, monkeypatch: object) -> None:
        """MDE_PLATFORM=macos should return macos."""
        os.environ["MDE_PLATFORM"] = "macos"
        try:
            assert detect_platform() == "macos"
        finally:
            os.environ.pop("MDE_PLATFORM", None)

    def test_explicit_devcontainer(self) -> None:
        """MDE_PLATFORM=devcontainer should return devcontainer."""
        os.environ["MDE_PLATFORM"] = "devcontainer"
        try:
            assert detect_platform() == "devcontainer"
        finally:
            os.environ.pop("MDE_PLATFORM", None)

    def test_is_macos_returns_bool(self) -> None:
        """is_macos should return a boolean."""
        assert isinstance(is_macos(), bool)
