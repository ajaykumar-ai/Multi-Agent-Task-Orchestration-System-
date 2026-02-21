from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    REVIEWING = "reviewing"
    REVISING = "revising"
    DONE = "done"
    ERROR = "error"


class AgentResult(BaseModel):
    agent: str
    status: str
    output: Any
    feedback: Optional[str] = None


class Task(BaseModel):
    id: str
    prompt: str
    status: TaskStatus
    created_at: str
    current_agent: Optional[str] = None
    events: list[dict] = Field(default_factory=list)
    plan: Optional[list[str]] = None
    research: Optional[dict] = None
    draft: Optional[str] = None
    feedback: Optional[str] = None
    final_report: Optional[str] = None
    agent_history: list[AgentResult] = Field(default_factory=list)
    error: Optional[str] = None
