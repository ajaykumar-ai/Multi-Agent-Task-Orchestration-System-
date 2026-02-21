import asyncio
import uuid
from datetime import datetime
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from agents import Orchestrator
from models import Task, TaskStatus

app = FastAPI(title="Multi-Agent Orchestration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store
tasks: dict[str, Task] = {}


class TaskRequest(BaseModel):
    prompt: str


@app.post("/tasks", response_model=dict)
async def create_task(request: TaskRequest):
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        prompt=request.prompt,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow().isoformat(),
    )
    tasks[task_id] = task

    # Run orchestration in background
    asyncio.create_task(run_orchestration(task_id))

    return {"task_id": task_id}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id].model_dump()


@app.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        last_event_count = 0
        while True:
            task = tasks.get(task_id)
            if not task:
                break

            # Send new events
            if len(task.events) > last_event_count:
                for event in task.events[last_event_count:]:
                    yield f"data: {json.dumps(event)}\n\n"
                last_event_count = len(task.events)

            # Send terminal event if done
            if task.status in (TaskStatus.DONE, TaskStatus.ERROR):
                yield f"data: {json.dumps({'type': 'done', 'task': task.model_dump()})}\n\n"
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def run_orchestration(task_id: str):
    task = tasks[task_id]
    orchestrator = Orchestrator(task)
    await orchestrator.run()
    tasks[task_id] = task
