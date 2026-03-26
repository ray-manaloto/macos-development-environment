# Community Plugin Deep Reviews — Batch 2: TDD/Testing/Quality

**Date**: 2026-03-26
**Agent**: claude-opus-4.6 (subagent batch evaluator)
**Plugins reviewed**: tdd-guard, tdd-evolutionary-loop, tidy-skills, claude-codebase-quality, claude-bugbash, governance-claude-skill, debug-skill, n360-engineering

---

## 1. tdd-guard

**VERDICT: REJECT**

- **Components**: skills=1 (setup), agents=0, cmds=0, hooks=6 (3 hook events with npx commands)
- **Policy conflicts**: Hooks execute `npx tdd-guard@latest` on every Write/Edit/MultiEdit/TodoWrite, UserPromptSubmit, and SessionStart. Uses npx which violates no-npx-for-mise-tools policy. Relies on Node.js npm ecosystem.
- **Overlap**: Heavy overlap with existing superpowers TDD skills and test-generator plugin.

**Rationale**: This is a Node.js-centric TDD enforcement tool. Its reporters target vitest/jest/storybook/PHPUnit/Go/Rust — the pytest reporter exists but it requires installing `tdd-guard-pytest` from PyPI and configuring a custom reporter. The 6 inline hooks that run `npx tdd-guard@latest` on every file edit add significant latency and context cost. The enforcement model (blocking writes unless tests exist) conflicts with mde's existing quality gate approach. The npm dependency chain is unnecessary for a pure Python project.

---

## 2. tdd-evolutionary-loop

**VERDICT: EXTRACT**

- **Components**: skills=1, agents=2 (coder, devils-advocate), cmds=0, hooks=0
- **Policy conflicts**: None. No .sh files, no hooks. Agents use standard tools.
- **Overlap**: Overlaps with superpowers TDD skills, but offers a distinct pattern: parallel variant implementations with adversarial review and convergence selection.

**Rationale**: The parallel coder + devil's advocate pattern is worth extracting. The core idea — spawn two independent implementations of the same interface against the same tests, then pick the winner via adversarial review — is a novel approach that aligns with mde's existing adversarial review infrastructure (`consensus.py`, `reviewd`). However, the plugin is too tightly coupled to Python file-swap strategies (symlink swap, PYTHONPATH manipulation) and lacks integration with mde's quality gate. **Extract the devil's advocate agent pattern and the convergence selection logic** into the existing autonomous-review-skill or as a new skill in research-review-toolkit. The variant file approach needs adaptation to work with mde's worktree-based workflow.

---

## 3. tidy-skills

**VERDICT: EXTRACT**

- **Components**: skills=1 (augmented-coding), agents=0, cmds=0, hooks=0
- **Policy conflicts**: None. No .sh files, no hooks. Pure skill with clean markdown instructions.
- **Overlap**: Partially overlaps with superpowers TDD skills, but the Kent Beck "Tidy First" methodology is distinct.

**Rationale**: The SKILL.md is 238 lines — a substantial context budget cost (~600-800 tokens). The "Genie" execution model (user drives, AI executes) conflicts with mde's more autonomous agent approach. The plan-file-driven workflow (`*-plan.md` files) adds a foreign artifact pattern. However, the **Tidy First tidying patterns catalog** (guard clause, extract method, normalize symmetry, etc.) and the **strict structural/behavioral commit separation rule** are high-value extractions. These patterns should be added to the existing superpowers TDD skill or a new refactoring skill in the mde toolkit, without the interactive plan-file overhead.

---

## 4. claude-codebase-quality

**VERDICT: INSTALL**

- **Components**: skills=0, agents=7, cmds=1 (/codebase-quality), hooks=0
- **Policy conflicts**: None. No .sh files, no hooks. All agents use standard tools. The secret-auditor explicitly disallows Bash. Uses `permissionMode: plan` on all agents. Read-only design.
- **Overlap**: Partially overlaps with research-review-toolkit, but fundamentally different focus: codebase-wide quality audit vs PR/commit review.

**Rationale**: This is the highest-quality plugin in the batch. Key strengths: (1) 7 specialized agents with clear separation of concerns, (2) validation pipeline that requires every finding to be independently confirmed before reporting, (3) explicit false-positive avoidance rules, (4) CLAUDE.md compliance checking with verbatim rule quoting, (5) read-only agents that cannot modify code, (6) structured report output with GitHub permalink generation. The context cost is moderate — the command is invoked on-demand (`/codebase-quality`), not auto-triggered. The agent definitions are concise (30-70 lines each). This fills a gap: mde has PR review but no periodic codebase-wide quality audit tool. The `--fast` and `--smoke` modes provide flexibility.

---

## 5. claude-bugbash

**VERDICT: INSTALL**

- **Components**: skills=2, agents=3 (hunter, api, ui), cmds=3 (/bug-bash, /bug-bash-quick, /bug-bash-deep), hooks=0
- **Policy conflicts**: None. No .sh files, no hooks. Clean plugin structure. All agents use `model: inherit`.
- **Overlap**: No overlap with existing mde capabilities. No exploratory testing / QA / bug-hunting tooling.

**Rationale**: Well-designed plugin with a clear charter: find and reproduce bugs, do not fix. The evidence bar system (S1-S4 severity with minimum evidence requirements per level) enforces rigor. The separation of API vs UI testing agents is sensible. The "suspected/flaky" table prevents false confidence. The structured JSON output enables ticket creation. Context cost is reasonable — skills trigger only on explicit keywords, and commands are invoked on-demand. This fills a genuine gap in the mde toolset for systematic exploratory testing of the CLI.

---

## 6. governance-claude-skill

**VERDICT: REJECT**

- **Components**: skills=1, agents=1, cmds=0, hooks=0
- **Policy conflicts**: TypeScript/Node.js focused (TSConfig strict mode, Vitest/Jest, JSDoc, npm run commands). References `npm run audit:standards` and `node scripts/governance-check.mjs`.
- **Overlap**: Heavy overlap with mde's existing quality gate, CLAUDE.md enforcement rules, and `.claude/rules/` policy system.

**Rationale**: This is a TypeScript-first governance tool that would require complete rewriting to work with the mde Python project. The "zero deferral" approach (fix everything immediately during review) conflicts with mde's issue-tracking policy (catalog unrelated errors as GitHub Issues). The trigger keywords are too broad ("code review", "commit", "standards", "compliance") and would capture prompts not intended for this plugin. The concept of delegated governance review is already better implemented by mde's reviewer subagent + `.claude/rules/` system.

---

## 7. debug-skill

**VERDICT: REJECT**

- **Components**: skills=1, agents=0, cmds=0, hooks=0
- **Policy conflicts**: Contains `scripts/install-dap.sh` — a shell script. SKILL.md instructs agent to run `bash scripts/install-dap.sh`. Installs Go binary via `brew install` or `go install` — violates mise-first policy.
- **Overlap**: No direct overlap (no interactive debugger tooling exists).

**Rationale**: The `dap` CLI tool for interactive debugging via DAP protocol is genuinely useful, and the SKILL.md is exceptionally well-written (264 lines). However: (1) the .sh installer script violates no-shell-scripts policy, (2) the `brew install` / `go install` installation violates mise-first policy, (3) the tool is not in the mde dependency tree. If the `dap` binary were added to mise config and the install script removed, this could be reconsidered. The debugging methodology content could be extracted into a reference document without the plugin infrastructure.

---

## 8. n360-engineering

**VERDICT: EXTRACT**

- **Components**: skills=3 (tdd, operating-standard, large-feature), agents=0, cmds=0, hooks=0
- **Policy conflicts**: operating-standard auto-triggers on every session start and mandates reading `tasks/handoff.md`, `tasks/todo.md`, `tasks/lessons.md` — files that do not exist. Assumes Node.js or Flutter.
- **Overlap**: TDD skill overlaps with superpowers TDD. operating-standard overlaps with `.claude/rules/`. large-feature overlaps with superpowers workflow guide.

**Rationale**: Three skills of very different quality. The **TDD skill** is the standout — its "Anti-Rationalisation Guard" table (6 common TDD excuses and correct responses) and "When to Scale Down" matrix are genuinely valuable and more concise than existing superpowers TDD content. **Extract the Anti-Rationalisation Guard and Scale Down matrix** into the existing superpowers TDD skill. The operating-standard is a 422-line behemoth too heavy and too generic. The large-feature protocol has good ideas (review gates every 3 tasks, context exhaustion handling) but is redundant with the superpowers workflow guide.
