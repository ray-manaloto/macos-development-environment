# gstack Complete Reference

> Definitive reference for garrytan/gstack v0.4.1 -- multi-agent orchestration patterns
> for Claude Code. Sources: gstacks.org, github.com/garrytan/gstack.
> Fetched: 2026-03-20.

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [Complete Skill Catalog (21 Skills)](#complete-skill-catalog-21-skills)
4. [The Sprint Workflow](#the-sprint-workflow)
5. [Skill Chaining and Artifact Handoff](#skill-chaining-and-artifact-handoff)
6. [Conductor: 10-15 Parallel Sessions](#conductor-10-15-parallel-sessions)
7. [Browser Automation](#browser-automation)
8. [Cookie Import for Authenticated Testing](#cookie-import-for-authenticated-testing)
9. [Automated QA Testing](#automated-qa-testing)
10. [Code Review with /review](#code-review-with-review)
11. [Greptile Integration](#greptile-integration)
12. [The /ship One-Command Release Pipeline](#the-ship-one-command-release-pipeline)
13. [The /codex Cross-Model Review Pattern](#the-codex-cross-model-review-pattern)
14. [The /investigate Auto-Freeze Debugging Pattern](#the-investigate-auto-freeze-debugging-pattern)
15. [Cross-Agent Compatibility](#cross-agent-compatibility)
16. [Analytics and Metrics Tracking](#analytics-and-metrics-tracking)
17. [Configuration](#configuration)
18. [Troubleshooting](#troubleshooting)
19. [Architecture Internals](#architecture-internals)

---

## Overview

gstack is an open-source (MIT) skill pack for Claude Code created by Garry Tan,
President and CEO of Y Combinator. It transforms a single AI assistant into a virtual
software development team by providing 21 slash-command skills covering the full
development lifecycle: product thinking, architecture, implementation, review, QA,
shipping, and retrospective.

**Core philosophy:** Planning is not review. Review is not shipping. Founder taste is
not engineering rigor. If you blur all of that together, you get mediocre output.
gstack provides "explicit gears" -- distinct cognitive modes activated by slash commands.

**Key stats (as of March 2026):**
- 16,000+ GitHub stars (10,000 in first 48 hours)
- 1,800+ forks
- 79.6% TypeScript, 18.3% Go
- Garry Tan's personal throughput: 10,000-20,000 LOC/day, 100+ PRs/week

**What it is NOT:** A prompt pack for beginners, a linter, a style checker, or a SaaS
product. It is an operating system for people who ship.

---

## Installation and Setup

### Requirements

| Dependency | Purpose |
|-----------|---------|
| Claude Code | Runtime environment -- skills are Claude Code slash commands |
| Git | Clone the gstack repository |
| Bun v1.0+ | Compile the /browse binary and install dependencies |
| Node.js | Windows only (fallback for Playwright pipe transport bug bun#4253) |

**Platforms:** macOS and Linux, x64 and arm64.

### Step 1: Install on Your Machine (30 seconds)

Open Claude Code and paste:

```
git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

The `setup` script:
1. Installs `node_modules` via Bun (gitignored)
2. Compiles the `/browse` binary (~58 MB native executable)
3. Creates symlinks for Claude Code skill discovery
4. Verifies installation

Then add a "gstack" section to CLAUDE.md listing all 21 skills and directing Claude to
use `/browse` instead of `mcp__claude-in-chrome__*` tools.

### Step 2: Add to Your Repo for Teammates (optional)

```bash
cp -Rf ~/.claude/skills/gstack .claude/skills/gstack
rm -rf .claude/skills/gstack/.git
cd .claude/skills/gstack && ./setup
```

Real files get committed (not a submodule). Teammates clone, then run `./setup` once.
Project-level skills override machine-level skills (same name = project version wins).

### What Gets Installed

| Component | Location | Size |
|-----------|----------|------|
| Skill files (Markdown) | `~/.claude/skills/gstack/` | Small |
| Symlinks | `~/.claude/skills/` | Pointers |
| Browser binary | `~/.claude/skills/gstack/browse/dist/browse` | ~58 MB |
| node_modules | `~/.claude/skills/gstack/node_modules/` | Gitignored |
| Config | `~/.gstack/config.yaml` | Created on first use |

Nothing touches PATH. No background daemons at install time.

### Upgrading

```
# Inside Claude Code:
/gstack-upgrade

# Or enable automatic upgrades:
# ~/.gstack/config.yaml
auto_upgrade: true
```

For project copies: `/gstack-upgrade` then `cp -Rf ~/.claude/skills/gstack .claude/skills/gstack`.

### Uninstalling

```bash
rm -f ~/.claude/skills/gstack-*
rm -rf ~/.claude/skills/gstack
rm -rf ~/.gstack
```

---

## Complete Skill Catalog (21 Skills)

### 15 Core Skills

| # | Skill | Specialist Role | Purpose |
|---|-------|----------------|---------|
| 1 | `/office-hours` | YC Office Hours | Start here. Six forcing questions that reframe your product before you write code. Pushes back on your framing, challenges premises, generates implementation alternatives. Design doc feeds into every downstream skill. |
| 2 | `/plan-ceo-review` | CEO / Founder | Rethink the problem from the user's POV. Find the 10-star product hiding inside the request. Four modes: Expansion, Selective Expansion, Hold Scope, Reduction. "Brian Chesky mode." |
| 3 | `/plan-eng-review` | Eng Manager / Tech Lead | Lock architecture, data flow, state transitions, edge cases, tests. Forces diagram generation: sequence, state, component, data-flow. Test matrices. |
| 4 | `/plan-design-review` | Senior Designer | Rates each design dimension 0-10, explains what a 10 looks like, edits the plan to get there. AI Slop detection. Interactive -- one AskUserQuestion per design choice. |
| 5 | `/design-consultation` | Design Partner | Build a complete design system from scratch. Knows the landscape, proposes creative risks, generates realistic product mockups. Writes `DESIGN.md`. |
| 6 | `/review` | Staff Engineer (Paranoid) | Structural audit for bugs that pass CI but blow up in production. N+1 queries, race conditions, trust boundary violations, missing indexes, stale reads. Two-pass: critical (blocks /ship) and informational. Auto-triages Greptile comments. |
| 7 | `/investigate` | Debugger | Systematic root-cause debugging. Iron Law: no fixes without investigation. Traces data flow, tests hypotheses, stops after 3 failed fixes. Auto-freezes to the module being investigated. |
| 8 | `/design-review` | Designer Who Codes | Same audit as /plan-design-review, then fixes what it finds. Atomic commits, before/after screenshots. |
| 9 | `/qa` | QA Lead | Test your app in a real browser, find bugs, fix them with atomic commits, re-verify. Auto-generates regression tests for every fix. Four modes: diff-aware, full, quick (~30s), regression baseline. Health score 0-100. |
| 10 | `/qa-only` | QA Reporter | Same methodology as /qa but report only. Pure bug report without code changes. |
| 11 | `/ship` | Release Engineer | Sync main, run tests, audit coverage, resolve Greptile comments, push, open PR. Bootstraps test frameworks if absent. One command. Auto-invokes /document-release. |
| 12 | `/document-release` | Technical Writer | Update all project docs to match what you just shipped. Catches stale READMEs. Auto-invoked by /ship. |
| 13 | `/retro` | Eng Manager | Team-aware weekly retro. Per-person breakdowns, shipping streaks, test health trends, growth opportunities. Saves JSON snapshots for trend tracking. Tracks Greptile batting average. |
| 14 | `/browse` | QA Engineer | Give the agent eyes. Persistent headless Chromium, real clicks, real screenshots. ~100ms per command after cold start. |
| 15 | `/setup-browser-cookies` | Session Manager | Import cookies from real browser (Comet, Chrome, Arc, Brave, Edge) into headless session. Test authenticated pages. Interactive domain picker. |

### 6 Power Tools

| # | Skill | Purpose |
|---|-------|---------|
| 16 | `/codex` | Second Opinion -- independent code review from OpenAI Codex CLI. Three modes: review (pass/fail gate), adversarial challenge, open consultation. Cross-model analysis when both /review and /codex have run. |
| 17 | `/careful` | Safety Guardrails -- warns before destructive commands (rm -rf, DROP TABLE, force-push). Say "be careful" to activate. Override any warning. |
| 18 | `/freeze` | Edit Lock -- restrict file edits to one directory. Prevents accidental changes outside scope while debugging. |
| 19 | `/guard` | Full Safety -- /careful + /freeze in one command. Maximum safety for production work. |
| 20 | `/unfreeze` | Unlock -- remove the /freeze boundary. |
| 21 | `/gstack-upgrade` | Self-Updater -- upgrade gstack to latest. Detects global vs vendored install, syncs both, shows changelog. |

---

## The Sprint Workflow

gstack is a process, not a collection of tools. The skills are ordered the way a sprint
runs:

```
Think --> Plan --> Build --> Review --> Test --> Ship --> Reflect
```

Each skill feeds into the next. Artifacts produced by one skill are consumed by the next.

### Complete Sprint Example

```
# 1. THINK: Reframe the problem
You:    I want to build a daily briefing app for my calendar.
/office-hours
Claude: [asks forcing questions, pushes back on framing]
        "You're not building a daily briefing app. You're building
         a personal chief of staff AI."
        [writes design doc --> feeds into downstream skills]

# 2. PLAN (Product): Pressure-test the idea
/plan-ceo-review
Claude: [reads design doc, challenges scope, runs 10-section review]
        [four modes: Expansion, Selective Expansion, Hold Scope, Reduction]

# 3. PLAN (Engineering): Design the architecture
/plan-eng-review
Claude: [ASCII diagrams for data flow, state machines, error paths]
        [test matrix, failure modes, security concerns]

# 4. PLAN (Design): Rate and improve design
/plan-design-review
Claude: [rates each dimension 0-10, AI Slop detection]

# 5. BUILD: Implement the plan
You:    Approve plan. Exit plan mode.
Claude: [writes code across multiple files, ~8 minutes]

# 6. REVIEW: Find production-grade bugs
/review
Claude: [AUTO-FIXED] 2 issues. [ASK] Race condition --> you approve fix.
        [triages any Greptile comments]

# 7. TEST: Verify everything works
/qa https://staging.myapp.com
Claude: [opens real browser, clicks through flows, finds and fixes bugs]
        Health: 62 --> 94

# 8. SHIP: Land the branch
/ship
Claude: Tests: 42 --> 51 (+9 new). PR: github.com/you/app/pull/42
        [auto-invokes /document-release]

# 9. REFLECT: Weekly retrospective
/retro
Claude: [per-person metrics, shipping streaks, biggest ship of the week]
```

**Timing:** One sprint, one person, one feature takes about 30 minutes. But you can
run 10-15 of these sprints in parallel via Conductor.

---

## Skill Chaining and Artifact Handoff

Skills share context within a Claude Code session. Each skill produces artifacts that
subsequent skills consume:

### Artifact Flow Diagram

```
/office-hours
  |-- writes design doc
  v
/plan-ceo-review
  |-- reads design doc, produces reframed specification
  v
/plan-eng-review
  |-- reads reframed spec, produces:
  |     - Architecture diagrams (sequence, state, component, data-flow)
  |     - Test matrix
  |     - Failure mode catalog
  v
/plan-design-review
  |-- reads plan, produces design ratings and DESIGN.md
  v
Implementation Phase
  |-- code is written guided by plan artifacts
  v
/review
  |-- reads git diff against main
  |-- reads Greptile PR comments (if present)
  |-- produces: critical findings list, informational findings
  |-- auto-fixes obvious issues
  v
/ship
  |-- reads /review findings (critical findings block shipping)
  |-- syncs main, runs tests
  |-- triages remaining Greptile comments
  |-- opens PR with structured description
  |-- auto-invokes /document-release
  v
/qa
  |-- reads git diff to identify affected routes
  |-- uses /browse for browser automation
  |-- produces: health score, bug report, atomic fix commits
  v
/retro
  |-- reads commit history, /review data, Greptile batting average
  |-- produces: JSON snapshot for trend tracking
```

### Concrete Example: Photo Upload Feature

**Input to /plan-ceo-review:** "Add photo upload to listings"

**Output from /plan-ceo-review (artifact 1):** Reframed spec: "Smart listing creation
from photos. Auto-identify item from image, generate title and description, pull specs
from product database, suggest pricing from comps."

**Input to /plan-eng-review:** The reframed spec above (read from session context).

**Output from /plan-eng-review (artifact 2):**
- Sequence diagram: client -> upload service -> image recognition -> product DB -> listing service
- State diagram: draft -> processing -> enriched -> published
- Component diagram: Upload widget, Image Analyzer, Product Matcher, Listing Builder
- Test matrix: 4 features x 3 test types = 12 test scenarios
- Failure modes: image recognition fails, product not found, concurrent uploads

**Input to /review:** git diff of the implementation.

**Output from /review (artifact 3):** "CRITICAL: find_or_create_by on product_match
without unique DB index. Race condition when two uploads match the same product
simultaneously."

**Input to /ship:** The review findings. Critical issues must be resolved before
/ship proceeds.

### Smart Review Routing

gstack tracks which reviews have been run and routes appropriately:
- CEO doesn't need to review infra bug fixes
- Design review isn't needed for backend-only changes
- The Review Readiness Dashboard shows status before shipping

---

## Conductor: 10-15 Parallel Sessions

[Conductor](https://conductor.build) is the orchestration layer that enables running
multiple Claude Code sessions in parallel, each in an isolated workspace.

### Architecture

1. **Workspace creation** -- Separate workspace per session with own working directory, git worktree, and shell context
2. **Session management** -- Independent Claude Code instances, started/stopped/monitored independently
3. **Automatic isolation** -- Each workspace gets its own Chromium process (separate cookies, tabs, console logs)
4. **State persistence** -- Per-workspace `.gstack/browse.json` tracking browser state
5. **Resource management** -- Auto-terminate browser daemons after idle
6. **Random port selection** -- Range 10000-60000, up to 5 retries on collision

### Workspace Isolation Details

```
.gstack/
  browse.json        # Browser state: port, PID, open tabs, session info
  cookies/           # Exported cookie storage per domain
  logs/              # Browser console and network logs
  screenshots/       # Captured screenshots from /browse commands
```

### What Gets Isolated Per Workspace

| Component | Isolation Level |
|-----------|----------------|
| Chromium process | Separate OS process per workspace |
| Cookies & sessions | Scoped to workspace browser |
| Console & network logs | Stored in workspace .gstack/ |
| Port binding | Random 10000-60000, no collisions |
| File system | Own git worktree |

### The Three-Agent Sprint Pattern

| Agent | Task | Skills Used |
|-------|------|-------------|
| Agent 1: Builder | Implementing feature or fixing bug | Code editing, /browse for local testing |
| Agent 2: Reviewer | Running /review on an open PR | Code review, static analysis |
| Agent 3: QA | Running /qa on staging | /browse, /qa, screenshot verification |

### ELI16 Mode

When 3+ sessions are active, every response re-grounds context. Instead of assuming
you remember what each session is doing, the AI re-establishes the situation:

> "Session 3 QA: the checkout flow on staging failed because the payment API returned
> a 502 -- retrying with a 3-second delay before the payment step."

### Resource Requirements

| Resource | Per Instance | 5 Parallel | 10 Parallel |
|----------|-------------|-----------|-------------|
| RAM (Chromium) | 150-300 MB | 750 MB-1.5 GB | 1.5-3 GB |
| CPU | Mostly idle between commands | Minimal | Minimal |
| Disk (.gstack/) | <10 MB | <50 MB | <100 MB |

**Recommendations:** 16 GB+ RAM for 3-5 sessions. 32 GB+ for 8-10 sessions.

### Performance Comparison

| Approach | Total Time | Context Switches |
|----------|-----------|-----------------|
| Sequential (traditional) | ~3 hours | 4+ major switches |
| Parallel (gstack + Conductor) | ~45 minutes | 0 per agent |

### Best Practices for Parallel Coding

1. Assign one cognitive mode per agent -- don't mix building and reviewing
2. Give complete tasks, not fragments -- each agent owns its task end-to-end
3. Use QA agents as continuous validators
4. Start with 3 agents, scale up as comfortable
5. Think like a technical lead, not an individual contributor

---

## Browser Automation

The `/browse` skill provides a persistent headless Chromium browser daemon powered by
Playwright (Microsoft).

### Performance

| Operation | Latency |
|-----------|---------|
| Cold start (first invocation) | ~3 seconds |
| Subsequent commands | ~100-200 ms |
| Screenshot capture | <500 ms |
| Auto-shutdown (idle) | 30 minutes |

Claimed to be **20x faster than Claude for Chrome MCP**, with no context bloat.

### The @ref System (Accessibility-Tree Refs)

Elements are addressed via accessibility-tree references (`@e1`, `@e2`, `@e3`) instead
of CSS selectors or XPath:

- **Resilient to UI changes** -- targets elements by accessibility role/position
- **Natural language friendly** -- "the submit button at @e5"
- **Accessibility-first** -- verifies elements are in the accessibility tree
- **Context-aware** -- references update with each snapshot
- Works with CSP-restricted sites, React hydration, and Shadow DOM

### Complete Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `goto` | Navigate to a URL | `/browse goto https://myapp.com` |
| `snapshot` | Capture page state (accessibility tree) | `/browse snapshot -i` |
| `click` | Click element by @ref | `/browse click @e4` |
| `fill` | Type text into form field | `/browse fill @e2 "hello"` |
| `screenshot` | Capture visual screenshot | `/browse screenshot` |
| `text` | Extract all visible text | `/browse text` |
| `console` | Read browser console logs | `/browse console` |
| `network` | Inspect network requests/responses | `/browse network` |
| `handoff` | Open visible Chrome at same page | `$B handoff` |
| `resume` | Resume after handoff | `$B resume` |

### Snapshot Flags

| Flag | Name | Purpose |
|------|------|---------|
| `-i` | Interactive | Show only interactive elements (buttons, links, form fields) |
| `-D` | Diff | Show only what changed since last snapshot |
| `-a` | Annotated | Screenshot with @ref labels overlaid on elements |
| `-C` | Cursor-Interactive | Enable hover states, drag-and-drop |

### Browser Handoff

When the AI gets stuck on a CAPTCHA, auth wall, or MFA prompt:

1. `$B handoff` opens a visible Chrome window at the exact same page with all cookies and tabs
2. You solve the problem manually
3. Tell Claude you're done
4. `$B resume` picks up right where it left off

The agent suggests handoff automatically after 3 consecutive failures.

### Technical Details

- **Binary:** Single 58 MB executable compiled with Bun
- **Engine:** Playwright by Microsoft
- **Communication:** Localhost-only HTTP with bearer token auth per session
- **Storage:** Native SQLite for cookie decryption
- **Shell injection prevention:** Hardcoded command registry, no string interpolation
- **Isolation:** Each Conductor workspace gets its own Chromium instance

---

## Cookie Import for Authenticated Testing

The `/setup-browser-cookies` skill imports real browser session cookies into the
headless Chromium instance.

### Supported Browsers

| Browser | Status |
|---------|--------|
| Comet | Auto-detected |
| Google Chrome | Auto-detected |
| Arc | Auto-detected |
| Brave | Auto-detected |
| Microsoft Edge | Auto-detected |

Firefox and Safari are NOT supported (different cookie storage/encryption).

### Two Import Modes

```bash
# Interactive picker (shows domains, you select which to import)
/setup-browser-cookies

# Direct domain import (skip picker)
/setup-browser-cookies github.com
```

### How It Works

1. **Browser detection** -- scans hardcoded registry of browser paths
2. **Cookie database access** -- copies SQLite DB to temp file (read-only original)
3. **Keychain decryption** -- retrieves key via macOS `security` command, PBKDF2 key derivation, AES-128-CBC decryption
4. **Interactive domain picker** -- terminal UI, no cookie values displayed
5. **Cookie injection** -- injected into Playwright headless Chromium

### Security Model

| Layer | Protection |
|-------|-----------|
| Keychain Gatekeeper | macOS prompt on first access per browser |
| In-Process Decryption | PBKDF2 + AES-128-CBC, never written to disk in plaintext |
| Read-Only DB Access | Original cookie DB never modified |
| Per-Session Key Caching | Key gone when server shuts down |
| No Cookie Values in Logs | Only domain names shown in picker and terminal |
| Shell Injection Prevention | Hardcoded registry, Bun.spawn() with explicit args |

### Common Workflow

```bash
# Import your staging session
/setup-browser-cookies staging.yourapp.com

# Now /browse and /qa can access authenticated routes
/browse goto https://staging.yourapp.com/admin/users
/browse snapshot

# Run QA on authenticated pages
/qa https://staging.yourapp.com
```

---

## Automated QA Testing

### /qa: Find, Fix, and Verify

Runs browser-based QA, fixes bugs with atomic commits, re-verifies. Produces
before/after health scores.

### /qa-only: Pure Bug Reports

Same methodology, never modifies code. Clean handoff for teams.

### Four Testing Modes

| Mode | Trigger | Duration | Description |
|------|---------|----------|-------------|
| Diff-Aware | Auto on feature branches | 5-15 min | Reads `git diff main`, tests only affected pages |
| Full | Manual | 5-15 min | Crawls entire app, all routes |
| Quick | Manual | ~30 seconds | Smoke test on critical paths |
| Regression | Manual | Varies | Diffs against saved baseline |

### Health Score System

Score 0-100 computed from number and severity of detected bugs, weighted against
scope of pages tested.

```
Before: 62  -->  After: 94
Ship-readiness: Ready to merge. 3 critical bugs fixed, 1 medium issue documented.
```

### Bug Severity Tiers

| Severity | Criteria | Examples |
|----------|----------|---------|
| Critical | Blocks core user flows or causes data loss | Broken checkout, login failure, JS crash, silent form failure |
| High | Major functionality degraded, workarounds exist | Wrong search results, broken pagination, unusable mobile layout |
| Medium | Visual or minor functional | Misaligned elements, console warnings, slow transitions |

/qa prioritizes critical bugs first. Each fix is an atomic commit (cherry-pickable/revertable).

### Reports

Saved to `.gstack/qa-reports/` with:
- Health score
- Categorized bug list with severity tags
- Screenshots of detected issues
- Testing mode used
- Timestamps
- Fix log with commit hashes (for /qa)

---

## Code Review with /review

The `/review` skill performs a structural audit -- not style nitpicking.

### Two-Pass Checklist

**Pass 1: Critical (Blocks /ship)**

| Category | What It Checks |
|----------|---------------|
| SQL and Data Safety | String interpolation in queries, TOCTOU races, update_column bypassing validations, N+1 queries |
| Race Conditions | Read-check-write without uniqueness constraints, find_or_create_by without unique DB indexes, non-atomic status transitions |
| LLM Trust Boundaries | LLM-generated values written to DB without format validation, structured tool output without type/shape checks |
| Enum/Value Completeness | New enum values traced through every consumer: case statements, allowlists, filter arrays |

**Pass 2: Informational (Non-blocking)**

| Category | What It Checks |
|----------|---------------|
| Conditional Side Effects | Code paths that forget side effects on one branch |
| Test Gaps | Tests asserting status but not side effects |
| Bad Retry Logic | Missing indexes, non-constant-time secret comparisons |
| Escaping/Type Coercion | Values crossing language boundaries where type could change |

### Explicit Suppressions

/review will NEVER flag:
- Harmless redundancy
- Missing comments on magic numbers during tuning
- Consistency-only changes

### Beyond the Diff

When a new enum value is introduced, /review uses Grep to find EVERY file referencing
sibling values, then reads each to verify the new value is handled in case statements,
allowlists, filter arrays, and display logic.

### Interactive Resolution

For each critical finding: fix it now, acknowledge and proceed, or mark as false positive.

---

## Greptile Integration

[Greptile](https://greptile.com) provides async PR review on GitHub. gstack adds a
triage layer on top.

### Setup

1. Install Greptile GitHub app on your repo (~30 seconds)
2. Push PRs as usual -- Greptile reviews automatically
3. Run `/review` or `/ship` -- gstack triages Greptile comments automatically

### Three-Way Classification

| Category | Action Taken | Developer Impact |
|----------|-------------|-----------------|
| Valid and Actionable | Added to critical findings, fix applied | Zero -- automated |
| Valid but Already Fixed | Auto-reply with fixing commit SHA | Zero |
| False Positive | Push back with concrete evidence | Zero |

### Tiered Reply System

- **Tier 1 (First response):** Friendly, evidence-included. Inline diff for fixes, code references for FPs.
- **Tier 2 (Re-flagged after prior reply):** Firm, overwhelming evidence. Full diff, evidence chain with file permalinks and commit SHAs, request to recalibrate severity.

Escalation detection is automatic -- checks if prior reply exists on the thread.

### Learning System

Every false positive is saved to `~/.gstack/greptile-history.md`:

```
2026-03-13 | garrytan/myapp | fp  | app/services/auth_service.rb | race-condition
2026-03-13 | garrytan/myapp | fix | app/models/user.rb           | null-check
2026-03-14 | garrytan/myapp | already-fixed | lib/payments.rb     | error-handling
```

- **Per-project history** -- used for suppressions on future runs
- **Global aggregate** -- feeds into /retro for batting average tracking
- **Append-only, fault-tolerant** -- malformed lines skipped silently

### Greptile Batting Average

Tracked by `/retro` over time. Shows percentage of Greptile comments that led to
actual code changes vs. dismissed. Answers:
- What percentage of comments are actionable?
- Is accuracy improving or degrading?
- Which bug categories are most reliable?

---

## The /ship One-Command Release Pipeline

### What /ship Does (6 Steps)

1. **Sync with main** -- pulls latest, handles merge (auto-resolves straightforward conflicts, flags complex ones)
2. **Branch state check** -- uncommitted changes, stale checkpoints, divergence issues
3. **Rerun tests** -- full suite after main sync to catch regressions from upstream
4. **Resolve Greptile reviews** -- three-way triage (valid: fix, already-fixed: auto-reply, FP: push back)
5. **Update metadata** -- changelog, version bumps per project conventions
6. **Push and open PR** -- well-structured description, or updates existing PR

### Additional Behaviors

- **Bootstraps test frameworks** from scratch if the project doesn't have one
- **Coverage audit** every run
- **Auto-invokes /document-release** to update project docs
- **Critical /review findings block shipping** -- informational findings go in PR body

### When to Use /ship

**Yes:**
- Branch is code-complete and has passed review
- Need to sync with latest main
- Greptile comments need triage
- Repo requires changelog/version updates

**No:**
- Still deciding what to build (use /plan)
- Implementation not finished
- Fundamental review feedback unaddressed
- Need architectural changes

### Time Savings

| Task | Manual | With /ship |
|------|--------|-----------|
| Sync with main | 3-10 min | Automatic |
| Rerun tests | 5-15 min | Automatic |
| Address review comments | 10-30 min | Triaged automatically |
| Update changelog/version | 5-10 min | Automatic |
| Push and open PR | 5-10 min | Automatic |
| **Total** | **28-75 min** | **Single command** |

---

## The /codex Cross-Model Review Pattern

`/codex` provides an independent code review from OpenAI's Codex CLI -- a completely
different AI model reviewing the same diff.

### Three Modes

| Mode | Purpose |
|------|---------|
| Review | Pass/fail gate. Independent assessment of the diff. |
| Adversarial Challenge | Actively tries to break your code. |
| Open Consultation | Session continuity for ongoing discussion. |

### Cross-Model Analysis

When BOTH `/review` (Claude) and `/codex` (OpenAI) have reviewed the same branch,
gstack produces a cross-model analysis showing:
- Which findings overlap (high confidence issues)
- Which findings are unique to each model
- Disagreements between models

This provides a two-model safety net where blind spots in one model are caught by
the other.

---

## The /investigate Auto-Freeze Debugging Pattern

`/investigate` is systematic root-cause debugging with built-in safety.

### Core Principles

1. **Iron Law:** No fixes without investigation. The skill traces data flow and tests hypotheses BEFORE attempting any fix.
2. **Auto-Freeze:** Automatically activates `/freeze` on the module being investigated, preventing accidental changes to unrelated code.
3. **Three-Strike Rule:** Stops after 3 failed fix attempts and reports findings rather than continuing to thrash.

### Workflow

1. Describe the bug
2. /investigate traces data flow through the system
3. Forms hypotheses about root cause
4. Tests each hypothesis methodically
5. Only proposes fixes after root cause is confirmed
6. If fix fails 3 times, stops and provides detailed investigation report

The auto-freeze behavior is critical -- during debugging, Claude often wants to "fix"
things it notices in other files. /investigate prevents this scope creep by locking
edits to the module being investigated.

---

## Cross-Agent Compatibility

gstack works on any agent that supports the SKILL.md standard.

### Supported Agents

| Agent | Install Location | Setup Command |
|-------|-----------------|---------------|
| Claude Code | `~/.claude/skills/gstack` | `./setup` (default) |
| Codex CLI | `~/.codex/skills/gstack` | `./setup --host codex` |
| Gemini CLI | Auto-detected | `./setup --host auto` |
| Cursor | Auto-detected | `./setup --host auto` |

### Installation for Non-Claude Agents

```bash
# Specific host:
git clone https://github.com/garrytan/gstack.git ~/.codex/skills/gstack
cd ~/.codex/skills/gstack && ./setup --host codex

# Auto-detect all installed agents:
git clone https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup --host auto
```

Auto-detect installs to `~/.claude/skills/gstack` and/or `~/.codex/skills/gstack`
depending on what's available. All 21 skills work across all supported agents.

### Compatibility Notes

- Skills live in `.agents/skills/` and are discovered automatically by compliant agents
- Hook-based safety skills (`/careful`, `/freeze`, `/guard`) use inline safety advisory prose on non-Claude hosts
- The SKILL.md standard is defined at github.com/anthropics/claude-code

---

## Analytics and Metrics Tracking

### /retro Metrics

| Metric | Description |
|--------|-------------|
| Commits and LOC | Total commits, lines added/removed/net, per contributor and per day |
| Test Ratio | Test code vs production code per contributor |
| PR Sizes | Average PR size in lines changed |
| Fix Ratio | Bug fix commits vs new feature commits |
| Shipping Streaks | Consecutive days with commits |
| Peak Hours | Most productive hours per contributor (commit timestamp histogram) |
| Coding Sessions | Clusters of commits detected from timestamp proximity |
| Hotspot Files | Files accumulating the most changes |
| Biggest Ship | Single most significant contribution per person per week |
| Greptile Batting Average | Percentage of valid vs dismissed Greptile comments |

### JSON Snapshots

Saved to `.context/retros/` after every `/retro` run:

```
.context/retros/
  retro-2026-03-09.json
  retro-2026-03-16.json
```

Use `/retro compare` for week-over-week delta analysis:

```
This Week vs Last Week
Commits:         47 (+12, +34%)
LOC Changed:     2,841 (-523, -16%)
Test Ratio:      0.31 (+0.08)
Avg PR Size:     184 lines (-67 lines)
Fix Ratio:       18% (-5%)
Shipping Streak: 5 days (continuing)
```

### QA Reports

Saved to `.gstack/qa-reports/` with health scores, bug lists, screenshots, timestamps.

### Local Analytics Dashboard

```bash
gstack-analytics
```

Personal usage dashboard from local JSONL file -- no remote data needed.

### Opt-In Telemetry

- Default: OFF
- What's sent (if opted in): skill name, duration, success/fail, gstack version, OS
- What's NEVER sent: code, file paths, repo names, branch names, prompts
- Toggle: `gstack-config set telemetry off`
- Storage: Supabase (insert-only access via RLS)
- Schema: `supabase/migrations/001_telemetry.sql`

---

## Configuration

### Config File

Location: `~/.gstack/config.yaml`

```yaml
# Auto-upgrade on session start
auto_upgrade: true

# Telemetry (default: off)
telemetry: false
```

### CLAUDE.md Integration

Add to your project's CLAUDE.md:

```markdown
## gstack
Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /review, /ship, /browse, /qa, /qa-only, /design-review,
/setup-browser-cookies, /retro, /investigate, /document-release, /codex, /careful,
/freeze, /guard, /unfreeze, /gstack-upgrade.
```

### Proactive Skill Suggestions

gstack notices what stage you're in (brainstorming, reviewing, debugging, testing)
and suggests the right skill. Disable with: "stop suggesting" (remembered across
sessions).

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| Skills not showing up | `cd ~/.claude/skills/gstack && ./setup` |
| /browse fails | `cd ~/.claude/skills/gstack && bun install && bun run build` |
| Stale install | `/gstack-upgrade` or `auto_upgrade: true` |
| Windows issues | Use Git Bash or WSL. Ensure both `bun` and `node` on PATH. |
| Claude can't see skills | Add gstack section to CLAUDE.md |
| Keychain prompt not appearing | Check macOS user session is active, reset in Keychain Access.app |
| Cookies not working after import | Re-login in real browser, re-import. Check for IP-based session binding. |
| Browser not detected | Ensure browser is at standard /Applications path |
| Permission errors (macOS) | `xattr -d com.apple.quarantine ~/.claude/skills/gstack/browse/browse` |
| Bun not installed | `curl -fsSL https://bun.sh/install \| bash` or `brew install oven-sh/bun/bun` |

---

## Architecture Internals

### Technology Stack

- **79.6% TypeScript** -- skill definitions, browser automation server, cookie handling
- **18.3% Go** -- performance-critical components
- **Binary:** Single 58 MB Bun-compiled executable
- **Browser engine:** Playwright (Microsoft)
- **Cookie decryption:** Native SQLite via Bun, PBKDF2 + AES-128-CBC
- **Communication:** Localhost HTTP with bearer token auth

### Browser Daemon Architecture

1. First invocation compiles and starts headless Chromium (~3 seconds)
2. Daemon listens on localhost, random port 10000-60000
3. Commands sent as HTTP requests, responses as structured data
4. Session state persists: cookies, tabs, localStorage
5. Auto-shutdown after 30 minutes idle
6. Per-workspace isolation via separate `.gstack/` directories

### Security Design

- Localhost-only binding (no network exposure)
- Bearer token auth per session
- Cookie values never written to disk in plaintext
- Keychain access requires explicit user approval
- Database opened read-only
- Shell injection prevented via hardcoded registry
- No telemetry by default

### Skill Files

Skills are Markdown files that define:
- Slash command name
- Cognitive mode description
- Behavioral constraints
- Output format expectations
- Integration points with other skills

All skills are human-readable, editable, and forkable. They live entirely in `.claude/`.

---

## Source URLs

| Source | URL |
|--------|-----|
| Documentation site | https://gstacks.org/ |
| GitHub repository | https://github.com/garrytan/gstack |
| Skills deep dive | https://gstacks.org/gstack-claude-code-skills.html |
| Plan review guide | https://gstacks.org/gstack-ai-plan-review.html |
| Code review guide | https://gstacks.org/gstack-ai-code-review.html |
| Shipping workflow | https://gstacks.org/gstack-ai-shipping-workflow.html |
| Browser automation | https://gstacks.org/gstack-browser-automation-testing.html |
| Automated QA testing | https://gstacks.org/gstack-automated-qa-testing.html |
| Parallel coding (Conductor) | https://gstacks.org/gstack-parallel-ai-coding.html |
| Engineering retrospective | https://gstacks.org/gstack-engineering-retrospective.html |
| Cookie import | https://gstacks.org/gstack-cookie-import-authenticated-testing.html |
| Greptile integration | https://gstacks.org/gstack-greptile-code-review.html |
| Setup/install guide | https://gstacks.org/gstack-setup-install-guide.html |
| Conductor | https://conductor.build |
| Greptile | https://greptile.com |
