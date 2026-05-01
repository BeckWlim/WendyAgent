from typing import Any

from pydantic import BaseModel, Field

class HistoryTurn(BaseModel):
    user: str | None = None
    assistant: str | None = None
    question: str | None = None
    answer: str | None = None

class AgentRequest(BaseModel):
    question: str
    history: list[HistoryTurn | dict[str, Any] | str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    conversation_id: str | None = None
    username: str | None = None


class TaskSubmitRequest(BaseModel):
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
