#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="${MDE_DOMAIN_CATALOG_FILE:-$ROOT_DIR/configs/mde-domain-catalog.json}"
QUERY="${*:-}"

python3 - "$CATALOG" "$QUERY" <<'PY'
from __future__ import annotations

import fnmatch
import json
import sys

catalog_path, query = sys.argv[1:3]
with open(catalog_path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)
query = query.strip().lower()
default_domain = data.get('routing_policy', {}).get('default_domain', 'mise-core')
if not query:
    print(default_domain)
    raise SystemExit(0)

tokens = [token for token in query.replace(',', ' ').split() if token]
best_id = default_domain
best_score = -1
for domain in data['domains']:
    domain_id = domain['id']
    if domain_id == query:
        print(domain_id)
        raise SystemExit(0)
    score = 0
    for alias in domain.get('ecosystem_aliases', []):
        alias = alias.lower()
        if alias == query:
            print(domain_id)
            raise SystemExit(0)
        if alias and alias in query:
            score += 5
    for keyword in domain.get('keywords', []):
        keyword = keyword.lower()
        if keyword and keyword in query:
            score += 3
    for pattern in domain.get('file_globs', []):
        pattern = pattern.lower()
        if fnmatch.fnmatch(query, pattern):
            score += 8
        for token in tokens:
            if fnmatch.fnmatch(token, pattern):
                score += 8
    if score > best_score:
        best_id = domain_id
        best_score = score
print(best_id)
PY
