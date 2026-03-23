"""Memory stack configuration validation.

Validates that the Honcho memory stack Docker files exist and are
correctly structured. This is a static check -- it does NOT require
the stack to be running. For runtime health checks, use
``mde-py memory verify``.
"""

from __future__ import annotations

from mde.domain.docker_stacks import MEMORY_COMPOSE
from mde.models.result import ValidationResult


def validate_memory() -> ValidationResult:
    """Validate memory stack configuration files exist."""
    result = ValidationResult()

    # Check compose file exists
    result.files_checked += 1
    if not MEMORY_COMPOSE.is_file():
        result.add_warning(
            str(MEMORY_COMPOSE),
            "Memory stack compose.yaml not found -- run setup or check docker/memory/",
            rule="memory.memory-compose-missing",
        )
        return result  # No point checking further if compose is missing

    # Check init.sql exists (required for pgvector extension)
    init_sql = MEMORY_COMPOSE.parent / "init.sql"
    result.files_checked += 1
    if not init_sql.is_file():
        result.add_warning(
            str(init_sql),
            "init.sql not found -- pgvector extension won't be created",
            rule="memory.init-sql-missing",
        )

    return result
