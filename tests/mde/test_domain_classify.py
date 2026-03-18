"""Tests for domain classification."""

from __future__ import annotations

import json
from pathlib import Path

from mde.domain.classify import classify_domain


class TestDomainClassify:
    """Tests for domain classification."""

    def test_classify_known_domain(self, tmp_path: Path) -> None:
        """A matching pattern should return the domain name."""
        configs = tmp_path / "configs"
        configs.mkdir()
        catalog = configs / "mde-domain-catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "domains": {
                        "ai": {"patterns": ["scripts/install-agent"]},
                    }
                }
            )
        )
        result = classify_domain(
            "scripts/install-agent-stack.sh",
            root=tmp_path,
        )
        assert result == "ai"

    def test_classify_unknown_returns_none(self, tmp_path: Path) -> None:
        """An unmatched path should return None."""
        configs = tmp_path / "configs"
        configs.mkdir()
        catalog = configs / "mde-domain-catalog.json"
        catalog.write_text(json.dumps({"domains": {}}))
        result = classify_domain("random/file.txt", root=tmp_path)
        assert result is None
