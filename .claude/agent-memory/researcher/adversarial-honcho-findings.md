---
name: Honcho memory design validation gaps
description: 9 architectural/implementation gaps found in the honcho memory design spec (2026-03-23) through adversarial review of validation and verification system
type: project
---

# Honcho Memory Design — Adversarial Review Summary

**Date**: 2026-03-23
**Spec**: docs/superpowers/specs/2026-03-23-honcho-memory-design.md
**Status**: 9 findings (1 CRITICAL, 2 HIGH, 6 MEDIUM)

## Why

The spec proposes comprehensive validation checks (lines 502-606) but provides only goals (what to validate), not mechanisms (how to validate). This creates ambiguity in implementation and risk of false positives/negatives in the quality gate. An adversarial review of 10 validation vectors found gaps in specification and implementation.

## How to Apply

**Before implementation of PR B**:
- Review the full finding document at docs/research/trail/findings/adversarial-validation-review.yaml
- Use the "RECOMMENDATIONS BEFORE IMPLEMENTATION" section to guide detailed validation pseudocode
- Add integration tests for each docker validation sub-check
- Update quality.py docstring to clarify check counting strategy

**Key implementation risks to avoid**:
1. Bake targets reference non-existent Dockerfile.honcho (design flaw, not validation issue)
2. subprocess calls to docker compose must use `env=os.environ.copy()` or vars won't be found
3. Digest pinning validation must use YAML parser (PyYAML), not regex (handles multi-line)
4. Port conflict detection requires parsing merged compose config from includes
5. Memory verify behavior is undefined when stack is down (UX issue, needs documentation)

## Confirmed Findings

1. **CRITICAL**: Bake --print doesn't validate Dockerfile existence (design decision issue)
2. **HIGH**: Digest pinning regex approach is fragile for multi-line YAML
3. **HIGH**: Port conflict detection across includes is method-unspecified
4. **MEDIUM**: Env var expansion requires subprocess env inheritance (hidden bug risk)
5. **MEDIUM**: Healthcheck coverage false positives on image-inherited checks
6. **MEDIUM**: validate --docker flag exists (CLI wired) but logic not implemented
7. **MEDIUM**: Compose version comparison needs semantic versioning, not string compare
8. **MEDIUM**: Memory verify behavior undefined when stack is not running
9. **MEDIUM**: Quality gate 6/6 claim doesn't reconcile with 8+ docker sub-checks

## Full Details

See docs/research/trail/findings/adversarial-validation-review.yaml for complete analysis of each vector, test evidence, and implications.
