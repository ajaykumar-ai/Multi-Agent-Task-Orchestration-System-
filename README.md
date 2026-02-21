# Multi-Agent Task Orchestration System

A full-stack AI orchestration platform where **four specialized agents** collaborate to produce a comprehensive research report from a single user prompt — powered by **Groq LLaMA 3.1**.

<img width="1919" height="1031" alt="Screenshot 2026-02-22 000734" src="https://github.com/user-attachments/assets/d70ae623-b6c3-4c76-8bc5-12a7aef8334e" />


```
User Prompt → Planner → Researcher → Writer → Reviewer → Final Report
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| LLM | Groq API · LLaMA 3.1 8B Instant (free) |
| Real-time | Server-Sent Events (SSE) |
| Frontend | Next.js 14 · TypeScript · CSS Modules |

---

## Agent Pipeline

| Agent | Role |
|-------|------|
| 🗂 **Planner** | Breaks your prompt into 3–5 discrete research sub-tasks |
| 🔍 **Researcher** | Gathers detailed information for each sub-task via LLM |
| ✍️ **Writer** | Synthesizes all research into a structured markdown report |
| 🔎 **Reviewer** | Evaluates quality; sends back for revision if needed (1 cycle max) |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Free **Groq API key** → [console.groq.com/keys](https://console.groq.com/keys) *(no credit card needed)*

---

## Setup

### 1. Clone the repo

```powershell
git clone https://github.com/ajaykumar-ai/Multi-Agent-Task-Orchestration-System-.git
cd Multi-Agent-Task-Orchestration-System-
```

### 2. Backend

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate        # Mac/Linux

# Install dependencies
pip install fastapi uvicorn pydantic groq python-dotenv

# Configure API key
copy .env.example .env
# Open .env and set: GROQ_API_KEY=your_key_here

# Start the server
python -m uvicorn main:app --port 8000
```

✅ Backend runs at `http://localhost:8000`

### 3. Frontend

Open a **new terminal**:

```powershell
cd frontend
npm install
npm run dev
```

✅ Open `http://localhost:3000` in your browser

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Submit a task `{ "prompt": "..." }` |
| `GET` | `/tasks/{id}` | Poll task state and results |
| `GET` | `/tasks/{id}/stream` | SSE stream of real-time agent events |

---

## Project Structure

```
multi-agent-system/
├── backend/
│   ├── main.py           # FastAPI app — routes, SSE endpoint
│   ├── agents.py         # Agent classes + Orchestrator logic
│   ├── models.py         # Pydantic models (Task, AgentResult)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Main UI — form, pipeline, log, report
│   │   ├── page.module.css   # Styles
│   │   ├── globals.css       # Global styles + markdown
│   │   └── layout.tsx
│   ├── package.json
│   └── tsconfig.json
├── DESIGN.md             # Architecture decisions & trade-offs
└── README.md
```

---

## Architecture Highlights

- **Blackboard Pattern** — The full `Task` object is passed to each agent; agents mutate specific fields (`plan`, `research`, `draft`, `feedback`) and read prior work
- **SSE Streaming** — Real-time agent events pushed to browser via `EventSource` — no WebSocket overhead
- **Review Loop** — Reviewer can send draft back to Writer once; capped at 1 revision to prevent infinite loops
- **Abstract Agent Base** — All agents share a `run(task) → AgentResult` interface for clean extensibility

---

## Environment Variables

```env
# backend/.env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `venv not activated` | Always run `venv\Scripts\Activate.ps1` before starting backend |
| `Port already in use` | Use `--port 8001` and update `const API` in `page.tsx` |
| `Failed to fetch` | Make sure backend is running and port matches in `page.tsx` |
| `Quota exceeded` | Get a free Groq key at [console.groq.com](https://console.groq.com/keys) |
| `DLL load failed` | Make sure venv is activated — don't use system Python |

---

## Design Document

See [DESIGN.md](DESIGN.md) for full architectural decisions, trade-offs, and what would be improved with more time.
