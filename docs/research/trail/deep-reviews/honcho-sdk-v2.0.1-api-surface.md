# Honcho SDK v2.0.1 API Surface Analysis

**Date:** 2026-03-24
**Source:** honcho-ai==2.0.1 (installed via pip)
**Method:** Package introspection via Python `inspect` module
**Scope:** Complete CRUD API surface, LLM operation classification, API-only mode safety matrix

---

## Executive Summary

Honcho SDK v2.0.1 provides **43 public methods** across sync and async client classes. The API cleanly separates:

- **32 CRUD operations** (safe in API-only mode without LLM keys)
- **11 LLM-dependent operations** (will return 500 errors if EMBED_MESSAGES=false or LLM keys missing)

### Critical for API-Only Deployments

Avoid these methods when running without LLM keys:
- `Peer.chat()`, `Peer.chat_stream()` — require LLM inference
- `Peer.search()`, `Peer.context()`, `Peer.representation()` — require embeddings + reasoning
- `Peer.conclusions_of()` — requires LLM reasoning
- `Session.search()`, `Session.context()`, `Session.representation()`, `Session.summaries()` — require LLM
- `Honcho.search()` — requires embeddings

All other operations (CRUD for peers, sessions, messages, metadata, configuration) succeed in API-only mode.

---

## API Classes

### Sync (Thread-safe)

- **Honcho** — Main client, workspace/peer/session management
- **Peer** — Individual agent or user participant
- **Session** — Conversation group/thread
- **Message** — Immutable conversation record

### Async (Coroutine-based)

- **HonchoAio** — Async equivalent of Honcho
- **PeerAio** — Async equivalent of Peer
- **SessionAio** — Async equivalent of Session

Method signatures are **identical** between sync and async versions; only execution model differs (blocking vs awaitable).

---

## CRUD Operations (Safe in API-Only Mode)

### Honcho (Workspace Management)

| Method | Purpose | API-Only Safe |
|--------|---------|---------------|
| `peer(id, metadata?, config?)` | Get/create peer | ✅ Yes |
| `peers(filters?)` | List peers | ✅ Yes |
| `session(id, metadata?, config?)` | Get/create session | ✅ Yes |
| `sessions(filters?)` | List sessions | ✅ Yes |
| `workspaces(filters?)` | List workspaces | ✅ Yes |
| `delete_workspace(workspace_id)` | Delete workspace | ✅ Yes |
| `get_configuration()` | Get workspace config | ✅ Yes |
| `set_configuration(config)` | Set workspace config | ✅ Yes |
| `get_metadata()` | Get workspace metadata | ✅ Yes |
| `set_metadata(metadata)` | Set workspace metadata | ✅ Yes |
| `refresh()` | Reload from server | ✅ Yes |
| `queue_status(observer?, sender?, session?)` | Check background job status | ✅ Yes |
| `schedule_dream(observer, session?, observed?)` | Queue peer reasoning task | ✅ Yes |

### Peer (Participant CRUD)

| Method | Purpose | API-Only Safe |
|--------|---------|---------------|
| `message(content, metadata?, config?, created_at?)` | Create message builder | ✅ Yes |
| `get_configuration()` | Get peer config | ✅ Yes |
| `set_configuration(config)` | Set peer config | ✅ Yes |
| `get_metadata()` | Get peer metadata | ✅ Yes |
| `set_metadata(metadata)` | Set peer metadata | ✅ Yes |
| `get_card(target?)` | Get peer description | ✅ Yes |
| `set_card(card, target?)` | Set peer description | ✅ Yes |
| `sessions(filters?)` | List peer's sessions | ✅ Yes |
| `refresh()` | Reload from server | ✅ Yes |

### Session (Conversation Management)

| Method | Purpose | API-Only Safe |
|--------|---------|---------------|
| `add_messages(messages)` | Insert messages | ✅ Yes |
| `messages(filters?)` | List session messages | ✅ Yes |
| `update_message(message, metadata)` | Update message metadata | ✅ Yes |
| `upload_file(file, peer, metadata?, config?, created_at?)` | Upload file as messages | ✅ Yes |
| `add_peers(peers)` | Add peer(s) to session | ✅ Yes |
| `set_peers(peers)` | Replace all peers | ✅ Yes |
| `remove_peers(peers)` | Remove peer(s) | ✅ Yes |
| `peers()` | List session peers | ✅ Yes |
| `get_peer_configuration(peer)` | Get peer config in session | ✅ Yes |
| `set_peer_configuration(peer, config)` | Set peer config in session | ✅ Yes |
| `get_configuration()` | Get session config | ✅ Yes |
| `set_configuration(config)` | Set session config | ✅ Yes |
| `get_metadata()` | Get session metadata | ✅ Yes |
| `set_metadata(metadata)` | Set session metadata | ✅ Yes |
| `delete()` | Delete session | ✅ Yes |
| `refresh()` | Reload from server | ✅ Yes |
| `clone(message_id?)` | Fork session | ✅ Yes |
| `queue_status(observer?, sender?)` | Check background jobs | ✅ Yes |

---

## LLM Operations (Unsafe in API-Only Mode)

These methods require LLM API keys (Anthropic, OpenAI, Google, Groq, or custom) and will return HTTP 500 if:
- `EMBED_MESSAGES=false` in server config, OR
- LLM provider keys not configured

### Peer (Inference Operations)

| Method | Purpose | Requires |
|--------|---------|----------|
| `chat(query, target?, session?, reasoning_level?)` | Query peer with LLM | Claude/GPT/Gemini |
| `chat_stream(query, target?, session?, reasoning_level?)` | Streaming query | Claude/GPT/Gemini |
| `context(target?, search_query?, search_top_k?, ...)` | Get conclusions + context | Embeddings + LLM |
| `search(query, filters?, limit?)` | Semantic search peer messages | Embeddings |
| `representation(session?, target?, search_query?, ...)` | LLM-generated peer summary | Claude/GPT/Gemini |
| `conclusions_of(target)` | Reasons about target peer | Claude/GPT/Gemini |
| `card(target?)` | Get peer card (with inference) | May require LLM |

### Workspace (Inference Operations)

| Method | Purpose | Requires |
|--------|---------|----------|
| `search(query, filters?, limit?)` | Semantic search all messages | Embeddings |

### Session (Inference Operations)

| Method | Purpose | Requires |
|--------|---------|----------|
| `context(summary?, tokens?, peer_target?, search_query?, peer_perspective?, ...)` | Conversation context with conclusions | Embeddings + LLM |
| `search(query, filters?, limit?)` | Semantic search session messages | Embeddings |
| `representation(peer, target?, search_query?, ...)` | LLM-generated peer representation in session | Claude/GPT/Gemini |
| `summaries()` | LLM-generated session summaries | Claude/GPT/Gemini |

---

## Key API Patterns

### 1. Builder Pattern (Message Creation)

```python
from honcho import Honcho

client = Honcho(api_key="...")
session = client.session("chat-123")
alice = client.peer("alice")

# Build message params, then add to session
msg = alice.message("Hello!", metadata={"tone": "friendly"}, created_at="2026-03-24T20:30:00Z")
messages = session.add_messages([msg])
```

**API-only safe:** `peer.message()` and `session.add_messages()` are pure CRUD.

### 2. Lazy Object Loading

Calling `client.peer(id)` or `client.session(id)` does **not** immediately fetch from server—it returns a lazy proxy. Network call happens only when you:
- Call a method on the object
- Set metadata/configuration with optional params in constructor

```python
alice = client.peer("alice")  # No network call
alice.refresh()  # Network call: fetch peer state
```

### 3. Pagination (SyncPage / AsyncPage)

All list methods return paginated iterators:

```python
for peer in client.peers():  # Yields Peer objects, auto-paginates
    print(peer.id)

peers_list = list(client.peers())  # Collect all pages into list
```

### 4. Configuration & Metadata Hierarchy

Three levels of config:
- **Workspace** — `client.get_configuration()`, `client.set_configuration()`
- **Peer** — `peer.get_configuration()`, `peer.set_configuration()`
- **Session** — `session.get_configuration()`, `session.set_configuration()`
- **Peer-in-Session** — `session.get_peer_configuration(peer)`, `session.set_peer_configuration(peer, config)`

Each is independent; session-specific peer config overrides global peer config.

### 5. Metadata Storage

All objects support arbitrary metadata dictionaries:

```python
peer.set_metadata({"location": "SF", "timezone": "PST", "preferences": {"theme": "dark"}})
metadata = peer.get_metadata()
```

Metadata is **not** versioned; updates are overwrites.

---

## Parameter Types & Return Values

### Common Parameters

| Type | Example | Notes |
|------|---------|-------|
| `filters: dict[str, object]` | `{"name": "alice"}` | Backend-specific filter syntax; optional on list methods |
| `metadata: dict[str, object]` | `{"role": "user"}` | Arbitrary JSON-serializable dict |
| `created_at: datetime \| str` | `"2026-03-24T20:30:00Z"` or `datetime.now()` | ISO 8601 or Python datetime object |
| `limit: int` | `10` | Search result limit, 1-100 (default 10) |
| `search_top_k: int` | `5` | Semantic search result count, 1-100 |
| `search_max_distance: float` | `0.3` | Vector distance threshold, 0.0-1.0 |
| `reasoning_level: Literal[...]` | `"high"` | Options: minimal, low, medium, high, max |

### Common Return Types

| Type | Contents |
|------|----------|
| `Message` | `{id, session_id, peer_id, content, created_at, metadata}` |
| `Peer` | Client proxy; methods: chat(), search(), get_metadata(), ... |
| `Session` | Client proxy; methods: add_messages(), get_context(), ... |
| `SyncPage[T, U]` | Paginated iterator; iterate to fetch pages on-demand |
| `PeerContextResponse` | `{representation: str, card: list[str], conclusions: list[...]}` |
| `SessionContext` | `{summary, messages, conclusions, to_openai(), to_anthropic()}` |

---

## Client Initialization

### Sync

```python
from honcho import Honcho

client = Honcho(
    api_key="your-api-key",
    environment="production",  # or "local", "demo"
    workspace_id="optional-workspace-override",
    base_url="https://api.honcho.dev"  # optional
)
```

### Async

```python
from honcho import HonchoAio

client = HonchoAio(
    api_key="your-api-key",
    environment="production",
    workspace_id="optional-workspace-override",
    base_url="https://api.honcho.dev"
)

# Use with asyncio:
async def main():
    alice = client.peer("alice")
    messages = await alice.sessions()
```

### Environment Variables

```bash
export HONCHO_API_KEY="your-api-key"
export HONCHO_BASE_URL="https://api.honcho.dev"
export HONCHO_WORKSPACE_ID="optional-workspace-id"
```

---

## Dependencies

- **Python:** 3.11+
- **Core deps:**
  - `httpx` — HTTP client (used for API requests)
  - `pydantic` — Data validation (types, field descriptions)

No additional dependencies beyond those listed.

---

## Official Documentation Status (2026-03-24)

**Problem:** Honcho docs at `https://docs.honcho.dev/v3/api-reference/` use v3 URL structure that is **not yet deployed**:
- `GET /v3/api-reference/workspaces` → 404
- `GET /v3/api-reference/peers` → 404
- `GET /v3/api-reference/sessions` → 404
- `GET /v3/api-reference/messages` → 404

**Workaround:** Use PyPI README (`https://pypi.org/project/honcho-ai/`) and package introspection for authoritative API reference.

---

## Testing in API-Only Mode

To test CRUD operations without LLM keys:

```python
import os
os.environ["HONCHO_API_KEY"] = "test-key"  # Valid API key only
# Do NOT set any LLM keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

client = Honcho(api_key="test-key")

# These succeed:
alice = client.peer("alice")
alice.set_metadata({"role": "user"})
session = client.session("chat-1")
session.add_messages([alice.message("Hi")])

# These fail (500 errors):
# response = alice.chat("What are you?")  # 500: No LLM keys
# results = session.search("greetings")  # 500: No embeddings
```

---

## Conclusion

Honcho SDK v2.0.1 is well-suited for API-only deployments if you avoid the 11 LLM-dependent operations. The remaining 32 CRUD operations provide robust persistent memory and multi-party conversation management without external LLM dependencies.

For full inference capabilities (chat, search, reasoning), configure Anthropic, OpenAI, or other LLM API keys in the server environment.
