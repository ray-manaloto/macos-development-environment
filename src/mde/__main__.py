"""CLI entrypoint: python -m mde <subcommand>."""

from __future__ import annotations

import sys

from mde.cli import run


def main() -> int:
    """Run the MDE CLI."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
