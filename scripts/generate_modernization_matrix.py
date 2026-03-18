#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "configs" / "mde-modernization-matrix.json"

ECOSYSTEM_DECISIONS = {
    "python-cli": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-python-cli-mise-cache.md",
        "summary": "Global Python CLIs stay mise-owned and should converge on declarative pipx backend entries; repo Python dependencies stay in pyproject/uv lockfiles.",
    },
    "node-cli": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-node-cli-mise-cache.md",
        "summary": "Global Node CLIs stay mise-owned through the npm backend with bun as the configured package manager and cache provider.",
    },
    "go-cli": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-go-tooling-mise-cache.md",
        "summary": "Go runtime stays a direct mise entry; any remaining Go-installed CLIs must move to declarative ownership and reuse module/build caches.",
    },
    "rust-cli": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-rust-tooling-mise-cache.md",
        "summary": "Rust runtime stays a direct mise entry; cargo-installed CLIs must be reconciled against declarative ownership and cargo caches.",
    },
    "sdk-mcp": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-sdk-mcp-mise-cache.md",
        "summary": "SDK and MCP CLIs remain mise-owned and must inherit the backend-native cache policy of their ecosystem instead of bespoke installer scripts.",
    },
    "container-dev": {
        "decision_record_path": "docs/research/ecosystem-decisions/2026-03-14-container-dev-mise-cache.md",
        "summary": "Container/dev tooling stays mise-first where possible and should preserve backend layer caches rather than forcing cold rebuilds.",
    },
}

CACHE_PROFILES: dict[str, dict[str, Any]] = {
    "mise-runtime": {
        "package_manager_backend": "mise",
        "cache_mechanism": "mise-managed install directories and backend downloads",
        "cache_directory_or_source": "$HOME/.local/share/mise/installs + backend-specific download caches",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "mise install",
        "cache_pruning_allowed": False,
        "cache_pruning_command": None,
        "cache_policy_mandatory_for_automation": True,
    },
    "python-uv": {
        "package_manager_backend": "uv",
        "cache_mechanism": "uv wheel/source cache reused by host scripts and automation",
        "cache_directory_or_source": "$UV_CACHE_DIR (defaults to $HOME/Library/Caches/uv on macOS, $HOME/.cache/uv elsewhere)",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "uv cache dir && mise install uv",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "uv cache prune",
        "cache_policy_mandatory_for_automation": True,
    },
    "python-pipx": {
        "package_manager_backend": "pipx",
        "cache_mechanism": "pipx-managed virtualenv reuse plus pip download cache",
        "cache_directory_or_source": "$PIPX_HOME + pip cache",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "mise install && mise exec -- pipx list",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "pipx uninstall-all",
        "cache_policy_mandatory_for_automation": True,
    },
    "node-bun-npm": {
        "package_manager_backend": "mise npm backend with bun package manager",
        "cache_mechanism": "bun global package store and tarball cache reused through mise npm backend",
        "cache_directory_or_source": "$BUN_INSTALL/install/cache",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "mise install",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "bun pm cache rm",
        "cache_policy_mandatory_for_automation": True,
    },
    "go-mod": {
        "package_manager_backend": "go",
        "cache_mechanism": "Go build cache and module cache",
        "cache_directory_or_source": "$GOCACHE + $GOMODCACHE",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "go env GOCACHE GOMODCACHE",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "go clean -cache -modcache",
        "cache_policy_mandatory_for_automation": True,
    },
    "cargo": {
        "package_manager_backend": "cargo",
        "cache_mechanism": "cargo registry and git cache plus managed install root",
        "cache_directory_or_source": "$CARGO_HOME/registry + $CARGO_HOME/git",
        "cache_scope": "backend-native",
        "cache_warming_supported": True,
        "cache_warming_command": "cargo fetch",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "cargo cache -a or rm within $CARGO_HOME if explicitly approved",
        "cache_policy_mandatory_for_automation": True,
    },
    "container-layers": {
        "package_manager_backend": "devcontainer/docker layer cache",
        "cache_mechanism": "OCI layer cache and builder cache mounts",
        "cache_directory_or_source": "builder-managed layer cache",
        "cache_scope": "shared",
        "cache_warming_supported": True,
        "cache_warming_command": "mise run mde:devcontainer:image:build",
        "cache_pruning_allowed": True,
        "cache_pruning_command": "docker builder prune",
        "cache_policy_mandatory_for_automation": True,
    },
    "system-exception": {
        "package_manager_backend": "exception-managed installer",
        "cache_mechanism": "installer-managed download caches only",
        "cache_directory_or_source": "installer-managed",
        "cache_scope": "exception",
        "cache_warming_supported": False,
        "cache_warming_command": None,
        "cache_pruning_allowed": False,
        "cache_pruning_command": None,
        "cache_policy_mandatory_for_automation": False,
    },
    "none": {
        "package_manager_backend": "none",
        "cache_mechanism": "none",
        "cache_directory_or_source": "none",
        "cache_scope": "none",
        "cache_warming_supported": False,
        "cache_warming_command": None,
        "cache_pruning_allowed": False,
        "cache_pruning_command": None,
        "cache_policy_mandatory_for_automation": False,
    },
}

SCRIPT_META: dict[str, dict[str, Any]] = {
    "scripts/install-agent-stack.sh": {
        "queue": "A",
        "priority": 1,
        "purpose": "Reconcile the agent runtime and CLI stack on the host.",
        "recommended_target_state": "reconcile-declared-config",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "bash scripts/install-agent-stack.sh",
        "declaration_mode": "transition-exception",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "python-uv",
        "docs_prompts_skills_registries_impacted": [
            "configs/mde-tool-ownership.json",
            "configs/mde-modernization-matrix.json",
            "docs/toolchain-precedence.md",
            ".agents/skills/mde-agent-runtime-contract/SKILL.md",
            ".agents/skills/mde-package-cache-policy/SKILL.md",
        ],
    },
    "scripts/install-langchain-cli-tools.sh": {
        "queue": "A",
        "priority": 2,
        "purpose": "Reconcile the LangChain, LangGraph, LangSmith, and adjacent Python CLI toolchain.",
        "recommended_target_state": "reconcile-declared-config",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "bash scripts/install-langchain-cli-tools.sh",
        "declaration_mode": "transition-exception",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "python-uv",
        "docs_prompts_skills_registries_impacted": [
            "configs/mde-tool-ownership.json",
            "configs/mde-modernization-matrix.json",
            "scripts/verify-langchain-tools.sh",
            "docs/toolchain-precedence.md",
            ".agents/skills/mde-python-backend-selection/SKILL.md",
        ],
    },
    "scripts/install-aws-k8s-tools.sh": {
        "queue": "A",
        "priority": 3,
        "purpose": "Reconcile AWS and Kubernetes host CLI tooling.",
        "recommended_target_state": "migrated",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "uv run mde-py install aws-k8s",
        "declaration_mode": "mise-declared",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "system-exception",
    },
    "scripts/macos-dev-maintenance.sh": {
        "queue": "A",
        "priority": 4,
        "purpose": "Run the host maintenance and update lifecycle.",
        "recommended_target_state": "reconcile-declared-config",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise run mde:update",
        "declaration_mode": "transition-exception",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "python-uv",
    },
    "scripts/ensure-managed-configs.sh": {
        "queue": "A",
        "priority": 5,
        "purpose": "Synchronize managed shell and environment configuration.",
        "recommended_target_state": "validator-or-reconciler",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise run mde:sync-dotfiles",
        "declaration_mode": "reconciler",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/mde-migrate-to-mise.sh": {
        "queue": "A",
        "priority": 6,
        "purpose": "Classify and migrate legacy global tools into the declarative mise ownership model.",
        "recommended_target_state": "migration-tool",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise run mde:migrate:global-tools -- --dry-run",
        "declaration_mode": "migration-helper",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n", "python3 -m json.tool"],
        "cache_profile": "none",
    },
    "scripts/mde-drift-check.sh": {
        "queue": "A",
        "priority": 7,
        "purpose": "Validate ownership and toolchain drift against the declared contract.",
        "recommended_target_state": "validator-only",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise run mde:drift",
        "declaration_mode": "validator",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/mde-remediate.sh": {
        "queue": "A",
        "priority": 8,
        "purpose": "Run deterministic host remediation against the current contract.",
        "recommended_target_state": "reconcile-declared-config",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise run mde:remediate",
        "declaration_mode": "reconciler",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/setup-mcp-servers.sh": {
        "queue": "A",
        "priority": 9,
        "purpose": "Configure MCP server wrappers and supporting host tools.",
        "recommended_target_state": "reconcile-declared-config",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "bash scripts/setup-mcp-servers.sh",
        "declaration_mode": "reconciler",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/setup-skypilot-aws.sh": {
        "queue": "A",
        "priority": 10,
        "purpose": "Configure the SkyPilot AWS host integration and prerequisites.",
        "recommended_target_state": "exception-or-reconciler",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "bash scripts/setup-skypilot-aws.sh",
        "declaration_mode": "exception-wrapper",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "system-exception",
    },
    "scripts/mde-research-autoimprove.sh": {
        "queue": "C",
        "priority": 24,
        "purpose": "Run the bounded multi-agent research and auto-improvement loop.",
        "recommended_target_state": "validator-or-reconciler",
        "owning_team": "mde-autoresearch-team",
        "proof_command": "mise run mde:research:autoimprove -- --report",
        "declaration_mode": "validator",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/devcontainer-image-build.sh": {
        "queue": "C",
        "priority": 28,
        "purpose": "Build the local devcontainer image used for smoke verification.",
        "recommended_target_state": "validator-or-reconciler",
        "owning_team": "devcontainer-image-release-team",
        "proof_command": "mise run mde:devcontainer:image:build",
        "declaration_mode": "reconciler",
        "decision_record_path": ECOSYSTEM_DECISIONS["container-dev"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "container-layers",
    },
    "scripts/devcontainer-image-smoke.sh": {
        "queue": "C",
        "priority": 29,
        "purpose": "Run the devcontainer image smoke contract.",
        "recommended_target_state": "validator-only",
        "owning_team": "devcontainer-image-release-team",
        "proof_command": "mise run mde:devcontainer:image:smoke",
        "declaration_mode": "validator",
        "decision_record_path": ECOSYSTEM_DECISIONS["container-dev"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "container-layers",
    },
    "scripts/generate-modernization-matrix.sh": {
        "queue": "A",
        "priority": 0,
        "purpose": "Thin compatibility shim that delegates matrix generation to the Python implementation.",
        "recommended_target_state": "validator-or-reconciler",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "bash scripts/generate-modernization-matrix.sh",
        "declaration_mode": "shim",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["shellcheck", "bash -n"],
        "cache_profile": "none",
    },
    "scripts/generate_modernization_matrix.py": {
        "queue": "A",
        "priority": 0,
        "purpose": "Generate the machine-readable modernization matrix from declarative registries.",
        "recommended_target_state": "native-helper",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "python3 scripts/generate_modernization_matrix.py",
        "declaration_mode": "native-helper",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m py_compile"],
        "cache_profile": "none",
    },
}

TASK_META: dict[str, dict[str, Any]] = {
    "mde:sync-dotfiles": {
        "queue": "C",
        "priority": 14,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:update": {"queue": "C", "priority": 15, "owning_team": "mde-update-remediation-team"},
    "mde:update:fast": {"queue": "C", "priority": 16, "owning_team": "mde-update-remediation-team"},
    "mde:verify": {"queue": "C", "priority": 17, "owning_team": "mde-update-remediation-team"},
    "mde:agent:preflight": {
        "queue": "C",
        "priority": 18,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:agent:verify": {
        "queue": "C",
        "priority": 19,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:agent:report": {
        "queue": "C",
        "priority": 20,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:test": {"queue": "C", "priority": 21, "owning_team": "mde-update-remediation-team"},
    "mde:drift": {"queue": "C", "priority": 22, "owning_team": "mde-update-remediation-team"},
    "mde:migrate:global-tools": {
        "queue": "C",
        "priority": 23,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:research:autoimprove": {
        "queue": "C",
        "priority": 24,
        "owning_team": "mde-autoresearch-team",
    },
    "mde:status": {"queue": "C", "priority": 25, "owning_team": "mde-update-remediation-team"},
    "mde:remediate": {"queue": "C", "priority": 26, "owning_team": "mde-update-remediation-team"},
    "mde:bootstrap:devcontainer": {
        "queue": "C",
        "priority": 27,
        "owning_team": "devcontainer-setup-sdlc-team",
    },
    "mde:devcontainer:image:build": {
        "queue": "C",
        "priority": 28,
        "owning_team": "devcontainer-image-release-team",
    },
    "mde:devcontainer:image:smoke": {
        "queue": "C",
        "priority": 29,
        "owning_team": "devcontainer-image-release-team",
    },
    "mde:mcp:sync": {"queue": "C", "priority": 30, "owning_team": "mde-update-remediation-team"},
    "mde:agents:review": {
        "queue": "C",
        "priority": 31,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:secrets:refresh": {
        "queue": "C",
        "priority": 32,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:secrets:restore:keychain": {
        "queue": "C",
        "priority": 33,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:secrets:backup:1password": {
        "queue": "C",
        "priority": 34,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:shell:profile:install-bench": {
        "queue": "C",
        "priority": 35,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:shell:profile:bench": {
        "queue": "C",
        "priority": 36,
        "owning_team": "mde-update-remediation-team",
    },
    "mde:team:modern-best-practices": {
        "queue": "C",
        "priority": 37,
        "owning_team": "mde-update-remediation-team",
    },
}

TOOL_META: dict[str, dict[str, Any]] = {
    "python": {
        "backend_type": "runtime",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mise-declarative-entry",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.python",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where python",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "python3 --version"],
        "cache_profile": "mise-runtime",
    },
    "node": {
        "backend_type": "runtime",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mise-declarative-entry",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.node",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where node",
        "decision_record_path": ECOSYSTEM_DECISIONS["node-cli"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "node --version"],
        "cache_profile": "mise-runtime",
    },
    "bun": {
        "backend_type": "runtime",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mixed-mise-and-bun-global",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.bun",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where bun",
        "decision_record_path": ECOSYSTEM_DECISIONS["node-cli"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "bun --version"],
        "cache_profile": "mise-runtime",
    },
    "go": {
        "backend_type": "runtime",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mixed-mise-and-go-install",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.go",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where go",
        "decision_record_path": ECOSYSTEM_DECISIONS["go-cli"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "go env GOCACHE GOMODCACHE"],
        "cache_profile": "mise-runtime",
    },
    "rustc": {
        "backend_type": "runtime",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mixed-mise-and-cargo-install",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.rust",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where rust",
        "decision_record_path": ECOSYSTEM_DECISIONS["rust-cli"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "rustc --version"],
        "cache_profile": "mise-runtime",
    },
    "uv": {
        "backend_type": "python-tooling",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mixed-mise-and-imperative-uv",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.uv",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where uv",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["uv --version", "uv cache dir"],
        "cache_profile": "python-uv",
    },
    "pixi": {
        "backend_type": "python-tooling",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mixed-mise-and-imperative-pixi",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.pixi",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "mise where pixi",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["pixi --version"],
        "cache_profile": "python-uv",
    },
    "codex": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mise-declarative-entry",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:@openai/codex",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v codex",
        "decision_record_path": ECOSYSTEM_DECISIONS["node-cli"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "codex --help"],
        "cache_profile": "node-bun-npm",
    },
    "devcontainer": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mise-declarative-entry",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:@devcontainers/cli",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v devcontainer",
        "decision_record_path": ECOSYSTEM_DECISIONS["container-dev"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "devcontainer --version"],
        "cache_profile": "node-bun-npm",
    },
    "gemini": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mixed-mise-and-bun-global",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:@google/gemini-cli",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v gemini",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "gemini --help"],
        "cache_profile": "node-bun-npm",
    },
    "claude": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mixed-mise-and-bun-global",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:@anthropic-ai/claude-code",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v claude",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "claude --help"],
        "cache_profile": "node-bun-npm",
    },
    "opencode": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mixed-mise-and-bun-global",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:opencode-ai",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v opencode",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "opencode --help"],
        "cache_profile": "node-bun-npm",
    },
    "mcp-inspector": {
        "backend_type": "node-cli",
        "package_manager": "npm-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "mixed-mise-and-imperative-node-global",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "npm:@modelcontextprotocol/inspector",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v mcp-inspector",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["bun --version", "mcp-inspector --help"],
        "cache_profile": "node-bun-npm",
    },
    "langchain-cli": {
        "backend_type": "python-cli",
        "package_manager": "pipx-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "imperative-uv-tool-install",
        "backend_native_declarative_config_exists": True,
        "backend_native_config_path": "/Users/rmanaloto/.config/mise/config.toml (pipx: entries)",
        "recommended_target_state": "mise + backend-native declarative config",
        "mise_linkage_method": "pipx:langchain-cli",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v langchain",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m pipx --version", "langchain --help"],
        "cache_profile": "python-pipx",
    },
    "langgraph-cli": {
        "backend_type": "python-cli",
        "package_manager": "pipx-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "imperative-uv-tool-install",
        "backend_native_declarative_config_exists": True,
        "backend_native_config_path": "/Users/rmanaloto/.config/mise/config.toml (pipx: entries)",
        "recommended_target_state": "mise + backend-native declarative config",
        "mise_linkage_method": "pipx:langgraph-cli",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v langgraph",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m pipx --version", "langgraph --help"],
        "cache_profile": "python-pipx",
    },
    "langsmith-mcp-server": {
        "backend_type": "python-cli",
        "package_manager": "pipx-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "imperative-uv-tool-install-or-git-clone",
        "backend_native_declarative_config_exists": True,
        "backend_native_config_path": "/Users/rmanaloto/.config/mise/config.toml (pipx: entries)",
        "recommended_target_state": "mise + backend-native declarative config",
        "mise_linkage_method": "pipx:langsmith-mcp-server",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v langsmith-mcp-server",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m pipx --version", "langsmith-mcp-server --help"],
        "cache_profile": "python-pipx",
    },
    "deepagents-cli": {
        "backend_type": "python-cli",
        "package_manager": "pipx-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "imperative-uv-tool-install",
        "backend_native_declarative_config_exists": True,
        "backend_native_config_path": "/Users/rmanaloto/.config/mise/config.toml (pipx: entries)",
        "recommended_target_state": "mise + backend-native declarative config",
        "mise_linkage_method": "pipx:deepagents",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v deepagents",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m pipx --version", "deepagents --help"],
        "cache_profile": "python-pipx",
    },
    "fabric": {
        "backend_type": "python-cli",
        "package_manager": "pipx-backend",
        "declaration_mode": "mise + backend-native declarative config",
        "current_install_config_method": "imperative-uv-tool-install",
        "backend_native_declarative_config_exists": True,
        "backend_native_config_path": "/Users/rmanaloto/.config/mise/config.toml (pipx: entries)",
        "recommended_target_state": "mise + backend-native declarative config",
        "mise_linkage_method": "pipx:fabric",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v fabric",
        "decision_record_path": ECOSYSTEM_DECISIONS["python-cli"]["decision_record_path"],
        "native_validation_toolchain": ["python3 -m pipx --version", "fabric --help"],
        "cache_profile": "python-pipx",
    },
    "pitchfork": {
        "backend_type": "generic-cli",
        "package_manager": "mise",
        "declaration_mode": "mise declarative entry",
        "current_install_config_method": "mise-declarative-entry",
        "backend_native_declarative_config_exists": False,
        "backend_native_config_path": None,
        "recommended_target_state": "mise declarative entry",
        "mise_linkage_method": "tools.pitchfork",
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v pitchfork",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor", "pitchfork --help"],
        "cache_profile": "mise-runtime",
    },
    "hk": {
        "backend_type": "generic-cli",
        "package_manager": "decision-pending",
        "declaration_mode": "decision-required",
        "current_install_config_method": "unresolved",
        "backend_native_declarative_config_exists": None,
        "backend_native_config_path": None,
        "recommended_target_state": "decision-required",
        "mise_linkage_method": None,
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v hk",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor"],
        "cache_profile": "none",
    },
    "fnox": {
        "backend_type": "generic-cli",
        "package_manager": "decision-pending",
        "declaration_mode": "decision-required",
        "current_install_config_method": "unresolved",
        "backend_native_declarative_config_exists": None,
        "backend_native_config_path": None,
        "recommended_target_state": "decision-required",
        "mise_linkage_method": None,
        "owning_team": "mde-update-remediation-team",
        "proof_command": "command -v fnox",
        "decision_record_path": ECOSYSTEM_DECISIONS["sdk-mcp"]["decision_record_path"],
        "native_validation_toolchain": ["mise doctor"],
        "cache_profile": "none",
    },
}

INSTALL_MARKERS = [
    ("uv tool install", "imperative-uv-tool-install", "python-cli", "uv"),
    ("bun add -g", "imperative-bun-global", "node-cli", "bun"),
    ("go install", "imperative-go-install", "go-cli", "go"),
    ("cargo install", "imperative-cargo-install", "rust-cli", "cargo"),
    ("pipx install", "imperative-pipx-install", "python-cli", "pipx"),
    ("pip install --user", "imperative-pip-user-install", "python-cli", "pip"),
    ("brew install", "imperative-brew-install", "system-package", "brew"),
    ("mise install", "mise-imperative-reconcile", "runtime-or-cli", "mise"),
    ("mise use -g", "mise-imperative-reconcile", "runtime-or-cli", "mise"),
    ("mise upgrade", "mise-imperative-upgrade", "runtime-or-cli", "mise"),
    ("pixi global install", "imperative-pixi-global", "python-cli", "pixi"),
    ("curl -fsSL", "curl-installer", "system-installer", "curl"),
    ("curl -LsSf", "curl-installer", "system-installer", "curl"),
]

CACHE_MARKERS = [
    ("UV_CACHE_DIR", "python-uv"),
    ("PIPX_HOME", "python-pipx"),
    ("BUN_INSTALL", "node-bun-npm"),
    ("GOCACHE", "go-mod"),
    ("GOMODCACHE", "go-mod"),
    ("CARGO_HOME", "cargo"),
    ("RUSTUP_HOME", "cargo"),
    ("docker build", "container-layers"),
    ("devcontainer build", "container-layers"),
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def detect_methods(text: str) -> tuple[list[str], list[str], list[str]]:
    methods: list[str] = []
    backends: list[str] = []
    managers: list[str] = []
    for needle, method, backend, manager in INSTALL_MARKERS:
        if needle in text:
            methods.append(method)
            backends.append(backend)
            managers.append(manager)
    if not methods:
        return ["no-install-detected"], ["none"], ["none"]
    return sorted(set(methods)), sorted(set(backends)), sorted(set(managers))


def detect_cache_profiles(text: str, fallback: str = "none") -> list[str]:
    found = {profile for needle, profile in CACHE_MARKERS if needle in text}
    if not found:
        return [fallback]
    return sorted(found)


def validation_coverage(root: Path, path_str: str) -> str:
    refs = subprocess.run(
        [
            "rg",
            "-l",
            "-F",
            path_str,
            str(root / "scripts"),
            str(root / "docs"),
            str(root / "configs"),
            str(root / "prompts"),
            str(root / ".agents"),
            str(root / ".mise.toml"),
            str(root / "AGENTS.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [
        line.strip()
        for line in refs.stdout.splitlines()
        if line.strip() and line.strip() != str(root / path_str)
    ]
    test_refs = [line for line in lines if "/scripts/tests/" in line or line.endswith(".test.sh")]
    contract_refs = [
        line
        for line in lines
        if "/docs/" in line
        or "/prompts/" in line
        or "/configs/agent-teams/" in line
        or line.endswith(".toml")
        or line.endswith("AGENTS.md")
    ]
    if test_refs and contract_refs:
        return "covered"
    if test_refs or contract_refs:
        return "partial"
    return "none"


def task_validation_coverage(root: Path, task_name: str) -> str:
    refs = subprocess.run(
        [
            "rg",
            "-l",
            "-F",
            task_name,
            str(root / "scripts"),
            str(root / "docs"),
            str(root / "configs"),
            str(root / "prompts"),
            str(root / ".agents"),
            str(root / "AGENTS.md"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line.strip() for line in refs.stdout.splitlines() if line.strip()]
    test_refs = [line for line in lines if "/scripts/tests/" in line or line.endswith(".test.sh")]
    contract_refs = [
        line
        for line in lines
        if "/docs/" in line
        or "/prompts/" in line
        or "/configs/agent-teams/" in line
        or line.endswith("AGENTS.md")
    ]
    if test_refs and contract_refs:
        return "covered"
    if test_refs or contract_refs:
        return "partial"
    return "none"


def default_script_owner(path_str: str) -> str:
    if "octokit" in path_str or "octokit-sdlc" in path_str:
        return "octokit-sdlc-team"
    if "devcontainer" in path_str:
        return "devcontainer-setup-sdlc-team"
    if "mde-research-autoimprove" in path_str or "mde-autoresearch" in path_str:
        return "mde-autoresearch-team"
    return "mde-update-remediation-team"


def default_script_purpose(path: Path) -> str:
    stem = path.stem
    return f"Inventory entry for {stem.replace('-', ' ')}."


def normalize_list(values: list[str]) -> str | list[str]:
    return values[0] if len(values) == 1 else values


def build_cache_policy(profile_name: str | list[str]) -> dict[str, Any] | list[dict[str, Any]]:
    if isinstance(profile_name, list):
        return [{"profile": name, **CACHE_PROFILES[name]} for name in profile_name]
    return {"profile": profile_name, **CACHE_PROFILES[profile_name]}


def load_ownership(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_domain_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def classify_domain(query: str, domain_catalog: dict[str, Any]) -> str:
    text = query.lower()
    best_id = domain_catalog.get("routing_policy", {}).get("default_domain", "mise-core")
    best_score = -1
    for domain in domain_catalog["domains"]:
        score = 0
        for token in domain.get("keywords", []):
            if token.lower() in text:
                score += 3
        for token in domain.get("ecosystem_aliases", []):
            if token.lower() in text:
                score += 2
        for token in domain.get("file_globs", []):
            token = token.lower().replace("*", "")
            if token and token in text:
                score += 4
        if score > best_score:
            best_id = domain["id"]
            best_score = score
    return best_id


def domain_payload(domain_id: str, domain_catalog: dict[str, Any]) -> dict[str, Any]:
    domains = {item["id"]: item for item in domain_catalog["domains"]}
    domain = domains[domain_id]
    return {
        "ecosystem_domain": domain_id,
        "domain_team_id": domain["team_id"],
        "project_authority": domain["project_authority"],
        "global_cli_authority_mode": domain["global_cli_authority_mode"],
        "reference_bundle_id": domain["reference_bundle_id"],
        "preset_bundle_id": domain["preset_bundle_id"],
        "cache_contract": domain["cache_contract"],
        "derived_from_authority": domain["derived_from_authority"],
    }


def build_scripts(root: Path, domain_catalog: dict[str, Any]) -> list[dict[str, Any]]:
    scripts_dir = root / "scripts"
    scripts: list[dict[str, Any]] = []
    for path in sorted(
        p for p in scripts_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ):
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        methods, backends, managers = detect_methods(text)
        meta = SCRIPT_META.get(rel, {})
        is_user_facing = rel.startswith("scripts/") and not any(
            part in rel for part in ["/lib/", "/tests/", "/teams/"]
        )
        cache_profiles = detect_cache_profiles(text, meta.get("cache_profile", "none"))
        script_domain_id = meta.get("ecosystem_domain", classify_domain(rel, domain_catalog))
        scripts.append(
            {
                "id": rel.replace("/", ":"),
                "path": rel,
                "kind": "script-surface",
                "owner_surface": rel,
                "purpose": meta.get("purpose", default_script_purpose(path)),
                "user_facing": meta.get("user_facing", is_user_facing),
                "queue": meta.get("queue", "D"),
                "priority": meta.get("priority"),
                "current_install_config_method": normalize_list(methods),
                "backend_type": normalize_list(backends),
                "package_manager": normalize_list(managers),
                "declaration_mode": meta.get("declaration_mode", "review-and-classify"),
                "backend_native_declarative_config_exists": meta.get(
                    "backend_native_declarative_config_exists",
                    None if backends != ["none"] else False,
                ),
                "backend_native_config_path": meta.get("backend_native_config_path"),
                "mise_linkage_method": meta.get("mise_linkage_method"),
                "recommended_target_state": meta.get(
                    "recommended_target_state", "review-and-classify"
                ),
                "current_validation_coverage": validation_coverage(root, rel),
                "owning_team": meta.get("owning_team", default_script_owner(rel)),
                "owning_implementation_language": meta.get(
                    "owning_implementation_language",
                    "shell"
                    if path.suffix == ".sh"
                    else "python"
                    if path.suffix == ".py"
                    else path.suffix.lstrip("."),
                ),
                "native_validation_toolchain": meta.get(
                    "native_validation_toolchain",
                    ["shellcheck", "bash -n"]
                    if path.suffix == ".sh"
                    else ["python3 -m py_compile"]
                    if path.suffix == ".py"
                    else [],
                ),
                "proof_command": meta.get(
                    "proof_command", f"bash {rel}" if path.suffix == ".sh" else f"python3 {rel}"
                ),
                "decision_record_path": meta.get("decision_record_path"),
                "allowed_wrapper_status": meta.get(
                    "allowed_wrapper_status",
                    "transition-exception" if "TRANSITION_EXCEPTION" in text else "allowed",
                ),
                "cache_policy": build_cache_policy(
                    cache_profiles if len(cache_profiles) > 1 else cache_profiles[0]
                ),
                "docs_prompts_skills_registries_impacted": meta.get(
                    "docs_prompts_skills_registries_impacted", []
                ),
                **domain_payload(script_domain_id, domain_catalog),
            }
        )
    return scripts


def build_tasks(root: Path, domain_catalog: dict[str, Any]) -> list[dict[str, Any]]:
    toml_text = (root / ".mise.toml").read_text(encoding="utf-8")
    task_blocks = re.finditer(
        r'^\[tasks\."([^"]+)"\]\n(.*?)(?=^\[tasks\.|\Z)', toml_text, re.MULTILINE | re.DOTALL
    )
    tasks: list[dict[str, Any]] = []
    for match in task_blocks:
        name = match.group(1)
        body = match.group(2)
        description_match = re.search(r'^description = "(.*)"$', body, re.MULTILINE)
        run_match = re.search(r'^run = "(.*)"$', body, re.MULTILINE)
        description = description_match.group(1) if description_match else ""
        run = run_match.group(1) if run_match else ""
        meta = TASK_META.get(name, {})
        decision_key = "container-dev" if "devcontainer" in name else "sdk-mcp"
        task_domain_id = meta.get(
            "ecosystem_domain", classify_domain(f"{name} {run}", domain_catalog)
        )
        tasks.append(
            {
                "id": name,
                "kind": "mde-task",
                "owner_surface": ".mise.toml",
                "purpose": description or f"Run {name}",
                "user_facing": True,
                "queue": meta.get("queue", "C"),
                "priority": meta.get("priority"),
                "current_install_config_method": "mise-task-entrypoint",
                "backend_type": "task-runner",
                "package_manager": "mise",
                "declaration_mode": "mise task entry",
                "backend_native_declarative_config_exists": True,
                "backend_native_config_path": ".mise.toml",
                "mise_linkage_method": f"tasks.{name}",
                "recommended_target_state": "validator-or-reconciler",
                "current_validation_coverage": task_validation_coverage(root, name),
                "owning_team": meta.get("owning_team", "mde-update-remediation-team"),
                "owning_implementation_language": "toml",
                "native_validation_toolchain": ["mise task ls", "mise run --help"],
                "proof_command": f"mise run {name}",
                "run_command": run,
                "decision_record_path": ECOSYSTEM_DECISIONS[decision_key]["decision_record_path"],
                "cache_policy": build_cache_policy(
                    "container-layers" if "devcontainer" in name else "none"
                ),
                "docs_prompts_skills_registries_impacted": [
                    ".mise.toml",
                    "configs/mde-modernization-matrix.json",
                    "AGENTS.md",
                    ".agents/AGENTS.md",
                ],
                **domain_payload(task_domain_id, domain_catalog),
            }
        )
    return tasks


def build_tools(
    root: Path, ownership: dict[str, Any], domain_catalog: dict[str, Any]
) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for item in ownership.get("tools", []):
        meta = TOOL_META.get(item["id"], {})
        cache_profile = meta.get("cache_profile", "none")
        tool_domain_id = (
            item.get("ecosystem_domain")
            or meta.get("ecosystem_domain")
            or classify_domain(f"{item['id']} {item['command']}", domain_catalog)
        )
        payload = domain_payload(tool_domain_id, domain_catalog)
        for key in (
            "project_authority",
            "global_cli_authority_mode",
            "reference_bundle_id",
            "preset_bundle_id",
            "cache_contract",
            "derived_from_authority",
        ):
            if item.get(key) is not None:
                payload[key] = item[key]
        payload["ecosystem_domain"] = item.get("ecosystem_domain", tool_domain_id)
        payload["domain_team_id"] = item.get("domain_team_id", payload["domain_team_id"])
        tools.append(
            {
                "id": item["id"],
                "command": item["command"],
                "tool_class": item["tool_class"],
                "owner": item["owner"],
                "preflight_required": item.get("preflight_required", False),
                "current_install_config_method": meta.get(
                    "current_install_config_method", "review-and-classify"
                ),
                "backend_type": meta.get("backend_type", "generic-cli"),
                "package_manager": meta.get("package_manager", "mise"),
                "declaration_mode": meta.get("declaration_mode", "review-and-classify"),
                "backend_native_declarative_config_exists": meta.get(
                    "backend_native_declarative_config_exists"
                ),
                "backend_native_config_path": meta.get("backend_native_config_path"),
                "recommended_target_state": meta.get(
                    "recommended_target_state", "mise declarative entry"
                ),
                "mise_linkage_method": meta.get("mise_linkage_method"),
                "final_ownership_class": meta.get(
                    "recommended_target_state", "mise declarative entry"
                ),
                "owning_team": meta.get("owning_team", "mde-update-remediation-team"),
                "owning_implementation_language": meta.get(
                    "owning_implementation_language", "toml"
                ),
                "native_validation_toolchain": meta.get(
                    "native_validation_toolchain", ["mise doctor"]
                ),
                "proof_command": meta.get("proof_command", f"command -v {item['command']}"),
                "decision_record_path": meta.get("decision_record_path"),
                "cache_policy": build_cache_policy(cache_profile),
                **payload,
            }
        )
    return tools


def build_matrix(root: Path) -> dict[str, Any]:
    ownership = load_ownership(root / "configs" / "mde-tool-ownership.json")
    domain_catalog = load_domain_catalog(root / "configs" / "mde-domain-catalog.json")
    scripts = build_scripts(root, domain_catalog)
    tasks = build_tasks(root, domain_catalog)
    tools = build_tools(root, ownership, domain_catalog)
    return {
        "version": 3,
        "generated_at": subprocess.run(
            ["date", "+%Y-%m-%d"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "policy": {
            "top_level_authority": "mise",
            "declaration_precedence": [
                "mise + backend-native declarative config",
                "mise declarative entry",
                "native project manifest",
                "exception",
                "removed",
            ],
            "cache_policy_defaults": {
                "reuse_caches_by_default": True,
                "cold_installs_are_exception_only": True,
                "native_cache_owners": [
                    "uv",
                    "pipx",
                    "bun/npm backend",
                    "go",
                    "cargo",
                    "container layer cache",
                ],
            },
            "notes": [
                "Global runtimes, global CLIs, and SDK CLIs remain mise-owned.",
                "Prefer backend-native declarative configuration when the backend exposes a modern config surface.",
                "Scripts are reconcilers, validators, migration helpers, or explicit exception handlers, not the authoritative install source.",
                "Automation must reuse declared backend caches unless an explicit reproducibility exception says otherwise.",
                "Domain ownership, preset coverage, mirrored references, and learning writeback are required contract surfaces.",
            ],
        },
        "domain_catalog_version": domain_catalog["version"],
        "ecosystem_decisions": [{"id": key, **value} for key, value in ECOSYSTEM_DECISIONS.items()],
        "cache_profiles": [{"profile": key, **value} for key, value in CACHE_PROFILES.items()],
        "coverage": {
            "scripts_total": len(scripts),
            "tasks_total": len(tasks),
            "global_tools_total": len(tools),
        },
        "global_tools": tools,
        "public_tasks": tasks,
        "script_surfaces": scripts,
    }


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    matrix = build_matrix(ROOT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
