"""Logging facade — single import for all mde modules.

Usage::

    from mde.log import logger, get_tracer

This is the anti-corruption layer: if the logging backend changes again,
only this file and observability.py need updating.
"""

from __future__ import annotations

from loguru import logger

from mde.observability import get_tracer

__all__ = ["get_tracer", "logger"]
