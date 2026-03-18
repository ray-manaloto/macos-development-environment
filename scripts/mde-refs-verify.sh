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
from collections import defaultdict
from pathlib import Path

repo_root = Path(sys.argv[1])
domain_filter = sys.argv[2].strip()
strict_mirror = os.environ.get('MDE_REQUIRE_REFERENCE_MIRROR', '0') == '1'


def resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_json(env_name: str, default_rel: str) -> dict:
    path = resolve_path(os.environ.get(env_name, str(repo_root / default_rel)), repo_root)
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def source_domains(source: dict) -> list[str]:
    values = source.get('domain_ids') or source.get('domains') or ([source.get('domain')] if source.get('domain') else [])
    return [value for value in values if value]


refs = load_json('MDE_REFERENCE_SOURCES_FILE', 'configs/mde-reference-sources.json')
domains = load_json('MDE_DOMAIN_CATALOG_FILE', 'configs/mde-domain-catalog.json').get('domains', [])
presets = load_json('MDE_PRESET_CATALOG_FILE', 'configs/mde-preset-catalog.json').get('presets', [])
domains_by_id = {domain.get('id'): domain for domain in domains if domain.get('id')}

known_domain_ids = {domain.get('id') for domain in domains if domain.get('id')}
known_preset_ids = {preset.get('id') for preset in presets if preset.get('id')}
source_by_id = {source.get('id'): source for source in refs.get('sources', []) if source.get('id')}
selected = []
failures = []

if refs.get('source_groups'):
    for group in refs['source_groups']:
        group_id = group.get('id')
        domain_id = group.get('domain_id') or group.get('domain') or group_id
        if domain_filter and domain_filter not in {group_id, domain_id}:
            continue
        selected.append(
            {
                'id': group_id,
                'domain_id': domain_id,
                'sources': [source_by_id[source_id] for source_id in group.get('source_ids', []) if source_id in source_by_id],
            }
        )
    required_kinds = set(refs.get('mirror_policy', {}).get('required_kinds', []))
else:
    grouped = defaultdict(list)
    for source in refs.get('sources', []):
        domain_ids = source_domains(source) or ['unclassified']
        for domain_id in domain_ids:
            grouped[domain_id].append(source)
    for domain_id, domain_sources in grouped.items():
        if domain_filter and domain_filter != domain_id:
            continue
        selected.append({'id': domain_id, 'domain_id': domain_id, 'sources': domain_sources})
    required_kinds = set()

if not selected:
    raise SystemExit(f'No reference source groups matched filter: {domain_filter or "<all>"}')

mirror_root_raw = refs.get('mirror_root')
mirror_root = resolve_path(mirror_root_raw, repo_root) if mirror_root_raw else None

for item in selected:
    if known_domain_ids and item['domain_id'] not in known_domain_ids:
        failures.append(f"reference group {item['id']} points to unknown domain {item['domain_id']}")
    if not item['sources']:
        failures.append(f"reference group {item['id']} has no sources")
        continue

    kinds = set()
    for source in item['sources']:
        source_id = source.get('id')
        if not source_id:
            failures.append(f"reference group {item['id']} contains a source without id")
            continue
        locator = source.get('url') or source.get('path') or source.get('repo') or source.get('mirror_path_hint')
        if not locator:
            failures.append(f"source {source_id} is missing url/path/repo locator")
        source_domain_ids = source_domains(source)
        if known_domain_ids:
            for domain_id in source_domain_ids:
                if domain_id not in known_domain_ids:
                    failures.append(f"source {source_id} points to unknown domain {domain_id}")
        if source.get('presets'):
            for preset_id in source['presets']:
                if preset_id not in known_preset_ids:
                    failures.append(f"source {source_id} points to unknown preset {preset_id}")
        kind = source.get('kind') or source.get('category')
        if kind:
            kinds.add(kind)

    if 'official-docs' not in kinds:
        failures.append(f"reference group {item['id']} is missing official docs coverage")
    domain = domains_by_id.get(item['domain_id'], {})
    if domain.get('cookbook_pages') and 'official-cookbook' not in kinds:
        failures.append(f"reference group {item['id']} is missing official cookbook coverage")
    if not ({'upstream-repo', 'release-notes', 'external-reference'} & kinds):
        failures.append(f"reference group {item['id']} is missing supporting upstream or external references")
    curated = [
        source for source in item['sources']
        if source.get('authority') not in {'official', 'upstream'}
    ]
    if not curated:
        failures.append(f"reference group {item['id']} is missing curated external references")

    if mirror_root is None:
        continue

    group_dir = mirror_root / item['id']
    group_json = group_dir / 'group.json'
    bundle_json = group_dir / 'bundle.json'
    readme = group_dir / 'README.md'
    if not group_dir.is_dir():
        if strict_mirror:
            failures.append(f"missing mirrored reference group directory: {group_dir}")
        continue
    if not group_json.is_file() and not bundle_json.is_file():
        failures.append(f"missing mirrored group manifest: {group_json} or {bundle_json}")
    if not readme.is_file():
        failures.append(f"missing mirrored group readme: {readme}")
    for source in item['sources']:
        locator = source.get('url') or source.get('path') or source.get('repo') or source.get('mirror_path_hint')
        marker_ref = group_dir / 'sources' / f"{source['id']}.ref"
        marker_url = group_dir / 'sources' / f"{source['id']}.url"
        marker = marker_ref if marker_ref.is_file() else marker_url
        if not marker.is_file():
            if strict_mirror:
                failures.append(f"missing mirrored source marker: {marker_ref} or {marker_url}")
            continue
        if locator and marker.read_text(encoding='utf-8').strip() != locator:
            failures.append(f"mirrored source marker mismatch for {marker}")
        hint = source.get('mirror_path_hint')
        if hint and strict_mirror and not (group_dir / hint).exists():
            failures.append(f"missing mirrored metadata file: {group_dir / hint}")

if failures:
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    raise SystemExit(1)

for item in selected:
    print(f"PASS {item['id']}")
PY
