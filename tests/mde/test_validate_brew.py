"""Tests for Homebrew validation (LLVM brew prefix check)."""

from __future__ import annotations

import platform
from typing import Any
from unittest.mock import patch

from mde.models.result import ValidationResult
from mde.validate.brew import _check_llvm_is_brew


def _mock_proc(*, returncode: int = 0, stdout: str = "", stderr: str = "") -> Any:
    """Create a mock CompletedProcess."""
    return type(
        "CompletedProcess",
        (),
        {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    )()


class TestLLVMBrewPrefixCheck:
    """Finding #7: LLVM validator must check brew prefix, not just reject Apple."""

    def test_apple_clang_rejected(self) -> None:
        """Apple clang should be rejected as before."""

        def mock_run(cmd: list[str], **_kw: Any) -> Any:
            if cmd == ["clang", "--version"]:
                return _mock_proc(stdout="Apple clang version 15.0.0\n")
            return _mock_proc()

        result = ValidationResult()
        with (
            patch.object(platform, "system", return_value="Darwin"),
            patch("mde.validate.brew.shutil.which", return_value="/usr/bin/clang"),
            patch("mde.validate.brew.subprocess.run", side_effect=mock_run),
        ):
            _check_llvm_is_brew(result)

        errors = [f for f in result.findings if f.rule == "brew.llvm-not-active"]
        assert len(errors) == 1
        assert "Apple" in errors[0].message

    def test_non_apple_non_brew_clang_rejected(self) -> None:
        """Non-Apple clang NOT under brew prefix should be rejected."""

        def mock_run(cmd: list[str], **_kw: Any) -> Any:
            if cmd[0] == "clang":
                return _mock_proc(stdout="clang version 17.0.0 (custom build)\n")
            if cmd[0] == "brew":
                return _mock_proc(stdout="/opt/homebrew\n")
            return _mock_proc()

        result = ValidationResult()
        with (
            patch.object(platform, "system", return_value="Darwin"),
            patch(
                "mde.validate.brew.shutil.which",
                return_value="/usr/local/custom/bin/clang",
            ),
            patch("mde.validate.brew.subprocess.run", side_effect=mock_run),
        ):
            _check_llvm_is_brew(result)

        errors = [f for f in result.findings if f.rule == "brew.llvm-not-active"]
        assert len(errors) == 1
        assert "not under Homebrew prefix" in errors[0].message

    def test_brew_clang_accepted(self) -> None:
        """Clang under the brew prefix should pass."""
        brew_prefix = "/opt/homebrew"

        def mock_run(cmd: list[str], **_kw: Any) -> Any:
            if cmd[0] == "clang":
                return _mock_proc(stdout="Homebrew clang version 18.1.0\n")
            if cmd[0] == "brew":
                return _mock_proc(stdout=f"{brew_prefix}\n")
            return _mock_proc()

        result = ValidationResult()
        with (
            patch.object(platform, "system", return_value="Darwin"),
            patch(
                "mde.validate.brew.shutil.which",
                return_value=f"{brew_prefix}/opt/llvm/bin/clang",
            ),
            patch("mde.validate.brew.subprocess.run", side_effect=mock_run),
        ):
            _check_llvm_is_brew(result)

        errors = [f for f in result.findings if f.rule == "brew.llvm-not-active"]
        assert len(errors) == 0

    def test_non_darwin_skipped(self) -> None:
        """Non-macOS systems should skip the check entirely."""
        result = ValidationResult()
        with patch.object(platform, "system", return_value="Linux"):
            _check_llvm_is_brew(result)
        assert len(result.findings) == 0
