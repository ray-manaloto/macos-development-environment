# Gap Analysis: Research Findings vs. Migration Spec

**Date:** 2026-03-20
**Analyst:** research-agent (Claude Opus 4.6, 1M context)
**Spec reviewed:** `docs/superpowers/specs/2026-03-20-native-claude-code-migration-design.md`
**Deep reviews analyzed:** 11 documents
**YAML findings analyzed:** 9 provenance records

---

## Methodology

For each of the 11 deep review documents, I compared every feature, technique, tool, skill, hook, pattern, and URL discovered against what is currently specified in the migration spec (Sections 1-15). Items that appear in the spec's "Patterns Adopted" table (Section 9, 30 entries) or "Not Adopted" table (Section 10, 25 entries) are marked as covered. Everything else is a gap.

---

## 1. agent-note-persistence-infrastructure.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| Write-early, write-often principle | Section 1 | YES | Spec pattern #15 |
| 4-tier memory hierarchy (hot/warm/cool/cold) | Section 3 | YES | Spec pattern #16 |
| One notebook per domain | Section 2 | YES | Spec pattern #17 |
| NotebookLM source add-research | Section 6 | YES | Spec pattern #18 |
| Git history as implicit memory | Section 6 | YES | Spec pattern #19 |
| claude-progress.txt + feature_list.json | Section 6 | PARTIAL | Spec pattern #14 mentions it but only adopts score-history.tsv, not the full two-file pattern |
| `notebooklm source guide <id>` for auto study guides | Section 6.4 | NO | NotebookLM `source guide` command for automatic study guide generation from any source |
| `notebooklm source fulltext <id>` for full extracted text | Section 2 | NO | Full text extraction from sources not mentioned in spec |
| `notebooklm configure` for persona/response settings | Section 2 | NO | Notebook configuration not mentioned in spec |
| `notebooklm source rename` for source management | Section 2 | NO | Source renaming not in spec |
| Claude Developer Platform Memory Tool (`memory_20250818`) | Section 6.1 | NO | SDK-level memory tool for custom agents built on Claude API |
| Subagent-specific persistent memory via `memory` field | Section 6.2 | YES | Spec uses `memory: project` in agent files |
| Phase 2 consolidation agent workflow | Section 5 | PARTIAL | Spec describes file flow but no dedicated consolidation agent or `mde-py research consolidate` command |
| Phase 3 periodic deep review workflow | Section 5 | NO | Weekly/milestone review process with Obsidian archival not specified |
| `notebooklm history` for conversation history retrieval | Section 2 | NO | History retrieval not mentioned in spec |
| Note-writing cadence (5 checkpoints) | Section 1 | PARTIAL | Stop and PreCompact hooks cover 2 of 5 checkpoints; session start, after discovery, and before risky operation are not hooked |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| No consolidation agent or `mde-py research consolidate` command | MEDIUM | Add a consolidation step to the research pipeline that ingests new findings into NotebookLM and cross-references |
| No periodic deep review process specified | LOW | Add a weekly review checklist to second-brain.md rule |
| NotebookLM `source guide` not mentioned | LOW | Add to second-brain.md as optional synthesis tool |
| Memory Tool API for SDK-built agents | LOW | Not relevant until building custom agents via Agent SDK |
| Only 2 of 5 note-writing checkpoints have hooks | MEDIUM | Add SessionStart hook to read git log and checkpoint state |

---

## 2. gstack-complete-reference.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| Skill chaining with artifact handoff | Section 5 | YES | Spec pattern #10 |
| /review two-pass checklist (critical blocks, informational doesn't) | Section 10 | YES | Spec pattern #11 |
| 21-skill pack | Section 3 | NO (explicitly rejected) | Spec rejection #15 |
| gstack Conductor for 10-15 parallel sessions | Section 6 | NO (rejected) | Spec rejection #17 |
| /browse browser automation | Section 7 | NO (rejected) | Spec rejection #16 |
| Greptile integration | Section 11 | NO (rejected) | Spec rejection #18 |
| /investigate auto-freeze on debugging module | Section 14 | NO | Auto-freeze pattern during debugging not adopted |
| /qa health score 0-100 | Section 9 | NO | Health scoring pattern for QA not adopted |
| /retro JSON snapshots for trend tracking | Section 16 | NO | Weekly retrospective with JSON snapshots not adopted |
| /ship one-command release pipeline | Section 12 | NO | Single-command ship workflow not adopted (we use finishing-a-development-branch) |
| /codex cross-model review | Section 13 | NO (rejected for ARIS) | Same as ARIS rejection #10 |
| Proactive skill suggestions based on work stage | Section 17 | NO | Claude suggesting which skill to use based on detected work stage |
| gstack-upgrade self-updater pattern | Section 15 | NO | Self-updating skill pattern not adopted |
| ELI16 mode (re-grounding context when 3+ sessions active) | Section 6 | NO | Context re-grounding for multi-session work not adopted |
| /careful destructive command warnings | Section 3 | NO | Pre-destructive-command warning system |
| /freeze edit-lock to one directory | Section 3 | NO | Directory-scoped edit restriction during debugging |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| /investigate auto-freeze pattern | MEDIUM | Add to reviewer.md or create a debugging skill that restricts edits to the module under investigation |
| /careful destructive command warnings | MEDIUM | The PreToolUse[Bash] guard-install hook partially covers this; consider extending to warn on `rm -rf`, `git reset --hard`, etc. |
| /freeze directory-scoped edit restriction | LOW | Useful for debugging; could be a future skill |
| Proactive skill suggestions | LOW | Could be a SessionStart hook that suggests relevant skills based on recent git activity |

---

## 3. aris-and-compound-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| REVIEW_STATE.json checkpoint with 24h staleness | Section 1.3 | YES | Spec pattern #5 |
| Subagents return text, orchestrator writes files | Section 3.6 | YES | Spec pattern #6 |
| Provenance enrichment (tags, implication, confidence prose) | Sections 2.3, 3.3 | YES | Spec pattern #7 |
| kw:confidence non-numeric assessment | Section 3.2 | YES | Spec pattern #8 |
| Grep-based retrieval in docs/ | Section 3.4 | YES | Spec pattern #9 |
| Protected artifacts (never flagged for deletion) | Section 2.4 | YES | Spec pattern #30 |
| ARIS cross-model review (GPT-5.4) | Section 1.6 | NO (rejected) | Spec rejection #10 |
| Compound 27+ review agents | Section 2.2 | NO (rejected) | Spec rejection #13 |
| ARIS AUTO_REVIEW.md cumulative log format | Section 1.4 | NO | Append-only cumulative review log with raw reviewer responses in `<details>` blocks |
| ARIS AUTO_PROCEED gate logic with timeout | Section 1.5 | NO | Auto-proceed with 10-second user timeout; options: approve/pick different/request changes/reject/stop |
| ARIS HUMAN_CHECKPOINT pause-after-each-round | Section 1.5 | NO | Pause after each review round with options: go/custom/skip/stop |
| ARIS fix prioritization rules | Section 1.7 | NO | Skip excessive compute, prefer reframing over new experiments, always implement cheap additions |
| Compound ce:brainstorm -> ce:plan -> ce:work -> ce:review -> ce:compound cycle | Section 2.2 | NO | Full compound engineering cycle not adopted (too heavy for our project) |
| Compound ce:compound-refresh staleness management | Section 2.5 | NO | 4 outcomes: Keep/Update/Replace/Archive for docs/solutions/ |
| Compound docs/solutions/ categorized knowledge base | Section 2.3 | NO | Categorized knowledge base with YAML frontmatter and problem_type taxonomy |
| Compound docs/brainstorms/ requirements docs | Section 2.2 | NO | Structured brainstorm -> requirements flow |
| Compound's auto-invoke triggers ("that worked", "it's fixed") | Section 2.2 | NO | Detecting solution completion from natural language triggers |
| ARIS Feishu/Lark integration | Section 1.9 | NO (rejected) | Spec rejection #11 |
| ARIS MCP servers (claude-review, llm-chat, minimax-chat) | Section 1.10 | NO (rejected) | Spec rejection #12 |
| kw:compound learning type taxonomy (insight/playbook/correction/pattern) | Section 3.3 | PARTIAL | Spec enriches provenance YAML but does not adopt the 4-type taxonomy as a finding_type enum |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| AUTO_REVIEW.md cumulative log format | MEDIUM | Adopt as template for multi-round research cycles; append raw findings per round |
| Fix prioritization rules | MEDIUM | Add to researcher.md: skip sources requiring excessive time, prefer synthesis over new fetches, always catalog cheap URLs |
| Staleness management (Keep/Update/Replace/Archive) | LOW | Future feature for docs/research/trail/ maintenance |
| Learning type taxonomy in finding_type enum | LOW | Extend finding_type to include insight/playbook/correction/pattern alongside existing values |
| AUTO_PROCEED gate logic | LOW | Not needed until we have automated multi-round research loops |

---

## 4. claude-mem-mcp2cli-amplihack-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| 3-layer progressive disclosure | Section 1 | YES | Spec pattern #1 |
| mcp2cli bake pattern | Section 2 | YES | Spec pattern #2 |
| TOON output format | Section 3 | YES | Spec pattern #3 |
| env:/file: secret prefixes | Section 5 | YES | Spec pattern #4 |
| claude-mem worker service | Section 3 | NO (rejected) | Spec rejection #5 |
| claude-mem SQLite + ChromaDB | Section 3 | NO (rejected) | Spec rejection #6 |
| amplihack Kuzu graph DB | Section 7 | NO (rejected) | Spec rejection #7 |
| amplihack L1-L12 eval | Section 1 | NO (rejected) | Spec rejection #8 |
| amplihack self-improvement loop | Section 3 | NO (rejected) | Spec rejection #9 |
| mcp2cli `--search` pattern filtering | Section 6 | NO | Tool filtering by name/description pattern not mentioned in spec |
| mcp2cli `--jq EXPR` for JSON filtering | Section 3 | NO | jq expression filtering of output |
| mcp2cli `--head N` for array limiting | Section 3 | NO | Output limiting for large result sets |
| mcp2cli OAuth support (PKCE, client credentials) | Section 4 | NO | OAuth flow support for authenticated APIs |
| mcp2cli GraphQL introspection mode | Section 1.4 | NO | Auto-discovery of GraphQL endpoints |
| mcp2cli OpenAPI spec mode | Section 1.3 | NO | Direct OpenAPI spec consumption |
| mcp2cli `bake install` for ~/.local/bin wrapper | Section 2 | NO | Installing baked tools as standalone CLI commands |
| mcp2cli caching (--cache-ttl, --refresh) | Section 7 | NO | Spec caching for repeated operations |
| amplihack 10-failure-mode error taxonomy | Section 2 | NO | Classifying failures into specific categories for targeted fixes |
| amplihack +2% commit threshold / >5% regression guard | Section 4 | NO | Quantitative improvement thresholds for self-improvement |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| mcp2cli `--search` pattern filtering | HIGH | Add to mcp-access.md rule: `mcp2cli @github --search "issue"` for scoping large MCP servers |
| mcp2cli `bake install` | MEDIUM | Add to migration checklist: install baked tools as standalone CLIs for common operations |
| mcp2cli caching flags | LOW | Useful for repeated API calls; document in mcp-access.md |
| Error taxonomy for classifying failures | MEDIUM | Adopt for research pipeline: categorize why sources fail (fetch error, parse error, no content, paywall, etc.) |
| Regression guard (+2% / >5%) | LOW | Future feature for research score tracking |

---

## 5. claude-code-native-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| Prompt-based hooks for quality gates | Section 4 | YES | Spec pattern #25 |
| Agent frontmatter field reference | Section 2 | YES | Spec pattern #26 |
| JSON over Markdown for modified state | Section 6C | YES | Spec pattern #12 |
| Initializer + Worker pattern | Section 6C | YES | Spec pattern #13 |
| claude-progress.txt progress file | Section 6C | YES | Spec pattern #14 |
| JIT retrieval with lightweight identifiers | Section 6D | YES | Spec pattern #20 |
| Context as finite resource | Section 6D | YES | Spec pattern #21 |
| Absolute minimum viable complexity | Section 6A | YES | Spec pattern #22 |
| Agent Teams experimental | Section 3 | YES | Spec Section 14 fully covers this |
| @import syntax for CLAUDE.md | Section 1 | NO | CLAUDE.md can import other files with `@path/to/file` syntax |
| claudeMdExcludes setting | Section 1 | NO | Setting to skip specific CLAUDE.md files |
| `--add-dir` flag for extra directories | Appendix A | NO | Not mentioned in spec; useful for multi-repo work |
| `context: fork` + `agent` field for skills | Section 5 | NO | Skills can run in forked subagent context |
| `!command` dynamic injection in skills | Section 5 | NO | Shell command output injected into skill content before sending to Claude |
| `$ARGUMENTS` substitution in skills | Section 5 | NO | String substitution variables for skill arguments |
| Skill description budget (2% of context window) | Section 5 | YES | Spec mentions this in context-budget.md |
| `disable-model-invocation: true` for skills | Section 5 | NO | Skills that only users (not Claude) can invoke |
| `user-invocable: false` for skills | Section 5 | NO | Skills hidden from user menu but auto-invocable by Claude |
| `allowed-tools` in skill frontmatter | Section 5 | NO | Auto-approve tools when skill is active |
| Hook `async: true` for non-blocking hooks | Section 4 | NO | Async hooks that don't block execution |
| Hook `once: true` for single-execution | Section 4 | NO | Hook that runs only once per session |
| Agent hook `type: "agent"` for multi-turn hooks | Section 4 | NO | Multi-turn subagent hooks |
| Agent hook `type: "http"` for HTTP hooks | Section 4 | NO | HTTP webhook hooks |
| `permissionDecision` in PreToolUse hooks | Section 4 | NO | Hooks can allow/deny/ask tool usage programmatically |
| `updatedInput` in PreToolUse hooks | Section 4 | NO | Hooks can modify tool input before execution |
| SessionStart `CLAUDE_ENV_FILE` pattern | Section 4 | NO | Setting environment variables via hooks at session start |
| InstructionsLoaded hook event | Section 4 | NO | Hook when CLAUDE.md or rules are loaded |
| ConfigChange hook event | Section 4 | NO | Hook when config files change |
| WorktreeCreate / WorktreeRemove hooks | Section 4 | NO | Hooks for worktree lifecycle events |
| PostCompact hook event | Section 4 | NO | Hook after compaction (spec only has PreCompact) |
| PostToolUseFailure hook event | Section 4 | NO | Hook for failed tool executions |
| Notification hook event | Section 4 | NO | Hook for permission_prompt, idle_prompt, auth_success notifications |
| Elicitation / ElicitationResult hooks | Section 4 | NO | Hooks for MCP user input requests |
| `/batch` skill for parallel decomposition | Section 5 | NO | Built-in skill for 5-30 parallel background agents in worktrees |
| `/loop` skill for repeated execution | Section 5 | NO | Run prompt on interval |
| `/simplify` skill for review + fix | Section 5 | NO | Spawn 3 review agents in parallel |
| `--from-pr` flag for PR-linked sessions | Appendix A | NO | Resume sessions linked to a PR |
| `--fork-session` for branching conversations | Appendix A | NO | New session ID when resuming |
| `--remote-control` for claude.ai control | Appendix A | NO | Enable remote control from claude.ai web |
| Agent memory scopes: `user`, `project`, `local` | Section 2 | PARTIAL | Spec uses `project` but doesn't document `user` or `local` scope options |
| `worktree.symlinkDirectories` setting | Appendix B | NO | Symlink directories into worktrees |
| `worktree.sparsePaths` setting | Appendix B | NO | Sparse checkout for worktrees |
| pyright-lsp plugin | Section 3 | PARTIAL | Spec lists as "consider installing" but defers to post-migration |
| skill-creator plugin | Section 3 | PARTIAL | Same as above |
| hookify plugin | Section 3 | PARTIAL | Same as above |
| ralph-loop autonomous agent loop | Section 3 | NO | Autonomous loop pattern from official plugins |
| claude-md-management plugin | Section 3 | NO | CLAUDE.md file management plugin not mentioned |
| code-review plugin | Section 3 | NO | Code review automation plugin not mentioned |
| `"ultrathink"` keyword in skill content | Section 5 | NO | Trigger extended thinking by including "ultrathink" in skill |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| @import syntax for CLAUDE.md | HIGH | Use `@docs/research/source-catalog.md` to import key references without copying content into CLAUDE.md |
| `/batch` skill | HIGH | Document in CLAUDE.md: use `/batch` for parallel file changes across codebase |
| `context: fork` + `agent` for skills | HIGH | Team spawn recipe skills should use `context: fork` with appropriate agent |
| Async hooks (`async: true`) | MEDIUM | Make SubagentStart/Stop hooks async to avoid blocking |
| PostCompact hook | MEDIUM | Add PostCompact hook that re-reads RESEARCH_STATE.json after compaction |
| SessionStart hook for environment setup | MEDIUM | Add SessionStart hook to read git log, set env vars |
| `allowed-tools` in skill frontmatter | MEDIUM | Team spawn skills should auto-approve relevant tools |
| `permissionDecision` in PreToolUse | MEDIUM | Use for guard-install hook: programmatically allow/deny instead of exit code |
| pyright-lsp, hookify, skill-creator plugins | MEDIUM | Install during migration (not defer) |
| `worktree.symlinkDirectories` | LOW | Useful for worktree isolation; add to settings.json |
| `"ultrathink"` keyword | LOW | Add to skills that need deep reasoning (spawn-research-team) |
| ralph-loop autonomous agent loop | LOW | Evaluate for automated research cycles |
| PostToolUseFailure hook | LOW | Could log failed tool calls for debugging |

---

## 6. orchestrator-autoresearch-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| results.tsv structured tracking | Section 2.7 | YES | Spec pattern #23 |
| Simplicity criterion | Section 2.6.3 | YES | Spec pattern #24 |
| Flat metadata over database | Section 1.14 | YES | Spec pattern #29 |
| agent-orchestrator 8-slot plugin architecture | Section 1.2 | NO (rejected) | Spec rejection #19 |
| agent-orchestrator reaction engine YAML | Section 1.4 | NO (rejected) | Spec rejection #20 |
| autoresearch "NEVER STOP" autonomy contract | Section 2.8.3 | NO | Agent autonomy instruction: never pause to ask if you should continue |
| autoresearch git-branch-as-experiment-journal | Section 2.8.1 | NO | Branch where only improvements survive (regression = git reset) |
| autoresearch fixed time budget for fair comparison | Section 2.3 | NO | TIME_BUDGET constant ensures fair experiment comparison |
| agent-orchestrator review comment fingerprinting | Section 1.4.5 | NO | Content hash dedup for review comments |
| agent-orchestrator consent gates with auditable overrides | Section 1.7.7 | NO | Human consent required for forks/PRs with audit trail |
| agent-orchestrator feedback journal with idempotency | Section 1.7.6 | NO | Idempotent mutation tracking with operation keys |
| agent-orchestrator hash-based namespacing | Section 1.9 | NO | SHA-256 of config path for collision-free multi-instance |
| agent-orchestrator 17-state session lifecycle | Section 1.3 | NO | Full lifecycle FSM for agent sessions |
| agent-orchestrator 6-state activity detection | Section 1.3.3 | NO | Active/ready/idle/waiting/blocked/exited detection |
| autoresearch `grep "^val_bpb:" run.log` result extraction | Section 2.6.4 | NO | Structured output block parsed by grep |
| agent-orchestrator notification routing by priority | Section 1.6 | NO | urgent/action/warning/info routing to different channels |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| "NEVER STOP" autonomy instruction for research agents | MEDIUM | Add to researcher.md: "Once a research cycle begins, continue autonomously until all sources are processed" |
| Git-branch-as-experiment-journal | LOW | Potentially useful for research branches where only improved scores survive |
| Review comment fingerprinting | LOW | Not relevant until we run automated review bots |

---

## 7. skill-plugin-ecosystem-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| recall + sync-claude-sessions for Obsidian | Section 3 | YES | Spec pattern #27 |
| CLI-Anything for agent-native CLIs | Section 8 | YES | Spec pattern #28 |
| hermes-agent closed learning loop | Section 5 | NO (rejected) | Spec rejection #21 |
| gitagent compliance framework | Section 7 | NO (rejected) | Spec rejection #22 |
| chezmoi dotfiles management | Section 6 | NO (rejected) | Spec rejection #23 |
| Composio 78-app automation | Section 2 | NO (rejected) | Spec rejection #24 |
| recall skill (cross-session memory via Obsidian) | Section 3 | NO | Installed as plugin for Obsidian-based cross-session recall |
| sync-claude-sessions skill (auto-export to Obsidian) | Section 3 | NO | Auto-export conversations to Obsidian at session end |
| plugin-dashboard observability | Section 4 | NO | Shows which tools/plugins used on every turn |
| kaizen continuous improvement skill | Section 2 | NO | Japanese Kaizen methodology for iterative improvement |
| subagent-driven-development skill | Section 2 | NO | Dispatches independent subagents with code review checkpoints |
| root-cause-tracing skill (obra/superpowers) | Section 2 | NO | Systematic deep debugging via execution trace-back |
| skill-bus meta-skill for wiring skills | Section 1 | NO | Declarative context/condition/skill wiring |
| context-mode plugin for large output processing | Section 1 | NO | Process large outputs in sandboxed subprocesses, 98% context savings |
| NotebookLM skill (ArtemXTech) for Obsidian import | Section 3 | NO | Import NotebookLM notebooks into Obsidian as knowledge graphs |
| agentskills.io standard | Section 7 | NO | Open standard for portable skills across 30+ tools |
| hermes-agent FTS5 session search | Section 5 | NO | Full-text search across past conversations |
| gitagent SkillsFlow for deterministic workflows | Section 7 | NO | YAML-based deterministic multi-step workflows |
| gitagent import/export for 10+ formats | Section 7 | YES | Spec Section 12.3 covers gitagent |
| test-driven-development skill (obra/superpowers) | Section 2 | NO | Not mentioned in spec |
| using-git-worktrees skill (obra/superpowers) | Section 2 | NO | Not mentioned in spec |
| finishing-a-development-branch skill (obra/superpowers) | Section 2 | NO | Referenced in project but not in migration spec |
| brainstorming skill (obra/superpowers) | Section 2 | NO | Not mentioned in spec |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| recall + sync-claude-sessions Obsidian plugins | HIGH | Install for Obsidian cross-session continuity; add to Phase 5 of migration |
| plugin-dashboard observability | MEDIUM | Install to track which tools/plugins are actually used vs dormant |
| root-cause-tracing skill | MEDIUM | Install from obra/superpowers for systematic debugging |
| test-driven-development skill | MEDIUM | Install from obra/superpowers |
| context-mode plugin for large outputs | MEDIUM | 98% context savings for large outputs; evaluate for research agent |
| kaizen continuous improvement skill | LOW | Evaluate for alignment with self-improving research pipeline |
| agentskills.io standard compliance | LOW | Ensure our skills follow the agentskills.io SKILL.md format |
| NotebookLM -> Obsidian import skill | LOW | Useful for consolidation workflow |

---

## 8. anthropic-official-complete.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| pyright-lsp plugin | Section 3 | PARTIAL | Listed as "consider" but deferred |
| skill-creator plugin | Section 3 | PARTIAL | Listed as "consider" but deferred |
| hookify plugin | Section 3 | PARTIAL | Listed as "consider" but deferred |
| claude-code-setup plugin | Section 3 | NO | Project configuration helper not mentioned |
| claude-md-management plugin | Section 3 | NO | CLAUDE.md management plugin not mentioned |
| code-review plugin | Section 3 | NO | Code review automation plugin not mentioned |
| ralph-loop plugin | Section 3 | NO | Autonomous agent loop pattern |
| commit-commands plugin | Section 3 | NO | Git commit slash commands |
| pr-review-toolkit plugin | Section 3 | NO | PR review tools |
| feature-dev plugin | Section 3 | NO | Feature development workflow |
| security-guidance plugin | Section 3 | NO | Security best practices plugin |
| Agent SDK @tool decorator | Section 2 | NO | Custom in-process MCP tools via Python |
| Agent SDK HookMatcher | Section 2 | NO | Python-native hook matching |
| Agent SDK ClaudeSDKClient | Section 2 | NO | Bidirectional interactive conversation client |
| Agent SDK create_sdk_mcp_server | Section 2 | NO | In-process MCP server creation |
| Anthropic cookbook: sub-agents recipe | Section 4 | NO | Multi-agent patterns cookbook not referenced |
| Anthropic cookbook: automated evaluations | Section 4 | NO | Eval patterns not referenced |
| Anthropic cookbook: prompt caching | Section 4 | NO | Performance optimization not referenced |
| C compiler parallel agent pattern (file-locking task claims) | Section 6B | NO | Git-based file locking for task coordination across parallel agents |
| C compiler multiple agent roles pattern | Section 6B | NO | One agent per concern: coalesce, optimize, quality critique, document |
| `--fast` test sampling for agent test harnesses | Section 6B | NO | 1% or 10% random test sampling for quick validation |
| 14 unfetched URLs from this review | Section 9 | NO | 14 Claude platform/engineering URLs never fetched |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| Install pyright-lsp during migration (not defer) | HIGH | Python type checking integration is directly relevant |
| Install security-guidance plugin | MEDIUM | Security best practices are always relevant |
| `--fast` test sampling | MEDIUM | Add `--fast` flag to `uv run mde-py validate` for quick agent validation |
| 14 unfetched URLs | MEDIUM | Add to source catalog for cycle 3 research |
| Agent SDK patterns | LOW | Not needed until building custom agents |

---

## 9. agent-file-schemas-and-generation.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| No official JSON Schema for agent frontmatter | Part 1.1 | YES | Spec Section 12.1 documents this |
| Derived JSON Schema (Approach A) | Part 3.1 | YES | Spec Section 12.2 covers this |
| gitagent as validation hub | Part 3.1 | YES | Spec Section 12.3 covers this |
| PostToolUse hook for real-time validation | Part 3.2 | YES | Spec Section 12.4 covers this |
| Pre-commit hook for frontmatter validation | Part 3.2 | YES | Spec Section 12.5 covers this |
| Weekly schema drift detection | Part 3.4 | YES | Spec Section 12.6 covers this |
| `skills-ref validate` for SKILL.md validation | Part 1.5 | NO | agentskills.io validator for skill files |
| Claude Code `/agents` interactive command | Part 1.2 | NO | Interactive agent creation UI not mentioned in spec |
| `--agents` CLI flag for session-only agents | Part 1.4 | NO | JSON-defined session-only agents |
| Agent SDK `AgentDefinition` dataclass gaps | Part 1.3 | NO | SDK missing 8+ fields that file-based frontmatter supports |
| Cross-framework format comparison (6 frameworks) | Part 2 | NO | Comparison table not in spec |
| gitagent `extends` for inheritance | Appendix B | NO | Agent inheritance via git URL |
| gitagent `delegation.mode` (auto/explicit/router) | Appendix B | NO | Delegation strategy configuration |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| `skills-ref validate` for our skills | MEDIUM | Install skills-ref and validate our SKILL.md files |
| `--agents` CLI flag documentation | LOW | Document in CLAUDE.md for ad-hoc agent testing |

---

## 10. chezmoi-mise-dotfiles-skills.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| mde-chezmoi-dotfiles skill | Section 5.1 | YES | Spec Section 13.2 covers this |
| mde-dotfiles-lifecycle skill | Section 5.1 | YES | Spec Section 13.3 covers this |
| mise-tool-management chezmoi cross-ref | Section 5.2 | YES | Spec Section 13.4 covers this |
| mise-enforcement chezmoi awareness | Section 5.2 | YES | Spec Section 13.4 covers this |
| Skill registry updates | Section 5.4 | YES | Spec Section 13.5 covers this |
| martinemde/dotfiles patterns | Section 7 | YES | Spec Section 13.6 covers this |
| mde-dotfiles-drift unified drift detection skill | Section 5.1 | NO | Unified chezmoi + mise drift detection skill |
| znap vs oh-my-zsh evaluation | Section 7.2 | NO | Performance evaluation of shell plugin managers |
| chezmoi `source guide` / `source fulltext` / `source rename` commands | Section 2.2 | NO | Advanced chezmoi commands not documented in skills |
| chezmoi externals for plugin management | Section 4.1 | NO | Pulling external repos/archives into dotfiles |
| Shell startup benchmarking (`time zsh -i -c exit`) | Section 7.3 | PARTIAL | Mentioned in spec Section 13.3 but not as a validation step |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| mde-dotfiles-drift skill | MEDIUM | Create unified drift detection skill or extend validation module |
| Shell startup benchmarking as validation step | LOW | Add `time zsh -i -c exit` to mde-py validate suite |
| znap evaluation | LOW | Separate research task |

---

## 11. specialized-agent-teams-patterns.md

| Feature/Technique/Tool/Skill | Source Section | In Spec? | Gap Description |
|------------------------------|---------------|----------|-----------------|
| 4 team templates (research, python, dotfiles, infra) | Section 3 | YES | Spec Section 14.2 covers this |
| Team spawn recipe skills | Section 4 | YES | Spec Section 14.3 covers this |
| Quality gate hooks per team type | Section 6 | YES | Spec Section 14.4 covers this |
| File-ownership decomposition strategies | Section 5 | YES | Spec Section 14.5 covers this |
| When to use teams vs subagents vs /batch | Section 9 | YES | Spec Section 14.6 covers this |
| `teammateMode` setting | Section 1 | YES | Spec Section 14.1 covers this |
| Competing hypotheses debugging pattern | Section 4 | NO | Spawn 4 agents with different hypotheses, have them challenge each other |
| Cross-layer feature implementation pattern | Section 4 | NO | Backend/CLI/integration/tests decomposition |
| Phased team with explicit dependencies | Section 4 | NO | Phase 1 (parallel) -> Phase 2 (dependent) -> Phase 3 (dependent) |
| Plan approval gate for complex tasks | Section 6 | NO | Require plan approval before teammates implement |
| Subagent definitions as team building blocks | Section 8 | NO | Define specialized subagents that teams reference |
| `--agents` CLI flag for reproducible teams | Section 8 | NO | JSON-defined teams for automation |
| Recommended additional subagent files (research-fetcher, python-implementer, etc.) | Section 8 | NO | 9 additional subagent definitions beyond the 4 in spec |
| Model routing table by role | Section 10 | PARTIAL | Spec mentions models per agent but no explicit routing table |
| Token cost management guidelines | Section 10 | NO | Guidelines for managing agent team costs |

**Priority gaps from this document:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| 9 additional subagent definitions (research-fetcher, python-implementer, etc.) | HIGH | Add these as reusable building blocks for agent teams |
| Competing hypotheses debugging pattern | MEDIUM | Add as a debugging skill or document in CLAUDE.md |
| Plan approval gate documentation | MEDIUM | Document in team spawn skills |
| Token cost management guidelines | LOW | Add to context-budget.md rule |

---

## 12. Cycle 1 YAML Findings

| Finding | In Spec? | Gap Description |
|---------|----------|-----------------|
| finding-gstack-skill-chaining | YES | Spec pattern #10 |
| finding-autoresearch-history-logging | PARTIAL | Spec has score-history.tsv but not ScoreHistory dataclass or binary gate wiring |
| finding-aris-checkpoint-state | YES | Spec pattern #5 |
| finding-compound-confidence-taxonomy | YES | Spec pattern #7, #8 |
| finding-claude-mem-3layer | YES | Spec pattern #1 |
| finding-orchestrator-ci-feedback | NO | CI-failure-to-agent routing with retry and escalation not in spec |
| finding-mcp2cli-token-savings | YES | Spec pattern #2, #3 |
| finding-amplihack-eval-ladder | NO | L1-L12 adapted for research not in spec |
| finding-claude-native-redundancy | YES | Entire spec is this migration |

**Priority gaps from findings:**

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| CI-failure-to-agent routing | MEDIUM | Add to finishing-a-development-branch skill: after PR check failure, extract log, retry with agent |
| ScoreHistory dataclass with per-metric breakdown | MEDIUM | Enhance score-history.tsv to include per-metric columns |
| Binary gate wiring in calculate_score() | MEDIUM | Wire BinaryGate checks to return 0.0 on failure |
| L1-L12 adapted for research pipeline | LOW | Future eval framework for research quality |

---

## 13. Tools to Install (Missing from Migration Checklist)

| Tool | Source | Current Spec Status | Priority | Recommendation |
|------|--------|-------------------|----------|----------------|
| mcp2cli | claude-mem-mcp2cli-amplihack | In Phase 5 (bake configs) | COVERED | Already in spec |
| gitagent | agent-file-schemas | In Phase 3 (step 13a) | COVERED | Already in spec |
| pyright-lsp plugin | anthropic-official | Deferred to post-migration | HIGH | Install during Phase 4 |
| security-guidance plugin | anthropic-official | Not mentioned | MEDIUM | Add to Phase 4 |
| recall plugin (ArtemXTech) | skill-plugin-ecosystem | Pattern #27 identified but not in checklist | HIGH | Add to Phase 5 |
| sync-claude-sessions plugin (ArtemXTech) | skill-plugin-ecosystem | Pattern #27 identified but not in checklist | HIGH | Add to Phase 5 |
| plugin-dashboard (amanaiproduct) | skill-plugin-ecosystem | Not mentioned | MEDIUM | Add to Phase 4 for observability |
| root-cause-tracing skill (obra/superpowers) | skill-plugin-ecosystem | Not mentioned | MEDIUM | Install to user-level skills |
| test-driven-development skill (obra/superpowers) | skill-plugin-ecosystem | Not mentioned | MEDIUM | Install to user-level skills |
| skills-ref validator | agent-file-schemas | Not mentioned | LOW | Install for SKILL.md validation |
| context-mode plugin | skill-plugin-ecosystem | Not mentioned | LOW | Evaluate for large output processing |

---

## 14. Skills to Preload into Agents (Missing from Spec)

The spec defines `skills: [agent-fetch]` for researcher, coder, and reviewer agents. The following skills from our research are not mapped:

| Skill | Relevant Agent | Source | Priority |
|-------|---------------|--------|----------|
| agent-fetch | researcher, coder, reviewer | Already in spec | COVERED |
| root-cause-tracing | coder, tester | obra/superpowers | MEDIUM |
| test-driven-development | tester | obra/superpowers | MEDIUM |
| dev | coder | existing project skill | HIGH |
| finishing-a-development-branch | coder | existing project skill | MEDIUM |
| mde-chezmoi-dotfiles | coder | new skill (spec Section 13.2) | MEDIUM |
| mise-tool-management | coder | existing project skill | MEDIUM |

---

## 15. Hooks Missing from Spec

The spec defines 6 hooks (PreToolUse[Bash], PostToolUse[Write|Edit], SubagentStart, SubagentStop, Stop, PreCompact). The following discovered hooks are not in the spec:

| Hook Event | Purpose | Source | Priority |
|------------|---------|--------|----------|
| SessionStart | Read git log, set env vars, restore state | claude-code-native Section 4 | HIGH |
| PostCompact | Re-read RESEARCH_STATE.json after compaction | claude-code-native Section 4 | MEDIUM |
| PostToolUseFailure | Log failed tool calls for debugging | claude-code-native Section 4 | LOW |
| WorktreeCreate | Initialize worktree with symlinks | claude-code-native Section 4 | LOW |
| InstructionsLoaded | Validate loaded rules | claude-code-native Section 4 | LOW |

---

## 16. Sources to Add to Catalog

URLs discovered in deep reviews but not in `docs/research/source-catalog.md`:

| URL | Source Document | Priority |
|-----|----------------|----------|
| https://platform.claude.com/docs/en/agent-sdk/python | anthropic-official | HIGH |
| https://platform.claude.com/docs/en/agent-sdk/hooks | anthropic-official | HIGH |
| https://platform.claude.com/docs/en/agent-sdk/permissions | anthropic-official | HIGH |
| https://agentskills.io | agent-file-schemas | HIGH |
| https://agentskills.io/specification | agent-file-schemas | HIGH |
| https://platform.claude.com/cookbook/patterns-agents-basic-workflows | anthropic-official | MEDIUM |
| https://platform.claude.com/cookbook/tool-use-memory-cookbook | anthropic-official | MEDIUM |
| https://docs.claude.com/en/api/skills-guide | anthropic-official | MEDIUM |
| https://www.anthropic.com/engineering/writing-tools-for-agents | anthropic-official | MEDIUM |
| https://www.anthropic.com/engineering/multi-agent-research-system | anthropic-official | MEDIUM |
| https://www.anthropic.com/engineering/claude-code-sandboxing | anthropic-official | LOW |
| https://www.anthropic.com/engineering/code-execution-with-mcp | anthropic-official | LOW |
| https://www.anthropic.com/engineering/advanced-tool-use | anthropic-official | LOW |
| https://www.anthropic.com/engineering/claude-think-tool | anthropic-official | LOW |
| https://github.com/anthropics/claudes-c-compiler | anthropic-official | LOW |
| https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding | anthropic-official | LOW |
| https://clau.de/plugin-directory-submission | anthropic-official | LOW |
| https://github.com/ArtemXTech/personal-os-skills | skill-plugin-ecosystem | MEDIUM |
| https://github.com/NousResearch/hermes-agent | skill-plugin-ecosystem | LOW |
| https://github.com/amanaiproduct/amans-skills | skill-plugin-ecosystem | LOW |
| https://github.com/NeoLabHQ/context-engineering-kit | skill-plugin-ecosystem | LOW |

---

## 17. Summary: All Gaps by Priority

### HIGH Priority (14 gaps)

1. **Install pyright-lsp plugin during migration** -- Python type checking is directly relevant (anthropic-official)
2. **Install recall + sync-claude-sessions Obsidian plugins** -- Cross-session continuity (skill-plugin-ecosystem)
3. **Add SessionStart hook** -- Read git log, restore RESEARCH_STATE.json, set env vars (claude-code-native)
4. **Use @import syntax in CLAUDE.md** -- Import key references without copying content (claude-code-native)
5. **Document /batch skill in CLAUDE.md** -- Built-in parallel decomposition (claude-code-native)
6. **Add `context: fork` + `agent` to team spawn skills** -- Run skills in isolated subagent context (claude-code-native)
7. **Create 9 additional subagent definitions** -- research-fetcher, python-implementer, python-tester, python-reviewer, research-synthesizer, mise-specialist, chezmoi-specialist, security-auditor, validator (specialized-agent-teams)
8. **Add mcp2cli `--search` to mcp-access.md rule** -- Pattern filtering for large MCP servers (mcp2cli)
9. **Add `dev` skill to coder.md skills list** -- Existing project skill not mapped (project)
10. **Add unfetched URLs to source catalog** -- 21 URLs discovered but not cataloged (all sources)
11. **Wire binary gates in calculate_score()** -- Return 0.0 on gate failure (finding-autoresearch-history-logging)
12. **Add ScoreHistory with per-metric breakdown** -- Enhance score-history.tsv (finding-autoresearch-history-logging)
13. **Install security-guidance plugin** -- Security best practices (anthropic-official)
14. **Add CI-failure-to-agent routing** -- After PR check failure, retry with agent (finding-orchestrator-ci-feedback)

### MEDIUM Priority (20 gaps)

1. Add consolidation step to research pipeline (agent-note-persistence)
2. Add PostCompact hook to re-read RESEARCH_STATE.json (claude-code-native)
3. Make SubagentStart/Stop hooks async (claude-code-native)
4. Add `allowed-tools` to skill frontmatter for team spawn skills (claude-code-native)
5. Use `permissionDecision` in PreToolUse hooks for guard-install (claude-code-native)
6. Add /investigate auto-freeze pattern as debugging skill (gstack)
7. Add /careful destructive command warning to guard-install hook (gstack)
8. Adopt AUTO_REVIEW.md cumulative log format for research cycles (aris-compound)
9. Add fix prioritization rules to researcher.md (aris-compound)
10. Add error taxonomy for research source failures (mcp2cli-amplihack)
11. Add mcp2cli `bake install` for standalone CLI creation (mcp2cli)
12. Add "NEVER STOP" autonomy instruction for research agents (orchestrator-autoresearch)
13. Install plugin-dashboard for tool observability (skill-plugin-ecosystem)
14. Install root-cause-tracing skill (skill-plugin-ecosystem)
15. Install test-driven-development skill (skill-plugin-ecosystem)
16. Add competing hypotheses debugging pattern (specialized-agent-teams)
17. Document plan approval gate in team spawn skills (specialized-agent-teams)
18. Add `--fast` test sampling to mde-py validate (anthropic-official)
19. Create mde-dotfiles-drift unified drift detection skill (chezmoi-mise-dotfiles)
20. Add skills-ref validation for SKILL.md files (agent-file-schemas)

### LOW Priority (19 gaps)

1. Add periodic deep review process to second-brain.md (agent-note-persistence)
2. Add NotebookLM `source guide` as optional tool (agent-note-persistence)
3. Add /freeze directory-scoped edit restriction skill (gstack)
4. Add proactive skill suggestions based on work stage (gstack)
5. Adopt staleness management (Keep/Update/Replace/Archive) (aris-compound)
6. Extend finding_type enum with learning types (aris-compound)
7. Add AUTO_PROCEED gate logic for automated research loops (aris-compound)
8. Add mcp2cli caching flags to mcp-access.md (mcp2cli)
9. Quantitative regression guard (+2% / >5%) for scores (mcp2cli-amplihack)
10. Git-branch-as-experiment-journal pattern (orchestrator-autoresearch)
11. Add token cost management guidelines to context-budget.md (specialized-agent-teams)
12. Install context-mode plugin for large outputs (skill-plugin-ecosystem)
13. Evaluate kaizen continuous improvement skill (skill-plugin-ecosystem)
14. Install NotebookLM -> Obsidian import skill (skill-plugin-ecosystem)
15. Ensure agentskills.io standard compliance (skill-plugin-ecosystem)
16. Add shell startup benchmarking to validation (chezmoi-mise-dotfiles)
17. Add PostToolUseFailure hook for debugging (claude-code-native)
18. Add worktree.symlinkDirectories to settings (claude-code-native)
19. L1-L12 adapted eval framework for research (finding-amplihack-eval-ladder)

---

## 18. Conclusion

The migration spec (Sections 1-15, 43 migration checklist items) covers **30 patterns** from the research and explicitly rejects **25 more**. However, this gap analysis identifies **53 additional items** that were discovered in the deep reviews but not accounted for in the spec:

- **14 HIGH priority**: Critical features and tools that should be adopted during migration
- **20 MEDIUM priority**: Valuable improvements to incorporate in the first post-migration cycle
- **19 LOW priority**: Nice-to-have features for future consideration

The most impactful categories of gaps are:

1. **Claude Code native features not utilized** (12 gaps from claude-code-native-complete.md): @import syntax, /batch, SessionStart hooks, PostCompact hooks, async hooks, context:fork for skills, ultrathink, skill frontmatter features
2. **Skills/plugins to install** (8 gaps): pyright-lsp, recall, sync-claude-sessions, security-guidance, plugin-dashboard, root-cause-tracing, test-driven-development, skills-ref
3. **Additional subagent definitions** (9 new agents needed for teams to function as designed)
4. **Research pipeline improvements** (5 gaps): consolidation step, error taxonomy, cumulative log format, autonomy instructions, CI-failure routing
5. **Uncataloged URLs** (21 URLs discovered but not in source-catalog.md)
