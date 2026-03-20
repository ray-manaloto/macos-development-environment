# Specialized Agent Teams Patterns for Claude Code

Date: 2026-03-20
Sources:
- https://code.claude.com/docs/en/agent-teams (full documentation)
- https://code.claude.com/docs/en/sub-agents (full documentation)
- https://code.claude.com/docs/en/common-workflows (worktree patterns)
- docs/research/trail/deep-reviews/gstack-complete-reference.md
- docs/research/trail/deep-reviews/aris-and-compound-complete.md
- docs/research/trail/deep-reviews/orchestrator-autoresearch-complete.md
- docs/research/trail/deep-reviews/skill-plugin-ecosystem-complete.md

---

## Table of Contents

1. [How Agent Teams Work (Official Documentation Summary)](#1-how-agent-teams-work)
2. [How Subagents Work (Complementary System)](#2-how-subagents-work)
3. [Specialized Team Templates](#3-specialized-team-templates)
4. [Team Spawn Patterns](#4-team-spawn-patterns)
5. [Task Decomposition Strategies](#5-task-decomposition-strategies)
6. [Quality Gates](#6-quality-gates)
7. [Comparison with Other Multi-Agent Frameworks](#7-comparison-with-other-multi-agent-frameworks)
8. [Team Configuration Files](#8-team-configuration-files)
9. [Combining Teams and Subagents](#9-combining-teams-and-subagents)
10. [Recommendations for the MDE Project](#10-recommendations-for-the-mde-project)

---

## 1. How Agent Teams Work

### Enabling

Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your environment or in `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Requires Claude Code v2.1.32 or later.

### Architecture

An agent team consists of four components:

| Component | Role |
|-----------|------|
| **Team lead** | The main Claude Code session that creates the team, spawns teammates, and coordinates work |
| **Teammates** | Separate Claude Code instances that each work on assigned tasks |
| **Task list** | Shared list of work items that teammates claim and complete |
| **Mailbox** | Messaging system for communication between agents |

Teams are stored locally at `~/.claude/teams/{team-name}/config.json` and tasks at `~/.claude/tasks/{team-name}/`.

### Key Differences from Subagents

| Aspect | Subagents | Agent Teams |
|--------|-----------|-------------|
| **Context** | Own context window; results return to caller | Own context window; fully independent |
| **Communication** | Report results back to main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only the result matters | Complex work requiring discussion and collaboration |
| **Token cost** | Lower: results summarized back to main context | Higher: each teammate is a separate Claude instance |

### Display Modes

- **In-process**: All teammates run inside the main terminal. Shift+Down cycles through teammates.
- **Split panes**: Each teammate gets its own pane (requires tmux or iTerm2).

Configure via `teammateMode` in settings.json (`"in-process"`, `"tmux"`, `"auto"`).

### Task Management

Tasks have three states: pending, in progress, completed. Tasks can depend on other tasks. A pending task with unresolved dependencies cannot be claimed until those dependencies complete.

Task claiming uses file locking to prevent race conditions.

### Current Limitations

- No session resumption with in-process teammates
- Task status can lag (teammates sometimes fail to mark tasks completed)
- Shutdown can be slow
- One team per session
- No nested teams (teammates cannot spawn teams)
- Lead is fixed (cannot transfer leadership)
- Permissions set at spawn (all teammates inherit lead's permission mode)
- Split panes not supported in VS Code terminal, Windows Terminal, or Ghostty

---

## 2. How Subagents Work

Subagents are the complementary system for non-collaborative parallel work. They are defined as Markdown files with YAML frontmatter.

### Key Configuration Options

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep, Bash
model: sonnet
permissionMode: plan
maxTurns: 20
memory: project
isolation: worktree
background: true
skills:
  - api-conventions
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
---

System prompt goes here in markdown body.
```

### Scope Hierarchy

| Location | Scope | Priority |
|----------|-------|----------|
| `--agents` CLI flag | Current session | 1 (highest) |
| `.claude/agents/` | Current project | 2 |
| `~/.claude/agents/` | All projects | 3 |
| Plugin's `agents/` directory | Where plugin is enabled | 4 (lowest) |

### Model Options

- `haiku` -- fast, cheap (good for fetchers, validators)
- `sonnet` -- balanced (good for implementation, testing)
- `opus` -- most capable (good for architecture, complex reasoning)
- `inherit` -- same as main conversation (default)
- Full model IDs also supported (e.g. `claude-opus-4-6`)

### Persistent Memory

Three scopes: `user` (~/.claude/agent-memory/), `project` (.claude/agent-memory/), `local` (.claude/agent-memory-local/). When enabled, the subagent gets a persistent directory with MEMORY.md that survives across conversations.

### Worktree Isolation

Set `isolation: worktree` to give each subagent its own git worktree. The worktree is automatically cleaned up if the subagent makes no changes.

---

## 3. Specialized Team Templates

### Research Team

**Use case:** Research cycles, source discovery, literature review, knowledge synthesis.

**Team composition:**

```
Lead: Research Coordinator (Opus, full tools)
  Purpose: Break research question into source-fetching tasks, synthesize findings,
  identify gaps, produce final deliverable.

Teammate 1: Source Fetcher A (any model, Bash-only)
  Purpose: Fetch and extract content from assigned URLs via agent-fetch or WebFetch.
  One source per task. Return raw content + key findings summary.

Teammate 2: Source Fetcher B (same configuration)
  Purpose: Parallel fetching of different source set.

Teammate 3: Synthesizer (Sonnet, read-only tools)
  Purpose: Read all fetched content, cross-reference findings, identify patterns,
  contradictions, and gaps. Does not modify files.

Teammate 4: Note Writer (Haiku, Write/Edit only)
  Purpose: Write findings to docs/research/ following provenance format.
  Updates source-catalog.md with discovered URLs.
```

**Spawn prompt:**

```
Create an agent team to research [TOPIC]. Spawn 4 teammates:

1. "fetcher-a" -- Fetches content from these sources: [URL1, URL2, URL3].
   For each URL, extract the full content and summarize key findings in a message
   to the synthesizer.

2. "fetcher-b" -- Fetches content from these sources: [URL4, URL5, URL6].
   Same instructions as fetcher-a.

3. "synthesizer" -- Wait for fetchers to complete, then read all findings.
   Cross-reference patterns, identify contradictions, produce a synthesis document.
   Send the synthesis to the note-writer.

4. "note-writer" -- Write the final findings document to
   docs/research/trail/deep-reviews/[FILENAME].md following the existing format
   in that directory. Also update docs/research/source-catalog.md with all
   discovered URLs.

Use Sonnet for all teammates. Require plan approval for the synthesizer
before they begin cross-referencing.
```

**Task decomposition:**

| Task | Owner | Dependencies |
|------|-------|-------------|
| Fetch source 1-3 | fetcher-a | None |
| Fetch source 4-6 | fetcher-b | None |
| Cross-reference all findings | synthesizer | Fetch tasks |
| Write findings document | note-writer | Synthesis |
| Update source catalog | note-writer | Synthesis |

### Python Development Team

**Use case:** Feature implementation in src/mde/, bug fixes, refactoring.

**Team composition:**

```
Lead: Architect (Opus, plan mode initially)
  Purpose: Analyze requirements, design implementation approach, decompose into
  tasks, review final output before merge.

Teammate 1: Implementer (Sonnet, full tools)
  Purpose: Write production code in src/mde/. Owns the source files.
  Follows existing patterns (Pydantic models, structlog, anyio).

Teammate 2: Tester (Sonnet, full tools)
  Purpose: Write tests in tests/. Runs pytest. Owns test files only.
  Does NOT modify src/mde/ files.

Teammate 3: Reviewer (Sonnet, read-only tools)
  Purpose: Review implementer's code for quality, security, and adherence
  to project conventions. Reports findings to the lead.
```

**Spawn prompt:**

```
Create an agent team to implement [FEATURE] in the mde Python package.
Spawn 3 teammates:

1. "implementer" -- Implement the feature in src/mde/ following existing patterns.
   Check pyproject.toml for dependencies. Use Pydantic for models, structlog for
   logging. Only modify files under src/mde/. Use Sonnet.

2. "tester" -- Write pytest tests for the implementation under tests/.
   Run tests with `uv run pytest tests/[relevant]`. Only modify files under tests/.
   Use Sonnet.

3. "reviewer" -- Review the implementation for code quality, security,
   and adherence to the project's declarative-config and no-shell-scripts policies.
   Read-only -- do not modify any files. Report findings to me. Use Sonnet.

The implementer should work first. Once implementation has initial commits,
the tester and reviewer can begin in parallel.

Wait for all teammates to complete before proceeding.
```

**File ownership (conflict avoidance):**

| Owner | Owns | Cannot Touch |
|-------|------|-------------|
| Implementer | `src/mde/**/*.py` | `tests/`, `docs/`, `pyproject.toml` |
| Tester | `tests/**/*.py` | `src/mde/`, `docs/` |
| Reviewer | Nothing (read-only) | Everything |
| Lead | `pyproject.toml`, `docs/` | Delegates src/ and tests/ |

### Dotfiles/Config Team

**Use case:** Changes spanning chezmoi templates, mise config, Brewfile, and system validation.

**Team composition:**

```
Lead: Coordinator (Opus)
  Purpose: Understand what tools/configs need changing, decompose across
  specialists, validate the final state.

Teammate 1: Mise Specialist (Sonnet)
  Purpose: Modify mise.toml, install tools via mise, update tool versions.
  Owns mise.toml and related mise config files.

Teammate 2: Chezmoi Specialist (Sonnet)
  Purpose: Modify chezmoi templates under home/. Handle template logic,
  encrypted secrets, file permissions.
  Owns home/ directory and .chezmoiignore.

Teammate 3: Validator (Haiku, read-only + Bash)
  Purpose: Run `uv run mde-py validate --all` after changes, report failures.
  Does not modify files.
```

**Spawn prompt:**

```
Create an agent team to [DESCRIBE CHANGE] across our dotfiles setup.
Spawn 3 teammates:

1. "mise-specialist" -- Handle all mise.toml changes. Add/update tools using
   the registry > aqua > github backend priority. Never use the deprecated
   ubi: backend. Use Sonnet.

2. "chezmoi-specialist" -- Handle all chezmoi template changes under home/.
   Ensure templates use proper Go template syntax. Use Sonnet.

3. "validator" -- After the other teammates finish, run validation:
   `uv run mde-py validate --all`. Report any failures. Read-only except
   for running validation commands. Use Haiku.

The mise-specialist and chezmoi-specialist can work in parallel.
The validator should wait until both are done.
```

### Infrastructure Team

**Use case:** Homebrew packages, system setup scripts, security hardening.

**Team composition:**

```
Lead: Coordinator (Opus)
  Purpose: Plan infrastructure changes, ensure nothing breaks the
  declarative config policies.

Teammate 1: Brew Specialist (Sonnet)
  Purpose: Modify Brewfile, handle cask installations, resolve conflicts
  with mise-managed tools.

Teammate 2: Security Auditor (Sonnet, read-only)
  Purpose: Review all changes for security implications. Check for
  secrets exposure, unsafe permissions, sudo usage.

Teammate 3: Docs Writer (Haiku, Write/Edit only)
  Purpose: Update relevant documentation to reflect infrastructure changes.
```

---

## 4. Team Spawn Patterns

### Pattern 1: Natural Language Team Request

The simplest approach -- describe the work and the team you want:

```
Create an agent team to refactor the authentication module. Spawn:
- An architect to plan the refactoring approach
- Two implementers, one for the backend auth service and one for the API routes
- A tester to write and run tests
Use Sonnet for implementers and tester, and require plan approval for the architect.
```

### Pattern 2: Explicit Model Assignment

When cost matters, specify models per teammate:

```
Create a team with 4 teammates:
- "researcher" using Haiku to search the codebase for all authentication patterns
- "architect" using Opus to design the new auth system
- "implementer" using Sonnet to write the code
- "tester" using Sonnet to write tests
```

### Pattern 3: Phased Team with Dependencies

For work that has a natural sequence:

```
Create an agent team for implementing the new CLI subcommand.

Phase 1 (parallel):
- "researcher" -- Find all existing CLI patterns in src/mde/cli/
- "spec-writer" -- Draft the subcommand specification

Phase 2 (after Phase 1):
- "implementer" -- Implement based on researcher's findings and spec
- "tester" -- Write tests once implementation starts

Phase 3 (after Phase 2):
- "reviewer" -- Review everything before we merge

Structure the task list so Phase 2 tasks depend on Phase 1,
and Phase 3 depends on Phase 2.
```

### Pattern 4: Competing Hypotheses (Debugging)

From the official docs, this is a strong pattern:

```
Users report the CLI exits after one command instead of staying in REPL mode.
Spawn 4 agent teammates to investigate different hypotheses.
Have them talk to each other to try to disprove each other's theories:
- Hypothesis 1: Signal handling issue in the event loop
- Hypothesis 2: stdin EOF detection triggering early exit
- Hypothesis 3: Exception in the REPL initialization
- Hypothesis 4: Race condition between async tasks
Update the findings doc with whatever consensus emerges.
```

### Pattern 5: Cross-Layer Feature Implementation

When a feature spans multiple layers:

```
Create a team to implement the new 'research score' feature:
- "backend" -- Implement the scoring algorithm in src/mde/research/scoring.py
- "cli" -- Add the CLI subcommand in src/mde/cli/research.py
- "integration" -- Wire the scoring into the existing research pipeline
- "tests" -- Write tests for all three layers

Each teammate owns their specific files. The backend teammate should
finish first since cli and integration depend on the scoring API.
```

### Pattern 6: Review Team (Parallel Lenses)

From the official docs:

```
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

---

## 5. Task Decomposition Strategies

### Strategy 1: File-Ownership Decomposition

The simplest and most conflict-free approach. Each teammate owns a distinct set of files:

```
Tasks:
1. [implementer] Modify src/mde/research/pipeline.py -- add source scoring
2. [implementer] Modify src/mde/research/catalog.py -- add URL classification
3. [tester] Create tests/test_research_scoring.py
4. [tester] Create tests/test_research_catalog.py
5. [reviewer] Review all changes (read-only)
```

**Rule:** Two teammates should NEVER edit the same file. If they must, make their tasks sequential with dependencies.

### Strategy 2: Layer Decomposition

Split by architectural layer:

| Layer | Owner | Files |
|-------|-------|-------|
| Data models | Teammate A | `src/mde/models/` |
| Business logic | Teammate B | `src/mde/services/` |
| CLI interface | Teammate C | `src/mde/cli/` |
| Tests | Teammate D | `tests/` |

### Strategy 3: Feature Slice Decomposition

Each teammate implements a complete vertical slice:

```
Tasks:
1. [teammate-1] Complete implementation of "catalog" subcommand:
   - Model in src/mde/models/catalog.py
   - Logic in src/mde/services/catalog.py
   - CLI in src/mde/cli/catalog.py
   - Tests in tests/test_catalog.py

2. [teammate-2] Complete implementation of "score" subcommand:
   - Model in src/mde/models/score.py
   - Logic in src/mde/services/score.py
   - CLI in src/mde/cli/score.py
   - Tests in tests/test_score.py
```

**Advantage:** Each teammate has full context for their feature.
**Risk:** Shared utilities or models may conflict.

### Strategy 4: Research Decomposition (Source-Per-Task)

For research work, assign one source per task:

```
Tasks:
1. Fetch and summarize https://example.com/doc1
2. Fetch and summarize https://example.com/doc2
3. Fetch and summarize https://example.com/doc3
4. [depends: 1,2,3] Cross-reference all findings
5. [depends: 4] Write final report
```

### Task Sizing Guidelines (from official docs)

- **Too small:** Coordination overhead exceeds the benefit
- **Too large:** Teammates work too long without check-ins
- **Just right:** Self-contained units that produce a clear deliverable
- **Target:** 5-6 tasks per teammate keeps everyone productive

---

## 6. Quality Gates

### TeammateIdle Hook

Runs when a teammate is about to go idle. Exit with code 2 to send feedback and keep the teammate working.

**Use case:** Ensure teammates don't stop prematurely.

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/check-teammate-done.py"
          }
        ]
      }
    ]
  }
}
```

**Example validation script for Python dev team:**

```python
#!/usr/bin/env python3
"""Check if a teammate has completed their quality criteria before going idle."""
import json
import subprocess
import sys

input_data = json.loads(sys.stdin.read())
teammate_name = input_data.get("teammate_name", "")

if "tester" in teammate_name:
    # Verify tests actually pass
    result = subprocess.run(["uv", "run", "pytest", "--tb=short", "-q"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("Tests are failing. Fix them before going idle.", file=sys.stderr)
        sys.exit(2)  # Keep teammate working

elif "implementer" in teammate_name:
    # Verify ruff passes
    result = subprocess.run(["uv", "run", "ruff", "check", "src/mde/"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("Ruff lint errors found. Fix them before going idle.", file=sys.stderr)
        sys.exit(2)

elif "reviewer" in teammate_name:
    # Verify reviewer produced findings
    # (check if they sent a message with findings)
    pass

sys.exit(0)  # Allow idle
```

### TaskCompleted Hook

Runs when a task is being marked complete. Exit with code 2 to prevent completion and send feedback.

**Use case:** Enforce quality standards before tasks can close.

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/validate-task-completion.py"
          }
        ]
      }
    ]
  }
}
```

**Example validation for different team types:**

```python
#!/usr/bin/env python3
"""Validate task completion criteria by team type."""
import json
import subprocess
import sys

input_data = json.loads(sys.stdin.read())
task_description = input_data.get("task_description", "").lower()

# Python development team gates
if "implement" in task_description:
    # Must pass type checking
    result = subprocess.run(["uv", "run", "ty", "check", "src/mde/"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("Type errors found. Fix before marking complete.", file=sys.stderr)
        sys.exit(2)

elif "test" in task_description:
    # Must have coverage above threshold
    result = subprocess.run(
        ["uv", "run", "pytest", "--cov=src/mde", "--cov-fail-under=80", "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Coverage below 80%. Add more tests.", file=sys.stderr)
        sys.exit(2)

# Research team gates
elif "fetch" in task_description or "source" in task_description:
    # Must have produced output in the expected location
    pass

elif "synthesize" in task_description:
    # Must reference all source tasks
    pass

sys.exit(0)
```

### Per-Team Quality Gate Matrix

| Team Type | TeammateIdle Check | TaskCompleted Check |
|-----------|-------------------|---------------------|
| **Python Dev** | ruff check + ty check + pytest | Coverage threshold, type safety, lint clean |
| **Research** | Has produced output file | Source content extracted, URLs cataloged |
| **Dotfiles** | `mde-py validate --all` passes | Validation clean, no new warnings |
| **Infrastructure** | No broken brew packages | Brewfile parseable, no conflicts with mise |
| **Review** | Has produced findings report | All critical findings addressed |

### Plan Approval Gate

For complex or risky tasks, require plan approval before implementation:

```
Spawn an architect teammate to refactor the research pipeline.
Require plan approval before they make any changes.
Only approve plans that include test coverage for every new module
and don't modify the existing scoring baseline.
```

The lead reviews and approves/rejects plans autonomously. Provide criteria in the prompt to guide its judgment.

---

## 7. Comparison with Other Multi-Agent Frameworks

### Native Agent Teams vs gstack Conductor

| Dimension | Native Agent Teams | gstack Conductor |
|-----------|-------------------|-----------------|
| **Orchestration** | Built-in: lead spawns teammates, shared task list | External: separate workspace per session, manual coordination |
| **Communication** | Direct teammate-to-teammate messaging + mailbox | No inter-session communication; ELI16 mode re-grounds context |
| **Isolation** | Same working directory (conflict risk) | Separate git worktree per session (full isolation) |
| **Task coordination** | Shared task list with claim/dependency system | No shared task list; each session has its own objective |
| **Scale** | 3-5 teammates recommended | 10-15 parallel sessions demonstrated |
| **Browser support** | None built-in | Each workspace gets its own Chromium process |
| **Skill chaining** | Not skill-aware; uses natural language | Full skill chain (plan -> review -> qa -> ship) |
| **Token cost** | Higher per teammate (full context window each) | Similar (each session is independent) |
| **Setup** | Environment variable + prompt | Install gstack + Conductor |
| **Quality gates** | TeammateIdle + TaskCompleted hooks | /review blocks /ship (critical findings gate) |
| **Best for** | Collaborative work needing discussion | Independent parallel sprints |

**Verdict:** Use agent teams when teammates need to share findings and coordinate. Use Conductor-style worktree parallelism when tasks are fully independent and you want stronger isolation.

### Native Agent Teams vs ARIS Cross-Model Review

| Dimension | Native Agent Teams | ARIS Cross-Model Review |
|-----------|-------------------|------------------------|
| **Review model** | Same model (Claude) reviews its own work | Different model (GPT-5.4) reviews Claude's work |
| **Blind spot coverage** | Teammates can challenge each other but share same model biases | Cross-model adversarial review breaks blind spots |
| **State persistence** | Team config at ~/.claude/teams/ | REVIEW_STATE.json survives context compaction |
| **Iteration** | Manual via lead coordination | Automated 4-round loop with score tracking |
| **Cost** | Multiple Claude sessions | Claude + GPT-5.4 API costs |
| **Setup** | Environment variable | Codex MCP server + API key |

**Verdict:** For code review, agent teams provide good coverage through multiple Claude perspectives. For research review where breaking blind spots is critical, ARIS's cross-model pattern is superior. Consider combining both: use agent teams for implementation with one teammate dedicated to cross-model review via Codex MCP.

### Native Agent Teams vs agent-orchestrator Fleet Management

| Dimension | Native Agent Teams | agent-orchestrator |
|-----------|-------------------|--------------------|
| **Architecture** | Monolithic (all in Claude Code process) | Plugin-based (8 swappable slots) |
| **State tracking** | Task list + mailbox | 17-state lifecycle + 6-state activity detection |
| **Reaction engine** | Hooks (TeammateIdle, TaskCompleted) | Configurable YAML reactions with retry/escalation |
| **PR integration** | Manual (teammate creates PR) | Automatic CI/review/merge monitoring |
| **Notifications** | None built-in | Desktop/Slack/webhook with priority routing |
| **Worktree isolation** | Optional (subagent `isolation: worktree`) | Default (each session gets its own worktree) |
| **Agent types** | Claude Code only | Claude Code, Codex, Aider, OpenCode |
| **Dashboards** | None | Next.js web dashboard |
| **Maturity** | Experimental | Production (3,288 tests) |

**Verdict:** Agent-orchestrator is more mature and feature-rich for production fleet management. Native agent teams are simpler to set up and better for ad-hoc collaborative work within a single Claude Code session.

### When to Use Each Approach

| Situation | Recommended Approach |
|-----------|---------------------|
| Quick 2-3 person collaborative task | Agent teams |
| Reviewing PR from multiple angles | Agent teams |
| Debugging with competing hypotheses | Agent teams |
| 5+ parallel independent tasks | Subagents with worktree isolation |
| Full sprint with build/review/QA | gstack Conductor pattern (worktrees) |
| Production CI/CD agent fleet | agent-orchestrator |
| Research with adversarial review | ARIS cross-model pattern |
| Large refactoring across many files | Agent teams with file ownership |
| Simple focused delegation (test run, search) | Subagents |
| Batch processing identical tasks | `/batch` or parallel subagents |

---

## 8. Team Configuration Files

### Current State (as of v2.1.32)

Agent teams are configured entirely through natural language prompts to the lead. There is **no declarative team template file format** in the official documentation.

However, we can create reusable team configurations using three complementary approaches:

### Approach 1: Subagent Definitions as Team Building Blocks

Define specialized subagents in `.claude/agents/` that can be referenced when spawning teams:

**`.claude/agents/research-fetcher.md`:**
```yaml
---
name: research-fetcher
description: Fetches and extracts content from URLs for research tasks. Use when a research team needs parallel source fetching.
tools: Bash, Read, Write
model: haiku
memory: project
---

You are a source fetcher for the research team. Your job:
1. Fetch the assigned URL using `npx agent-fetch "<url>" --json` or WebFetch
2. Extract the key content: title, main findings, relevant code/patterns
3. Write a summary to the location specified in your task
4. Log the URL to docs/research/source-catalog.md

Always catalog every URL you encounter, even tangential ones.
Classify: HIGH/MEDIUM/LOW/SKIP.
```

**`.claude/agents/python-implementer.md`:**
```yaml
---
name: python-implementer
description: Implements Python code in src/mde/ following project conventions. Use for mde development tasks.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
memory: project
skills:
  - dev
---

You are a Python implementer for the mde project. Rules:
- All code goes in src/mde/
- Use Pydantic for models, structlog for logging
- Tool config in pyproject.toml, never standalone config files
- Use `uv run <tool>` not `uv run python -m <module>`
- Run `uv run ruff check` and `uv run ty check` before finishing
```

**`.claude/agents/python-tester.md`:**
```yaml
---
name: python-tester
description: Writes and runs pytest tests for mde. Use for testing tasks.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
memory: project
---

You are a test writer for the mde project. Rules:
- All tests go in tests/
- Use pytest with fixtures
- Run tests with `uv run pytest`
- Never modify files under src/mde/
- Aim for edge cases, not just happy paths
```

### Approach 2: Skills as Team Recipes

Define skills that contain team spawn instructions:

**`.claude/skills/spawn-research-team.md`:**
```yaml
---
name: spawn-research-team
description: Spawns a specialized research team for source fetching and synthesis.
---

# Research Team Spawn Recipe

When invoked, create an agent team with the following structure.
Adapt the number of fetchers to the number of sources provided.

## Team Structure

1. **Lead (you):** Coordinate the research, synthesize final output
2. **Fetchers (1 per 3 sources):** Fetch and extract content from URLs
3. **Synthesizer (1):** Cross-reference all findings, identify patterns
4. **Writer (1):** Produce the final document in the project format

## Instructions for Lead

- Break the source list into groups of 3
- Assign each group to a fetcher teammate
- Set task dependencies: synthesizer depends on all fetchers, writer depends on synthesizer
- Use Haiku for fetchers, Sonnet for synthesizer, Haiku for writer
- Require plan approval for the synthesizer

## Output Format

The final document goes to `docs/research/trail/deep-reviews/[topic].md`
following the format of existing files in that directory.
```

**`.claude/skills/spawn-python-team.md`:**
```yaml
---
name: spawn-python-team
description: Spawns a specialized Python development team for src/mde/ work.
---

# Python Development Team Spawn Recipe

Create an agent team with these roles:

1. **Lead (you):** Plan architecture, review output, manage dependencies
2. **Implementer:** Write code in src/mde/ following project patterns
3. **Tester:** Write tests in tests/, run pytest
4. **Reviewer:** Read-only review for quality and convention adherence

## File Ownership Rules (CRITICAL)

- Implementer ONLY modifies: src/mde/**/*.py
- Tester ONLY modifies: tests/**/*.py
- Reviewer modifies: NOTHING (read-only)
- Lead modifies: pyproject.toml, docs/

## Quality Gates

Before marking any implementation task complete:
- `uv run ruff check src/mde/` must pass
- `uv run ty check src/mde/` must pass

Before marking any test task complete:
- `uv run pytest tests/` must pass

## Task Decomposition

Break the feature into:
1. Data models (if any new Pydantic models needed)
2. Business logic (service layer)
3. CLI integration (if user-facing)
4. Tests for each of the above
```

### Approach 3: CLI-Defined Teams for Automation

Use `--agents` flag for reproducible team configurations in scripts:

```bash
claude --agents '{
  "research-fetcher": {
    "description": "Fetches URLs for research. Use proactively for source fetching.",
    "prompt": "You fetch and extract content from URLs. Use agent-fetch or WebFetch.",
    "tools": ["Bash", "Read", "Write"],
    "model": "haiku"
  },
  "research-synthesizer": {
    "description": "Synthesizes research findings. Use after fetching completes.",
    "prompt": "You cross-reference findings from multiple sources. Read-only analysis.",
    "tools": ["Read", "Glob", "Grep"],
    "model": "sonnet"
  }
}'
```

### Recommended Configuration Structure for MDE

```
.claude/
  agents/
    research-fetcher.md       # Haiku, Bash-only
    research-synthesizer.md   # Sonnet, read-only
    python-implementer.md     # Sonnet, full tools
    python-tester.md          # Sonnet, full tools
    python-reviewer.md        # Sonnet, read-only
    mise-specialist.md        # Sonnet, full tools
    chezmoi-specialist.md     # Sonnet, full tools
    security-auditor.md       # Sonnet, read-only
    validator.md              # Haiku, Bash for validation commands
  skills/
    spawn-research-team.md
    spawn-python-team.md
    spawn-dotfiles-team.md
    spawn-infra-team.md
```

---

## 9. Combining Teams and Subagents

The most effective pattern for our project combines both systems:

### Subagents for Focused Delegation

Use subagents (defined in `.claude/agents/`) when:
- The task is self-contained and doesn't need inter-agent communication
- You want cost control (Haiku for simple tasks)
- You want tool restrictions (read-only reviewers)
- You want worktree isolation for risky operations

### Teams for Collaborative Work

Use agent teams when:
- Teammates need to share findings and challenge each other
- The work requires coordination across multiple concerns
- You want the shared task list and claim system
- You're debugging with competing hypotheses

### Hybrid Pattern

1. Use **subagents** as the building blocks (defined in `.claude/agents/`)
2. Use **skills** as team recipes (defined in `.claude/skills/`)
3. Use **agent teams** when the skill recipe calls for collaboration
4. Use **standalone subagents** when the recipe calls for focused work

Example: A research cycle might start with an agent team for collaborative source analysis, then dispatch a standalone subagent for writing the final document (since writing doesn't need collaboration).

---

## 10. Recommendations for the MDE Project

### Immediate Actions

1. **Create the subagent files** listed in Section 8 under `.claude/agents/`. These are the reusable building blocks.

2. **Create team recipe skills** under `.claude/skills/` for the four team types (research, python, dotfiles, infrastructure).

3. **Add quality gate hooks** to `.claude/settings.json` for TeammateIdle and TaskCompleted, using the Python scripts from Section 6.

4. **Add `teammateMode` to settings.json:**
   ```json
   {
     "env": {
       "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
     },
     "teammateMode": "in-process"
   }
   ```

### Model Routing by Role

| Role | Model | Rationale |
|------|-------|-----------|
| Lead / Architect | Opus | Complex reasoning, plan review |
| Implementer | Sonnet | Balanced capability and cost |
| Tester | Sonnet | Needs to reason about edge cases |
| Reviewer | Sonnet | Needs to reason about patterns |
| Fetcher | Haiku | Simple extraction, low cost |
| Writer | Haiku | Structured output, low cost |
| Validator | Haiku | Run commands, check output |
| Synthesizer | Sonnet | Cross-referencing requires reasoning |

### Token Cost Management

Agent teams are expensive. Manage costs by:

1. **Use Haiku for simple roles** (fetchers, writers, validators)
2. **Limit team size to 3-5** (official recommendation)
3. **Use subagents for non-collaborative work** (lower overhead)
4. **Set maxTurns on subagents** to prevent runaway costs
5. **Use plan approval** for expensive operations to catch mistakes early

### File Organization

Per our project rules:
- Subagent definitions: `.claude/agents/` (checked into git)
- Team recipe skills: `.claude/skills/` (checked into git)
- Quality gate scripts: `src/mde/hooks/` (Python, not shell scripts)
- Team config (runtime): `~/.claude/teams/` (not in git)
- Hook configuration: `.claude/settings.json` or `~/.claude/settings.json`

### What NOT to Do

1. **Do not use teams for single-file edits** -- overkill, use main session
2. **Do not let two teammates edit the same file** -- leads to overwrites
3. **Do not spawn more than 5 teammates** -- diminishing returns, higher costs
4. **Do not leave teams running unattended for long** -- monitor and steer
5. **Do not use teams when subagents suffice** -- teams have higher token cost
6. **Do not nest teams** -- not supported; use subagents within team members instead

---

## Source URLs

| Source | URL |
|--------|-----|
| Agent teams documentation | https://code.claude.com/docs/en/agent-teams |
| Subagents documentation | https://code.claude.com/docs/en/sub-agents |
| Common workflows | https://code.claude.com/docs/en/common-workflows |
| Hooks documentation | https://code.claude.com/docs/en/hooks |
| gstack reference | Local: docs/research/trail/deep-reviews/gstack-complete-reference.md |
| ARIS reference | Local: docs/research/trail/deep-reviews/aris-and-compound-complete.md |
| agent-orchestrator reference | Local: docs/research/trail/deep-reviews/orchestrator-autoresearch-complete.md |
| Plugin ecosystem reference | Local: docs/research/trail/deep-reviews/skill-plugin-ecosystem-complete.md |
