from pydantic import BaseModel
from typing import List, Dict, Any

class HistoryTurn(BaseModel):
    user: str
    assistant: str

class AgentRequest(BaseModel):
    question: str
    history: List[HistoryTurn] = []
    meta: Dict[str, Any] = {}