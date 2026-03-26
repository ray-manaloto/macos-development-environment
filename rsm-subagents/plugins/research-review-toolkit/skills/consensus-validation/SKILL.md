---
name: consensus-validation
description: >
  This skill should be used when the user asks to "check consensus", "validate
  agreement", "evaluate review threshold", "check autonomy mode", "verify consensus
  gate", or mentions consensus validation, agreement threshold, 75% gate, autonomy
  modes, or ConsensusGate evaluation.
---

# Consensus Validation

## ConsensusGate (from src/mde/consensus.py)

The consensus gate evaluates agreement across multi-model review results.

### Threshold

- **75% agreement** required for consensus to pass
- Ported from claude-octopus v9.13.0 quality.sh `evaluate_quality_branch()`

### Autonomy Modes

| Mode | Behavior |
|------|----------|
| FULL | Auto-commit if consensus passes and quality gate passes |
| SUPERVISED | Auto-commit with notification to human |
| GATED | Require human approval before commit |
| MANUAL | Human must review and commit manually |

### Consensus Decision Flow

1. Collect structured review results from all models
2. Count agreements on each finding (severity + category match)
3. Calculate agreement percentage per finding
4. Apply 75% threshold to determine consensus
5. Map consensus result to autonomy mode action

### Using the Python Module

```python
from mde.consensus import ConsensusGate, ConsensusDecision, AutonomyMode

gate = ConsensusGate(threshold=0.75)
decision = gate.evaluate(review_results)

if decision.passed:
    # Consensus reached — apply autonomy mode
    ...
else:
    # Escalate to human review
    ...
```

### Debate Integrity Integration

Before evaluating consensus, debate integrity rules must pass:
- `DebateIntegrityRule` checks from `src/mde/consensus.py`
- Circular reasoning detection
- Severity inflation detection
- Rubber-stamp detection

## Rules

- 75% threshold is mandatory — never lower it
- Debate integrity must pass before consensus evaluation
- Failed consensus always escalates to human review
- Log consensus decisions with full rationale for audit trail
- Never auto-commit in GATED or MANUAL autonomy modes
