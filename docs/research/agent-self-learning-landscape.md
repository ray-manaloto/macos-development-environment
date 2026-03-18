# Agent Self-Learning Landscape: A Comparative Analysis of 14 Frameworks

Status: Final Draft
Created: 2026-03-17
Scope: Self-learning, memory management, and auto-optimization across agent frameworks

---

## 1. Executive Summary

"Self-learning" in agent frameworks as of early 2026 spans a wide spectrum, from simple conversation memory to genuine iterative self-improvement. At the most basic level, frameworks persist past interactions so agents avoid repeating mistakes. At the most advanced, systems like DSPy perform automatic prompt optimization by evaluating outputs against metrics and rewriting their own instructions.

The core mechanisms observed across frameworks fall into five categories:

- **Experience replay**: Storing task outcomes (success/failure, approach taken, context) and retrieving relevant experiences before starting new tasks. This is the most common form of "learning" and is present in most frameworks that claim memory support.
- **Pattern extraction**: Moving beyond raw experience storage to distill reusable patterns — e.g., "when the user asks for X, tool Y with prompt Z produces the best results." Few frameworks do this automatically; most require manual curation.
- **Reflection loops**: Having agents evaluate their own outputs, identify errors, and retry with corrections. AutoGen and DSPy implement this most explicitly. CrewAI supports it through agent delegation chains.
- **Memory management**: Deciding what to remember, what to forget, and how to organize knowledge. Letta/MemGPT is the standout here, implementing explicit memory tiers analogous to operating system memory hierarchies.
- **Prompt optimization**: Automatically tuning prompts based on accumulated performance data. DSPy is the only framework with a mature implementation of this. Claude-flow's neural training hooks are conceptually similar but less proven at scale.

The honest assessment is that most frameworks are still early in true self-improvement. The majority offer persistence (saving state between runs) and retrieval (searching past context), but genuine closed-loop learning — where the system measurably improves its own performance over time without human intervention — remains rare. DSPy and Letta/MemGPT are the furthest along, with different approaches: DSPy optimizes the program (prompts and pipelines), while Letta optimizes the memory (what context to surface when).

For this project (MDE with claude-flow), the most actionable insights come from DSPy's metric-driven optimization, Letta's tiered memory architecture, and LangGraph's robust checkpointing. The gap between claude-flow's current hooks-based learning and these mature implementations is significant but bridgeable with targeted improvements.

---

## 2. Framework Analysis

### 2.1 claude-flow (ruvnet/claude-flow)

- **Memory Architecture**: Hybrid — HNSW-indexed vector store for semantic search, key-value store for named patterns, SQLite-backed persistence. Supports namespaces for organizing patterns, solutions, and tasks separately.
- **Learning Mechanisms**: Pre-task/post-task hooks that can store and retrieve patterns automatically. Neural pattern training via the RuVector intelligence system (SONA, MoE, EWC++). Background workers for consolidation and optimization. The learning pipeline exists architecturally but depends on the orchestrating agent (Claude Code) to actually invoke the hooks consistently.
- **Persistence Model**: Per-project with session save/restore. Memory persists in local SQLite databases. Cross-project transfer is supported via IPFS registry but is not widely used.
- **Auto-optimization Features**: Model routing via hooks (Haiku/Sonnet/Opus tier selection), agent booster for simple transforms, coverage-aware routing. Neural prediction for task approaches. The infrastructure is comprehensive; actual closed-loop improvement depends on consistent hook invocation.

### 2.2 LangGraph (langchain-ai/langgraph)

- **Memory Architecture**: Checkpointer-based persistence with pluggable backends (SQLite, Postgres, Redis). Memory is graph-state-centric — each node in the execution graph can read/write state. LangGraph Platform adds a managed memory store with semantic search.
- **Learning Mechanisms**: No built-in self-learning. Learning must be implemented as custom graph nodes. The checkpointing system enables "time travel" (replaying from any state), which is a building block for experience replay but requires custom implementation.
- **Persistence Model**: Per-thread (conversation) and per-checkpoint. Cross-session via the LangGraph Platform's managed store. State is serialized at every step, enabling robust recovery.
- **Auto-optimization Features**: None built-in. Tool selection and routing are manual. LangSmith integration provides observability but not automatic optimization.

### 2.3 CrewAI (crewAIInc/crewAI)

- **Memory Architecture**: Short-term (conversation context), long-term (SQLite with RAG), entity memory (structured knowledge about entities), and user memory. Uses embeddings for retrieval.
- **Learning Mechanisms**: Long-term memory stores task outcomes with metadata. Before new tasks, agents can search for relevant past experiences. Delegation chains allow agents to reflect by consulting other agents. No automatic prompt tuning.
- **Persistence Model**: Per-crew, file-based. Long-term memory persists across crew runs. Knowledge sources can be added as static context (PDFs, text files).
- **Auto-optimization Features**: Task delegation to specialized agents is a form of auto-routing. No self-optimization of prompts or tool selection.

### 2.4 AutoGen (microsoft/autogen)

- **Memory Architecture**: Conversation-based — agents share a message history. AutoGen 0.4+ (AgentChat) supports pluggable memory with a `ChatMemory` protocol. Mem0 integration provides vector-indexed long-term memory.
- **Learning Mechanisms**: Multi-agent conversation inherently creates reflection loops — a critic agent can evaluate a coder agent's output. Teachability extension allows agents to learn facts from conversations. No automatic pattern extraction.
- **Persistence Model**: Conversation state can be serialized. Long-term memory via external integrations (Mem0, ChromaDB). No built-in cross-session persistence in the core library.
- **Auto-optimization Features**: Model selection per agent. No automatic prompt optimization or tool selection learning.

### 2.5 DSPy (stanfordnlp/dspy)

- **Memory Architecture**: Not memory-focused per se. DSPy programs are declarative pipelines of modules. State is in the compiled program (optimized prompts and few-shot examples) rather than in a runtime memory store.
- **Learning Mechanisms**: This is DSPy's strength. Optimizers (formerly "teleprompters") automatically tune prompts by: generating candidate prompts, evaluating them against metrics on a training set, and selecting the best. Supports BootstrapFewShot, COPRO (prompt optimization), MIPROv2, and more. This is genuine automatic self-improvement.
- **Persistence Model**: Compiled programs are saved as JSON and can be loaded across sessions. The optimization is offline (batch evaluation) rather than online (continuous learning).
- **Auto-optimization Features**: Automatic prompt optimization is the core value proposition. Also supports automatic assertion checking, self-refinement modules, and pipeline structure optimization (MIPRO).

### 2.6 Letta/MemGPT (cpacker/MemGPT)

- **Memory Architecture**: Tiered memory inspired by OS virtual memory: core memory (always in context, editable by the agent), archival memory (vector-indexed, unlimited, searchable), recall memory (conversation history, searchable). The agent explicitly manages its own memory via tool calls.
- **Learning Mechanisms**: The agent learns by deciding what to write to core memory and archival memory. This is a form of explicit self-directed learning — the agent curates its own knowledge. No automatic prompt optimization.
- **Persistence Model**: Fully persistent. All memory tiers persist across sessions. The agent resumes exactly where it left off, with its self-curated context.
- **Auto-optimization Features**: The agent self-manages context window utilization. No automatic tool selection or prompt tuning, but the memory self-management is a powerful form of optimization.

### 2.7 OpenAI Agents (openai/openai-agents-python)

- **Memory Architecture**: Minimal. Context is managed through the conversation thread. No built-in long-term memory or vector store.
- **Learning Mechanisms**: None built-in. Handoff patterns between agents enable routing but not learning. Tracing is supported for observability but not for automatic improvement.
- **Persistence Model**: Thread-based conversation persistence via the OpenAI API. No cross-session learning.
- **Auto-optimization Features**: None. The SDK is intentionally minimal, focusing on agent composition rather than self-improvement.

### 2.8 Semantic Kernel (microsoft/semantic-kernel)

- **Memory Architecture**: Pluggable memory connectors — supports Azure AI Search, ChromaDB, Pinecone, Qdrant, Redis, and more. Semantic memory allows storing and retrieving text by semantic similarity.
- **Learning Mechanisms**: No built-in learning loops. Memory is a retrieval system, not a learning system. Plugins (functions) can be composed automatically via the planner.
- **Persistence Model**: Depends on the chosen memory connector. Can be fully persistent with external vector DBs.
- **Auto-optimization Features**: The planner auto-selects which plugins to invoke for a goal. Token management and context window optimization are handled by the kernel. No prompt self-optimization.

### 2.9 Aider (Aider-AI/aider)

- **Memory Architecture**: Repository map — a hierarchical summary of the codebase generated from AST analysis. Chat history persists in markdown files. No vector store or semantic search.
- **Learning Mechanisms**: Conventions file (`.aider.conventions.md`) allows users to teach Aider project-specific patterns. Linting integration provides feedback loops — Aider auto-fixes lint errors. No automatic learning from past sessions.
- **Persistence Model**: Chat history saved per session in markdown. Repository map regenerated each session. Conventions file is the only cross-session "learning."
- **Auto-optimization Features**: Auto-selects which files to include in context based on the repository map. Auto-retries on lint errors. Architect mode plans before coding. No prompt optimization.

### 2.10 OpenHands (All-Hands-AI/OpenHands)

- **Memory Architecture**: Event stream — all actions and observations are logged as events. Microagents provide domain-specific knowledge as static context files (repository-level and global).
- **Learning Mechanisms**: Feedback mechanism allows users to rate outputs, which is stored for future reference. Microagents can be thought of as curated knowledge, but they are static files, not automatically generated. No automatic learning loop.
- **Persistence Model**: Event stream persists per session. Microagents persist per repository. No automatic cross-session learning.
- **Auto-optimization Features**: Runtime auto-selection (Docker sandbox, local, remote). No automatic prompt or tool optimization.

### 2.11 Attractor (strongdm/attractor)

- **Memory Architecture**: Limited public information. Security-focused framework with emphasis on policy enforcement over memory. Configuration-driven rather than memory-driven.
- **Learning Mechanisms**: No known self-learning capabilities. Focus is on security guardrails and policy compliance rather than adaptation.
- **Persistence Model**: Configuration-based persistence. No dynamic memory system documented.
- **Auto-optimization Features**: Policy-based tool selection and access control. Security posture is the optimization target, not task performance.

### 2.12 Get Shit Done (gsd-build/get-shit-done)

- **Memory Architecture**: Task-oriented state management. Uses file-based persistence for task tracking and progress. Limited memory beyond task state.
- **Learning Mechanisms**: No self-learning. Focused on task decomposition and execution rather than improvement over time.
- **Persistence Model**: File-based task state. Persists across sessions via project files.
- **Auto-optimization Features**: Task prioritization and decomposition. No automatic prompt or tool optimization.

### 2.13 Oh My Claude Code (yeachan-heo/oh-my-claudecode)

- **Memory Architecture**: Enhancement layer over Claude Code. Adds structured memory via CLAUDE.md and project rules. Memory is file-based and manually curated.
- **Learning Mechanisms**: Prompt engineering enhancements and workflow templates. Users can define reusable patterns, but there is no automatic learning or pattern extraction.
- **Persistence Model**: File-based (markdown rules and configuration). Persists per project via git.
- **Auto-optimization Features**: Workflow templates optimize for specific task types. No dynamic optimization.

### 2.14 Kata.sh

- **Memory Architecture**: Cloud-based environment with persistent workspaces. Memory is primarily workspace state (files, environment) rather than semantic memory.
- **Learning Mechanisms**: No documented self-learning. Focus is on providing a consistent cloud environment for AI coding rather than agent self-improvement.
- **Persistence Model**: Cloud workspace persistence. Session state maintained by the platform.
- **Auto-optimization Features**: Environment auto-configuration. No agent-level optimization.

---

## 3. Comparative Matrix

| Framework | Memory Type | Learning Type | Persistence | Auto-optimize | Self-improve | Maturity |
|-----------|------------|---------------|-------------|---------------|--------------|----------|
| claude-flow | Hybrid (HNSW + KV + SQLite) | Hooks-based, neural training | Per-project, session save/restore | Model routing, agent boosting | Infrastructure present, usage dependent | Alpha |
| LangGraph | Checkpointer (SQL/Redis) | None built-in | Per-thread, cross-session via platform | None | None | Production |
| CrewAI | Short/long/entity (SQLite + RAG) | Experience replay, delegation | Per-crew, file-based | Agent delegation routing | Minimal | Production |
| AutoGen | Conversation + pluggable (Mem0) | Multi-agent reflection | Conversation serialization | Model selection per agent | Teachability extension | Production |
| DSPy | Compiled program state | Prompt optimization, metrics-driven | Saved compiled programs | Automatic prompt tuning | Yes — core feature | Production |
| Letta/MemGPT | Tiered (core/archival/recall) | Self-directed memory curation | Fully persistent, cross-session | Context window management | Memory self-management | Production |
| OpenAI Agents | Thread-based conversation | None | Thread persistence | None | None | Production |
| Semantic Kernel | Pluggable vector DBs | None built-in | Via external connectors | Planner auto-selects plugins | None | Production |
| Aider | Repo map + chat history | Conventions file, lint feedback | Chat history files | File selection, auto-retry | None | Production |
| OpenHands | Event stream + microagents | User feedback storage | Event stream per session | Runtime selection | None | Production |
| Attractor | Config-based | None known | Configuration files | Policy-based selection | None | Early |
| Get Shit Done | File-based task state | None | Task state files | Task prioritization | None | Early |
| Oh My Claude Code | File-based rules | Manual pattern curation | Git-based project files | Workflow templates | None | Early |
| Kata.sh | Cloud workspace | None documented | Cloud persistence | Environment auto-config | None | Early |

---

## 4. Patterns & Anti-Patterns

### Patterns (What Works)

1. **Experience replay with quality scoring** (DSPy, CrewAI): Store task outcomes with success/failure metadata and a quality score. Retrieve high-scoring experiences when facing similar tasks. DSPy's optimizers demonstrate that scored examples dramatically improve prompt quality.

2. **Tiered memory with explicit management** (Letta/MemGPT): Separating always-available context (core) from searchable archives (archival) from raw history (recall) prevents context bloat while preserving knowledge. The agent's ability to manage its own memory is more robust than automated heuristics.

3. **Reflection loops with structured evaluation** (AutoGen, DSPy): Having agents explicitly evaluate their outputs against criteria before finalizing produces measurably better results. DSPy's assertions and AutoGen's critic agents both implement this effectively.

4. **Checkpoint-based time travel** (LangGraph): Serializing state at every step enables debugging, replay, and branching. Even without learning, this makes the system more reliable and analyzable.

5. **Offline optimization with online serving** (DSPy): Separating the expensive optimization phase (batch evaluation of prompt variants) from runtime serving (using the compiled best-performing variant) balances improvement speed with operational cost.

6. **Convention files as curated memory** (Aider, Oh My Claude Code): Allowing humans to curate project-specific patterns in files that agents always read is a simple, effective form of knowledge transfer. It bridges the gap until automatic pattern extraction is reliable.

### Anti-Patterns (What Fails)

7. **Unbounded memory accumulation**: Storing every interaction without pruning or scoring leads to retrieval degradation. As the memory store grows, irrelevant results dilute useful ones. Letta's explicit memory management and DSPy's curated example sets avoid this.

8. **Learning without validation**: Storing patterns without verifying they actually improve outcomes leads to "superstitious learning" — the system believes in patterns that are coincidental or context-dependent. DSPy's metric-driven validation is the counter.

9. **Over-reliance on vector similarity**: Semantic search is powerful but imprecise. Retrieving "similar" experiences that are actually different enough to mislead the agent is a common failure mode. Combining semantic search with structured metadata filtering reduces this.

10. **Monolithic memory with no namespacing**: Mixing task patterns, error logs, user preferences, and domain knowledge in a single store makes retrieval noisy. Claude-flow's namespace system is a good pattern; many frameworks lack this.

---

## 5. Gap Analysis for This Project

### What claude-flow does well

- **HNSW-indexed vector search** provides fast semantic retrieval, on par with or exceeding most frameworks' memory lookup speed.
- **Hooks system** (pre-task, post-task, pre-edit, post-edit) provides comprehensive insertion points for learning. This is more granular than any other framework's learning triggers.
- **Namespace-based memory organization** (patterns, solutions, tasks) prevents the monolithic memory anti-pattern.
- **Neural training infrastructure** (RuVector, SONA, MoE) is architecturally ambitious and unique among the analyzed frameworks.
- **Model routing** (3-tier Haiku/Sonnet/Opus) with agent boosting is a practical cost optimization that no other framework implements as directly.
- **Background workers** for consolidation, optimization, and auditing provide asynchronous improvement that most frameworks lack entirely.

### What's missing compared to peers

- **vs. DSPy's prompt optimization**: Claude-flow stores patterns but does not automatically evaluate prompt variants against metrics or recompile prompts with optimal few-shot examples. DSPy's optimizers (BootstrapFewShot, MIPROv2) are a generation ahead in automatic improvement. The gap is significant: claude-flow has the memory to support this but lacks the optimization loop.

- **vs. Letta/MemGPT's memory self-management**: Claude-flow's memory is managed by the orchestrator (Claude Code invoking hooks), not by the agent itself. Letta agents actively decide what to remember and forget via tool calls. This self-directed curation produces higher-quality memory than passive accumulation.

- **vs. LangGraph's checkpointing**: Claude-flow's session save/restore is coarser than LangGraph's per-step checkpointing. There is no ability to "rewind" to a specific point in a multi-step task and branch from there.

- **vs. CrewAI's structured experience replay**: CrewAI's long-term memory automatically stores task outcomes with structured metadata. Claude-flow has the infrastructure but depends on the agent remembering to invoke the hooks — there is no guaranteed automatic storage.

- **vs. AutoGen's multi-agent reflection**: Claude-flow can spawn critic agents, but there is no standard pattern for structured reflection after multi-step tasks. AutoGen's conversation-based reflection is more natural for multi-agent setups.

- **Pattern quality scoring and decay**: No framework except DSPy has robust quality scoring, but claude-flow also lacks basic usage tracking and age-based decay for stored patterns. Without these, the memory store will degrade over time.

---

## 6. Improvement Recommendations

### High Impact, Low Effort

1. **Guaranteed pattern storage on task success**: Wire post-task hooks into the standard workflow so that every successful task automatically stores its approach, tools used, and outcome. Do not rely on the agent remembering to invoke the hook.

2. **Guaranteed memory search on task start**: Wire pre-task hooks to always search for relevant patterns and inject them into the agent's initial context. This is the single highest-leverage improvement.

3. **Pattern usage tracking**: Log every time a stored pattern is retrieved and whether the task that used it succeeded. This creates the data needed for quality scoring.

### High Impact, Medium Effort

4. **Quality scoring with decay**: Score patterns by (retrieval count x success rate) / age. Prune patterns below a threshold. This prevents unbounded accumulation and keeps the memory store useful.

5. **Structured reflection after complex tasks**: After any multi-step task (swarm execution), spawn a reflection agent that evaluates what worked, what failed, and stores meta-patterns.

6. **Cross-session knowledge transfer**: When a pattern has been successfully used in 3+ separate sessions, promote it to a global namespace for cross-project reuse.

### High Impact, High Effort

7. **Metric-driven prompt optimization (DSPy-inspired)**: For the most common task types (bug fix, feature, refactor), collect outcomes and use them to optimize the system prompts. This could use DSPy directly or implement a simpler variant.

8. **Agent-directed memory management (Letta-inspired)**: Give agents explicit memory management tools (remember, forget, update) rather than relying solely on the hook system.

9. **Per-step checkpointing**: Implement fine-grained state serialization for multi-step tasks, enabling replay and branching.

### Medium Impact, Medium Effort

10. **Tool selection learning**: Track which tools (Bash, Edit, Grep, etc.) are most effective for which task types. Surface tool recommendations in pre-task context.

11. **Confidence calibration**: Track prediction accuracy for the neural predict system. Adjust confidence scores based on actual outcomes to prevent overconfident routing.
