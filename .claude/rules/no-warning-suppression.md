# No Warning Suppression Policy

## Rule
AI agents and validators MUST NOT suppress, filter, downgrade, or hide warnings
or errors from external tools. Every finding must be surfaced at its original
severity level.

## What counts as suppression
- Filtering warnings by check name, message content, or pattern matching
- Downgrading severity (e.g., WARNING → INFO) to avoid failing a gate
- Catching and silently discarding error output
- Adding "benign" or "known" allowlists that skip findings
- Using `|| true`, `2>/dev/null`, or equivalent to hide failures

## Correct approach
1. **Map severity honestly**: if chezmoi says WARNING, our validator says WARNING
2. **Surface everything**: print all findings to the user, every run
3. **Fix root causes**: if a warning is structural, fix the layout or config
4. **File upstream issues**: if a tool lacks config to resolve a false positive,
   request the feature upstream (e.g., `[doctor.ignore]` in chezmoi)
5. **Document, don't suppress**: if a warning is expected and unfixable, document
   it in CLAUDE.md or a policy rule — but still show it

## Quality gate architecture
- ERROR findings → `passed = False` → gate fails → must fix before commit
- WARNING findings → visible in output → gate passes → human decides
- INFO findings → visible in output → gate passes → informational only
- The gate failing/passing is determined by severity, NOT by filtering

## Why this matters
Suppression creates blind spots. A "benign" filter today hides a real problem
tomorrow when the message changes or a new issue shares the same check name.
The zero-suppression policy ensures every signal reaches the human operator.
