---
name: Multi-model CLI orchestration finding
description: Python subprocess wrapper is the only viable approach for orchestrating codex/gemini/claude CLIs with subscription auth
type: reference
---

**Key Discovery**: No Python library can orchestrate heterogeneous LLM backends (CodeX + Gemini + Claude) while preserving subscription-based authentication.

**Why frameworks don't work**:
- DSPy, BAML, LiteLLM, Instructor, PydanticAI all require programmatic API keys
- claude-agent-sdk only spawns Claude agents (no CodeX/Gemini support)
- openai-agents only spawns OpenAI agents

**Why subprocess wrapper IS viable**:
- All three CLIs installed via mise (0.116.0, 0.34.0, 2.1.81)
- CLI signatures support non-interactive modes (-p/--print/--prompt, exec, review)
- Subscription auth works correctly via system env/keychain
- Zero new dependencies (stdlib subprocess)
- Protocol-based design enables future expansion

**Recommendation**: Build thin wrapper in src/mde/domain/multi_model.py
- Pattern: CodeReviewer protocol + implementations per CLI
- Type-safe: Pydantic ReviewResult dataclass
- Supports adversarial review via consensus voting across three models
- Follows mde library-first policy (assemble, don't build)

**Finding file**: `/Users/rmanaloto/dev/github/ray-manaloto/macos-development-environment/docs/research/trail/findings/cli-orchestration-sdk-independent-2026-03-24.yaml`

**Source catalog entries**: 3 CLI tools + 5 framework evaluations added 2026-03-24
