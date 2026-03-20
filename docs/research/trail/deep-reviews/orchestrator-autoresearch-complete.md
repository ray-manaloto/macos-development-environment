# Deep Review: ComposioHQ/agent-orchestrator and karpathy/autoresearch

Date: 2026-03-20
Sources fetched: GitHub READMEs, program.md, prepare.py, train.py, types.ts, lifecycle-manager.ts,
workspace-worktree plugin, feedback-routing-and-followup-design.md, agent-orchestrator.yaml.example,
CLI.md, DEVELOPMENT.md, pyproject.toml

---

## Part 1: ComposioHQ/agent-orchestrator

Repository: https://github.com/ComposioHQ/agent-orchestrator
License: MIT
Package: `@composio/ao` (npm)
Tag line: "Agentic orchestrator for parallel coding agents -- plans tasks, spawns agents, and
autonomously handles CI fixes, merge conflicts, and code reviews."

### 1.1 Architecture Overview

Monorepo with four main packages:

```
packages/
  core/          -- Types, services, config (the engine)
  cli/           -- `ao` command (depends on core + all plugins)
  web/           -- Next.js dashboard (depends on core)
  plugins/       -- 21 plugin packages across 8 slots
```

Build order: core must be built before cli, web, or plugins.
Build system: pnpm monorepo, ESM-only with `.js` extensions on local imports.
Test suite: 3,288 test cases, vitest.
Dashboard: Next.js at http://localhost:3000

### 1.2 The 8 Plugin Slots (Complete Reference)

Every abstraction is swappable. All interfaces defined in `packages/core/src/types.ts`.

| Slot       | Interface    | Default        | Alternatives                          |
|------------|-------------|----------------|---------------------------------------|
| Runtime    | `Runtime`    | tmux           | process, docker, k8s, ssh, e2b       |
| Agent      | `Agent`      | claude-code    | codex, aider, opencode                |
| Workspace  | `Workspace`  | worktree       | clone                                 |
| Tracker    | `Tracker`    | github         | linear                                |
| SCM        | `SCM`        | github         | (gitlab planned)                      |
| Notifier   | `Notifier`   | desktop        | slack, composio, webhook              |
| Terminal   | `Terminal`   | iterm2         | web                                   |
| Lifecycle  | (core)       | core           | Non-pluggable                         |

#### 1.2.1 Runtime Interface

```typescript
interface Runtime {
  readonly name: string;
  create(config: RuntimeCreateConfig): Promise<RuntimeHandle>;
  destroy(handle: RuntimeHandle): Promise<void>;
  sendMessage(handle: RuntimeHandle, message: string): Promise<void>;
  getOutput(handle: RuntimeHandle, lines?: number): Promise<string>;
  isAlive(handle: RuntimeHandle): Promise<boolean>;
  getMetrics?(handle: RuntimeHandle): Promise<RuntimeMetrics>;
  getAttachInfo?(handle: RuntimeHandle): Promise<AttachInfo>;
}
```

RuntimeHandle is an opaque handle with `id`, `runtimeName`, and `data: Record<string, unknown>`.
AttachInfo types: `"tmux" | "docker" | "ssh" | "web" | "process"`.

#### 1.2.2 Agent Interface

```typescript
interface Agent {
  readonly name: string;
  readonly processName: string;  // e.g. "claude", "codex", "aider"
  readonly promptDelivery?: "inline" | "post-launch";
  getLaunchCommand(config: AgentLaunchConfig): string;
  getEnvironment(config: AgentLaunchConfig): Record<string, string>;
  detectActivity(terminalOutput: string): ActivityState;  // deprecated
  getActivityState(session: Session, readyThresholdMs?: number): Promise<ActivityDetection | null>;
  isProcessRunning(handle: RuntimeHandle): Promise<boolean>;
  getSessionInfo(session: Session): Promise<AgentSessionInfo | null>;
  getRestoreCommand?(session: Session, project: ProjectConfig): Promise<string | null>;
  postLaunchSetup?(session: Session): Promise<void>;
  setupWorkspaceHooks?(workspacePath: string, config: WorkspaceHooksConfig): Promise<void>;
}
```

`promptDelivery`:
- `"inline"` (default): prompt included in launch command (e.g. -p flag)
- `"post-launch"`: prompt sent via runtime.sendMessage() after agent starts

`AgentSessionInfo` includes: `summary`, `summaryIsFallback`, `agentSessionId`, and optional
`CostEstimate` (`inputTokens`, `outputTokens`, `estimatedCostUsd`).

#### 1.2.3 Workspace Interface

```typescript
interface Workspace {
  readonly name: string;
  create(config: WorkspaceCreateConfig): Promise<WorkspaceInfo>;
  destroy(workspacePath: string): Promise<void>;
  list(projectId: string): Promise<WorkspaceInfo[]>;
  postCreate?(info: WorkspaceInfo, project: ProjectConfig): Promise<void>;
  exists?(workspacePath: string): Promise<boolean>;
  restore?(config: WorkspaceCreateConfig, workspacePath: string): Promise<WorkspaceInfo>;
}
```

#### 1.2.4 Tracker Interface

```typescript
interface Tracker {
  readonly name: string;
  getIssue(identifier: string, project: ProjectConfig): Promise<Issue>;
  isCompleted(identifier: string, project: ProjectConfig): Promise<boolean>;
  issueUrl(identifier: string, project: ProjectConfig): string;
  issueLabel?(url: string, project: ProjectConfig): string;
  branchName(identifier: string, project: ProjectConfig): string;
  generatePrompt(identifier: string, project: ProjectConfig): Promise<string>;
  listIssues?(filters: IssueFilters, project: ProjectConfig): Promise<Issue[]>;
  updateIssue?(identifier: string, update: IssueUpdate, project: ProjectConfig): Promise<void>;
  createIssue?(input: CreateIssueInput, project: ProjectConfig): Promise<Issue>;
}
```

#### 1.2.5 SCM Interface (Richest Plugin Interface)

```typescript
interface SCM {
  readonly name: string;
  verifyWebhook?(request, project): Promise<SCMWebhookVerificationResult>;
  parseWebhook?(request, project): Promise<SCMWebhookEvent | null>;
  detectPR(session, project): Promise<PRInfo | null>;
  resolvePR?(reference, project): Promise<PRInfo>;
  assignPRToCurrentUser?(pr): Promise<void>;
  checkoutPR?(pr, workspacePath): Promise<boolean>;
  getPRState(pr): Promise<PRState>;
  getPRSummary?(pr): Promise<{ state, title, additions, deletions }>;
  mergePR(pr, method?): Promise<void>;
  closePR(pr): Promise<void>;
  getCIChecks(pr): Promise<CICheck[]>;
  getCISummary(pr): Promise<CIStatus>;
  getReviews(pr): Promise<Review[]>;
  getReviewDecision(pr): Promise<ReviewDecision>;
  getPendingComments(pr): Promise<ReviewComment[]>;
  getAutomatedComments(pr): Promise<AutomatedComment[]>;
  getMergeability(pr): Promise<MergeReadiness>;
}
```

MergeReadiness: `{ mergeable, ciPassing, approved, noConflicts, blockers: string[] }`.
CICheck statuses: `"pending" | "running" | "passed" | "failed" | "skipped"`.
ReviewDecision: `"approved" | "changes_requested" | "pending" | "none"`.

#### 1.2.6 Notifier Interface

```typescript
interface Notifier {
  readonly name: string;
  notify(event: OrchestratorEvent): Promise<void>;
  notifyWithActions?(event: OrchestratorEvent, actions: NotifyAction[]): Promise<void>;
  post?(message: string, context?: NotifyContext): Promise<string | null>;
}
```

The notifier is described as "the PRIMARY interface between the orchestrator and the human.
Push, not pull. The human never polls."

#### 1.2.7 Terminal Interface

```typescript
interface Terminal {
  readonly name: string;
  openSession(session: Session): Promise<void>;
  openAll(sessions: Session[]): Promise<void>;
  isSessionOpen?(session: Session): Promise<boolean>;
}
```

#### 1.2.8 Plugin Module Contract

```typescript
interface PluginModule<T = unknown> {
  manifest: PluginManifest;
  create(config?: Record<string, unknown>): T;
  detect?(): boolean;  // detect if plugin's runtime/binary is available
}
```

### 1.3 Session Lifecycle State Machine

#### 1.3.1 Session Status (17 states)

```typescript
type SessionStatus =
  | "spawning"
  | "working"
  | "pr_open"
  | "ci_failed"
  | "review_pending"
  | "changes_requested"
  | "approved"
  | "mergeable"
  | "merged"
  | "cleanup"
  | "needs_input"
  | "stuck"
  | "errored"
  | "killed"
  | "idle"
  | "done"
  | "terminated";
```

Terminal (dead) states: `killed`, `terminated`, `done`, `cleanup`, `errored`, `merged`.
Non-restorable states: `merged` (only).

#### 1.3.2 State Transition Diagram

```
spawning --> working --> pr_open --> ci_failed       (CI fails)
                                --> review_pending   (PR opened, awaiting review)
                                    --> changes_requested  (reviewer requests changes)
                                    --> approved --> mergeable --> merged
                                                              --> cleanup --> done
                     (no PR path)
                     --> stuck      (idle beyond threshold)
                     --> needs_input (agent asking question)
                     --> killed     (process died or PR closed)
                     --> errored
```

#### 1.3.3 Activity Detection (6 states, orthogonal to lifecycle)

```typescript
type ActivityState =
  | "active"         // agent is processing (thinking, writing code)
  | "ready"          // agent finished its turn, alive and waiting for input
  | "idle"           // agent has been inactive for a while (stale)
  | "waiting_input"  // agent is asking a question / permission prompt
  | "blocked"        // agent hit an error or is stuck
  | "exited";        // agent process is no longer running
```

Default ready-to-idle threshold: 300,000 ms (5 minutes).

Detection priority:
1. JSONL-based activity detection (reads agent's session files directly) -- preferred
2. Terminal output parsing (deprecated fallback)

### 1.4 Lifecycle Manager (Polling + Reaction Engine)

Source: `packages/core/src/lifecycle-manager.ts` (922 lines)

#### 1.4.1 Polling Architecture

- Default poll interval: 30 seconds (`start(intervalMs = 30_000)`)
- Re-entrancy guard prevents overlapping polls
- All sessions polled concurrently via `Promise.allSettled`
- Prunes stale entries from tracked state and reaction trackers

#### 1.4.2 Status Determination Algorithm (per session per poll)

```
Step 1: Check if runtime is alive
        - If not alive: return "killed"

Step 2: Check agent activity (prefer JSONL-based, fallback to terminal parsing)
        - If waiting_input: return "needs_input"
        - If exited: return "killed"
        - If idle/blocked: record timestamp for stuck detection later
        - Otherwise (active/ready): proceed

Step 3: Auto-detect PR by branch name if PR metadata is missing
        - Skips orchestrator sessions
        - Uses SCM.detectPR()
        - Persists PR URL to metadata

Step 4: If PR exists, check PR state via SCM
        - Merged: return "merged"
        - Closed: return "killed"
        - CI failing: return "ci_failed"
        - Changes requested: return "changes_requested"
        - Approved/none + mergeable: return "mergeable"
        - Approved: return "approved"
        - Pending review: return "review_pending"
        - Idle beyond threshold: return "stuck"
        - Otherwise: return "pr_open"

Step 5: No PR -- check stuck threshold on idle detection from step 2

Step 6: Default fallback
        - If spawning/stuck/needs_input: return "working"
        - Otherwise: keep current status
```

#### 1.4.3 Reaction Engine

Reactions are configured in YAML. Each reaction maps an event to an action.

**Event-to-Reaction Key Mapping:**

| Event Type                  | Reaction Key       |
|----------------------------|--------------------|
| `ci.failing`               | `ci-failed`        |
| `review.changes_requested` | `changes-requested`|
| `automated_review.found`   | `bugbot-comments`  |
| `merge.conflicts`          | `merge-conflicts`  |
| `merge.ready`              | `approved-and-green`|
| `session.stuck`            | `agent-stuck`      |
| `session.needs_input`      | `agent-needs-input`|
| `session.killed`           | `agent-exited`     |
| `summary.all_complete`     | `all-complete`     |

**Reaction Config Schema:**

```typescript
interface ReactionConfig {
  auto: boolean;                    // whether this reaction is enabled
  action: "send-to-agent" | "notify" | "auto-merge";
  message?: string;                 // for send-to-agent
  priority?: EventPriority;         // for notifications
  retries?: number;                 // max retries before escalating
  escalateAfter?: number | string;  // escalation threshold (count or duration like "30m")
  threshold?: string;               // time-based trigger (e.g. "10m" for stuck detection)
  includeSummary?: boolean;
}
```

**Default Reaction Config (from YAML example):**

```yaml
reactions:
  ci-failed:
    auto: true
    action: send-to-agent
    retries: 2
    escalateAfter: 2          # escalate after 2 failed retry attempts
  changes-requested:
    auto: true
    action: send-to-agent
    escalateAfter: 30m         # escalate after 30 minutes
  approved-and-green:
    auto: false                # set to true for auto-merge
    action: notify
    priority: action
  agent-stuck:
    threshold: 10m             # detect after 10 minutes idle
    action: notify
    priority: urgent
```

#### 1.4.4 Escalation Mechanism

The `executeReaction()` function tracks attempts per session per reaction key via a `ReactionTracker`:

```typescript
interface ReactionTracker {
  attempts: number;
  firstTriggered: Date;
}
```

Escalation triggers when ANY of:
1. `tracker.attempts > maxRetries` (count-based)
2. `escalateAfter` is a duration string AND elapsed time exceeds it
3. `escalateAfter` is a number AND attempts exceed it

On escalation: emits `"reaction.escalated"` event and notifies human with `"urgent"` priority.

#### 1.4.5 Review Comment Fingerprinting (Deduplication)

The lifecycle manager tracks review comments via fingerprints to avoid dispatching the same
comments repeatedly:

```
fingerprint = sort(comment_ids).join(",")
```

Two parallel tracking systems:
1. **Human review comments** (via `getPendingComments`):
   - Metadata keys: `lastPendingReviewFingerprint`, `lastPendingReviewDispatchHash`, `lastPendingReviewDispatchAt`
   - Reaction key: `changes-requested`

2. **Automated review comments** (via `getAutomatedComments`):
   - Metadata keys: `lastAutomatedReviewFingerprint`, `lastAutomatedReviewDispatchHash`, `lastAutomatedReviewDispatchAt`
   - Reaction key: `bugbot-comments`

Logic:
- If fingerprint changes: clear reaction tracker (reset retry count), update fingerprint
- If fingerprint matches previous dispatch hash: skip (already handled)
- If fingerprint differs from dispatch hash: execute reaction, record dispatch hash + timestamp
- On merge/kill: clear all fingerprints and trackers

### 1.5 Worktree Plugin (workspace-worktree)

Source: `packages/plugins/workspace-worktree/src/index.ts`

#### 1.5.1 Directory Structure

```
~/.worktrees/               # worktreeBaseDir (configurable via worktreeDir)
  {projectId}/
    {sessionId}/            # one worktree per session
```

#### 1.5.2 Path Safety

- Path segments validated with: `/^[a-zA-Z0-9_-]+$/`
- `assertSafePathSegment()` called for both projectId and sessionId
- Prevents directory traversal via regex enforcement

#### 1.5.3 Branch Creation

```
create(cfg):
  1. git fetch origin --quiet (in main repo; tolerates offline)
  2. git worktree add -b {branch} {worktreePath} origin/{defaultBranch}
     - On "branch already exists" error:
       a. git worktree add {worktreePath} origin/{defaultBranch}
       b. git checkout {branch} (in worktree)
       c. On checkout failure: git worktree remove --force (cleanup)
```

#### 1.5.4 Symlink Support

In `postCreate()`:
- Iterates `project.symlinks` array (relative paths only)
- Validates: no absolute paths, no ".." segments
- Verifies resolved target stays within workspace (traversal prevention)
- Creates parent directories if needed
- Removes existing target before creating symlink

#### 1.5.5 Cleanup / Destroy

```
destroy(workspacePath):
  1. git rev-parse --git-common-dir (find main repo from worktree)
  2. git worktree remove --force {workspacePath}
  3. Does NOT delete the branch (intentional -- prevents deleting unrelated branches)
  4. Fallback: if git fails, rmSync(workspacePath, { recursive: true })
```

#### 1.5.6 Restore

```
restore(cfg, workspacePath):
  1. git worktree prune (clean stale entries)
  2. git fetch origin --quiet
  3. Try: git worktree add {path} {branch}
  4. Fallback: git worktree add -b {branch} {path} origin/{branch}
  5. Last resort: git worktree add -b {branch} {path} origin/{defaultBranch}
```

### 1.6 Event System (Complete Reference)

#### 1.6.1 Event Types (28 total)

```typescript
type EventType =
  // Session lifecycle (8)
  | "session.spawned" | "session.working" | "session.exited"
  | "session.killed" | "session.idle" | "session.stuck"
  | "session.needs_input" | "session.errored"
  // PR lifecycle (4)
  | "pr.created" | "pr.updated" | "pr.merged" | "pr.closed"
  // CI (4)
  | "ci.passing" | "ci.failing" | "ci.fix_sent" | "ci.fix_failed"
  // Reviews (5)
  | "review.pending" | "review.approved" | "review.changes_requested"
  | "review.comments_sent" | "review.comments_unresolved"
  // Automated reviews (2)
  | "automated_review.found" | "automated_review.fix_sent"
  // Merge (3)
  | "merge.ready" | "merge.conflicts" | "merge.completed"
  // Reactions (2)
  | "reaction.triggered" | "reaction.escalated"
  // Summary (1)
  | "summary.all_complete";
```

#### 1.6.2 Priority Inference

```
urgent: stuck, needs_input, errored
action: approved, ready, merged, completed
warning: fail, changes_requested, conflicts
info: summary.*, everything else
```

#### 1.6.3 Notification Routing

```yaml
notificationRouting:
  urgent: [desktop, slack]   # agent stuck, needs input, errored
  action: [desktop, slack]   # PR ready to merge
  warning: [slack]           # auto-fix failed
  info: [slack]              # summary, all done
```

### 1.7 Feedback Routing Design (from design doc)

Source: `docs/design/feedback-routing-and-followup-design.md`

#### 1.7.1 Feedback Pipeline (5 stages)

```
1. Report capture -> validate payload, compute dedupe key
2. Issue resolution -> find existing issue by markers; create or comment/update
3. Follow-up planning -> decide: issue-only vs issue+PR vs issue+fork
4. Execution -> SCM action path OR agent-session path
5. Linking and journal update -> persist outcome state and references
```

#### 1.7.2 Feedback Tools

Two tool types with confidence scores:
- `bug_report` -- minimum confidence: 0.6
- `improvement_suggestion` -- minimum confidence: 0.75

#### 1.7.3 Follow-up Decision Matrix

| Condition                                        | Action           |
|-------------------------------------------------|-----------------|
| `self_blocking_now = false`                      | issue-only      |
| `self_blocking_now = true` + ready branch/commits| issue + PR      |
| `self_blocking_now = true` + no writable upstream| issue + fork    |
| `self_blocking_now = true` + no code yet         | spawn agent-session |

#### 1.7.4 Dedupe Markers (HTML comments in issue/PR body)

```html
<!-- ao:feedback-tool:<tool> -->
<!-- ao:dedupe-key:<dedupeKey> -->
<!-- ao:session:<sessionId> -->
```

#### 1.7.5 Idempotency

- `dedupeKey` for issue-level identity
- `operationKey` for each side effect (create issue, create fork, create PR, add comment)
- All mutations are "find-or-create" operations
- Exponential backoff with bounded attempts for retryable failures

#### 1.7.6 Journal Schema

```json
{
  "reportId": "fr_01HT2H2F3H4A5",
  "dedupeKey": "f4d7dbe5b0f8...",
  "mode": "scm",
  "stage": "create_pr",
  "status": "failed",
  "attempt": 2,
  "operationKey": "create_pr:f4d7dbe5b0f8:upstream",
  "targetRepo": "ComposioHQ/agent-orchestrator",
  "issueUrl": "https://github.com/ComposioHQ/agent-orchestrator/issues/399",
  "prUrl": null,
  "consent": {
    "createFork": "approved",
    "createPR": "approved",
    "switchTarget": "not-needed"
  },
  "lastError": {
    "code": "FORBIDDEN",
    "message": "PR creation blocked by repository policy"
  },
  "updatedAt": "2026-03-10T15:45:00Z"
}
```

#### 1.7.7 Consent Gates (Default Policy)

Hard defaults for non-dogfooding projects:
1. Human consent required before creating a fork
2. Human consent required before creating a PR
3. Human consent required before switching execution target
4. No silent infrastructure flip

Override requires: explicit project-owner enablement, scoped per operation
(`createFork`, `createPR`, `switchTarget`), and must be auditable.

#### 1.7.8 Governance Hooks

```
canCreateIssue(project, actor, targetRepo)
canCreateFork(project, actor, forkOwner)
canCreatePR(project, actor, targetRepo, sourceRepo)
canSpawnSession(project, actor, followUpIntent)
```

#### 1.7.9 Proposed Components

1. `FeedbackRouter`: local vs scm dispatch
2. `IssueResolver`: dedupe-aware issue create/update/comment
3. `FollowUpPlanner`: issue-only vs issue+PR vs issue+fork decision
4. `TargetResolver`: upstream/fork target determination
5. `FollowUpExecutor`: direct SCM or agent-session execution path
6. `FeedbackPublishJournal`: status, links, retries, recovery metadata

### 1.8 Configuration Schema

#### 1.8.1 Top-Level Config (`agent-orchestrator.yaml`)

```typescript
interface OrchestratorConfig {
  configPath: string;           // auto-set during load
  port?: number;                // default: 3000
  terminalPort?: number;        // default: 3001
  directTerminalPort?: number;  // default: 3003
  readyThresholdMs: number;     // default: 300000 (5 min)
  defaults: DefaultPlugins;
  projects: Record<string, ProjectConfig>;
  notifiers: Record<string, NotifierConfig>;
  notificationRouting: Record<EventPriority, string[]>;
  reactions: Record<string, ReactionConfig>;
}
```

#### 1.8.2 Project Config

```typescript
interface ProjectConfig {
  name: string;
  repo: string;                // "owner/repo" format
  path: string;                // local path
  defaultBranch: string;
  sessionPrefix: string;
  runtime?: string;
  agent?: string;
  workspace?: string;
  tracker?: TrackerConfig;
  scm?: SCMConfig;
  symlinks?: string[];
  postCreate?: string[];
  agentConfig?: AgentSpecificConfig;
  orchestrator?: RoleAgentConfig;
  worker?: RoleAgentConfig;
  reactions?: Record<string, Partial<ReactionConfig>>;
  agentRules?: string;          // inline rules for every agent prompt
  agentRulesFile?: string;      // path to rules file (relative to project)
  orchestratorRules?: string;
  orchestratorSessionStrategy?: "reuse" | "delete" | "ignore" | "delete-new" | "ignore-new" | "kill-previous";
  decomposer?: {
    enabled: boolean;
    maxDepth: number;          // default: 3
    model: string;             // default: "claude-sonnet-4-20250514"
    requireApproval: boolean;  // default: true
  };
}
```

#### 1.8.3 Agent Permission Modes

```typescript
type AgentPermissionMode = "permissionless" | "default" | "auto-edit" | "suggest";
```

- `permissionless`: no interactive prompts (most permissive)
- `default`: agent's normal permission model
- `auto-edit`: auto-approve edits where supported
- `suggest`: conservative, asks approval for high-risk actions
- Legacy alias: `"skip"` maps to `"permissionless"`

### 1.9 Hash-Based Namespacing

All runtime data paths derived from SHA-256 of config file directory:

```
hash = sha256(dirname(configPath)).slice(0, 12)  // e.g. "a3b4c5d6e7f8"
instanceId = `${hash}-${projectId}`
dataDir = `~/.agent-orchestrator/${instanceId}`
tmuxSessionName = `${hash}-${prefix}-${num}`       // globally unique
userFacingName = `${prefix}-${num}`                // clean display name
```

### 1.10 Spawn Flow

```
spawn(config)
  1. Validate issue (Tracker.getIssue) -- fails fast, no resources created
  2. Reserve session ID
  3. Determine branch name
  4. Create workspace (Workspace.create)
  5. Generate issue prompt (Tracker.generatePrompt)
  6. Build agent launch command (Agent.getLaunchCommand)
  7. Assemble full prompt (prompt-builder.ts -- 3 layers)
  8. Create runtime session (Runtime.create)
  9. Post-launch setup (Agent.postLaunchSetup, optional)
 10. Write metadata file
```

### 1.11 Prompt Assembly (3 layers)

1. Base agent guidance -- standard instructions for all sessions
2. Config context -- project-specific info, agent rules from `agentRules` / `agentRulesFile`
3. User rules -- inlined last, highest priority

Orchestrator sessions use a separate prompt from `orchestrator-prompt.ts`.

### 1.12 Session Metadata (Flat File Format)

```typescript
interface SessionMetadata {
  worktree: string;
  branch: string;
  status: string;
  tmuxName?: string;
  issue?: string;
  pr?: string;
  prAutoDetect?: "on" | "off";
  summary?: string;
  project?: string;
  agent?: string;
  createdAt?: string;
  runtimeHandle?: string;
  restoredAt?: string;
  role?: string;               // "orchestrator" for orchestrator sessions
  dashboardPort?: number;
  terminalWsPort?: number;
  directTerminalWsPort?: number;
  opencodeSessionId?: string;
}
```

Stored as flat key=value files at `~/.agent-orchestrator/{hash}-{project}/sessions/{session-id}`.
Design decision: flat files over database for debuggability, crash survival, no schema migration.

### 1.13 CLI Reference

**Human commands:**
```
ao start                        # Auto-detect, generate config, start dashboard + orchestrator
ao start <url>                  # Clone repo, auto-configure, and start
ao start ~/other-repo           # Add a new project and start
ao stop                         # Stop everything
ao status                       # Overview of all sessions
ao dashboard                    # Open web dashboard
ao doctor                       # Check install, runtime, stale temp issues
ao doctor --fix                 # Apply safe fixes
ao update                       # Update local AO install
ao config-help                  # Show full config schema reference
```

**Orchestrator agent commands:**
```
ao spawn [issue]                # Spawn an agent
ao spawn 123 --agent codex      # Override agent for this session
ao batch-spawn 101 102 103      # Spawn agents for multiple issues
ao send <session> "message"     # Send instructions to running agent
ao session ls                   # List sessions
ao session kill <session>       # Kill a session
ao session restore <session>    # Revive a crashed agent
```

### 1.14 Key Design Decisions

1. **Flat metadata files over database** -- debuggable via `cat`, no setup, survives crashes
2. **Polling over webhooks** -- simpler local setup, survives restarts, works offline
3. **Plugin slots** -- swappable runtimes/agents/trackers without forking
4. **Hash-based namespacing** -- multiple orchestrator checkouts never collide
5. **ESM with .js extensions** -- Node.js ESM compliance, explicit import resolution

---

## Part 2: karpathy/autoresearch

Repository: https://github.com/karpathy/autoresearch
License: MIT
Tag line: "AI agents running research on single-GPU nanochat training automatically"

### 2.1 Complete File Structure

```
autoresearch/
  prepare.py       -- fixed constants, data prep, tokenizer, dataloader, evaluation (DO NOT MODIFY)
  train.py         -- model, optimizer, training loop (AGENT MODIFIES THIS)
  program.md       -- agent instructions (HUMAN MODIFIES THIS)
  pyproject.toml   -- dependencies
  progress.png     -- progress chart
  README.md        -- documentation
```

Only three files matter. Deliberately minimal.

### 2.2 Dependencies (pyproject.toml)

```toml
[project]
name = "autoresearch"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "kernels>=0.11.7",
    "matplotlib>=3.10.8",
    "numpy>=2.2.6",
    "pandas>=2.3.3",
    "pyarrow>=21.0.0",
    "requests>=2.32.0",
    "rustbpe>=0.1.0",
    "tiktoken>=0.11.0",
    "torch==2.9.1",
]
```

Torch pinned to 2.9.1 with CUDA 12.8 index. No new packages can be added by the agent.

### 2.3 Constants (from prepare.py)

```python
MAX_SEQ_LEN = 2048       # context length
TIME_BUDGET = 300        # training time budget in seconds (5 minutes)
EVAL_TOKENS = 40 * 524288  # = 20,971,520 tokens for val eval
VOCAB_SIZE = 8192
CACHE_DIR = ~/.cache/autoresearch/
DATA_DIR = ~/.cache/autoresearch/data/
TOKENIZER_DIR = ~/.cache/autoresearch/tokenizer/
MAX_SHARD = 6542
VAL_SHARD = 6542         # pinned validation shard (shard_06542.parquet)
```

Data source: `huggingface.co/datasets/karpathy/climbmix-400b-shuffle`
Tokenizer: BPE via `rustbpe` with GPT-4-style split pattern, saved as tiktoken-compatible format.

### 2.4 The evaluate_bpb() Function (Exact Algorithm)

```python
@torch.no_grad()
def evaluate_bpb(model, tokenizer, batch_size):
    """
    Bits per byte (BPB): vocab size-independent evaluation metric.
    """
    token_bytes = get_token_bytes(device="cuda")      # int32 tensor: token_id -> byte count
    val_loader = make_dataloader(tokenizer, batch_size, MAX_SEQ_LEN, "val")
    steps = EVAL_TOKENS // (batch_size * MAX_SEQ_LEN)  # fixed number of eval steps
    total_nats = 0.0
    total_bytes = 0

    for _ in range(steps):
        x, y, _ = next(val_loader)                    # input, target, epoch
        loss_flat = model(x, y, reduction='none').view(-1)  # per-token CE in nats
        y_flat = y.view(-1)
        nbytes = token_bytes[y_flat]                  # byte length of each target token
        mask = nbytes > 0                             # exclude special tokens (0 bytes)
        total_nats += (loss_flat * mask).sum().item()  # sum masked nats
        total_bytes += nbytes.sum().item()             # sum masked bytes

    return total_nats / (math.log(2) * total_bytes)   # convert nats/byte -> bits/byte
```

Key properties:
- Vocab-size-independent (measures bits per byte, not per token)
- Special tokens excluded from both numerator and denominator
- Fixed MAX_SEQ_LEN ensures comparability across architecture changes
- Fixed EVAL_TOKENS ensures consistent eval budget
- Lower is better

### 2.5 Dataloader (Best-Fit Packing)

```python
make_dataloader(tokenizer, B, T, split, buffer_size=1000)
```

- BOS-aligned: every row starts with BOS token
- Best-fit packing: documents packed to minimize cropping
  - Find largest document that fits remaining space
  - If none fits: crop shortest document to fill exactly
- 100% utilization (no padding)
- Infinite iterator with epoch tracking
- Pre-allocated pinned CPU and GPU buffers for async transfer

### 2.6 program.md (Complete Agent Instructions)

This is the actual prompt/skill that drives the autonomous agent. Key sections:

#### 2.6.1 Setup Protocol

1. Agree on a run tag (e.g. `mar5`)
2. Create branch: `git checkout -b autoresearch/<tag>`
3. Read in-scope files: README.md, prepare.py, train.py
4. Verify data exists at `~/.cache/autoresearch/`
5. Initialize `results.tsv` with header row
6. Confirm and begin

#### 2.6.2 Constraints

**CAN do:**
- Modify `train.py` -- everything is fair game: architecture, optimizer, hyperparams, batch size,
  model size, training loop

**CANNOT do:**
- Modify `prepare.py` (read-only, contains fixed evaluation)
- Install new packages
- Modify the evaluation harness

#### 2.6.3 Simplicity Criterion

Quoted verbatim:
> All else being equal, simpler is better. A small improvement that adds ugly complexity is not
> worth it. Conversely, removing something and getting equal or better results is a great outcome
> -- that's a simplification win. When evaluating whether to keep a change, weigh the complexity
> cost against the improvement magnitude. A 0.001 val_bpb improvement that adds 20 lines of
> hacky code? Probably not worth it. A 0.001 val_bpb improvement from deleting code? Definitely
> keep. An improvement of ~0 but much simpler code? Keep.

#### 2.6.4 Output Format

The training script prints a summary block:

```
---
val_bpb:          0.997900
training_seconds: 300.1
total_seconds:    325.9
peak_vram_mb:     45060.2
mfu_percent:      39.80
total_tokens_M:   499.6
num_steps:        953
num_params_M:     50.3
depth:            8
```

Agent extracts key metric: `grep "^val_bpb:" run.log`

### 2.7 results.tsv Schema

Tab-separated (NOT comma-separated). 5 columns:

```
commit	val_bpb	memory_gb	status	description
```

| Column      | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| commit      | string | Short git hash (7 chars)                       |
| val_bpb     | float  | Validation bits per byte (0.000000 for crashes)|
| memory_gb   | float  | Peak VRAM in GB, 1 decimal (0.0 for crashes)  |
| status      | enum   | `keep`, `discard`, or `crash`                  |
| description | string | Short text of what the experiment tried         |

Example:
```
commit	val_bpb	memory_gb	status	description
a1b2c3d	0.997900	44.0	keep	baseline
b2c3d4e	0.993200	44.2	keep	increase LR to 0.04
c3d4e5f	1.005000	44.0	discard	switch to GeLU activation
d4e5f6g	0.000000	0.0	crash	double model width (OOM)
```

Note: results.tsv is NOT committed to git (left untracked).

### 2.8 The Experiment Loop (Complete Protocol)

```
LOOP FOREVER:
  1. Look at git state: current branch/commit
  2. Edit train.py with an experimental idea
  3. git commit
  4. Run: uv run train.py > run.log 2>&1     (redirect all output, NO tee)
  5. Read results: grep "^val_bpb:\|^peak_vram_mb:" run.log
  6. If grep empty -> crash:
     - tail -n 50 run.log for stack trace
     - Attempt fix (few tries), else give up
  7. Record in results.tsv
  8. If val_bpb improved (lower): advance branch (keep commit)
  9. If val_bpb equal or worse: git reset to previous state
```

#### 2.8.1 Git Branching Strategy

- Dedicated branch per run: `autoresearch/<tag>` (e.g. `autoresearch/mar5`)
- Branch created from current master
- On improvement: branch advances (commit kept)
- On regression: `git reset` back to last good commit
- The branch is a linear history of only improvements
- results.tsv stays untracked (not committed)

#### 2.8.2 Timeout and Crash Handling

- Each experiment: ~5 minutes + overhead
- If run exceeds 10 minutes: kill it, treat as failure (discard + revert)
- Crashes (OOM, bugs): use judgment
  - Typo/missing import: fix and re-run
  - Fundamentally broken idea: log "crash", move on
- `math.isnan(train_loss_f) or train_loss_f > 100`: immediate FAIL exit

#### 2.8.3 Autonomy Rules

Quoted verbatim:
> NEVER STOP: Once the experiment loop has begun, do NOT pause to ask the human if you should
> continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human
> might be asleep. You are autonomous. If you run out of ideas, think harder -- read papers
> referenced in the code, re-read the in-scope files, try combining previous near-misses, try
> more radical architectural changes. The loop runs until the human interrupts you, period.

Expected throughput: ~12 experiments/hour, ~100 experiments overnight.

### 2.9 train.py Architecture (Default Configuration)

#### 2.9.1 Model (GPT)

```python
@dataclass
class GPTConfig:
    sequence_len: int = 2048
    vocab_size: int = 32768    # overridden by tokenizer at runtime
    n_layer: int = 12
    n_head: int = 6
    n_kv_head: int = 6
    n_embd: int = 768
    window_pattern: str = "SSSL"
```

Key architectural features:
- RMS normalization (no bias)
- Rotary positional embeddings (RoPE)
- Sliding window attention pattern: S=half context, L=full context
- Value Embeddings (ResFormer): alternating layers with input-dependent gate per head
- Per-layer residual scaling via `resid_lambdas` and `x0_lambdas`
- Logit soft-capping at 15
- Flash Attention 3 (Hopper FA3 for H100, kernels-community fallback)
- ReLU squared activation in MLP (not GeLU)

#### 2.9.2 Default Hyperparameters

```python
ASPECT_RATIO = 64       # model_dim = depth * ASPECT_RATIO
HEAD_DIM = 128
WINDOW_PATTERN = "SSSL"
TOTAL_BATCH_SIZE = 2**19  # ~524K tokens per optimizer step
EMBEDDING_LR = 0.6
UNEMBEDDING_LR = 0.004
MATRIX_LR = 0.04
SCALAR_LR = 0.5
WEIGHT_DECAY = 0.2
ADAM_BETAS = (0.8, 0.95)
WARMUP_RATIO = 0.0
WARMDOWN_RATIO = 0.5
FINAL_LR_FRAC = 0.0
DEPTH = 8
DEVICE_BATCH_SIZE = 128
```

Model dim = DEPTH * ASPECT_RATIO = 8 * 64 = 512, rounded up to nearest HEAD_DIM multiple = 512.
Number of heads = 512 / 128 = 4.

#### 2.9.3 Optimizer (MuonAdamW)

Combined optimizer:
- **Muon** for 2D matrix parameters: Nesterov momentum + Polar Express orthogonalization +
  NorMuon variance reduction + cautious weight decay
- **AdamW** for everything else: embeddings, unembeddings, per-layer scalars, value embeddings

Both optimizers use `torch.compile(dynamic=False, fullgraph=True)` for their step functions.

Muon has separate parameter groups per unique shape (for stacked gradient operations).

LR scaling: AdamW LRs scaled by `1/sqrt(model_dim/768)`.

#### 2.9.4 LR Schedule

```python
def get_lr_multiplier(progress):
    if progress < WARMUP_RATIO:        # warmup phase (default: 0 = no warmup)
        return progress / WARMUP_RATIO
    elif progress < 1.0 - WARMDOWN_RATIO:  # constant phase
        return 1.0
    else:                                   # warmdown phase (default: last 50%)
        cooldown = (1 - progress) / WARMDOWN_RATIO
        return cooldown * 1.0 + (1 - cooldown) * FINAL_LR_FRAC
```

Muon momentum ramps from 0.85 to 0.95 over first 300 steps.
Weight decay decays linearly: `WEIGHT_DECAY * (1 - progress)`.

#### 2.9.5 Training Loop

- Time-based termination: runs until `total_training_time >= TIME_BUDGET` (300s)
- First 10 steps excluded from time budget (compilation warmup)
- EMA smoothed training loss (beta=0.9) for display
- Fast fail: NaN or loss > 100 triggers immediate exit
- GC management: `gc.freeze()` + `gc.disable()` after step 0, periodic collect every 5000 steps
  (avoids ~500ms GC stalls)
- Gradient accumulation: `TOTAL_BATCH_SIZE / (DEVICE_BATCH_SIZE * MAX_SEQ_LEN)` steps

### 2.10 Notable Forks

- miolini/autoresearch-macos (MacOS)
- trevin-creator/autoresearch-mlx (MacOS)
- jsegov/autoresearch-win-rtx (Windows)
- andyluo7/autoresearch (AMD)

### 2.11 Tuning Recommendations for Smaller GPUs

From README, for non-H100 platforms:
1. Use TinyStories dataset (lower entropy = better results with small models)
2. Decrease `vocab_size` (8192 -> 4096/2048/1024/256)
3. Lower `MAX_SEQ_LEN` (down to 256), increase `DEVICE_BATCH_SIZE` to compensate
4. Decrease `EVAL_TOKENS` for faster validation
5. Lower `DEPTH` (8 -> 4)
6. Use `WINDOW_PATTERN = "L"` (banded attention inefficient on small hardware)
7. Lower `TOTAL_BATCH_SIZE` (keep powers of 2, down to 2**14)

---

## Part 3: Comparative Analysis

### 3.1 Design Philosophy Comparison

| Dimension              | agent-orchestrator                    | autoresearch                         |
|------------------------|---------------------------------------|--------------------------------------|
| Complexity             | Enterprise-grade, 21 plugins          | Deliberately minimal, 3 files        |
| Agent scope            | Code generation across entire codebase| Single file modification (train.py)  |
| Feedback loop          | CI/PR/Review -> agent -> fix -> merge | Train -> evaluate -> keep/discard    |
| Human involvement      | Review and merge (notified when needed)| Sleep (check results in morning)    |
| Metric                 | PR merged successfully                | val_bpb (lower is better)            |
| Rollback strategy      | Git worktrees (isolated branches)     | Git reset to last good commit        |
| Parallelism            | Multiple agents on multiple issues    | Single agent, sequential experiments |
| State persistence      | Flat key=value metadata files         | results.tsv (untracked)              |
| Configuration          | YAML + TypeScript types               | program.md (Markdown "skill")        |
| Escalation             | Retry -> escalate -> notify human     | Crash -> try fix -> give up -> next  |

### 3.2 Patterns Worth Extracting

From agent-orchestrator:
- 8-slot plugin architecture for swappable abstractions
- Reaction engine with configurable retry/escalation thresholds
- Review comment fingerprinting for deduplication
- Hash-based namespacing for multi-instance isolation
- Flat metadata files for debuggability
- Consent gates with auditable overrides
- Feedback journal with idempotency keys

From autoresearch:
- program.md as a "skill" -- human programs the prompt, agent programs the code
- Fixed time budget for fair experiment comparison
- val_bpb as vocab-size-independent metric
- Git branch as experiment journal (only improvements survive)
- results.tsv with structured crash/keep/discard status tracking
- Simplicity criterion as explicit evaluation heuristic
- "NEVER STOP" autonomy contract
- GC management for training stability (freeze + disable + periodic collect)

### 3.3 Relevance to mde Project

| Pattern                        | Applicability to mde              |
|-------------------------------|-----------------------------------|
| Plugin slot architecture       | High -- for tool/runtime plugins  |
| Reaction engine YAML config    | High -- for CI/hook automation    |
| Worktree isolation per task    | Already used (worktree-pr-workflow)|
| Flat metadata for debugging    | Medium -- simpler than DB         |
| program.md as skill pattern    | High -- already using skills      |
| Experiment loop with keep/discard | Medium -- for research pipeline |
| Simplicity criterion           | High -- matches research pipeline |
| Review fingerprinting          | Low -- not running review bots    |

---

## Appendix A: Full Feedback Config Schema

```yaml
feedback:
  mode: scm                    # local | scm
  scm:
    provider: github           # github | gitlab
    targetRepo: auto           # auto | upstream | fork
    forkStrategy: upstream     # upstream | fork | skip
    prReference: if_present    # required | if_present | never
    minConfidence:
      bug_report: 0.6
      improvement_suggestion: 0.75
  followUp:
    enableAgentSession: true
    requireIssueBeforeSession: true
  consent:
    defaultPolicy: require_human_for_major_mutations
    requireFor:
      createFork: true
      createPR: true
      switchTarget: true
    projectOverride:
      enabled: false
  governance:
    allowedForkOwners: ["<org-or-user>"]
    requireApprovalForForkCreation: true
```

## Appendix B: Full agent-orchestrator.yaml Example

```yaml
dataDir: ~/.agent-orchestrator
worktreeDir: ~/.worktrees
port: 3000

defaults:
  runtime: tmux
  agent: claude-code
  workspace: worktree
  notifiers: [desktop]

projects:
  my-app:
    name: My App
    repo: org/my-app
    path: ~/my-app
    defaultBranch: main
    sessionPrefix: app
    # tracker:
    #   plugin: linear
    #   teamId: "your-team-id"
    # scm:
    #   plugin: github
    #   webhook:
    #     path: /api/webhooks/github
    #     secretEnvVar: GITHUB_WEBHOOK_SECRET
    #     signatureHeader: x-hub-signature-256
    #     eventHeader: x-github-event
    #     deliveryHeader: x-github-delivery
    #     maxBodyBytes: 1048576
    # symlinks: [.env, .claude]
    # postCreate:
    #   - "pnpm install"
    # agentConfig:
    #   permissions: skip
    #   model: opus
    # agentRules: |
    #   Always run tests before pushing.
    # agentRulesFile: .agent-rules.md

reactions:
  ci-failed:
    auto: true
    action: send-to-agent
    retries: 2
    escalateAfter: 2
  changes-requested:
    auto: true
    action: send-to-agent
    escalateAfter: 30m
  approved-and-green:
    auto: false
    action: notify
    priority: action
  agent-stuck:
    threshold: 10m
    action: notify
    priority: urgent
```

## Appendix C: autoresearch program.md (Complete)

See Section 2.6 for the full content. The file is a lightweight "skill" that instructs the
agent on setup, constraints, output format, logging, and the experiment loop. It is approximately
3.5KB and constitutes the entire coordination protocol for the autonomous research agent.

## Appendix D: Source URLs Fetched

| URL | Status | Method |
|-----|--------|--------|
| https://github.com/ComposioHQ/agent-orchestrator | 200 | agent-fetch |
| https://github.com/karpathy/autoresearch | 200 | agent-fetch |
| karpathy/autoresearch/contents/program.md | 200 | gh api raw |
| karpathy/autoresearch/contents/prepare.py | 200 | gh api raw |
| karpathy/autoresearch/contents/train.py | 200 | gh api raw |
| karpathy/autoresearch/contents/pyproject.toml | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/packages/core/src/types.ts | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/packages/core/src/lifecycle-manager.ts | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/packages/plugins/workspace-worktree/src/index.ts | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/docs/design/feedback-routing-and-followup-design.md | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/agent-orchestrator.yaml.example | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/docs/CLI.md | 200 | gh api raw |
| ComposioHQ/agent-orchestrator/contents/docs/DEVELOPMENT.md | 200 | gh api raw |
