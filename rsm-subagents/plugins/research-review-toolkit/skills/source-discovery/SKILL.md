---
name: source-discovery
description: >
  This skill should be used when the user asks to "find sources", "discover URLs",
  "catalog a source", "classify a URL", "search for libraries", "check what exists",
  or mentions source discovery, URL cataloging, source classification, or research
  source management.
---

# Source Discovery

## Source Discovery Protocol

When discovering sources, follow this workflow:

1. **Search** — Check existing source-catalog.md for duplicates
2. **Fetch** — Use `npx agent-fetch "<url>" --json` for full content
3. **Classify** — Assign priority: HIGH / MEDIUM / LOW / SKIP
4. **Catalog** — Append to `docs/research/source-catalog.md`
5. **Record** — Write YAML provenance for HIGH/MEDIUM sources

## Classification Criteria

| Priority | Criteria |
|----------|----------|
| HIGH | Directly addresses current research question, authoritative source |
| MEDIUM | Related context, community discussion, alternative approach |
| LOW | Tangentially related, outdated but historically relevant |
| SKIP | Irrelevant, broken link, or duplicate of existing source |

## Source Catalog Format

Append entries to `docs/research/source-catalog.md`:
```
| [status] | Source Name | URL | Type | Verdict |
```

## Rules

- Log EVERY URL encountered — never silently discard
- Use `npx agent-fetch` for content, never WebFetch (truncates)
- Check for duplicates before adding to catalog
- HIGH sources get immediate YAML provenance records
- Include verdict explaining why the source was classified at that level
