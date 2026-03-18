# MDE Remediation Triage Prompt

Objective: review the supplied remediation target and evidence pack and classify concrete failure modes, ownership drift, and declaration gaps with direct evidence.

Requirements:
- State the exact remediation item id and evidence path(s) used.
- Use `configs/mde-modernization-matrix.json` as the inventory source of truth.
- Group findings by remediation class, not by chronology.
- Point to likely owning scripts, tasks, registry entries, and functions.
- Distinguish immediate declarative fixes from follow-up investigation.
