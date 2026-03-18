"""Domain classification for scripts and configs."""

from __future__ import annotations

import json
from pathlib import Path


def classify_domain(target: str, root: Path | None = None) -> str | None:
    """Classify a file path into its owning domain.

    Args:
        target: File path to classify.
        root: Project root. Defaults to cwd.

    Returns:
        Domain name string, or None if unclassified.
    """
    root = root or Path.cwd()
    catalog_path = root / "configs" / "mde-domain-catalog.json"
    if not catalog_path.exists():
        return None

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        return None

    domains = catalog.get("domains", {})
    if not isinstance(domains, dict):
        return None

    for domain_name, domain_def in domains.items():
        if not isinstance(domain_def, dict):
            continue
        patterns = domain_def.get("patterns", [])
        if not isinstance(patterns, list):
            continue
        for pattern in patterns:
            if isinstance(pattern, str) and pattern in target:
                return str(domain_name)
    return None
