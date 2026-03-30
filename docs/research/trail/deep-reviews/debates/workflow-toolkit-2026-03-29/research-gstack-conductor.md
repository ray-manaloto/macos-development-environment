# gstack Conductor Research Notes
**Date:** 2026-03-29
**Sources:**
- https://gstacks.org/gstack-setup-install-guide.html
- https://github.com/garrytan/gstack
- https://gstacks.org/gstack-parallel-ai-coding.html

---

## What Is gstack?

gstack is an open-source (MIT) collection of Claude Code slash-command skills authored by Garry Tan (YC president). It extends Claude Code with 29 specialist skills covering product review, engineering review, code review, QA, browser automation, security audit, and release management. The project claims 600K+ lines of production code shipped in 60 days at 10K–20K LOC/day using these skills.

The skills follow the SKILL.md standard and are compatible with Claude Code, Codex CLI, Gemini CLI, Cursor, and Factory Droid.

---

## How Conductor Coordinates CLI Tools

### What Conductor Is

Conductor is a **third-party workspace orchestration tool** available at `conductor.build`. It is NOT part of the gstack codebase itself — it is a dependency that gstack documents as required for parallel workflows. gstack does not ship conductor; it ships the skills that run *inside* conductor-managed workspaces.

### What Conductor Does

Conductor creates and manages isolated Claude Code sessions, each running in its own workspace. The coordination model:

1. **Workspace creation** — Conductor creates a separate workspace per Claude Code session. Each workspace is a fully isolated environment with its own working directory, git worktree, and shell context.

2. **Session management** — Each session runs an independent Claude Code instance. Sessions can be started, stopped, and monitored independently.

3. **Automatic browser isolation** — Every workspace gets its own isolated Chromium browser instance automatically (spawned on-demand by the `/browse` skill). No configuration is required for isolation.

4. **State persistence** — Each workspace maintains `.gstack/browse.json` tracking browser state, open tabs, and session data.

5. **Resource management** — Browser daemons auto-terminate after 30 minutes of idle time. Conductor handles workspace cleanup on session end.

### Isolation Mechanisms

Per workspace, the following are isolated:
- Separate headless Chromium process (own cookies, tabs, localStorage)
- Random port selection (10000–60000) with 5 retries on collision — no manual port management
- Per-workspace `.gstack/` directory:
  ```
  .gstack/
    browse.json        # Browser state: port, PID, open tabs
    cookies/           # Exported cookie storage per domain
    logs/              # Browser console and network logs
    screenshots/       # Captured screenshots
  ```
- Independent console/log streams — no cross-session pollution
- Separate git worktree — no file system conflicts between agents

### How Prompts Are Passed Between Tools

gstack does NOT define a message-passing protocol between agents. Instead, prompt chaining is implemented via **shared file artifacts**:

- `/office-hours` writes a design doc that `/plan-ceo-review` reads
- `/plan-eng-review` writes a test plan that `/qa` picks up
- `/review` catches bugs that `/ship` verifies are fixed

Each skill is a SKILL.md file (Markdown prompt definition). Skills are context-matched, not event-driven. The skill pipeline is:

```
/office-hours -> design doc -> /plan-ceo-review -> /plan-eng-review -> build -> /review -> /qa -> /ship
```

There is no runtime message bus. Downstream skills read artifacts (files) that upstream skills write. The Claude Code session context carries the conversation history.

### How Output Is Captured and Structured

- Skills produce output as Claude Code conversation responses (markdown)
- Browser output stored in `.gstack/screenshots/` and `.gstack/logs/`
- Retro data aggregated from git history (commits, lines added) across sessions
- `/retro` can run globally across all projects: `/retro global`
- Local analytics available via `gstack-analytics` CLI from local JSONL file
- Optional telemetry (off by default) posts: skill name, duration, success/fail, version, OS to Supabase

---

## Setup and Configuration

### Requirements

| Dependency | Purpose |
|---|---|
| Claude Code | Runtime host for all skills |
| Git | Clone gstack repo |
| Bun v1.0+ | Compiles `/browse` binary (~58MB headless Chromium) and installs node_modules |
| Node.js (Windows only) | Bun has a bug with Playwright pipe transport on Windows |

### Installation (Two-Step)

**Step 1 — Machine-global install:**
```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

The `setup` script:
1. Installs `node_modules` via Bun
2. Compiles the `/browse` binary (native executable, ~58 MB)
3. Creates symlinks for Claude Code skill discovery in `~/.claude/skills/`
4. Verifies installation

**Step 2 — Project repo (optional, for teams):**
```bash
cp -Rf ~/.claude/skills/gstack .claude/skills/gstack
```
Real files committed to repo (NOT a submodule) — `git clone` just works. Each teammate runs `.claude/skills/gstack/setup` once to build locally.

### Configuration File

`~/.gstack/config.yaml` — created on first use:
```yaml
auto_upgrade: true  # Check for updates at session start
```

### Claude Code CLAUDE.md Integration

Skills are only invocable if CLAUDE.md has a gstack section:
```markdown
## gstack
Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
Available skills: /office-hours, /plan-ceo-review, ...
```

### Codex/Gemini/Non-Claude Hosts

```bash
# Repo-local for Codex
git clone ... .agents/skills/gstack
cd .agents/skills/gstack && ./setup --host codex

# User-global for Codex
git clone ... ~/gstack
cd ~/gstack && ./setup --host codex

# Auto-detect installed agents
./setup --host auto
```

On non-Claude hosts, hook-based safety skills (`careful`, `freeze`, `guard`) use inline safety advisory prose instead of Claude Code hooks.

---

## Conductor Pattern vs. Direct CLI Invocation

### Direct CLI Invocation (without Conductor)

Without Conductor, you run a single Claude Code session. You can still use all gstack skills, but work is sequential:
- One task at a time
- Context switches between build/review/test modes
- Single browser instance

### Conductor Pattern

With Conductor:
- Multiple Claude Code sessions run in parallel in isolated workspaces
- Each session is assigned exactly one cognitive mode: Builder / Reviewer / QA / Planner
- Sessions do not share state; isolation is enforced at the process level
- You act as an orchestrator (director) rather than a single-threaded executor

### Cognitive Mode Specialization

The key insight is that each mode produces better results when isolated:

| Mode | Characteristics | Primary Skills |
|---|---|---|
| Builder | Creative, iterative, implementation-focused | Code editing, `/browse` for local testing |
| Reviewer | Critical, analytical, bug-finding | `/review`, `/codex` |
| QA | Adversarial, edge-case focused | `/qa`, `/browse` |
| Planner | Strategic, architecture-focused | `/office-hours`, `/plan-*` |

### Practical Parallel Patterns

**Three-agent sprint (most common):**
- Agent 1 (Builder): implementing feature
- Agent 2 (Reviewer): reviewing open PR
- Agent 3 (QA): testing staging deployment

**Feature + Live QA:**
- Builder agent implements, tests locally with `/browse`
- QA agent simultaneously runs regression on staging — browser instances do not interfere

**Multi-service testing:**
- One agent per service, each browser pointed at a different URL

### ELI16 Mode (Context Management at Scale)

When 3+ sessions are active, every question re-grounds the context. The AI re-establishes what each session is working on before presenting new information — reduces cognitive overhead of managing many parallel workspaces.

---

## CLI Failure Handling Techniques

### Browser Daemon Failures

- Browser daemon checks `.gstack/browse.json` to determine if existing daemon is running
- Random port selection with 5 retries on collision
- Auto-shutdown after 30 idle minutes
- macOS Gatekeeper quarantine fix: `xattr -d com.apple.quarantine ~/.claude/skills/gstack/browse/browse`

### Session Failures / Auth Walls

- CAPTCHA/auth wall hit: `$B handoff` opens headed Chrome at same page with cookies intact
- Human solves problem; `$B resume` picks up where left off
- Auto-suggested after 3 consecutive failures

### /investigate Auto-Freeze

The `/investigate` skill auto-activates `/freeze` (directory edit lock) to prevent Claude from accidentally "fixing" unrelated code while debugging.

### Shell Escaping / Prompt Passing

No documented shell escaping patterns. gstack skills are Markdown prompt files (SKILL.md standard). The skills are passed as-is to the Claude Code runtime — escaping is handled by the SKILL.md runtime, not by conductor.

---

## Key Technical Observations

1. **Conductor is external** — gstack documents it but does not ship it. The `conductor.build` product manages workspace creation; gstack provides the skill layer.

2. **No message bus** — Agents communicate only via shared file artifacts (design docs, test plans). There is no runtime IPC between sessions.

3. **SKILL.md standard** — Skills are Markdown files with a defined format. Compatible with multiple agent hosts (Claude Code, Codex, Gemini, Factory Droid). Portability is by design.

4. **Browser binary is local** — The `/browse` skill compiles a ~58MB native Chromium binary locally using Bun. Not downloaded as a pre-built binary — avoids Gatekeeper issues.

5. **Project-level skill precedence** — `.claude/skills/gstack/` (project) overrides `~/.claude/skills/gstack/` (global). Teams can pin versions in repo.

6. **No submodules** — gstack is committed as real files (not a git submodule). Intentional: simplifies `git clone` workflow.

7. **Practical parallel limit** — Garry Tan reports 10–15 parallel sprints as practical max. Each Chromium instance uses 150–300 MB RAM; 16 GB machine comfortable with 3–5, 32 GB+ with 8–10.

---

## Gaps and Unknowns

- **Conductor internals** — How Conductor creates worktrees and manages Claude Code process lifecycle is not documented in gstack sources. Requires separate research at `conductor.build`.
- **SKILL.md format spec** — The full SKILL.md standard (format, required fields, context-matching rules) is referenced but not fully specified in these sources.
- **Inter-session coordination** — How (if at all) agent results flow between sessions is unclear. Artifact-based (files) is confirmed, but no polling/event mechanism is documented.
- **Codex/Gemini skill generation** — `./setup --host codex` generates Codex-compatible skills; the transformation from SKILL.md to Codex format is not documented here.
- **Factory Droid `disable-model-invocation: true`** — The meaning and mechanism of this flag for sensitive skills is undocumented.

---

## Source Catalog Entries

| URL | Classification | Notes |
|---|---|---|
| https://gstacks.org/gstack-setup-install-guide.html | HIGH | Install guide, setup steps, architecture overview |
| https://github.com/garrytan/gstack | HIGH | Primary repo, README, full skill catalog |
| https://gstacks.org/gstack-parallel-ai-coding.html | HIGH | Conductor architecture, isolation mechanisms, parallel patterns |
| https://conductor.build | HIGH (unfetched) | Conductor workspace orchestrator — separate product |
| https://bun.sh | MEDIUM | Runtime dependency for /browse binary compilation |
