"""Result types for validation and maintenance operations."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity level for validation findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Finding(BaseModel):
    """A single validation finding."""

    path: str = Field(description="File path or config location")
    message: str = Field(description="Human-readable description")
    severity: Severity = Field(default=Severity.ERROR)
    rule: str = Field(default="", description="Rule identifier (e.g. 'toml.syntax')")
    line: int | None = Field(default=None, description="Line number, if applicable")
    fixable: bool = Field(default=False, description="Whether auto-fix is available")


class ValidationResult(BaseModel):
    """Aggregated result from a validation run."""

    findings: list[Finding] = Field(default_factory=list)
    files_checked: int = Field(default=0)
    passed: bool = Field(default=True)

    def add(
        self,
        path: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        rule: str = "",
        line: int | None = None,
        fixable: bool = False,
    ) -> None:
        """Add a finding to the result."""
        self.findings.append(
            Finding(
                path=path,
                message=message,
                severity=severity,
                rule=rule,
                line=line,
                fixable=fixable,
            )
        )
        if severity == Severity.ERROR:
            self.passed = False

    @property
    def error_count(self) -> int:
        """Count of error-severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    def add_error(self, path: str, message: str, **kwargs: Any) -> None:
        """Add an error finding."""
        self.add(path, message, severity=Severity.ERROR, **kwargs)

    def add_warning(self, path: str, message: str, **kwargs: Any) -> None:
        """Add a warning finding."""
        self.add(path, message, severity=Severity.WARNING, **kwargs)

    def add_info(self, path: str, message: str, **kwargs: Any) -> None:
        """Add an info finding."""
        self.add(path, message, severity=Severity.INFO, **kwargs)

    @property
    def has_warnings(self) -> bool:
        """Whether any warning-severity findings exist."""
        return self.warning_count > 0

    def merge(self, other: ValidationResult) -> None:
        """Merge another result into this one."""
        self.findings.extend(other.findings)
        self.files_checked += other.files_checked
        if not other.passed:
            self.passed = False
