from typing import Any

from app.runtime.agent_runtime import get_runtime
from app.runtime.schemas import AgentRunRequest


async def run_agent_async(question: str, history: list[Any], meta: dict[str, Any]):
    request = AgentRunRequest(question=question, history=history, meta=meta)
    result = await get_runtime().run(request)
    return result.answer
