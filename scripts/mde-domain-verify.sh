#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
DOMAIN_FILTER="${1:-${MDE_ACTIVE_DOMAIN:-}}"

python3 - "$ROOT_DIR" "$DOMAIN_FILTER" <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

repo_root = Path(os.environ.get('MDE_REPO_ROOT', sys.argv[1]))
domain_filter = sys.argv[2].strip()
required_stage_ids = {
    'mirror-refresh-agent',
    'docs-tutorial-agent',
    'repo-mining-agent',
    'social-signal-agent',
    'authority-agent',
    'implementation-agent',
    'validation-agent',
    'learning-consolidator-agent',
}


def resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_json(env_name: str, default_rel: str) -> dict:
    path = resolve_path(os.environ.get(env_name, str(repo_root / default_rel)), repo_root)
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def parse_yaml_ids(path: Path) -> list[str]:
    ids: list[str] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'^\s*-\s+id:\s+(.+?)\s*$', line)
        if match:
            ids.append(match.group(1))
    return ids


domain_catalog = load_json('MDE_DOMAIN_CATALOG_FILE', 'configs/mde-domain-catalog.json')
refs = load_json('MDE_REFERENCE_SOURCES_FILE', 'configs/mde-reference-sources.json')
preset_catalog = load_json('MDE_PRESET_CATALOG_FILE', 'configs/mde-preset-catalog.json')
learning_registry = load_json('MDE_LEARNING_REGISTRY_FILE', 'configs/mde-learning-registry.json')

domains = domain_catalog.get('domains', [])
presets = preset_catalog.get('presets', [])
learning_records = learning_registry.get('records') or learning_registry.get('learning_registry') or []
known_preset_ids = {preset.get('id') for preset in presets if preset.get('id')}
known_group_ids = {group.get('id') for group in refs.get('source_groups', []) if group.get('id')}
known_learning_ids = {record.get('id') for record in learning_records if record.get('id')}
selected_domains = [domain for domain in domains if not domain_filter or domain.get('id') == domain_filter]

if not selected_domains:
    raise SystemExit(f'No domains matched filter: {domain_filter or "<all>"}')

failures = []
seen_domain_ids: set[str] = set()
for domain in domains:
    domain_id = domain.get('id')
    if not domain_id:
        failures.append('domain catalog entry missing id')
        continue
    if domain_id in seen_domain_ids:
        failures.append(f'duplicate domain id: {domain_id}')
    seen_domain_ids.add(domain_id)

for domain in selected_domains:
    domain_id = domain.get('id')
    if 'team_config_path' in domain or 'bundle_path' in domain:
        required_fields = ['id', 'description', 'team_id', 'team_config_path', 'bundle_path', 'reference_source_group', 'learning_record_id']
        for field in required_fields:
            if not domain.get(field):
                failures.append(f'domain {domain_id} missing field {field}')
        for preset_id in domain.get('preset_ids', []):
            if preset_id not in known_preset_ids:
                failures.append(f'domain {domain_id} points to unknown preset {preset_id}')
        if domain.get('reference_source_group') and known_group_ids and domain['reference_source_group'] not in known_group_ids:
            failures.append(f'domain {domain_id} points to unknown reference source group {domain["reference_source_group"]}')
        if domain.get('learning_record_id') and domain['learning_record_id'] not in known_learning_ids:
            failures.append(f'domain {domain_id} points to unknown learning record {domain["learning_record_id"]}')
        if domain.get('bundle_path'):
            bundle_path = resolve_path(domain['bundle_path'], repo_root)
            if not bundle_path.exists():
                failures.append(f'domain {domain_id} bundle path missing: {bundle_path}')
        if domain.get('team_config_path'):
            team_path = resolve_path(domain['team_config_path'], repo_root)
            if not team_path.is_file():
                failures.append(f'domain {domain_id} team config missing: {team_path}')
            else:
                ids = set(parse_yaml_ids(team_path))
                if ids != required_stage_ids:
                    failures.append(f'domain {domain_id} stage ids mismatch: {sorted(ids)}')
    else:
        if not domain.get('description'):
            failures.append(f'domain {domain_id} missing description')
        if not domain.get('owner_team'):
            failures.append(f'domain {domain_id} missing owner_team')
        delegation_markers = domain.get('delegation_markers') or []
        if not delegation_markers:
            failures.append(f'domain {domain_id} missing delegation_markers')

contract_checks = {
    'scripts/agent-runner.sh': ['configs/mde-domain-catalog.json', 'configs/mde-reference-sources.json', 'configs/mde-preset-catalog.json', 'configs/mde-learning-registry.json', 'domain classification', 'delegat'],
    'scripts/teams/run-mde-autoresearch-team.sh': ['configs/mde-domain-catalog.json', 'configs/mde-reference-sources.json', 'configs/mde-preset-catalog.json', 'configs/mde-learning-registry.json', 'domain classification', 'delegat', 'run-mde-domain-team.sh'],
    'scripts/teams/validate-mde-autoresearch-output.sh': ['domain classification', 'delegat', 'preset', 'learning registry'],
    'scripts/teams/run-mde-domain-team.sh': ['configs/mde-domain-catalog.json', 'configs/mde-reference-sources.json', 'configs/mde-preset-catalog.json', 'configs/mde-learning-registry.json', 'domain classification', 'delegat'],
    'scripts/teams/validate-mde-domain-output.sh': ['domain classification', 'delegat', 'preset', 'learning registry'],
    'scripts/mde-agent-verify.sh': ['mde-refs-verify.sh', 'mde-preset-verify.sh', 'mde-domain-verify.sh', 'mde-learn-verify.sh'],
}

for rel, patterns in contract_checks.items():
    path = repo_root / rel
    if not path.is_file():
        failures.append(f'missing contract surface: {path}')
        continue
    text = path.read_text(encoding='utf-8')
    for pattern in patterns:
        if pattern not in text:
            failures.append(f'{rel} missing pattern: {pattern}')

if failures:
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    raise SystemExit(1)

for domain in selected_domains:
    print(f"PASS {domain['id']}")
PY

bash "$SCRIPT_DIR/mde-refs-verify.sh" "$DOMAIN_FILTER"
bash "$SCRIPT_DIR/mde-preset-verify.sh" "$DOMAIN_FILTER"
bash "$SCRIPT_DIR/mde-learn-verify.sh" "$DOMAIN_FILTER"
