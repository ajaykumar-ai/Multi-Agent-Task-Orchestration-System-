# Multi-Agent Task Orchestration System

A full-stack AI orchestration platform where four specialized agents (Planner, Researcher, Writer, Reviewer) collaborate to produce a comprehensive report from a user prompt — powered by **Gemini 1.5 Flash**.

## Stack
- **Backend:** Python + FastAPI + Google Generative AI SDK
- **Frontend:** Next.js 14 (App Router) + TypeScript + CSS Modules
- **Real-time:** Server-Sent Events (SSE)

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and set: GEMINI_API_KEY=your_key_here

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## How It Works

1. **Submit a prompt** — e.g. *"Research microservices vs monoliths and write a summary report"*
2. **Planner Agent** breaks the request into discrete sub-tasks using Gemini
3. **Researcher Agent** gathers detailed information for each sub-task via Gemini
4. **Writer Agent** synthesizes all research into a structured markdown report
5. **Reviewer Agent** evaluates the report; if it `NEEDS_REVISION`, the draft is sent back to the Writer (once)
6. The **final report** is displayed in the UI with full activity log

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tasks` | Submit a new task `{ "prompt": "..." }` |
| `GET` | `/tasks/{id}` | Poll task state and results |
| `GET` | `/tasks/{id}/stream` | SSE stream of agent events |

---

## Project Structure

```
multi-agent-system/
├── backend/
│   ├── main.py          # FastAPI app, routes
│   ├── agents.py        # Agent classes + Orchestrator
│   ├── models.py        # Pydantic data models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # Main UI
│   │   ├── page.module.css  # Styles
│   │   └── globals.css
│   ├── package.json
│   └── tsconfig.json
└── DESIGN.md
```
