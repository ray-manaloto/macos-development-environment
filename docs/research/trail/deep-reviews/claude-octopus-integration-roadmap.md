# Claude Octopus Integration Roadmap for autonomous-fix-review

## Executive Summary

Claude Octopus (v9.13.0, MIT-licensed) is a mature, production-ready Claude Code plugin that implements exactly the consensus gate and multi-model orchestration needed for autonomous-fix-review. The plugin can be adapted rather than rebuilt.

**Verdict: ADAPT** — Extract consensus gate logic into the mde Python library; port shell orchestration to async Python with trio; integrate into the skill.

---

## Part 1: What Claude Octopus Gives Us (Free)

### 1.1 Consensus Gate Implementation

**Problem we're solving:** Prevent bad reviews from shipping by requiring agreement across multiple models.

**Claude Octopus solution:**

```bash
# From scripts/lib/quality.sh
evaluate_quality_branch() {
    local success_rate="$1"
    local autonomy="${3:-$AUTONOMY_MODE}"

    if [[ $success_rate -ge 90 ]]; then
        echo "proceed"  # Quality gate PASSED
    elif [[ $success_rate -ge $QUALITY_THRESHOLD ]]; then
        echo "proceed_warn"  # PASSED with warnings (default: 75%)
    elif [[ "$LOOP_UNTIL_APPROVED" == "true" && $retry_count -lt $MAX_QUALITY_RETRIES ]]; then
        echo "retry"  # Auto-retry enabled
    elif [[ "$autonomy" == "supervised" ]]; then
        echo "escalate"  # Human decision required
    else
        echo "abort"  # Failed, no retry
    fi
}
```

**Key features:**
- Configurable threshold (default 75%)
- Autonomy modes: `supervised` (escalate), `semi-autonomous` (retry), `autonomous` (proceed)
- Exit codes for downstream handling: 0 (proceed), 2 (retry), 1 (abort)
- Provider lockout to prevent infinite retry loops

**Directly reusable:** YES. Can be ported to Python/trio with minimal logic changes.

### 1.2 Adversarial Debate System

**From scripts/lib/debate.sh:**

```bash
grapple_debate() {
    local prompt="$1"
    local principles="${2:-general}"
    local rounds="${3:-3}"
    local debate_mode="${4:-cross-critique}"
```

**Two debate modes:**

1. **Cross-critique (ACH falsification)** — Each model sees competitors' proposals and rebuts
   - Round 1: Parallel proposal generation (Codex, Gemini, Claude)
   - Round 2: Cross-model critique with mandatory integrity rules
   - Round 3: Synthesis by Claude

2. **Blinded mode** — Independent evaluation without anchoring bias
   - Round 1: Parallel proposals
   - Round 2: Independent risk assessment (no cross-contamination)
   - Round 3: Synthesis

**Debate integrity rules (always-on):**
- **ANTI-CONTRARIAN:** Agree if approach is sound; cite specific technical evidence
- **ANTI-RUBBER-STAMP:** Disagree if flaw exists, even if approach is good overall
- **EVIDENCE-BASED:** Every claim must cite technical reason, not sentiment
- **PROPORTIONAL:** Calibrate severity honestly (minor style ≠ critical flaw)

**Directly reusable:** YES. Rules become system prompts in Python implementation.

### 1.3 Multi-Model Dispatch (CLI-Native)

**Key insight:** Claude Octopus uses subprocess dispatch, not APIs:

```bash
codex_output=$(run_agent_sync "codex" "$prompt" 120 "implementer" "grapple")
gemini_output=$(run_agent_sync "gemini" "$prompt" 120 "researcher" "grapple")
```

The `run_agent_sync` function (in agents.sh) dispatches to CLI tools:
- `codex exec --model gpt-5.4 --prompt "$prompt"`
- `gemini -y -m gemini-3.1-pro-preview "$prompt"`
- `claude --prompt "$prompt"` (built-in)

**Why this matters:** We can use codex/gemini CLIs (already installed) without API keys. Perfect for our zero-API-key constraint.

**Auth detection (preflight.sh):**
```bash
# Codex: tries ~/.codex/auth.json (OAuth) OR OPENAI_API_KEY
if command -v codex &>/dev/null; then
    if [[ -f "$HOME/.codex/auth.json" ]]; then
        CODEX_AUTH=oauth
    elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
        CODEX_AUTH=api-key
    else
        CODEX_AUTH=none  # ← Claude works alone
    fi
fi
```

**Directly reusable:** YES. We already have this pattern in mde; can adapt run_agent_sync to async.

### 1.4 Persona & Role Assignment

Claude Octopus ships with 32 personas (security-auditor, code-reviewer, architect, etc.). The debate system auto-assigns personas by context:

```bash
codex_proposal=$(run_agent_sync "codex" "$prompt" 120 "implementer" "grapple")
gemini_proposal=$(run_agent_sync "gemini" "$prompt" 120 "researcher" "grapple")
sonnet_critique=$(run_agent_sync "claude-sonnet" "$prompt" 120 "code-reviewer" "grapple")
```

The 4th parameter ("implementer", "researcher", "code-reviewer") selects the persona from `.claude/agents/*.md`.

**Directly reusable:** PARTIAL. We can adapt the persona selection logic; our existing specialist agents are a subset of octopus's 32.

---

## Part 2: What We Need to Adapt

### 2.1 Shell → Python/Async Port

**Current octopus design:** Synchronous bash orchestration with parallel jobs (`wait`, `&`)

**Our need:** Async Python with trio for:
- Better error handling (structured exceptions vs exit codes)
- Type safety (Pydantic models for debate rounds)
- Integration with mde CLI
- Testability (no subprocess mocking)

**Adaptation strategy:**

```python
# mde/orchestration/debate.py
import trio
from dataclasses import dataclass

@dataclass
class DebateProposal:
    model: str
    hypothesis: str
    assumptions: list[str]
    falsification_criteria: list[str]
    implementation: str

async def grapple_debate(
    prompt: str,
    principles: str = "general",
    rounds: int = 3,
    debate_mode: str = "cross-critique",
) -> tuple[DebateProposal, DebateProposal, DebateProposal]:
    """Adversarial 3-model debate with consensus scoring."""

    # 1. Parallel proposal generation
    async with trio.open_nursery() as nursery:
        codex_proposal = await run_model_debate_round(
            "codex", prompt, principles, "implementer"
        )
        gemini_proposal = await run_model_debate_round(
            "gemini", prompt, principles, "researcher"
        )
        claude_proposal = await run_model_debate_round(
            "claude", prompt, principles, "moderator"
        )

    # 2. Cross-critique or blinded evaluation
    if debate_mode == "cross-critique":
        critiques = await run_cross_critique(
            codex_proposal, gemini_proposal, claude_proposal
        )
    else:
        critiques = await run_blinded_evaluation(
            codex_proposal, gemini_proposal, claude_proposal
        )

    # 3. Synthesis & consensus scoring
    consensus_score = calculate_consensus_score(critiques)
    return consensus_score
```

### 2.2 Quality Gate Configuration

**Current octopus:** Hardcoded `QUALITY_THRESHOLD=75` in variables

**Our need:** Configurable per-workflow:

```python
# From mde/orchestration/quality.py
class QualityGate:
    def __init__(self, threshold: float = 0.75, autonomy: str = "semi-autonomous"):
        self.threshold = threshold  # 75% consensus required
        self.autonomy = autonomy     # supervised / semi-autonomous / autonomous
        self.max_retries = 3

    def evaluate(self, success_rate: float) -> str:
        """Returns: proceed, proceed_warn, retry, escalate, abort"""
        if success_rate >= 0.90:
            return "proceed"
        elif success_rate >= self.threshold:
            return "proceed_warn"
        elif self.autonomy == "semi-autonomous" and self.retries < self.max_retries:
            return "retry"
        elif self.autonomy == "supervised":
            return "escalate"
        else:
            return "abort"
```

### 2.3 Provider Detection & Subprocess Dispatch

**Current octopus:** Bash functions in lib/preflight.sh and lib/dispatch.sh

**Our need:** Python wrapper for subprocess dispatch:

```python
# From mde/orchestration/providers.py
import subprocess
from typing import Optional

class ModelProvider:
    def __init__(self, name: str, cli_cmd: str, auth_path: Optional[str] = None):
        self.name = name
        self.cli_cmd = cli_cmd  # "codex", "gemini", "claude"
        self.auth_path = auth_path

    async def execute(self, prompt: str, model: str, persona: str) -> str:
        """Dispatch to CLI tool via subprocess."""
        cmd = [self.cli_cmd, "exec", "--prompt", prompt]
        if model:
            cmd.extend(["--model", model])

        result = await trio_run_subprocess(cmd)
        if result.returncode != 0:
            raise ProviderError(f"{self.name} failed: {result.stderr}")
        return result.stdout

# Provider detection
def detect_providers() -> dict[str, ModelProvider]:
    """Auto-detect available providers (like octopus preflight.sh)."""
    providers = {}

    # Claude is always available
    providers["claude"] = ModelProvider("claude", "claude", auth_path=None)

    # Codex: check ~/.codex/auth.json OR OPENAI_API_KEY
    if shutil.which("codex") and (
        Path.home() / ".codex" / "auth.json"
    ).exists():
        providers["codex"] = ModelProvider("codex", "codex", auth_path=str(Path.home() / ".codex" / "auth.json"))

    # Gemini: check ~/.gemini/oauth_creds.json OR GEMINI_API_KEY
    if shutil.which("gemini") and (
        Path.home() / ".gemini" / "oauth_creds.json"
    ).exists():
        providers["gemini"] = ModelProvider("gemini", "gemini", auth_path=str(Path.home() / ".gemini" / "oauth_creds.json"))

    return providers
```

### 2.4 Persona Selection

**Current octopus:** Manual persona assignment in debate.sh:

```bash
codex_proposal=$(run_agent_sync "codex" "$prompt" 120 "implementer" "grapple")
gemini_proposal=$(run_agent_sync "gemini" "$prompt" 120 "researcher" "grapple")
claude_critique=$(run_agent_sync "claude" "$prompt" 120 "code-reviewer" "grapple")
```

**Our need:** Map octopus personas to mde specialist agents:

```python
# From mde/orchestration/personas.py
PERSONA_MAP = {
    # octopus → mde
    "implementer": "coder",
    "researcher": "researcher",
    "code-reviewer": "reviewer",
    "security-auditor": "security-auditor",
    "architect": "architect",
    # ... etc
}

def get_persona_for_context(context: str, role: str) -> str:
    """Map octopus personas to mde agents."""
    return PERSONA_MAP.get(role, "researcher")  # fallback
```

---

## Part 3: Integration Points

### 3.1 Into autonomous-fix-review Skill

Current skill structure:
```
autonomous-fix-review/
├── main.yaml          # Skill definition
├── impl.py            # Current implementation (sequential review)
├── agents.yaml        # Review agents
└── ...
```

With consensus gate:
```
autonomous-fix-review/
├── main.yaml          # Skill definition (add consensus_gate_enabled flag)
├── impl.py            # Call orchestration.debate.grapple_debate()
├── debate.py          # New: debate orchestration (from octopus port)
├── quality.py         # New: quality gate logic (from octopus port)
├── providers.py       # New: provider detection & dispatch
├── agents.yaml        # Link to coder/reviewer/security-auditor
└── ...
```

### 3.2 Into mde Python Library

```
src/mde/
├── orchestration/           # NEW: Multi-model orchestration
│   ├── __init__.py
│   ├── debate.py            # grapple_debate() - adversarial review
│   ├── quality.py           # QualityGate class - consensus threshold
│   ├── providers.py         # ModelProvider, detect_providers()
│   ├── personas.py          # Persona → agent mapping
│   └── integrity.py         # Debate integrity rules as prompts
└── ...
```

### 3.3 CLI Integration

```bash
# New subcommand: mde orchestrate
uv run mde-py orchestrate debate \
  --input <pr-url> \
  --models codex,gemini,claude \
  --rounds 3 \
  --threshold 0.75 \
  --autonomy semi-autonomous

# Output: JSON consensus report with per-model scores
```

---

## Part 4: Gaps & Open Questions

### 4.1 Can debate.sh Run Standalone?

**Question:** Does debate.sh have hard dependencies on orchestrate.sh's state variables?

**Answer required:** Need to verify:
- Does `run_agent_sync()` depend on global variables set in orchestrate.sh?
- Are there implicit dependencies on `$RESULTS_DIR`, `$LOGS_DIR`, etc.?

**Risk:** If dependencies exist, we need to either:
a) Port the entire orchestrate.sh context (bloat)
b) Extract run_agent_sync() to standalone lib (clean)

### 4.2 Threshold Configuration Stability

**Question:** Does changing `QUALITY_THRESHOLD` from 75 → 70 break any downstream logic?

**Answer required:** Check if any part of quality.sh or workflows.sh hardcodes the 75% threshold.

**Risk:** If hardcoded, we need to add indirection layer.

### 4.3 Persona Matching

**Question:** Do octopus's 32 personas map cleanly to our 5 specialist agents (coder, reviewer, security-auditor, researcher, architect)?

**Answer:** Partial overlap expected:
- "implementer" → coder ✓
- "code-reviewer" → reviewer ✓
- "security-auditor" → security-auditor ✓
- "ui-ux-designer" → (we don't have this, fallback to researcher)
- "product-manager" → (we don't have this, fallback to researcher)

**Mitigation:** Map unknown personas to "researcher" with a warning.

### 4.4 Shell to Async Port Complexity

**Question:** Will porting 400 LOC of bash debate.sh to Python/trio introduce bugs?

**Answer:** Mitigate with:
1. Property-based testing (compare bash vs Python outputs on same inputs)
2. Dry-run mode (execute logic without subprocess dispatch)
3. Gradual rollout (expert model first, then add Gemini/Claude)

---

## Part 5: Implementation Roadmap

### Phase 1: Setup & Scaffolding (Week 1)
- [ ] Read full debate.sh + quality.sh (400 LOC each)
- [ ] Verify standalone dependencies (are they clean?)
- [ ] Create mde/orchestration/ module structure
- [ ] Write Pydantic models for debate rounds, consensus scores

### Phase 2: Core Porting (Week 2)
- [ ] Port quality.py (simpler, ~100 LOC Python)
- [ ] Port providers.py (provider detection + subprocess dispatch)
- [ ] Port personas.py (persona → agent mapping)
- [ ] Write unit tests (no subprocess mocking yet)

### Phase 3: Debate Orchestration (Week 3)
- [ ] Port debate.py with trio parallelism
- [ ] Implement debate integrity rule prompts
- [ ] Add dry-run mode (no subprocess dispatch)
- [ ] Write integration tests vs octopus (bash reference impl)

### Phase 4: Skill Integration (Week 4)
- [ ] Update autonomous-fix-review/impl.py to call debate.py
- [ ] Add consensus_gate_enabled flag to skill config
- [ ] Write CLI subcommand: mde orchestrate debate
- [ ] Test on live PR with codex + gemini CLIs

### Phase 5: Documentation & Release (Week 5)
- [ ] Document debate integrity rules
- [ ] Document persona mapping
- [ ] Update CLAUDE.md with consensus gate policy
- [ ] Tag v0.1.0 of mde.orchestration module

---

## Part 6: Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Bash → Python port introduces subtle bugs | Property-based testing vs octopus reference | Coder |
| Provider detection doesn't work with subscription CLIs | Integration test on real codex/gemini installs | Coder |
| Debate rounds timeout (long prompts) | Configurable timeout, default 600s (octopus uses) | Coder |
| Quality gate threshold not configurable per-workflow | Config inheritance: skill level → gate level | Coder |
| Consensus score calculation is opaque | Document scoring formula in code + README | Coder |
| Persona mapping misses edge cases | Fallback to researcher, log warnings | Coder |

---

## Part 7: Success Criteria

- [ ] debate.py passes property-based tests vs octopus bash (same inputs → same decisions)
- [ ] quality.py handles all autonomy modes (supervised/semi-autonomous/autonomous)
- [ ] providers.py detects codex/gemini CLIs correctly (zero false positives/negatives)
- [ ] autonomous-fix-review skill uses consensus gate on 75% threshold by default
- [ ] CLI command: `mde orchestrate debate` runs without errors on test PR
- [ ] Documentation lists debate integrity rules and persona mapping
- [ ] No breaking changes to existing skill APIs

---

## Appendix: Claude Octopus Architecture Map

**Files we need to extract:**
```
scripts/lib/debate.sh              ← grapple_debate() function
scripts/lib/quality.sh             ← QualityGate logic, thresholds
scripts/lib/providers.sh           ← Provider detection
scripts/lib/agents.sh              ← run_agent_sync() dispatcher
scripts/lib/personas.sh            ← Persona definitions
docs/AGENTS.md                     ← 32 persona descriptions
docs/ARCHITECTURE.md               ← Double Diamond methodology
```

**Files we can skip:**
```
scripts/lib/factory.sh             ← Dark Factory mode (not needed)
scripts/lib/sentinel.sh            ← Reaction engine (separate feature)
mcp-server/                        ← OpenClaw compatibility (not needed)
openclaw/                          ← OpenClaw extension (not needed)
docs/COMMAND-REFERENCE.md          ← Full octopus CLI (we only need debate)
```

**Total extraction:** ~800 LOC of bash → ~500 LOC of Python (with better structure)

---

## References

- Claude Octopus GitHub: https://github.com/nyldn/claude-octopus
- README (consensus gate details): https://raw.githubusercontent.com/nyldn/claude-octopus/main/README.md
- debate.sh (source code): https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/debate.sh
- quality.sh (source code): https://raw.githubusercontent.com/nyldn/claude-octopus/main/scripts/lib/quality.sh
- ARCHITECTURE.md (methodology): https://raw.githubusercontent.com/nyldn/claude-octopus/main/docs/ARCHITECTURE.md

