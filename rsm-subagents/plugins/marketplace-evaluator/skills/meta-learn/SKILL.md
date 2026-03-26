---
name: meta-learn
description: >
  This skill should be used when the user asks to "improve evaluator", "learn from evaluations",
  "evolve evaluation prompts", "check prediction accuracy", "review overridden verdicts",
  "meta-learn", or "how accurate are plugin evaluations".
  Reviews past evaluations vs actual outcomes and evolves the screening/review prompts.
argument-hint: "[--report-only] [--evolve-prompts]"
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Agent]
---

# Meta-Learning for Marketplace Evaluator

Analyze past evaluation accuracy and evolve the evaluator's own prompts and criteria.

## Data Sources

1. **Evaluations JSON** — All past verdicts with confidence scores
2. **Settings JSON** — Which plugins are actually enabled (ground truth)
3. **Meta-learning JSON** — History of prompt evolution and accuracy metrics
4. **User overrides** — Verdicts manually changed by the user

## Analysis Pipeline

### Step 1: Collect Outcomes

1. Read current `.claude/settings.json` to find all enabled plugins
2. Compare against evaluation verdicts:
   - INSTALL verdicts that ARE enabled → True Positive
   - INSTALL verdicts that are NOT enabled → False Positive (user rejected)
   - REJECT verdicts that ARE enabled → False Negative (user overrode)
   - REJECT verdicts that are NOT enabled → True Negative
3. Compute accuracy, precision, recall, F1

### Step 2: Analyze Patterns

1. For False Positives: Why did the evaluator recommend plugins the user rejected?
   - Policy violations missed?
   - Overlap with existing tooling not detected?
   - Context budget impact underestimated?
2. For False Negatives: Why did the evaluator reject plugins the user installed?
   - Policy too strict? (user accepted a policy violation)
   - Value underestimated?
   - Goal alignment missed?

### Step 3: Evolve Prompts (if `--evolve-prompts`)

1. Spawn **meta-learner** agent (model from config)
2. Agent reviews the pattern analysis and current agent prompts
3. Agent proposes specific prompt modifications:
   - Screening criteria adjustments
   - Policy strictness calibration
   - Goal keyword additions
   - Confidence scoring weight changes
4. Write proposals to meta-learning JSON for human review
5. Do NOT auto-apply prompt changes — present for approval

### Step 4: Report

Output a meta-learning report:

```
Meta-Learning Report
====================
Evaluations analyzed: 51
Accuracy: 82% | Precision: 75% | Recall: 90%

False Positives (recommended but not installed): 5
  - plugin-x: User rejected because [pattern]
  - plugin-y: Overlap with existing tooling

False Negatives (rejected but user installed): 2
  - plugin-z: Policy override accepted by user

Prompt Evolution Proposals:
  1. Relax bash-hooks policy for guard utilities (3 FN from this)
  2. Add "worktree" keyword to agent-improvement goal
  3. Increase overlap detection weight from 0.2 to 0.3
```

## Additional Resources

- **`references/meta-learning-patterns.md`** — Common patterns in evaluation drift and correction strategies
