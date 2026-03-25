# Cross-Model Review Methodology

**Date:** 2026-03-24
**Purpose:** Reusable methodology for sending specs/docs to multiple AI models for independent adversarial review.

---

## CLI Tools Used

### OpenAI Codex CLI (v0.116.0)
- **Binary:** `/Users/rmanaloto/.local/share/mise/installs/codex/0.116.0/codex`
- **Non-interactive mode:** `codex exec` subcommand
- **Model used:** GPT-5.4 (default)

### Google Gemini CLI (v0.34.0)
- **Binary:** `/Users/rmanaloto/.local/share/mise/installs/gemini-cli/0.34.0/bin/gemini`
- **Non-interactive mode:** `-p` / `--prompt` flag
- **Model used:** gemini-3-flash-preview (default)

---

## Exact Commands That Work

### Codex CLI

```bash
# Pipe document content + review prompt via stdin
cat <spec-file> <prompt-file> | codex exec -c 'sandbox_permissions=["disk-full-read-access"]' -

# Key flags:
# exec           - non-interactive mode (runs and exits)
# -              - read prompt from stdin (when no PROMPT arg given)
# -c 'sandbox_permissions=["disk-full-read-access"]'  - allow reading repo files
# -m <model>     - override model (optional)
```

**Behavior notes:**
- Codex has full repo context (reads CLAUDE.md equivalents, skills, and project files)
- It runs shell commands to validate claims (e.g., `which ffmpeg`, `mise registry | rg ...`)
- It loads skills from `.codex/skills/` and `.agents/skills/`
- MCP servers configured in `config.toml` are started (some may fail; non-blocking)
- Output includes intermediate tool calls and reasoning before final findings
- Token usage reported at end (117,810 tokens for this review)
- Startup time: ~15-30 seconds (MCP server initialization)

### Gemini CLI

```bash
# Pipe document via stdin, prompt via -p flag
cat <spec-file> | gemini -p "$(cat <prompt-file>)" --sandbox

# Key flags:
# -p "<prompt>"  - non-interactive/headless mode
# --sandbox      - run in sandbox mode for safety
# -m <model>     - override model (optional)
# -o text        - force text output format (optional)
```

**Behavior notes:**
- Gemini loads extensions from `~/.gemini/extensions/` (can be slow)
- Many MCP servers may fail during startup; these are non-blocking warnings
- Skill conflicts logged but non-fatal
- OpenTelemetry export timeouts at shutdown are cosmetic
- Output is inline (no separate tool calls visible in non-interactive mode)
- Session hooks fire at end (SessionEnd)
- Startup time: ~20-40 seconds (extension loading + MCP init)

---

## Prompt Structure for Adversarial Review

### Template (save as `/tmp/review-prompt.txt`)

```
You are an adversarial technical reviewer. Read this spec for [DOMAIN]. Find ALL problems:
1. Claims without evidence
2. Missing error handling and failure modes
3. Tool compatibility issues (especially [TARGET PLATFORM])
4. Security concerns ([DOMAIN-SPECIFIC RISKS])
5. Missing edge cases ([LIST SPECIFIC CASES])
6. Vague specifications that can't be implemented
7. Missing dependency version pins
8. Resource consumption concerns (disk space, memory, API rate limits)
9. Missing rollback/cleanup procedures
10. Assumptions about system state or available tools

Be harsh and specific. Rate each finding as CRITICAL/HIGH/MEDIUM/LOW. Output your findings as a numbered list with the format:
[SEVERITY] Finding title: Description of the problem and why it matters.
```

### Key prompt design principles:
- **Explicit severity ratings** - forces structured output instead of prose
- **Numbered checklist** - ensures coverage of common blind spots
- **"Be harsh and specific"** - counteracts model politeness bias
- **Domain-specific risks** - customize items 4-5 for the review domain
- **Platform callout** - ensures hardware/OS compatibility is checked

---

## Consolidation Process

### Step 1: Run reviews in parallel
Both CLIs can run simultaneously since they are independent processes.

### Step 2: Extract findings
- Codex: findings appear after tool execution, in a numbered list at the end
- Gemini: findings appear inline as the response body

### Step 3: Deduplicate and merge
1. List all findings from both models
2. Group by topic (security, compatibility, resource, etc.)
3. When both models flag the same issue, note agreement and use the higher severity
4. When only one model flags an issue, note which model and why (repo context vs external knowledge)

### Step 4: Agreement analysis
Create a table showing which findings each model identified. Strong agreement between models on a finding increases confidence. Disagreements highlight model-specific strengths:
- **Codex advantage:** Reads repo files, validates against existing decisions, runs commands to check system state
- **Gemini advantage:** Broader knowledge of library compatibility, faster at surface-level analysis

---

## Limitations

### Codex CLI
- MCP server startup failures can be noisy (non-blocking but verbose)
- Skills must exist at expected paths or errors are logged
- Sandbox permissions must be explicitly granted for file reads
- Token cost is substantial (~118K tokens for a 313-line spec review)
- Cannot easily control which repo files it reads (may read irrelevant context)

### Gemini CLI
- Extension loading is slow and noisy (~20-40s startup)
- OpenTelemetry export timeouts at shutdown (cosmetic but confusing)
- MCP server failures logged as errors even when non-blocking
- Less depth than Codex (12 vs 30 findings for same spec)
- Does not validate claims against repo state (no shell command execution observed in headless mode)

### Both
- Neither model can verify external URLs (e.g., whether a GitHub repo actually exists)
- Both are limited by training data cutoff for library version accuracy
- Neither performs actual installation testing
- Review quality depends heavily on prompt specificity

---

## Recommendations for Future Use

1. **Always run both models** - they find different things due to different context access
2. **Customize the prompt** - generic prompts produce generic findings; domain-specific checklists improve coverage
3. **Give Codex repo context** - its ability to validate claims against existing code/decisions is its primary advantage
4. **Use Gemini for breadth** - it covers common issues quickly even without repo context
5. **Budget 3-5 minutes** per model for startup + review of a ~300-line spec
6. **Save raw outputs** - the intermediate reasoning (especially Codex tool calls) contains valuable verification evidence
