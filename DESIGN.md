# Design Document — Multi-Agent Task Orchestration System

## Architectural Decisions

### Agent Abstraction
Each agent is implemented as a class inheriting from an abstract `Agent` base with a single `run(task: Task) -> AgentResult` interface. This ensures a consistent contract: every agent receives the full task context (so later agents can see prior work) and returns a typed `AgentResult`. The `emit()` helper method on the base class lets agents push real-time progress events into the task's event log, decoupling logging from business logic.

### Orchestrator as a Linear Pipeline with Review Loop
The Orchestrator is a plain async class that sequences agents: **Planner → Researcher → Writer → Reviewer**, with a single revision cycle if the Reviewer returns `NEEDS_REVISION`. This covers the full requirement with minimal complexity. The revision cap (1 iteration) prevents infinite loops in production while still demonstrating the feedback mechanic.

### Shared Task State Object
A single `Task` Pydantic model is passed by reference through all agents. Each agent mutates specific fields (`plan`, `research`, `draft`, `feedback`, `final_report`) and appends to `events`. This "blackboard" pattern keeps agents loosely coupled — the Writer doesn't need to know how the Researcher formatted its output, just that `task.research` is populated.

### SSE for Real-Time Updates (vs. WebSockets / Polling)
| Approach | Pros | Cons |
|---|---|---|
| Polling | Simple, stateless | Latency, wasted requests |
| WebSockets | Bidirectional, low latency | Heavier infra, overkill for 1-way streaming |
| **SSE (chosen)** | Native browser support, lightweight, HTTP/1.1 compatible | Server-to-client only |

SSE was chosen because the data flow is strictly one-directional (server pushes agent events to client). It requires no additional library on the client (`EventSource` is built-in) and no special server infrastructure.

### Gemini 1.5 Flash as the LLM
All four agents call the same Gemini 1.5 Flash model with different system prompts. Using one model keeps the dependency footprint small. Flash was chosen over Pro for speed — since agents run serially, latency compounds, and faster inference leads to a noticeably better UX.

---

## Trade-offs Considered

**Sync vs. Async execution of agents:** The orchestrator runs agents sequentially by awaiting each. A parallel Researcher (running sub-tasks concurrently) would be faster — I left this as a stretch goal since it requires a gather/fan-out pattern and more complex state merging.

**In-memory state vs. persistent storage:** Tasks are stored in a Python dict for simplicity. In production this would be Redis or a database, enabling task history and horizontal scaling. The current design fails on server restart.

**Single revision loop vs. arbitrary retries:** One revision cycle is sufficient for demo purposes. A production system would parameterize `max_revisions` and potentially let the user set it.

---

## What I'd Do With More Time

- **Parallel Researcher:** Use `asyncio.gather()` to run sub-task research concurrently, with a fan-out/fan-in in the orchestrator.
- **Persistent storage:** Replace the in-memory dict with SQLite (via SQLModel) or Redis so task history survives restarts.
- **Agent configurability:** Let the user toggle the Review step or add custom agents via the UI.
- **Error recovery:** Add per-agent retry logic with exponential backoff; surface partial results if an agent fails mid-pipeline.
- **Streaming tokens:** Stream token-by-token output from Gemini into the UI for a more alive, real-time feel.
- **Unit tests:** Test the Orchestrator with mocked agents to verify state transitions and the revision loop logic.
- **Auth + rate limiting:** Required before any public exposure.

---

## Assumptions Made

1. "Simulated or stubbed" research is acceptable — I chose to use Gemini for real, meaningful output since the API is available.
2. A single revision cycle satisfies the "reviewer can send it back" requirement without needing a configurable loop count.
3. CORS is open to `localhost:3000` only — assumed single-developer local setup.
4. No authentication is needed for this take-home scope.
