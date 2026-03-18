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
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

repo_root = Path(sys.argv[1])
domain_filter = sys.argv[2].strip()


def resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


refs_path = resolve_path(os.environ.get('MDE_REFERENCE_SOURCES_FILE', str(repo_root / 'configs' / 'mde-reference-sources.json')), repo_root)
with refs_path.open('r', encoding='utf-8') as fh:
    refs = json.load(fh)

sources = refs.get('sources', [])
source_by_id = {source.get('id'): source for source in sources if source.get('id')}
selected = []

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
else:
    grouped = defaultdict(list)
    for source in sources:
        domain_ids = source.get('domain_ids') or source.get('domains') or ([source.get('domain')] if source.get('domain') else ['unclassified'])
        for domain_id in domain_ids:
            grouped[domain_id].append(source)
    for domain_id, domain_sources in grouped.items():
        if domain_filter and domain_filter != domain_id:
            continue
        selected.append({'id': domain_id, 'domain_id': domain_id, 'sources': domain_sources})

if not selected:
    raise SystemExit(f'No reference source groups matched filter: {domain_filter or "<all>"}')

mirror_root_raw = refs.get('mirror_root')
if not mirror_root_raw:
    for item in selected:
        print(item['id'])
    raise SystemExit(0)

mirror_root = resolve_path(mirror_root_raw, repo_root)
mirror_root.mkdir(parents=True, exist_ok=True)
refreshed_at = datetime.now(timezone.utc).isoformat()

for item in selected:
    group_dir = mirror_root / item['id']
    sources_dir = group_dir / 'sources'
    sources_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        'id': item['id'],
        'domain_id': item['domain_id'],
        'refreshed_at': refreshed_at,
        'source_count': len(item['sources']),
        'source_ids': [source.get('id') for source in item['sources']],
        'sources': [],
    }
    lines = [
        f"# {item['id']}",
        '',
        f"Domain classification: `{item['domain_id']}`",
        f"Refreshed at: `{refreshed_at}`",
        '',
        '## Sources',
    ]
    for source in item['sources']:
        locator = source.get('url') or source.get('path') or source.get('repo') or source.get('mirror_path_hint') or ''
        manifest['sources'].append(
            {
                'id': source.get('id'),
                'title': source.get('title') or source.get('label') or source.get('id'),
                'kind': source.get('kind') or source.get('category') or 'unknown',
                'locator': locator,
                'domain_ids': source.get('domain_ids') or source.get('domains') or ([source.get('domain')] if source.get('domain') else []),
            }
        )
        if locator:
            lines.append(f"- `{source.get('kind') or source.get('category') or 'source'}` {source.get('title') or source.get('label') or source.get('id')}: `{locator}`")
            (sources_dir / f"{source['id']}.ref").write_text(locator + '\n', encoding='utf-8')
            (sources_dir / f"{source['id']}.url").write_text(locator + '\n', encoding='utf-8')
        else:
            lines.append(f"- `{source.get('kind') or source.get('category') or 'source'}` {source.get('title') or source.get('label') or source.get('id')}")
        hint = source.get('mirror_path_hint')
        if hint:
            mirror_file = group_dir / hint
            mirror_file.parent.mkdir(parents=True, exist_ok=True)
            mirror_file.write_text(
                json.dumps(
                    {
                        'source_id': source.get('id'),
                        'title': source.get('title') or source.get('label') or source.get('id'),
                        'kind': source.get('kind') or source.get('category') or 'unknown',
                        'locator': locator,
                        'refreshed_at': refreshed_at,
                    },
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
    (group_dir / 'group.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (group_dir / 'bundle.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (group_dir / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(item['id'])
PY
