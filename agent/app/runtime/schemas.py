from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RuntimeMessage(BaseModel):
    role: str
    content: str


class AgentRunRequest(BaseModel):
    question: str
    history: list[Any] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class AgentRunResult(BaseModel):
    answer: str
    correlation_id: str | None = None
    memory_refs: list[str] = Field(default_factory=list)
    rag_refs: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class RuntimeTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.pending
    result: dict[str, Any] | None = None
    error: str | None = None
