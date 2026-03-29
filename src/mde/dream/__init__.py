"""Dream module — self-improvement pipeline for the MDE project.

CLI subcommand: ``mde-py auto-dream`` (module directory stays ``dream``
to avoid Python package hyphen issues).

Implements a 3-stage feedback loop:
  extract  → scan signal sources for recurring patterns
  propose  → generate improvement proposals with promotion ladder
  apply    → execute approved proposals (tiered autonomy)
  status   → show pipeline state and pattern inventory
"""

from __future__ import annotations
