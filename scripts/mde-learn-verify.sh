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


def record_domain_id(record: dict) -> str:
    return record.get('domain_id') or record.get('domain') or ''


def record_source_ids(record: dict) -> list[str]:
    values = record.get('authoritative_source_ids') or record.get('source_ids') or []
    return [value for value in values if value]


def record_preset_ids(record: dict) -> list[str]:
    values = record.get('preset_ids') or []
    return [value for value in values if value]


domain_catalog = load_json('MDE_DOMAIN_CATALOG_FILE', 'configs/mde-domain-catalog.json')
refs = load_json('MDE_REFERENCE_SOURCES_FILE', 'configs/mde-reference-sources.json')
preset_catalog = load_json('MDE_PRESET_CATALOG_FILE', 'configs/mde-preset-catalog.json')
learning_registry = load_json('MDE_LEARNING_REGISTRY_FILE', 'configs/mde-learning-registry.json')

domains = domain_catalog.get('domains', [])
records = learning_registry.get('records') or learning_registry.get('learning_registry') or []
known_source_ids = {source.get('id') for source in refs.get('sources', []) if source.get('id')}
known_preset_ids = {preset.get('id') for preset in preset_catalog.get('presets', []) if preset.get('id')}
selected_domains = [domain for domain in domains if not domain_filter or domain.get('id') == domain_filter]

if not selected_domains:
    raise SystemExit(f'No learning domains matched filter: {domain_filter or "<all>"}')

failures = []
for domain in selected_domains:
    domain_id = domain.get('id')
    matching = [record for record in records if record_domain_id(record) == domain_id]
    if not matching:
        failures.append(f'missing learning records for {domain_id}')
        continue

    expected_learning_id = domain.get('learning_record_id')
    if expected_learning_id and expected_learning_id not in {record.get('id') for record in matching if record.get('id')}:
        failures.append(f'domain {domain_id} missing expected learning record {expected_learning_id}')

    for record in matching:
        record_id = record.get('id', '<missing>')
        if learning_registry.get('records') is not None:
            required_fields = ['id', 'domain_id', 'status', 'owning_team_id', 'bundle_path', 'authoritative_source_ids', 'accepted_learnings', 'next_refresh_due']
        else:
            required_fields = ['id', 'domain', 'summary', 'source_ids']
        for field in required_fields:
            value = record.get(field)
            if value in (None, '', []):
                failures.append(f'record {record_id} missing field {field}')
        bundle_path = record.get('bundle_path')
        if bundle_path:
            resolved = resolve_path(bundle_path, repo_root)
            if not resolved.exists():
                failures.append(f'record {record_id} bundle path missing: {resolved}')
        for source_id in record_source_ids(record):
            if source_id not in known_source_ids:
                failures.append(f'record {record_id} points to unknown source {source_id}')
        for preset_id in record_preset_ids(record):
            if preset_id not in known_preset_ids:
                failures.append(f'record {record_id} points to unknown preset {preset_id}')
        disposition = record.get('disposition')
        status = record.get('status')
        if disposition and disposition not in {'adopted', 'deferred', 'rejected'}:
            failures.append(f'record {record_id} has invalid disposition {disposition}')
        if status and status not in {'seeded', 'active', 'archived', 'deferred', 'adopted', 'rejected'}:
            failures.append(f'record {record_id} has invalid status {status}')

if failures:
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    raise SystemExit(1)

for domain in selected_domains:
    print(f"PASS {domain['id']}")
PY
