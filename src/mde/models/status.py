"""Status enums for validation checks."""

from __future__ import annotations

from enum import Enum


class CheckStatus(str, Enum):
    """Overall status of a validation check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
