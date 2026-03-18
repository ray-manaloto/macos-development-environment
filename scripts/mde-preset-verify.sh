#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
DOMAIN_FILTER="${1:-${MDE_ACTIVE_DOMAIN:-}}"

python3 - "$MDE_REPO_ROOT" "$DOMAIN_FILTER" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
domain_filter = sys.argv[2].strip()


def resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_json(env_name: str, default_rel: str) -> dict:
    path = resolve_path(os.environ.get(env_name, str(repo_root / default_rel)), repo_root)
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def preset_domain_ids(preset: dict) -> list[str]:
    values = preset.get('domain_ids') or preset.get('domains') or ([preset.get('domain')] if preset.get('domain') else [])
    return [value for value in values if value]


def preset_source_refs(preset: dict) -> list[str]:
    values = preset.get('reference_source_groups') or preset.get('source_ids') or []
    if isinstance(values, str):
        values = [values]
    return [value for value in values if value]


def preset_learning_refs(preset: dict) -> list[str]:
    values = preset.get('learning_record_ids') or preset.get('learning_ids') or []
    if isinstance(values, str):
        values = [values]
    return [value for value in values if value]


domain_catalog = load_json('MDE_DOMAIN_CATALOG_FILE', 'configs/mde-domain-catalog.json')
refs = load_json('MDE_REFERENCE_SOURCES_FILE', 'configs/mde-reference-sources.json')
preset_catalog = load_json('MDE_PRESET_CATALOG_FILE', 'configs/mde-preset-catalog.json')
learning_registry = load_json('MDE_LEARNING_REGISTRY_FILE', 'configs/mde-learning-registry.json')

domains = domain_catalog.get('domains', [])
presets = preset_catalog.get('presets', [])
learning_records = learning_registry.get('records') or learning_registry.get('learning_registry') or []

known_domain_ids = {domain.get('id') for domain in domains if domain.get('id')}
known_group_ids = {group.get('id') for group in refs.get('source_groups', []) if group.get('id')}
known_source_ids = {source.get('id') for source in refs.get('sources', []) if source.get('id')}
known_learning_ids = {record.get('id') for record in learning_records if record.get('id')}
preset_by_id = {preset.get('id'): preset for preset in presets if preset.get('id')}

selected_domains = [domain for domain in domains if not domain_filter or domain.get('id') == domain_filter]
if not selected_domains:
    raise SystemExit(f'No preset domains matched filter: {domain_filter or "<all>"}')

failures = []
for preset in presets:
    preset_id = preset.get('id')
    if not preset_id:
        failures.append('preset entry missing id')
        continue
    domain_ids = preset_domain_ids(preset)
    if not domain_ids:
        failures.append(f'preset {preset_id} does not declare any domains')
    for domain_id in domain_ids:
        if domain_id not in known_domain_ids:
            failures.append(f'preset {preset_id} points to unknown domain {domain_id}')

    source_refs = preset_source_refs(preset)
    if not source_refs:
        failures.append(f'preset {preset_id} does not declare any reference sources or groups')
    for source_ref in source_refs:
        if source_ref not in known_group_ids and source_ref not in known_source_ids:
            failures.append(f'preset {preset_id} points to unknown source or group {source_ref}')

    for learning_ref in preset_learning_refs(preset):
        if learning_ref not in known_learning_ids:
            failures.append(f'preset {preset_id} points to unknown learning record {learning_ref}')

    for bundle_path in preset.get('bundle_paths', []):
        resolved = resolve_path(bundle_path, repo_root)
        if not resolved.exists():
            failures.append(f'preset {preset_id} bundle path missing: {resolved}')
    base_bundle = preset.get('primary_bundle_path') or (preset.get('bundle_paths') or [None])[0]
    for starter_file in preset.get('starter_files', []):
        resolved = resolve_path(f"{base_bundle}/{starter_file}", repo_root) if base_bundle else resolve_path(starter_file, repo_root)
        if not resolved.exists():
            failures.append(f'preset {preset_id} starter file missing: {resolved}')

for domain in selected_domains:
    domain_id = domain.get('id')
    matching = [preset for preset in presets if domain_id in preset_domain_ids(preset)]
    if not matching:
        failures.append(f'missing preset coverage for domain {domain_id}')
        continue
    expected_preset_ids = domain.get('preset_ids') or []
    for preset_id in expected_preset_ids:
        if preset_id not in preset_by_id:
            failures.append(f'domain {domain_id} points to unknown preset {preset_id}')
            continue
        if domain_id not in preset_domain_ids(preset_by_id[preset_id]):
            failures.append(f'domain {domain_id} preset mapping mismatch for {preset_id}')

if failures:
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    raise SystemExit(1)

for domain in selected_domains:
    print(f"PASS {domain['id']}")
PY
