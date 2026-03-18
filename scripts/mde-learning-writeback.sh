#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/mde-agent-policy.sh
source "$SCRIPT_DIR/lib/mde-agent-policy.sh"

mde_policy_init
DOMAIN="${1:?domain is required}"
DATE_STAMP="${2:-$(date +%F)}"
OUTPUT_DIR="${3:-reports/mde-domain-sdlc/$DOMAIN}"

python3 - "$MDE_REPO_ROOT" "$DOMAIN" "$DATE_STAMP" "$OUTPUT_DIR" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
domain_id = sys.argv[2]
date_stamp = sys.argv[3]
output_dir = sys.argv[4]
registry_path = repo_root / 'configs' / 'mde-learning-registry.json'
domain_catalog_path = repo_root / 'configs' / 'mde-domain-catalog.json'
reference_sources_path = repo_root / 'configs' / 'mde-reference-sources.json'
with registry_path.open('r', encoding='utf-8') as fh:
    registry = json.load(fh)
with domain_catalog_path.open('r', encoding='utf-8') as fh:
    domains = {item['id']: item for item in json.load(fh)['domains']}
with reference_sources_path.open('r', encoding='utf-8') as fh:
    refs = json.load(fh)
source_groups = {item['id']: item for item in refs['source_groups']}
if domain_id not in domains:
    raise SystemExit(f'Unknown domain: {domain_id}')
domain = domains[domain_id]
source_group = source_groups[domain['reference_bundle_id']]
record_id = f'{date_stamp}-{domain_id}-domain-run'
required_verification = [
    f'mise run mde:team:domain -- --domain {domain_id}',
    'mise run mde:refs:verify',
    'mise run mde:preset:verify',
    'mise run mde:domain:verify',
    'mise run mde:learn:verify',
]
new_record = {
    'id': record_id,
    'domain': domain_id,
    'domain_id': domain_id,
    'status': 'accepted',
    'seeded_on': date_stamp,
    'owning_team_id': domain['team_id'],
    'bundle_path': domain['tool_bundle_dir'],
    'preset_ids': domain.get('preset_ids', []),
    'authoritative_source_ids': source_group['source_ids'],
    'title': f"{domain['name']} domain team run recorded for {date_stamp}",
    'disposition': 'adopted',
    'source_snapshots': [{'bundle_id': source_group['id'], 'source_ids': source_group['source_ids']}],
    'affected_prompts': ['prompts/agent-team/mde-domain-sdlc/*.md'],
    'affected_skills': ['skills/mise-enforcement', 'skills/research-source-discovery', 'skills/github-repo-mining', 'skills/social-signal-mining', 'skills/evidence-synthesis'],
    'affected_docs': ['docs/mise-config.md', 'docs/toolchain-precedence.md', 'docs/decision-log.md'],
    'affected_tasks': ['mde:team:domain', 'mde:refs:refresh', 'mde:refs:verify', 'mde:preset:verify', 'mde:domain:verify', 'mde:learn:verify'],
    'required_verification': required_verification,
    'decision_record_path': 'docs/research/domain-decisions/2026-03-15-domain-team-governance.md',
    'notes': [
        f'Output directory: {output_dir}',
        f'Project authority: {domain["project_authority"]}',
        f'Global CLI authority mode: {domain["global_cli_authority_mode"]}',
    ],
    'accepted_learnings': [
        f"Domain run completed for {domain_id}.",
        f"Authority anchored on: {domain['project_authority']}.",
    ],
    'open_questions': [],
    'next_refresh_due': date_stamp,
    'last_reviewed_at': date_stamp,
}
records = [record for record in registry['records'] if record['id'] != record_id]
records.append(new_record)
registry['records'] = records
registry['updated_at'] = date_stamp
registry_path.write_text(json.dumps(registry, indent=2) + '\n', encoding='utf-8')
print(record_id)
PY
