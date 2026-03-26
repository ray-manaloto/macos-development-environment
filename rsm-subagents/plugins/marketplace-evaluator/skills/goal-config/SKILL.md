---
name: goal-config
description: >
  This skill should be used when the user asks to "update evaluation goals", "add plugin goal",
  "change marketplace evaluator config", "modify evaluation criteria", "add a new capability need",
  "remove a goal", or "reconfigure evaluator models".
  Manages the goals.yaml configuration for the marketplace evaluator.
allowed-tools: [Read, Write, Edit]
---

# Goal Configuration Management

Manage the marketplace evaluator's goals, models, policies, and output paths.

## Configuration File

All configuration lives in `${CLAUDE_PLUGIN_ROOT}/config/goals.yaml`. Read it first to understand current state.

## Operations

### Add a Goal

Append a new entry to the `goals:` list:

```yaml
- id: new-goal-id          # kebab-case, unique
  name: Human-Readable Name
  description: What plugins this goal is looking for
  keywords: [keyword1, keyword2, keyword3]
  weight: 1.0              # 0.0-1.0, affects ranking priority
```

Update `last_updated` timestamp.

### Remove a Goal

Remove the entry from `goals:` list. Existing evaluations referencing this goal remain valid but the goal will not be used in future scans.

### Update Models

Modify the `models:` section:

```yaml
models:
  screener: haiku          # Fast pass: haiku recommended
  deep_reviewer: opus      # Deep review: opus or sonnet
  meta_learner: opus       # Meta-learning: opus recommended
  codex_reviewer: true     # Enable/disable codex follow-up
```

### Update Policies

Add or modify auto-reject rules in `policies.auto_reject:` or soft overrides in `policies.soft_reject_overridable:`.

### Update Output Paths

Modify `output:` section paths. Ensure target directories exist.

## Validation

After any change:
1. Verify YAML is valid (no syntax errors)
2. Check all goal IDs are unique
3. Verify referenced output paths exist
4. Confirm model names are valid (haiku/sonnet/opus/inherit)
