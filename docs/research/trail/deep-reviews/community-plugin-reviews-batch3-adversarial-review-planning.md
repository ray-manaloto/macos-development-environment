# Community Plugin Deep Reviews — Batch 3: Adversarial/Review/Planning

**Date**: 2026-03-26
**Agent**: claude-opus-4.6 (subagent batch evaluator)
**Plugins reviewed**: adversarial-review, adversarial-spec, challenger-plugin, plan-review-skill, wave-planner-claude-skill, claude-project-setup-plugin, python-remote-debug-skill, vitals

---

## 1. adversarial-review — REJECT

- **Components**: skills=1, agents=0, cmds=2, hooks=0
- **Policy conflicts**: scripts/codex-review.sh (bash wrapping codex exec)
- **Overlap**: HIGH with research-review-toolkit (autonomous-review agent, debate-orchestration)
- **Rationale**: Shell script is hard policy violation. codex exec pattern already implemented in existing adversarial review workflow. Plugin is a subset of research-review-toolkit.

## 2. adversarial-spec — EXTRACT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: litellm with API keys as primary path (but supports subscription CLIs)
- **Overlap**: Moderate with research-review-toolkit debate-orchestration/consensus-validation
- **Rationale**: Spec/PRD refinement via multi-model debate is novel and not covered by existing plugins. litellm conflicts with subscription-only policy. EXTRACT: debate convergence protocol, document templates, preserve-intent concept, anti-laziness press check. Integrate into research-review-toolkit as spec-refinement skill using subscription CLIs only.

## 3. challenger-plugin — INSTALL

- **Components**: skills=2, agents=5, cmds=0, hooks=0
- **Policy conflicts**: None — pure prompt-based, no shell scripts, no API keys
- **Overlap**: Low-moderate — stress-tests decisions/plans, not code review like research-review-toolkit
- **Rationale**: Strongest candidate. 4-agent adversarial arena (skeptic, architect, pragmatist, sentinel) with evidence-backed challenges, confidence scoring, ROI-prioritized fix lists. Auto-scaling intensity (quick/deep/brutal). Passive challenger-watch agent monitors for high-stakes moments. Complements research-review-toolkit.

## 4. plan-review-skill — REJECT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: None
- **Overlap**: HIGH with challenger-plugin (more sophisticated multi-perspective review)
- **Rationale**: Redundant if challenger-plugin installed. VP personas are simpler version of challenger's agents with less rigor.

## 5. wave-planner-claude-skill — REJECT

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: LINEAR_API_KEY, claude-flow MCP, docker, git-crypt dependencies
- **Overlap**: Low
- **Rationale**: Tightly coupled to Linear + claude-flow + Docker + hive-mind toolchain not used by this project. LINEAR_API_KEY conflicts with subscription-only policy.

## 6. claude-project-setup-plugin — REJECT

- **Components**: skills=5, agents=0, cmds=3, hooks=0
- **Policy conflicts**: test/dry-run.sh
- **Overlap**: Low — project has mature .claude/ config
- **Rationale**: Designed for greenfield setup. mde already has extensive hand-curated .claude/ configuration far more sophisticated than auto-generated output.

## 7. python-remote-debug-skill — INSTALL

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: None — pure documentation/guidance skill
- **Overlap**: None — no debugging skill exists
- **Rationale**: Focused skill for Python 3.14 sys.remote_exec() debugging. Project runs 3.14. Covers stack trace injection, gevent introspection, PID finding. Zero infrastructure, minimal context.

## 8. vitals — INSTALL

- **Components**: skills=1, agents=0, cmds=0, hooks=3 (PostToolUse, Stop, SessionEnd)
- **Policy conflicts**: None — hooks use python3 (vitals_cli.py, provenance.py)
- **Overlap**: Low — quality gate checks correctness, vitals checks structural health
- **Rationale**: Hotspot detection (cli.py = 17 commits), co-change coupling, knowledge risk, ROI-ranked refactoring. Python hooks. Trend tracking across scans. AI provenance tracking.
