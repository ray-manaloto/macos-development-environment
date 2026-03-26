# Meta-Learning Patterns

## Common Evaluation Drift Patterns

### Pattern 1: Policy Strictness Drift

**Symptom**: Many False Negatives where user overrides REJECT verdicts.
**Root cause**: Hard policy rules reject plugins the user finds acceptable.
**Example**: safety-net uses Node.js hooks (policy violation) but user installed it because
the guard utility use case is acceptable.
**Fix**: Add the specific use case to `soft_reject_overridable` in goals.yaml.

### Pattern 2: Goal Keyword Gaps

**Symptom**: Good plugins classified as LOW in screening despite being relevant.
**Root cause**: The goal's keyword list is missing terms the plugin uses.
**Example**: A plugin described as "autonomous development pipeline" wasn't caught by
the agent-improvement goal because "pipeline" wasn't in keywords.
**Fix**: Add missing keywords to the goal config.

### Pattern 3: Overlap Over-Detection

**Symptom**: Many REJECT verdicts citing overlap, but the plugins actually complement (not duplicate) existing tooling.
**Root cause**: Reviewer sees same domain and assumes overlap without checking granularity.
**Example**: codebase-quality was initially rejected as overlapping with research-review-toolkit,
but they serve different purposes (periodic audit vs PR review).
**Fix**: Instruct reviewer to distinguish "same domain" from "same function."

### Pattern 4: Context Budget Paranoia

**Symptom**: Plugins rejected solely for having "too many" skills, even when they're on-demand.
**Root cause**: Reviewer counts total skills without distinguishing always-loaded vs on-demand.
**Fix**: Differentiate between always-loaded descriptions (~100 tokens each) and
on-demand SKILL.md bodies (loaded only when triggered).

## Correction Strategies

### Strategy 1: Evidence-Based Policy Relaxation

When multiple user overrides share the same policy violation:
1. Count overrides per policy rule
2. If >2 overrides for same policy → propose moving to soft_reject_overridable
3. Document the acceptable use cases

### Strategy 2: Keyword Expansion from False Negatives

For each False Negative:
1. Extract the plugin's description keywords
2. Check which goal the user intended it for
3. Add missing keywords to that goal

### Strategy 3: Confidence Calibration

Track confidence scores vs actual outcomes:
- If high-confidence INSTALLs are often overridden → reduce weight of that scoring dimension
- If low-confidence INSTALLs are often accepted → increase weight of that dimension

### Strategy 4: Prompt A/B Testing

When proposing prompt changes:
1. Run both old and new prompts on the same 10 plugins
2. Compare verdicts
3. If new prompt matches user decisions better → adopt it
4. Track which prompt version produced each verdict for rollback
