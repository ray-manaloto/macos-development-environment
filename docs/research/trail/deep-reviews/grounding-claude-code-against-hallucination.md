# Grounding Claude Code Against Self-Hallucination

> Research into techniques and tools that prevent Claude Code from providing false
> information about its own configuration, capabilities, and the state of the project.
> Compiled 2026-03-26 from analysis of this project's existing mechanisms, official
> Claude Code documentation, community plugins, and general anti-hallucination patterns.

---

## The Problem

Claude Code can confidently assert false things about:

1. **Its own configuration** -- claiming hooks exist that do not, reporting settings values from training data instead of actual `.claude/settings.json`
2. **Its capabilities** -- asserting it can use tools it does not have, or that features exist that were never implemented
3. **Project state** -- claiming tests pass without running them, asserting files exist without checking, reporting build status from memory instead of evidence
4. **Platform features** -- confusing API-only features with Claude Code features, citing deprecated or nonexistent parameters

The root cause is that the model draws on training data (which includes documentation, blog posts, and speculation) rather than reading the actual runtime environment.

---

## Taxonomy of Grounding Techniques

### Layer 1: Declarative Grounding (CLAUDE.md + Rules)

**Mechanism:** Instructions loaded into every session that tell the model what is true about its environment.

**What this project already does:**
- `CLAUDE.md` (69 lines) declares the exact commands, architecture, conventions, and enforcement rules
- 18 rules files in `.claude/rules/` covering specific policy domains
- Rules use imperative, verifiable language ("NEVER use X", "ALL Y must Z")

**Best practices for anti-hallucination:**

| Practice | Example from this project | Why it works |
|----------|--------------------------|--------------|
| Specific over vague | "Use `uv run mde-py quality` not 'run the linter'" | Eliminates guessing |
| Exhaustive enums | "Commits: `feat:`, `fix:`, `docs:`, `research:`" | Closed set prevents invention |
| Negative constraints | "NEVER create `.sh` files" | Blocks common hallucinated actions |
| Pointing to files | "See `.claude/rules/` for details" | Directs to verifiable source |
| Version-pinned references | "14 frontmatter fields: name, description, ..." | Prevents field invention |

**Key insight:** CLAUDE.md is a *claim* about reality, not a *verification* of reality. It reduces hallucination by narrowing the space of plausible actions, but the model can still deviate. Rules are stronger than CLAUDE.md because they are loaded unconditionally and cover specific domains.

**Limitation:** If CLAUDE.md itself contains stale information (e.g., says "16 policy files" when there are now 18), it becomes a source of hallucination rather than a cure.

---

### Layer 2: Schema-Driven Validation (Runtime Type Checking)

**Mechanism:** Pydantic models generated from JSON Schema that validate configuration at write time, not just at read time.

**What this project already does:**
- `docs/schemas/agent-frontmatter.schema.json` -- canonical schema for agent `.md` frontmatter
- `src/mde/hooks/_agent_frontmatter_model.py` -- auto-generated Pydantic model from that schema
- `src/mde/hooks/validate_agents.py` -- PostToolUse hook that validates every Write/Edit to `.claude/agents/` against the schema
- Additional schemas: `honcho-client.schema.json`, `skillsmp.schema.json`
- `src/mde/statusline/statusline-stdin.schema.json` -- schema for statusline input

**How it prevents hallucination:**
```
Model writes agent file with invented field "priority: high"
  -> PostToolUse hook fires
  -> Pydantic model has extra="forbid"
  -> Validation error: "Extra inputs are not permitted"
  -> Model receives error feedback
  -> Model corrects the file
```

**Key properties of this approach:**
- Schema is the single source of truth, not training data
- `extra="forbid"` catches invented fields (the most common hallucination)
- Enum types (`Model`, `PermissionMode`, `Effort`) prevent invalid values
- Regex patterns (`^[a-z][a-z0-9-]*$`) enforce naming conventions
- Codegen from schema means the validator is never hand-maintained (no drift)

**Generalization opportunity:** Any configuration format that Claude Code writes can be protected this way -- `settings.json`, `plugin.json`, `hk.pkl`, `mise.toml`. The pattern is:
1. Define JSON Schema for the format
2. Generate Pydantic model via `datamodel-codegen`
3. Wire a PostToolUse hook that validates on every edit

---

### Layer 3: PreToolUse Guards (Behavioral Enforcement)

**Mechanism:** Hooks that intercept tool calls *before execution* and block prohibited actions.

**What this project already does:**
- `guard_install.py` -- blocks `brew install`, `pip install`, `npm install -g`, etc. with a deny decision JSON
- `guard_dotfile_edit.py` -- blocks direct edits to `~/.` files, enforcing chezmoi source-first workflow

**How it prevents hallucination:**
The model may "hallucinate" that the correct action is to `brew install` a tool. The guard hook intercepts this before execution and returns a structured denial with the correct procedure. The model then self-corrects.

**Key design pattern:**
```python
# Allow-list takes precedence over block-list
for pattern in _ALLOW_PATTERNS:
    if pattern.search(command):
        return None  # permitted

for pattern in _BLOCK_PATTERNS:
    if pattern.search(command):
        return {"decision": "deny", "reason": _DENY_REASON}
```

The deny reason is itself a grounding instruction: it tells the model *what to do instead*, not just what not to do.

---

### Layer 4: Verification-Before-Completion (Evidence Gates)

**Mechanism:** Skills and rules that require the model to produce evidence before making claims.

**What this project already does:**
- `verification-before-completion` skill (SKILL.md, 140 lines) -- the most aggressive anti-hallucination mechanism in the project
- Core principle: "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"
- Prevents: "should work now", "I'm confident", "tests pass" without running tests
- Derived from 24 documented failure cases where the model made false claims

**Why this works:** It does not prevent the model from generating false beliefs internally. Instead, it prevents false beliefs from becoming false *claims* by requiring an executable verification step between belief and assertion.

**Limitation:** The skill relies on the model following instructions. Under context pressure or after compaction, adherence degrades.

---

### Layer 5: Runtime Documentation Fetching (Context7)

**Mechanism:** Instead of relying on training data for library/API documentation, fetch current documentation at query time.

**What this project already does:**
- `~/.claude/rules/context7.md` (global rule, `alwaysApply: true`) -- instructs the model to use Context7 MCP for all library questions
- Three integration layers: MCP server, plugin, CLI skills
- `resolve-library-id` + `query-docs` tools available

**How it prevents hallucination:**
```
Model needs to use a library API
  -> Instead of recalling from training data
  -> Calls resolve-library-id("library-name", "question")
  -> Calls query-docs("/org/library", "question")
  -> Receives current, version-specific documentation
  -> Generates code from fetched docs, not memory
```

**Key insight from researcher memory:** "LLMs hallucinate APIs and use outdated docs from training data cutoff." Context7 solves this by making documentation a runtime input rather than a training data recall.

**Limitation:** Only works for libraries indexed by Context7. Does not help with Claude Code's own features, which are not in Context7's index.

---

### Layer 6: Adversarial Challenge (Multi-Agent Verification)

**Mechanism:** A second agent (or multiple agents) stress-tests the primary agent's claims, looking for logical flaws, unverified assertions, and missing evidence.

**What this project already does:**
- `challenger` plugin (v3.5.0) with 4 adversarial agents: skeptic, sentinel, architect, pragmatist
- `skeptic` agent specifically targets "weak assumptions, logical fallacies, and unverified claims"
- Skeptic uses Read/Grep/Glob to verify claims against actual code
- Auto-scaling intensity: quick (1 round) to brutal (unlimited rounds)
- `/challenge` skill for on-demand adversarial review

**How it prevents hallucination:**
```
Primary agent claims: "The hook system supports 22 events"
  -> /challenge
  -> Skeptic agent spawns
  -> Reads .claude/settings.json, counts actual hook event types
  -> If count differs: "Challenge: You claimed 22 events but I found N"
  -> Primary agent must provide evidence or correct the claim
```

**Key design:** The skeptic explicitly uses tools to verify, not just reason about claims. From the agent definition: "When you find evidence, cite it. When you can't find evidence for a claim, say so -- that IS your challenge."

---

### Layer 7: PostToolUse Validation Hooks (Continuous Quality)

**Mechanism:** Hooks that run after every relevant tool use to catch quality issues immediately.

**What this project already does:**
- `validate-plugins` hook -- runs after every Write/Edit, validates plugin structure
- `log-edit-outcome` hook -- logs what was changed for audit trail
- `remind-chezmoi-commit` hook -- fires on Bash to remind about chezmoi workflow
- `ruff format` hook -- auto-formats Python on every edit (eliminates formatting hallucination)

**How it prevents hallucination:** The model cannot write invalid plugin configuration and proceed as if it is valid. The validation hook catches the error immediately and feeds it back into the conversation context.

---

### Layer 8: Stop/PreCompact Memory Preservation

**Mechanism:** Hooks that fire at session boundaries to prevent knowledge loss.

**What this project already does:**
- `Stop` hook with prompt: "Did the agent write all findings to files on disk?"
- `PreCompact` hook with prompt: "Are there any research findings in the conversation that have NOT been written?"
- `persist-transcripts` command hook on both Stop and PreCompact

**Anti-hallucination angle:** After compaction, the model may hallucinate about what happened before compaction. By forcing findings to disk before compaction, the model can re-read them from files rather than hallucinating their contents.

---

## Techniques NOT Yet Implemented (Opportunities)

### A. Self-Interrogation Hook

A PreCompact or periodic hook that asks the model to list what it believes about its own configuration, then validates those beliefs against actual files:

```
Prompt hook: "List the tools available to you. Now read .claude/settings.json
and list the actual configured tools. Report any discrepancies."
```

### B. Configuration Snapshot in CLAUDE.md

Auto-generate a section of CLAUDE.md from actual runtime state:

```bash
# Generate grounding facts from actual config
python3 -c "
import json, pathlib
settings = json.loads(pathlib.Path('.claude/settings.json').read_text())
hooks = settings.get('hooks', {})
print(f'## Verified Configuration (auto-generated)')
print(f'- Hook events configured: {len(hooks)}')
for event in sorted(hooks):
    print(f'  - {event}: {len(hooks[event])} matcher groups')
plugins = settings.get('enabledPlugins', {})
enabled = [k for k,v in plugins.items() if v]
print(f'- Enabled plugins: {len(enabled)}')
for p in sorted(enabled):
    print(f'  - {p}')
"
```

This would be run as a SessionStart hook, writing to a `.claude/rules/verified-config.md` file that the model reads. The model then has ground truth about its own configuration.

### C. Schema Validation for settings.json

The agent frontmatter schema pattern could be extended to `.claude/settings.json` itself. If every write to settings.json is validated against a schema, the model cannot introduce invalid hook events, malformed matchers, or invented settings keys.

### D. Fact-Checked Rules Files

Rules files could include machine-verifiable assertions:

```markdown
# Hook Events (verified 2026-03-26)
<!-- verify: jq '.hooks | keys | length' .claude/settings.json == 7 -->

This project configures 7 hook event types: PreToolUse, PostToolUse, SubagentStart,
SubagentStop, SessionStart, Stop, PreCompact, PostCompact.
```

A SessionStart hook could parse these `<!-- verify: ... -->` comments and run the commands, flagging any rules file whose assertions no longer hold.

### E. Agent Capability Manifest

Each agent definition could include a machine-readable list of what it can and cannot do, validated at SubagentStart:

```yaml
capabilities:
  can_write_files: true
  can_spawn_subagents: false
  can_access_mcp:
    - github
    - context7
assertions:
  - "tool:Write in tools list"
  - "tool:Agent not in tools list"
```

### F. Periodic Ground Truth Refresh

A background agent that periodically (e.g., every 50 tool calls) reads key configuration files and injects a summary into context:

```
"Ground truth refresh: .claude/settings.json has 7 hook events, 25 enabled plugins.
 .claude/agents/ contains 10 agent definitions. src/mde/hooks/ has 11 hook modules."
```

---

## Summary: Defense in Depth

| Layer | Mechanism | When | Prevents |
|-------|-----------|------|----------|
| 1 | CLAUDE.md + rules | Session start | Inventing procedures, tools, workflows |
| 2 | Schema validation | PostToolUse (write) | Invalid configuration fields/values |
| 3 | PreToolUse guards | Before execution | Prohibited actions the model thinks are correct |
| 4 | Verification skill | Before claims | False completion/success claims |
| 5 | Context7 | During coding | Outdated/invented API usage |
| 6 | Adversarial agents | On demand | Unverified logical claims |
| 7 | PostToolUse hooks | After every edit | Quality drift, invalid formats |
| 8 | Stop/PreCompact | Session boundaries | Post-compaction hallucination |

**The key insight is that no single layer is sufficient.** CLAUDE.md can be stale. Schema validation only covers structured formats. Guards only cover known bad patterns. Verification requires the model to follow instructions. Context7 only covers indexed libraries. Adversarial review is expensive and on-demand.

The most robust approach is defense in depth: multiple independent layers that catch different failure modes at different points in the workflow. This project already implements 8 of these layers, making it significantly more resistant to self-hallucination than a bare Claude Code setup.

---

## Recommended Priority for New Mechanisms

1. **Configuration snapshot rule** (technique B) -- highest ROI, prevents the most common hallucination class (model claims about its own configuration)
2. **Schema for settings.json** (technique C) -- extends proven pattern to the most critical config file
3. **Fact-checked rules** (technique D) -- makes rules self-verifying, catches stale documentation
4. **Self-interrogation hook** (technique A) -- periodic grounding refresh during long sessions
5. **Capability manifest** (technique E) -- useful for complex multi-agent setups
6. **Periodic refresh** (technique F) -- most complex, best for very long sessions
