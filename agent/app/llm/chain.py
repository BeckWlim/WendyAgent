import json
from langchain_deepseek import ChatDeepSeek
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.messages.base import BaseMessage
from app.config import settings
from pydantic import SecretStr

api_key_secret = SecretStr(settings.DEEPSEEK_API_KEY)

llm = ChatDeepSeek(
    model=settings.MODEL_NAME,
    temperature=0.7,
    api_key=api_key_secret
)

async def run_agent_async(question: str, history: list, meta: dict):
    messages: list[BaseMessage] = []
    for turn_str in history:
        turn = json.loads(turn_str)
        messages.append(HumanMessage(content=turn.get("question", "")))
        messages.append(SystemMessage(content=turn.get("assistant", "")))
        messages.append(AIMessage(content=turn.get("answer", "")))
    messages.append(HumanMessage(content=question))

    response = await llm.ainvoke(messages)
    return response.content