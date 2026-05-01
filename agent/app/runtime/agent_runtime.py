from __future__ import annotations

import json
from typing import Any

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages.base import BaseMessage
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from app.config import settings
from app.memory import MarkdownMemoryVault
from app.persistence import RuntimeStore
from app.rag import PostgresVectorStore
from app.runtime.schemas import AgentRunRequest, AgentRunResult
from app.runtime.schemas import RuntimeTask
from app.tasks import TaskManager
from app.tools import ToolContext, ToolRegistry, ToolSpec
from app.utils.logger import logger


class AgentRuntime:
    def __init__(
        self,
        store: RuntimeStore,
        memory: MarkdownMemoryVault,
        vector_store: PostgresVectorStore,
        tools: ToolRegistry,
        task_manager: TaskManager,
    ):
        self.store = store
        self.memory = memory
        self.vector_store = vector_store
        self.tools = tools
        self.task_manager = task_manager
        self._llm: ChatDeepSeek | None = None

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        conversation_id = self._conversation_id(request.meta)
        username = self._username(request.meta)
        self.store.ensure_conversation(conversation_id, username, request.meta)
        self.store.add_message(conversation_id, "user", request.question)

        memory_hits = self.memory.search(request.question, limit=3)
        rag_hits = self.vector_store.search(request.question, top_k=settings.RAG_TOP_K)
        messages = self._build_messages(request, memory_hits, rag_hits, conversation_id)

        response = await self._get_llm().ainvoke(messages)
        answer = str(response.content)

        self.store.add_message(conversation_id, "assistant", answer)
        self.memory.append_session_turn(conversation_id, request.question, answer)
        self.vector_store.upsert_text(
            document_id=f"conversation:{conversation_id}:{len(answer)}",
            text=f"User: {request.question}\nAssistant: {answer}",
            metadata={"conversation_id": conversation_id, "username": username},
        )

        return AgentRunResult(
            answer=answer,
            correlation_id=request.correlation_id,
            memory_refs=[note.path for note in memory_hits],
            rag_refs=[document.id for document in rag_hits],
            tool_calls=[],
        )

    async def call_tool(
        self,
        name: str,
        args: dict[str, Any],
        conversation_id: str | None = None,
        username: str | None = None,
    ) -> Any:
        context = ToolContext(conversation_id=conversation_id, username=username)
        result = await self.tools.call(name, args, context)
        self.store.record_tool_invocation(conversation_id, name, args, result)
        return result

    def _build_messages(
        self,
        request: AgentRunRequest,
        memory_hits: list[Any],
        rag_hits: list[Any],
        conversation_id: str,
    ) -> list[BaseMessage]:
        context_sections: list[str] = []
        if memory_hits:
            context_sections.append(
                "Markdown memory hits:\n"
                + "\n\n".join(f"- {note.title}: {note.content[:800]}" for note in memory_hits)
            )
        if rag_hits:
            context_sections.append(
                "RAG hits:\n"
                + "\n\n".join(f"- {doc.id}: {doc.text[:800]}" for doc in rag_hits)
            )

        system_prompt = (
            "You are a general Agent Runtime. Answer with useful, concise reasoning. "
            "Use supplied memory and RAG context when relevant. "
            "Do not claim tool execution unless a tool result is explicitly provided."
        )
        if context_sections:
            system_prompt += "\n\n" + "\n\n".join(context_sections)

        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for item in self._normalize_history(request.history):
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item["role"] == "assistant":
                messages.append(AIMessage(content=item["content"]))

        for item in self.store.recent_messages(conversation_id, limit=10):
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item["role"] == "assistant":
                messages.append(AIMessage(content=item["content"]))

        messages.append(HumanMessage(content=request.question))
        return messages

    def _normalize_history(self, history: list[Any]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for turn in history:
            data = self._coerce_turn(turn)
            question = data.get("question") or data.get("user")
            answer = data.get("answer") or data.get("assistant")
            if question:
                normalized.append({"role": "user", "content": str(question)})
            if answer:
                normalized.append({"role": "assistant", "content": str(answer)})
        return normalized

    def _coerce_turn(self, turn: Any) -> dict[str, Any]:
        if isinstance(turn, str):
            try:
                return json.loads(turn)
            except json.JSONDecodeError:
                return {"user": turn}
        if hasattr(turn, "model_dump"):
            return turn.model_dump()
        if isinstance(turn, dict):
            return turn
        return {}

    def _conversation_id(self, meta: dict[str, Any]) -> str:
        return str(meta.get("sessionId") or meta.get("session_id") or meta.get("conversation_id") or "default")

    def _username(self, meta: dict[str, Any]) -> str | None:
        value = meta.get("username")
        return str(value) if value is not None else None

    def _get_llm(self) -> ChatDeepSeek:
        if self._llm is None:
            if not settings.DEEPSEEK_API_KEY:
                raise RuntimeError("DEEPSEEK_API_KEY is required for chat inference")
            self._llm = ChatDeepSeek(
                model=settings.MODEL_NAME,
                temperature=0.7,
                api_key=SecretStr(settings.DEEPSEEK_API_KEY),
            )
        return self._llm


_runtime: AgentRuntime | None = None


def get_runtime() -> AgentRuntime:
    global _runtime
    if _runtime is None:
        store = RuntimeStore(settings.AGENT_DB_PATH)
        memory = MarkdownMemoryVault(settings.MEMORY_VAULT_PATH)
        vector_store = PostgresVectorStore(
            settings.RAG_POSTGRES_DSN,
            settings.RAG_POSTGRES_TABLE,
            connect_timeout=settings.RAG_POSTGRES_CONNECT_TIMEOUT,
        )
        allowlist = {item.strip() for item in settings.TOOL_ALLOWLIST.split(",") if item.strip()}
        tools = ToolRegistry(allowlist=allowlist)
        task_manager = TaskManager(store, concurrency=settings.WORKER_CONCURRENCY)
        _runtime = AgentRuntime(store, memory, vector_store, tools, task_manager)
        _register_builtin_tools(_runtime)
        _register_builtin_tasks(_runtime)
    return _runtime


def _register_builtin_tools(runtime: AgentRuntime) -> None:
    def memory_search(query: str, limit: int = 5, context: ToolContext | None = None) -> list[dict[str, Any]]:
        return [
            {"path": note.path, "title": note.title, "score": note.score, "preview": note.content[:500]}
            for note in runtime.memory.search(query, limit=limit)
        ]

    def memory_write(title: str, content: str, namespace: str = "notes", context: ToolContext | None = None) -> dict[str, str]:
        path = runtime.memory.write_note(title, content, namespace=namespace)
        return {"path": path}

    def rag_search(query: str, top_k: int = 4, context: ToolContext | None = None) -> list[dict[str, Any]]:
        return [
            {"id": doc.id, "score": doc.score, "metadata": doc.metadata, "preview": doc.text[:500]}
            for doc in runtime.vector_store.search(query, top_k=top_k)
        ]

    def rag_upsert(document_id: str, text: str, metadata: dict[str, Any] | None = None, context: ToolContext | None = None) -> dict[str, str]:
        runtime.vector_store.upsert_text(document_id, text, metadata or {})
        return {"id": document_id}

    runtime.tools.register(ToolSpec("memory.search", "Search Markdown Memory Vault notes.", memory_search))
    runtime.tools.register(ToolSpec("memory.write", "Write a Markdown note into the Memory Vault.", memory_write))
    runtime.tools.register(ToolSpec("rag.search", "Search the PostgreSQL vector store.", rag_search))
    runtime.tools.register(ToolSpec("rag.upsert", "Insert or update one text document in PostgreSQL RAG storage.", rag_upsert))
    logger.info("Agent runtime initialized with tools: %s", runtime.tools.list_tools())


def _register_builtin_tasks(runtime: AgentRuntime) -> None:
    async def tool_call(task: RuntimeTask) -> dict[str, Any]:
        name = str(task.payload["name"])
        args = task.payload.get("args", {})
        conversation_id = task.payload.get("conversation_id")
        username = task.payload.get("username")
        result = await runtime.call_tool(name, args, conversation_id=conversation_id, username=username)
        return {"result": result}

    async def memory_index_vault(task: RuntimeTask) -> dict[str, Any]:
        count = 0
        for note in runtime.memory.iter_notes():
            runtime.vector_store.upsert_text(
                document_id=f"memory:{note.path}",
                text=note.content,
                metadata={"path": note.path, "title": note.title},
            )
            count += 1
        return {"indexed": count}

    runtime.task_manager.register_handler("tool.call", tool_call)
    runtime.task_manager.register_handler("memory.index_vault", memory_index_vault)
