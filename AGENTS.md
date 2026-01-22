<!-- SKILLPORT_START -->
## SkillPort Skills

Skills are reusable expert knowledge that help you complete tasks effectively.
Each skill contains step-by-step instructions, templates, and scripts.

### Workflow

1. **Find a skill** - Check the list below for a skill matching your task
2. **Get instructions** - Run `skillport show <skill-id>` to load full instructions
3. **Follow the instructions** - Execute the steps using your available tools

### Tips

- Skills may include scripts - execute them via the skill's path, don't read them into context
- If instructions reference `{path}`, replace it with the skill's directory path
- When uncertain, check the skill's description to confirm it matches your task

<available_skills>
<skill>
  <name>agent-browser</name>
  <description>Automates browser interactions for web testing, form filling, screenshots, and data extraction. Use when the user needs to navigate websites, interact with web pages, fill forms, take screenshots, test web applications, or extract information from web pages.</description>
</skill>
<skill>
  <name>d3k</name>
  <description>d3k web development assistant. Use when working on web apps with d3k running. Primary tool is fix_my_app for diagnosing and fixing errors.</description>
</skill>
<skill>
  <name>react-best-practices</name>
  <description>React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements.</description>
</skill>
<skill>
  <name>skills/12-factor-apps</name>
  <description>Perform 12-Factor App compliance analysis on any codebase. Use when evaluating app architecture or cloud-native readiness against the original Twelve-Factor methodology.</description>
</skill>
<skill>
  <name>skills/adr-decision-extraction</name>
  <description>Extract architectural decisions from conversations. Identifies problem-solution pairs, trade-off discussions, and explicit choices. Use when analyzing session transcripts for ADR generation.</description>
</skill>
<skill>
  <name>skills/adr-writing</name>
  <description>Write Architectural Decision Records following MADR template. Applies Definition of Done criteria, marks gaps for later completion. Use when generating ADR documents from extracted decisions.</description>
</skill>
<skill>
  <name>skills/agent-architecture-analysis</name>
  <description>Perform 12-Factor Agents compliance analysis on LLM/agent systems. Use when reviewing agent architectures, LangGraph/DeepAgents designs, or multi-agent deployments for reliability and scale.</description>
</skill>
<skill>
  <name>skills/ai-elements</name>
  <description>Vercel AI Elements for workflow UI components. Use when building chat interfaces, displaying tool execution, showing reasoning/thinking, or creating job queues. Triggers on ai-elements, Queue, Confirmation, Tool, Reasoning, Shimmer, Loader, Message, Conversation, PromptInput.</description>
</skill>
<skill>
  <name>skills/app-intents-code-review</name>
  <description>Reviews App Intents code for intent structure, entities, shortcuts, and parameters. Use when reviewing code with import AppIntents, @AppIntent, AppEntity, AppShortcutsProvider, or @Parameter.</description>
</skill>
<skill>
  <name>skills/brainstorming</name>
  <description>You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.</description>
</skill>
<skill>
  <name>skills/bubbletea-code-review</name>
  <description>Reviews BubbleTea TUI code for proper Elm architecture, model/update/view patterns, and Lipgloss styling. Use when reviewing terminal UI code using charmbracelet/bubbletea.</description>
</skill>
<skill>
  <name>skills/cloudkit-code-review</name>
  <description>Reviews CloudKit code for container setup, record handling, subscriptions, and sharing patterns. Use when reviewing code with import CloudKit, CKContainer, CKRecord, CKShare, or CKSubscription.</description>
</skill>
<skill>
  <name>skills/combine-code-review</name>
  <description>Reviews Combine framework code for memory leaks, operator misuse, and error handling. Use when reviewing code with import Combine, AnyPublisher, @Published, PassthroughSubject, or CurrentValueSubject.</description>
</skill>
<skill>
  <name>skills/dagre-react-flow</name>
  <description>Automatic graph layout using dagre with React Flow (@xyflow/react). Use when implementing auto-layout, hierarchical layouts, tree structures, or arranging nodes programmatically. Triggers on dagre, auto-layout, automatic layout, getLayoutedElements, rankdir, hierarchical graph.</description>
</skill>
<skill>
  <name>skills/deepagents-architecture</name>
  <description>Guides architectural decisions for Deep Agents applications. Use when deciding between Deep Agents vs alternatives, choosing backend strategies, designing subagent systems, or selecting middleware approaches.</description>
</skill>
<skill>
  <name>skills/deepagents-code-review</name>
  <description>Reviews Deep Agents code for bugs, anti-patterns, and improvements. Use when reviewing code that uses create_deep_agent, backends, subagents, middleware, or human-in-the-loop patterns. Catches common configuration and usage mistakes.</description>
</skill>
<skill>
  <name>skills/deepagents-implementation</name>
  <description>Implements agents using Deep Agents. Use when building agents with create_deep_agent, configuring backends, defining subagents, adding middleware, or setting up human-in-the-loop workflows.</description>
</skill>
<skill>
  <name>skills/dispatching-parallel-agents</name>
  <description>Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies</description>
</skill>
<skill>
  <name>skills/docling</name>
  <description>Docling document parser for PDF, DOCX, PPTX, HTML, images, and 15+ formats. Use when parsing documents, extracting text, converting to Markdown/HTML/JSON, chunking for RAG pipelines, or batch processing files. Triggers on DocumentConverter, convert, convert_all, export_to_markdown, HierarchicalChunker, HybridChunker, ConversionResult.</description>
</skill>
<skill>
  <name>skills/executing-plans</name>
  <description>Use when you have a written implementation plan to execute in a separate session with review checkpoints</description>
</skill>
<skill>
  <name>skills/fastapi-code-review</name>
  <description>Reviews FastAPI code for routing patterns, dependency injection, validation, and async handlers. Use when reviewing FastAPI apps, checking APIRouter setup, Depends() usage, or response models.</description>
</skill>
<skill>
  <name>skills/finishing-a-development-branch</name>
  <description>Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup</description>
</skill>
<skill>
  <name>skills/github-projects</name>
  <description>GitHub Projects management via gh CLI for creating projects, managing items, fields, and workflows. Use when working with GitHub Projects (v2), adding issues/PRs to projects, creating custom fields, tracking project items, or automating project workflows. Triggers on gh project, project board, kanban, GitHub project, project items.</description>
</skill>
<skill>
  <name>skills/go-code-review</name>
  <description>Reviews Go code for idiomatic patterns, error handling, concurrency safety, and common mistakes. Use when reviewing .go files, checking error handling, goroutine usage, or interface design.</description>
</skill>
<skill>
  <name>skills/go-testing-code-review</name>
  <description>Reviews Go test code for proper table-driven tests, assertions, and coverage patterns. Use when reviewing *_test.go files.</description>
</skill>
<skill>
  <name>skills/healthkit-code-review</name>
  <description>Reviews HealthKit code for authorization patterns, query usage, background delivery, and data type handling. Use when reviewing code with import HealthKit, HKHealthStore, HKSampleQuery, HKObserverQuery, or HKQuantityType.</description>
</skill>
<skill>
  <name>skills/langgraph-architecture</name>
  <description>Guides architectural decisions for LangGraph applications. Use when deciding between LangGraph vs alternatives, choosing state management strategies, designing multi-agent systems, or selecting persistence and streaming approaches.</description>
</skill>
<skill>
  <name>skills/langgraph-code-review</name>
  <description>Reviews LangGraph code for bugs, anti-patterns, and improvements. Use when reviewing code that uses StateGraph, nodes, edges, checkpointing, or other LangGraph features. Catches common mistakes in state management, graph structure, and async patterns.</description>
</skill>
<skill>
  <name>skills/langgraph-implementation</name>
  <description>Implements stateful agent graphs using LangGraph. Use when building graphs, adding nodes/edges, defining state schemas, implementing checkpointing, handling interrupts, or creating multi-agent systems with LangGraph.</description>
</skill>
<skill>
  <name>skills/llm-artifacts-detection</name>
  <description>Detects common LLM coding agent artifacts in codebases. Identifies test quality issues, dead code, over-abstraction, and verbose LLM style patterns. Use when cleaning up AI-generated code or reviewing for agent-introduced cruft.</description>
</skill>
<skill>
  <name>skills/llm-judge</name>
  <description>LLM-as-judge methodology for comparing code implementations across repositories. Scores implementations on functionality, security, test quality, overengineering, and dead code using weighted rubrics. Used by /beagle:llm-judge command.</description>
</skill>
<skill>
  <name>skills/postgres-code-review</name>
  <description>Reviews PostgreSQL code for indexing strategies, JSONB operations, connection pooling, and transaction safety. Use when reviewing SQL queries, database schemas, JSONB usage, or connection management.</description>
</skill>
<skill>
  <name>skills/prometheus-go-code-review</name>
  <description>Reviews Prometheus instrumentation in Go code for proper metric types, labels, and patterns. Use when reviewing code with prometheus/client_golang metrics.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-agent-creation</name>
  <description>Create PydanticAI agents with type-safe dependencies, structured outputs, and proper configuration. Use when building AI agents, creating chat systems, or integrating LLMs with Pydantic validation.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-common-pitfalls</name>
  <description>Avoid common mistakes and debug issues in PydanticAI agents. Use when encountering errors, unexpected behavior, or when reviewing agent implementations.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-dependency-injection</name>
  <description>Implement dependency injection in PydanticAI agents using RunContext and deps_type. Use when agents need database connections, API clients, user context, or any external resources.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-model-integration</name>
  <description>Configure LLM providers, use fallback models, handle streaming, and manage model settings in PydanticAI. Use when selecting models, implementing resilience, or optimizing API calls.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-testing</name>
  <description>Test PydanticAI agents using TestModel, FunctionModel, VCR cassettes, and inline snapshots. Use when writing unit tests, mocking LLM responses, or recording API interactions.</description>
</skill>
<skill>
  <name>skills/pydantic-ai-tool-system</name>
  <description>Register and implement PydanticAI tools with proper context handling, type annotations, and docstrings. Use when adding tool capabilities to agents, implementing function calling, or creating agent actions.</description>
</skill>
<skill>
  <name>skills/pytest-code-review</name>
  <description>Reviews pytest test code for async patterns, fixtures, parametrize, and mocking. Use when reviewing test_*.py files, checking async test functions, fixture usage, or mock patterns.</description>
</skill>
<skill>
  <name>skills/python-code-review</name>
  <description>Reviews Python code for type safety, async patterns, error handling, and common mistakes. Use when reviewing .py files, checking type hints, async/await usage, or exception handling.</description>
</skill>
<skill>
  <name>skills/react-flow</name>
  <description>React Flow (@xyflow/react) for workflow visualization with custom nodes and edges. Use when building graph visualizations, creating custom workflow nodes, implementing edge labels, or controlling viewport. Triggers on ReactFlow, @xyflow/react, Handle, NodeProps, EdgeProps, useReactFlow, fitView.</description>
</skill>
<skill>
  <name>skills/react-flow-advanced</name>
  <description>Advanced React Flow patterns for complex use cases. Use when implementing sub-flows, custom connection lines, programmatic layouts, drag-and-drop, undo/redo, or complex state synchronization.</description>
</skill>
<skill>
  <name>skills/react-flow-architecture</name>
  <description>Architectural guidance for building node-based UIs with React Flow. Use when designing flow-based applications, making decisions about state management, integration patterns, or evaluating whether React Flow fits a use case.</description>
</skill>
<skill>
  <name>skills/react-flow-code-review</name>
  <description>Reviews React Flow code for anti-patterns, performance issues, and best practices. Use when reviewing code that uses @xyflow/react, checking for common mistakes, or optimizing node-based UI implementations.</description>
</skill>
<skill>
  <name>skills/react-flow-implementation</name>
  <description>Implements React Flow node-based UIs correctly using @xyflow/react. Use when building flow charts, diagrams, visual editors, or node-based applications with React. Covers nodes, edges, handles, custom components, state management, and viewport control.</description>
</skill>
<skill>
  <name>skills/react-router-code-review</name>
  <description>Reviews React Router code for proper data loading, mutations, error handling, and navigation patterns. Use when reviewing React Router v6.4+ code, loaders, actions, or navigation logic.</description>
</skill>
<skill>
  <name>skills/react-router-v7</name>
  <description>React Router v7 best practices for data-driven routing. Use when implementing routes, loaders, actions, Form components, fetchers, navigation guards, protected routes, or URL search params. Triggers on createBrowserRouter, RouterProvider, useLoaderData, useActionData, useFetcher, NavLink, Outlet.</description>
</skill>
<skill>
  <name>skills/receive-feedback</name>
  <description>Process external code review feedback with technical rigor. Use when receiving feedback from another LLM, human reviewer, or CI tool. Verifies claims before implementing, tracks disposition.</description>
</skill>
<skill>
  <name>skills/receiving-code-review</name>
  <description>Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation</description>
</skill>
<skill>
  <name>skills/requesting-code-review</name>
  <description>Use when completing tasks, implementing major features, or before merging to verify work meets requirements</description>
</skill>
<skill>
  <name>skills/review-feedback-schema</name>
  <description>Schema for tracking code review outcomes to enable feedback-driven skill improvement. Use when logging review results or analyzing review quality.</description>
</skill>
<skill>
  <name>skills/review-skill-improver</name>
  <description>Analyzes feedback logs to identify patterns and suggest improvements to review skills. Use when you have accumulated feedback data and want to improve review accuracy.</description>
</skill>
<skill>
  <name>skills/review-verification-protocol</name>
  <description>Mandatory verification steps for all code reviews to reduce false positives. Load this skill before reporting ANY code review findings.</description>
</skill>
<skill>
  <name>skills/shadcn-code-review</name>
  <description>Reviews shadcn/ui components for CVA patterns, composition with asChild, accessibility states, and data-slot usage. Use when reviewing React components using shadcn/ui, Radix primitives, or Tailwind styling.</description>
</skill>
<skill>
  <name>skills/shadcn-ui</name>
  <description>shadcn/ui component patterns with Radix primitives and Tailwind styling. Use when building UI components, using CVA variants, implementing compound components, or styling with data-slot attributes. Triggers on shadcn, cva, cn(), data-slot, Radix, Button, Card, Dialog, VariantProps.</description>
</skill>
<skill>
  <name>skills/sqlalchemy-code-review</name>
  <description>Reviews SQLAlchemy code for session management, relationships, N+1 queries, and migration patterns. Use when reviewing SQLAlchemy 2.0 code, checking session lifecycle, relationship() usage, or Alembic migrations.</description>
</skill>
<skill>
  <name>skills/sqlite-vec</name>
  <description>sqlite-vec extension for vector similarity search in SQLite. Use when storing embeddings, performing KNN queries, or building semantic search features. Triggers on sqlite-vec, vec0, MATCH, vec_distance, partition key, float[N], int8[N], bit[N], serialize_float32, serialize_int8, vec_f32, vec_int8, vec_bit, vec_normalize, vec_quantize_binary, distance_metric, metadata columns, auxiliary columns.</description>
</skill>
<skill>
  <name>skills/subagent-driven-development</name>
  <description>Use when executing implementation plans with independent tasks in the current session</description>
</skill>
<skill>
  <name>skills/swift-code-review</name>
  <description>Reviews Swift code for concurrency safety, error handling, memory management, and common mistakes. Use when reviewing .swift files for async/await patterns, actor isolation, Sendable conformance, or general Swift best practices.</description>
</skill>
<skill>
  <name>skills/swift-testing-code-review</name>
  <description>Reviews Swift Testing code for proper use of</description>
</skill>
<skill>
  <name>skills/swiftdata-code-review</name>
  <description>Reviews SwiftData code for model design, queries, concurrency, and migrations. Use when reviewing .swift files with import SwiftData, @Model, @Query, @ModelActor, or VersionedSchema.</description>
</skill>
<skill>
  <name>skills/swiftui-code-review</name>
  <description>Reviews SwiftUI code for view composition, state management, performance, and accessibility. Use when reviewing .swift files containing SwiftUI views, property wrappers (@State, @Binding, @Observable), or UI code.</description>
</skill>
<skill>
  <name>skills/systematic-debugging</name>
  <description>Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes</description>
</skill>
<skill>
  <name>skills/tailwind-v4</name>
  <description>Tailwind CSS v4 with CSS-first configuration and design tokens. Use when setting up Tailwind v4, defining theme variables, using OKLCH colors, or configuring dark mode. Triggers on @theme, @tailwindcss/vite, oklch, CSS variables, --color-, tailwind v4.</description>
</skill>
<skill>
  <name>skills/test-driven-development</name>
  <description>Use when implementing any feature or bugfix, before writing implementation code</description>
</skill>
<skill>
  <name>skills/using-git-worktrees</name>
  <description>Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification</description>
</skill>
<skill>
  <name>skills/using-superpowers</name>
  <description>Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions</description>
</skill>
<skill>
  <name>skills/vercel-ai-sdk</name>
  <description>Vercel AI SDK for building chat interfaces with streaming. Use when implementing useChat hook, handling tool calls, streaming responses, or building chat UI. Triggers on useChat, @ai-sdk/react, UIMessage, ChatStatus, streamText, toUIMessageStreamResponse, addToolOutput, onToolCall, sendMessage.</description>
</skill>
<skill>
  <name>skills/verification-before-completion</name>
  <description>Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always</description>
</skill>
<skill>
  <name>skills/vitest-testing</name>
  <description>Vitest testing framework patterns and best practices. Use when writing unit tests, integration tests, configuring vitest.config, mocking with vi.mock/vi.fn, using snapshots, or setting up test coverage. Triggers on describe, it, expect, vi.mock, vi.fn, beforeEach, afterEach, vitest.</description>
</skill>
<skill>
  <name>skills/watchos-code-review</name>
  <description>Reviews watchOS code for app lifecycle, complications (ClockKit/WidgetKit), WatchConnectivity, and performance constraints. Use when reviewing code with import WatchKit, WKExtension, WKApplicationDelegate, WCSession, or watchOS-specific patterns.</description>
</skill>
<skill>
  <name>skills/web-design-guidelines</name>
  <description>Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".</description>
</skill>
<skill>
  <name>skills/widgetkit-code-review</name>
  <description>Reviews WidgetKit code for timeline management, view composition, configurable intents, and performance. Use when reviewing code with import WidgetKit, TimelineProvider, Widget protocol, or @main struct Widget.</description>
</skill>
<skill>
  <name>skills/wish-ssh-code-review</name>
  <description>Reviews Wish SSH server code for proper middleware, session handling, and security patterns. Use when reviewing SSH server code using charmbracelet/wish.</description>
</skill>
<skill>
  <name>skills/writing-plans</name>
  <description>Use when you have a spec or requirements for a multi-step task, before touching code</description>
</skill>
<skill>
  <name>skills/writing-skills</name>
  <description>Use when creating, editing, or verifying agent skills before deployment. Emphasizes test-driven skill writing and tight frontmatter.</description>
</skill>
<skill>
  <name>skills/zustand-state</name>
  <description>Zustand state management for React and vanilla JavaScript. Use when creating stores, using selectors, persisting state to localStorage, integrating devtools, or managing global state without Redux complexity. Triggers on zustand, create(), createStore, useStore, persist, devtools, immer middleware.</description>
</skill>
<skill>
  <name>ui-ux-pro-max</name>
  <description>UI/UX design intelligence. 50 styles, 21 palettes, 50 font pairings, 20 charts, 9 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, mobile app, .html, .tsx, .vue, .svelte. Elements: button, modal, navbar, sidebar, card, table, form, chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, flat design. Topics: color palette, accessibility, animation, layout, typography, font pairing, spacing, hover, shadow, gradient. Integrations: shadcn/ui MCP for component search and examples.</description>
</skill>
<skill>
  <name>web-design-guidelines</name>
  <description>Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".</description>
</skill>
</available_skills>
<!-- SKILLPORT_END -->
